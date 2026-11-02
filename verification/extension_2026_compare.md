# Extension to May 2026 cross-check: independent build vs Agent 1

**Result:** the two builds match. No month differs by more than 1 basis point (bp; 1 bp = 0.01%), in any column, so there are no differences to explain.

**Status of this run:** a labelled extension, not the headline. Returns are CRSP through December 2025 and Compustat `trt1m` for January to May 2026. **Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy).

**Files compared:** `output/extension_2026/returns.csv` (SHA-256 starts 891D0994; unchanged at the end) and `results.md` with its tables. My numbers were final before I opened Agent 1's outputs. I did not read `10_extension_2026.py` or its validation outputs.

**Terms:** alpha is the annual return left after six factors. A t-stat beyond about ±2 is conventionally significant. CAGR is compound annual growth.

## 1. Comparison

| Item | Result |
|---|---|
| Monthly net returns, 252 months: High, Middle, Low, Benchmark, Spread, RSP, SPY | Largest gap about 0.000000000002 bp; 0 months over 1 bp |
| Gross returns | Agent 1's file is net only. In 2026 net equals gross in both builds because no cost applies. Earlier months were already compared in `portfolios_compare.md` |
| Security mapping, 364 names | Same gvkey and iid on every name |
| Regressions, 252 months, net: High, Spread, Benchmark, High minus Benchmark | Alpha, t-stat, R² and betas match to rounding |
| 2015-06 to 2026-05 regressions, and the unchanged first subperiod | Match |
| Performance: CAGR, volatility, Sharpe, drawdown | Match |
| Year by year, 21 holding years | Match |
| Hit rate | 11 of 21 in both; same winning years |

## 2. Numbers (net of costs, identical in both builds)

| Portfolio | Jan-May 2026 | CAGR, Jun 2005 to May 2026 | Sharpe | CAGR, headline to Dec 2025 |
|---|---|---|---|---|
| High | +15.36% | 11.44% | 0.63 | 10.91% |
| Middle | +11.12% | 11.58% | 0.67 | 11.26% |
| Low | +45.07% | 12.68% | 0.61 | 10.93% |
| Benchmark | +15.16% | 11.86% | 0.67 | 11.35% |
| RSP | +9.48% | 10.12% | 0.56 | 9.85% |
| SPY | +11.24% | 11.22% | 0.67 | 10.88% |

| Alpha, annual (t-stat) | Headline, to Dec 2025 | Extension, to May 2026 |
|---|---|---|
| High, full period | -0.78% (-0.71) | -0.47% (-0.42) |
| Spread (High minus Low), full period | -2.04% (-0.72) | -2.83% (-1.01) |
| High minus Benchmark, full period | -0.95% (-1.02) | -0.85% (-0.91) |
| Benchmark, full period | +0.18% (+0.25) | +0.39% (+0.59) |
| High, from 2015-06 | -3.83% (-4.10) | -3.25% (-3.16) |
| High minus Benchmark, from 2015-06 | -2.63% (-2.30) | -2.51% (-2.31) |
| Spread, from 2015-06 | -5.72% (-1.49) | -6.79% (-1.84) |

Holding year June 2025 to May 2026: High +28.28%, Middle +21.86%, Low +63.99%, Benchmark +27.09%, RSP +20.34%, SPY +29.82%. High beat the Benchmark, which takes the hit rate from 10 of 20 complete years to 11 of 21.

**Plain reading:** the answer does not change. High still has no significant full-period alpha, and the extended 2015-on High alpha stays negative and beyond |t| = 2. Section 8c's caution on that t-stat applies, and the random-portfolio work behind it was not rerun on this window.

## 3. What to keep in mind about these five months

- **Low's +45% comes largely from two stocks.** On Agent 1's contribution table, Western Digital adds about 18.7 points and Intel about 10.6, together about 29 of Low's 45 points. Western Digital had drifted to a large weight in Low by December 2025. High has the same pattern on a smaller scale: Micron adds about 9.1 of its 15 points. I took these from Agent 1's table and did not recompute them.
- **The audit confirmed Intel's and Micron's prices against IBES,** and all list prices matched. Dividends and spin-offs in those months have no separate check.
- **Five months prove little,** and the row mixes two data sources. Keep the headline as the result of record.

## 4. Events and sensitivity

| Event | Treatment in both builds |
|---|---|
| Hologic, final return April 2026 | High; value spreads pro-rata afterwards |
| Coterra, final return May 2026 | Middle; last month of the holding year |
| Kellanova, delisted December 2025 | No 2026 return; out before January |
| Comcast January 2026, Becton Dickinson February 2026 | Spin-off months used as given; both in Middle |

| Spin-off sensitivity, Jan-May 2026 compound (mine) | Middle | Benchmark |
|---|---|---|
| Use the audit's `secd` returns for both | +0.35 bp | +0.24 bp |
| Comcast up by the 8.43-point worst earlier gap | +2.25 bp | +1.58 bp |
| Becton Dickinson up by the 8.43-point worst earlier gap | +3.03 bp | +2.13 bp |

High, Low and Spread are not affected. These are stress cases and I cannot say which source is right. Agent 1's harsher cases (price-only spin-off months, Hologic and Coterra ±494 bp) also leave High's alpha and the hit rate essentially unchanged.

## 5. Ambiguities and assumptions

- **Mapping:** both builds reach the same line by different routes: mine from the link table, Agent 1's from gvkey with CUSIP or ticker. Five CUSIP differences appear in both: Honeywell, Exxon (now EXXONMOBIL HOLDINGS), DuPont, ONEOK, and Corteva (now named VYLOR INC on its only line). I did not confirm what happened to each in 2026. Their overlap returns match CRSP.
- **Drift:** December 2025 CRSP weights carry over, with no rebalance or cost.
- **End of test:** no June 2026 rebalance and no final selling cost.
- **Second subperiod:** extended to 2026-05 in this run only.

## 6. Limits

- The match is on a shared `secm` file and shared written rules, including the audit's named exits. A shared reading or a data error in that file would not show up here.
- `secm` cannot be compared with CRSP for 2026 until CRSP covers it. It differs at spin-offs and exits in earlier years.
- Earlier rounds showed that two builds can match while sharing an error, so this result shows consistent implementation only.
- No Agent 1 file, `CLAUDE.md`, `config.py`, `data/` or `output/` file was changed.

**Files:** `verify_extension_2026.py`, `compare_labelled_runs.py`, `labelled_runs_compare_raw.txt` and the `ext_*` outputs, all in `verification/`.
