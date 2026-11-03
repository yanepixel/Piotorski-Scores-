# Re-audit fixes check (Agent 3, 2026-11-02)

Note: this report was written before the corrections it lists were applied. Where it describes the wording of other files, those files have since been corrected.

Scope: the uncommitted changes in the project folder on top of the last committed state (`git status`, `git diff HEAD --ignore-cr-at-eol`, read-only). Written only this file.

**Verdict: GO.** No number changed, every new figure traces, and no script line alters a computation. Five Low fixes and two statements about the public repository that I could not check are listed; none blocks.

Note on the diff size: `14_spec_v2_evaluate.py` (579 lines), `00_test_wrds.py` (97) and `README.md` (170) show large raw diffs because their line endings changed. With `--ignore-cr-at-eol` the real changes are 33, 9 and 12 lines.

## (1) New figures in the write-up

Traced and correct:
- **"How many tests were run" section.** "About 250" and "252 distinct", "288 re-estimates" and "about 400 counting audit runs" match my trial log (`audit_checklist_run_agent3.md` section 4: 252 distinct; 288 convention re-estimates; about 400 with audits).
- **Critical |t| table** (1.98, 2.68, 3.09, 3.37, 3.58, 3.84 for N = 1, 6, 20, 50, 100, 250): equal to `t.ppf(1 - 0.05/(2N), 122)`, which I computed independently; they match to two decimals. The script computes them from the 2015-25 alpha's own degrees of freedom (122).
- **The 2015-25 four-factor alpha against t = 3.** t -2.70 clears 2.68 (N = 6) and not about 3 (N = 20 gives 3.09); -2.65 with the T/(T-k) correction, -2.94 at lag 6 and -3.72 at lag 12: all match `tests_v2.csv` and my recomputation.
- **"All |t| of 3 or more are shortfalls."** I scanned every CSV under `output/` (excluding the archive and logs) for |t| of 3 or more: 22 cells, all negative, all the 2015-25 High alpha (the v1 headline, six of the nine robustness variants, the extension, the REIT substitute, and the v2 lag-6, lag-12 and six-factor versions). True. "Most are variants of the same second-half series" is true and could say "all".
- **No-held-out sentence.** Matches my section 3 (whole sample seen in v1; extension added after the results and the second-half weakness; five months cannot support an alpha test; v1 order rests on the project lead's account).
- **Terms added** (degrees of freedom, T/(T-k), Compustat/CRSP, RSP and SPY, formation date): accurate.
- **Coverage lines** in the regenerated reports: I checked them against the parquet files: 8,414 list rows from 930 companies, 857 scored; by bucket High 547, Middle 790, Low 441, Unscored 170; 18,265 company-years from 1,122 companies, 14,111 scored from 935 companies. All match.

## (2) v1 versus v2 section against the archive

- "v1 had already reported this comparison as a post-hoc sensitivity (High +0.19% a year against all included names, t 0.22)": confirmed at `output/archive_v1/writeup_v1.md:174` ("a sensitivity seen after results that changed no rule ... High's raw gap is +0.19% a year (t 0.22), with alpha -0.44% (t -0.45)"). The script reads the figure from the archive text by pattern, so it cannot drift.
- The sentence "so the flip is a change of which benchmark is primary, not a new finding" is accurate.
- Earlier-year fallback bullet: "43 list rows to an earlier year, 4 stale, 3 with no earlier scored year": matches my counts exactly.
- The benchmark caveat for the three v1-specification runs ("scored-only runs 0.50% a year above the all-included, so these excesses would look about that much better against all included names, and the all-included comparison was not computed") is correct in direction and size (the two benchmarks differ by 0.50% in mean excess, 0.57% in CAGR). It is approximate because those runs use v1 scores.

## (3) Statements about the public repository versus the project

- Accurate and clear, as far as the project side shows: only `headline_v2.csv` and `tests_v2.csv` from `literal_sensitivity/` are in the allowlist; `output/extension_2026/validation.md` is excluded by `.gitignore`; the public `verification/` holds reports only. The removal of the "8.4 points on a single stock" figure (a company-level value) in the extension paragraph is applied by script 17 with an assertion that the old text is present.
- **Not checked by me** (I was told not to touch `public_release`): (a) the claim in the Verification paragraph that "the public `04_scores.py` also differs from the project's in explanatory comments only"; (b) the new `CLAUDE.md` 8f sentence "the public repository was updated to match". If the push has not happened when this is committed, (b) should read "will be updated to match".
- **Low:** the Verification paragraph says the v1 scripts, v1 outputs and "all earlier raw and clean data files were checked unchanged by hash after each v2 stage". What I can confirm is the end state: `git status` shows no modified v1 script or output; the seven first-pull raw hashes in `output/logs/pull_raw_hashes.csv` and the four added hashes in `raw_hashes_added.csv` match the files; the two v2 raw pulls match their logs. There is no stored hash baseline for `data/clean/*.parquet` (git does not track `data/`), and I saw no record of a per-stage check. Fix: "checked unchanged by git comparison (scripts and outputs) and by SHA-256 (the raw files); the cleaned data files have no stored hash".

## (4) Terms defined on first use

- Write-up answer paragraph: t-stat, p-value, alpha, 80% power, Holm, Newey-West are all defined where first used. **Low:** "High" and "F-score of 8 or 9" are used before the Terms section. Fix: in the first sentence write "those with an F-score of 8 or 9 (High: the companies scoring 8 or 9 out of 9 financial-health tests)".
- README answer paragraph: t-stat, four-factor alpha, Newey-West lag, Holm and power are defined. **Low:** "adjusted p 0.047" uses p without defining it. Fix: "adjusted p-value 0.047 (the chance of a result at least this extreme if there were no effect, after the Holm correction)".

## (5) Script diffs: can any line change a number?

No. Line by line (`git diff HEAD --ignore-cr-at-eol`):
- `12a`, `12c`: a new `--log-only` branch that reads the stored raw file and appends a coverage section to the log; the pull path is unchanged and still refuses to overwrite.
- `12b`: one assertion that `fallback_availability == "exclude"` (config value is "exclude") and one added report line. No score logic touched.
- `13`: one added report line (unique companies by bucket). No portfolio logic touched.
- `14`: `ALPHA, POWER` now read `alpha_level` and `power_level` from `SPEC_V2`; `LAG_A, LAG_B` read `sensitivity_lags`; the correction flag reads `sensitivity_small_sample_correction`. The config values are 0.05, 0.80, [6, 12] and True, identical to the constants that were hard-coded before (I read the earlier code: 0.05, 0.80, lags 6 and 12, `correction=True`). Column names (`lag6_t`, `lag12_t`, `holm_p_lag6`, ...) are unchanged because they are built from the same numbers. Four assertions check that other `SPEC_V2` keys equal the behaviour coded; all hold. The rest is report text.
- `16`: the sensitivity lags read from config (6 and 12, as before).
- `17`: new text, the critical-t table, hand-copied entries, the benchmark caveat and the public-repository sentences. It does not compute any return or test.
- Evidence that no number moved: `git status` shows none of `tests_v2.csv`, `headline_v2.csv`, `portfolio_returns_v2.csv` or any other v2 numeric table as modified; the only changed outputs are `.md` reports (coverage lines added), the two pull logs (coverage sections added) and `writeup_figures_v2.csv` (17 new figure rows, 2 rows re-sorted). `config.py`: no existing value changed (diff shows four new keys, comments and a docstring); `NEWEY_WEST_LAGS` is only annotated. I searched scripts 12b, 13, 14, 16 and 17 for `NEWEY_WEST_LAGS` and `SIGNIFICANCE_T_STAT`: no reads, as the new docstring says.
- `00_test_wrds.py` adds six tables to the access check; `requirements.txt` adds `scipy==1.18.1`, which is the installed version (statsmodels 0.15.0, pandas 2.2.3, pyarrow 26.0.0 and numpy 2.5.4 also match).

## (6) Raw-file hashes

`output/logs/raw_hashes_added.csv`: the four sha256 values equal mine (comp_fundq f43e33da..., comp_co_filedate_quarterly 12a0e53e..., comp_funda_reit_fields 1581cbaa..., comp_secm_extension 57c0386b...) and match the files; bytes and rows match (85,580; 62,276; 20,796; 9,392 rows). The note field says "hashed after the fact, not at pull time", which is accurate. The log refers to my audit file by name, which is fine in the project (not in the public allowlist).

## (7) `CLAUDE.md` 8f: history described accurately?

Mostly. Against git (first commit 11-01 23:01, then 11-02 17:18, 17:19 and 17:22; first v2 returns file 17:25:08; designation commit 17:42):
- "The specification below was fixed before any v2 return existed": true for the specification and the clarifications.
- **Low:** the new heading says only the Designation paragraph "was added after", but the paragraph "Section 8f overrides the earlier sections ..." and the "Implementation notes, added after the returns" paragraph were also added after, as the notes themselves say. The heading date "2026-11-02" is also when the revisions were made; the section first appeared on 2026-11-01 at 23:01. Suggested heading: `## 8f. spec_v2: re-specification after external review (first committed 2026-11-01 23:01; revised and clarified 2026-11-02, all before any v2 return existed; the override sentence, implementation notes and Designation were added after the returns)`.
- Implementation note (a), "nine firm-years differ between the two readings and none is scored under either": verified. Of 18,265 company-years, 9 differ between `LEVER_{t-1}` computable and `lag2_ok` for the zero-debt override, and all 9 have no score.
- Note (b), no reinvestment charge for an exit in the final holding month, "none of the 191 exits is in that position": true by construction (an exit is defined as a last return before the final month).
- Note (c), constants moved to `SPEC_V2` keys: verified (item 5).
- The 8d change (v1 write-up now at `output/archive_v1/writeup_v1.md`) is accurate.

## Fixes (all Low, none blocking)

1. `CLAUDE.md` 8f heading: replace as above (cover the override sentence, implementation notes, and the first-commit date).
2. `CLAUDE.md` 8f: confirm "the public repository was updated to match" is true when committed, or change to "will be updated".
3. Write-up Verification paragraph: replace the "checked unchanged by hash after each v2 stage" wording as in section 3; confirm the clause about the public `04_scores.py`.
4. Write-up answer paragraph: define High and F-score at first use; README: define "adjusted p".
5. `17_spec_v2_writeup.py` `HAND` entries "252", "288", "400", "250" read "Agent 3's trial log (verification/audit_checklist_run_agent3.md ...)" and are written into `output/spec_v2/writeup_figures_v2.csv`, which is on the public allowlist. Replace "Agent 3's trial log (...)" with "the project's trial log of tests (verification/audit_checklist_run_agent3.md, section 4; not in the public repository)", and the same for the three "same trial log" entries.
