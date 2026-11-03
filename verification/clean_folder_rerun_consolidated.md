# Clean-folder rerun of the consolidated pipeline (2026-11-03)

Method: the code files of the consolidated pipeline (scripts 00-22, config.py, tests, markdown; no data, no outputs) were copied to an empty folder outside the project, with every WRDS table pulled again live (read-only) and the SEC company-facts files for the 250 sampled firm-years downloaded again. 35 steps were run in README order: 00 to 04c, 05 to 08 with both issuance rules, 09 to 22, and the unit tests.

Result: every step exited 0, the unit tests passed (9 of 9), and the headline numbers (`output/core/headline_numbers.csv`, literal and net) are identical to the pre-consolidation project's. Of 36 result CSVs with a counterpart in the old project, 35 have identical numeric columns; the 36th (the REIT table) differs only because its first-specification comparison rows were removed. Nine files have no counterpart under the same name (renamed or new, such as the literal-rule drops tables, which did not exist before because the old drops script ran on the net rule only).

Scope: this run used the code state at commit 196adfc. Wording-level edits made afterwards (README, write-up prose, comments, the sentence in the evaluation report, trial-count text) did not change any CSV; after each edit the stage CSVs were rehashed and compared.

Limits: same-day reproduction only; no different WRDS vintage; the raw REIT pull file was removed in the consolidation (its `che` and `lt` values are identical, cell for cell, to the single-vintage pull); the consolidation was reviewed by three independent reviewers, whose reports are `consolidation_review_agent1.md`, `consolidation_review_agent2.md` and `consolidation_review_agent3.md`.
