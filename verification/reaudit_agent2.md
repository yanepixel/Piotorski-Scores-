# Re-audit: can a clean clone reproduce the first v1 commit?

Report only. Written for the user and the coordinator. Date: 2026-11-01.

**Answer:** the numbers reproduce, but the documented run order does not work on a clean clone. Script 10 fails because its raw file comes from a helper outside the numbered order. With that helper added, all scripts exit 0, all 15 data files match the project's by hash, and every result table and chart reproduces. Only logs, timestamps, row order and one file-count sentence differ.

**The open item is settled.** The final wording of `output/long_short_100_100/results.md` comes from `11_long_short.py`. It regenerates byte for byte except for one count: 164 files hashed, where the commit says 163. The extra file is `.gitignore`, created after that run.

## Method

- The first v1 commit, cloned to my session scratch folder, outside the project, with no `data/` folder at the start.
- Each script ran by full path with the clone as its working folder.
- **Pass 1:** 01 to 11 in the numbered order.
- **Pass 2, same clone:** the helper `output/extension_2026/stage1_validate.py`, then 10, `check_contributors.py` and 11.
- **Pass 3, new clone:** 01 to 08, the helper, 09, 10, `check_contributors.py`, 11.
- WRDS use was only what these scripts already pull. `00_test_wrds.py` and the `verification/` scripts were not run.

**A slip on my side:** in pass 1, my command to change into the clone failed, so the wrapper process started from the real project folder. The wrapper passed the clone as each script's working folder, and its log confirms that. Afterwards I checked the real project: all 15 `data/` hashes are unchanged, and no tracked file changed. The only new files there are other agents' audit files.

## Exit codes

| Script | Pass 1 | Pass 3 | Note |
|---|---|---|---|
| 01_build_universe | 0 | 0 | Pulls from WRDS |
| 02_pull_data | 0 | 0 | Pulls from WRDS; creates `data/raw` |
| 03_clean to 07_evaluate | 0 | 0 | |
| 08_robustness | 0 | 0 | Pulls quarterly data |
| `stage1_validate.py` (not numbered) | not run | 0 | Pulls `comp_secm_extension.parquet` |
| 09_reit_liquidity | 0 | 0 | Pulls `che` and `lt` |
| 10_extension_2026 | **1** | 0 | Pass 1: `FileNotFoundError` on `data/raw/comp_secm_extension.parquet` |
| `check_contributors.py` (not numbered) | not run | 0 | |
| 11_long_short | **0** | 0 | Pass 1 exit 0 relied on the committed `output/extension_2026/returns.csv` |

`.gitignore` removes nothing a script cannot regenerate, apart from the gap in finding 1. No numbered script needs a `verification/` file; those names appear only in report text.

## Comparison with the commit

138 tracked files under `output/`, compared by git's content hash and by raw bytes. Pass 3 differences:

| File | Type | Cause |
|---|---|---|
| `output/logs/pull_log.csv` | Timestamp | The script appends 7 rows on every run |
| `output/logs/pull_runs.csv` | Timestamp | The script appends 1 row on every run |
| `output/robustness/pull_log_quarterly.csv` | Timestamp | Pull time only; row counts and dates match |
| `output/logs/universe_removed_stopped_trading.csv` | Ordering | Same 727 rows when sorted; WRDS returned them in a different order |
| `output/logs/pull_checks.md` | Timestamps, plus stale text | Times change. Two lines also differ because the committed log predates a config change: it says the last subperiod ends 2026-05-31 and is "NOT covered", while the current config gives 2025-12-31, "covered" |
| `output/long_short_100_100/results.md` | One count | 164 vs 163 files hashed, see below |

**Line endings:** `check_contributors.py`, `stage1_validate.py` and `output/writeup.md` also differ in raw bytes between the clone and the real working copy. Git shows no content change, so I read this as line endings only under `core.autocrlf=true`; I did not inspect those files byte by byte.

**Everything else matches:** all tables, regressions, return series, year-by-year files and charts across 01 to 11. All 15 `data/` files in clone 1 (pass 2) match the real project by hash; I ran that hash check on clone 1 only. No tracked file outside `output/` changed.

### The `results.md` count

- `11_long_short.py` counts project files, including those in the top folder.
- `.gitignore` is dated 3:09:56 PM and `results.md` 3:09:51 PM, so `.gitignore` did not exist during that run.
- A recount on the clone gives 164 with `.gitignore`, and 163 without it follows from that.
- **Pass 1 matched byte for byte only by coincidence.** `.gitignore` added one file and the missing `comp_secm_extension.parquet` removed one.

### The REIT `results.md` count

- `09_reit_liquidity.py` also counts files. In pass 1 it reads 128 against the commit's 129, because the Compustat file was not there yet.
- With the helper before 09 (pass 3), the file is byte-identical. This shows the original order had the helper before 09.

## Could a stranger follow the docs?

| Item | Documented? | Evidence |
|---|---|---|
| Requirements and versions | **No** | No `requirements.txt` or README. This run used Python 3.13.2, pandas 2.2.3, numpy 2.5.4, statsmodels 0.15.0, matplotlib 3.11.2, pyarrow 26.0.0, wrds 3.5.0 |
| Run order, 00 to 08 | Yes | `CLAUDE.md` section 5 |
| Run order, 09 to 11 and helpers | **No** | Section 8d describes the runs but names no scripts or order. `CLAUDE.md` does not mention `stage1_validate.py` |
| Which scripts re-pull data | **Partly wrong** | The `.gitignore` comment names 02, 08 and 09, not the helper. It also omits 01's own WRDS use |
| "Runnable in order from a fresh `data/`" | **Not true as stated** | `CLAUDE.md` section 6 item 1; see finding 1 |
| WRDS username | Partly | `CLAUDE.md` section 9 and the scripts handle `PGUSER` or `pgpass.conf`. `00_test_wrds.py`, the first script a stranger would run, calls `wrds.Connection()` with no username. In a non-interactive session that fails with `EOFError`, as my first call did here |
| WRDS access needed | Partly | Section 3 lists tables, not that the raw data is licensed and absent from the repo; only a `.gitignore` comment says so |

## Findings

### MUST FIX

1. **The numbered order fails from a clean clone.** `10_extension_2026.py` needs a raw file that only `output/extension_2026/stage1_validate.py` pulls. That helper is unnumbered, sits in an output folder and is undocumented. This contradicts `CLAUDE.md` section 6 item 1.
2. **No reproduction instructions exist.** There is no requirements file and no complete run order. A stranger has no way to find the steps for 09 to 11 and the two helpers. The order that works is: 01 to 08, `stage1_validate.py`, 09, 10, `check_contributors.py`, 11.

### SHOULD FIX

3. **`11_long_short.py` hides an upstream failure.** With 10 failed, it exited 0 using the committed `returns.csv`. A full run can therefore look clean while part of it rests on old output.
4. **Two `results.md` sentences depend on what is in the folder.** The counts in `09_reit_liquidity.py` and `11_long_short.py` change with unrelated files, as `.gitignore` did. The committed long/short file does not regenerate byte for byte for this reason.
5. **`output/logs/pull_checks.md` is stale against the current config.** It still says "NOT covered" for a date the config no longer uses. No result is affected, but a reader of the log would be misled.
6. **`00_test_wrds.py` does not follow section 9's username rule.** It works only when the Windows and WRDS usernames match, or with a person at the prompt. Its comment does tell the user to expect a prompt.
7. **The `.gitignore` comment lists the wrong re-pull scripts.** It should agree with the run order.

### OPTIONAL

8. **Append-only logs dirty the tree.** `pull_log.csv` and `pull_runs.csv` grow on every run, so a clean rerun never matches the commit.
9. **Row order in `universe_removed_stopped_trading.csv` isn't fixed.** Sorting it would remove a harmless difference.
10. **Timestamps in `pull_checks.md` and `pull_log_quarterly.csv`** always change a hash. Either expect this in the docs or exclude them from comparisons.
11. **No `.gitattributes`.** Raw hashes depend on the machine's line-ending setting. Git's own comparison is unaffected.
12. **Helpers live in `output/extension_2026/`.** Scripts stored among outputs are easy to miss.

## Limits

- **Same machine, same day.** This used my existing Python and saved WRDS login, not a fresh install. It does not test the versions a stranger would get.
- **Same WRDS data.** Raw files matched because WRDS returned the same data today. A later pull may differ, especially for recent Compustat rows and revisions, and the raw data is not stored in the repo. Identical hashes today do not guarantee identical results later.
- **Hand-written documents are not regenerated:** `output/writeup.md` and the audit reports. This re-audit does not check their numbers against the tables.
- **`verification/` scripts and `00_test_wrds.py`** were not run.
- Reproduction shows the same code gives the same output. It does not show the rules or results are right.

Logs of all passes are in my session scratch folder, under `scratchpad\reaudit\logs`. They are not part of the project.

---

## Update, 2026-11-01: rerun of the uncommitted fixes

**This section tests the working tree after the fixes, which are not yet committed.** The sections above are kept as the record for the first v1 commit.

**Answer:** the fixes work. Following `README.md` from an export with no `data/` folder, all 14 scripts exit 0 using a fresh install from `requirements.txt`. 323 of 328 files are byte-identical. The other 5 are logs: 4 differ only by timestamps, appended rows or row order, and `pull_checks.md` also loses a hand-written note. No result differs.

### Method

- Exported `git ls-files -co --exclude-standard` to a new scratch folder outside the project: 330 listed, 328 copied. The 2 not copied are the deleted helpers, `check_contributors.py` and `stage1_validate.py`, which `git ls-files -c` still lists until the deletion is committed.
- The export had no `data/` folder and no parquet files at the start.
- Every command confirmed its folder first, and the runner refused to start unless its current folder was the export. No step started in the real project, and the earlier slip did not recur.
- A new virtual environment was built from `requirements.txt`.
- Hashes of the real tree and real data were saved before the run.

### Exit codes (README order)

| Script | Exit |
|---|---|
| `00_test_wrds.py` | 0, and it ran non-interactively |
| `01_build_universe.py` to `08_robustness.py` | 0 each |
| `09_reit_liquidity.py` | 0 |
| `09a_extension_pull.py` | 0 |
| `10_extension_2026.py` | 0 |
| `10a_extension_contributors.py` | 0 |
| `11_long_short.py` | 0 |

### Differences from the working tree

| File | Type | Detail |
|---|---|---|
| `output/logs/pull_log.csv` | Appended rows | 7 new rows from this run |
| `output/logs/pull_runs.csv` | Appended row | 1 new row |
| `output/robustness/pull_log_quarterly.csv` | Timestamps | Row counts and dates match |
| `output/logs/universe_removed_stopped_trading.csv` | Row order | Same 728 lines when sorted |
| `output/logs/pull_checks.md` | Timestamps, plus a hand note | See below |

**`pull_checks.md`:** apart from timestamps, 3 things differ. The real tree has a hand-written two-line note saying the log reflects the config at pull time. Its "Last subperiod" line and its "Latest month" line show 2026-05-31 from the original pull, while a rerun shows 2025-12-31 and "covered", with the wording "in config at pull time". No result depends on this. The difference comes from keeping the original log and annotating it, not from a calculation.

All 15 `data/` files in the export match the real project's by hash. All tables, regressions, return series and charts match, including the three `results.md` files.

### Items you asked me to confirm

| Check | Result |
|---|---|
| File-count sentences | No longer differ. All three now say "files hashed before and after this run" with no count, and each `results.md` is byte-identical |
| 11 stops if 10's output is missing (in the copy) | Yes: exit 1, `STOP: ['returns.csv'] not found. Run 06_portfolios.py, 09a_extension_pull.py and 10_extension_2026.py first.` `results.md` unchanged |
| 11 stops if 10's output is older than its inputs (in the copy) | Yes: exit 1, `STOP: output/extension_2026/returns.csv is older than [...]`. `results.md` unchanged. After restoring the file, 11 exits 0 with the same hash |
| Real data hashes | Unchanged, all 15 |
| Real tree | I changed only this file. `output/writeup.md` and `verification/reaudit_agent3.md` changed during the run, not by me, so this run tested the earlier `writeup.md`. That file is hand-written and no script reads it |

### Were `README.md` and `requirements.txt` enough?

Yes, for this run. I needed nothing else, and `pip install -r requirements.txt` gave working imports in a new environment. The earlier MUST FIX and SHOULD FIX items are closed, with `pull_checks.md` handled by a note rather than regenerated:

| Earlier finding | Status |
|---|---|
| 1. Numbered order fails on a clean clone | Fixed: `09a` is now in the order |
| 2. No reproduction instructions | Fixed: `README.md`, `requirements.txt` |
| 3. 11 hides an upstream failure | Fixed |
| 4. Count sentences depend on the folder | Fixed |
| 5. `pull_checks.md` stale against the config | Explained by a hand note; a rerun differs, see below |
| 6. `00_test_wrds.py` username | Fixed: exit 0 non-interactively |
| 7. `.gitignore` comment | Fixed: it now points to the README order |
| 12. Helpers stored among outputs | Fixed: now `09a` and `10a` |
| 8-11. Logs, row order, timestamps, `.gitattributes` | Still open; all were OPTIONAL |

### New findings

**MUST FIX:** none.

**SHOULD FIX**

1. **The README's reproduction sentence leaves out one difference.** It says a rerun matches "apart from timestamps, appended log rows and the row order of one log". `pull_checks.md` also differs by the hand note and two date lines.

**OPTIONAL**

2. **`pull_checks.md` shows as changed on every line against the commit, in the real tree.** That looks like a line-ending change from the hand edit, but I did not confirm it. Committing it adds noise to the diff, not a content problem.
3. **Long folder paths can break the install on Windows.** `pip` first failed under my long scratch path, because one dependency's file exceeded the Windows path limit. It worked in a short folder, so I put the environment there. An ordinary project path should not hit this, and the README does not mention it.
4. **Indirect dependencies are not pinned.** `requirements.txt` pins direct packages only, so a later install could get different versions of, for example, scipy. Today's install gave scipy 1.18.1.
5. **`git ls-files -c` still lists the 2 deleted helpers** until the deletion is committed. Anyone exporting before then would see missing files. It clears itself on commit.

### Limits

- **Same machine and account.** I used my saved WRDS login and the same Python 3.13.2. This is a clean install and clean folder, not a stranger's computer or account, so setting up the login from the README was not tested.
- **Same-day WRDS data.** Later pulls may differ, as the README says.
- **Not a commit.** This tested the files as they stood at export. If they change before commit, the result applies only to what was exported.
- **Hand-written documents** are not regenerated or checked here, and the `verification/` scripts were not run.
- A matching rerun shows the same code gives the same output. It does not show the rules or results are right.

Logs are in my session scratch folder, under `scratchpad\reaudit2\logs`, and are not part of the project.
