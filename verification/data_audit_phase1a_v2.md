# Phase 1a re-audit after the Checkpoint 1 decisions

Scope: `01_build_universe.py`, `config.py`, `data/clean/universe.parquet` and `output/logs/universe_checks.md`, tested against `CLAUDE.md` section 8. WRDS access was read-only and I did not edit Agent 1's files. No scores or stock returns were used, so no finding here was chosen for its effect on performance.

Terms: **point-in-time** means the value as known on that date. **Look-ahead** means using something not yet known on that date. **Sibling link** means taking the company ID (GVKEY) from another share class of the same company (PERMCO). **Mortgage REIT** means a REIT that lends against property or holds mortgage securities rather than owning buildings.

Files tested (SHA-256, first 12 characters): `01_build_universe.py` 4C948CC171CB, `config.py` E5F5753A00F9, `universe.parquet` 7301144C123C, `universe_checks.md` C4EAC761444547 (first 14).

Evidence: `verification/audit_06_data.py`, `audit_06b_followup.py`, `audit_07_checks_can_fail.py`, and their `_output.txt` files.

## Result

**No look-ahead or survivorship bug found, and the build matches section 8. One decision for the user and one check to strengthen should be settled before Phase 1b.**

| ID | Severity | Finding | Action |
|---|---|---|---|
| V1 | Medium | 3 mortgage REITs are kept (19 company-dates), and they are the only kept REITs after Sept 2016 | User decision, before any scores exist |
| V2 | Medium | If the stopped-trading removal broke, the script would still exit 0 | Agent 1: make it a failure |
| V3 | Low | A sibling gvkey from another company is caught only if that company is also on the list | Agent 1: add a check |
| V4 | Low | The included range was set after the counts were seen, so passing it proves little | Describe it as a sanity check |
| V5 | Low | Trend check still compares only first and last years | Note, or strengthen |
| V6 | Low | 4 included names delist on the formation date | Phase 5 must handle them |
| V7 | Low | 20 GVKEYs span two PERMCOs across time | Phase 3 must check its year-on-year comparisons |

**Reproducibility:** my separate rebuild matches all 10,500 rows on company, rank and market cap, and `included` matches on every row (8,433 included). Running the script again with outputs sent to a scratch folder gave an identical parquet.

## (a) Is the row-level REIT flag point-in-time? Yes, no look-ahead found

The flag switches on or after the real effective date, never earlier. It also has to matter before it could cause harm: it changes membership only for a REIT in sector 40 (266 company-dates) or held as `SB` shares (69). A REIT in any other sector is included regardless (265).

| Company | Flag first set: month (start date in dated issuer history) | Actual conversion | First list row where the flag kept it |
|---|---|---|---|
| Weyerhaeuser | Jan 2010 (2010-01-04) | Elected for tax year 2010; announced Dec 2009; special distribution declared July 2010 | May 2011 |
| Equinix | Jan 2015 (2015-01-23) | Effective 2015-01-01; board approved 2014-12-23 | May 2016 |
| Iron Mountain | Jan 2015 (2015-01-21) | Elected effective 2014-01-01; key IRS rulings June 2014 | May 2016 |
| American Tower | Jan 2012 (2012-01-03) | Effective 2012-01-01 | May 2012 |
| Crown Castle | Jan 2014 (2014-01-02) | Effective 2014-01-01 | May 2014 |

- **Backfill test.** A flag backfilled by later events would show the conversion at the start of a firm's history or before the real date. It does not. All five firms read `CORP` for years first. Iron Mountain is flagged about a year after its effective date, which is the opposite of look-ahead.
- **Weyerhaeuser is the closest call.** The May 2010 row is flagged before the July 2010 distribution, but it was in sector 15 then, so the flag changed nothing. It was first kept in May 2011.
- **All list securities.** 17 securities that were ever on a list have a move to or from REIT. 12 of the 17 moves fall in January, which fits tax-year elections. None sits on a list row in a way that changes the result: names in the real-estate group while still `CORP` are CBRE, Forest City 2007, Realogy and St Joe, and all stay excluded.
- **Independent cross-check.** Of the 266 kept rows, 261 are in dated GICS group 4040 and 5 are mortgage REITs that GICS moved to 4020 in 2016.
- **Starwood Hotels.** `REIT` on the 2005 row, then a new security coded `CORP` from April 2006, which fits its restructuring.

**Limit:** the flag is not perfect. CBS Outdoor/Outfront is `CORP` throughout in CRSP, which I believe is wrong because it converted, but it has no list row, so nothing changes. I also cannot prove CRSP never revised a flag later; no as-first-published copy is available. Conversion dates for the five companies come from their SEC filings, and for Weyerhaeuser the filings support the tax year rather than one exact date.

## (b) Mortgage REITs among kept REITs: 19 company-dates, 3 companies

| Year | Names | Count |
|---|---|---|
| 2005 | iStar Financial | 1 |
| 2006 | none | 0 |
| 2007 | iStar Financial | 1 |
| 2008-2011 | Annaly | 1 a year |
| 2012-2014 | Annaly, American Capital Agency | 2 a year |
| 2015-2018 | Annaly | 1 a year |
| 2019 | Annaly, AGNC | 2 |
| 2020 | Annaly | 1 |
| 2021-2025 | none | 0 |

That is 0.23% of all included rows, at ranks 179-495.

- **Identification:** 18 rows use the mortgage REIT GICS codes (40402030, 40204010). iStar 2005 carries the generic code 40401010, the code all 15 kept REITs have in 2005. I added it by reading that list of names. No other name in it looks like a lender, but that is my judgment rather than a data field.
- **Mortgage REITs are the only kept REITs after 2016.** All 5 kept rows in 2017-2020 are Annaly and AGNC. Equity REITs are in sector 60 by then and need no exception.
- **Wording mismatch.** The `config.py` comment says "(pre-2016)", yet the code applies on all dates, which matches section 8's "on all dates".

### V1. Medium: decision for the user

Section 8 was approved with REITs in general in mind, and the code follows it. But these are lenders, which is what the financials exclusion is meant to remove, and the F-score's margin and turnover inputs may not mean the same for them. Options, to be chosen before scores exist:

1. Keep them and disclose them, which is what section 8 currently says.
2. Exclude mortgage REITs on all dates, using a dated sub-industry code plus a named exception for iStar 2005. This is a new rule in `config.py`.

I have no recommendation based on results. The effect on list size is at most 2 names a year.

## (c) Sibling links: correct on all 34 uses

Each of the 34 logged uses (8 companies) passed all of these, tested from the raw link table:

- The held security is in that PERMCO on the date.
- The sibling security is listed in the same PERMCO on the date.
- The sibling link is valid on the date and is LC/LU with P/C.
- The link's own PERMCO equals the company's.
- The company has exactly one valid GVKEY on the date.
- The held class's own (disallowed) link points to the same GVKEY, which is strong confirmation it is the same company.
- The Compustat name matches the company.

Every universe row lacking a direct valid link is in the sibling log, so none are unlogged. No two companies share a GVKEY on any date. Multi-GVKEY companies stay failed as designed (Liberty 2016 and 2017).

**One name to watch:** Liberty 2015 uses GVKEY 017010, now named "Liberty Media SiriusXM Group". Its link is valid 2013-01-14 to 2016-04-17, so the 2015 use is right, but its accounts should be looked at in Phase 3.

### V3. Low: check gap

The code is correct, but the checks would not catch a future error. When I forced Alphabet onto Apple's GVKEY, the shared-GVKEY check failed as it should. When I forced it onto Lehman's, which is not on the list on those dates, the run passed with exit 0. Add a failure if a sibling link's `lpermco` differs from the company's PERMCO.

## (d) Stopped-trading removal: no future information, no live names removed

All 727 removals (422 otherwise eligible, 19 in the top 500) match my own calculation.

| Test | Result |
|---|---|
| Delisting record in `crsp.stkdelists`, same month | 727 of 727 |
| Delisting date after the formation date (future information) | 0 |
| Delisting date equals the last price date | 727 of 727 |
| Delisting on the formation date itself among removals | 0 |
| Exchange-trading rows after the last price, through the formation date | 0 |
| Volume on those days | 0 |
| Priced monthly row after removal | 0 |

Each removal has exactly one later daily row by the formation date, flagged `DA`, `DP` or `DM` with status `D` and exchange `X`. These are CRSP's delisting entries, not trades. My first script labelled them "TRADING FOUND"; that label in `audit_06_output.txt` is wrong, and the follow-up settles it.

- **Over-the-counter trading.** Some removed stocks may have traded off-exchange after delisting. CRSP does not show it here, and they would fail the NYSE/Nasdaq/NYSE American rule anyway.
- **Partial removals are correct.** 9 removed classes belong to companies with another class still trading (e.g. Liberty 2006, QVC 2025). Only the class that stopped is removed.
- **Not removed, correctly.** 5 eligible rows have an older price but no delisting flag. One is in a listed company: a small, thinly traded Molson Coors class in 2007, priced the day before. It is still listed.
- **The rule uses only the row's own May flag and dates**, all known by the formation date.

### V6. Low: for Phase 5

92 flagged securities delist on the formation date itself and stay in, as the rule intends. Four are held and included: CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017. They have no later returns, so Phase 5 must treat them under the delisting rule. Waste Connections looks like a merger into a successor security and is worth checking.

## (e) Can each changed check fail? Yes, with two weak spots

I ran the real `main()` with one thing broken at a time and its output sent to a scratch folder.

| What I broke | Outcome |
|---|---|
| Size set above eligible names | FAIL: company count |
| Included range (380, 425) | FAIL: 2007=379 |
| Included range (375, 416) | FAIL: 2021=417 |
| `KEEP_REITS_ON_ALL_DATES` False | FAIL: 4 dates (2005, 2006, 2007, 2016) |
| `MIN_LINK_RATE` 0.998 | FAIL: by name |
| Sibling rule off | FAIL: by market cap on 9 dates; overall was 98.11% |
| Two companies share a GVKEY | FAIL |
| Security with several GVKEYs | FAIL |
| GVKEY with several sectors | FAIL |
| Sibling forced to a listed company's GVKEY | FAIL |
| **Sibling forced to an unlisted company's GVKEY** | **Passed, exit 0 (V3)** |
| Lehman removed from the data | FAIL |
| Unknown required name | FAIL |
| 2025 market caps cut 90% | FAIL: trend |
| `CUTOFF_DIP_YEAR_REQUIRED` = 2010 | FAIL: dip absent |
| **Stopped-trading removal off** | **FLAG only, exit 0 (V2)** |
| Move limit 10% | 16 flags, exit 0, as approved |
| Reported dip year 2021 | No failure, as approved |

The sibling-off test shows the per-date market cap test is what catches Alphabet: the overall rate alone would have passed.

### V2. Medium

Section 8 requires removal before ranking. With it off, 18 stopped securities return to the list and the run reports only a flag and exit 0. Since a rule break should fail loudly, change this flag to a failure whenever any held security has `mthdelflg <> 'N'` and `mthprcdt < formation_date`. Do not fail on all older prices: a held class with no delisting flag could legitimately have one.

### V4. Low

The 375-425 range was approved after the counts were known (actual 379-417). It can fail, but passing shows little, so call it a sanity range. The low end has only 4 names of margin.

### V5. Low

The trend check compares only 2005 and 2025. It caught a 90% cut in the last year, but it cannot see problems in between. The 50% flag covers much of that gap.

## Section 8 compliance

| Item | Result |
|---|---|
| 1. REITs stay in on all dates | Met; see V1 |
| 2. Sibling links, returns from held class, each logged | Met |
| 3. LC/LU kept; Eaton 2005-2012 and Ceridian 2020 out and reported | Met |
| 4. No sector: excluded and reported, no current-only fill | Met (Yahoo, 13 dates) |
| 5. Stopped-trading names removed before ranking | Met; see V2 |
| 6. Filter codes in `config.py`; UG and Cboe excluded | Met |
| 7. 375-425, 50% as a flag, 2020 reported | Met |
| 8. Link rate by name and market cap; required names in config | Met |
| 9. RSP and SPY | Set in `config.py`; used in later phases |

The earlier findings on Alphabet's link, stopped-trading names and rules outside `config.py` are resolved. The remaining constants in the script are labels and report settings; the ones I traced do not affect membership.

## V7. Low: for Phase 3

20 GVKEYs appear under two PERMCOs at different times, never on the same date. Most are re-listings or successors, such as HCA, Dell, GM, Dow to DuPont, and IAC to Match. Year-on-year F-score comparisons should be checked across those joins. No action is needed in Phase 1a.

## Sources for conversion dates

- Weyerhaeuser: [2010 proxy statement](https://www.sec.gov/Archives/edgar/data/0000106535/000119312510039219/ddef14a.htm), [FY2010 10-K](https://www.sec.gov/Archives/edgar/data/0000106535/000119312511047563/d10k.htm)
- Equinix: [FY2015 10-K](https://www.sec.gov/Archives/edgar/data/1101239/000162828016011802/equix_20151231x10k.htm)
- Iron Mountain: [June 2014 8-K press release](https://www.sec.gov/Archives/edgar/data/0001020569/000110465914048318/a14-16059_1ex99d1.htm), [FY2014 10-K](https://www.sec.gov/Archives/edgar/data/0001020569/000104746915001413/a2223186z10-k.htm)
- American Tower: [FY2012 10-K](https://www.sec.gov/Archives/edgar/data/0001053507/000119312513077821/d448028d10k.htm)
- Crown Castle: [FY2014 10-K](https://www.sec.gov/Archives/edgar/data/0001051470/000105147015000034/cci10-k123114.htm)

## Final audit after the mortgage REIT exclusion

This section is later than everything above and replaces V1, V2, V3 and V5. The user chose to exclude mortgage REITs on all dates.

Files tested (SHA-256, first 14 characters): `universe.parquet` DE7F2A8BBA9FF4, `01_build_universe.py` B40EF13AF025F4, `config.py` 47822BB173C283, `universe_checks.md` 8C889A430A3C94. All four were unchanged at the end of testing. Evidence: `verification/audit_08_final.py`, `audit_08b_lender_screen.py` and their `_output.txt` files.

**Result: no High or Medium findings. Two Low items remain, and the "no remaining lender" conclusion rests partly on my judgment.**

| Request | Result |
|---|---|
| Full rebuild matches on every row, all 21 dates | Yes. 10,500 rows, 500 a date; 0 differences in permno, rank, market cap, gvkey, sector or `included` (8,414 included, 378-417 a date) |
| Exactly the 19 listed rows changed | Yes. All 19 went from included to not included; no other column or row changed; same set as `universe_mortgage_reits_excluded.csv` |
| No included row has a mortgage code on its date | Yes. 0 rows on the config codes; no other mortgage code found |
| No remaining included REIT looks like a lender | None found, on codes and name review; see the limit below |
| V2, V3 and V5 checks present | Yes, and each fails when broken |
| New code using future information | None found |

### The 19-row comparison

The prior file had been overwritten. I regenerated it by running the real script with `EXCLUDE_MORTGAGE_REITS` off. The result starts `7301144C123C`, the same hash recorded for the prior version above, so this compares against the actual prior file rather than an approximation. Because the exclusion comes after ranking, ranks and the 500th-company cutoff did not move.

### Mortgage codes

- All 247 included rows in sector 40 are row-level REITs in GICS group 4040. None is in another sector 40 group, and no included row is in sector 55.
- Their codes are 40401010 (2005 generic), 40402010, 40402020, 40402035, 40402040, 40402045, 40402050, 40402060 and 40402070. The mortgage code 40402030 is absent.
- To look for codes the config might miss, I listed every code used across lender names in the whole `co_hgic` table. The other financial codes that appear (such as thrift and mortgage finance, 40102010 and 40201050) occur on non-REITs in the list, and those rows are all out through sector 40.
- **The generic 2005 code is the remaining gap.** All REITs share it until 2006-04-30. Among lender names, only iStar reaches the 2005 list, and it is excluded by the named exception. The other 14 included rows on that code are named property owners.

### Limit on the lender conclusion

Accounting data did not settle this. Two screens could not tell lenders from property owners, so neither counts as evidence:

- **Balance sheet:** it flagged nearly every REIT, because Compustat leaves property blank for them and puts real estate under other investments.
- **Interest income share:** `idit` is 0 even for Annaly and AGNC, so the zero or near-zero values among included REITs say nothing.

The conclusion therefore rests on the sub-industry codes and on my reading of all 52 included REIT companies. All are recognisable property, tower, data-centre, timber or net-lease owners. HCP has the highest receivables among the medians screened and holds some property loans, but it is a health-care property owner. This is judgment, not a data field.

### Checks broken on purpose

| What I broke | Outcome |
|---|---|
| V2: stopped-trading removal off | FAIL: 18 held securities listed |
| V3: sibling link row carries a different `lpermco` | FAIL: 9 Alphabet rows |
| V5: cutoff falls through the middle years, ends above the start | FAIL: rank correlation -0.406 |
| Mortgage rows forced to included | FAIL: 19 rows |
| Gvkey overwritten after the sibling step | Passed, exit 0 (L2) |
| Named exception removed | Passed, exit 0 (L1) |
| Mortgage rule off | Passed, exit 0, as designed |

### Future information

I read the whole script. The new code uses the row's own `issuertype`, a `gsubind` valid on the date, and the config list, and it runs after ranking. The other new lines are check logic and report tables. The only current-dated data is the S&P overlap section and the `co_hgic` lookup for it, which are report-only and do not reach the parquet. The one hand-made input is the iStar 2005 exception: a judgment made today, and already marked for disclosure in the write-up.

### Remaining Low items

- **L1. Mortgage check shares the rule's own inputs.** It confirms that rows meeting the rule are out, so it cannot notice a code missing from the config, or the iStar exception being removed or no longer matching. The exception matches on an exact name and year. Today's list is clean by my separate scan. To guard this, fail if the excluded list differs from 19 rows unless a new labelled run is declared.
- **L2. The V3 check reads the link row, not the final gvkey.** The script assigns the gvkey directly from those rows, so there is no current path for them to differ. This narrows the earlier V3 gap but does not fully close it; no action is needed unless that code changes.

The included range now has a margin of 3 names at the low end (378 against 375), so V4 still applies. V6 and V7 remain for Phases 5 and 3.
