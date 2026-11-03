# Compliance reaudit of spec_v2 (Agent 1, 2026-11-02)

Note: this report was written before the corrections it lists were applied. Where it describes the wording of other files, those files have since been corrected.

Report only. This is the only file I wrote; no rule, script, result or public_release file was changed. Citations are `file:line` in the project folder as it stands now (the committed state plus later edits as read from disk). I ran two read-only pandas checks on `data/clean/spec_v2/*` and `output/spec_v2/*`, and read the public copy read-only for item 5.

**Independence.** I am not independent. I wrote 12b, 12c, 13, 14, 15, 16 and 17, and I wrote the number check (16) that this audit leans on. 16 recomputes numbers with separate numpy code but follows my design, and the HAC definition (statsmodels Bartlett, no correction) is the same one I chose, so it cannot catch a design error. Where I say "met", I mean the code does what the clarification says; I have not tested whether the clarification is the right rule (and was told not to). Agent 2's independent build and Agent 3's audits (`spec_v2_compare.md`, `review_response_agent3.md`) are the independent evidence.

## 1. Requirement by requirement (CLAUDE.md 8f, clarifications 1 to 10, Designation, `SPEC_V2`)

Status: **Met** / **Changed** (by a cited decision) / **Not met**.

| # | Requirement | Status | Proof |
|---|---|---|---|
| a | `ib` in ROA, accrual and DROA | Met | `12b_spec_v2_scores.py:64` (`ib_lag1`), `:70` (ROA = ib / at_lag1), `:72` (ROA_lag1 = ib_lag1 / at_lag2), `:74` (ACCRUAL = CFO - ROA); `config.py:202`; raw pull `12a_spec_v2_pull.py:56`, write-once `:42-43` |
| b | Net issuance rule (clarification 3): `sstk - prstkc <= 0`, nulls 0, negatives as reported, no 2% rule or share floor | Met | `12b:111` (`net_issue = sstk.fillna(0) - prstkc.fillna(0)`), `:113` (`<= 0`); 12b never reads `csho`; raw pull `12c_spec_v2_pull_prstkc.py:40-41` (write-once). Changed from the first draft by a cited decision: `config.py:203`, the 2026-11-02 17:18 commit, `output/writeup.md` timing bullet |
| b2 | Literal rule as a reported sensitivity only | Met | `12b:114-115`, `--rule literal`; outputs `*_literal.*` and `output/spec_v2/literal_sensitivity/`; write-up section "The issuance signal and the literal-rule sensitivity" |
| c | Zero-debt override needs dltt and dltt_lag1 both present and zero, and lag2_ok (clarification 2) | Met, implemented by a proxy | `12b:100-105`: `(dltt == 0) & (dltt_lag1 == 0) & (LEVER.notna() & LEVER_lag1.notna())`. NaN never equals 0, so "present" holds. The gate is `LEVER_lag1` computable, not the column `lag2_ok` itself. I checked the data: no row passes with `lag2_ok` false; 9 firm-years have both debts zero and `lag2_ok` true but are not passed, all with `at_lag2` missing, none scored (F_DROA and F_DTURN are also uncomputable). No effect on any score (see O1) |
| d | No fallback date; filing + 3 calendar days <= formation date; earlier scored year if the newest fails; 18-month rule (clarification 4) | Met | `12b:122-124` (no filing date gives no score; `avail_date_v2 = filing_date + 3 days`), `:133` (`merge_asof` backward on the buffered date, ties broken on datadate), `:137` (18-month rule); checks `:193-197`. The "most recent earlier scored year" is the one with the latest available date; I checked that no valid list row has a higher scored fiscal year available than the attached one (0 of 7,614), so the two readings agree in this data |
| e | All included names in the primary benchmark with actual returns, charged like the buckets (clarification 5) | Met | `13:148` (Benchmark = whole cohort), `:30` (PORTS), `:160-167` (every portfolio gets the same turnover cost), check `:210` (benchmark holds every included name) |
| f | Reinvestment charged one-sided in the exit month; exit not a trade; hold-flat months not charged (clarifications 7, 10) | Met, with one undocumented detail | `13:67-68` (end-of-month weight of leaving names x 10 bps, `charge_every_trade`), `:167` (added to that month's cost). Detail: an exit in the final holding month is not charged (`m < months[-1]`). It never binds (0 of 191 exits; checked) and is stated only in the script docstring, not in 8f (O2). Hold-flat names are not "leaving": `:108` counts hold-flat months as returns |
| g | Formation-date delister at 1/N in the target, charged as a buy, earns nothing, weight respread free (clarification 10) | Met | `13:158-162` (target is 1/N over members; drifted weights exclude the delister), 4 cases in `portfolio_exits_v2.csv` |
| h | Hold flat at 0%, no charge, Maxim 2007-11 to 2008-05 and General Growth 2009-05 only; any other held null stops the run (clarification 9) | Met | `config.py:150-151`; `13:31` (FLAT), `:52-58` (0% in those months), `:104-107` (flat allowed only for an Unscored name, otherwise a failure), `:122-126, 129-130` (stop before compounding); run log: 8 hold-flat months, 0 unapproved nulls |
| i | `MISSING_SIGNAL_RULE` stays "drop" (clarification 6) | Met | `12b:119-120`; `config.py` unchanged |
| j | Leverage on dltt only; paper's current-portion debt a noted deviation (clarification 1) | Met | `12b:70-79` (LEVER from `dltt` only); deviation stated in the write-up paper section |
| k | HAC lag floor(4(T/100)^(2/9)); p-values from t(T-k) | Met | `14:49-50` (formula), `:72` (statsmodels HAC, no correction), `:75` (`st.t.sf`, df = nobs - k); lag 4 for 247, 120 and 127 months. The config label says "newey_west_1994_automatic" (`config.py:210`), which suggests the data-dependent bandwidth; the formula is what is coded and what the comment on the same line states (S1) |
| l | Holm over one family of six (clarification 8) | Met | `14:163-166` (family = High's two tests x full period and the two `SUBPERIODS`; assertion that it has six), `:82` (`holm`) |
| m | Power (minimum detectable effect at 80%, 5% two-sided) | Met | `14:36` (`ALPHA, POWER = 0.05, 0.80`), `:78-80` (`mde`); columns `mde_80pct_power_annual` in `tests_v2.csv` |
| n | Sensitivities: lag 12 and scored-only benchmark | Met, and extended | `14:137` (lag 12), `:151` (scored-only), plus lag 6 and the T/(T-k) correction (`:138-139`) added at the project lead's request after the config was locked, so `config.py:215` lists only two (S1). Cited decision: the project lead's message, recorded in the write-up |
| o | `headline_v2` table beside v1 | Met | `14:129` (`headline_v2.csv`), `:277` (`.md`), `:240` (`headline_v2_numbers.csv`) |
| p | Number check | Met | `16_spec_v2_numcheck.py` (75 checks per rule, 0 differ at the last run) |
| q | Drops table (a) no GVKEY link, (b) no sector, (c) stopped trading, (d) unscored by reason, v1 beside v2, (e) market-cap share, sectors 40 and 60 | Met | `15_spec_v2_drops.py:62` onward; `output/spec_v2/drops_by_date_v2.csv`, `drops_reasons_v2.csv`, `drops_summary_v2.md`; reasons add to the unscored count on every date (check in the script) |
| r | Designation: v2 replaces v1; v1 unchanged and labelled superseded; the three later runs labelled v1-specification; both benchmarks together; Holm result with its convention sensitivity; power limits | Met | `output/archive_v1/*` (identical to the originals apart from the note, by hash); write-up sections "Runs after the v1 write-up", "The two benchmarks", the convention table, "The answer"; `config.py:198` |
| s | Pre-return report and ordering (8f heading) | Met, as disclosed | The write-up Timing bullet states the order of the four commits (2026-11-01 23:01; 2026-11-02 17:18, 17:19, 17:22) and the first return file (17:25:08). Agent 3 checked it against the git log |

Not met: none of the stated requirements. The gaps are in config-driven design, logging and wording, below.

## 2. Checks asked for

### (1) Every `SPEC_V2` and config key is read by a v2 script or flagged as descriptive: **not met**

I searched `12a` to `17` (and `04_scores.py`, which 12b loads) for each key.

- `SPEC_V2` keys **read**: `label` (12b), `output_dir` (all), `profit_field` (12a), `issuance_field`, `issuance_sensitivity` (12b), `zero_debt_requires_lag2` (12b), `availability_buffer_days` (12b, 15, 17), `charge_every_trade` (13).
- `SPEC_V2` keys **not read by any script**: `fallback_availability`, `primary_benchmark`, `hac_lag_rule`, `small_sample`, `primary_tests`, `multiple_testing`, `report_power`, `sensitivities` (`config.py:206, 208, 210-215`). The behaviour is hard-coded to match them (14:49-50, 72, 75, 163-166, 36-80, 137-139; 12b:122-123; 13:148). Nothing flags these keys as descriptive; the config docstring (`config.py:5-6`) lists the descriptive names and omits them.
- Top-level names read by no script at all: `HEADLINE_SPEC` (`config.py:198`, new in this round, and not in the descriptive list), plus the nine already listed as descriptive (`DATA_SOURCE`, `UNIVERSE`, `UNIVERSE_BUFFER`, `HEADLINE_VERSION`, `LONG_SHORT_SPREAD`, `HEADLINE_RETURNS`, `PRIMARY_BENCHMARK`, `STANDARD_ERRORS`, `PROFITABILITY_SCREEN`), which is correct. `NEWEY_WEST_LAGS` (v1: 12) is not read by 14; the lag-12 sensitivity hard-codes 12 (`14:137`).
- Constants in v2 scripts that are not in the config (ground rule 3, "no magic numbers"): `14:36` (0.05, 0.80), `14:137-139` (lags 12 and 6, correction on), `13` none, `17` the HAND table and STRUCT constants (provenance text, acceptable).

### (2) Ground rule 6 (logs with row counts, company counts, date ranges, drop reasons), 12a to 17: **partly met**

| Script | Log | Row counts | Company counts | Date range | Drop reasons |
|---|---|---|---|---|---|
| 12a | `output/spec_v2/pull_ib_log.md` | yes | no (no unique gvkeys) | no (no fiscal-year range) | n/a (no drops; key mismatch counts) |
| 12c | `pull_prstkc_log.md` | yes | no | no | n/a |
| 12b | `scores_checks_v2.md` | yes | per-date included/scored; no unique-company count | formation dates; no fiscal-year range stated | yes (no-filing-date, stale, missing, buffer cases) |
| 13 | `portfolio_checks_v2.md` | company-dates | no unique-company count | yes (months) | exits and delisters, hold-flat months |
| 14 | `report_v2.md` | months only | no | yes | n/a |
| 15 | `drops_summary_v2.md` | yes | yes | yes | yes |
| 16 | `numcheck_v2.md` | checks only | n/a | n/a | n/a |
| 17 | `writeup_figures_v2.csv`, `writeup_untraced_v2.txt` | figure counts | n/a | n/a | n/a |

The v2 logs go to `output/spec_v2/`, not `output/logs/` (CLAUDE.md ground rule 6 names `output/logs/`; `config.py:201` sets the v2 folder). The README row for `output/logs/` (`README.md:68`) still says "for each script", which is not true of 12a to 17.

### (3) Ground rule 8 (terms defined on first use): **partly met**

- Write-up: the Terms section (`output/writeup.md:13`) comes after the short answer (`:9`), as in v1 and as the project lead asked. The answer uses F-score, alpha, t-stat, "multiple-testing adjustment", power, REIT and lag before they are defined. All of those are defined in Terms. Used with no definition anywhere in the write-up: **degrees of freedom** and "T - k" (`:48` onward), **t distribution**, **Compustat** and **CRSP** (first used in Method), **RSP and SPY** (`:47`, "fund returns" is the only gloss), **basis points** (defined inline at the first use, so fine), "list rows" and "formation date" (used in Results before the Method wording; Method does say "last trading day of each May"), and `sstk` / `prstkc` (described in words at first use, with the variable names after).
- README: the answer paragraph (`README.md:7`) uses income before extraordinary items, net issuance, Newey-West, Holm adjustment, power, alpha and t-stat with no definition and no pointer to the write-up's Terms; Compustat and CRSP are named without gloss (`:12`).

### (4) Stale wording

| Where | Stale statement | Why |
|---|---|---|
| `config.py:209` | `charge_every_trade`: "mid-period reinvestment after an exit is charged ... like any other trade" | Clarification 7 says one-sided on the value reinvested, exit not a trade |
| `config.py:210` | key name `newey_west_1994_automatic` | The code uses the fixed formula, not the NW94 bandwidth (the comment says so; the key name does not) |
| `config.py:215` | `sensitivities`: `hac_lag_12`, `scored_only_benchmark` | The run also reports lag 6 and the T/(T-k) correction (`14:138-139`, write-up convention table) |
| `config.py:5-6` | "Descriptive only" list omits `HEADLINE_SPEC` and the eight unread `SPEC_V2` keys | See (1) |
| `CLAUDE.md:246` | 8f heading "before any v2 return exists" | The section also holds the Designation (user, after the returns) and the timing sentence; only the specification part is pre-return |
| `CLAUDE.md:248` | "The v1 headline, its files and the public repository are not changed or pushed without the user's approval" | The user has since approved v2 as headline and the public update; the sentence reads as still pending |
| `CLAUDE.md:162, 192, 235` | Phase 5 benchmark "all scored, included names"; deliverable "results table and key charts; robustness summary"; 8d "never change ... `output/writeup.md`'s headline" | v1 wording; only the Designation paragraph (`:254`) supersedes it, and 8f does not say it overrides earlier sections as 8b and 8c do (`:202, :218`) |
| `README.md:56` | "The brief has three stop points ... They have been passed for this result" | The three checkpoints were passed for v1; v2 had separate user approvals |
| `README.md:66, 68` | `literal_sensitivity/` "holds the same run"; `output/logs/` "for each script" | See (4) above and item 5 |
| `output/writeup.md:152` | "so unscored companies are in the comparison instead of silently left out" | The v1 write-up did disclose them: it reported the all-included comparison as a post-hoc sensitivity (+0.19% a year, t 0.22), see (6) |
| `14_spec_v2_evaluate.py:11` | docstring says tests come from "SPEC_V2 primary_tests" | The key is not read (1) |

### (5) Does the public README or write-up say anything not true of the public files?

Read-only against `public_release` as it stands.

- `README.md` (public) row for `output/spec_v2/`: "`literal_sensitivity/` holds the same run under the literal issuance rule" is not true: the public folder holds two files from it (`headline_v2.csv`, `tests_v2.csv`).
- Public `output/writeup.md`: "The full tables are in `output/spec_v2/literal_sensitivity/`" is likewise not true of the public copy (same two files).
- Public README `output/logs/` row and the write-up's pointers to `drops_reasons_v2.csv`, `output/tables/permco_joins_review.csv`, the extension and long/short result files, and `data/raw/...` files name things that are absent; the opening notes of both documents cover these generally. I extracted the backticked paths from both public documents and checked them against the public folder: 20 are absent. Apart from the two literal-sensitivity statements above, they are files the scripts produce (the opening notes say so).
- The write-up's Verification paragraph says the v1 scripts and "all earlier raw and clean data files are unchanged by hash". That is a statement about the project folder. The public `04_scores.py` differs from the project's (number-trimmed review comments), and no hash file is published, so a public reader cannot check it.
- Public `config.py` carries the project's comments, including "designated by the user" (`config.py:198`) and "REVISED before any v2 return" (`:203`): true, not a mismatch.

### (6) Does the write-up's v1-versus-v2 section match the archive?

Compared with `output/archive_v1/writeup_v1.md` (project) and the v1 tables.

- Matches: v1 High 10.91%, scored-only benchmark 11.35%, excess -0.29%; 6 fallback-dated rows; 12 fixed lags; net income; 2% tolerance; reinvestment not charged; 843 unscored; High 1,553 rows. All traced to the v1 files by `17_spec_v2_writeup.py` (figures CSV).
- Does not match: "(primary benchmark) ... instead of silently left out" (`output/writeup.md:152`), see above. Also not mentioned: the archive already reports High against all included names (10.79% net) as a post-hoc sensitivity: raw gap +0.19% a year (t 0.22), alpha -0.44% (t -0.45). The v2 section says the sign flipped because the benchmark changed, which is right, but a reader of the archive will have seen the same comparison there; the v2 section should say so.
- Gap: the v2 section lists seven changes, but the earlier-year fallback of clarification 4 appears only as "the buffer moves 43 list rows to an earlier year" under availability, not as a rule change in its own right.

## 3. Findings

### MUST FIX (compliance with a non-negotiable ground rule; no result changes)

- **M1. Config-driven rule (ground rule 3) is not met for the statistics block.** Eight `SPEC_V2` keys and `HEADLINE_SPEC` are read by nothing (`config.py:198, 206, 208, 210-215`), while `14` hard-codes alpha 0.05, power 0.80 and lags 6 and 12 (`14:36, 137-139`) and ignores `NEWEY_WEST_LAGS`. Either read them (add `alpha`, `power`, `sensitivity_lags` and the correction flag to `SPEC_V2` and use them), or list them as descriptive in the `config.py` docstring and state in 14's docstring which constants are fixed in code. This does not change any result.

### SHOULD FIX

- **S1. Stale or misleading config labels:** `config.py:209` (like any other trade), `:210` (key name), `:215` (sensitivities list). Align them with clarifications 7 and 8 and the convention table.
- **S2. Ground rule 6 for 12a to 17:** v2 logs omit unique-company counts and fiscal-year ranges (12a, 12b, 12c, 13, 14); add them to the existing report files or to `output/logs/`, and correct the README `output/logs/` row.
- **S3. Ground rule 8:** README answer uses undefined terms (`README.md:7`); write-up uses degrees of freedom, t distribution, Compustat, CRSP, RSP and SPY without definition. Add them to Terms and a pointer from the README to the write-up's Terms.
- **S4. Public statements not true of the public files:** the two `literal_sensitivity` sentences (public README `output/spec_v2/` row; public write-up "full tables are in ...") and the "unchanged by hash" sentence as read by a public reader.
- **S5. CLAUDE.md wording:** 8f heading and the "not pushed without approval" sentence; add one line to 8f that it overrides earlier sections where they differ (as 8b and 8c do); mark 8d line 235 as superseded by the Designation.
- **S6. v1-versus-v2 section:** replace "silently left out" and say that v1 already showed the all-included comparison as a post-hoc sensitivity (+0.19%, t 0.22); list the earlier-year fallback as a rule change.
- **S7. README `:56`:** say the checkpoints were passed for v1.

### OPTIONAL

- **O1.** The zero-debt gate is implemented as "LEVER_{t-1} computable" (proxy for `lag2_ok`). I found 9 firm-years where the two readings differ (both debts zero, `lag2_ok` true, `at_lag2` missing); none is scored under either reading. State the proxy in 8f clarification 2 or use the column.
- **O2.** The final-month exemption from the reinvestment charge (`13:67`) is documented only in 13's docstring; it never applies in this data (0 of 191). Add it to 8f clarification 7 for completeness.
- **O3.** Cosmetic: `14:140` puts the new `lag_corr_*` keys before `universe_label` in the row dict (column order in `tests_v2.csv`); `16`'s "report prints every v2 headline value" check tests string membership anywhere in the report and would pass on a coincidental match.
- **O4.** `13` rejects a hold-flat month if the name is scored in that cohort (good), but FLAT is keyed on (permno, month) across cohorts; today only one cohort window contains each month, so this is safe, but a future overlapping case would be flagged only at the data check (`:104`).
- **O5.** The `config.py` top docstring still says "Locked rules. Do not edit after seeing results"; the `HEADLINE_SPEC` line and the SPEC_V2 comment were edited after the returns existed (the 17:42 commit). The write-up discloses this; the docstring could say "except labelled additions".

## 4. What this audit did not test

- Whether any rule is right (not asked).
- Independence: see the top.
- The public release against git history (Agent 3 did that).
- Restated data for FY2015-24 (comp_snapshot not available; stated in the write-up).
- Data revisions: the raw pulls are from 2026-11-02 and WRDS may differ later.
