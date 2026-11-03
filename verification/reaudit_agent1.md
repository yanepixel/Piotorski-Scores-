# Compliance re-audit of the brief (Agent 1)

Report only. This is the only file I wrote or changed in the project. I made no WRDS requests, and I ran no script that writes project files. Baseline: the first v1 commit, and `git status` and `git diff` against it were empty when I started.

**Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy).

**Terms.** **Magic number:** a value written directly in a script rather than read from `config.py`. **Report-only:** it changes wording or a log, not membership or returns. **Unread key:** a `config.py` setting no script reads, so changing it does nothing.

## Result

**No finding changes a headline number, the answer or any portfolio. The test's rules were followed.** The gaps are in compliance and upkeep: labels, logs, definitions and stale wording.

| Class | Count | Meaning here |
|---|---|---|
| MUST FIX | 3 | A non-negotiable rule or an explicit "every" requirement is unmet, with no approved decision. All are small, and none touches a figure. |
| SHOULD FIX | 8 | The file misleads or disagrees with another file, or a setting doesn't do what it appears to. |
| OPTIONAL | 7 | Tidiness. Leaving these does no harm. |

**Nothing needs adding to answer the large-cap question.** The headline, the robustness runs and the disclosures already answer it. No new study, data or variant is proposed.

## Where I am not independent

I wrote scripts 01-11, most of the logs and most of the write-up text, so:

- **This audit doesn't test correctness.** I didn't recompute results. That evidence is Agent 2's rebuilds and Agent 3's audits, and my reading of their reports is second-hand.
- **I may be lenient on my own choices.** Examples are what counts as "report-only", and whether a line in a log counts as a definition. Please weigh those classifications with that in mind.
- **"Met" means the file exists and says so.** Where I name a code path, I read the code I wrote.
- **My key and literal scans are text searches I wrote.** They look for `cfg.NAME` and for literals. A setting read another way would show as unread. I also read the code by hand, but a second reader should spot-check it.
- **I can't prove three things from files:** that the user approved each checkpoint, that the 10-K hand-check happened, and that no config value changed after results. Those rest on `CLAUDE.md`, the master session's messages and Agent 3's hash baselines. Git has only one commit, so it has no history to check.

## MUST FIX

**M1. The exact label is missing from 6 tables in `output/tables/` (section 4: "every table").** They are `coverage_by_sector_year.csv`, `handcheck_sample.csv`, `permco_joins_review.csv`, `score_distribution.csv`, `signal_pass_rates.csv` and `signal_pass_rates_by_year.csv`, all written by `04_scores.py`. The other 12 tables and all 4 charts carry it. The fix is a label column, or a first row in the transposed hand-check file. No values change. Variant CSVs without the label are in O1.

**M2. Ground rule 6 is partly unmet for `05`, `06`, `07` and `08`.** See the table in section 2. `05` and `06` log no unique-company count. `07` and `08` write nothing to `output/logs/`, and `08` logs no company counts for any variant. Fix: a short log line or file per script. No results change.

**M3. Ground rule 8: `output/robustness/robustness_report.md` defines no terms.** It is a reader-facing report using alpha, t-stat, Sharpe, CAGR, spread and variant names. Fix: add the glossary already in `07_evaluate.py`.

## SHOULD FIX

**S1. `04_scores.py` counts 7,570 scored list rows, and the real figure is 7,571.** `align_for_counts` (line 157) sorts by availability date alone, without the `datadate` tie-break section 9 later required in `05_align.py`. So `output/logs/scores_checks.md`, `coverage_by_sector_year.csv` (sector 45: 1,524, against 1,525 in formation) and "Too old: 50" (formation: 49) disagree with `formation.parquet`. One Maxim row. The write-up doesn't use the affected figures, and scores themselves are unaffected.

**S2. `validation.md` still says "nothing here has been applied".** The treatment was approved and applied in `10_extension_2026.py`. Fix: reword in `stage1_validate.py`, without rerunning anything else, or add a status line.

**S3. The extension's build order is not stated, and a fresh run would stop.** `10_extension_2026.py` needs `data/raw/comp_secm_extension.parquet` and `security_map.csv`, both from `output/extension_2026/stage1_validate.py`, a script outside the numbered order and inside an output folder. `11` needs `10`'s `returns.csv`. `.gitignore`'s note lists `02`, `08` and `09` as the re-pull scripts and omits `stage1_validate.py`. Fix: state the order in one place and correct that note.

**S4. Section 6 item 1, "runnable in order from a fresh `data/` folder", has not been demonstrated.** Each script ran in order, and `08` reproduces the universe and returns. But no run has started from an empty folder, and I couldn't test it here without WRDS. I read no obstacle in 01-08. Scripts `01` and `03` read WRDS directly, so a later rerun can differ if WRDS revises data, and `01`'s inputs are not stored as raw. Fix: run it once when WRDS use is allowed, and compare to the stored hashes.

**S5. `00_test_wrds.py:22` calls `wrds.Connection()` with no username.** Section 9 says all WRDS scripts must pass it. It prompts, and crashes when non-interactive. It is outside the pipeline.

**S6. Nine `config.py` keys are unread, and six more entries are read only as text or not at all.** Changing them changes nothing, while the file presents them as rules. See section 1. The two null-return settings are the ones most likely to mislead.

**S7. Hold-flat cases are written in scripts, not config.** They affect results, by tiny amounts. See section 1.

**S8. Stale wording.** See section 4, items 1-6. The `config.py` and `CLAUDE.md` items are for the master session only.

## OPTIONAL

- **O1.** Label missing from CSVs outside `output/tables/`: 35 in `output/robustness/`, 7 in `output/reit_liquidity_substitute/`, 5 in `output/extension_2026/`, all 18 in `output/logs/`. Most are logs or mechanical files rather than results tables.
- **O2.** Rule 8 in the six check logs (`universe_`, `pull_`, `clean_`, `scores_`, `formation_`, `portfolio_checks.md`), which have few or no definitions. A one-line pointer to the write-up's Terms section would do. These are working logs.
- **O3.** The write-up leaves a few terms undefined: placebo, survivorship and look-ahead (Verification and restatement text), cap-weighted, sector-neutral and buffer (explained only partly). An equity analyst will know book-to-market and likely the weighting terms. **Placebo** is the one I'd define.
- **O4.** The answer paragraph uses alpha and t-stat just before the Terms section. It explains alpha in words. I would leave it, since the paragraph is settled.
- **O5.** The brief asks for a "short" write-up. It runs to about 5,500 words because of the required disclosures, and the answer is in one paragraph at the top. No action advised.
- **O6.** `pull_log.csv` covers 7 tables. The other raw files are logged elsewhere (`pull_log_quarterly.csv`, `validation.md`), and `comp_funda_reit_fields.parquet`'s 20,796 rows are only in the console output and audit.
- **O7.** Unused code: `log_lines` (`08`), `REAL_ESTATE_TYPE_SECTORS` (`09`), and `che_nonpos` (`09`), which measures `lt`, not `che`. The `wrds_username` function is copied into four files.

## 1. Config keys and magic numbers

### Keys no script reads

| Key | Note |
|---|---|
| `DATA_SOURCE`, `UNIVERSE` | Descriptive |
| `UNIVERSE_BUFFER` | Headline None is implied. `08` reads the rule from `ROBUSTNESS` |
| `HEADLINE_VERSION` | Version A is implied. `ROBUSTNESS`'s "B" is not read either |
| `LONG_SHORT_SPREAD` | Descriptive |
| `HEADLINE_RETURNS` | Net is hard-built in `06` and `07` |
| `PRIMARY_BENCHMARK` | Benchmark is built directly |
| `STANDARD_ERRORS` | Newey-West is called directly in `07`; only the lag count is read |
| `PROFITABILITY_SCREEN` | Off by construction; `08` always runs the variant |

### Entries read only as text, or not at all

| Entry | What actually happens | Affects results if changed? |
|---|---|---|
| `EIGHT_SIGNAL_NULL_RETURN_RULE` | Printed in a note only. Hold-flat is applied regardless | Would, but doesn't |
| `BUFFER_NULL_RETURN_RULE` | Same | Would, but doesn't |
| `ROBUSTNESS` entries for `value_filter_B`, `eight_signal_no_liquidity` and `profitability_screen` | `08` runs them by name, and the values aren't read | Would, but don't |
| `REIT_LIQUIDITY_SUBSTITUTE["applies_to"]` | Unread; descriptive | No |

`09` and `11` check their other descriptive values and exit if they differ, which is the better pattern.

### Magic numbers that affect results

| Where | Value | Size | Advice |
|---|---|---|---|
| `08:30`, `09:32` | General Growth 79129, 2009-05 | One month, one name | S7: put in config; currently repeated in two scripts |
| `08:32` | Comverse 10942, 2007-02 to 05 | -0.16 / -0.11 bp a year | S7 |
| `10:74`, `10:124` | Extension starts "2026-01" | None today | Derive from `RETURNS_END` |
| `10:210` | 252 months, 2005-06, 2026-05 check | A check, not a rule | Derive from config |
| `05` | `limit_denominator(1000)` for the exact fraction | None; recovers 1/3 | Leave, it is mechanics |
| `stage1_validate.py:25, 29` | Pull window; RSP and SPY CUSIPs | Defines the raw pull | Optional. `10` then uses config's lines |
| `08`, `09` | Pull field lists for `fundq` and `funda` extras | Defines the raw pull | Optional, for parity with `FUNDA_FIELDS` |
| `01:183`, `01:446` | `indtype = 'GICS'` | The only value in the table | Leave |
| `check_contributors.py:27` | Hologic, Coterra dates | Report only: repeats config, and a change wouldn't follow | Read from config |

### Report-only labels: no action needed

`01`: `GICS_REAL_ESTATE_GROUP`, `CRASH_WINDOW`, `CONTEXT_RANKS`, `CONTEXT_YEARS`. `02`/`03`: `"USD"` in reports. `04`: `HANDCHECK_SAMPLE`, `JOIN_READINGS`, chart colours. `05`: `LARGE_MOVE_RATIOS`. `07`: `SUBPERIOD_CONTEXT`, glossary. `10`: `EXIT_GAP_BP` (sensitivity), `DISCLOSURE`. `11`: audit figures quoted in text (46%, 26%, 2.3-2.5, 0.11). `stage1_validate.py`: `LARGE_PRICE_GAP`.

These quoted figures don't update if results change, which is acceptable because they cite audits at a point in time. Numerical tolerances such as `1e-12` are checks, not rules.

## 2. Ground rule 6, script by script

| Script | Rows | Unique companies | Date range | Drop reasons | Where | Status |
|---|---|---|---|---|---|---|
| `00_test_wrds.py` | n/a | n/a | n/a | n/a | Console | Access test; no data kept |
| `01` | Yes | Yes | Yes | Yes, waterfall per date | `logs/universe_*` | Met |
| `02` | Yes | Yes (IDs) | Yes | Yes (null gvkeys, 90 unmatched PERMNOs) | `logs/pull_*` | Met |
| `03` | Yes | Yes | Yes | No drops; flags counted | `logs/clean_*` | Met |
| `04` | Yes | Yes, scored | Fiscal years | Yes, by signal and reason | `logs/scores_*` | Met |
| `05` | Yes | **No** | Per date | Yes, stale and missing | `logs/formation_*` | **Partly (M2)** |
| `06` | Yes | **No** | Yes | Yes, exits logged | `logs/portfolio_*` | **Partly (M2)** |
| `07` | Months | **No** | Yes | Nothing dropped | `output/checkpoint3_results.md`, **not logs** | **Partly (M2)** |
| `08` | Per variant | **No** | Report text | Screen failures, thin buckets | `output/robustness/`, **not logs** | **Partly (M2)** |
| `09` | Yes | Companies added only | Report text | Yes | Own folder (8d) | Partly, folder approved |
| `10` | Months | Named exits only | Yes | Named exits | Own folder (8d) | Partly, folder approved |
| `11` | Months | n/a, uses portfolio series | Yes | n/a | Own folder (8d) | Met in substance |
| `stage1_validate.py` | Yes | Yes | Yes | Coverage flags | Own folder (8d) | Met |

## 3. Ground rule 8, output by output

| Output | Terms section? | Status |
|---|---|---|
| `output/writeup.md` | Yes | Mostly met; O3, O4 |
| `output/checkpoint3_results.md` | Yes | Met |
| `output/extension_2026/results.md`, `validation.md` | Yes | Met |
| `output/reit_liquidity_substitute/results.md` | Yes | Met |
| `output/long_short_100_100/results.md` | Yes | Met |
| `output/robustness/robustness_report.md` | **No** | **Not met (M3)** |
| Six check logs in `output/logs/` | No; `universe_checks.md` explains GVKEY in a heading | Not met literally (O2) |
| Charts | Axis titles in words; the F-score chart relies on the term | Met |

## 4. Stale wording

| # | Where | Says | Reality | Who |
|---|---|---|---|---|
| 1 | `validation.md`, from `stage1_validate.py:372` | "nothing here has been applied" | Applied in `10` | Agent 1 |
| 2 | `.gitignore` | Re-pull with 02, 08, 09 | `stage1_validate.py` too | Master |
| 3 | `01`, `02`, `03`, `stage1_validate.py` docstring on `wrds_username` | "the password field is never read into a variable" | The whole line is read into memory and only the username is used. It is never printed or stored, as section 9 requires, but the comment overstates | Agent 1 |
| 4 | `03_clean.py:63` | "any duplicate stops the run" | It records a failure, and only a `gvkey-datadate` duplicate halts it at the merge. There are none. The brief's "keep original over amendment" isn't implemented, because the table has no amendment marker | Agent 1 |
| 5 | `config.py:84` | "for user review at Checkpoint 2" | Approved, section 8b item 8 | Master |
| 6 | `config.py:102` | "Pembroke-style long-only context" | Unexplained; nothing else mentions it | Master |
| 7 | `config.py:3` | "Do not edit after seeing results" | Robustness and post-write-up entries were added later, as approved in 8c and 8d. Accurate for headline values | Master, optional |
| 8 | `CLAUDE.md` section 1 | "from 2005 to 2026" | Headline ends December 2025 (8b item 3), and sections 8-8b override | Master, optional |
| 9 | `CLAUDE.md` section 3 | Credentials in `.pgpass`, "no password prompts" | On this machine, `pgpass.conf`, with a username needed (section 9) | Master, optional |
| 10 | `CLAUDE.md` section 5 tree | Ends at `08` | `09`, `10`, `11` exist (8d) | Master, optional |
| 11 | `CLAUDE.md` section 9 title | "from the Phase 1a audit" | Also covers later audits | Master, optional |
| 12 | `02` docstring; `01` docstring | Log lists | Omit `pull_raw_hashes.csv` and `universe_mortgage_reits_excluded.csv` | Agent 1, optional |
| 13 | `stage1_validate.py` cause labels | DuPont gap: "distribution treated differently" | The audit reads it as a spin-off. Both are consistent, but the label is vague | Agent 1, optional |
| 14 | `verification/` reports | Version B first-run figures and older hashes | Correct at their date; the write-up gives both | No action |

## 5. Requirements, line by line

Status: **Met**; **Changed** by the decision cited; **Not met**; **Unverified** where a file can't prove it.

### Section 2: ground rules

| # | Requirement | Status | Proof |
|---|---|---|---|
| 1 | No look-ahead | Met | `05_align.py`, `formation_checks.md`; `data_audit_phase4_6.md` placebos |
| 2 | No survivorship; rebuilt each date | Met | `01_build_universe.py`; Lehman, Sears in `universe_checks.md` |
| 3 | Config-driven; no magic numbers; ask if missing | Mostly met | Rules were asked for and locked. Exceptions S6, S7 |
| 4 | Raw immutable, written once by the pull script | Met; extra writers approved | `02`, `08`, `09` and `stage1_validate.py` write only new files, write-once. Hashes in earlier reports. The later raw files come from those scripts, not `02` (Phase 7, 8d) |
| 5 | No config value changes after results | Unverified, evidence good | Headline outputs byte-identical across later runs. Git has one commit |
| 6 | Log everything | Partly | Section 2; **M2** |
| 7 | Drops, failed links, fallback in write-up | Met | `writeup.md` Drop counts, Limitations |
| 8 | Terms defined on first use | Partly | Section 3; **M3** |

### Section 3: data access

| Requirement | Status | Proof |
|---|---|---|
| Tables as listed; `msf_v2` used, legacy as fallback only | Met | `01`, `02`; legacy `msenames` only as a cross-check |
| No S&P history; `idxcst_his` only to compare today's list | Met | `universe_checks.md` section 6 |
| Inspect columns before querying | Met | `02`, `08`, `09`, `stage1_validate.py` check at run time. `01` was inspected before writing, not in the script |

### Section 4: universe

| Requirement | Status | Proof |
|---|---|---|
| Exact label in every table, chart, write-up | **Not met** for 6 tables | **M1**. Charts and write-up met |
| Formation date, last trading day of May, 2005-2025 | Met | `universe.parquet`, 21 dates |
| Steps 1-5 | Met; step 1 changed by 8 item 5 | `01`; `universe_removed_stopped_trading.csv` |
| Step 2: US common, three exchanges; no ETFs, ADRs, preferreds, funds, units; REITs in | Changed by 8 items 1, 6 | `config.py` filters; `universe_mortgage_reits_excluded.csv` |
| Step 6: link rule | Changed by 8 item 2 | `universe_sibling_links.csv`, `universe_link_failures.csv` |
| Step 7: sector after ranking | Changed by 8 items 1, 4 | `universe_checks.md` |
| Output columns | Met | `universe.parquet` |
| Config entries; `INDEX` removed | Met | `config.py:10-14` |

### Section 5: phases

| Phase | Requirement | Status | Proof |
|---|---|---|---|
| Layout | Each phase its own script, runs from prior outputs, re-runnable | Met | `01`-`08`; several reruns |
| 1a | 500 per date | Met | `universe_checks.md` |
| 1a | ~400-430 after | Changed, 8 item 7 (375-425) | Same, 378-417 |
| 1a | Cutoff trend, dips, 50% flag | Changed, 8 item 7 | Same; 2021 flag |
| 1a | Link rate at least 98%, every failure named | Changed, 8 item 8 | 99.88% / 99.96%; `universe_link_failures.csv` |
| 1a | Overlap reported | Met | 83.6% |
| 1a | Year-over-year turnover | Met | `universe_checks.md` section 7 |
| 1a | Known names | Changed, 8 item 8 | `universe_checks.md` section 8 |
| 1a | Fail loudly | Met | Exit code 1 path |
| CP1 | Stop and wait | Unverified from files | `CLAUDE.md` section 8; master's message |
| 1b | Master list, all 21 lists | Met | `pull_checks.md` |
| 1b | `funda` range, filters, fields | Met; `curcd` added with approval | `comp_funda.parquet`; `config.py:57` |
| 1b | `co_filedate` 10-K only | Met | `FILING_SRCTYPES` |
| 1b | `co_hgic` full history | Met | `comp_co_hgic.parquet` |
| 1b | `msf_v2` Jan 2005 to latest, all linked PERMNOs | Met | `pull_checks.md`; latest is 2025-12 |
| 1b | RSP and SPY | Met | `crsp_benchmarks.parquet` |
| 1b | Factors merged on month, coverage checked | Met | `ff_factors.parquet`, `pull_checks.md` |
| 1b | One file per table | Met; two FF tables merged as asked, link table added | `data/raw/` |
| 1b | `pull_log.csv` fields | Met | Timestamp, rows, IDs, range |
| 2 | Standardize names and units | Met; units already USD millions, CAD by 8b item 4 | `03_clean.py`, `clean_non_usd.csv` |
| 2 | One row per gvkey-fiscal year; original over amendment | Met; moot | 0 duplicates; S8 item 4 in section 4 |
| 2 | Flag stubs; exclude from comparisons | Met | `clean_stub_years.csv`; `STUB_EXCLUSION` |
| 2 | Availability; log fallback share | Met | `clean_checks.md` |
| 2 | Sanity flags; outliers not dropped | Met | `clean_outliers.csv`; 11 negative sales listed |
| 2 | Output file | Met | `fundamentals_clean.parquet` |
| 3 | Lag rules; definitions; signals | Met | `04_scores.py`; Agent 2's `scores_compare.md`; hand-check |
| 3 | Drop rule; count and reason by signal | Met | `scores_drops.csv`, `scores_checks.md` |
| 3 | Signals and inputs kept | Met | `fscores.parquet` |
| 3 | Histogram | Met; peak is 6, not 5, reported | `fscore_histogram.png` |
| 3 | Hand-check sample | Met; label missing, M1 | `handcheck_sample.csv` |
| CP2 | User hand-check before Phase 4 | Unverified from files | `CLAUDE.md` 8b |
| 4 | `merge_asof`, age rule | Met; changed by 8b item 5 | `05_align.py` |
| 4 | Book-to-market and tercile | Met; rule locked in config | `formation.parquet`; float bug fixed and disclosed |
| 4 | Output; log per date | Met | `formation_log.csv` |
| 5 | Buckets | Changed, 8b item 1 | `06_portfolios.py` |
| 5 | Count per year; flag under 10 | Met | `bucket_counts.csv` |
| 5 | Equal weight, drift, reinvest | Met | `06`; Agent 2 and 3 rebuilds |
| 5 | Turnover and costs | Met; basis locked | `portfolio_turnover.csv` |
| 5 | Spread diagnostic, no shorting costs | Met; cost credit disclosed, 8d item 4 | `writeup.md` |
| 5 | Output columns | Met; gross columns added | `portfolio_returns.csv` |
| 6 | Performance table | Met; hit rate is in the report, not `performance.csv` | `performance.csv`, `checkpoint3_results.md` |
| 6 | Versus benchmark | Met | `versus_benchmark.csv` |
| 6 | Regressions | Met | `factor_regressions.csv` |
| 6 | Monotonicity | Met; gross, with caution | `returns_by_score.csv` |
| 6 | Year-by-year; subperiods | Changed, 8b item 3 | `year_by_year.csv`, `subperiods.csv` |
| 6 | Three charts | Met | `output/charts/` |
| CP3 | Stop, plain-English result | Unverified from files | `CLAUDE.md` 8c; `checkpoint3_results.md` |
| 7 | Each `ROBUSTNESS` entry, buffer, screen | Met | `output/robustness/` |
| 7 | One comparison table | Met | `robustness_comparison.csv` |

### Section 6: deliverables

| Requirement | Status | Proof |
|---|---|---|
| Runnable in order from fresh `data/` | **Not demonstrated** | **S3, S4** |
| Tables and charts | Met | `output/` |
| Write-up: answer, method, results and charts, robustness, limitations with overlap, fallback, drops, shorting | Met; not short (O5) | `writeup.md` |

### Section 7: working with the user

| Requirement | Status | Proof |
|---|---|---|
| Define terms | Partly | Section 3 |
| Stop at checkpoints | Unverified from files | Master's records |
| Suspect too-good results | Met in spirit | Re-checks at Phase 6; `data_audit_phase4_6.md`. Results weren't too good, and a large negative subperiod alpha was re-checked anyway |

### Sections 8, 8b, 8c, 8d: decisions and disclosures

| Item | Status | Proof, `writeup.md` unless stated |
|---|---|---|
| 8.1 REITs in, mortgage REITs out, iStar disclosed | Met | "Who is in and out" |
| 8.2 Sibling links, each logged | Met | `universe_sibling_links.csv`; 34 uses |
| 8.3 Eaton, Ceridian reported | Met | Same section |
| 8.4 No-sector excluded and reported | Met | Yahoo |
| 8.5 Stopped trading removed | Met | `universe_removed_stopped_trading.csv` |
| 8.6 Filter codes in config; UG, Cboe out | Met | `config.py`; "Partnerships coded as units", Cboe |
| 8.7 Range, flag, 2020 reported | Met | "The universe is a proxy" |
| 8.8 Link by cap; names in config | Met | `universe_checks.md`, `config.py` |
| 8.9 RSP and SPY | Met | Results table |
| 8 disclosures: Visa/Mastercard/PayPal, CBRE, range timing, Dell and Liberty | Met; Visa group and CBRE confirmed in `universe.parquet` | Same sections |
| 8b.1 Low 0-4 disclosed | Met | "Low is broader" |
| 8b.2 Drop rule; exclusions disclosed; 8-signal run | Met; buckets could not be set before any returns, disclosed, set under 8c | Robustness timing |
| 8b.3 2025 partial; ends before 2026 | Met | Header, Data limits |
| 8b.4 Non-USD, version B only | Met | Tim Hortons; `formation_non_usd.csv` |
| 8b.5 Score age | Met | `SCORE_AGE_BASIS`; Method |
| 8b.6 Thin May 2005 | Met | Data limits |
| 8b.7 Mergers, 270 rows, joins table | Met | Merger paragraph |
| 8b.8 Cleaning rules | Met | Timing and accounting choices |
| 8c timing; headline stays; 2015-25 wording and range | Met | Robustness timing, quoted context |
| 8d.1 Extension after validation | Met per master's gate; order with REIT disclosed to master | `validation.md`, `results.md`; `data_audit_post_writeup.md` section 8 |
| 8d.2 REIT, not blind | Met | Final section |
| 8d.3 Option C not requested | Not run, correctly | No such folder |
| 8d.4 100/100; not blind, fee assumed, credit disclosed | Met | Final section; Portfolio mechanics |

### Section 9

| Item | Status | Proof |
|---|---|---|
| `wrds_username` in all WRDS scripts | **Not met for `00_test_wrds.py`** (S5); met for 01-03, 08, 09, `stage1_validate.py` | `00_test_wrds.py:22` |
| Never print or store password | Met; comment overstates | Section 4 item 3 |
| 20 GVKEYs tested | Met | `permco_joins_review.csv` |
| 4 delisters | Met | `portfolio_checks.md`, write-up |
| CAD via `curcd` | Met | `clean_non_usd.csv` |
| Late filings logged | Met | `clean_late_filings.csv` |
| RSP chained | Met | `06`, `portfolio_checks.md` |
| Ties, inversions, 13 and 15 rows | Met | `formation_checks.md`, write-up |
| Restatement text; 270 rows | Met | Data limits; Merger paragraph |
| 2025 partial | Met | `year_by_year.csv` |

## What I did not check

I did not re-trace figures in the write-up, which Agent 3 traced earlier. Nor did I check the final section's figures beyond my own earlier check, read every line of every log, or run any script end to end.
