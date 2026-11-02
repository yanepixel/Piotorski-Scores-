# Re-audit at commit 259a4f7

Agent 3, report only. Nothing is committed. No WRDS query was made: every test here uses files already in the project. I did not read `verification/reaudit_agent1.md`, so this stays independent of it. `output/writeup.md` is FF9C57FF69E129, read in full.

**Terms.**
- **Alpha:** return left after the six factors, in percent a year.
- **t:** a number divided by its standard error, with beyond about 2 treated as significant.
- **Reading:** how a rule was interpreted, as opposed to whether code applied it correctly.
- **Bucket:** the High, Middle or Low portfolio.

## Verdict

**No MUST FIX: I found no wrong number.** The answer paragraph stands, and no test here moves a full-period High alpha near significance.

There are six SHOULD FIX items, all short wording changes, and six OPTIONAL. The most important is that the write-up says "the nine Piotroski tests" without saying which readings differ from Piotroski, and the 2% share tolerance matters more than any scoring choice the write-up tests.

## SHOULD FIX

### S1. "The nine Piotroski tests" hides three readings (line 42)

No build could catch these, because all follow `CLAUDE.md`. The write-up never lists the tests, and config and CLAUDE.md differ from Piotroski (2000) as follows. I cite the paper from memory and did not check it here.

| Reading in this project | Piotroski | Measured effect, as run: High alpha -0.78% (t -0.71) |
|---|---|---|
| `F_EQ_OFFER`: split-adjusted shares up no more than 2% | Did not issue common equity | No tolerance: 770 of 7,571 rows change bucket, alpha -0.08% (t -0.08). 5% tolerance: 166 rows, alpha -1.24% (t -1.30) |
| `F_DLEVER`: no long-term debt in both years passes | Leverage fell | Not passing: 120 rows change bucket, alpha -1.09% (t -0.97). These passes are 10.1% of all passes on this test |
| ROA on `ni` | Income before extraordinary items (`ib`) | Not testable: `ib` is not in the raw data, and no pull was wanted |

For 2015-25, the same runs give alpha -3.18% (t -3.40), -3.71% (t -4.55) and -4.17% (t -4.23), so that pattern stays too. High minus Benchmark alpha ranges from -0.25% (t -0.30) to -1.42% (t -1.90). These tests came after the results were known, and they are sensitivity only. No rule should change because of them.

The swing of -0.08% to -1.24% from one reading of one test is as large as anything in the robustness table's full-period column, and it isn't in that table.

**Why it's needed for the large-cap question:** the answer depends on what "F-score" means here. A reader who knows the paper would assume the standard tests.

**Suggested text, after "the nine Piotroski tests":** "The rules are in `CLAUDE.md`. Three readings differ from Piotroski: net income rather than income before extraordinary items, a share rise of up to 2% still passes the no-issuance test, and a company with no long-term debt in both years passes the leverage test. In a later check, removing the 2% tolerance gave a High alpha of -0.08% (t -0.08), a 5% tolerance -1.24% (t -1.30), and failing the no-debt case -1.09% (t -0.97). None is significant. The net income reading was not tested."

### S2. The answer implies the second decade's gap was significant (line 9)

"High did better than the benchmark in the first decade, though not significantly, and worse in the second."

The qualifier attaches to one half only, but the gap to the benchmark wasn't significant in either:

| High minus Benchmark, Newey-West 12 lags | Excess a year (t) | Six-factor alpha (t) |
|---|---|---|
| 2005-15 | +1.02% (1.04) | +0.99% (0.80) |
| 2015-25 | -1.53% (-1.22) | -2.63% (-2.30) |

**Suggested text:** "High did better than the benchmark in the first decade and worse in the second, neither significantly on raw return." The factor-adjusted figures follow later in the write-up with their caution.

### S3. The restatement test quotes the sample, not this project's companies (line 174)

This is my wording from the Phase 2-3 audit, and it left out the more relevant column. The same table in `data_audit_phase2_3.md` gives:

| | All sample | Project companies (55) |
|---|---|---|
| Score unchanged | 98.5% | 97.3% |
| Bucket changed | 0.2% | 0.45% |

**Suggested addition:** "Only 55 of those companies are in this project; for them, 97.3% matched and 0.45% changed bucket. The test ends with fiscal 2014 and uses today's share adjustment." The size of the problem is still small, so the conclusion doesn't change.

### S4. The Benchmark excludes a weak group (lines 9, 15, 168)

The answer states correctly that the benchmark is the scored companies, and comparing like with like is right for testing the score. But "universe" in the question invites a wider reading. The unscored names, a median of 39 a date, earned much less:

| June 2005 to December 2025 | CAGR |
|---|---|
| Unscored names, gross | 6.24% (alpha -4.18%, t -2.01) |
| All included names, gross | 10.83% |
| All included names, net | 10.79% |
| High, net | 10.91% |
| Benchmark, scored names, net | 11.35% |

So High is ahead of all included names by 0.19% a year (t 0.22), with alpha -0.44% (t -0.45). That isn't significant either, so the answer holds. The sign of the raw gap does depend on the benchmark, though, and a reader can't see that. The filter uses only what was known on each date, so I see no look-ahead in it. About half of the unscored rows are REITs (432 of 843).

**Why it's needed:** it answers the obvious follow-up about how much the scored-only benchmark matters.

**Suggested addition to line 168:** "Those 843 unscored rows earned 6.24% a year gross. Against all included names (10.79% net), High's raw gap is +0.19% a year (t 0.22), and still not significant."

### S5. The charged monthly view isn't disclosed as added after the result was seen (line 298)

The config value is `sensitivity_reset: "monthly"`, and the charged version came after the locked run and after my audit suggested it. Line 298 presents it as a second view, and line 317's 1.38 of 1.80 points is measured against it. It is a fair measure, and it lowers rather than raises the monthly figure compared with the free one, but it was not pre-set.

**Suggested addition:** "The charged version was added after the locked result had been seen."

### S6. The timing paragraph attributes some claims, but not all (lines 96, 199)

- "By the coordinator's record" covers who saw results. The next sentence, that the independent builder recommended the Comverse rule with its first run already holding Comverse flat before results were compared, is stated as fact. I noted in Phase 7 that I can't confirm this from files.
- "On structural grounds" (lines 96, 199) is a statement of motive. The definitions look structural to me, but no file can show why they were chosen.
- The repository has one commit, so it can't show the order of events either. File dates only show the last save.

**Suggested text:** "By the coordinator's record, the Comverse rule was recommended ...", and "set after the headline existed, by the coordinator's account on structural grounds". The paragraph already says "not set blind", which is the essential point and is correct.

## OPTIONAL

| # | Line | Item |
|---|---|---|
| O1 | 192 | Waste Connections 2016 is listed among names that "delist". The company continued under PERMNO 92949. Following it: Low 2016-17 13.65% to 14.24%, Benchmark 18.71% to 18.79%, Spread alpha -2.04% to -2.06%, High unchanged. Could add "(the company continued; following it changes nothing material)". |
| O2 | 168 | The named exclusions leave out recent IPOs and spin-offs, which lack the two prior years the score needs. The drop table shows them only as counts. |
| O3 | 289 | "So it mostly reflects year-end cash timing" is my inference, not a test. "Likely" would be more accurate. |
| O4 | 51 | The turnover column excludes the first year, as `checkpoint3_results.md` says. The write-up doesn't. |
| O5 | 319 | The sentence gives shuffled-score numbers for the first t of -2.35 only. For the second: mean t -2.36, 65.8% past 2. |
| O6 | 267 | The write-up says -2.7 to -3.2 and `output/extension_2026/results.md` says -2.7 to -3.25. Both round the same range, and my report used both. |

## Tested from a different angle, no problem found

| Shared reading | Test | Result |
|---|---|---|
| Other formulas against the paper | Read `04_scores.py` line by line | CFO, change in ROA, accrual, leverage on average assets, liquidity, gross margin and turnover on opening assets all agree |
| Split adjustment | Looked for year-on-year share ratios near split factors, before and after adjustment | Works: raw 323 rows, adjusted 76. Apple 2014, Nvidia and Tesla stay level. Two real misses found (below) |
| Availability dates | Filing lag on list rows | Minimum 20 days, median 54, 1% under 27. Nothing implausibly early. 193 rows arrive within 30 days of formation, 15 on the day (disclosed) |
| Unused newer years | Rows where a newer year was out but unused | 13, equal to the disclosed count |
| Buy-and-hold | A cohort's 12-month return against the mean of its stocks' compounded returns, 5 High cohorts with no exit | Gap 3e-16 |
| Month alignment | Benchmark against market with factors shifted | Correlation 0.978 unshifted, within 0.08 of zero at one and two months either way |
| Newey-West | Own formula against statsmodels | Same t to 6 decimals: Bartlett weights, 12 lags, no correction, as disclosed |
| Non-overlapping view | 20 complete years, High minus Benchmark | Mean -0.69% (t -0.69), same reading as the headline |
| Benchmark level against funds | All included names 10.83% gross, against RSP 9.85% and SPY 10.88% | About a third of the 1.54-point gross gap between scored names (11.39%) and RSP is the scored-only filter (S4). The rest includes RSP's fees and its financials and utilities, which I did not split. No sign of survivorship, though this test can't exclude it |
| Drop table | The figure 2,060 appears twice, which looked like a copy error | Real coincidence: share type 2,060 and sector exclusions 1,446 + 614 |
| REIT counts | 26 of 247 and 64 of 274 (line 168) against 80 of 512 (line 278) | Reconcile: Real Estate has 12 scored non-REIT rows, and 3 REIT rows sit in other sectors |
| Tables | All robustness and subperiod cells against the output files | All match |
| Internal consistency | `writeup.md`, `checkpoint3_results.md`, three `results.md`, `CLAUDE.md`, `config.py` | No contradiction beyond O6 |

**Two share events treated as issuance:** Alphabet FY2014 (Class C share dividend, score 5 not 6, 2015 list) and Telephone & Data FY2005 (share dividend, score 5 not 6, 2007 list). Both stay in Middle, so no return changes. They appear because `ajex` doesn't reflect those distributions, which is a data limit. I read 25 of the 42 rows of this kind on scored years, and the rest of those 25 look like real deals or IPOs. The other 17 were not read.

## Open items from earlier audits

| Item | Status |
|---|---|
| Waste Connections effect (`portfolios_compare.md`) | Closed: O1 |
| 1/N charge on formation-date delisters | Closed: disclosed at line 192, small |
| Version B old figures in the write-up (`robustness_compare.md`) | Closed: line 139 uses the corrected ones |
| Long/short monthly runs not compared month by month | Closed: my engine matched them |
| Stale "not rerun" lines in `results.md` files | Closed: since updated |
| Write-up change from C77BA3D9 to 2C9015 | Closed: read in full here, nothing wrong found |
| Who saw which result when (Phase 7) | **Stays open:** can't be settled from files (S6) |
| 55 scored outlier rows not individually checked (`scores_compare.md`) | Open, low: real values as far as checked |
| 279 unexplained restatement rows (Phase 2-3) | Open, low: a limit of that test, covered in substance by line 174 |
| Currency change within four quarters, profitability screen | Open, low: variant only, and only 2 companies report in CAD |
| 2026 months against CRSP | Open until CRSP covers them: disclosed at line 268 |

## Limits

- The alternative readings in S1 came after results were known, and I chose them because they are the plain alternatives to each rule. They are not a search, but they are not blind.
- `ib` against `ni`, and a direct `sstk`-based issuance test, are untested. `sstk` is positive in 79.9% of scored rows, so a literal "no issuance" test would fail most companies, which is presumably why a tolerance exists.
- I have not re-run Phase 1 to 3 from raw here. Earlier audits did.

The test scripts are not in this repository.

## Re-read after the fixes, 2026-11-01

`output/writeup.md` 67C097598C76B2, read in full and compared with commit 259a4f7. Report only. No project file changed.

**Result: every new figure is correct, and the answer still stands. Two items should change (R1, R2), three smaller ones are worth fixing (R3 to R5), and the sensitivities can't be rerun by a reader yet (R6).**

### Should change

**R1. Line 42 states the Piotroski differences as fact, without saying the paper wasn't checked.** "Three readings differ from Piotroski" came from my memory of the paper, and neither I nor Agent 1 checked its text. The write-up doesn't say so.

Suggested text: "Three readings differ from Piotroski's paper as recalled by the audit, not checked against its text: ..."

**R2. The clause on -2.63% (t -2.30) belongs in the answer, but not bare (lines 9 and 84).** Keep it: without it, "neither significantly" would understate the factor-adjusted result, and that is the comparison the question asks about. But t -2.30 now appears in the answer paragraph with no caution, and the caution at lines 80-82 is about a different series, High's alpha against the risk-free rate. I had not tested this t before, so I did now:

| High minus Benchmark alpha, June 2015 to December 2025 | Result |
|---|---|
| t at lags 0, 4, 8, 12, 18, 24 | -2.21, -2.39, -2.55, **-2.30**, -2.13, -2.01 |
| Simulated size, no true alpha, shuffled and 12-month-block residuals | Passes 2 in 8.4% and 9.8% of runs, not 5% |
| Rescaled t | -1.99, -1.95 |
| p | 0.044, 0.066 |

So the fair reading is about -2, borderline. Also, this gap is High's alpha minus a Benchmark alpha that doesn't change under shuffling, so its placebo share equals the alpha's: 1.5% of random selections and 11% if they keep High's sector mix. That follows from the arithmetic. The extended period's output shows the two shares identical, at 1.7% and 12.5%.

Suggested line 9 clause: "although the factor-adjusted gap in the second decade was -2.63% (t -2.30, about -2 after allowing for how often this test overstates; see Results)."

Suggested addition to line 84: "In simulations that t is about -2 (p 0.04 to 0.07), and the gap falls in the lowest 11% of random selections that keep High's sector mix."

### Smaller

**R3. Line 203, "the repository has a single commit", will go out of date when these fixes are committed.** Suggested text: "the repository's history begins after these events".

**R4. Line 243, "label, log and wording fixes", leaves out one small count correction.** The `04_scores.py` tie-break changed `score_distribution.csv` (score 8 list rows 1,255 to 1,256) and `coverage_by_sector_year.csv` (2009, sector 45, 65 to 66). These review tables now agree with `formation.parquet`, which has 1,256 at score 8, and no portfolio changes. All other shared columns in the six changed tables are identical, apart from an added label column. `portfolio_returns.csv` and the other return tables are unchanged at the commit. Suggested text: "label, log, wording and two review-table count fixes".

**R5. `README.md` line 72 is broader than the write-up on one point.** It says a rerun reproduced the same tables and charts, while line 243 adds that the clean-copy run came before the helpers moved into the numbered order. The README's run order (09, then 09a) is therefore not the order that was run. Agent 2's report has the helper before 09, or added afterwards. Suggested addition: "That run came before the helper scripts were renumbered." Everything else in the README agrees with the write-up or the code: the answer figures, the `--overwrite` rule in `02`, the stop in `11`, and Python 3.13.2.

### Tracing the sensitivities

**R6. A reader can find the figures but can't rerun them.**

- The write-up doesn't name the source. Line 243 says "that re-audit" and gives no file. It should cite `verification/reaudit_agent3.md`, as line 249 does for the other audits.
- The figures are in that report. The scripts are not in this repository.

### Checked, no problem

| Item | Result |
|---|---|
| S1 figures, line 42 | -0.08 (-0.08), -1.24 (-1.30), -1.09 (-0.97); 2015-25 -3.18 (-3.40), -3.71 (-4.55), -4.17 (-4.23): all match |
| S2, line 9 | +1.02 (1.04), -1.53 (-1.22), -2.63 (-2.30) match. "Neither significantly on raw return" is accurate |
| S3, line 178 | 55, 97.3%, 0.45%, fiscal 2014, today's share adjustment: match |
| S4, line 172 | 843, 6.24%, -4.18% (-2.01), 10.79%, +0.19% (0.22), -0.44% (-0.45): match. The heading is accurate, since -0.29% becomes +0.19% |
| S5, line 304 | Present and correct |
| S6, lines 98, 203 | Attribution now covers both claims. "Structural grounds" is gone from every project file outside the audit reports |
| Waste Connections, line 196 | PERMNO 92949, -2.04% to -2.06%, High unchanged: match |
| New disclosures against the rest | No contradiction. Lines 42 and 172 are labelled as later sensitivities, and line 98's "every variant run" still holds, since they aren't variants |
| Answer paragraph | Reads clearly. The new sentence is long but correct. Its first and last sentences are unchanged |
| Other changes | Unchanged text is as it was at 259a4f7, by the diff. Config additions set out approved cases and pull fields, with no changed value |

**Low, `CLAUDE.md` section 8c:** "before their own results were reported" is also the coordinator's record, not something files can show. The write-up attributes this correctly at line 203, so nothing a reader relies on depends on it.

**Optional items O2 to O6 were not taken up.** That is fine, as none affects a conclusion.
