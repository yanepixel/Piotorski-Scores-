# Universe, scoring and data limits

These disclosures were required by the project brief and were first written for the earliest specification. The counts below were computed on that specification's lists and scores (fundamentals-based availability with a 120-day fallback, `ni`, share-count issuance test). The final pipeline keeps the same universe and exclusion rules, but scored counts, merger-year row counts and fallback statistics can differ slightly under the final scoring (no fallback, `ib`, literal issuance rule, 3-day filing buffer), so read them as describing the universe and its known quirks, not as exact current counts. The restatement bullet is updated: for FY2015-24 a sample against SEC as-filed data is in `output/results/sec_vintage_check.md`. The full text of the first write-up is in git (tag `archive-v1-v2-v3-pre-consolidation`).

**Low bucket:** the final pipeline uses Low = scores 0-4 (widened from 0-2 on name counts before any returns; Piotroski's own weak group is 0-1, with 0-2 as a footnote), High = 8-9, Middle = 5-7. The 2025 portfolio is partial (7 of 12 months, to December 2025).

**The universe is a proxy.**

- It is not the official S&P 500, because S&P membership history was not available. The 2025 list holds 418 of the 500 current S&P members, an overlap of 83.6%. That membership is as of October 2026, not May 2025. Of the 82 missing, 47 rank below 500, 29 are incorporated outside the US (such as Linde, Accenture and Medtronic), 5 have no valid link, and 1 is Cboe, whose listing is excluded by rule.
- Partnerships coded as units, such as Enterprise Products, are excluded.
- The check on 375-425 names per date was set after the counts were known, before any returns, and is a sanity check only. Actual range: 378-417.
- 500th-company market cap: the 2021 move of +63.6% is flagged and looks market-wide. The May date shows no 2020 dip (+0.8%), though the same cutoff fell in March 2020.

**Who is in and out.**

- Equity REITs stay in on all dates, including while GICS classed them in Financials. Mortgage REITs (lenders) are excluded on all dates, by dated GICS sub-industry plus one named exception, iStar 2005, which carries a generic code. That exception is a judgment call. 19 company-dates are affected.
- Visa, Mastercard and PayPal leave the universe when GICS moved them to Financials in March 2023.
- CBRE, which is not a REIT, is excluded through 2016 and included from 2017 after the Real Estate sector change.
- If the held share class has no valid link, the GVKEY comes from the same PERMCO when it has exactly one, and returns still come from the held class. This was used 34 times across 8 companies, including Alphabet 2014-2022.
- Eaton 2005-2012 and Ceridian 2020 drop out under the link filter. Dell 2017-18 and Liberty Media LSXMK 2016-17 have no GVKEY and are excluded.
- Yahoo 2005-2017 has no sector on the date and is excluded.
- Securities that stopped trading before the formation date are removed before ranking.

**The test effectively excludes some companies.** A company-year with any uncomputable signal is dropped. That effectively excludes traditional REITs, most homebuilders and finance-arm firms, which have no current assets or liabilities in Compustat. Only 26 of 247 kept REIT rows in Financials and 64 of 274 Real Estate rows have a score, against 91%-97% in other sectors. The eight-signal variant shows the effect of including them.

**Low is broader than Piotroski's weak group.** `LOW_SCORES` was changed from 0-2 to 0-4 on name counts only, before any returns: scores 0-2 had a median of 2 names a date and were empty in 2006, 2007 and 2011. Middle is therefore 5-7.

**Data limits.**

- Restatements: Fundamentals come from the current Compustat database, not a record of what was reported at the time, while availability dates use original 10-K filing dates. In a test on a sample of 1,480 companies for 2005-2015, 98.5% of F-scores matched those computable at the time and 0.2% changed bucket. Look-ahead from restated figures for FY2015-24 is measured only on a sample against SEC as-filed data (`output/results/sec_vintage_check.md`). Only 55 of those companies are in this project; for them, 97.3% matched and 0.45% changed bucket. The test ends with fiscal 2014 and uses today's share adjustment.
- Returns end in December 2025, so the 2025 portfolio is partial, and the last subperiod ends then.
- The thin May 2005 list: 25 companies with January-May year-ends have no score that year, because the data pull is not extended. 318 of 384 included names are scored on that date.
- Two companies report in Canadian dollars (11 rows). They are not converted. Ratios are unaffected, and their 3 list rows (Tim Hortons) are excluded from version B only.

**Timing and accounting choices.**

- 10-K filings over 120 days late: 108. Over a year late: 13, such as Maxim FY2006 and Fannie Mae FY2004. They are real dates and are used.
- 13 list rows use an older fiscal year because the newest available year has no score (such as Best Buy, Mastercard and Salesforce). 15 list rows were filed on the formation date itself and may not have been known at that day's close.
- Same-day filings are resolved to the later fiscal year (Maxim, United Rentals). Availability order inverts for H&R Block FY2021 and Super Micro FY2017, and no list row is affected.
- Fiscal-year changes: 49 stub years are flagged, and no year-over-year comparison runs into or out of them. Share counts under 1 million are treated as placeholders, so the share test is not computed. Margin is not computed when sales are zero or negative.
- Year-over-year moves above 10x are flagged, never dropped: assets 15, sales 42, adjusted shares 64.

**Merger and separation years are kept.** 270 list rows have 2x-10x moves in assets or sales, including real company split-ups, and these distort year-over-year tests. 20 GVKEYs span two PERMCOs over time. Comparisons that look invalid and reach a list: DuPont FY2017-18, Match FY2020-21, Starz FY2011, Dell FY2018 and Kraft Heinz FY2016. Splits that keep the same PERMCO, such as DuPont FY2019, are not caught by this test. The list of those joins is kept in the private project.

**Portfolio mechanics.**

- 4 included names delist on the formation date (CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017) and have no later returns. Their weight is spread pro rata in the first holding month, and they are charged as buys. Waste Connections continued under PERMNO 92949; in a later check, following it moves the Spread alpha from -2.04% to -2.06%, with High unchanged.
- 179 mid-period exits (High 32, Middle 125, Low 22). Reinvesting their proceeds is not charged.
- RSP has two rows for April 2018 and they are chained into one return.
- The spread carries no shorting costs, and its -65.9% drawdown compounds a long-short series with no financing, so it is a rough diagnostic only.
- The published net Spread column subtracts Low's net return from High's, which credits Low's trading costs to the spread by about 0.35 points a year. It stays as published, at -0.57% a year (alpha -2.04%, t -0.72). With both legs charged, the Spread is -0.92% a year (alpha -2.39%, t -0.85).
- t-stats use no small-sample correction, and significance is a fixed |t| of 2.

**Robustness timing.** The robustness definitions and null-return rules were set after the headline existed. The independent builder's first variant run and the main build's crashed run existed before two later rules were settled: the Comverse hold-flat rule and the instruction to use the quantile boundary for version B. By the coordinator's record, those results were not reported to the coordinator or the other builder, but each author had access to its own, so these rules were not set blind. Also by the coordinator's record, the Comverse rule was recommended by the independent builder, whose first run already held Comverse flat, before the two builds' results were compared. No file can show the order of these events: the repository's history begins after these events, and file dates show only the last save. The rule's effect is -0.16 basis points a year on Middle and -0.11 on the Benchmark, with High and Low unaffected. Bucket placement for the eight-signal version could not be set before any returns existed, as first planned.

