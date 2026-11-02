# Phase 4-6 audit: look-ahead, survivorship and return errors

Correction, Phase 7 audit: the full-period High alpha t is -0.71 (exact -0.7146); this report first showed -0.72 in three places, now corrected.

Report only. I edited no project code, changed no setting, and did not start `08_robustness.py`. `NEWEY_WEST_LAGS` stays locked at 12; other lag lengths here are sensitivity only. Nothing below recommends a rule change because of performance.

Terms: **alpha** is return left after accounting for market, size, value, profitability, investment and momentum factors. **Newey-West** adjusts standard errors for returns correlated over time; **lags** is how many months back it looks. **t-stat** is how many standard errors a number sits from zero. **Placebo** is a deliberately meaningless or deliberately cheating version of the test, run to see whether the machinery responds as it should. **Shuffled scores** means randomly reassigning scores among the same companies on each date.

Files tested (SHA-256, first 14 characters), unchanged at the end of testing: `05_align.py` AD2C26659C67C2, `06_portfolios.py` 908E24BCEC39B8, `07_evaluate.py` 25D3D93C1524E6, `config.py` 46F3FBAAF3403E, `formation.parquet` 2EAE1EB7EA2ACD, `portfolio_returns.csv` B8D0F94AD52F84, `checkpoint3_results.md` 8BFFF3C21C88E2.

Evidence: `verification/audit_17_raw_returns.py`, `audit_18_placebo.py` and their `_output.txt` files.

## Result

**No High findings. I found no look-ahead, survivorship or return bug in Phases 4-6.** A separate engine reproduces every published series to rounding error, and the placebos behave as they should.

**The negative 2015-25 High alpha is calculated correctly and is not a bug or an effect of the 2017 sector change. But t = -4.10 overstates the evidence against the F-score itself.** A fair summary:

- The alpha is -3.83% a year, with a defensible t of about -2.5 to -3.6.
- About one third of it belongs to the whole universe, not to High: randomly chosen stocks average -1.3%.
- Measured against random selection, it is unusual (about 1.5% one-sided, 3% two-sided). Measured against random selection within the same sectors, it is not clearly unusual (11% one-sided).
- It is one of four subperiod alphas tested. The full-period alpha is -0.8%, t -0.71.

| ID | Severity | Finding | Who acts |
|---|---|---|---|
| M1 | Medium | t = -4.10 should not be reported alone | Master session: write-up |
| M2 | Medium | The eight-signal run has no bucket rule yet, and returns now exist | User decision |
| M3 | Medium | That run puts one null-return month into a held position | User decision |
| L1-L4 | Low | See the Low findings section | Noted |

## 1. Independent engine

I rebuilt portfolios from `formation.parquet` and raw returns, using none of Agent 1's code.

| Bucket | Largest gross difference | Largest net difference | Largest turnover difference |
|---|---|---|---|
| High | 1.4e-16 | 1.4e-16 | 8.9e-16 |
| Middle | 1.9e-16 | 1.9e-16 | 1.0e-15 |
| Low | 1.4e-16 | 1.4e-16 | 1.6e-15 |
| Benchmark | 2.5e-16 | 2.5e-16 | 1.6e-15 |

## 2. Placebos: the machinery works

**Shuffled scores (2,000 draws, keeping each date's High and Low sizes):**

| Measure | Shuffled mean | Actual | Expected from machinery |
|---|---|---|---|
| High alpha, full period | +0.1%, t +0.08 | -0.8%, t -0.71 | Near zero: yes |
| High alpha, 2005-15 | +1.4% | +2.5% | Near the Benchmark's +1.5%: yes |
| High alpha, 2015-25 | -1.3% | -3.8% | Near the Benchmark's -1.2%: yes |
| High minus Low alpha, full | +0.1%, t +0.05 | -2.0% | Near zero: yes |
| High minus Benchmark alpha, 2015-25 | -0.1% | -2.6% | Near zero: yes |
| Two-way turnover | 1.69 | 1.64 | Similar: yes |

**Look-ahead placebo: High built from next year's score, which isn't yet known.**

| Period | As used | Next year's score |
|---|---|---|
| High alpha, full | -0.8%, t -0.71 | +2.0%, t +1.30 |
| High alpha, 2005-15 | +2.5%, t +1.76 | +5.6%, t +4.36 |
| High alpha, 2015-25 | -3.8%, t -4.10 | -1.3%, t -0.71 |
| High minus Low alpha, full | -2.0%, t -0.72 | +10.5%, t +4.82 |

So cheating produces a large, obvious fake result, and the real results show nothing like it. This is good evidence against meaningful look-ahead.

Ignoring filing dates, using the latest fiscal year ended by formation, changes 217 rows and moves the full-period alpha only from -0.8% to -0.9%. The filing-lag rule isn't what drives the result either way. The two-years-ahead and one-year-stale variants couldn't run because a bucket was empty in 2025 and 2005.

## 3. The 2015-25 High alpha

### Calculation confirmed

Net alpha is -3.83% a year, t -4.104, by three routes: my matrix code, statsmodels, and a scalar formula with no matrices. Plain OLS gives -2.47.

### Sensitivity to lags (sensitivity only)

| Lags | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 10 | **12** | 15 | 18 | 24 | 36 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t | -2.52 | -2.51 | -2.65 | -2.82 | -3.06 | -3.40 | -3.78 | -3.97 | **-4.10** | -4.28 | -4.50 | -4.91 | -5.39 |
| t, small-sample correction | -2.45 | -2.44 | -2.58 | -2.74 | -2.97 | -3.31 | -3.67 | -3.86 | **-3.99** | -4.16 | -4.38 | -4.78 | -5.24 |

**Why the gap exists:** residuals are mildly negatively autocorrelated (the first 12 autocorrelations sum to -0.42), so each extra lag shrinks the standard error. With 127 months, that long a lag also becomes unreliable. Common rule-of-thumb lags for this sample are about 4, which gives -3.06. No single outlier causes this: dropping the 6 largest residual months gives -4.2%, t -4.42.

### How far is the t inflated?

I simulated the Newey-West 12 t at 127 months with true alpha set to zero, holding factors fixed.

| Simulation | Spread of null t (should be 1) | Share past \|2\| (should be about 5%) | 2.5% / 97.5% | Two-sided p of -4.10 | t after rescaling |
|---|---|---|---|---|---|
| Independent residuals | 1.15 | 8.6% | -2.25 / +2.34 | 0.0016 | -3.56 |
| Block-12 residuals | 1.04 | 5.9% | -2.08 / +2.12 | 0.0006 | -3.96 |

A pairs block bootstrap (block 12) gives a 95% range of -6.0% to -1.6%, with 0.06% of draws at or above zero, implying t about -3.4.

**Verdict on the gap:** it is partly a small-sample effect, so -4.10 is too large, but the alpha doesn't vanish. Every t here is at least -2.4 in size. This tests alpha against zero, though, and zero is the wrong yardstick for the F-score, as the next section shows.

### Compared with random selection

| Random comparison | Actual alpha | Random mean | Share of draws at or below actual (alpha) | Share at or below actual (t) |
|---|---|---|---|---|
| Same-size random High (2,000) | -3.83% | -1.3% | 1.45% (two-sided 2.85%) | 0.25% (two-sided 0.45%) |
| Random within sector, same mix (1,000) | -3.83% | -2.6% | 11% | 3.2% |

- **Random High portfolios pass the significance bar easily:** 18.8% of shuffled High portfolios have |t| of 2 or more in 2015-25, against 1.4% over the full period. The period itself leans negative.
- **Rough split of the -3.83%:** about -1.3 points is the universe (random stocks, including costs), about -1.3 is High's sector mix, and about -1.2 is stock selection within sectors. That last part is not unusual by chance, at 11% one-sided.

The t-based shares are stronger than the alpha-based ones because High's residual risk happens to be low. I give more weight to the alpha-based shares, since the t carries the lag issue above.

**Directly against the Benchmark:** High minus Benchmark alpha is -2.63%, t -2.30 (random: 1.45% at or below for alpha, 4.1% for t; within sector: 11% and 14.6%).

**Multiple tests:** four subperiod alphas are reported (High and Spread, in two periods). A rough Bonferroni adjustment of the 2.85% two-sided alpha share gives about 11%. The period split was fixed in advance, which helps, but the full-period result remains insignificant, and 2005-15 has the opposite sign (+2.5%).

### Not caused by a factor loading

| Model | CAPM | FF3 | FF3+MOM | FF5 | **FF5+MOM** | No RMW | No CMA | No SMB | No HML |
|---|---|---|---|---|---|---|---|---|---|
| Alpha | -3.80% | -3.47% | -3.43% | -3.83% | **-3.83%** | -3.42% | -3.85% | -4.01% | -3.79% |
| t | -2.59 | -3.48 | -3.68 | -3.88 | **-4.10** | -3.72 | -4.17 | -4.44 | -3.76 |

Alpha barely moves whichever factor is removed. The return breakdown confirms it: High's excess return of +8.68% a year equals alpha -3.83% plus market +12.28%, RMW +0.63%, SMB -0.30%, CMA -0.06%, HML -0.04%, MOM 0.00%. Loadings other than market are small (SMB 0.11, HML 0.04, RMW 0.18, CMA 0.06, MOM 0.00).

### Not a bug, and not the 2017 sector change

| Test (High net, 2015-25) | Alpha | t |
|---|---|---|
| As reported | -3.8% | -4.10 |
| No REITs | -3.7% | -4.03 |
| No sector 60 | -3.7% | -4.03 |
| No real estate at all | -3.7% | -4.03 |
| 2015-06 to 2017-05 only | -1.1% | -1.12 |
| 2017-06 to 2025-12 only | -4.2% | -3.95 |

High holds only 0-4 real-estate names a date, so the sector change cannot move this. The first subsample is just 24 months, so the lower figure there is weak evidence of any shift.

### Where it comes from

- **Timing:** High minus Benchmark alpha is -3.7% (t -3.21) from 2015-06 to 2020-05, but -0.5% (t -0.25) from 2020-06 and 0.0% from 2021. High's own alpha stays near -3.6% in 2021-25 because the universe alpha is also negative then. So High's relative shortfall is concentrated in the earlier half.
- **Energy:** the largest sector contribution is energy (-0.91 points a year of a -1.74 gap; a rough attribution, gross, with exits carried flat). High averages 8.6% energy on 2015-25 lists against 7.0% for all names. Removing energy from High and Benchmark gives High -2.3%, t -2.08, and High minus Benchmark -1.3%, t -1.20. **This is diagnosis only, not a proposal to exclude energy.** Removing technology goes the other way (-6.3%).
- **Single years:** dropping any one holding year leaves -2.8% to -4.6%, t -2.12 to -5.13. The biggest single change is dropping 2022. The 2020 list has the largest selection shortfall (-10.8 points), as Low's rebound names led that year.
- **Names:** largest detractors are Occidental, Freeport-McMoRan, Halliburton, Applied Materials and Tesla. Largest helpers include Palantir, Micron and Delta. No single name decides it.

### M1. Medium: how to report this

The calculation is right, so the number may stand as the locked headline, but it needs context beside it. Suggested text:

> "High's alpha for June 2015 to December 2025 was -3.8% a year, t -4.10 with the pre-set 12 lags (-2.47 without adjustment; -3.06 with 4 lags). In simulations, 12 lags on 127 months overstate significance somewhat, implying a t nearer -3.4 to -4.0. Randomly chosen portfolios from the same universe also averaged -1.3%, and 19% of them reached |t| of 2 or more. The alpha falls in the lowest 1.5% of random selections, but the lowest 11% if the random selections keep High's sector mix. The full-period alpha is -0.8%, t -0.71, and 2005-15 has the opposite sign."

## 4. Bucket mix: no domination

| Measure | High | Low |
|---|---|---|
| Largest single-sector share on any date | 35.1% (consumer discretionary, 2010) | 50.0% (technology, 2022, of 28 names) |
| Share of all name-dates by list year | 2.8% to 8.2% | 2.7% to 9.8% |
| Names per date | 43-127 | 20-71 |

- **2015-25 shares compared with all names:** High energy 8.6% vs 7.0%, industrials 16.1% vs 16.4%, technology 22.1% vs 22.4%. Low energy 15.7%, technology 28.7%.
- **Size:** High's median rank (232) is close to all names' (242) on 2015-25 lists.
- **Repeat names:** no company is in High on more than 9 dates (Occidental, Paychex, EOG).
- **Low's fatter periods:** 2021 (71 names), 2016 (57), 2020 (53). It is broader and more cyclical, as already disclosed.

## 5. Delisting returns (raw data)

| Test | Result |
|---|---|
| Exits before the data ends, among 942 included securities | 329, all with a delisting record |
| Final-month return null | 0 |
| Final-month return zero | 1, a merger |
| Performance-type exits | 37, none null or zero |
| Final-month return matches legacy `ret` combined with `dlret` | 313 of 316 within 0.1% |

- **In actual portfolios:** 179 mid-period exits (High 32, Middle 125, Low 22), all with delisting flags. The script's checks report no null returns or gaps inside held windows. Four names delist on the formation date (2 Middle, 2 Low), and their weight is spread pro rata.
- **Largest effect:** among included positions, the one bankruptcy while held is SunEdison, -58.9%. A full wipeout would add about 10bp in that year.
- **Limit:** a delisting return runs to CRSP's first available price, and 5 merger exits with non-cash parts (such as Safeway) may leave some value out. Low.

## 6. Factors, regression and annualization: correct

- **Units:** decimals throughout. Same-month correlation with the market is 0.988, against 0.009 one month ahead.
- **Join:** on month, cut to December 2025, with a failure if any value is missing. The code does this correctly.
- **Excess returns:** High, Low and Benchmark subtract `rf`. Spread and High minus Benchmark rightly don't.
- **Newey-West:** Bartlett weights with 12 lags, confirmed by hand. statsmodels applies no small-sample correction and uses the normal distribution, so results are slightly generous (L1).
- **Alpha annualization:** monthly alpha x 12, simple and consistent.
- **Partial 2025:** 7 months count in the regressions and the full-period figures, CAGR uses the actual month count, and the hit rate excludes it. All labelled.

## 7. Benchmarks: correct

SPY is within 0.02 points of published annual returns for 2006-2024 (mean 0.00). RSP is within 0.76 (mean 0.18), and all gaps are under 1 point. Published figures are from my recollection, not checked against a source. SPY's agreement to two decimals makes that a strong check; RSP's figures are less certain.

**April 2018 chain:** the code chains the two rows into one return, matching all daily rows compounded. 2018 agrees with the published annual figure to about 0.1 point.

## 8. Costs: correct and charged once

- **Reproduced exactly:** turnover and net returns match my engine, to rounding error.
- **Once per rebalance:** the cost is applied only in the first holding month of each cohort.
- **Consistent:** 10bp on each side of two-way turnover. High's 1.64 two-way gives about 16bp a year, matching the published 0.16%.
- **Mid-period reinvestment** is uncharged, as set in the config. It's small: 179 exits over 21 years.
- **Small point:** a name delisting on the formation date is charged as a buy, though it can't be held (L3).

## 9. Eight-signal note

**Agent 1's note is correct, and the check works.** Under an eight-signal rule, 641 rows would join the 7,571 held. Exactly one null-return month then falls in a held position: General Growth Properties, May 2009, on the 2008 list. It is the last month of that holding year. `06_portfolios.py` would stop on its null-return check, so it can't pass silently.

General Growth filed for bankruptcy in April 2009 and left the NYSE. CRSP has no priced rows from then, with status `X` and flag `NT`, and it has later priced rows, so this is not a recorded delisting.

### M3. Medium: a rule is needed first

Without a rule, the code's `dropna` would treat it as an exit: the position's weight goes pro rata to the others, and it earns nothing that month. Options are that treatment, or holding the value flat for that month. Size is small: one name of about 395 in the benchmark, for one month, so the choice can't matter much. It just needs to be fixed and stated.

### M2. Medium: bucket placement isn't defined, and returns now exist

Section 8b requires the eight-signal bucket placement to be defined "before any returns exist", and `config.py` still says "to be defined". Headline returns now exist, so that condition can no longer be met. Without a rule, the run can't produce High or Low. The user should set the rule on structural grounds, for example rescaling 8 signals to 9 or using fixed eight-signal cutoffs, without looking at any eight-signal returns. The write-up should disclose that it was set after headline results were seen.

## Low findings

- **L1.** Newey-West t-stats use no small-sample correction, and significance uses a fixed |2|. Disclose alongside M1; no change to the locked setting.
- **L2.** `checkpoint3_results.md` says "Alphas at or beyond |t| = 2: none" at the top, while the only significant result sits in the subperiod section. It is stated correctly, but readers may miss it.
- **L3.** Formation-date delisters are charged as buys. Four names, trivial size.
- **L4.** The returns-by-score table includes scores 0-3 with few names, and the rank correlation of -0.32 uses them. The table flags this; the correlation should carry the same warning.

## What this doesn't establish

The placebo and bootstrap results describe this sample and these methods. The within-sector comparison shows the result isn't clearly separable from sector mix; it doesn't show that sector mix caused it. Nothing here says whether the 2015-25 shortfall would continue.
