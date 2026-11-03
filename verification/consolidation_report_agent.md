# Consolidation report (2026-11-03)

Work was done only in the scratchpad copy `consol`. The original project was read only, as the reference for comparisons. No git, no `public_release`, no credentials printed.

## 1. Old to new name map

Scripts (old name -> new name):

| Old | New |
|---|---|
| 00, 01, 02, 03 | unchanged (03 report text now points at `05_scores.py`) |
| (inside 08_robustness: universe-buffer builder) | `01b_build_universe_buffer.py` (new, extracted) |
| (inside 08_robustness: `pull_quarterly`) | `02b_pull_quarterly.py` (new, extracted) |
| (inside 09a_extension_pull: the comp.secm pull) | `02c_pull_extension.py` (new, extracted) |
| 12a_spec_v2_pull / 12c_spec_v2_pull_prstkc / 12d_single_vintage_pull | `04a_pull_ib.py` / `04b_pull_prstkc.py` / `04c_pull_single_vintage.py` |
| 04_scores (SIGNALS, lag_inputs) + 05_align (exact_quantile) + 12b_spec_v2_scores | `05_scores.py` |
| 13_spec_v2_portfolios / 14_spec_v2_evaluate / 15_spec_v2_drops | `06_portfolios.py` / `07_evaluate.py` / `08_drops.py` |
| 18_v3_inference | `09_inference.py` |
| 19_v3_numcheck (independent) / 16_spec_v2_numcheck (arithmetic) | `10_numcheck_independent.py` / `11_numcheck_arithmetic.py` |
| 20_v3_cost_sensitivity | `12_costs.py` |
| 22_v3_robustness / 27_v3_robustness_extra | `13_robustness.py` / `14_robustness_extra.py` |
| 23_v3_null_return_rule | `15_null_return_rule.py` |
| 25_v3_long_short | `16_long_short.py` |
| 26a_pull_cik / 26b_sec_vintage_check | `17a_pull_cik.py` / `17b_sec_vintage.py` |
| 28_v3_extension_2026 / 29_v3_reit_liquidity | `18_extension.py` / `19_reit.py` |
| 30_v3_bm_replication | `20_bm_replication.py` |
| 24_hash_raw / 21_v3_writeup | `21_hash_raw.py` / `22_writeup.py` |
| tests/test_signals.py | same name, updated (loads `05_scores.py`) |

Numbering has letter suffixes (01b, 02b, 02c, 04a-c, 17a-b) for stages with several scripts; the numeric stages 00 to 22 are contiguous.

Folders and files:

| Old | New |
|---|---|
| `output/spec_v2/literal_sensitivity/*_v2.csv` | `output/core/*.csv` (primary) |
| `output/spec_v2/*` (net rule, root) | `output/core/net_sensitivity/*` |
| `output/spec_v3/*_v3.*` | `output/results/*` |
| `output/prereg_v3.md`, `prereg_v3_bm.md` | `output/prereg_main.md`, `prereg_bm.md` (script names and paths inside updated; a consolidation note added; the history wording "v1/v2/v3" kept as decision record) |
| `data/clean/spec_v2/{fscores,formation}_v2[_literal].parquet` | `data/clean/core/{fscores,formation}.parquet`; net in `data/clean/core/net_sensitivity/` |
| `output/robustness/universe_buffer/universe.parquet` | `data/clean/universe_buffer.parquet` |
| pull logs (`output/spec_v2/pull_*_log.md`, `output/spec_v3/single_pull_log.md`) | `output/logs/` (moved unchanged; deviation from the folder mapping because they are pull logs) |
| `output/logs/raw_hashes_v3.csv`, `raw_hash_compare_v3.csv` | `raw_hashes.csv`, `raw_hash_compare.csv` |
| `data/external/extension_2026_v3_names.csv`, `reit_liquidity_v3_rows.csv` | `extension_names.csv`, `reit_rows.csv` |
| column `avail_date_v2` | `avail_date_buffered` (the cleaned fundamentals still carry the older fallback-based `avail_date`; see section 6) |
| config `SPEC_V2` | `PIPELINE` (label `core`, output_dir `output/core`); `NULL_RETURN_HOLD_FLAT_MONTHS` keys `spec_v2` -> `pipeline`, `spec_v2_reruns` -> `extension_and_reit` |
| table columns `v2_X` / `v3_spec` / `v3_baseline` / `v3_variant` / `change_v3` | `X` / `value` / `baseline` / `variant` / `change` |

Default rule is now literal in 05, 06, 07, 08, 11 (`--rule net` writes the net sensitivity).

## 2. Deleted, with reason

- Scripts of the first specification, superseded: old 04_scores, 05_align, 06_portfolios, 07_evaluate, 08_robustness, 09_reit_liquidity, 09a_extension_pull, 10_extension_2026, 10a_extension_contributors, 11_long_short. Reason: no live script depends on them after extracting the signal code, `exact_quantile`, the buffered-universe builder and the two pulls.
- 12a-12d and 13-30 under their old names (renamed, not lost); 17_spec_v2_writeup.py (deleted as briefed).
- Outputs: `output/tables`, `charts`, `robustness`, `extension_2026`, `reit_liquidity_substitute`, `long_short_100_100`, `archive_v1`, `archive_v2`, old `spec_v2` and `spec_v3`; v1 logs (`evaluate_log`, `formation_*`, `portfolio_checks`, `portfolio_exits`, `robustness_log`, `scores_checks`, `scores_drops`).
- Data: `data/clean/fscores.parquet`, `formation.parquet`, `spec_v2/`; `data/raw/comp_funda_reit_fields.parquet` (its `che` and `lt` are cell-for-cell identical to `comp_funda_single.parquet`, checked on all 20,796 rows, so `19_reit.py` reads them from there and no REIT pull script exists).
- Version-comparison content removed from scripts: `list_rows_by_bucket_v1_v2*`, `list_rows_by_date_v1_v2*`, `list_rows_bucket_transition*`, `writeup_figures_v2.csv`; v1 columns in the score distribution, pass rates, eq-offer-by-year, unscorable list, headline, drops, extension (`v1_spec`, difference, note) and REIT tables (`v1_headline`, `v1_variant`, `change_v1`, the `v1_only` block); the v1 security-map check in 18; the v1-versus-v3 sentences and the v1 CAGR (11.44%) in the write-up.
- Dead code removed: `count_trials()` in 09 (never called); local copies of `exact_quantile` in 14.
- Not touched: `verification/` (historical reports and audit scripts, some of which refer to the removed scripts; they are not part of the pipeline).

## 3. Config keys removed (proven unused by grep of every live script and the tests)

BOOK_EQUITY_RULE, BUFFER_NULL_RETURN_RULE, CAP_WEIGHT_BASIS, CHARGE_MIDPERIOD_REINVESTMENT, CHARGE_PRIMARY_BENCHMARK, COST_TIMING, DATA_SOURCE, EIGHT_SIGNAL_NULL_RETURN_RULE, EXPECTED_SPAN_GVKEYS, HEADLINE_RETURNS, HEADLINE_SPEC, HEADLINE_VERSION, HIT_RATE_COMPLETE_YEARS_ONLY, LONG_SHORT_SPREAD, MIN_CSHO_FOR_SHARE_TEST, NEWEY_WEST_LAGS, PRIMARY_BENCHMARK, PROFITABILITY_SCREEN, PROFITABILITY_SCREEN_SCOPE, QTR_SELECTION, QTR_UNCONFIRMED_RULE, REIT_PULL_FIELDS, SCORE_AGE_BASIS, SECTOR_NEUTRAL_EMPTY_SECTOR, SECTOR_NEUTRAL_WEIGHTS, SHARE_ISSUANCE_TOLERANCE, SIGNIFICANCE_T_STAT, STANDARD_ERRORS, TURNOVER_BASIS, UNIVERSE, UNIVERSE_BUFFER, V2_RERUNS, WEIGHTING; inside dicts: `ROBUSTNESS` trimmed to `universe_buffer` (the only entry read), `NULL_RETURN_HOLD_FLAT_MONTHS` keys `eight_signal_no_liquidity` and `reit_liquidity_substitute`, `PIPELINE["sensitivities"]`. Several of these only documented behaviour the code implements (for example WEIGHTING, TURNOVER_BASIS, COST_TIMING); that behaviour stays described in CLAUDE.md.
Only renamed keys were added. A check against the original `config.py` found no value difference for any remaining key (PIPELINE compared without `label` and `output_dir`, which are the renamed path/label).
Two live scripts now read config values they previously hard-copied, with identical values: `14_robustness_extra.py` reads `EIGHT_SIGNAL_HIGH_SCORES`, `EIGHT_SIGNAL_LOW_SCORES` and `NULL_RETURN_HOLD_FLAT_MONTHS["universe_buffer"]`.
Unread inner keys of the labelled-variant dicts (`REIT_LIQUIDITY_SUBSTITUTE`, `LONG_SHORT_100_100`, `EXTENSION_2026`) were left in place as documentation.

## 4. Verification

1. **Compile and tests.** Every script compiles (`python -m py_compile`). `python tests/test_signals.py`: all 9 pass, including the planted-bug test, against `05_scores.py`. `pytest` is not installed here, so `python -m pytest` was not run.
2. **WRDS-free run.** After deleting all superseded files, every non-WRDS stage ran in README order against CONSOL's data (05 to 08 and 11 with both rules; 09, 10, 12 to 16, 17b, 18 to 22), all with exit 0 (rerun from empty `output/core`, `output/results`, `data/clean/core`). 17b used the SEC cache in `data/external/sec` and needed no network.
3. **Result comparison against the original project** (script `scratchpad/compare.py`, pandas, exact equality, not tolerance): all 43 retained CSVs match (42 exact, 1 with a wording-only difference); 7 original files were removed on purpose (v1 comparison tables and writeup_figures_v2.csv). Old `spec_v3` (11 CSVs), old `literal_sensitivity` (as `output/core`) and old net root (as `output/core/net_sensitivity`, including drops, score distribution, pass-rate and unscorable tables) have identical numbers in every column that still exists. The only differences: removed v1 columns and tables (section 2), renamed columns, and wording in one text column (`tests.csv` status: "after seeing earlier results" versus "after seeing the earlier results"). `data/external/extension_names.csv`, `reit_rows.csv` and `sec_vintage_rows.csv` are identical to the originals. The new literal drops tables (`output/core/drops_*.csv`) have no original counterpart: the old drops script ran on the net rule only, and scorability differs between the rules (the net rule makes a missing prstkc unscorable), so literal drops numbers are new, not changed. Write-up and README answer block: every numeric token matches the original except the removed v1 CAGR (11.44%), version numbers in text and script numbers; the README answer block matches exactly apart from the "v1/v2" mentions.
4. **Pull scripts.** Tested in a second scratch copy (`scratchpad/consol2`) with the target raw files absent, read-only WRDS queries: `02b`, `02c`, `04a`, `04b`, `04c`, `17a`, `01b`. Results compared with the originals: comp_fundq, comp_co_filedate_quarterly, comp_secm_extension, comp_funda_ib, comp_funda_prstkc and comp_company_cik are byte-identical; comp_funda_single is equal in every cell (bytes differ only by the pull timestamp column); the buffered universe is byte-identical to the original and the script's own check that its plain path reproduces the headline universe passed. Write-once guards were not run against existing files in CONSOL, only read in code. `00`, `01`, `02` and `03` were not rerun (unchanged, WRDS).

## 5. Behaviour changes

- Default rule is literal everywhere (as decided); the net rule writes to `net_sensitivity`.
- `04c` no longer compares the single pull with the REIT pull (that file was removed), so a rerun would write a log without that block; the stored `single_pull_log.md` is the original text.
- `02b` and `02c` refuse to run when their raw files exist (the old scripts silently reused them); they otherwise run the same queries.
- `18_extension.py` takes company names from the comp.secm names instead of the saved v1 map; the names file came out identical.
- `19_reit.py` reads `che`/`lt` from the single-vintage pull (identical values).
- Texts, reports and printed labels changed to plain terms; a few write-up sentences were removed or reworded where they existed only to compare versions.

## 6. Not done, not testable, flagged

- Typed figures in the write-up prose bullets (for example "+0.95% to +0.96%", "191 exits", "119 usable firm-years", "91.6%", "33 names", "p 0.047", "about 360 trials") were kept as typed; they were not regenerated from tables, as before.
- `03_clean.py` still writes the older fallback-based `avail_date`, `avail_source` and `filing_lag_days` columns into `fundamentals_clean.parquet`; nothing live reads them. Left as briefed (03 kept unchanged apart from one text string).
- `verification/` scripts and reports still name the removed scripts and old paths; they were not edited.
- CLAUDE.md sections 5 to 8h still describe earlier script names as history; section 8i was added. The git tag `archive-v1-v2-v3-pre-consolidation` is named in the text but was not created here (no git).
- The comparison and second-copy files live in `scratchpad/` (`compare.py`, `consol2/`, `config_before.py`) outside CONSOL; they are scratch.
- `output/logs/raw_hashes_added.csv` (hashes of the quarterly pulls recorded earlier) was kept as a record.
