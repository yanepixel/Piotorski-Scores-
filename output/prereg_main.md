# prereg_main: decisions fixed before any v3 run (dated 2026-11-02)

_Consolidation note: this is the decision record as written; "v1", "v2" and "v3" refer to the earlier specifications kept in git history (tag archive-v1-v2-v3-pre-consolidation). Script and file names below were updated to the single pipeline (see README.md and verification/consolidation_report_agent.md)._

Status: written and committed BEFORE any v3 number was produced. v1 and v2 outputs are archived, not deleted. Where a choice was needed, the rule is: take the Piotroski (2000, published 2002) definition, else the conservative option. No choice below was made by looking at returns or t-statistics. Known prior knowledge, stated for honesty: the v1 and v2 results are already seen, so v3 is a correction of errors, not a fresh blind test.

## A. Inference family
1. The 2015-05 split and the family of six in v2 were fixed after v1 showed t -4.10. They are labelled POST-HOC and exploratory. The words "pre-specified" are removed for them. The 0.047 is not presented as inference.
2. New primary family (fixed here, three tests, Holm-adjusted, alpha 0.05): (a) High minus all-included benchmark, raw monthly mean; (b) High minus all-included benchmark regressed on Mkt-RF, SMB, HML, MOM (intercept); (c) High minus Low regressed on the same four factors. Reason: they isolate the score from the universe's own factor tilt; High-minus-Low is the paper's own construct.
3. Report the real trial count (re-counted from the trial log, about 250 t-statistics before v3 plus all v3 tests) and the Bonferroni-equivalent critical |t| for that count.
4. Subperiod and 2015-25 results stay as exploratory tables only.

## B. Headline wording
State both the mean monthly gap times 12 (arithmetic) and the compounded gap (CAGR difference), with "excess return" defined in the same sentence; Sharpe beside it. "No." becomes "no detectable edge", with the minimum detectable effect (2.13% a year, 80% power) and the 95% interval (-1.42% to +1.57%), noting it contains Piotroski's +1.7 point effect.

## C. Benchmark
Both benchmarks are shown side by side everywhere. Primary stays all included names, for a reason independent of sign: the brief defines the comparison as the equal-weighted universe, and the scored-only set is defined by the strategy's own data availability. The scored-only comparison is given equal prominence. The audit script that produced the -5.29% unscored-names figure is brought into the repo.

## D. Equity issuance
Primary = the paper's literal rule: EQ_OFFER = 1 if no common equity issued (sstk not positive; sstk missing is read as none, as in the paper's Compustat convention). Net rule (sstk - prstkc <= 0) becomes a labelled sensitivity; in it a missing prstkc is UNKNOWN (signal missing, flagged), not 0. Add a per-year table of High count and signal pass rate.

## E. Restated data
Pull all inputs of a score in one pull with one stamp. Extend the vintage check to FY2015-24 only if an as-first-reported source is readable; if none, say so, bound the effect from the FY2005-14 overlap, and add a sensitivity using only inputs less prone to restatement (cash-flow and balance-sheet items, no accruals built from restated income).

## F. Numcheck
Rewrite so it recomputes F-scores independently from raw pulls on a random sample (seed fixed here: 20261102), recomputes portfolio returns for sample months from raw CRSP returns, covers every table row, and matches every number in writeup.md and README.md to the CSVs exactly. The "every number" claim is rewritten to what is checked.

## G. Robustness
Rerun 08-11 under the final spec. Replace lag_90_days with lag 150, lag 180 and filing-date-plus-N (N = 30, 60). Check no row is identical to the headline.

## H. Smaller items
1. Rename newey_west_1994_automatic to hac_lag_formula_floor_4_T_over_100_pow_2_9; report lags 4, 6, 12 side by side.
2. Null-return rule applied to both sides (a held name with a null return is held flat for the portfolio and for the benchmark when it is in the benchmark); add a Shumway delisting-return sensitivity (missing performance-related delisting return = -30%, as Shumway 1997).
3. 12b independent of existing output files.
4. Hash and timestamp every live pull; pull links and GICS with the universe; prove reproducibility by two pulls compared.
5. Every SPEC key drives behaviour or is deleted; constants moved to config.
6. Hard-coded numbers in the old evaluate script removed or reproduced.
7. The 100/100 long-short is relabelled an illustration; leverage capped at 2x gross in a sensitivity.
8. Transaction-cost sensitivities 5, 20, 50 bp beside 10 bp.
9. Missing-signal firm-years kept with the score on available signals, labelled sensitivity.
10. Book-to-market replication: optional, separate, own pre-spec, not part of this run.

## I. Tests
Unit tests on hand-worked synthetic data for each signal, nulls, fiscal-year gaps and lags, plus planted-bug tests.

## Stop conditions
Anything that needs WRDS access we do not have is reported as not done. Nothing is pushed.
