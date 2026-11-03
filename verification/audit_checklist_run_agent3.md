# Equity audit checklist, run by Agent 3 (2026-11-02, project state after the spec_v2 write-up)

Scope: the whole project: spec_v2 as headline, v1 archived, and the v1-specification extension, REIT and 100/100 runs. Read-only. Written only this file. Git use: read-only `log`, `show`, `diff` and `status` in the project's working repository, whose history is not part of this public repository (commits are therefore given by time). Nothing was run against WRDS.

Where an item was verified in my earlier audits I cite the file. Audits `audit_01` to `audit_37` were written in earlier sessions; I cite them but did not re-run them this pass.

## 1. Findings

**No BLOCKER.** No result is unusable. Seven RISKs and four NOTEs.

**RISK 1: the write-up never states how many tests were tried.** `output/writeup.md:11` (answer paragraph) and `:113` say "one of the six pre-specified tests" survives Holm. That is correct for the family, but the project has produced about 250 reported t-statistics in its own tables (about 400 with the audit runs; trial log, section 4). The write-up gives no count and no stricter threshold. Fix: add to the paragraph under the standard-error table: "In all, the project has reported about 250 alpha or excess-return t-statistics in its tables (about 400 counting audit runs), most on the same few return series. The six-test Holm family is the only pre-specified correction. Against a threshold of about t = 3, the 2015-25 four-factor alpha as run (t -2.70) does not pass."

**RISK 2: the 2015-25 four-factor alpha does not clear t = 3 as run.** t -2.70 (p 0.0078, 122 df), Holm 0.047. It clears a Bonferroni correction only if 6 or fewer tests are counted (it reaches the 5% level at N = 6.3). Section 2 below has the thresholds. It exceeds 3 only under longer lags (lag 6 t -2.94, lag 12 t -3.72), or in the secondary six-factor version (-3.01 at lag 4). The write-up wording ("weak evidence") is right; the count above is missing (RISK 1).

**RISK 3: no period was held out, and the write-up does not say so.** Section 3. Fix: add "No period was held out. The whole of June 2005 to December 2025 was seen in v1 before v2 was specified, and the January-May 2026 extension (v1 specification only) was added after the v1 results." No sentence like this is in `output/writeup.md` or `README.md` (searched for held out, hold-out, out-of-sample, untouched).

**RISK 4: the order of v1 rules and results rests on the project lead's account.** The whole of v1 (headline, nine robustness variants, extension, REIT substitute, 100/100) was committed once, on 2026-11-01 at 17:18:53, after every v1 result existed; a second commit (18:06) followed with re-audit fixes. Git therefore shows nothing about v1 order. File creation times cannot replace it: the v1 robustness files show creation at 01:04 to 01:07 on 11-01, before the headline returns file (01:39:32) and before the raw pull time in `output/logs/pull_runs.csv` (05:06:42 UTC = 01:06 local), because the project was re-run from a clean data folder (README, "Later pulls may differ"). `CLAUDE.md` 8, 8b and 8c admit that robustness definitions, the Comverse hold-flat rule and the version B boundary were settled after results existed. `output/writeup.md:235` states the dependence on the project lead's account. No fix is possible; keep the disclosure.

**RISK 5: four raw files have no recorded hash.** `output/logs/pull_raw_hashes.csv` covers the seven first-pull tables, and `output/spec_v2/pull_ib_log.md` and `pull_prstkc_log.md` cover the two v2 pulls (all nine match the files today). No log holds a hash for `comp_fundq.parquet`, `comp_co_filedate_quarterly.parquet`, `comp_funda_reit_fields.parquet` or `comp_secm_extension.parquet`. The checklist asks that every pull's table, time, rows and hash be logged; for these four, "write-once" rests on the reuse-if-exists code. Fix: record the current values in a log now, with a note that they were hashed on 2026-11-02, not at pull time:
- comp_fundq 558968 bytes sha256 f43e33dab53912416bad650368a84f8a464c0e2c93488508269bfeb5bcfc1290
- comp_co_filedate_quarterly 360099 bytes sha256 12a0e53e471ff4f52ab07e35cb26c1a41aaebaf20650bbe05b015200e3634ceb
- comp_funda_reit_fields 310504 bytes sha256 1581cbaac6b786322f9332aa373b1c7e5d3fa20047e5a5255e45d2e677192b01
- comp_secm_extension 264278 bytes sha256 57c0386b2b34c15d592a0e471b8b16f43c2e7b0ce98c16ef44dffa14288e709e

**RISK 6: the v1-specification runs show one benchmark only.** The extension, REIT and 100/100 tables (`output/writeup.md:264` onward) use the scored-only benchmark. The checklist asks for both benchmarks wherever a result depends on the choice. They are labelled v1-specification, so this is a disclosure gap, not an error; the all-included benchmark was not computed for them.

**RISK 7: restatement exposure is unmeasured for FY2015-2024.** Stated at `output/writeup.md` ("Data limits"). The second-half result, the only nominally significant one, falls where the vintage test (`verification/data_audit_phase2_3.md`, 2005-2015 sample of 55 project companies) does not reach. Cannot be closed without `comp_snapshot` access.

**NOTE 1: v1 used a fallback availability date** (120 days, 6 held list rows). Allowed by the brief and disclosed; v2 removes it.

**NOTE 2: the v2 primary test is the four-factor alpha, chosen over the six-factor.** This was fixed in the first spec_v2 commit (2026-11-01 23:01), after the v1 six-factor result (t -4.10) was known. The choice lowered the 2015-25 t (-2.70 against -3.01), so it was not in the direction of a stronger result.

**NOTE 3: the leverage deviation** (long-term debt only; the paper adds current-portion debt) is listed in the write-up but its effect on scores is not measured.

**NOTE 4: `output/writeup.md:235`** said "the project coordinator's account"; it now reads "the project lead's account".

## 2. Does any result pass a stricter threshold, and where does the 2015-25 alpha stand

Critical |t| for a two-sided 5% family-wise level, Bonferroni, t with 122 df (normal in brackets):

| Tests counted N | Critical \|t\| |
|---|---|
| 1 | 1.98 (1.96) |
| 6 | 2.68 (2.64) |
| 20 | 3.09 (3.02) |
| 50 | 3.37 (3.29) |
| 100 | 3.58 (3.48) |
| 250 | 3.84 (3.72) |

Reading: about 250 reported t-statistics (section 4), but they are far from independent: the same High, Low and Benchmark series enter almost all of them, so the effective number is much smaller, perhaps 15 to 30. I cannot measure it. Against N of about 20 the threshold is about 3.1; against 250 it is 3.8.

Where each stands:
- **2015-25 four-factor alpha, as run (v2 net):** -3.38% a year, t -2.70, p 0.0078. Bonferroni with N = 6 gives 0.047 (this is the Holm figure). It would pass t = 3 only at N of 6 or below. **Fails** the stricter threshold.
- **Same alpha, other lags** (shown in the write-up, not used to choose): lag 6 t -2.94 (just below 3.09 for N = 20); lag 12 t -3.72, which clears N up to about 165 but not 250; with the T/(T-k) correction t -2.65.
- **Six-factor 2015-25 alpha, v2:** t -3.01 at lag 4 (clears N of about 16), -4.08 at lag 12 (clears N up to about 620).
- **v1 results with |t| of 3 or more** (all the same 2015-25 High alpha, 12 lags, six factors): headline -4.10; robustness variants sector-neutral -3.36, cost 25 bps -4.45, eight-signal -4.33, universe buffer -3.41, profitability screen -4.17, lag 90 -4.10; extension to May 2026 -3.16; REIT substitute -4.40. These are variants of one series in one decade, so they count as one finding repeated, not many.
- **Any result on the hypothesised side (positive) with t of 2 or more:** one: Middle against the all-included benchmark in 2015-25 (+0.99%, t +2.30, outside the family, explained as benchmark composition). No High alpha or excess is above 2 on the positive side in any file. The one with t = 1.94 (2005-15 four-factor alpha at lag 12) is below 2.
- Direction: every |t| of 3 or more is a shortfall of High against the benchmark or factor model, not an edge.

Verdict: no result passes about t = 3 on a pre-specified, as-run basis. The 2015-25 shortfall passes it only under 12 lags, where the 12-lag estimate may be less reliable at T = 127 (the size of the 12-lag t was examined in `audit_18` and `audit_37`, which I cite but did not re-run; my own size simulation, `review_response_agent3.md` item 4, covers lag 4 only).

## 3. Held-out period

**None.** Plainly:
- The full sample June 2005 to December 2025 was used in the v1 headline, in all nine robustness variants and in all three labelled runs.
- v2 was specified after v1's results (including the 2015-25 weakness and the six-factor t of -4.10) were known (`output/writeup.md:160`, `:235`). Its subperiod split is the original `SUBPERIODS` in `config.py:127`, which was in the first commit but cannot be shown to precede v1 results (RISK 4).
- January to May 2026 (Compustat, five months) was never in the v1 or v2 specification and was added after the v1 write-up (`CLAUDE.md` 8d). It is the only data seen later than the specification, but it is five months long (T = 5 cannot support an alpha test), was chosen after the spread and the 2015-25 weakness were known, and was run for v1 only, not under v2. It is not an untouched hold-out.

## 4. Trial log

Counting convention: one test = one reported t-statistic on an alpha, an excess return or a spread, in a file under `output/` (counted from the t columns of the CSVs by script) or in an audit output. Duplicates of the v1 headline copied into later tables are removed. Beta t-statistics are not counted. Counts are by column search, so treat them as accurate to about 10%. Dates are 2026-11-01 unless noted; times are file creation times (first run) with the reason given where file times are unreliable (RISK 4).

| # | Run | Date and what changed | Tests produced | In write-up |
|---|---|---|---|---|
| A | v1 headline: 7 six-factor alphas (High net and gross, Spread net and gross, High minus benchmark, Low, Benchmark), 6 excess t-statistics against benchmarks, 2 subperiods x (High, Spread) alpha | Phase 6, 01:39 to 01:41; Checkpoint 3 | 17 | 8 |
| B | Nine robustness variants (high cutoff 7+, version B, cap-weighted, sector-neutral, lag 90, cost 25 bps, eight-signal, universe buffer, profitability screen): 3 full-period alpha t each (High, High minus benchmark, Spread) plus 2 subperiods x 2 | Phase 7; definitions set after the headline returns (CLAUDE.md 8c) | 63 (27 full period, 36 subperiod; 7 headline duplicates excluded) | 0 in v2 write-up (summary only in archived v1) |
| C | REIT liquidity substitute | 13:42; defined after similar variants were seen | 7 (3 full period, 4 subperiod) | 6 |
| D | 2026 extension (Jan-May 2026): 10 regressions, 4 sensitivity rows x 3, 3 subperiod rows x 3 | 13:56; spin-off and exit sensitivities included | 31 | 8 |
| E | 100/100 long/short: 8 performance alphas, 12 monthly-reset sensitivities, 4 both-legs-charged, 12 subperiod, 6 charged-monthly subperiod | 15:09; borrow fee 0.5% and 2.0%, annual and monthly reset | 38 (42 cells, 4 are v1 duplicates) | 12 |
| F1 | spec_v2 net: 48 rows in `tests_v2.csv` (High, Middle, Low, Spread, Benchmark; full period and two subperiods; raw excess, 4-factor, 6-factor, scored-only benchmark) | 2026-11-02 17:26 (specification committed 11-01 23:01) | 48 (6 in the Holm family) | 24 |
| F2 | spec_v2 literal issuance sensitivity: same 48 rows | 2026-11-02 17:25 | 48 | 2 |
| F3 | SE-convention re-estimates (lag 6, lag 12, lag 4 corrected) of the 96 F tests | 2026-11-02 | 288 re-estimates (not separate hypotheses) | 24 (as-run column repeated) |

Totals, project tables: A 17 + B 63 + C 7 + D 31 + E 38 + F 96 = **252 distinct reported t-statistics**, plus 288 convention re-estimates of F. Appearing in the v2 write-up text: about 70.

Audit, placebo and sensitivity runs (in `verification/`), counted from outputs and scripts, approximate:

| Run | Script and date | What was run | Tests / draws |
|---|---|---|---|
| Independent rebuilds and trace checks | `audit_19`, `22`, `28`, `30`, `32`, `35`, `37`, `45`; `compare_*` | Rebuilds of the same series; re-computed alphas | about 60 t-statistics, all repeats of A to F |
| Shuffled-score and random-selection placebos | `audit_18` (2,000 draws, 1,000 within sector, 5,000 + 5,000 block resamples), `audit_27` (2,000 + 1,000 draws, 20,000 and 5,000 + 5,000 resamples), `audit_31` and `33` (2,000 draws each, long/short views), `audit_39` (1,000 + 1,000 cap-weighted draws) | Calibration of how unusual an observed alpha is; not hypothesis tests | 6 placebo experiments, about 26,000 simulated tests |
| Delisting scenarios | `audit_38` (11-01 23:02) | Four Shumway scenarios x High, benchmark, Spread | about 12 |
| Cap-weight and mega-cap | `audit_39` (23:03) | Actual, drop top 0, 5, 10, 20 names | 5 |
| spec_v2 design checks | `audit_40` (23:05), `41`, `42`, `43`, `44` (11-02) | HAC tables (12 rows x 2 lags), size simulations (4 x 2,000), Holm table, five convention variants x six tests, NW94 | about 70 |

Total with audits: **about 400 reported t-statistics** (252 + about 150), plus the placebo draws. The rule of thumb: effective independent tests are far fewer than 400 because the series overlap.

## 5. Checked and found clean (with the evidence)

- **Raw data write-once (partly):** seven first-pull files and the two v2 pulls match their logged SHA-256 today; `pull_runs.csv` shows the second run refused (2026-11-01T05:06:54Z and 18:08:56Z). The four unlogged files are RISK 5.
- **Earlier specifications byte-identical:** `git status` shows no modified tracked file; a git comparison of all v1 scripts and v1 output folders against the re-audit commit (2026-11-01 18:06) shows no change. `CLAUDE.md` and `config.py` changed only as described in the project's release review (not included here).
- **Period and availability dates kept separately:** `data/clean/fundamentals_clean.parquet` carries `datadate`, `filing_date`, `avail_date`, `avail_source`; v2 availability checked against the raw 10-K file on all 7,614 scored rows (`verification/review_response_agent3.md`, "Audit of the v2 build", item 1).
- **Buffer and ties:** v2 uses filing date plus 3 days, minimum observed gap 3 days, no row too old (same audit). v1 same-day filings (15 rows) and ties are handled by the stated rule and listed.
- **No fallback in v2:** 6 fallback-dated v1 rows are all lost (3 stale, 3 no earlier year), counted in the write-up drop table.
- **Dates:** the last portfolio is labelled partial (7 of 12 months); returns end 2025-12-31; factor months align (`audit_17`, `audit_43`). Raw files hold later dates (FY2025 fundamentals, filings to 2026-10, factors to 2026-09) that no score or return uses (`LAST_SCORE_FY = 2024`).
- **Survivorship and identifiers:** universe rebuilt each May from CRSP; stopped-trading removals counted per date (727 total); benchmarks pinned by PERMNO (`config.py:65`); name losses by date, with unscored market-value share, in `drops_by_date_v2.csv` (earlier Phase 1a audits: `audit_01` to `audit_08`, not re-run).
- **Definitions:** signals follow the brief; deviations from the paper listed in the write-up (leverage, Low band, issuance); Phase 2-3 recomputation by `audit_15`; v2 net rule checked by me (`audit_41`, `audit_43`).
- **Missing-signal handling:** counted by signal and reason (`drops_summary_v2.md`: 689 of 800 are missing-signal, 647 of those liquidity); the removed firm types (traditional REITs, homebuilders, finance arms) are stated.
- **Mechanics:** delisting returns included; 1 performance delisting held in 21 years, no zero or missing return (`audit_38`); missing returns enumerated (`NULL_RETURN_HOLD_FLAT_MONTHS`, any other stops the run: `13_spec_v2_portfolios.py`); costs on every trade including reinvestment in v2 (v1 omission disclosed); my gross rebuild matches to 1e-16 and Agent 2's rebuild to 0.001 bp.
- **Both benchmarks in v2:** shown together in tables, answer and benchmark section.
- **Bucket sizes:** `bucket_counts_v2.csv` and `year_by_year_v2.csv` carry names per date; none under 10 in the net rule.
- **Power:** stated in the write-up and corrected in my earlier audit (minimum detectable excess 2.13% full period, 2.8% and 3.1% subperiods; the paper's +1.7% is below it).
- **Family and SE sensitivity fixed before results (v2):** Holm family, automatic lag rule, power and the two sensitivities are in `config.py` in the first spec_v2 commit (2026-11-01 23:01), before the first v2 return file (created 2026-11-02 17:25:08). Sensitivity of the one significant result to the SE convention is shown (write-up table; my own recomputation).
- **Rules locked before results (v2):** commit evidence in section 6.
- **Report text:** every v2 number traced (`audit_45`; release review); no claim stronger than the evidence in the answer paragraph.

## 6. Rules locked before results: evidence of order

| Rule family | Evidence of order | Strength |
|---|---|---|
| v1 universe, filters, link rules (CLAUDE.md 4, 8) | `data_audit_phase1a*.md` created 00:33 to 01:00 on 11-01; `universe.parquet` created 00:25 before any returns file (01:39); CLAUDE.md 8 dated "before any returns"; single git commit after all results | File times (weak) and project lead's account |
| v1 score definitions, cleaning rules (CLAUDE.md 5, 8b) | `fscores.parquet` created 01:15, hand-check by user (project lead's account), `data_audit_phase2_3.md` 01:25; Low band changed 0-2 to 0-4 "on counts only, before any returns" (config comment, 8b) | File times and project lead's account |
| v1 portfolio mechanics, costs, benchmark (config "set before any returns") | Config comments; first returns file 01:39 | Project lead's account |
| v1 evaluation (12 lags, six factors, subperiods) | In the original brief (CLAUDE.md 5 Phase 6); single commit after results | Project lead's account |
| v1 robustness grid names | In the brief (Phase 7); config `ROBUSTNESS` | Project lead's account |
| v1 robustness definitions, Comverse hold-flat, version B boundary | Admitted as set after headline returns and after first variant runs (CLAUDE.md 8c) | Disclosed as post-results |
| Extension, REIT substitute, 100/100 | Config labels "post-write-up", "not a blind test", "set after similar variants were seen" (8d) | Disclosed as post-results |
| v2 design: `ib`, fallback exclusion, 3-day buffer, all-included benchmark, charge every trade, automatic lag, t(T-k), Holm family, power, sensitivities | Git commit, 2026-11-01 23:01:10; before first v2 return file 2026-11-02 17:25:08 | Git and file creation times (strong; commit dates are the author's) |
| v2 issuance rule revision (net of `prstkc`) | Git commit, 2026-11-02 17:18:04, after the pre-return report and the 77% issuer count, before returns | Git and file times |
| v2 clarifications (zero-debt lag 2, nulls, older-year fallback, Holm family, reinvestment charge) | Git commit, 17:19:57 | Git and file times |
| v2 hold-flat rule for Maxim and General Growth | Git commit, 17:22:32; `13_spec_v2_portfolios.py` created 17:24:57; first returns 17:25:08 | Git and file times |
| v2 designation as headline | Git commit, 17:42:04; only the `HEADLINE_SPEC` line and one comment changed (compared with the 17:22:32 commit) | Git |

The T/(T-k) correction was not in any locked version (confirmed from the first spec_v2 commit's configuration); it is a sensitivity only. Auditors compared v1 returns of dropped rows (`audit_40`, 11-01 23:05) before the older-year clarification was settled; no v2 return was read.

## 7. Could not check

- Order of v1 rules against v1 results beyond the project lead's account and the file times listed (RISK 4).
- The data vintage for FY2015-2024 (no `comp_snapshot`).
- The Piotroski Table 4 figures (not seen; transcribed by the project lead).
- Effective number of independent tests (needs a model of dependence between overlapping series; I give a range only).
- The `audit_01` to `audit_37` results themselves; I cite them without re-running.
- Whether the audit-run test counts (section 4, second table) are complete: outputs for `audit_35`, `37`, `38`, `39`, `40` are not all saved as text files, so those counts come from the scripts, not from stored output.
- Whether file creation times reflect first creation on every file (clean-folder re-run, RISK 4).
