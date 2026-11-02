# Audit of the 100/100 long/short run

Agent 3, report only. No project code, config, data or results were changed. WRDS was read-only.

Scripts: `verification/audit_30_lib.py`, `audit_30_longshort.py`, `audit_31_ls_placebo.py`. Output: `audit_30_output.txt`, `audit_31_output.txt`.

Files audited, first 14 characters of SHA-256: `11_long_short.py` 9491633322254E, `config.py` 160E4725AD3E6D, `CLAUDE.md` A81B4DB5C60C97, `results.md` FB6CDCC7729ED4, `nav_main.csv` B54BDC0D424A62.

**Terms.**
- **NAV:** net asset value, the capital in the strategy.
- **L and S:** dollar value of the long leg (High) and short leg (Low).
- **Gross:** (L + S) / NAV. **Net:** (L - S) / NAV.
- **Annual reset:** L = S = NAV each June only, the locked rule. **Monthly reset:** the same every month.
- **CAGR:** constant yearly growth rate. **Alpha:** return left after six factors. **t:** alpha over its standard error, with beyond about 2 treated as significant.
- **Placebo:** the same run with shuffled scores.
- **Points:** percentage points of NAV.

## Verdict

**No High items. The reported figures and accounting are correct:** CAGR -1.80%, Sharpe -0.22, drawdown -75.8%, alpha -4.53% (t -1.48), stress alpha -6.18% (t -1.98). My stock-level rebuild matches `nav_main.csv` and `nav_extension.csv` to 5e-16.

| Severity | Finding |
|---|---|
| Medium | **The annual-reset design drives most of the headline loss.** CAGR is -1.80% as locked and -0.42% with monthly resets at a real charge. That is 1.38 of the 1.80 points. No reset choice makes alpha significant or the result positive. |
| Medium | **"100/100" describes June only.** Gross reaches 5.0x, net -0.70, and equity falls to 20% of gross, at the end of February 2021. At end May 2026 the short is 243% of NAV and Western Digital alone 46%. `results.md` says no margin limit is modelled but does not give these sizes. |
| Medium | **t -2.35 is not evidence about the F-score.** Shuffled scores within sectors average t -2.11 for the same window, and 56.5% pass |t| 2. |
| Medium | **-32.65% in 2025-26 is mostly two Compustat-era names.** Without Western Digital and Intel it is +9.0%. Without those two and Micron it is -3.6%. |
| Low | The caution line in `results.md` uses t -2.35 for two different series and says "Full period" without saying it is the extended period. |
| Low | `drift_and_rounding` in `results.md` is mislabelled. It contains no rounding, and the note's reference to cash interest and compounding does not describe it. It is an exact sum of two effects. |
| Low | The uncharged June resizing is real but immaterial: CAGR -1.83% instead of -1.80%. |

## 1. Accounting from dollar positions

All correct.

- **P&L:** rebuilt from L, S, cash, fee and cost. Largest gap against NAV is 7e-16.
- **Cash:** rolling it forward alone, as cash x (1 + rf) minus the fee, reproduces NAV - L + S to 1e-15. So no money appears or disappears within the year.
- **Reset:** after each June cost, L = S = cash = NAV, gap 2e-16.
- **Fee:** charged monthly on the drifted short, 11.0% of NAV in total. Costs total 7.0%.
- **Stress and monthly columns:** reproduced to 5e-16.
- **Cash never goes negative,** so no debit balance arises. The lowest is 0.81x NAV.

The project's mechanics test covers only the free monthly case. My rebuild covers the annual path too.

## 2. The drift effect, decomposed

Agent 1's -1.25 is right. It isn't really a residual: the monthly identity below is exact, to 3e-16.

With g = (L + S) / 2 and d = L - S, each as a share of NAV:

excess return = spread - costs - fee at size 1 - fee on extra size + (g - 1) x spread + d x average leg excess return

| Points a year, mean | Full (Dec 2025) | Extended (May 2026) | 2005-15 | 2015-25 |
|---|---|---|---|---|
| Gross Spread | -0.58 | -1.72 | +2.06 | -3.07 |
| Costs on both legs | -0.34 | -0.33 | -0.33 | -0.35 |
| Fee at size 1 | -0.50 | -0.50 | -0.50 | -0.50 |
| Fee on drifted extra size | -0.03 | -0.04 | -0.02 | -0.05 |
| **Size effect:** legs larger than NAV, times the spread | **-0.60** | -0.91 | -0.71 | -0.51 |
| **Net effect:** short exposure, times rising legs | **-0.65** | -0.96 | -0.14 | -1.12 |
| Return above rf | **-2.71** | -4.46 | +0.36 | -5.60 |

**How drift loses money.**
- It is nearly all timing. Average exposures are close to neutral: mean net -0.01, mean g +0.06. The averages alone give only -0.04 and -0.10. Timing gives -0.57 and -0.55.
- When Low beats High, S grows while NAV falls, so the book is largest and most net short just when that continues.
- It is concentrated. The drift effect is -1.29 a year over 20 complete years, and -0.68 without 2019-20 and 2020-21. The annual-monthly gap in holding-year return has mean -1.26 points and median -0.28. It is negative in 14 of 20 years, and worst in 2020-21 (-9.3), 2019-20 (-4.2) and 2017-18 (-3.4). In 2025-26 it is -11.1.

**Is it mechanical?** No. On the placebo, the design costs almost nothing on average:

| CAGR, annual minus free monthly | Mean | 95% range | Actual |
|---|---|---|---|
| Random portfolios | -0.07 | -0.65 to +0.42 | **-1.49** |
| Within-sector portfolios | -0.23 | -0.82 to +0.32 | **-1.49** |

None of the 3,000 draws reached -1.49. So the drift loss isn't a fixed cost of annual resets. It is what a drifting book does on this specific path, where a short leg ran hard against it. Annual reset amplifies a loss that already exists.

### How much the design drives the headline

| Reset, Dec 2025 | CAGR | Mean excess | Volatility | Drawdown | Alpha | t | Max gross | Extended CAGR | Extended alpha (t) |
|---|---|---|---|---|---|---|---|---|---|
| **June only (locked)** | **-1.80** | -2.71 | 12.27 | -75.8 | -4.53 | -1.48 | 5.02 | -3.59 | -5.80 (-1.86) |
| Every 6 months, charged | -1.21 | -2.27 | 10.90 | -71.2 | -3.95 | -1.44 | 2.78 | -2.72 | -5.06 (-1.80) |
| Every 3 months, charged | -0.81 | -1.91 | 10.44 | -69.5 | -3.51 | -1.24 | 2.63 | -2.09 | -4.42 (-1.56) |
| Monthly, charged 10 bp on resize | **-0.42** | -1.53 | 10.41 | -67.5 | -3.00 | -1.06 | 2.00 | -1.55 | -3.78 (-1.35) |
| Monthly, free (published) | -0.31 | -1.42 | 10.41 | -67.0 | -2.89 | -1.03 | 2.00 | -1.44 | -3.67 (-1.31) |

**Plainly:**
- The annual-reset design accounts for 1.38 of the 1.80 points of annual loss, about three-quarters, measured against a charged monthly reset. Of the 1.49-point gap to the free monthly figure, 1.29 is lower average return and 0.21 is more variance drag.
- The design does not create the negative result. CAGR stays below zero, drawdown about -67%, and alpha -3.00%, at every frequency. The charged monthly reset costs only 0.11 a year, so the -0.31% barely overstates what is achievable.

**Which is the fairer description of a 100/100 strategy?** Monthly reset, charged. A book with 226% short and 175% long, as at the start of May 2026, isn't 100/100, and few managers or brokers would let it run to 5x gross. The annual reset is an accurate test of something else: a position opened 100/100 and left alone for 12 months. It also matches the project's buy-and-hold rule and needs no assumed trades.

Annual reset was locked before the run, so it stays as the rule. This is a description of what each number means, and not a recommendation to swap. Both should be read together: "-1.80% with 12-month drift; about -0.4% if held near 100/100".

## 3. The uncharged June resizing

Measured name by name, from dollars held before the reset to dollars required after it.

| | Result |
|---|---|
| Mean charged a year | 34.0 bp of NAV |
| Mean real a year | 37.5 bp of NAV |
| Largest extra | 22.8 bp, June 2021 (52.9 real against 30.1 charged; L 1.95, S 2.39 before reset) |
| Years real cost is lower than charged | 7 of 20 (legs below NAV, so smaller trades) |
| CAGR, charged / real | -1.80 / -1.83 |
| Alpha (t), charged / real | -4.53 (-1.48) / -4.56 (-1.49) |

**Charging it changes nothing that matters.** The sentence in `results.md` explaining why it is uncharged is accurate as to the rule. It should not be read as implying the cost is zero.

## 4. Shorting assumptions

Each is sized in the direction that flatters the strategy now, so that real-world terms would make it worse unless noted. Base: CAGR -1.80, alpha -4.53, t -1.48.

| Assumption replaced | CAGR | Alpha | t | Change in CAGR |
|---|---|---|---|---|
| Cash earns rf - 25 bp | -2.05 | -4.79 | -1.57 | -0.25 |
| Cash earns rf - 50 bp | -2.31 | -5.05 | -1.65 | -0.51 |
| No interest at all on short proceeds (retail-like) | -3.43 | -6.23 | -2.11 | -1.63 |
| Fee 1% | -2.34 | -5.08 | -1.65 | -0.54 |
| Fee 2% (published stress) | -3.43 | -6.18 | -1.98 | -1.63 |
| Fee 5% | -6.68 | -9.57 | -2.93 | -4.88 |
| Fee by short interest: above 20% of shares 5%, above 10% 2%, else 0.5% (average 0.62%) | -1.93 | -4.66 | -1.52 | -0.13 |
| Same: 10%, 3% (average 0.72%) | -2.05 | -4.78 | -1.55 | -0.25 |
| Same: 20%, 5% (average 0.91%) | -2.27 | -5.00 | -1.61 | -0.47 |
| Delisted shorts: no gain in final month | -1.80 | -4.53 | -1.49 | 0.00 |
| Real June trades | -1.83 | -4.56 | -1.49 | -0.03 |
| **Combined moderate:** 1% fee, rf - 25 bp, real June | **-2.63** | -5.37 | -1.74 | -0.83 |

**Reading each one:**
- **Rate on cash:** each 1 point of haircut is about 1 point of CAGR, since cash averages about 1x NAV. A 0.50% fee plus full rf amounts to a rebate of rf - 50 bp on proceeds, which is a plausible large-institution general-collateral rate, in my judgment and not from data. It is out of reach for a retail account, where the -1.63 row applies.
- **Fee:** about 1.09 points of CAGR per point of fee. Flat 0.50% looks reasonable for most of this list. Low names are large, with median short interest 1.6% of shares, and only 6.5% above 10% and 0.8% above 20% (93.4% coverage from `comp.sec_shortint`, others at 0.5%). The tiers are illustrative; I have no borrow-rate data. Recalls and fee spikes during squeezes aren't captured.
- **Delisted shorts at face value:** does not matter. There are 22 Low exits in holding years, and 19 had a final return of zero or above, almost all takeovers. The only large fall is SunEdison (-58.9%), at a very small share of the leg by then. The takeover price rise has generally already hit the short before the final month.
- **Margin: the direction isn't one-way.** Month-end equity/gross is below 40% in 36 months, 30% in 8, 25% in 4, 20% in 1, at lowest 19.9% (main period, corrected 2026-11-01). Starting 100/100 with cash already sits at 50%.

| Forced cut to 2x gross when equity/gross falls below | Calls | CAGR | Alpha (t) |
|---|---|---|---|
| 40% | 10 | -1.22 | -3.74 (-1.35) |
| 30% | 3 (2010-04, 2020-05, 2020-12) | -1.67 | -4.13 (-1.45) |
| 25% | 1 (2021-02) | -2.28 | -4.78 (-1.50) |

Forced cuts sometimes helped by capping the drift and sometimes hurt by selling at the worst point. Results depend on the trigger level and month. Month-end data also misses intramonth breaches, so these are likely fewer than a real account would see.

## 5. The short leg's bad years

**Part real rebound, but mostly not "rebound".** Bad years, with short leg under -25 points: 2009-10, 2010-11, 2013-14, 2014-15, 2017-18, 2019-20, 2020-21, 2025-26.

- In those years Benchmark averaged +25.6%, the median Low stock +26.9%, and Low beat Benchmark by 15.8 points. In other years Low lagged it by 5.7. Part of the short's loss is the rising market, which the long leg offsets.
- Low's prior 12-month return does not predict this. Across years, correlation of Low-minus-Benchmark with Low's prior return gap is +0.14 (n = 20). In bad years Low's prior gap was +0.9 points on average, in others -3.4. Low-minus-Benchmark with its own prior year is -0.14.
- **A true rebound fits 2009-10.** Low was down 36.6% over the prior year, against 27.5% for all names, and 85.7% of Low then rose. It partly fits 2020-21 for names like Ford and Freeport.
- **The others are mostly low-score growth, or sector rallies.** Names with weak accounting scores kept running: biotech in 2014-15 (Incyte, BioMarin, Vertex), growth in 2019-20 (DexCom, DocuSign, Seagen), memory chips in 2025-26. The L/S profitability loading of +0.52 (t 2.89) agrees: it loses when unprofitable stocks rally.

**Concentration varies by year:**

| Holding year | Short leg, points | Top 3 names' share | Names | Effective names at end | Share of Low up | Top names |
|---|---|---|---|---|---|---|
| 2009-10 | -41.5 | 24% | 49 | 43.9 | 86% | SanDisk, Whirlpool, Wynn |
| 2010-11 | -33.7 | 17% | 41 | 40.0 | 95% | El Paso, Concho, Pride |
| 2013-14 | -34.3 | 31% | 39 | 32.6 | 90% | Micron, Cheniere, Tesla |
| 2014-15 | -26.3 | 52% | 23 | 20.8 | 74% | Incyte, BioMarin, Vertex |
| 2017-18 | -28.8 | 36% | 31 | 27.6 | 81% | Netflix, Valero, Twitter |
| 2019-20 | -36.0 | 72% | 20 | 15.6 | 75% | DexCom, DocuSign, Seagen |
| 2020-21 | -65.4 | 24% | 53 | 44.3 | 91% | Freeport, Snap, Roku |
| 2025-26 | -64.1 | 72% | 33 | 15.3 | 79% | Western Digital, Intel, Steel Dynamics |

So the short side is broad in most bad years, and concentrated in 2019-20, 2025-26 and partly 2014-15, when Low's list was small or one name ran far. Low never falls below 20 names, and its largest end-year position is usually 3%-12%, apart from Western Digital in 2025-26.

**Checked:** the top five losers in each of the eight bad years, 40 rows. CRSP and compounded `comp.secm` total returns agree with a median gap of zero and none above 2 points. Whiting needed a different Compustat issue from its latest link, a matter for my check only.

## 6. Significance

**The test itself** on this series (lags 0 / 12 / 24; size checks from 3,000 simulations per row):

| Series | t by lag | Passes 2 with no true alpha | p | Bootstrap implied t |
|---|---|---|---|---|
| Main, 0.5% | -1.87 / **-1.48** / -1.29 | 7.5%-8.6% | 0.18-0.21 | -1.44 |
| Main, 2% | -2.52 / **-1.98** / -1.72 | 6.4%-8.9% | 0.07-0.09 | -1.91 |
| 2015-26, 0.5% | -2.60 / **-2.35** / -2.17 | 8.2%-12.9% | 0.05-0.08 | -2.41 |
| Extended, 2% | -2.91 / **-2.35** / -2.19 | 6.5%-11.7% | 0.03-0.07 | -2.42 |

Unlike long-only High, t here *shrinks* as lags rise, so 12 lags isn't flattering it through lag choice. The size problem remains, so |t| of 2 is more like 2.3-2.5 for 5%. **None of these rows is clearly significant at 5% under all checks.**

**Placebo** (2,000 random shuffles, 1,000 within sector):

| | Actual | Random mean | At or below actual | Past abs. t 2 | Within-sector mean | At or below actual | Past abs. t 2 |
|---|---|---|---|---|---|---|---|
| CAGR, main | -1.80% | +0.53% | 5.4% | | -0.25% | 14.7% | |
| Alpha, main | -4.53% | -0.92% | 0.7% | | -2.38% | 7.8% | |
| t, main | -1.48 | -0.65 | 22.5% | 11.0% | -1.37 | 45.3% | 24.6% |
| Alpha, 2015-25 | -8.68% | -1.00% | 0.05% | | -4.48% | 3.5% | |
| t, 2015-25 | -1.95 | -0.50 | 11.3% | 11.8% | -1.90 | 47.5% | 45.4% |
| Alpha, 2015-26 | -10.31% | -1.07% | 0.05% | | -5.11% | 2.7% | |
| t, 2015-26 | -2.35 | -0.48 | 6.2% | 12.2% | -2.11 | 40.6% | 56.5% |
| Monthly-reset t, main | -1.03 | -0.67 | 37.1% | 11.2% | -1.28 | 61.0% | 20.2% |

**Reading.**
- By t, the result is entirely ordinary for same-sector portfolios: above 40% in each row. Sector exposure of Low and High alone produces a significant-looking t in about half of all draws in the 2015 windows.
- The alpha percentages look far more extreme, because the actual series is unusually volatile. The t adjusts for that, so I'd rely on t. The low alpha shares do mean this path's loss is large in dollars, so it can't be called an average outcome either; it reflects a few wide-loss years.
- With monthly reset, nothing is unusual on either scale.

**The caution line in `results.md`.** It is not clear enough:
- t -2.35 appears twice, for different series: "Long/short, 0.50% borrow, 2015-06 to 2026-05" and "Full period: Long/short, 2.00% borrow stress". The second is not the reported stress t of -1.98. It is June 2005 to May 2026, which includes Compustat months, and the line doesn't say so.
- It cites "about 127 months", while several listed rows have 132.
- It says the testing "was not rerun for the long/short series". This audit has now done it, and the -2.5 to -3.6 range is for long-only High and doesn't carry over.

## 7. 2025-26's -32.65%

| Removed (sensitivity only) | 12-month | Jan-May alone | Free monthly, 12-month | End-April gross | End-April net |
|---|---|---|---|---|---|
| None | **-32.65** | -32.60 | -21.55 | 4.01 | -0.52 |
| Western Digital | -5.49 | -11.57 | -4.16 | 2.80 | -0.15 |
| Western Digital, Intel | +8.98 | -0.50 | +8.03 | 2.37 | -0.02 |
| Micron | -45.22 | -43.71 | -29.94 | 4.30 | -0.66 |
| All three | -3.59 | -9.82 | -2.83 | 2.46 | -0.09 |

**Answer:** almost all of it. Western Digital alone costs 28.2 points of the short leg's -64.05 over 12 months, and Intel 14.7. Jun-Dec is only -0.06% overall, so the year's whole loss falls in the five Compustat months, when the short leg lost 50.9 of its 64.05 points. Prices for these were verified in my post-write-up audit (IBES, secd).

Three things compound here:
- Two long-running winners.
- A short position that grew with them. By end May 2026 Western Digital is 46% of NAV and Intel 26%.
- Annual-reset drift, -11.1 points of the -32.65.

**Effect on the full period:** this one year moves CAGR from -1.80% to -3.59%, and alpha from -4.53% (t -1.48) to -5.80% (t -1.86). That is too much weight on one year and one data source. The December 2025 figures stay the main result, as `results.md` already says.

## Limits

- I have no borrow-rate, recall or margin data. Those rows use assumptions.
- Monthly data misses intramonth margin breaches and price peaks.
- 2026 months can't be checked against CRSP yet.
- The placebo keeps bucket sizes, sectors where stated and buy-and-hold rules, but scores are shuffled independently each year.
- My first run of the cash-rate rows had an error in my own script, an annual haircut applied monthly. It was fixed and rerun. No published number was affected.

## Decisions for the user

None requires a rule change:

1. How to present the headline: my recommendation is to show -1.80% alongside the charged monthly -0.42% and state that one has 12-month drift, up to 5x gross.
2. Whether to state peak leverage in the results: my recommendation is yes, with the end May 2026 position sizes for the extension.
3. Whether to reword the caution line and relabel `drift_and_rounding` as described in sections 2 and 6.

## Final trace of the write-up additions, 2026-11-01

Files: `output/writeup.md` FF9C57FF69E129, `11_long_short.py` 1CBAA49B4E6D69, `config.py` 0880F2C026D5E9, `output/long_short_100_100/results.md` 55B426B77A4D88. Scripts: `verification/audit_32_trace.py`, `audit_33_trace_placebo.py`. Output: `audit_33_output.txt`.

**Result: no mismatches in the write-up additions.** One Low item in `results.md`, and three corrections to my own report.

**1. Figures traced.** Every figure in "Runs after this write-up" and the new Portfolio mechanics bullet agrees with the project's output files or my audits.
- **Extension:** both columns of the table; January-May returns; 29.4, 45.07, 9.06, 15.36; 84.8%, 51.4%, +16.7%, +0.3%; -2.7 to -3.2, about -2; 1.7%, 12.5%; 15,752, 99.96%, 8.4.
- **REIT:** the table; 430 rows (61, 302, 67), 44 companies, 48.1%; 0.9989; 2.75%. I recounted the 211 rows independently, and the 2 REIT rows match `reit_rows_still_unscored.csv`.
- **Long/short:** both tables; 5.0x, -0.70; 243%, 46%; 1.38 of 1.80; -0.92, -2.71, 0.53, 1.25, -0.60, -0.65; -2.11, 56.5%; +9.0%, -3.6%; -3.59; -3.43.
- **Bullet:** 0.35, -0.57%, -2.04%, -0.72, -0.92%, -2.39%, -0.85.

**2. Existing text.** Removing the new section and the one Spread bullet from FF9C57FF, and restoring the file ending, reproduces 2C9015FA9180F5 byte for byte. So nothing else changed from that version, and the answer paragraph stands. As I noted in the post-write-up audit, 2C9015 itself differs from C77BA3D9, the version I last read in full. This trace does not cover that earlier change.

**3. Peak date.** **End of February 2021 is correct, and Agent 1 is right.** Month-end gross is 5.02, long 2.16, short 2.86, net -0.70, equity/gross 19.9%. At end of March 2021 gross is 4.16. My "March 2021" came from a row holding start-of-March balances.

**4. Charged numbers, own engine.** Monthly returns match both charged files to 5e-16.

| | CAGR | Drawdown | Alpha | t |
|---|---|---|---|---|
| Monthly charged, 0.50%, main | -0.42% | -67.5% | -3.00% | -1.06 |
| Monthly charged, 2.00%, main | -1.90% | -73.5% | -4.50% | -1.60 |
| Monthly charged, 0.50%, to May 2026 | -1.55% | -67.5% | -3.78% | -1.35 |
| Monthly charged, 2.00%, to May 2026 | -3.02% | -73.5% | -5.28% | -1.89 |

Charged Spread: main -0.92% a year, alpha -2.39%, t -0.85. To May 2026: -2.06% a year, alpha -3.18%, t -1.13.

**Random-portfolio claims.** The write-up does not apply them to a charged series. One sentence did reach past what I had tested: "neither t of -2.35 is evidence about the F-score". My placebo covered the 0.50% window but not the 2.00% series to May 2026. I have now run it, and **the sentence holds**:

| 1,000 draws each | Actual t | Random mean, share at or below actual, past abs. t 2 | Within-sector mean, share at or below actual, past abs. t 2 |
|---|---|---|---|
| Annual, 2.00%, to May 2026 | -2.35 | -1.63, 25.0%, 37.0% | -2.36, 49.2%, 65.8% |
| Annual, 2.00%, main | -1.98 | -1.74, 40.9%, 39.9% | -2.34, 64.6%, 63.5% |
| Monthly charged, 0.50%, main | -1.06 | -0.70, 35.9%, 11.7% | -1.39, 63.3%, 22.6% |

No write-up change is needed. The 2.00% fee moves shuffled portfolios too, which is why their t is so often past 2.

**Low, `results.md`:** "those tests were not run on the charged series" is now out of date. The charged series is also unremarkable, as the last row shows.

**5. Strength of claims.** Nothing in the new section is stronger than my audits. "No alpha over the main period reaches |t| of 2" is true of the full main period, the sense it is used in. Subperiod rows do reach it, such as the 2.00% annual reset for 2015-25 at t -2.29, and those stay listed in `results.md`.

**Corrections made to this report:**
- Peak date, in the verdict table: end of February 2021.
- Month-end equity/gross counts, section 4: 36, 8, 4, 1 (was 29, 6, 3, 1). My first count used start-of-month balances, which left out each May-end.
- Section 7 table: the gross and net columns are end-April values, now labelled so. End May 2026 is gross 4.33, net -0.53.
