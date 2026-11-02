# Piotroski F-score backtest

This repository holds the code, the write-up and summary tables only. Licensed WRDS data is not included, and neither are the detailed files derived from it. Files named in the text but not present here, such as logs and monthly or company-level tables, are produced when you run the scripts with your own WRDS access. A few company-level cells were removed from the published summaries, so a rerun will show more than this copy does. Some audit reports and their test scripts, named in the included reports, are also not here. Do not commit reruns from a copy of this repository, because a rerun restores detail files and values left out here.

A research test, not a trading system. The universe is the **Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)**. Each May, it asks whether buying the financially strongest companies, measured by the Piotroski F-score (a 0-9 count of financial-health tests), beat an equal-weighted portfolio of the same stocks, and whether any gain survives known factors.

## The answer

No. From June 2005 to December 2025, High (scores 8-9) grew 10.91% a year after costs, against 11.35% for the benchmark of all scored companies, and its return left after the six factors (alpha) was -0.78% a year (t-stat -0.71), not distinguishable from zero. This tests large US companies, not the cheap, smaller companies Piotroski studied. The full answer, method, limits and later labelled runs are in [`output/writeup.md`](output/writeup.md).

## What you need

- Python 3.13 and the packages in `requirements.txt`: `pip install -r requirements.txt`.
- A WRDS account with Compustat, CRSP and Fama-French access. The data is licensed, so `data/` is not in the repository, and the scripts pull it.

## WRDS login

Passwords are never stored in this project. Save your own login in the PostgreSQL password file:

- Windows: `%APPDATA%\postgresql\pgpass.conf`
- Others: `~/.pgpass`

Scripts use the `PGUSER` environment variable if it is set, otherwise the username from that file's WRDS line, and pass it to `wrds.Connection`. This matters if your computer's username differs from your WRDS one, since `wrds` would otherwise prompt for it and fail when no one is there to answer. Run `python 00_test_wrds.py` first to check your access.

## Run order

Run from this folder, in numeric order. All rules are in `config.py`, and `CLAUDE.md` is the brief and the record of decisions.

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

A script exits with code 1 if one of its checks fails, and most write their outputs first so the failure can be inspected. `11_long_short.py` stops if `10_extension_2026.py`'s output is missing or older than its inputs.

The brief has three stop points for human review (Checkpoints 1, 2 and 3 in `CLAUDE.md`). They have been passed for this result; a rerun does not pause for them.

## Where outputs go

| Folder | Contents |
|---|---|
| `data/raw/` | Pulled data, not in the repository |
| `data/clean/` | Universe, cleaned fundamentals, scores, formation lists |
| `output/writeup.md` | The write-up: start here |
| `output/checkpoint3_results.md` | Headline results, with terms defined |
| `output/tables/`, `output/charts/` | Headline tables, robustness comparison and charts |
| `output/logs/` | Row counts, drop reasons and checks for each script |
| `output/robustness/` | Each robustness variant and its report |
| `output/extension_2026/`, `output/reit_liquidity_substitute/`, `output/long_short_100_100/` | Labelled runs, none of them the headline |
| `verification/` | Selected reports from independent rebuilds and audits; their scripts and data are not included. The reports call the reviewers Agent 1, Agent 2 and Agent 3, which were separate AI reviewers, and Master, the coordinating AI session |

## Raw data is write-once

Files in `data/raw/` are never edited.

- `02_pull_data.py` refuses to run and exits with code 1 if any of its raw files exist.
- `08_robustness.py`, `09_reit_liquidity.py` and `09a_extension_pull.py` reuse their raw file if it exists, without pulling again.
- All four replace raw files only if you pass `--overwrite`.

## Later pulls may differ

WRDS revises its data, and recent Compustat rows change most often. `01_build_universe.py` and `03_clean.py` also read WRDS directly on each run. So a later rerun can differ from the stored results even with identical code. A rerun on the same data from no data folder, in the order above, reproduced the same data files, tables and charts. Only logs differed: timestamps, appended rows, the row order of one log, and a hand-added note and two date lines in `output/logs/pull_checks.md`. That run used the same machine, saved login and same-day data.
