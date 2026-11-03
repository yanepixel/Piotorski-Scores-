# Clean-folder rerun of the v3 pipeline (2026-11-02, after commit 62be518)

Method: the code files (scripts 00-23, config.py, tests, markdown; no data, no outputs) were copied to an empty folder outside the project. All 13 raw WRDS tables were pulled again live (read-only) and scripts 00-15, 16, 18-23 were run in README order (31 steps), including both issuance rules.

Result: every step exited 0. All 44 CSV files under output/spec_v2 and output/spec_v3 are byte-identical to the project's, all cleaned parquet files are byte-identical, and output/writeup.md is byte-identical. Because the raw pulls were repeated, this also shows the pulls reproduce the same downstream numbers on the day.

Limits: it shows the pipeline reproduces from raw pulls the same day; it does not test a different WRDS vintage, and the v1 variants, extension, REIT and 100/100 steps ran on their earlier specifications. Step 17 (the v2 write-up generator) was replaced by 21 and not run. The unit tests were not part of this run.

Addendum (24_hash_raw.py, review item H4): the 13 raw files from this second pull were hashed (SHA-256) against the project's raw files: all 13 are byte-identical (rows and hashes in output/logs/raw_hash_compare_v3.csv; the project's own hashes, sizes, rows and file times are in output/logs/raw_hashes_v3.csv). Not built: hashing inside each pull script at pull time; the recorded hashes are taken after the fact, and the pulls still link and GICS tables separately from the universe pull.
