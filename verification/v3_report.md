# v3 report: what changed, old vs new, what was not done

Written for: the project owner and the two reviewers who raised the issues. Rules were fixed in `output/prereg_v3.md` (commit 794aa5f) before any v3 number. Nothing is pushed. All figures below are read from `output/spec_v3/` and `output/spec_v2/` as of commit 58398d8.

## Per item

| Item | Status | What changed |
|---|---|---|
| A. Holm family, "survivor" | Done | `18_v3_inference.py`. New primary family of three (High minus benchmark mean; High minus benchmark four-factor alpha; High minus Low four-factor alpha). 2015-05 split and the v2 family of six labelled POST-HOC. The 0.047 is not presented as inference. Trial count stated as an approximate upper bound (~250 earlier + v3 rows, about 360; critical \|t\| about 3.8). |
| B. Headline | Done | README and write-up say "no detectable edge", define excess return, and give both the mean gap x12 and the CAGR gap with Sharpe. Minimum detectable effect and 95% interval are the literal-rule figures. |
| C. Benchmark | Done | Both benchmarks side by side everywhere. All-included stays primary for a reason that does not depend on sign (the brief's equal-weighted universe); stated as set after v1. The -5.29% audit script is `verification/audit_43_v2_audit.py` (already in repo). |
| D. Issuance | Done | Literal paper rule primary (negative `sstk` passes, after an audit found this wrong); net rule a sensitivity; missing `prstkc` is unknown under it; per-year High count and pass-rate table. |
| E. Restated data | Not done | Single-vintage pull not built; FY2015-24 vintage test blocked (`comp_snapshot` denied, sample table ends FY2014); no restatement-resistant sensitivity built. |
| F. Numcheck | Partly | `19_v3_numcheck.py`: 400 random F-scores recomputed from raw Compustat, 400 of 400 agree; gross High and Low returns recomputed from raw CRSP, 247 of 247 months agree for each. Printed-number matching was removed (it could not fail); README and write-up numbers are generated from the CSVs. Old `16_` check unchanged. The "every number recomputed" claim is removed. |
| G. Robustness | Partly | `22_v3_robustness.py`: lag-90 replaced by filing +30/+60 and year-end +150/+180; also 7+ cutoff, cap-weighted, available-signals scoring. Each differs from the headline (checked in code). Sector-neutral, value, profitability, universe-buffer and eight-signal variants not rerun. |
| H1 lag key | Done | Renamed; lags 4, 6, 12 reported side by side. |
| H2 null returns / delisting | Done | `23_v3_null_return_rule.py`: exit rule on all portfolios (gap +1.21% to +1.21%, no change worth reporting); all 191 mid-period exits already have a delisting return, so Shumway -30% replaces nothing. |
| H3 12b run order | Not done | `12b` still reads the literal scores file for a pass-rate figure when present. |
| H4 pulls | Partly | `24_hash_raw.py`: hashes, sizes, rows, times; a second live pull is byte-identical on all 13 files. Hashing is after the fact; links/GICS not pulled in the universe pass. |
| H5 config constants | Done | Guard 20 and 0.975/0.8 moved to config. Not audited: every SPEC_V2 key driving behaviour. |
| H6 `07_evaluate.py` numbers | Done (relabelled) | The v1 audit-simulation text is labelled quoted history; not reproduced. |
| H7 100/100 | Done | `25_v3_long_short.py`, labelled an illustration; exposure peaks shown (up to 3.95x gross uncapped). |
| H8 costs | Done | `20_v3_cost_sensitivity.py`, 0/5/10/20/50 bp. |
| H9 missing signals | Done | Variant `score_on_available_signals` in robustness. |
| H10 B/M replication | Not started | Optional. |
| I. Tests | Done | `tests/test_signals.py`: hand-worked signals, nulls, year gaps, filing dates, five planted bugs; all pass. |
| End-to-end rerun | Done | `verification/clean_folder_rerun_v3.md`: 31 steps exit 0 from fresh copy and fresh pulls; 44 CSVs, cleaned data and write-up byte-identical. Extension and REIT scripts (09-10) still on earlier specifications. |

## Headline numbers, old vs new

| Number | v2 as published | v3 literal (primary) | v3 net (sensitivity) |
|---|---|---|---|
| High CAGR | 10.75% | 12.00% | 10.62% |
| All-included benchmark CAGR | 10.79% | 10.79% | 10.79% |
| CAGR gap vs all-included | -0.04% | +1.21% | -0.17% |
| Mean gap x12 vs all-included | +0.08% (t 0.10) | +1.42% (t 1.03) | -0.04% (t -0.05) |
| Gap vs scored-only (mean x12) | -0.42% | +0.92% | -0.53% |
| High minus benchmark, 4-factor alpha | n/a | +1.06% (t 0.77) | -0.22% (t -0.26) |
| High minus Low, 4-factor alpha | n/a | +0.70% (t 0.36) | -0.11% (t -0.05) |
| High 4-factor alpha (v2 test) | -0.15% (t -0.13) | not a primary test | not a primary test |
| Smallest Holm-adjusted p, primary family | v2 family of six: 0.047 (post-hoc) | 0.91 | 1.00 |
| Min detectable effect (80% power) | 2.13% | 3.9% to 5.4% | 2.1% to 6.1% |
| Sharpe, High / all-included | 0.59 / 0.61 | 0.63 / 0.61 | 0.59 / 0.61 |
| 2015-25 High 4-factor alpha | -3.38% (t -2.70) | -1.41% (t -0.78) | -3.36% (t -2.67), exploratory |
| 2015-25 benchmark's own alpha | -1.70% (t -1.88) | same | same |
| 2015-25 High minus benchmark alpha | n/a | +0.29% (t 0.15) | -1.66% (t -1.58) |

An interim v3 run (before the audit fixes) gave literal 11.74% and +0.95%; the negative-`sstk` fix and the missing-`prstkc` rule changed it. The old-vs-new figures above are the final ones. The reviewer's figure of -0.92% (t -0.85) for High minus benchmark in 2015-25 was not reproduced (mine, net rule: -1.66%, t -1.58).

## What could not be done and why

- FY2015-24 restatement testing: `comp_snapshot` is denied on this account and the sample point-in-time table ends at FY2014. Effect is unmeasured. Bounded only by the FY2005-14 overlap (98.5% of scores unchanged, 0.2% changed bucket, 99.6% of High stayed High).
- A single-vintage pull and same-pass links/GICS pull: would need rewriting the pull scripts and fresh live pulls; not done.
- Held-out period: none exists.
- Extension and REIT runs, and the five v1 robustness variants, remain on earlier specifications.
- Printed-number matching for README: no reliable machine check was built; README numbers are generated.
- Not independently audited: the final state after the last four commits (an auditor reviewed commit 889764b; fixes were then applied by me).

## Conclusion

On the 500 largest non-financial, non-utility US stocks, buying high F-score companies shows no detectable edge. Which side of zero the point estimate falls on depends on defensible choices (the paper's literal issuance rule gives about +1.2% a year compounded against the all-included benchmark; the net rule gives about -0.2%), and none of the primary tests is anywhere near significant (smallest Holm-adjusted p 0.91 under the primary rule). The tests could only reliably detect an edge of roughly 4% a year or more, so Piotroski's own +1.7 point effect is not ruled out. The one earlier significant result (2015-25) was found by a post-hoc split, and most of it is the universe's own weak factor performance. Costs up to 50 bp do not change the picture. Data-vintage exposure after FY2014 is unmeasured. This universe is also not a test of the paper's claim, which concerns high book-to-market firms and is weak among the largest.
