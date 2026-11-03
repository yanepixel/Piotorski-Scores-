# Piotroski F-score backtest

This repository holds the code, the write-up and summary tables only. Licensed WRDS data is not included, and neither are the detailed files derived from it. Files named in the text but not present here, such as logs and monthly or company-level tables, are produced when you run the scripts with your own WRDS access. A few company-level cells were removed from the published summaries, so a rerun will show more than this copy does. The spec_v2 stock-level files (monthly portfolio returns, exits, turnover, formation lists, scores and the per-company reasons behind the drop counts) are likewise not included; the scripts `12a` to `17` produce them. Some audit reports and their test scripts, named in the included reports, are also not here. Do not commit reruns from a copy of this repository, because a rerun restores detail files and values left out here.

A research test, not a trading system. The universe is the **Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)**. Each May, it asks whether buying the financially strongest companies, measured by the Piotroski F-score (a 0-9 count of financial-health tests), beat an equal-weighted portfolio of the same stocks, and whether any gain survives known factors.

## The answer

No. The headline is **spec_v2**, a re-specification after an external review (income before extraordinary items, a net-issuance test, no 120-day fallback, a 3-day filing buffer, an all-included benchmark, a lag length for the Newey-West standard errors, which allow for returns correlated over time, set by a formula; the Holm adjustment, a correction for looking at several tests at once; and power, the smallest true effect the test would detect 80% of the time). From June 2005 to December 2025, High (scores 8-9) earned +0.08% a year more than an equal-weighted portfolio of every included company after costs (t-stat 0.10, the number of standard errors the estimate sits from zero), with a four-factor alpha, the return left after market, size, value and momentum are removed, of -0.15% a year (t -0.13). Against scored companies only the excess is -0.42%. The test could not reliably detect an edge under 2.13% a year. The one pre-specified test below 0.05 after multiple-testing adjustment is the 2015-25 four-factor alpha (-3.38% a year, adjusted p 0.047, the p-value after the Holm adjustment), which is borderline under one standard-error convention and has the opposite sign in 2005-15, so it is weak evidence only. The first specification (v1) is kept unchanged in `output/archive_v1/`. The full answer, method, limits and the later labelled runs are in [`output/writeup.md`](output/writeup.md).

## What you need

- Python 3.13 and the packages in `requirements.txt`: `pip install -r requirements.txt`.
- A WRDS account with Compustat (company accounts), CRSP (monthly stock prices and returns) and Fama-French (published return factors) access, including the quarterly, monthly-security and company-name tables that `python 00_test_wrds.py` checks. `crsp.msp500list` is expected to print NO ACCESS: S&P 500 membership history is not available, which is why the universe is a market-cap proxy. The data is licensed, so `data/` is not in the repository, and the scripts pull it.

## WRDS login

Passwords are never stored in this project. Save your own login in the PostgreSQL password file:

- Windows: `%APPDATA%\postgresql\pgpass.conf`
- Others: `~/.pgpass`

Scripts use the `PGUSER` environment variable if it is set, otherwise the username from that file's WRDS line, and pass it to `wrds.Connection`. This matters if your computer's username differs from your WRDS one, since `wrds` would otherwise prompt for it and fail when no one is there to answer. Run `python 00_test_wrds.py` first to check your access.

## Run order

Run from this folder, in the order below (the spec_v2 scripts 12a, 12c, 12b are not in numeric order; see the note after the table). All rules are in `config.py`, and `CLAUDE.md` is the brief and the record of decisions.

| Script | What it does | Uses WRDS |
|---|---|---|
| `00_test_wrds.py` | Checks access | Yes |
| `01_build_universe.py` | Builds the 21 yearly lists | Yes |
| `02_pull_data.py` | Pulls fundamentals, filing dates, sectors, returns, benchmarks, factors | Yes |
| `03_clean.py` | Cleans fundamentals and sets availability dates | Yes, company names only |
| `04_scores.py` | Computes F-scores and the hand-check sample | No |
| `05_align.py` | Attaches the score known on each formation date | No |
| `06_portfolios.py` | Builds monthly portfolio returns | No |
| `07_evaluate.py` | Performance, regressions, year-by-year table, charts | No |
| `08_robustness.py` | Reruns with one setting changed each time; pulls quarterly data | Yes |
| `09_reit_liquidity.py` | Labelled variant: REIT liquidity substitute | Yes, first run |
| `09a_extension_pull.py` | Pulls and validates Compustat returns for 2026; maps securities | Yes |
| `10_extension_2026.py` | Labelled extension to May 2026 | No |
| `10a_extension_contributors.py` | Name-level contributors to January-May 2026 | No |
| `11_long_short.py` | Labelled variant: 100/100 long/short | No |
| `12a_spec_v2_pull.py` | spec_v2: pulls income before extraordinary items (`ib`) | Yes |
| `12c_spec_v2_pull_prstkc.py` | spec_v2: pulls stock repurchases (`prstkc`) for the net-issuance test | Yes |
| `12b_spec_v2_scores.py` | spec_v2: scores and lists. Run `python 12b_spec_v2_scores.py` (net rule, primary) and `python 12b_spec_v2_scores.py --rule literal` (sensitivity) | No |
| `13_spec_v2_portfolios.py` | spec_v2: monthly portfolio returns, same `--rule` option | No |
| `14_spec_v2_evaluate.py` | spec_v2: performance, tests, Holm, power, sensitivities, same `--rule` option | No |
| `15_spec_v2_drops.py` | spec_v2: drops by formation date, v1 beside v2 | No |
| `16_spec_v2_numcheck.py` | spec_v2: recomputes the headline numbers with separate code, same `--rule` option | No |
| `17_spec_v2_writeup.py` | spec_v2: writes `output/writeup.md` from the v2 files and records the source of each figure | No |

A script exits with code 1 if one of its checks fails, and most write their outputs first so the failure can be inspected. `11_long_short.py` stops if `10_extension_2026.py`'s output is missing or older than its inputs.

Order for the headline: scripts 00 to 07 give the data, universe and the v1 files that v2 reads; then `12a`, `12c`, `12b` (literal first, then net, because the net report quotes the literal pass rate), `13`, `14`, `16` (each net, then literal), `15`, `17`. `08` to `11` (robustness, REIT liquidity substitute, 2026 extension, long/short) are v1-specification runs: they are **not rerun under v2**, and the write-up labels them that way. `07_evaluate.py` and the other v1 scripts are unchanged and still write the v1 tables, but `output/writeup.md` and `output/checkpoint3_results.md` were moved: the v1 versions are in `output/archive_v1/`, so rerunning `07_evaluate.py` recreates `output/checkpoint3_results.md` in `output/`.

The brief has three stop points for human review (Checkpoints 1, 2 and 3 in `CLAUDE.md`). They were passed for the v1 results. spec_v2 was approved separately by the user as the headline (`CLAUDE.md` section 8f); a rerun does not pause for any of them.

## Where outputs go

| Folder | Contents |
|---|---|
| `data/raw/` | Pulled data, not in the repository |
| `data/clean/` | Universe, cleaned fundamentals, scores, formation lists |
| `output/writeup.md` | The write-up for spec_v2 (the headline): start here |
| `output/archive_v1/` | The superseded first specification's write-up and Checkpoint 3 results, unchanged apart from a note at the top |
| `output/spec_v2/` | spec_v2 tables, reports and checks. In the project folder, `literal_sensitivity/` holds the full run under the literal issuance rule; the public repository carries only its `headline_v2.csv` and `tests_v2.csv` |
| `output/tables/`, `output/charts/` (v1) | The v1 tables and charts, unchanged; the headline is in `output/spec_v2/` |
| `output/logs/` | Row counts, drop reasons and checks for the v1 scripts 00 to 11, and `raw_hashes_added.csv`. The spec_v2 scripts (12a to 17) write their logs and checks into `output/spec_v2/` instead (`pull_*_log.md`, `scores_checks_v2.md`, `portfolio_checks_v2.md`, `report_v2.md`, `drops_summary_v2.md`, `numcheck_v2.md`). In the public repository `output/logs/` holds only `raw_hashes_added.csv`, and of the spec_v2 files named here only `report_v2.md`, `drops_summary_v2.md` and `numcheck_v2.md` are present. |
| `output/robustness/` | Each robustness variant and its report |
| `output/extension_2026/`, `output/reit_liquidity_substitute/`, `output/long_short_100_100/` | Labelled runs, none of them the headline |
| `verification/` | Reports of independent rebuilds and audits. The public repository carries the reports only (some trimmed of company-level values); the rebuild and audit scripts and their data are not in it |

## Raw data is write-once

Files in `data/raw/` are never edited.

- `02_pull_data.py` refuses to run and exits with code 1 if any of its raw files exist.
- `08_robustness.py`, `09_reit_liquidity.py` and `09a_extension_pull.py` reuse their raw file if it exists, without pulling again. `12a_spec_v2_pull.py` and `12c_spec_v2_pull_prstkc.py` refuse to replace theirs.
- All of them replace raw files only if you pass `--overwrite`.

## Later pulls may differ

WRDS revises its data, and recent Compustat rows change most often. `01_build_universe.py` and `03_clean.py` also read WRDS directly on each run. So a later rerun can differ from the stored results even with identical code. For the v1 pipeline (scripts 00 to 11), a rerun on the same data from no data folder, in the order above, reproduced the same data files, tables and charts. Only logs differed: timestamps, appended rows, the row order of one log, and a hand-added note and two date lines in `output/logs/pull_checks.md`. That run used the same machine, saved login and same-day data. Compare with `output/logs/pull_raw_hashes.csv` to see whether the raw data changed.

That clean-copy reproducibility test was done for v1 only. It has not yet been done for the spec_v2 scripts (12a to 17).
