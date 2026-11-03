# Piotroski F-score backtest: write-up

Universe: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy). June 2005 to December 2025 (247 months). Rules are in `output/prereg_main.md`, written and committed before any number here. The earlier specifications are kept only in git history (tag `archive-v1-v2-v3-pre-consolidation`); this pipeline corrects errors found in review and does not search for a better-looking result.

## Answer

**No detectable edge.** Excess return means High's return minus the benchmark's, shown both as the mean monthly gap times 12 and as the gap between compounded annual returns (CAGR).

| Issuance rule | Benchmark | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | Sharpe High / benchmark |
|---|---|---|---|---|---|---|
| literal (primary) | all included (primary) | 12.00% | 10.79% | +1.21% | +1.42% | 0.63 / 0.61 |
| literal (primary) | scored only | 12.00% | 11.36% | +0.65% | +0.92% | 0.63 / 0.65 |
| net (sensitivity) | all included (primary) | 10.62% | 10.79% | -0.17% | -0.04% | 0.59 / 0.61 |
| net (sensitivity) | scored only | 10.62% | 11.35% | -0.73% | -0.53% | 0.59 / 0.65 |

The literal issuance rule is primary because the paper defines it. It was designated primary after the earlier results were known (the literal results already existed as a sensitivity, and the headline sign changes with the rule), so the choice rests on the paper's definition, not on blindness to the outcome; the net rule (sstk minus prstkc) was adopted earlier after seeing a pass rate and is a sensitivity. Both are shown because they give different signs. All-included is the primary benchmark because the brief defines the comparison as the equal-weighted universe; it was chosen after the first results, so scored-only is shown with equal prominence.

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

The 2015-06 split and the earlier family of six were chosen after a large t appeared. They are exploratory only. In that period (net rule) High's four-factor alpha is -3.36% (t -2.67), but the all-included benchmark's own alpha is -1.70% (t -1.88) and High minus the benchmark is -1.66% (t -1.58). Under the literal rule High minus the benchmark in the same period is +0.29% (t 0.15). The earlier 'Holm survivor' (p 0.047) is not presented as inference.

Roughly 250 earlier t-statistics (the reviewers' figure) plus the rows of this run (`output/results/trial_count.md`) give an approximate count of about 385 trials, and a Bonferroni-equivalent critical |t| of about 3.83 (an approximation, not an exact count). No score-isolating test reaches it. No period was held out.

## Transaction costs (High minus all-included benchmark, CAGR gap)

| bps per side | Literal | Net |
|---|---|---|
| 0 | +1.37% | -0.03% |
| 5 | +1.29% | -0.10% |
| 10 | +1.21% | -0.17% |
| 20 | +1.05% | -0.31% |
| 50 | +0.57% | -0.73% |

## 100/100 long-short: an illustration, not a strategy test (`16_long_short.py`, literal rule)

| Variant | CAGR | Volatility | Sharpe | Max drawdown | Peak gross exposure | Peak short / NAV |
|---|---|---|---|---|---|---|
| annual reset, 0.50% borrow (uncapped) | +1.25% | 8.9% | -0.00 | -50.3% | 3.85x | 2.05x |
| annual reset, 2.00% borrow (uncapped) | -0.35% | 9.0% | -0.18 | -58.5% | 3.95x | 2.10x |
| monthly reset, 0.50% borrow (gross exposure reset to 2x each month start) | +1.63% | 8.7% | 0.04 | -44.2% | 2.38x | 1.22x |

Long High and short Low, each equal to NAV at every formation date, costs charged on both legs. Borrow fees are flat assumptions; short availability and recall are not modelled. The uncapped annual-reset versions drift to roughly 4x gross exposure with the short leg above 2x NAV, so their returns are not a realistic account of a fund. The monthly-reset row resets exposure to 2x each month start. None of this is added to the test family.


## Robustness under the final specification (literal rule; `13_robustness.py`)

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

Variants: High = 7-9; market-cap weights; availability at filing date + 30 or 60 days; availability at year-end + 150 or 180 days (filing date ignored, no fallback); firm-years missing some signals kept, scored on the signals available (needs 7 of 9). None is identical to the headline (checked in code). The headline reproduces the literal portfolio exactly. All gaps have |t| below 1.5.


## The five earlier robustness variants, rerun under the final specification (`14_robustness_extra.py`, literal rule)

| Variant | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | t |
|---|---|---|---|---|---|
| headline | 12.00% | 10.79% | +1.21% | +1.42% | 1.03 |
| sector_neutral | 12.61% | 10.79% | +1.82% | +1.80% | 1.33 |
| value_filter_B | 7.92% | 10.42% | -2.50% | -1.16% | -0.51 |
| profitability_screen | 12.20% | 10.66% | +1.53% | +1.71% | 1.21 |
| universe_buffer | 11.99% | 10.89% | +1.10% | +1.34% | 0.94 |
| eight_signal_no_liquidity | 11.83% | 10.79% | +1.04% | +1.25% | 0.91 |

Definitions were locked in config.py before their results were seen. The value-filter High bucket is as thin as 3 names on some dates. The universe-buffer variant reads the buffered universe (`01b_build_universe_buffer.py`; raw CRSP holds only names that were ever in the top 500). None is significant.

## Book-to-market replication-lite (`20_bm_replication.py`, own preregistration `output/prereg_bm.md`)

Inside our 500 names only: top book-to-market quintile, High-score names against that whole quintile. **This is not a replication of Piotroski (2000)**: it excludes the small value firms where he found the effect, and a real replication needs a broad-universe pull that has not been authorised.

| Comparison | Test | Estimate / yr | t | p | Min detectable (80% power) |
|---|---|---|---|---|---|
| High - Quintile | mean | +2.33% | 0.72 | 0.471 | 9.1% |
| High - Quintile | alpha4 | +1.37% | 0.42 | 0.676 | 9.2% |
| High - Low | mean | +0.57% | 0.14 | 0.891 | 11.6% |
| High - Low | alpha4 | -0.32% | -0.07 | 0.941 | 12.2% |

The High bucket has a median of 5 names (17 of 21 dates under 10), and the test can only detect effects of about 9% a year, so it is uninformative rather than a refutation.

## Extension to May 2026 and the REIT substitute (`18_extension.py`, `19_reit.py`; descriptive only)

- Extension (2025 list held to May 2026): High CAGR June 2005 to May 2026 13.39% against the all-included benchmark's 11.29%; High minus benchmark mean gap x12 +2.27% (t 1.47). The 2025 High list under the literal rule is small (33 names).
- REIT substitute (che/lt for the liquidity signal): High CAGR 12.00% without it, 11.43% with it; High minus all-included benchmark mean gap x12 +1.42% to +0.88%. Adding REITs makes High slightly worse against both benchmarks.


## Issuance signal drift and bucket size

The signal pass rate rises over the sample under both rules (literal 8.8% in FY2004 to 37.1% in FY2024; net 45.7% to 84.4%), so High membership clusters in later years. Literal-rule High holds between 14 and 59 names a year (net 46 to 107); thin buckets are noisy. Per-year counts: `output/results/high_count_and_passrate_by_year.csv`.

## What was checked, and what was not

- Independent F-score recomputation from raw Compustat on 400 random firm-years (seed 20261102): see `output/results/numcheck.md`.
- Independent recomputation of gross High and Low returns from raw CRSP for every month: see the same file.
- Signal unit tests with hand-worked numbers and planted bugs: `tests/test_signals.py`.
- Null returns and delistings (`15_null_return_rule.py`): treating the approved no-trade months as exits instead of flat zero, for every portfolio, leaves the headline gap at +1.42% (t 1.03) in both cases; all 191 mid-period exits already carry a recorded delisting return, so Shumway's -30% replacement replaces nothing (`output/results/delisting_check.md`).
- NOT claimed: that every number in every table was recomputed. Middle, RSP, SPY, tracking error, information ratio, factor loadings and subperiod CAGRs are checked only by `11_numcheck_arithmetic.py`, which reads the same portfolio file the evaluator reads (arithmetic, not pipeline). Printed numbers in README.md and this write-up are not machine-checked against the tables (an earlier lenient check was removed because it could not fail).

## Known limits and work not done

Universe, exclusions, the Low bucket, merger years and other data quirks are disclosed in `output/disclosures.md` (carried from the first specification; the reference tables are in `output/reference/`).

- Fundamentals are current-vintage Compustat dated by original filing date; `ib` and `prstkc` came from separate pulls, but a single-vintage pull (`04c_pull_single_vintage.py`) matches them on every cell. Compustat point-in-time testing exists only to FY2014 (98.5% of scores unchanged then); `comp_snapshot` is denied. For FY2015-24 a sample check against SEC as-filed data (`17b_sec_vintage.py`, 119 usable firm-years, simple tag map) found 91.6% of scores unchanged, 5.0% changing bucket (all involving Middle; no High-to-Low jumps; all 26 High stayed High). It is a sample with a lenient tag map and likely overstates presentation-driven revisions, but the exposure is measured and larger than in 2005-15.
- Under the net rule a missing `prstkc` now makes the signal unknown and the firm-year unscorable (prereg D); that sensitivity therefore scores fewer firm-years.
- The literal rule treats a negative `sstk` as no issuance (paper: nothing issued), fixed after an audit found it failing them; all numbers here are from after that fix.
- The extension, REIT variant and 100/100 long-short are descriptive (scripts 18, 19, 16); the 100/100 is an illustration.
- Not done: a full-market book-to-market replication. Raw pulls are hashed after the fact (`21_hash_raw.py`), not inside each pull script.
- This universe (the 500 largest) is not a test of Piotroski's claim, which concerns high book-to-market firms; the paper itself finds the effect weak among the largest firms.

## Conclusion

On the 500 largest non-financial, non-utility US stocks, buying high F-score names shows no detectable edge, and the sign depends on defensible choices (issuance rule, benchmark) that no test here can separate. Costs of realistic size do not change that. An effect of about 4% a year would be needed to show up reliably, so a Piotroski-sized effect is not ruled out. The one earlier significant result is a post-hoc, mostly universe-wide shortfall. Several corrections remain outstanding (listed above).
