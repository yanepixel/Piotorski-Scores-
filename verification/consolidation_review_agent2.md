# Independent rebuild of the consolidated pipeline's headline (Agent 2, 2026-11-03)

Written for: the master session reviewing the consolidation. Conclusion: my rebuild from raw data reproduces the pipeline's primary (literal-rule) headline and every monthly return I compared, to under 0.001 bp.

## What I built
My own minimal implementation (scratch folder only; no project file edited, no git, no network). Inputs: `data/raw/comp_funda.parquet`, `comp_funda_ib.parquet`, `comp_co_filedate.parquet`, `crsp_msf_v2.parquet`, and `data/clean/universe.parquet` for the formation lists. Rules taken from `output/prereg_main.md`, `CLAUDE.md` 8f-8i and `config.py`; I did not read scripts 05-08.

1. **Signals and score.** Nine signals with `ib` in ROA, CFO and accruals, and in the change in ROA. Zero-debt pass only where dltt and prior dltt are both zero and prior leverage is computable. Literal issuance: pass if `sstk` is null or not positive, so negative passes. A score exists only if all nine signals are computable. Year-over-year comparisons require consecutive fiscal years with gaps of 350-380 days. A flagged stub year is excluded on both sides (the old stub rule, carried over from my spec_v2 rebuild; I did not find it restated in the current docs).
2. **Alignment.** Earliest 10-K filing date + 3 calendar days on or before the formation date, no fallback, latest datadate wins, age at most 18 months. Buckets: High 8-9, Low 0-4, Middle the rest. Benchmark: all included names.
3. **Returns.** Equal weight, buy and hold, pro rata redistribution on exit. 10 bp on turnover (1.0 for the first portfolio, formation-date delisters at 1/N in the target) and 10 bp one-sided on value reinvested after a mid-period exit. Hold-flat: Maxim 2007-11 to 2008-05 and General Growth 2009-05, applied in any series that holds them (the config says "all-included benchmark only"; nothing else stopped the run).
4. **Statistics.** CAGR from 247 monthly returns, mean monthly gap x 12, and a Newey-West t on the mean gap (lag floor(4*(T/100)^(2/9)) = 4, t with T-k = 246 degrees of freedom).

## Numbers beside the pipeline's
| Quantity | Mine | Pipeline (`headline_numbers.csv`) |
|---|---|---|
| High CAGR, net | 12.0025% | 12.0025% |
| Benchmark CAGR, net | 10.7890% | 10.7890% |
| CAGR gap | +1.21% | +1.21% (12.0025 - 10.7890) |
| Mean monthly gap x 12 | +1.4208% | +1.4208% |
| t (lag 4, df 246) | 1.031 | 1.0313 |
| p | 0.303 | 0.3034 |
| Middle / Low / scored-only benchmark CAGR | 11.1525% / 10.8355% / 11.3557% | identical to six decimals |

Monthly returns against `output/core/portfolio_returns.csv`, 247 months each: High net max difference 0.0004 bp, Benchmark net 0.00003 bp, Low 0.0004 bp, Middle 0.0001 bp, scored-only 0.00004 bp, High and Benchmark gross 0.0 bp. No month differs by 0.01 bp.

My own counts: 7,614 scored list rows (of 8,414), 625 High rows.

## Differences
None above rounding. The 0.0004 bp residuals are float-order noise.

## What I could not check
- **Universe.** I read the pipeline's `data/clean/universe.parquet` (membership, formation dates) and did not rebuild the top-500 ranking, the financial and utility exclusions or the permno/permco mapping from raw. A universe error would pass this check unseen.
- **Not compared:** the High-vs-Low alpha and four-factor tests, Holm values, turnover, bucket counts and the net-rule sensitivity. I compared only what the brief listed. I did not open the pipeline's score or list files, so list membership is checked only through the returns.
- **Shared inputs:** my filing dates and fundamentals come from the same raw files as the pipeline, so a raw-data error would be common to both.
- **Overlap with my earlier work:** the engine is my own earlier spec_v2 rebuild, adapted (literal rule, raw `ib` file, hold-flat in all series); it matched Agent 1 then and matches now, which is agreement of two builds, not proof of correctness.
- No scripts of the pipeline were run, and the README run order was not tested.
