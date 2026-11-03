# Consolidation review (Agent 1, builder role)

Scope: README.md, config.py, scripts 00-22, tests/test_signals.py, with CLAUDE.md, prereg_main.md and output/writeup.md read for contradictions. No git, no WRDS, data/ untouched.

## Edits made (computed numbers and script behaviour unchanged)
1. `22_writeup.py` docstring: removed the pointer to the non-existent `REFACTOR_REPORT.md`.
2. `22_writeup.py`: variable `V3` renamed `RES` (same path, output/results).
3. `22_writeup.py` prose (checks bullet on null returns): "+0.95% to +0.96% (t 0.86)" was stale; the tables give mean gap x12 +1.42% (t 1.03) under both rules (robustness.csv vs robustness_exit_rule.csv). Now reads "leaves the headline gap at +1.42% (t 1.03) in both cases". Reflected in output/writeup.md after rerun.
4. `config.py` comments: two "version B" comments now name the `value_filter_B` variant; docstring notes that some LONG_SHORT_100_100 / REIT_LIQUIDITY_SUBSTITUTE keys are descriptive and not read. No values changed.
5. `README.md`: write-once list now includes `01b_build_universe_buffer.py`, which also refuses to overwrite.

Checks: py_compile OK for 22_writeup.py and config.py; 22_writeup.py rerun; SHA-256 of every CSV/md in output/core and output/results identical before and after (only README.md and output/writeup.md changed, as intended). tests/test_signals.py: 9 of 9 PASS.

## Verified, no change needed
Hand-typed 22_writeup numbers matching tables: 33 names in the 2025 High list; 400 firm-years/seed 20261102; SEC sample 119 usable, 91.6%, 5.0%, 26 of 26; 191 exits; "all gaps |t| below 1.5" (max 1.44); thin value-filter bucket of 3 names; about 360 trials and critical |t| 3.8 (358, 3.81); MDE range 3.9-5.4%; REITs make High worse against both benchmarks. All config top-level names and PIPELINE keys are read somewhere (grep).

## Found, left alone
- Config keys never read by code (only descriptive): LONG_SHORT_100_100 long_scores, short_scores, reset, short_side_costs, cash_interest, sensitivity_reset; REIT_LIQUIDITY_SUBSTITUTE applies_to. Removing them would be a config.py change, so I only documented them.
- `CLAUDE.md` line 274 and `output/prereg_main.md` header point to `REFACTOR_REPORT.md`, which does not exist; the name map is in `verification/consolidation_report_agent.md`. Not edited (CLAUDE.md out of scope; prereg is a decision record). Suggest repointing.
- `CLAUDE.md` section 8i says "SPEC_V2 ... now PIPELINE": history, fine. Sections 5-8h still use old names, labelled as history in 8i.
- Variant label `value_filter_B` and config key `VERSION_B_CURRENCY` kept: they are written to CSVs / read by code.
- `22_writeup.py` mentions the earlier "Holm survivor (p 0.047)"; that p appears in no current table (history from the earlier family; prereg_main A.1 says the same). Left as history.
- `22_writeup.py` table-row f-string contains a dead `... if False else ...` branch; harmless, behaviour-preserving cleanup skipped.
- verification/ scripts still reference removed scripts (README says so).
