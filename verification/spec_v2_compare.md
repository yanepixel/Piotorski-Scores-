# spec_v2 independent rebuild (Agent 2)

Status: the sections from "Inputs and assumptions" to "Issues reported" below are my FIRST build, written before I saw Agent 1's tables. That build had one error (stub handling, see "Comparison with Agent 1") that changed 15 list rows. Its numbers are superseded by the corrected build in the comparison section at the end; where they differ, use the end section. The corrected build changes: firm-years with a consecutive t, t-1, t-2 chain 18,419 (was 18,464), complete scores 14,838 (was 14,875), scored list rows 7,614 (was 7,629), High list rows 1,408 (was 1,409), Mid 5,348, and the primary test results listed at the end. I did not read scripts 04-12, `output/spec_v2/` or `output/tables/`. Scratch code and outputs are outside the project (the session scratchpad: `build.py`, `stats.py`, `a2_*.csv/parquet`).

## Inputs and assumptions (locked by the master, CLAUDE.md 8f)
- Raw: `comp_funda`, `comp_co_filedate` (10K only, earliest per gvkey-datadate), `ff_factors`, `crsp_msf_v2`, `universe.parquet` (included rows). `ib`, `prstkc` and `sstk` come from my own read-only WRDS pull (20,796 rows, matching comp_funda one to one on gvkey-datadate).
- Scores: v1 definitions with `ib` for ROA, CFO and accruals, and DROA. All signals need fiscal years t, t-1, t-2 consecutive (350-380 days apart). Denominators must be > 0. Margin needs sale > 0, liquidity needs lct > 0. Any uncomputable signal drops the firm-year.
- Zero-debt override: dltt = 0 and dltt_{t-1} = 0 (both present) and LEVER_{t-1} computable.
- F_EQ_OFFER = 1 if sstk - prstkc <= 0 (nulls as 0). Literal sensitivity: 1 only if sstk is 0 or null.
- Availability: filedate + 3 calendar days <= formation date; no fallback; falls back to the most recent earlier scored year; age <= 18 calendar months from FYE.
- Buckets High 8-9, Low 0-4, Mid 5-7. Equal weight, buy-and-hold, two-way turnover at 10 bps in the first holding month, first portfolio turnover 1.0.
- Benchmark: all included names (scored and unscored), charged like the buckets. Scored-only benchmark is a sensitivity.
- Mid-period exit: weight is reinvested pro rata; a one-sided 10 bps is charged on the weight reinvested, in the exit month.
- Hold flat at 0%, no charge, in the all-included benchmark only: Maxim 2007-11 to 2008-05 and General Growth 2009-05. Any other held null stops the run (none occurred).
- Formation-date delisters (4 names with no CRSP row in the first month): counted at 1/N in the turnover target, charged as a buy, earn nothing, weight respread free.
- Tests: HAC lag floor(4(T/100)^(2/9)), t(T-k) p-values. Primary: High minus all-included benchmark (raw monthly net excess), and a 4-factor alpha (Mkt-RF, SMB, HML, MOM) of High minus RF. Holm over one family of six (2 tests x full period, 2005-06..2015-05, 2015-06..2025-12). Minimum detectable effect at 80% power, 5% two-sided, uses the HAC standard error and t(T-k) quantiles. Alphas are monthly x 12.
- Choices I made where the spec is silent: the 4-factor alpha is for High less RF (not High less the benchmark), and the six-factor alpha is reported as secondary.

## Scale
- Firm-years 20,796; consecutive t, t-1, t-2: 18,464; complete nine-signal score: 14,875; with a real 10-K filing date: 14,761.
- Uncomputable signals within the consecutive set: ROA 79, CFO 83, DROA 139, accrual 83, leverage 209, liquidity 3,412, margin 141, turnover 139.
- Included list rows 8,414; scored under the net rule: 7,629.
- 247 monthly returns, June 2005 to December 2025 (the 2025 portfolio has 7 months).
- No filing date earlier than its datadate. Exits recorded in net-run portfolios: 553 (across all five portfolios).
- sstk: 109 negative, 899 null; prstkc: 0 negative, 1,172 null. Negative sstk is used as reported.

## F_EQ_OFFER pass rate by fiscal year (complete scored firm-years)
Net rule: 2004 .41, 2005 .51, 2006 .60, 2007 .62, 2008 .67, 2009 .46, 2010 .56, 2011 .65, 2012 .67, 2013 .69, 2014 .71, 2015 .73, 2016 .72, 2017 .76, 2018 .78, 2019 .78, 2020 .71, 2021 .73, 2022 .82, 2023 .83, 2024 .83, 2025 .86; overall .685.
Literal sstk: .09 in 2004 rising to .38 in 2025; overall .21 (the literal rule fails most firm-years).

## Score distribution (list rows, net rule)
0: 2, 1: 9, 2: 57, 3: 183, 4: 607, 5: 1,489, 6: 1,934, 7: 1,939, 8: 1,158, 9: 251.
Literal: 0: 3, 1: 15, 2: 84, 3: 376, 4: 1,150, 5: 1,883, 6: 1,928, 7: 1,570, 8: 565, 9: 55.

## List rows by bucket and formation year
Net rule, High / Low (Mid is 214-270 each year):
2005 78/27, 2006 87/26, 2007 68/23, 2008 59/37, 2009 57/59, 2010 52/66, 2011 109/26, 2012 80/27, 2013 49/56, 2014 64/34, 2015 67/41, 2016 46/64, 2017 65/34, 2018 79/24, 2019 58/25, 2020 47/60, 2021 48/75, 2022 93/29, 2023 47/51, 2024 83/43, 2025 73/31.
Total High 1,409, Low 858. Every bucket has at least 10 names in every year.
Literal rule, High / Low:
2005 43/44, 2006 36/57, 2007 24/56, 2008 21/80, 2009 25/116, 2010 23/88, 2011 59/51, 2012 29/61, 2013 16/110, 2014 23/78, 2015 23/77, 2016 13/107, 2017 24/82, 2018 40/56, 2019 28/59, 2020 14/101, 2021 21/122, 2022 53/55, 2023 31/95, 2024 41/73, 2025 33/60. The literal rule has High below 20 in 2013, 2016 and 2020.

## Performance, net of costs (June 2005 to December 2025)
| Variant | Portfolio | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|---|
| net | High | 10.77% | 16.96% | 0.594 | -45.7% |
| net | Mid | 11.39% | 15.88% | 0.658 | -49.1% |
| net | Low | 10.19% | 18.89% | 0.523 | -56.9% |
| net | All-included benchmark | 10.79% | 16.26% | 0.613 | -50.6% |
| net | Scored-only benchmark | 11.34% | 16.16% | 0.647 | -49.2% |
| literal | High | 11.74% | 18.15% | 0.615 | -45.9% |
| literal | Low | 10.89% | 17.01% | 0.599 | -52.0% |

Average annual two-way turnover (net run): High 1.63, Low 1.70, Mid 0.81, benchmarks 0.36 to 0.37.

## Primary tests (annualised), net rule, HAC automatic lag 4 in all three periods
| Period | T | Test | Estimate | SE | t | p | Holm p | MDE at 80% power |
|---|---|---|---|---|---|---|---|---|
| full | 247 | High less benchmark | +0.10% | 0.76% | 0.13 | 0.900 | 1.000 | 2.13% |
| full | 247 | 4-factor alpha, High | -0.13% | 1.14% | -0.12 | 0.907 | 1.000 | 3.20% |
| 2005-06..2015-05 | 120 | High less benchmark | +1.17% | 1.00% | 1.18 | 0.242 | 0.968 | 2.82% |
| 2005-06..2015-05 | 120 | 4-factor alpha, High | +2.31% | 1.46% | 1.58 | 0.116 | 0.581 | 4.12% |
| 2015-06..2025-12 | 127 | High less benchmark | -0.92% | 1.09% | -0.85 | 0.399 | 1.000 | 3.08% |
| 2015-06..2025-12 | 127 | 4-factor alpha, High | -3.38% | 1.25% | -2.70 | 0.0078 | 0.047 | 3.53% |

Sensitivities (net rule): scored-only benchmark, full period excess -0.39% (t -0.52); 2015-06..2025-12 excess -1.48% (t -1.34). Six-factor alpha: full -0.84% (t -0.74), 2005-06..2015-05 +2.18%, 2015-06..2025-12 -3.79% (t -3.01, p 0.003). HAC lag 12 instead of 4: standard errors fall, giving 2015-06..2025-12 four-factor alpha t -3.72, 2005-06..2015-05 four-factor alpha t 1.98 (p 0.050); full-period t are unchanged in sign and size (excess 0.14, alpha -0.13).

Literal sensitivity (not used to choose): full High less benchmark +1.19% (t 0.86, p 0.39); full 4-factor alpha +0.77% (t 0.53); 2005-06..2015-05 excess +2.50% (t 1.47); 2015-06..2025-12 excess -0.05%, alpha -1.84% (t -0.98). Holm p are 1.0 for the full period and 0.87 to 1.0 for the subperiods. The literal rule's MDEs are 3.9% (excess) and 4.1% (alpha) over the full period.

Reading: no test is significant on the full period. The only Holm-adjusted p below 0.05 is the 2015-06..2025-12 four-factor alpha (adjusted p 0.047, borderline), and it is the second-subperiod result only. The MDEs (about 2.1% and 3.2% a year for the full period) are larger than any full-period estimate.

## Hand checks
Three firm-years were scored by hand from raw values and all three matched the script. The firms, years and signal values are not listed here.

## Issues reported
- Null returns in the benchmark: Maxim Integrated 2007-11..2008-05 and General Growth 2009-05, handled by hold-flat per the master's decision. No other held nulls.
- Four formation-date delisters (one each in 2010, 2011, 2016 and 2017) handled as above.
- Net-rule pass rate (68%) differs from the v1 rate the master quoted (81%) because v1 used the 2% share-growth test; this is expected.
- Not yet done: comparison against Agent 1's tables, which waits for the master's go-ahead.

---

# Comparison with Agent 1's tables (added after the master released them)

Files compared: `output/spec_v2/` (net rule) and `output/spec_v2/literal_sensitivity/`, plus `data/clean/spec_v2/formation_v2*.parquet`. I read Agent 1's CSV outputs and, to trace a difference, one line of `04_scores.py` (the `lag2_ok` definition). I did not otherwise read its scripts.

## Difference found in my first build, and its cause
My first build and Agent 1 differed on 15 list rows (same 15 in the net rule and the literal sensitivity). In each, Agent 1 had no score and I had one. Cause, by name: my own stub handling. In my first build I tested only the gap between consecutive year-end dates, so a short (stub) fiscal year sitting at the t-2 position did not block the comparison. The v1 rule in `config.py` (`STUB_EXCLUSION = "both_sides"`) excludes any year-over-year comparison into or out of a flagged year, and Agent 1 applied it. The cases are 15 company-years where a stub or short fiscal year (273 to 275 days, or a year-end moved by several months) sat at the t-2 position, in fiscal years between 2003 and 2012. In the "stale" cases Agent 1 fell back to an older year that failed the 18-month rule; in the "missing" cases it had no earlier year. I confirmed the stub explanation directly for five of them; for the other ten the pattern matched (`lag2_ok` false, six computable signals) and I did not inspect each one. Agent 1's treatment follows the v1 rule, and I changed my build to match.

The rows involved sit in these formation years: 2006, 2010, 2013, 2014 (two), 2015 (two), 2016 (three), 2017, 2019, 2020, 2021 and 2023. Before the fix the monthly differences over 1 bp were: High, 7 months (June to December 2014, up to 26.9 bp); Middle, 91 months (up to 11.3 bp); scored-only benchmark, 76 months (up to 8.0 bp); the literal Low, 11 months (2006-07 to 2007-05, up to 17.4 bp). Low and the all-included benchmark under the net rule did not differ. These all came from the 15 rows.

## After the fix: everything matches
- Scores and list membership: 8,414 list rows match on formation date and permno in both rules. Zero score differences. Scored 7,614, unscored 800 (Agent 1 labels 750 missing + 50 stale); bucket counts agree for every portfolio and year (net: High 1,408, Mid 5,348, Low 858; literal: High 620, Mid 5,367, Low 1,627).
- Monthly returns, net and gross, 247 months: High, Middle, Low, all-included benchmark and scored-only benchmark. Largest absolute difference is 0.001 bp (net Low); no month differs by more than 1 bp, in either rule.
- RSP and SPY: recomputed from `crsp_benchmarks.parquet` with April 2018 RSP chained; they match Agent 1 to 1e-12 bp.
- Turnover: all 105 portfolio-year values match (largest difference 4e-15). Mid-period reinvestment costs agree, because monthly net returns match to 0.001 bp.
- Annual returns by formation year (compounded, 12 months, plus partial 2025): largest difference 8e-8. Hit rate over the 20 complete years: net 45% (9 of 20) for both builds against the all-included benchmark and 50% against the scored-only benchmark; literal 50% and 50%.
- Headline performance: CAGR, volatility and max drawdown agree to five decimals for High, Middle, Low and benchmark in both rules. Sharpe differs by 0.001 or less (for example High net 0.5917 against my 0.5925). That is a convention difference: I divide mean monthly return over RF by monthly volatility, annualised; Agent 1's number is slightly different, and I did not trace which. It does not affect any test.

## Standard-error convention (the question you asked me to check first)
Both builds use statsmodels OLS with `cov_type='HAC'`, a Bartlett kernel, `maxlags` = floor(4(T/100)^(2/9)) and no small-sample scaling of the covariance (statsmodels' `use_correction` off). Both take p-values from the t distribution with T-k degrees of freedom. Agent 1's `df` column is 246, 242 (alpha, k=5), 240 (six factors, k=7), 119, 115 and so on; mine is statsmodels' `df_resid`, which is the same T-k. The standard errors match exactly (ratio 1.0000 in every row) and so do t and p. So the two follow the same convention, and I believe it follows the spec: `small_sample` says critical values and p-values come from t with T-k df, which both do. What "without a small-sample correction" means here is that neither multiplies the covariance by T/(T-k); the spec does not ask for that scaling, so I read the spec as satisfied. If the master intended that scaling too, it would raise every standard error by about 0.4% to 1.3% (for the full period, sqrt(247/242) = 1.0103 on the alpha, 1.0 on a mean), which changes no conclusion. I would flag this as a wording ambiguity, not a mismatch.

## Primary tests, net rule (corrected build, HAC lag 4 in all three samples; T = 247, 120, 127)
| Period | Test | Estimate (annual) | t | p | Holm p | MDE | Agent 1 |
|---|---|---|---|---|---|---|---|
| full | High less all-included benchmark | +0.075% | 0.099 | 0.921 | 1.000 | 2.13% | identical |
| full | 4-factor alpha, High | -0.148% | -0.131 | 0.896 | 1.000 | 3.19% | identical |
| 2005-06..2015-05 | High less benchmark | +1.13% | 1.133 | 0.259 | 1.000 | 2.82% | identical |
| 2005-06..2015-05 | 4-factor alpha | +2.28% | 1.561 | 0.121 | 0.606 | 4.12% | identical |
| 2015-06..2025-12 | High less benchmark | -0.92% | -0.847 | 0.399 | 1.000 | 3.08% | identical |
| 2015-06..2025-12 | 4-factor alpha | -3.38% | -2.704 | 0.0078 | 0.0470 | 3.53% | identical |

Differences in estimate between the two builds are below 0.001 bp (annual 0.00005%). Sensitivities also match to the displayed digits: scored-only benchmark (full t -0.561, p 0.575), six-factor alpha (full t -0.749; sub1 1.430; sub2 -3.008, p 0.0032), and HAC lag 12 (t, p): High less benchmark full 0.111 (0.912), sub1 1.404 (0.163), sub2 -0.958 (0.340); 4-factor alpha full -0.142 (0.887), sub1 1.944 (0.054), sub2 -3.724 (0.0003). Literal-sensitivity tests match too (for example full excess t 0.858, p 0.392; 4-factor alpha t 0.532, p 0.595; sub1 excess t 1.466, p 0.145; Holm p are 1.0 for the full period and 0.872 for sub1).

Note the corrected build differs from my first one: in the first build the second-subperiod alpha was -3.38% with t -2.70 and the full-period excess was +0.10% with t 0.13. The corrections are the 15 stub rows and are all small.

## Remaining differences and open items
- None above 1 bp, none in t or p.
- Sharpe convention, noted above (at most 0.002).
- Not independently checked: Agent 1's `portfolio_exits_v2.csv` event list (I compared only the effect through returns and turnover) and its `drops_*` tables. Agent 1's `numcheck` and `portfolio_checks` files were not read.
- The pre-fix first build is kept above only as the record of what I wrote before seeing Agent 1's numbers.
