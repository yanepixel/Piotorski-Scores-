# F-score cross-check: independent build vs `data/clean/fscores.parquet`

**Result:** the two builds match on every company-year. All 18,265 company-years for FY2004-FY2024 are in both builds, and 13,993 are scored in both. There are 0 differences to explain, so neither version is closer to the brief than the other.

**File checked:** SHA-256 `2271B613917F446A3B6ABCFDAC3EA26438236B9EE2E28DCE669E53568EFC2B57`, the same before and after the comparison.

**Terms:** a company-year is one company's fiscal year. A stub is a short or irregular fiscal period, usually from changing the year-end month. PERMCO is CRSP's company ID and GVKEY is Compustat's. ROA is return on assets.

## 1. Comparison

| Item compared | Differences |
|---|---|
| Company-years present in only one build | 0 |
| Fiscal year-end date | 0 |
| Availability date and its source (filing or fallback) | 0 |
| Each of the nine signals, value and whether computable | 0 |
| F_SCORE, value and whether computable | 0 |
| 12 underlying ratios and changes, compared up to rounding | 0 |
| Stub flag | 0 |

Score distribution in both builds, scores 0 to 9: 3, 37, 141, 436, 1,210, 2,707, 3,657, 3,275, 2,049, 478. The mean is 6.11. The shape is bell-like with no spike at 0, but it centres nearer 6 than the brief's "around 5".

## 2. Hand-check sample

I recomputed the four rows of `output/tables/handcheck_sample.csv` from the raw Compustat, filing and sector files, with each formula written out from the brief. This used a script, not a separate manual calculation. All 220 values compared match: raw inputs, ratios, signals, scores, dates and sectors.

| Company | Fiscal year | F_SCORE | Signals failed |
|---|---|---|---|
| Exxon Mobil (listed as EXXONMOBIL HOLDINGS CORP) | 2023 | 6 | ΔROA, ΔMARGIN, ΔTURN |
| Microsoft | 2023 | 5 | ΔROA, ΔLIQUID, ΔMARGIN, ΔTURN |
| Walmart | 2023 | 8 | ΔLEVER |
| Intuitive Surgical | 2018 | 8 | ΔMARGIN |

This confirms the sample is calculated correctly from Compustat. It does not replace the Checkpoint 2 comparison against the actual 10-Ks.

## 3. First run on record

My first run used my own reading before the locked values were known, and it scored 14,096 company-years. Applying the locked config values removed 103, added none, and changed no score value:

- **54: share test only.** `MIN_CSHO_FOR_SHARE_TEST` removes very small placeholder share counts, mostly years when a company was private (Univision, First Data, SS&C).
- **49: stub rules.** These come from the 350-380 day range, which now also flags 11- and 13-month gaps such as Best Buy FY2012 and MSCI FY2011, and from excluding comparisons on both sides of a flagged year.

First-run files are kept as `verify_scores_run1.py`, `fscores_independent_run1.parquet` and `fscores_independent_run1_log.txt`.

## 4. How the ambiguities came out

| Ambiguity | Treatment in both builds | Effect on scored company-years |
|---|---|---|
| Exactly one fiscal year gap | Fiscal-year numbers never skip in the raw data, even across a 2- or 18-month gap, so the 350-380 day test does the real work | Without the stub test, 97 more would be scored |
| Stub detection | Days between year-ends. This cannot separate a short stub from a normal year after an unreported transition | Widening to 338-395 days changes nothing, which confirms the config comment |
| `STUB_EXCLUSION` both sides | No comparison into or out of a flagged year | Excluding only into the flagged year would score 36 more |
| ΔROA needing at_{t-2} | Required | 226 first rows and 289 rows with a non-comparable prior year are dropped |
| Zero debt when lever lags are null | Passes in my build, and the two builds agree on every row | 58 rows rely on it, but none ends up fully scored, so no effect |
| sale = 0 in margin | Uncomputable at sale <= 0 | 41 are dropped on margin alone, a count that includes null cogs |
| csho x ajex with ajex missing | Uncomputable | No effect: raw `ajex` has no nulls |

No alternative reading changed the value of any score. They only change which company-years are scored.

## 5. Points for the user at Checkpoint 2

The builds agree on all of these, so agreement does not settle them.

1. **REITs mostly drop out at scoring.** REITs usually have no current assets or liabilities in Compustat, so F_DLIQUID cannot be computed. As a rough guide, setting each fiscal year against the next May's list, 10.5% of included sector 40 names (26 of 247) and 23.4% of sector 60 names (64 of 274) are scored, against 91-98% in other sectors. The decision to keep REITs in therefore affects the universe far more than the portfolios.
2. **Merger years are compared across different-sized companies.** The section 9 check finds 20 GVKEYs with two PERMCOs in the universe, matching the audit's count, and 14 of them have a scored year in the gap between the two PERMCOs that feeds an included name on that rough guide. Share-count tests behave sensibly: most of these show issuance and fail. The ratios are less clean because ROA and turnover divide this year's flows by last year's pre-deal assets. DuPont FY2017 is an example, with assets sharply higher. This is true of any large merger, not only these names. Neither build adjusts for it and the brief does not ask for it, so I recommend leaving it as is and disclosing it.
3. **The share placeholder floor of 1 million misses values just above it.** CDW's prior-year csho sits just above the floor in FY2013, which counts as a very large increase, and Neiman Marcus FY2006 is similar. CDW's IPO was real issuance, but the ratio is not meaningful. On the rough guide above, neither score feeds an included name.
4. **Restaurant Brands FY2014 passes the share test** with csho down sharply in the Tim Hortons deal, probably because exchangeable partnership units are not counted. I have not confirmed this against the 10-K. On the rough guide, the score does not feed an included name.
5. **Ovintiv FY2004 mixes currencies.** FY2002 is in CAD and FY2003 onward in USD, so its prior-year ROA and leverage combine the two. It is not in the 2005 or 2006 lists, so nothing is affected. Tim Hortons is CAD on every row with no switch, so its ratios are consistent.
6. **Outliers.** 55 scored company-years carry Agent 1's review flag, mostly IPOs and early-stage biotech with large swings in revenue. They are real values as far as I can tell, and I did not check them individually.

## 6. Limits

- **Independence:** I did not read `03_clean.py` or `04_scores.py`. The match is on locked config values I applied before comparing, and those values were written with sight of the data. So the match shows consistent implementation, and it does not show that the values are the right choice.
- **Fiscal years outside FY2004-FY2024:** Agent 1's file holds only this range, so my FY2002, FY2003 and FY2025 rows were not compared.
- **Company names** come from Compustat's current name, so older years can read oddly (DuPont for the former Dow, Viatris for Mylan). Keep this in mind when finding 10-Ks.
- **Rough-guide figures** use the next May's list and are not the Phase 4 alignment.

## 7. Files

`verify_scores.py`, `compare_scores.py`, `fscores_independent.parquet`, `fscores_independent_log.txt` and `scores_compare_raw.txt`. No Agent 1 file, `CLAUDE.md`, `config.py` or `data/` file was changed.
