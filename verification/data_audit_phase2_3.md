# Phase 2-3 audit: inputs, look-ahead, and review of `03_clean.py` and `04_scores.py`

No return data was used. From `crsp_msf_v2` I read only issuer type and name. No code or data of Agent 1's was edited, and no later phase was started.

Terms: **look-ahead** means using something not yet known on the date. **Restatement** means a company later changing figures it already reported. **Point-in-time** means a value as it could be seen on that date. **Formation date** is the last trading day of May, when each portfolio is built. **Unclassified balance sheet** means a balance sheet with no current/non-current split.

Files tested (SHA-256, first 14 characters), unchanged at the end of testing: `03_clean.py` 6A19F87E5C91FE, `04_scores.py` 7EFB9BB541E13F, `config.py` AB81468492BBAA, `fscores.parquet` 2271B613917F44, `universe.parquet` DE7F2A8BBA9FF4.

Evidence: `verification/audit_09` to `audit_16` scripts and their `_output.txt` files; `audit_12_edgar_sample.csv`.

## Result

**The code is correct and I found no look-ahead bug. My separate recomputation from raw data matches every signal and score on all 18,265 company-years. But two High problems come from the data and rules, not the code, and both need a decision from the user before any returns are seen.**

| ID | Severity | Finding | Who acts |
|---|---|---|---|
| H1 | **High** | The missing-signal rule removes 84.4% of included REIT rows, plus homebuilders and firms with finance arms | User decision |
| H2 | **High** | The Low bucket is under 10 names on 20 of 21 dates, and empty on 3 | User decision before Phase 5 |
| M1 | Medium | 25 companies with fiscal years ending January-May have no score in May 2005 | User decision |
| M2 | Medium | 270 list rows (3.6%) have a 2x-10x asset or sales move that the 10x flag misses, including real company split-ups | Disclose; user may add a test |
| M3 | Medium | Restatements are a real data limit, with a small measured effect | Disclose |
| L1-L8 | Low | See the Low findings section | Noted |

## 1. Filing dates are reliable

| Test | Result |
|---|---|
| 10-K dates on or before year-end | 0 of 20,285 |
| Random sample vs SEC EDGAR | 193 matched, 193 exact |
| Late filers (over 120 days) vs EDGAR | 35 matched, 35 exact |
| Early filers (30 days or less) vs EDGAR | 203 matched, 201 exact |
| Compustat date equals an amendment date | 0 |
| Duplicate 10-K dates for one fiscal period | 0 |

- **Two dates are too early:** Ford FY2005 and International Game Technology FY2011, each earlier than the EDGAR date. Neither crosses a May date, so neither changes a list.
- **Unmatched filings:** 7 of 200 in the random sample and 22 of 57 in the late sample had no EDGAR 10-K with that period. Many late ones are newly separated or newly listed companies (AbbVie, Veralto, Kraft Foods Group, Cable One), where the Compustat "10K" date looks like a registration filing. I did not open those filings.
- **Pattern of very late filings (66 over 180 days):** mainly accounting and option-backdating restatements (Maxim, Comverse, Fannie Mae, Super Micro, United Rentals, Flowserve, McAfee) and companies coming from a spin-off or registration. They are real dates, and using them is correct and conservative.
- **Fallback dates:** 2.91% of FY2004-2024 rows with assets use year-end + 120 days, but only 6 of 7,570 chosen list rows do. Actual filing lag exceeds 120 days on 0.5% of filed rows, so this risk is small.

## 2. Restatements: real limit, small measured effect (M3)

**The premise needs narrowing.** `funda` in `STD` format is not simply "as restated":

- Current `funda` nearly equals the snapshot's restated table (net income differs on 0.08% of rows).
- But for company-years that Audit Analytics records as restated, `funda` net income matched the **original** figure in 488 rows, the restated figure in 150, both in 88 and neither in 279. So most formal restatements of an old year do not overwrite that year's value here. The 279 unexplained rows are a limit on this test.
- 795 distinct company-years (5.3% of project FY2004-2024 rows) have a net income change recorded, with a median change of 3.1%. Net income changed sign in 26 of 1,005 rows.

**The direct look-ahead test.** Using `compsamp_snapshot.wrds_csa_pit`, I rebuilt signals from what was visible on each 31 May in 2005-2015 and compared them with today's `funda`.

| Measure | All sample | Project companies |
|---|---|---|
| Company-dates with complete scores | 3,502 | 446 (55 companies) |
| Score unchanged | 98.5% | 97.3% |
| Bucket changed | 0.2% | 0.45% |
| Today's High that were High then | 99.6% | 98.9% |
| Largest signal flip | F_DMARGIN 1.53% | F_DMARGIN 2.14% |
| F_ROA flip | 0.04% | 0.00% |

The signal most exposed is margin, because cost of goods sold gets reclassified. A cruder comparison against the first number ever recorded gives 91% unchanged and 1.7% bucket changes, but that likely includes preliminary figures replaced by the 10-K itself, so it overstates the problem.

**Limits:**
- The sample holds 1,480 companies, ending with FY2014, and only 55 project companies. It uses fiscal years ending June-December, and today's `ajex` because the snapshot has none.
- It cannot show whether the few changed names lean toward later winners or losers, since no returns were used.

**Source availability:** the full point-in-time library (`comp_snapshot`) was not available. Only the sample library and Audit Analytics are readable, so a full as-first-reported rebuild is not possible on this account.

**Suggested disclosure:** "Fundamentals come from the current Compustat database, not a record of what was reported at the time, while availability dates use original 10-K filing dates. In a test on a sample of 1,480 companies for 2005-2015, 98.5% of F-scores matched those computable at the time and 0.2% changed bucket. Any remaining look-ahead from restated figures could not be measured for the whole sample or for later years."

## 3. May availability is correct

- No chosen score was filed after its formation date, has a year-end after it, or falls outside the score years (0 of 7,570 rows each).
- **FY filed after May:** 15-41 prior-year rows per date are available only after that May, and none is used.
- **May year-ends:** a few FY rows end on 31 May after a 28-30 May formation date. They are excluded.
- **`LAST_SCORE_FY` = 2024 works:** the 758 FY2025 rows are never available by 2025-05-30, and 15 FY2024 rows filed later are correctly unusable.
- `FIRST_SCORE_FY` is the problem; see M1.

## 4. H1: the missing-signal rule removes most REITs

| Group | Included rows | Scored | Scored % |
|---|---|---|---|
| Equity REITs | 512 | 80 | 15.6% |
| Sector 25 | 1,455 | 1,324 | 91.0% |
| Sector 20 | 1,272 | 1,163 | 91.4% |
| Sector 45 | 1,588 | 1,523 | 95.9% |
| Other sectors | 3,587 | 3,480 | 96-100% |

- **Cause:** `act` and `lct` are blank on 84% of chosen REIT rows, so F_DLIQUID can't be computed. 3,124 company-years are dropped for this signal alone.
- **By date:** REITs scored are 0-6 a date against 15-34 kept. The 80 are almost all towers, data centres, storage and timber (American Tower, Equinix, Weyerhaeuser, Plum Creek, SBA, Iron Mountain, Crown Castle, Rayonier). Ordinary apartment, office, retail and health-care REITs are almost entirely gone.
- **Other names lost for the same reason:** Deere and Paccar (21 dates each), Textron (20), GE (17), D.R. Horton and Lennar (17), Ford (13), NVR (11), Western Union (11), Pulte (8).
- **The code follows the brief.** Two approved rules conflict: "equity REITs stay in" and "any uncomputable signal drops the company-year".

**Options for the user, before returns are seen:**
1. Keep the rule and disclose that scored portfolios effectively exclude ordinary REITs, homebuilders and finance-arm firms.
2. Score those firms on eight signals. This changes the meaning of the 0-9 scale.
3. Count F_DLIQUID as a fixed pass or fail for them. This pushes them toward one bucket.

I make no recommendation based on results. `scores_checks.md` shows this only indirectly, through sector 40 (10.5%) and sector 60 (23.4%). It should show REITs as their own row.

## 5. H2: the Low bucket is nearly empty

Using `LOW_SCORES` = 0, 1, 2 on included lists:

- **Low:** 52 rows in 21 years, median 2 names a date. It is below `MIN_BUCKET_NAMES` (10) on 20 of 21 dates and empty in 2006, 2007 and 2011. Only 2021 reaches 10, with 12 names.
- **High:** 43-127 names a date, median 73.
- **Cause:** this follows directly from large-company pass rates (section 7).

**Consequence:** the Low portfolio and the High-minus-Low spread would rest on one or two stocks in most years, and cannot run at all in three. The bucket check would only flag this, so the spread could still be calculated and reported. For comparison, a score of 3 or below gives a median of 7-8 names, and 4 or below gives about 31, but the user should decide whether to change it, before returns exist. Any change is a rule change, and must not be chosen by looking at spreads. The High-versus-benchmark test is not affected.

## 6. Splits and `ajex`: correct

`csho x ajex` is the right direction. On the 597 forward splits in the file:

| Comparison across a split | Median change |
|---|---|
| Raw `csho` | +100.9% |
| `csho x ajex` | +0.5% |
| `csho / ajex` (wrong direction) | +301.7% |

- **Named checks:** Walmart 2024, Apple 2005/2014/2020, Nvidia 2006/2007/2021/2024, Tesla 2020/2022, Netflix 2004/2015/2025, Amazon 2022, Alphabet 2022, Nike 2006/2012/2015, Starbucks 2006/2015, Visa 2015, Mastercard 2014, Chipotle 2024, Broadcom 2006/2024, Microsoft 2003, CoStar 2021, Lam 2025. All show only small changes after adjusting, except Broadcom 2024, a larger rise in the year of its VMware purchase.
- **All splits:** 575 of 597 are within 25%. The other 22 years mostly look like large deals (Bank of America 2004, Reynolds 2015, Hologic 2008) rather than timing errors. None shows a split missing from `csho`.
- **Walmart FY2023:** the adjustment works across the split, so the comparison is consistent.

**Hand-check warning:** a 10-K filed after a split can show the post-split count. Walmart's split came just after that year-end, so its 10-K may show the later count. If so, compare the 10-K to `adj_shares`, not `csho`. I did not open that filing.

## 7. Are the pass rates and the peak at 6 plausible? Yes

**Fundamentals check on F_ROA and F_CFO, FY2004-2024:**

| Group | Net income > 0 | Operating cash flow > 0 | Cash flow > net income |
|---|---|---|---|
| All Compustat industrial firms | 58.5% | 68.0% | 80.8% |
| Assets $1bn or more | 81.5% | 92.1% | 84.9% |
| Top 500 by assets | 89.6% | 92.7% | |
| **This project (scored)** | **84.5%** | **94.8%** | **89.4%** |

**The mean is arithmetic.** The nine pass rates sum to exactly the mean of 6.115. The level signals (ROA, cash flow, accruals, no share issuance) contribute about 3.5, because large companies usually pass. The five change signals contribute about 2.6, near coin-flips at 48-58%. The brief's "around 5" fits a broad stock sample better than a large-cap one, since small loss-making firms pull the level signals down.

**The peak at 6 is a real feature.** Treating signals as independent predicts a peak at 6: 29.7% predicted against 26.1% actual. The actual spread is a little wider (standard deviation 1.47 vs 1.29), as expected, because good signals cluster: F_ROA with F_CFO correlates 0.42, F_DROA with F_DTURN 0.35. There is no spike at 0, and no gap.

**Year patterns fit events:** F_ROA is low in FY2008 (79.9%), FY2015-16 (about 80%, oil and commodities) and FY2020 (70.0%). F_DTURN falls to 29% in FY2009 and 27% in FY2020.

## 8. M2: large moves below the 10x flag

Among 7,570 list rows with a score:

- **270 rows (3.6%), 213 companies** have an asset or sales ratio of 2x-10x up or down: 229 up, 42 down. Two rows are both.
- **Another 243 rows** have such a move only in the prior year, which still feeds change signals.
- **264 of the 270** are not in `permco_joins_review.csv`, so the join review doesn't address them.
- **Effect on buckets:** these rows average 5.22 against 6.28 overall. About 15 of the 52 Low rows are in this group, against about 14 of 1,552 High rows. So they matter most for the already thin Low bucket.

**Shrinkers that look like separations of a business (my reading):** HP Inc FY2016, DuPont FY2019, eBay FY2015, Altria FY2008, Motorola Solutions FY2011, Beam FY2011, Marathon Oil FY2011, ConocoPhillips FY2012, Howmet FY2020, Yum FY2016, Match FY2020. Others are operating shocks, not breaks: airlines, casinos and hotels FY2020, and oil FY2015.

**Growers:** mostly acquisitions (Hologic FY2008, Freeport FY2007, Fiserv FY2019, Sears FY2005, Bristol-Myers FY2019) and IPO cash (Snowflake, Datadog, DoorDash).

The full list by name is in `audit_15_output.txt`. These are real events and the data isn't wrong, but a separation or large merger compares two different businesses. Disclose this. If the user wants a test, the honest form is a labelled robustness run excluding these rows, fixed before returns are seen.

## 9. Placeholder share counts near the floor

**Across all rows:** 38 rows have a smaller share count just above the floor, 16 of them scored. They include CDW and Neiman Marcus, neither of which reaches a list with that score, and Berkshire and Ally, which are not scored.

**On included lists (L1):**

| Company | FY | List | Share count |
|---|---|---|---|
| Las Vegas Sands | 2004 | 2005 | Large rise after its IPO |
| Molycorp | 2010 | 2011 | Large rise after its IPO |
| QEP Resources | 2010 | 2011 | Large rise after its spin-off |

Each fails F_EQ_OFFER. Sands and Molycorp were real IPOs, so the fail is defensible. QEP was a spin-off, so its fail is an artefact, and the floor doesn't catch its earlier count. That is 3 of 7,570 rows.

**More broadly:** 26 list rows have very large moves in adjusted shares, mainly first years after an IPO (Coupang, Lyft, Snowflake, Uber), where pre-IPO preferred stock converted. They count as failing F_EQ_OFFER, which is arguably correct for an IPO, but this should be disclosed.

**Floor blocks:** 120 rows are blocked by the floor. Kraft Heinz FY2015, Invitation Homes FY2017, Oak Street FY2020 and Activision FY2008 lose their newest score this way.

## 10. M1: May 2005 loses off-calendar companies

May 2005 has 66 names with no score, against 30-44 on other dates. Of these, 25 are companies whose FY2004 ends in early 2005 and isn't filed by May, including Nike, Oracle, Medtronic, FedEx, General Mills, Symantec, Heinz and Paychex. Their last filed year is FY2003, which is before `FIRST_SCORE_FY`.

Scoring FY2003 needs FY2001 for ΔROA, and the pull starts at FY2002. The code follows the config. Options: extend the pull to FY2001 and set `FIRST_SCORE_FY` to 2003, as a labelled rule change before results, or disclose that the first list under-represents these companies. Raw files would need a new pull, not an edit.

## 11. Code review

**`03_clean.py`: no errors found.** Duplicates fail the run, amendments are excluded, and the earliest valid filing date is used. Fallback uses the config lag, and flags never drop rows. Stub detection found 49 years, all with a fiscal-year-end change.

**`04_scores.py`: no errors in signals.**
- Every definition matches section 5 of the brief. Lags are null unless years are consecutive, and `at_lag2` requires both year pairs to be valid.
- Infinities become null, and the zero-debt rule follows the config.
- The checks exist and can fail for duplicates, scores outside 0-9, sum mismatches, scored stubs, floor breaches and availability on or before year-end.
- No return data is read.

**Rules still needing approval:** `STUB_MIN_DAYS`, `STUB_MAX_DAYS`, `STUB_EXCLUSION`, `OUTLIER_YOY_RATIO`, `MIN_SALE_FOR_MARGIN` and `MIN_CSHO_FOR_SHARE_TEST` are new rules. They are in the config and marked for user review at Checkpoint 2, so that review must actually happen.

## Low findings

- **L1.** Three placeholder-driven share rows reach lists (section 9).
- **L2.** Phase 4 must break ties on `datadate`. Maxim (FY2006-2008) and United Rentals (FY2004-2005) share availability dates, and `align_for_counts` sorts by availability date alone, so the row chosen isn't guaranteed. No list row is affected today.
- **L3.** Availability order inverts for H&R Block FY2021 and Super Micro FY2017, where an older year becomes available after a newer one. Super Micro's newer year uses a fallback date. No list row picks an older year this way today.
- **L4.** 13 list rows use an older fiscal year because the newest available year has no score (Best Buy, Mastercard, Salesforce and others, ages 12-17 months). This fits "most recent F_SCORE", but Phase 4 should log it.
- **L5.** 15 list rows were filed on the formation date itself. `filedatetime` has times, many in the evening, so the number may not have been known at that day's close. I couldn't confirm the time zone. Consider requiring filing before the date, or disclose it. That is 0.2% of rows.
- **L6.** F_DLEVER passes only 34.4% in FY2019, the lowest year by far. Median long-term debt grew 11.2% and rose for 73.7% of firms, against about 0-3% in most years. This could be the lease accounting change (ASC 842) in `dltt`, or real borrowing. I did not establish the cause, so check before describing this as economic.
- **L7.** `04_scores.py` fails if there aren't exactly 20 PERMCO-spanning gvkeys, so any universe change will trip it. That is intended as a guard, but the number belongs in the config.
- **L8.** Two CAD reporters are not converted. Ratios are unaffected, but book-to-market will need the decision already recorded in section 9 of the brief.

The new sources for this audit are SEC EDGAR, for which my script sent only public company CIK numbers, and the WRDS sample libraries.
