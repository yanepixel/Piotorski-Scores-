# Robustness cross-check: independent rebuild vs Agent 1

**Result:** the two builds match on all 9 variants and the headline. No month differs by more than 1 basis point (bp; 1 bp = 0.01%), so there are no differences to explain, and both versions follow config equally on everything compared.

**Separate problem found:** `output/writeup.md` overstates the headline alpha in three places. The correct figure is **-0.78% a year, t -0.71**, not -0.80%, t -0.72. See section 3.

**Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy). **Period:** June 2005 to December 2025, 247 months; the 2025 portfolio is partial.

**Terms:** alpha is the annual return left after the six factors. A t-stat beyond about ±2 is conventionally significant. Sharpe is excess return per unit of risk.

## 1. Comparison

Compared for the headline and each of the 9 variants:

| Item | Result |
|---|---|
| Membership by formation date | Identical on every date (7,571 list rows in most variants; see table below) |
| Bucket and score for each list row | 0 differences |
| Monthly gross and net returns: High, Middle, Low, Benchmark | Largest gap about 0.000000000002 bp, which is rounding noise; 0 months over 1 bp |
| Turnover, 84 values per variant | 0 differences |
| Full-period High and Spread alpha and t-stat, excess return, Sharpe, CAGR | Match to at least 7 decimals |
| Subperiod High alpha and t-stat | Match to at least 6 decimals |

List rows that differ from the headline's 7,571: `value_filter_B` 2,523, `eight_signal_no_liquidity` 8,212, `universe_buffer` 7,469, `profitability_screen` 6,582.

## 2. Results (net of costs, identical in both builds)

| Variant | High alpha | t | High minus Benchmark, annual | High Sharpe | Spread alpha | t |
|---|---|---|---|---|---|---|
| Headline | -0.78% | -0.71 | -0.29% | 0.60 | -2.04% | -0.72 |
| High cutoff 7+ | -0.22% | -0.30 | +0.09% | 0.65 | -1.48% | -0.60 |
| Value filter (version B) | -0.87% | -0.46 | +0.21% | 0.51 | -1.79% | -0.46 |
| Cap-weighted | -0.78% | -0.54 | -0.99% | 0.63 | -4.03% | -1.36 |
| Sector-neutral | -0.48% | -0.55 | -0.18% | 0.61 | -1.53% | -0.71 |
| Fallback lag 90 days | -0.78% | -0.71 | -0.29% | 0.60 | -2.04% | -0.72 |
| Cost 25 bps | -1.02% | -0.94 | -0.48% | 0.59 | -2.02% | -0.72 |
| Eight signals, no liquidity | -0.97% | -0.90 | -0.11% | 0.59 | -1.87% | -0.68 |
| Universe buffer | -0.72% | -0.64 | -0.33% | 0.61 | -1.49% | -0.56 |
| Profitability screen | -0.78% | -0.70 | -0.03% | 0.61 | -0.87% | -0.32 |

| Variant | High alpha 2005-06 to 2015-05 (t) | High alpha 2015-06 to 2025-12 (t) |
|---|---|---|
| Headline | +2.48% (+1.76) | -3.83% (-4.10) |
| High cutoff 7+ | +1.72% (+1.89) | -2.10% (-2.61) |
| Value filter (version B) | +3.24% (+1.37) | -5.10% (-2.68) |
| Cap-weighted | -0.10% (-0.07) | -1.66% (-0.87) |
| Sector-neutral | +1.68% (+1.51) | -2.88% (-3.36) |
| Fallback lag 90 days | +2.48% (+1.76) | -3.83% (-4.10) |
| Cost 25 bps | +2.23% (+1.57) | -4.10% (-4.45) |
| Eight signals, no liquidity | +2.30% (+1.68) | -4.04% (-4.33) |
| Universe buffer | +2.38% (+1.56) | -3.59% (-3.41) |
| Profitability screen | +2.68% (+1.94) | -3.99% (-4.17) |

**Plain reading:** no variant gives a positive full-period alpha for High, and none is significant in either direction. Every variant is negative in 2015-25, and all but the cap-weighted one reach |t| above 2. Section 8c's context on the -4.10 t-stat applies to these subperiod figures too.

The lag-90 variant matches the headline on every list row and month, so this fallback setting has no effect on results.

## 3. The headline alpha discrepancy

**`output/tables/factor_regressions.csv` holds -0.007780 (-0.78% a year), t -0.7146, for High, net, 247 months.** Its value is correct: my separate rebuild gives -0.007780 and t -0.714574, and Agent 1's new robustness table agrees. The correct rounding is -0.78%, t -0.71.

| Location | States | Status |
|---|---|---|
| `output/writeup.md` line 9 | -0.8%, t -0.72 | t is wrong |
| `output/writeup.md` line 65 (results table) | -0.80%, t -0.72 | Both wrong |
| `output/writeup.md` line 75 | -0.8%, t -0.72 | t is wrong |
| `output/writeup.md` line 93 (robustness table) | -0.78%, t -0.71 | Correct, so the write-up disagrees with itself |
| `output/checkpoint3_results.md` lines 9 and 136 | -0.8%, t -0.72 | t is wrong |
| `verification/data_audit_phase4_6.md` lines 20 and 46 | -0.8%, t -0.72 | t is wrong (line 57 has t -0.71) |

**Likely cause:** rounding an already rounded number. `checkpoint3_results.md` line 70 shows alpha -0.008 and t -0.715. From those, -0.008 becomes -0.80% and -0.715 rounds to -0.72, while the unrounded values give -0.78% and -0.71. I inferred this from the numbers and did not trace how the text was written.

**Effect:** no conclusion changes, and the error is 0.02 percentage points of alpha. The write-up should still be corrected, since a reader can see two figures for the same number. I changed none of these files. The audit's wording is carried into the write-up through section 8c, so correcting the quoted t there may need the coordinator's or the user's sign-off.

## 4. Comverse effect

Comverse Technology stopped trading in February 2007 while held in the universe buffer's 2006 list (Middle and Benchmark). The locked rule holds it flat for February to May 2007 and counts it as sold at its last value at the 2007 rebalance. The comparison case treats it as an exit in February 2007, spread pro-rata.

| Month | Middle: hold minus exit | Benchmark: hold minus exit |
|---|---|---|
| 2007-02 | +0.22 bp | +0.16 bp |
| 2007-03 | -0.53 bp | -0.30 bp |
| 2007-04 | -1.52 bp | -1.03 bp |
| 2007-05 | -1.28 bp | -0.91 bp |
| 2007-06 (through the turnover charge) | -0.01 bp | -0.02 bp |
| Holding year June 2006 to May 2007 | 22.47% vs 22.51% | 22.21% vs 22.24% |
| Full-period CAGR | -0.16 bp | -0.11 bp |

High and Low are unaffected. It is one name out of 221 in Middle and 331 in Benchmark that year; my earlier message estimated about 260 for Middle, which was wrong. The hold-flat rule lowers these returns slightly because the frozen weight earned nothing in months when the rest of the portfolio rose.

## 5. Limits

- **The match is not fully independent.** I did not read `08_robustness.py`, but most ambiguous choices were locked in config during my build, or taken from an approved rule, so the two builds were following nearly the same instructions. I also adopted Agent 1's turnover treatment after seeing it in the Phases 4-6 comparison. An exact match shows consistent implementation; it does not test the rules, the data or whether the variants are the right tests.
- **Earlier runs differ by design.** My rank-percentile run is kept in `robust_run1_rank_percentile/`. It used a version B rule that the coordinator replaced, and is not current.
- **Currency in the quarterly screen:** earnings are summed as reported, and I did not check for a currency change within a name's four quarters.
- **Not compared:** Agent 1's `thin_buckets.csv`, `robustness_report.md` text and `portfolio_exits.csv`.

## 6. Files

In `verification/`: `verify_robustness.py`, `compare_robustness.py`, `robustness_compare_raw.txt`, and the `robust_*` outputs. No Agent 1 file, `CLAUDE.md`, `config.py`, `data/` or `output/` file was changed.

---

## Update, 2026-11-01: version B float rounding fix

**This section supersedes the version B figures above.** Sections 1 to 6 are kept as the first-run record.

**Result:** after both builds moved to the exact 2/3 point, version B matches exactly at 2,530 list rows, and the other 8 variants and the headline are still matched. No month differs by more than 1 bp in any variant.

**Files compared:** `data/clean/formation.parquet` (F19F0A0A), `output/robustness/value_filter_B/portfolio_returns.csv` (70F006A4), `output/tables/robustness_comparison.csv` (1D29269B), `output/tables/robustness_subperiods.csv` (BE9BEFD1). I did not read Agent 1's fix.

**The problem:** computing the point as `1 - 1/3` in floating-point arithmetic can land just above a company's book-to-market when that company sits exactly on the 2/3 point. It then fails "at or above". Both builds had this problem, so the first comparison matched at 2,523 rows while both were 7 rows short. My script now finds the position in exact fractions.

**The 7 names restored:**

| Date | Company | Bucket |
|---|---|---|
| 2007 | Coventry Health Care | Middle |
| 2008 | Bath & Body Works | Middle |
| 2014 | Constellation Brands | Middle |
| 2016 | Target | High |
| 2021 | Cerner | Middle |
| 2023 | AMD | Middle |
| 2025 | TransUnion | High |

The list matches my earlier rank-percentile run exactly, and matches `in_version_b` in the new `formation.parquet`.

| Version B, net | Before (2,523 rows) | Now (2,530 rows) |
|---|---|---|
| High alpha, full period (t) | -0.87% (-0.46) | **-1.11% (-0.59)** |
| High alpha, 2005-06 to 2015-05 (t) | +3.24% (+1.37) | +3.24% (+1.37) |
| High alpha, 2015-06 to 2025-12 (t) | -5.10% (-2.68) | **-5.51% (-2.91)** |
| High minus Benchmark, annual | +0.21% | **-0.00%** (-0.002%) |
| High Sharpe | 0.51 | 0.50 |
| Spread alpha (t) | -1.79% (-0.46) | -2.03% (-0.53) |

Agent 1's reported figures are confirmed. The first-decade alpha does not move because neither High name falls in that period.

**Other variants:** my summary figures changed only for `value_filter_B`. Membership, buckets, scores, monthly returns, turnover, alpha, t-stats and subperiods still match Agent 1's for all 10 runs. The Comverse figures in section 4 are unchanged.

**What this adds for readers:**
- **Thin bucket:** adding just two names to a thin High bucket (8 names in 2016) moved the full-period alpha by 0.24 percentage points and took High minus Benchmark from +0.21% to about zero. Treat version B as fragile.
- **Timing:** this fix came after variant returns had been seen. It restores the approved rule, moves no conclusion (still not significant over the full period), and made the result slightly worse for High. The timing should still be disclosed. Any write-up text quoting the old version B figures needs updating; I did not check `output/writeup.md` for this.
- **The match:** the first comparison's exact match did not catch this, because both builds shared the same error. An exact match between builds is not proof of correctness, which supports the limit stated in section 5.

**Runs on record:** `robust_run1_rank_percentile/` and `robust_run2_float_quantile/`. Top-level `robust_*` files are now current. Comparison output is in `robustness_compare_raw_v2.txt`.
