# Trial count (approximate)

Earlier t-statistics (before this specification): about 250, the reviewers' figure; not re-derivable from the CSVs with a single rule.
This run adds 108 t-statistics in `tests.csv` (tests x rules x periods x three lag conventions; the same test at three lags is not three independent trials), plus 26 robustness and replication rows in `robustness.csv` and its exit-rule copy.
Bonferroni-equivalent two-sided 5% critical |t| at 384 trials (normal approximation): 3.83. Read this as approximate: the earlier 250 is not re-derivable.
Only the 3-test primary family has a defensible Holm adjustment. The earlier family of six is post-hoc.
