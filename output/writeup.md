# Piotroski F-score backtest: v3 write-up

Universe: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy). June 2005 to December 2025 (247 months). Rules are in `output/prereg_v3.md`, written and committed before any v3 number. The v1 and v2 results are archived (`output/archive_v1/`, `output/archive_v2/`); v3 corrects errors found in review and does not search for a better-looking result.

## Answer

**No detectable edge.** Excess return means High's return minus the benchmark's, shown both as the mean monthly gap times 12 and as the gap between compounded annual returns (CAGR).

| Issuance rule | Benchmark | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | Sharpe High / benchmark |
|---|---|---|---|---|---|---|
| literal (primary) | all included (primary) | 12.00% | 10.79% | +1.21% | +1.42% | 0.63 / 0.61 |
| literal (primary) | scored only | 12.00% | 11.36% | +0.65% | +0.92% | 0.63 / 0.65 |
| net (sensitivity) | all included (primary) | 10.62% | 10.79% | -0.17% | -0.04% | 0.59 / 0.61 |
| net (sensitivity) | scored only | 10.62% | 11.35% | -0.73% | -0.53% | 0.59 / 0.65 |

The literal issuance rule is primary because the paper defines it (fixed before looking at results); the net rule (sstk minus prstkc) was adopted in v2 after seeing a pass rate and is a sensitivity. Both are shown because they give different signs. All-included is the primary benchmark because the brief defines the comparison as the equal-weighted universe; it was chosen after v1, so scored-only is shown with equal prominence.

## Primary tests (three, Holm-adjusted; full period, HAC lag by formula, t with T-k df)

| Rule | Test | Estimate / yr | t | p | Holm p | Min detectable (80% power) |
|---|---|---|---|---|---|---|
| literal (primary) | (a) High - Benchmark(all included), mean | +1.42% | 1.03 | 0.303 | 0.910 | 3.88% |
| literal (primary) | (b) High - Benchmark(all included), 4-factor alpha | +1.06% | 0.77 | 0.441 | 0.910 | 3.85% |
| literal (primary) | (c) High - Low, 4-factor alpha | +0.70% | 0.36 | 0.716 | 0.910 | 5.36% |
| net (sensitivity) | (a) High - Benchmark(all included), mean | -0.04% | -0.05 | 0.957 | 1.000 | 2.14% |
| net (sensitivity) | (b) High - Benchmark(all included), 4-factor alpha | -0.22% | -0.26 | 0.793 | 1.000 | 2.33% |
| net (sensitivity) | (c) High - Low, 4-factor alpha | -0.11% | -0.05 | 0.961 | 1.000 | 6.06% |

No primary test is close to significant. Piotroski's own +1.7 point effect is inside the range these tests could not rule out.

## The 2015-25 shortfall is mostly the universe's, and the split is post-hoc

The 2015-06 split and the v2 family of six were chosen after v1 showed a large t. They are exploratory only. In that period (net rule) High's four-factor alpha is -3.36% (t -2.67), but the all-included benchmark's own alpha is -1.70% (t -1.88) and High minus the benchmark is -1.66% (t -1.58). Under the literal rule High minus the benchmark in the same period is +0.29% (t 0.15). The v2 'Holm survivor' (p 0.047) is not presented as inference.

Roughly 250 earlier t-statistics plus the v3 rows (`output/spec_v3/trial_count_v3.md`) give an approximate upper bound of about 360 trials, and a Bonferroni-equivalent critical |t| of about 3.8 (a conservative bound, not an exact count). No score-isolating test reaches it. No period was held out.

## Transaction costs (High minus all-included benchmark, CAGR gap)

| bps per side | Literal | Net |
|---|---|---|
| 0 | +1.37% | -0.03% |
| 5 | +1.29% | -0.10% |
| 10 | +1.21% | -0.17% |
| 20 | +1.05% | -0.31% |
| 50 | +0.57% | -0.73% |

## 100/100 long-short: an illustration, not a strategy test (`25_v3_long_short.py`, literal rule)

| Variant | CAGR | Volatility | Sharpe | Max drawdown | Peak gross exposure | Peak short / NAV |
|---|---|---|---|---|---|---|
| annual reset, 0.50% borrow (uncapped) | +1.25% | 8.9% | -0.00 | -50.3% | 3.85x | 2.05x |
| annual reset, 2.00% borrow (uncapped) | -0.35% | 9.0% | -0.18 | -58.5% | 3.95x | 2.10x |
| monthly reset, 0.50% borrow (gross exposure reset to 2x each month start) | +1.63% | 8.7% | 0.04 | -44.2% | 2.38x | 1.22x |

Long High and short Low, each equal to NAV at every formation date, costs charged on both legs. Borrow fees are flat assumptions; short availability and recall are not modelled. The uncapped annual-reset versions drift to roughly 4x gross exposure with the short leg above 2x NAV, so their returns are not a realistic account of a fund. The monthly-reset row resets exposure to 2x each month start. None of this is added to the test family.


## Robustness under the final specification (literal rule; `22_v3_robustness.py`)

| Variant | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | t |
|---|---|---|---|---|---|
| headline | 12.00% | 10.79% | +1.21% | +1.42% | 1.03 |
| high_7plus | 10.59% | 10.79% | -0.20% | -0.11% | -0.15 |
| cap_weighted | 12.30% | 12.20% | +0.10% | +0.55% | 0.29 |
| avail_filing_plus_30 | 12.02% | 10.79% | +1.23% | +1.44% | 1.04 |
| avail_filing_plus_60 | 11.87% | 10.79% | +1.08% | +1.30% | 0.95 |
| avail_datadate_plus_150 | 12.44% | 10.79% | +1.65% | +1.75% | 1.44 |
| avail_datadate_plus_180 | 11.86% | 10.79% | +1.07% | +1.08% | 0.89 |
| score_on_available_signals | 11.86% | 10.79% | +1.07% | +1.27% | 0.95 |

Variants: High = 7-9; market-cap weights; availability at filing date + 30 or 60 days; availability at year-end + 150 or 180 days (filing date ignored, no fallback); firm-years missing some signals kept, scored on the signals available (needs 7 of 9). None is identical to the headline (checked in code). The headline reproduces the v2 literal portfolio exactly. All gaps have |t| below 1.5. Sector-neutral, value-filter, profitability-screen, universe-buffer and eight-signal variants from v1 are not rerun.


## Issuance signal drift and bucket size

The signal pass rate rises over the sample under both rules (literal 8.8% in FY2004 to 37.1% in FY2024; net 45.7% to 84.4%), so High membership clusters in later years. Literal-rule High holds between 14 and 59 names a year (net 46 to 107); thin buckets are noisy. Per-year counts: `output/spec_v3/high_count_and_passrate_by_year_v3.csv`.

## What was checked, and what was not

- Independent F-score recomputation from raw Compustat on 400 random firm-years (seed 20261102): see `output/spec_v3/numcheck_v3.md`.
- Independent recomputation of gross High and Low returns from raw CRSP for every month: see the same file.
- Signal unit tests with hand-worked numbers and planted bugs: `tests/test_signals.py`.
- Null returns and delistings (`23_v3_null_return_rule.py`): treating the approved no-trade months as exits instead of flat zero, for every portfolio, moves the headline gap from +0.95% to +0.96% (t 0.86); all 191 mid-period exits already carry a recorded delisting return, so Shumway's -30% replacement replaces nothing (`output/spec_v3/delisting_check_v3.md`).
- NOT claimed: that every number in every table was recomputed. Middle, RSP, SPY, tracking error, information ratio, factor loadings and subperiod CAGRs are checked only by `16_spec_v2_numcheck.py`, which reads the same portfolio file the evaluator reads (arithmetic, not pipeline). The printed-number match in `19_v3_numcheck.py` is lenient.

## Known limits and work not done

- Fundamentals are current-vintage Compustat dated by original filing date; `ib` and `prstkc` came from separate pulls. Point-in-time testing exists only to FY2014 (98.5% of scores unchanged then); `comp_snapshot` is denied, so FY2015-24 exposure is unmeasured.
- Under the net rule a missing `prstkc` now makes the signal unknown and the firm-year unscorable (prereg D); that sensitivity therefore scores fewer firm-years.
- The literal rule treats a negative `sstk` as no issuance (paper: nothing issued), fixed after an audit found it failing them; all v3 numbers are from after that fix.
- The extension and REIT variant (scripts 09-10) are still on the earlier specifications; the 100/100 long-short is rerun on v3 as an illustration (script 25). Scripts 08 robustness is replaced by 22 for the variants listed above; the rest of the v1 variants are not rerun.
- Not done: single-vintage pull, pull hashing, book-to-market replication. Raw pulls are hashed after the fact (`24_hash_raw.py`), not inside each pull script.
- This universe (the 500 largest) is not a test of Piotroski's claim, which concerns high book-to-market firms; the paper itself finds the effect weak among the largest firms.

## Conclusion

On the 500 largest non-financial, non-utility US stocks, buying high F-score names shows no detectable edge, and the sign depends on defensible choices (issuance rule, benchmark) that no test here can separate. Costs of realistic size do not change that. An effect of about 4% a year would be needed to show up reliably, so a Piotroski-sized effect is not ruled out. The one earlier significant result is a post-hoc, mostly universe-wide shortfall. Several corrections remain outstanding (listed above).
