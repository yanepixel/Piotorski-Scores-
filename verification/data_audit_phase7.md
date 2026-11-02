# Phase 7 audit: robustness runs and draft write-up

Report only. I edited no pipeline code or settings. No rule change here is recommended because of performance. The one project file I changed is my own earlier report, `data_audit_phase4_6.md`, to correct a rounding error (see M2).

Terms: **variant** is a rerun with one setting changed. **Look-ahead** means using something not yet known on the date. **Alpha** is return left after accounting for market, size, value, profitability, investment and momentum factors. **t-stat** is how many standard errors a number sits from zero. **Effective number of tests** estimates how many truly separate tests a set of correlated ones amounts to.

Files tested (SHA-256, first 14 characters), unchanged at the end of testing: `08_robustness.py` 5A3CE6D161C550, `output/writeup.md` E128B737A8622E, `config.py` CA766BB0B74E6F, `07_evaluate.py` 976E05339FE8BE, `robustness_comparison.csv` 9D036393A64934, `robustness_subperiods.csv` 0A52B2BB59FB1C.

Evidence: `verification/audit_19_phase7.py`, `audit_20_trace_writeup.py`, `audit_21_loose_ends.py` and their `_output.txt` files; `phase7_baseline_hashes.csv`.

## Result

**No High findings. I found no look-ahead in the screen, buffer or Version B timing, the headline is unchanged, and every variant reproduces. The first paragraph answers the question and isn't stronger than the evidence, apart from small rounding errors. Four Medium items should be fixed before the write-up is final.**

| ID | Severity | Finding | Who acts |
|---|---|---|---|
| M1 | Medium | "The time pattern holds ... 8 of 9" reads as confirmation, but the variants mostly share holdings | Master session: reword |
| M2 | Medium | Four wrong figures in the draft, including the headline alpha and its t | Master session: correct |
| M3 | Medium | A float boundary leaves 7 rows out of Version B, moving its High alpha from -1.11% to -0.87% | User decision |
| M4 | Medium | The draft lacks the "-2.5 to -3.6" range that section 8c requires | Master session: add |
| L1-L8 | Low | See the Low findings section | Noted |

## (b) Which headline alpha is correct

**Correct: -0.78% a year, t -0.71.** The exact values are -0.77803% and t -0.71457, confirmed by my separate calculation.

| Source | Alpha | t | Status |
|---|---|---|---|
| `factor_regressions.csv` | -0.0077803 | -0.71457 | Correct |
| `robustness_comparison.csv` | -0.0077803 | -0.71457 | Correct |
| `checkpoint3_results.md` | -0.008 | -0.715 | Correct to 3 decimals, and the origin of the error |
| `writeup.md` robustness table, line 93 | -0.78% | -0.71 | Correct |
| `writeup.md` answer, line 9 | -0.8% | -0.72 | t wrong |
| `writeup.md` regression table, line 65 | -0.80% | -0.72 | Both wrong |
| `writeup.md` quoted context, line 75 | -0.8% | -0.72 | t wrong |

**Cause:** rounding an already rounded number: -0.008 was shown as -0.80%, and -0.715 as -0.72. I made the same t error in my Phase 4-6 report and in the suggested wording the draft quotes, so part of this is mine. I have corrected that report.

## (a) Figures traced

A script checked 231 figures against source files, rounded as the draft shows them: 3 mismatches. Reading the remaining text claims against logs and tables found 1 more.

### M2. Medium: all mismatches

| Line | Item | Draft | Correct | Source |
|---|---|---|---|---|
| 9 | Answer: High alpha t | -0.72 | **-0.71** | `factor_regressions.csv` |
| 65 | Regression table: High alpha | -0.80% | **-0.78%** | `factor_regressions.csv` |
| 65 | Regression table: High alpha t | -0.72 | **-0.71** | `factor_regressions.csv` |
| 66 | Regression table: Spread HML | 0.08 | **0.07** (exact 0.0748) | `factor_regressions.csv` |
| 75 | Quoted context: full-period t | -0.72 | **-0.71** | `factor_regressions.csv` |
| 180 | "Dell FY2018-19" looks invalid | FY2018-19 | **FY2018 only** | `permco_joins_review.csv` reads FY2019's ratios as "the same business" |

The Spread alpha t of -0.72 on line 66 is correct (exact -0.7238). These are the only numeric mismatches, and none changes a conclusion. They matter because the headline currently appears with two values in one document.

**Everything else matched,** including all performance, excess-return, subperiod, score, robustness, name-count, screen, overlap, coverage, exit and drop-table figures.

**Checked by reading, against audit files rather than project tables:** the quoted -2.47, -3.06, -1.3%, 19%, 1.5% and 11% match `audit_18_output.txt`. The restatement figures 1,480, 98.5% and 0.2% match `audit_14_output.txt`.

**Not traceable to a file I can check:** the user's 10-K hand-check is taken from section 8b of `CLAUDE.md`.

## (c) Are the 2015-25 variants independent? No

| Variant | Share of its High also in headline High | Share of headline High it holds | Residual correlation with headline, 2015-25 | t, 2015-25 |
|---|---|---|---|---|
| Lag 90 days | 100% | 100% | 1.000 | -4.10 |
| Costs 25 bps | 100% | 100% | 0.999 | -4.45 |
| Eight-signal | 98% | 100% | 0.997 | -4.33 |
| Profitability screen | 100% | 95% | 0.980 | -4.17 |
| Universe buffer | 98% | 95% | 0.984 | -3.41 |
| Sector-neutral | 100% | 100% (different weights) | 0.873 | -3.36 |
| High cutoff 7+ | 45% | 100% | 0.792 | -2.61 |
| Version B | 100% | 31% | 0.598 | -2.68 |
| Cap-weighted | 100% | 100% (different weights) | 0.325 | **-0.87** |

- **Effective number of tests:** about 4 to 5 across all 10 series (Nyholt 4.7, Li-Ji 4.0).
- **Lag 90 days is the headline.** Costs 25 bps holds the same stocks with a higher charge. Those two rows add no evidence.
- **The variant least like the headline by correlation, cap-weighted, is the one that isn't significant.** That matters more than the count: the shortfall is much weaker when large companies carry more weight.
- **The lag caution applies to all of them,** and the random-portfolio context was measured only for the headline.

### M1. Medium: reword line 130

The draft does state the lag and benchmark cautions, but "The time pattern holds" and "8 of 9" invite counting them as separate confirmations, and nothing says they overlap. Suggested text:

> "**The time pattern is not independently confirmed.** High's alpha is lower in 2015-25 than 2005-15 in every variant, and it reaches |t| of 2 in 8 of 9. These are not separate tests: most variants hold nearly the same stocks (Lag 90 days is identical to the headline), and across all 10 series there are only about 4 to 5 effectively separate tests. The variant that differs most, cap-weighted, is not significant (t -0.87). The same lag caution applies, and the benchmark itself runs negative in that period."

**Multiple testing overall:** the robustness tables and files hold 60 alpha tests: 30 for High and 30 for Spread (full period and two subperiods, 10 series). None is significant over the full period. The single Spread result at |t| of 2 (cap-weighted 2015-25, -2.03) is what chance could produce among this many tests (L3).

## (d) The first paragraph

**It answers both parts of the question in the brief, and it isn't stronger than the evidence.**

- **Did High beat the universe?** "No": 10.91% against 11.35% after costs, 10 of 20 years. Accurate.
- **Does outperformance survive the factors?** It states alpha "not distinguishable from zero". There's no outperformance to survive. Accurate, once the t is corrected.
- **Scope limit:** it says the test covers large US companies and doesn't test Piotroski's original claim. Good.
- **"Similar risk":** volatility 16.79% vs 16.17%, drawdown -44.4% vs -49.1%. Fair.

**Two improvements (L4), neither required:**
- "No" could be read as proof that no edge exists. The 95% ranges are wide: excess return -2.0% to +1.4% a year, alpha -2.9% to +1.4%. One clause would say a small edge in either direction can't be ruled out.
- "Worse in the second" doesn't mention the 2015-25 alpha reaching significance. That understates rather than overstates, and the context follows later.

## Variant checks

**Rebuilt with my own engine:** all 10 series match the published returns, alpha and t with no measurable difference.

| Variant | Separate membership rebuild | Result |
|---|---|---|
| Headline copy | Published held rows and counts | Same |
| Eight-signal | Own scoring and asof | 8,212 rows, 0 bucket differences; 641 eight-signal rows (31, 578, 32) |
| Universe buffer | Own ranks from the raw May panel | All 21 lists identical |
| Profitability screen | Own quarter logic | 6,582 passes, same set |
| Version B | Own book-to-market | Same set using `1 - 1/3`; see M3 |

The draft's independent-check caveat on line 228 can be updated once these findings are dealt with (L8).

### Profitability screen: no look-ahead found

- **30,284 quarter rows used: 0 available after formation, and 0 with a quarter-end after it.**
- **Dates:** the earliest non-amendment 10-Q or 10-K filing after quarter-end. Only 0.12% of used rows use the 120-day fallback, and 26 list rows have a fallback quarter as their newest.
- **Against EDGAR:** in a sample of 199 used quarters, 194 matched by report date. 193 are exact, and one is 3 days later in Compustat, which is conservative. None is earlier.
- **Typical timing:** 83% of latest quarters end in March, reported by the May date, and the median age is 2 months.
- **Limit:** `niq` is current Compustat, so it carries the same restatement limit as the annual data. The draft doesn't say so (L2).

### Universe buffer: no future ranks

The rule uses only the prior list and that date's rank, and every rank in the file equals that date's rank. 2005 equals the top 500, as configured. 338 list rows are kept at rank 501-550. Sizes of 481-501 and scored names of 318-377 are correct.

### Version B: same fiscal year, available at formation

All 7,571 held rows take book equity from the same fiscal year as the score, with the same availability date, and none is available after formation. Market cap is from the formation date. No non-positive book rows or non-USD rows are in the cheapest third.

### M3. Medium: float boundary in the Version B cutoff

`05_align.py` uses `1 - cfg.VALUE_FILTER_QUANTILE` (0.6666666666666667), rather than exactly two-thirds. When the quantile lands exactly on a stock, that tiny difference pushes the cutoff just above it, so the stock is left out, though `>=` means it should be in. This affects 7 rows on 7 dates: Coventry 2007, Bath & Body Works 2008, Constellation 2014, Target 2016, Cerner 2021, AMD 2023, TransUnion 2025.

| Version B High | As run (2,523 rows) | With exact two-thirds (2,530 rows) |
|---|---|---|
| Alpha, full period | -0.87% | -1.11% |
| t, full period | -0.46 | -0.59 |
| Alpha, 2015-25 | -5.10% | -5.51% |
| t, 2015-25 | -2.68 | -2.91 |

Two of the seven (Target, TransUnion) are High names, in a bucket with a median of only 23. No conclusion changes, and the headline is unaffected: this column is used only by Version B. It does show how sensitive this thin variant is to one or two names, which is worth saying regardless.

**For the user:** either fix it as a mechanical correction and rerun Version B, or keep it and disclose it. The fix would change `formation.parquet`'s hash, though not its headline columns. The choice should rest on the rule's meaning, not on these numbers.

## Headline unchanged

Of 41 baseline files, 38 are unchanged, including all pre-existing raw data, `formation.parquet`, `portfolio_returns.csv`, `factor_regressions.csv`, `performance.csv` and `subperiods.csv`.

| Changed file | Reason found |
|---|---|
| `07_evaluate.py` | Report text: adds caution on rank correlation and the significance line. Tables stayed byte-identical. |
| `checkpoint3_results.md` | Same report text, from the rerun |
| `config.py` | Adds robustness definitions. Headline settings match those used. |

I recorded only hashes, so I can't show a line-by-line diff of `config.py`. The evidence that headline settings are unchanged is that every headline output is byte-identical after the rerun. New raw files `comp_fundq` and `comp_co_filedate_quarterly` were added, with no existing raw file edited.

## Disclosures: all present except one

| Section | Status |
|---|---|
| 8: mortgage REITs and iStar, sibling links, Eaton and Ceridian, no-sector exclusions, stopped trading, UG and Cboe, 375-425 range, 2021 flag, 2020 dip, Visa/Mastercard/PayPal, CBRE, Dell and Liberty | Present |
| 8b: Low 0-4 and why, traditional REITs etc. excluded, 2025 partial, non-USD, score age, May 2005, mergers and 270 rows, cleaning rules | Present |
| 8c: variant timing | Present |
| 8c: 2015-25 alpha context, "t about -2.5 to -3.6 is defensible" | **Wording present, range absent (M4)** |
| 9: 20 GVKEYs, 4 formation-date delisters, CAD, late filings, RSP chain, ties and inversions, 13 older-year and 15 same-day rows, restatement text, 2025 partial | Present |
| Brief section 6: proxy and overlap, fallback share, dropped company-years, no shorting costs | Present |

### M4. Medium: add the range

The quoted text says "a t nearer -3.4 to -4.0", which comes from my suggested wording and describes only the simulation results. Section 8c says "-2.5 to -3.6 is defensible". The two aren't in conflict, since the wider range also includes the unadjusted figure, but my own report gave both without reconciling them, and the draft shows only the higher one. Suggested addition after the quote: "Taken together, a t of about -2.5 to -3.6 is defensible, not -4.10 alone." In the same quote, change the full-period t to -0.71.

## Low findings

- **L1. Lag 90 explanation (line 133).** "No list row changes, because only 6 of 7,571 chosen rows use the fallback date" isn't quite the reason. A shorter lag changes a row only if a fallback date crosses a May date. Exactly one could (UiPath, FY ending January 2021, May 2021 list), and no row changes because that year doesn't supply a score there. Suggested: "no list row changes: only one fallback date crosses a May date, and it changes no score."
- **L2. Screen data limit.** Add that quarterly net income has the same restatement limit as the annual data, and that 26 list rows have a fallback date on their newest quarter.
- **L3. Cap-weighted spread (line 132).** The t of -2.03 is singled out. Add that it's one of 60 alpha tests.
- **L4. First paragraph.** Consider the 95% range clause in section (d).
- **L5. Terms not defined in the draft (brief rule 8).** Tracking error, information ratio, REIT, GICS and rank correlation.
- **L6. Version B book equity rule isn't described:** `ceq + txditc`, null `txditc` as zero, non-positive book stays ranked and is never cheapest.
- **L7. Timing claim.** "Before any variant's returns" fits the code, which shows no results for a stopped variant. But `config.py` changed after my baseline, and the Comverse rule appears to have been added after a run stopped on it. I can't confirm the order from files, so the master session should confirm it.
- **L8. Line 228 status.** "The independent check of the robustness runs is not yet complete" should be updated once these findings are dealt with.

## What this doesn't establish

Matching a file shows a figure was copied correctly, not that the underlying data is true. The EDGAR samples test filing dates, not earnings values. The overlap and correlation figures describe holdings and residuals in this sample; the effective number of tests is an approximation.


## Final check, 2026-11-01

Scope: `output/writeup.md` C77BA3D91A69FA. Report only. Evidence: `verification/audit_22_trace_final.py`, `audit_22_final_extra.py`, `audit_22_variants_final.py` and their `_output.txt` files.

**Result: no figure mismatches, and no sentence rests on Version B's first-run result. All of M1-M4 and L1-L8 landed. One optional wording point (N1) and one cosmetic point (N2) remain. No High or Medium findings.**

### Figures

The script re-traced 231 figures, including every Version B line. It flags 6, all from my own test labels rather than the draft: its text check looks for the label as I wrote it (`6582`, `74 of 1553`, `8414`, `7571`, `34 across 8`, `1/1`), while the draft writes `6,582`, `74 of 1,553`, or puts it in words. All 6 values agree with their files.

New text, checked separately:

| Item | Draft | File or recomputed |
|---|---|---|
| Excess return range | -2.0% to +1.4% | -1.99% to +1.40% |
| Alpha range | -2.9% to +1.4% | -2.91% to +1.36% |
| Version B High minus Benchmark | -0.00% | -0.0017% (t -0.00) |
| Version B High alpha | -1.11%, t -0.59 | -1.1077%, t -0.586 |
| Version B 2015-25 | -5.5%, t -2.91 | -5.514%, t -2.912 |
| Version B first run, as a history | -0.87%, t -0.46; -5.10%, t -2.68; +0.21% | Matches my earlier output |
| Comverse names, 2006 list | 221 Middle, 331 Benchmark | Same; it is in Middle |
| Comverse effect, Middle | -0.16 bp a year | -0.162 |
| Comverse effect, Benchmark | -0.11 bp a year | -0.109 |
| Comverse effect, High and Low | None | 0.0 |
| Effective tests | About 4 to 5 | Nyholt 4.69, Li-Ji 4.0 |
| 2015-25 at \|t\| of 2 | 8 of 9 | 8 of 9 |

### Earlier items

| Item | Landed | Where |
|---|---|---|
| M1 time pattern | Yes | Line 137 |
| M2 figures | Yes, all | Lines 9, 70, 71, 80, 188 |
| M3 Version B | Yes: fixed, rerun, disclosed | `05_align.py`; line 139 |
| M4 range | Yes | Line 82 |
| L1 lag 90 | Yes | Line 141 |
| L2 screen limits | Yes | Line 144 |
| L3 cap-weighted | Yes | Line 140 |
| L4 ranges | Yes | Line 9 |
| L5 terms | Yes | Lines 23-27 |
| L6 book equity | Yes | Line 138 |
| L7 timing | Yes, disclosed | Lines 96, 198 |
| L8 status | Yes | Line 236 |

**The Version B fix is correct.** My separate calculation with exact fractions gives the same 2,530 rows, each date holding 33.3%-33.5% of ranked names, with no non-positive book or non-USD rows. All 10 series again match my own engine. Eight-signal, buffer and screen memberships still match.

### First-run remnants

`+0.21%`, `-0.87%`, `-0.46`, `-5.10%` and `-2.68` appear only in line 139, as stated history. The other `-0.87` values (lines 126, 137) are cap-weighted's own t. No sentence says High beat its cheap-third benchmark. `robustness_report.md` also shows the corrected row.

### Baseline

35 of 41 baseline files are unchanged, including all earlier raw data and every headline table and chart.

| Changed file | Finding |
|---|---|
| `formation.parquet` | **Only the 7 intended rows.** Restoring the old float cutoff to the new file and saving it reproduces the baseline hash exactly (2EAE1EB7EA2ACD), so `value_tercile` and `in_version_b` are the only differences |
| `05_align.py` | The Version B fix |
| `07_evaluate.py` | Report text. Tables stay byte-identical |
| `checkpoint3_results.md` | Report text from reruns. The headline regression row is the same |
| `config.py` | Per the coordinator, heading wording. I hold only hashes, so I can't show the diff; the heading reads as described, and headline outputs are byte-identical |
| `CLAUDE.md` | Per the coordinator, section 8c timing wording, which now reads as described |

### Opening paragraph

**Nothing in it is stronger than the evidence, and no change is needed.** It answers both parts of the question, gives the ranges, marks the first decade as not significant, and limits the claim to large companies.

### Remaining notes, optional

- **N1. "High matched" (line 138).** True for the average monthly gap (-0.0017% a year), with a wide range of -2.65% to +2.65%. But High compounds at 9.96% against 10.35%, 0.40% a year behind, and its Sharpe is lower (0.50 vs 0.55). A clause would avoid this reading as a tie on all measures: "matched ... on average return (-0.00% a year), though it compounded more slowly (9.96% vs 10.35%)."
- **N2. Line 1 still says "draft write-up",** and line 141 has two colons in one sentence. Cosmetic.

### Not verified

Line 198 says first variant results "reached no one but their authors", and that the independent builder recommended the Comverse rule before results were compared. I can't confirm either from files, so they rest on the coordinator's account. I recorded the baseline after the robustness definitions began to be added, so its `config.py` hash is not a pre-Phase 7 version of those definitions.
