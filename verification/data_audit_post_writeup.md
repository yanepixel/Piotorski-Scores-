# Audit of the extension to May 2026 and the REIT liquidity variant

Agent 3, report only. No project code, config, data or results were changed. WRDS was read-only.

Scripts: `verification/audit_27_lib.py`, `audit_27_extension.py`, `audit_28_reit.py`, `audit_29_followup.py`. Output: `audit_27_output.txt`, `audit_28_output.txt`.

Files audited, first 14 characters of SHA-256: `10_extension_2026.py` 30974EFBCA26D1, `09_reit_liquidity.py` 0291F734DB5407, `config.py` 4D34351FBA2E43, `comp_secm_extension.parquet` 57C0386B2B34C1, `comp_funda_reit_fields.parquet` 1581CBAAC6B786.

**Terms.**
- **Alpha:** return left after the six factors (market, size, value, profitability, investment, momentum), in percent a year.
- **t:** alpha divided by its standard error. Beyond about 2 is treated as significant.
- **Lag:** how many months of residual correlation the Newey-West standard error allows for. The locked rule is 12.
- **Spread:** High minus Low.
- **Placebo:** the same test on portfolios built with shuffled scores, to see how often chance gives the same result.
- **Points:** percentage points of a portfolio's return.

## Verdict

**No High items. Both runs are correct as calculated, and I reproduced every monthly return independently.** The largest gap was 3e-16 for both the extension's 252 months and the REIT variant's High and Benchmark.

The issues below concern how the results are read:

| Severity | Finding |
|---|---|
| Medium | The extended t of -3.16 needs the same lag caution. The fair range is about -2.0 to -3.25, most estimates near -2.7 to -3.25. It does not separate stock selection from sector tilt: within-sector placebo 12.5% for alpha, 7.4% for t. |
| Medium | "Two names" is only part of the Spread's story. Removing Western Digital and Intel turns the 12-month gap from -35.8 to +5.9 points, but Low also rose much more broadly than High: median stock +16.7% against +0.3%. |
| Medium | Five months moved the Spread figures noticeably. Average yearly Spread goes from -0.57% to -1.71%, and the 2015-on Spread alpha t from -1.49 to -1.84. The 21-year Spread alpha stays insignificant (t -1.01). Those extended Spread figures should always be shown with the headline next to them. |
| Medium | The REIT variant's -4.24% (t -4.40) is the same result, not new evidence. Its monthly returns correlate 0.9989 with the headline's, and most of the fall comes from adding REITs of any kind. |
| Low | `10_extension_2026.py:301` puts "was not rerun here" into `results.md`. The placebo has now been rerun, below. |
| Low | `output/writeup.md` is now 2C9015FA9180F5, different from the C77BA3D9 version I last checked. It was last saved at 1:08 PM, before both runs, and does not cite either. I did not re-audit the change. |
| Low | The evidence that the extension rules were locked first rests on file timestamps (section 8). |

## Extension

### 1. Prices, returns, weights

**The stated numbers are right.** Western Digital and Intel supply 29.4 of Low's 45.07 points. Micron supplies 9.06 of High's 15.36. My rebuild of `contributors_jan_may_2026.csv` matches on all 107 rows with no gap.

The large positions are Western Digital and Intel in Low, and Micron in High. Each weight follows from its Jun-Dec return and the bucket's total return.

**Price checks on the top 12 contributors in each bucket and six of the largest detractors (30 names):**
- **December splice:** for all 362 names held in December, Compustat and CRSP prices agree within 1 cent and December returns within 25 bp. No name jumps on the change of source.
- **Daily data:** `comp.secd` total returns match the `trt1m` chain within 0.12 points over five months.
- **IBES, a separate vendor:** 210 of 210 price dates match within 0.1% across December to June. Changes between IBES dates equal the secd changes for all 30 names.
- **Splits:** none in the window for these names. All three large moves are confirmed as price moves.

Limits: IBES dates are mid-month, so month-end prices are confirmed only by secm and secd, both S&P. CRSP cannot check these months yet. I checked that prices are right, not why they moved.

A fresh pull of secm matched the project's raw file with no differences. All 364 security links match my own. The 15 nulls in that comparison are null returns on the raw rows and none falls on a live holding, as the rebuild shows.

### 2. The four conditions

| Condition | Result | Evidence |
|---|---|---|
| No `secstat` filter | Met | Column is never read. A return rebuild without it matches. |
| Hologic and Coterra stop after their rule months | Met | `extend` drops by rule and stops on any other missing or null value. My rebuild using the same rule matches. |
| Becton Dickinson and Comcast used as given and reported | Met | Named-events table and price-only sensitivity in `results.md`. |
| Labelled as Compustat, separate from the headline | Met | `return_source` column, disclosure text and "not the headline" in `results.md`. The six headline files changed since my Phase 7 baseline are the same six explained then. |

### 3. Does t -3.16 carry the lag caution? Yes.

Period: June 2015 to May 2026, 132 months, alpha -3.25%.

| Method | t or equivalent |
|---|---|
| Lags 0, 4, 8, 12 | -1.98, -2.47, -2.96, **-3.16**; flat from 12 to 36 |
| Simulated size of the 12-lag test, no alpha, shuffled residuals | Passes 2 in 8.1% of runs instead of 5%. Rescaled t **-2.74**, p 0.009 |
| Same, residuals in 12-month blocks | Passes 2 in 6.6%. Rescaled t -3.25, p 0.004 |
| Pairs block bootstrap | Implied t -3.03. 95% range -5.7% to -1.5% |

The t rises with lags because the residuals are mildly negatively autocorrelated, which is the same pattern as the headline. With no lag allowance it is just below 2. I would describe it as "about -2.7 to -3.2, and about -2 with no lag allowance".

**Placebo on the extended period** (2,000 shuffles across all stocks, 1,000 within sector, bucket sizes kept):

| June 2015 to May 2026 | Actual | Random mean | Share of random at or below actual | Within-sector mean | Share of within-sector at or below actual |
|---|---|---|---|---|---|
| High alpha | -3.25% | -0.90% | 1.7% | -2.03% | 12.5% |
| High t | -3.16 | -0.80 | 1.6% | -1.75 | 7.4% |
| High minus Benchmark alpha | -2.51% | -0.17% | 1.7% | -1.30% | 12.5% |
| Spread alpha | -6.79% | -0.04% | 0.1% | -3.93% | 9.1% |
| Spread t | -1.84 | -0.01 | 6.9% | -1.85 | 50% |

Over the 21 years, High alpha -0.47% sits at 17.9% of random and 41.4% of within-sector.

Random High portfolios pass |t| 2 in the 2015-on window 12.9% of the time, and within-sector ones 40.8%. So a significant-looking t is common for this universe in this decade. High does worse than random stocks, but it isn't clearly worse than random stocks from the same sectors. This agrees with my headline result (1.5% and 11%); the extra months did not change it.

### 4. The Spread's -35.72 points

**Effect of removing names** (gross returns, so the base gap is -35.78). This is a sensitivity only, not a rule. Removing large winners always flatters the other side.

| Removed | Jan-May High | Jan-May Low | Jan-May gap | 12-month gap |
|---|---|---|---|---|
| None | +15.4 | +45.1 | -29.7 | -35.8 |
| Western Digital | +15.4 | +29.0 | -13.6 | -8.6 |
| Western Digital, Intel | +15.4 | +18.3 | -2.9 | +5.9 |
| Micron | +6.5 | +45.1 | -38.5 | -48.4 |
| All three | +6.5 | +18.3 | -11.7 | -6.7 |

**How much is two or three names?**
- Removing Western Digital and Intel alone accounts for almost all of the gap and flips the 12-month sign. That comparison keeps Micron on the High side, however.
- Removing all three on both sides, the fair version, leaves -11.7 points in five months and -6.7 over 12 months. So those three names explain about 60% of the Jan-May gap and about 80% of the 12-month gap.
- **The rest is breadth, which the two-name framing misses.** 84.8% of Low rose against 51.4% of High. The median Low stock made +16.7% against +0.3%. Without drift weights, the stocks average +29.8% in Low against +5.5% in High. Without the top names, that is +18.2% against +2.2%.
- **Sectors matter.** Information technology gives Low 33.6 of its 45.1 points on a 28% weight, against 12.6 of High's 15.4 on a 24% weight. Energy is 26% of Low and gave 6.2 points, against 1.5% of High.

**How unusual is it?**
- Among 20,000 random 76-name and 33-name portfolios from the 2025 list, the 5-month gap has a 95% range of -26.8 to +21.8 points. The actual -29.7 is at the 1.5% tail. The 12-month -35.8 is at 4.8%.
- Across 243 overlapping 5-month windows in the headline period, only about 0.4% are as low, all from the 2020-21 stretch.
- -35.7 is the lowest of 21 holding years, next to -30.0 (2020-21) and -28.0 (2019-20).
- These percentages describe this one year's stock returns, chosen after the fact, and stocks in one sector rise together. They are not a test of the F-score.

**Are the full-period figures driven by these five months?** In part, for the Spread only.

| | Headline to Dec 2025 | Extended to May 2026 |
|---|---|---|
| High alpha, full | -0.78% (t -0.71) | -0.47% (t -0.42) |
| High minus Benchmark alpha, full | -0.95% (t -1.02) | -0.85% (t -0.91) |
| Spread alpha, full | -2.04% (t -0.72) | -2.83% (t -1.01) |
| Average Spread a year, full | -0.57% | -1.71% |
| High alpha, 2015 on | -3.83% (t -4.10) | -3.25% (t -3.16) |
| Spread alpha, 2015 on | -5.72% (t -1.49) | -6.79% (t -1.84) |

No conclusion flips. High's figures improve because High beat what its factor loadings predicted by about 6 points in the window. The Spread's 5-month unexplained return is about -20.6 points. Removing April 2026 alone moves the full Spread alpha only to -2.50%. A difference of 1.14 points a year in average Spread from 5 of 252 months is large, so the three-times larger average should not be presented as a stronger trend.

**What can fairly be concluded from 5 months on one data source:**
- The arithmetic and prices can be relied on, subject to later CRSP comparison.
- High did not protect against a rally led by low-score, cyclical and memory-chip stocks in this window. Low beat it by an unusually large amount, with two stocks supplying most of the margin but with breadth behind it.
- The window adds no real evidence on whether the F-score works. It is one narrow episode, part of one holding year, about one sector-driven market move. It should not strengthen or weaken the headline in either direction.
- The December weights come from the rule itself, not from any choice in this run. These positions got that large because of how the fixed 12-month hold works.

## REIT variant

### 5. Code, timing, zero uncomputable

**The code matches `REIT_LIQUIDITY_SUBSTITUTE`.** My own rebuild from a fresh Compustat pull matches `formation.parquet` on all 8,001 rows, with no difference in score, bucket or fiscal year.

- **REIT flag:** read at permno and formation date, with no null issuer type among 8,414 included rows. No non-REIT row uses the substitute.
- **No look-ahead:** no row's `avail_date` is after formation, and no fiscal year-end is on or after it. `che` and `lt` come from the same fiscal-year row as the other signals and carry the same availability date. As everywhere in this project, Compustat values are today's, not as first reported.
- **Fresh pull:** 20,796 rows of `che` and `lt`, no differences against the raw file.

**Zero uncomputable is real, with an explanation worth stating:**
- Among 943 REIT company-years, `che` is null 4 times and `lt` 4 times. They are always missing together, and `lt` is never zero or below. `che` is zero once.
- Among the 757 company-years needing the substitute, none has a null or zero `che`, or a null `lt`, in either the current or prior year.
- The test is partly structural. "Needing" requires the other eight signals to exist, and rows with missing balance-sheet data usually fail those first. 24 REIT company-years fail on another signal, which is where the gaps show up. That is why 2 list rows stay unscored.
- These are also large listed REITs. Nulls across the whole file are only 0.6% for `che` and 0.8% for `lt`.

**Harmless timing cases on the REIT flag:** 14 of the 430 rows use accounts ending before the first REIT flag for that stock. 13 are May 2005 rows where the CRSP file simply starts in January 2005. The other is Weyerhaeuser at formation May 2010, using December 2009 accounts while the flag begins in January 2010. The config rule flags on the formation date, so this follows the rule.

One added row is in the Materials sector, which accounts for the difference between the 430 here and the write-up's 429 real estate and financial rows. I infer but did not confirm that this row is Weyerhaeuser.

### 6. Is the pass rate plausible? Yes.

48.1% is close to 48.9%, the rate for the same `che`/`lt` test across all firms with both measures (14,544 company-years). The test is a change in a ratio, so about half is what one would expect.

The 26.9%-68.8% range is mostly small-sample noise. Each year has only 13 to 27 rows.
- Equal yearly rates are not rejected: chi-square 24.8 on 20 degrees of freedom, p about 0.2.
- Simulation with a constant 48.1% gives a typical range of 27.3%-69.2%. As wide a range appears in 26% of runs.
- Yearly rates correlate 0.48 with non-REIT `F_DLIQUID`. That is modest shared movement, as with 2009 and 2020, when firms raised cash.

**Note on quality, not a rule suggestion.** `che/lt` agrees with the current-ratio test 70% of the time where both exist. The median REIT ratio is 2.75% of liabilities, so the signal mostly reflects year-end cash timing. It is noisy, as the rate shows, but it's what the rule specifies.

### 7. Why 2015-25 alpha falls to -4.24%: same result, not new evidence

| 2015-25, 127 months | Headline | Variant | Change |
|---|---|---|---|
| High alpha | -3.83% (t -4.10) | -4.24% (t -4.40) | -0.41 |
| Benchmark alpha | -1.20% (t -1.63) | -1.53% (t -2.00) | -0.33 |
| High minus Benchmark alpha | -2.63% (t -2.30) | -2.70% (t -2.36) | -0.07 |

- **Sector effect, in both High and Benchmark.** Added REITs across all buckets have alpha -5.51% (t -1.46). All included REITs have -5.08% (t -1.47). Against High, the fall is matched almost entirely by the fall in Benchmark.
- **The score isn't choosing worse REITs.** Replacing the High REITs with the same number of randomly chosen added REITs gives a mean alpha of -4.18%, range -4.46% to -3.90%. The actual -4.24% sits at 34%. So about -0.35 of the -0.41 comes from adding any REITs, and about -0.06 from which ones, which is noise.
- **Few rows, large effect.** Added REITs are 41 of 787 High rows from 2015 on (5.2%), usually two to four names. Their own alpha, -7.00% (t -1.71), rests on few names.
- **Same portfolio.** Variant and headline High correlate 0.9989 on monthly returns, and 0.986 on residuals.
- **Same lag caution.** t by lag: lag 0 -2.80, lag 4 -3.29, lag 12 -4.40, lag 24 -5.18.

Over the full period, High alpha moves only from -0.78% (t -0.71) to -1.01% (t -0.91), and High minus Benchmark alpha from -0.95% (t -1.02) to -0.96% (t -1.00). The variant tells us the headline result holds when most missing REITs are added, and that REITs were weak in that decade. It should not be counted as another test or as stronger evidence, and the rise in t from -4.10 to -4.40 shouldn't be quoted as such. The results file already says this isn't a blind test.

### 8. Did knowing the REIT result affect the extension?

**Nothing in `10_extension_2026.py` departs from the locked rules.**

| Rule | In the code |
|---|---|
| End May 2026, `trt1m` only | Reads end and field from config, exits if field differs |
| Named exits, then pro rata | From config. Any other gap stops the run |
| Spin-offs used as given | Base run has no override. Price-only is sensitivity only |
| No new rebalance or cost | None in `extend`. June 2026 is not used |
| CRSP weights to December | Checks against the published June-December series |
| Benchmarks | SPY and RSP from the config lines |
| Separate outputs | Writes only to `output/extension_2026/`, and exits with an error if a headline file changes |
| Sensitivity sizes | 494 bp matches `validation.md`. Sensitivities do not feed base results |

**Timing, from file timestamps on 2026-11-01:**
- secm pull 1:36 PM
- `validation.md` 1:39
- `CLAUDE.md` 1:40
- `config.py` 1:42:28
- REIT results 1:42:52
- extension script 1:44:28
- extension results 1:44:33

So `config.py` was last saved before the REIT results, and the script after them, as Agent 1 disclosed. There is no git history in this project, so this cannot exclude earlier versions of the script or earlier runs. It only shows that the final rules predate the REIT output and the final code follows them. Neither run has a choice that would help it: the REIT run does not feed the extension at all, and the extension has no free parameters left.

## Decisions for the user

These are presentation choices and none needs a rule change:

1. Whether to quote the extended 2015-on t as -3.16 alone. My recommendation is to give the range above and the within-sector placebo next to it.
2. Whether to count the REIT variant's -4.40 as support. My recommendation is not to; report it as a robustness check only.
3. When CRSP covers 2026, compare these five months with it before treating any extended figure as final.
