# Trial count (approximate upper bound)

Prior t-statistics (v1 and v2): about 250, the reviewers' figure and the CLAUDE.md trial log; not re-derivable from the CSVs with a single rule.
v3 adds 108 t-statistics in `tests_v3.csv` (tests x rules x periods x three lag conventions; the same test at three lags is not three independent trials), plus the robustness rows in `robustness_v3.csv` and its exit-rule copy.
Bonferroni-equivalent two-sided 5% critical |t| at 358 trials (normal approximation): 3.81. Read this as a conservative bound.
Only the 3-test primary family has a defensible Holm adjustment. The v2 'family of six' is post-hoc.
