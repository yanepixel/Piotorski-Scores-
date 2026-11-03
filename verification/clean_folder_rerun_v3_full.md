# Second clean-folder rerun of the full v3 pipeline (2026-11-03, after commit 0299084)

Method: code only (scripts 00-30, config.py, tests, markdown; no data, no outputs) copied to an empty folder outside the project; all raw WRDS tables pulled again live (read-only), and the SEC company-facts files for the 250 sampled firm-years downloaded again. 41 steps were run in README order, including the single-vintage pull (12d), both issuance rules, scripts 18-30, the raw-file hash comparison (24), the write-up generator (21) and the unit tests.

Result:
- Steps 00-11, 12a-12c, 12b-23, 25-30, 24 and 21 exited 0. Two steps failed on the first pass and were fixed and rerun: 12d (it wrote its log into an output folder that did not yet exist in a fresh copy; a one-line mkdir was added) and the unit tests (the runner's path syntax, not the tests; run directly, all 9 pass).
- 67 CSV and markdown files under output/spec_v2 and output/spec_v3 were compared with the project's. 64 are byte-identical, including every result table, `output/writeup.md` and `README.md`. The 3 that differ are logs holding pull timestamps and coverage notes added later (`pull_ib_log.md`, `pull_prstkc_log.md`, `single_pull_log.md`), not results.
- Raw files: 13 of 14 are byte-identical across the two independent pulls (including the new CIK file). The 14th, `comp_funda_single.parquet`, differs only in its `pull_stamp_utc` column; all other columns are equal.
- The SEC vintage-check report is identical on a fresh download.

Limits: same-day reproduction only; no different WRDS vintage was tested; the SEC feed could change as filings are amended. The agents' scripts (27-30) were reviewed by running them, not by line-by-line audit.
