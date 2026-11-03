# Drops: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**0 check failure(s).** One row per formation date: `drops_by_date.csv`; one row per unscored name: `drops_reasons.csv` (same folder). No return value was used.


## Totals over the 21 lists

- (a) Universe names with no GVKEY link: 13; (b) no sector: 13; (c) securities removed as stopped trading before ranking: 727.
- (d) Included list rows: 8414. Unscored: 800 (9.5%). Split: missing 750, stale 50.
- (e) Average share of included market cap held by unscored names per date: 6.3%.
- Unscored names in GICS sectors 40 and 60 (REITs sit in 40 until the 2016 change, then 60; sector 40 also holds any remaining financials): 431 of 800 (53.9%).

## Unscored names by reason

| reason | list_rows | share_of_unscored_pct |
|---|---|---|
| missing signal | 689 | 86.1 |
| unscorable t-2 (no consecutive prior years) | 54 | 6.8 |
| no 10-K filing date | 25 | 3.1 |
| stale score | 15 | 1.9 |
| no usable fiscal year | 13 | 1.6 |
| stub or fiscal-year change | 4 | 0.5 |


Missing-signal reasons, counted per signal (a name missing two signals counts in both):

| signal | unscored_rows_missing_it |
|---|---|
| F_ROA | 3 |
| F_CFO | 3 |
| F_DROA | 8 |
| F_ACCRUAL | 3 |
| F_DLEVER | 33 |
| F_DLIQUID | 647 |
| F_EQ_OFFER | 0 |
| F_DMARGIN | 15 |
| F_DTURN | 8 |


## By formation date

| formation_date | universe_companies | a_no_gvkey_link | b_no_sector | c_removed_stopped_trading | included | d_unscored | e_unscored_mktcap_share | unscored_in_sectors_40_60 |
|---|---|---|---|---|---|---|---|---|
| 2005-05-31 | 500 | 1 | 1 | 38 | 384 | 65 | 0.1435 | 13 |
| 2006-05-31 | 500 | 1 | 1 | 38 | 381 | 37 | 0.1119 | 14 |
| 2007-05-31 | 500 | 1 | 1 | 44 | 378 | 40 | 0.1098 | 16 |
| 2008-05-30 | 500 | 1 | 1 | 34 | 393 | 35 | 0.0823 | 15 |
| 2009-05-29 | 500 | 1 | 1 | 49 | 404 | 26 | 0.0488 | 13 |
| 2010-05-28 | 500 | 1 | 1 | 35 | 402 | 33 | 0.0566 | 19 |
| 2011-05-31 | 500 | 1 | 1 | 23 | 413 | 31 | 0.0622 | 20 |
| 2012-05-31 | 500 | 1 | 1 | 23 | 407 | 41 | 0.0756 | 22 |
| 2013-05-31 | 500 | 0 | 1 | 26 | 408 | 39 | 0.0758 | 20 |
| 2014-05-30 | 500 | 0 | 1 | 14 | 410 | 45 | 0.0741 | 21 |
| 2015-05-29 | 500 | 0 | 1 | 20 | 409 | 40 | 0.0707 | 21 |
| 2016-05-31 | 500 | 1 | 1 | 38 | 400 | 43 | 0.0752 | 27 |
| 2017-05-31 | 500 | 2 | 1 | 28 | 398 | 40 | 0.0546 | 25 |
| 2018-05-31 | 500 | 1 | 0 | 29 | 403 | 35 | 0.04 | 22 |
| 2019-05-31 | 500 | 0 | 0 | 41 | 396 | 47 | 0.0527 | 28 |
| 2020-05-29 | 500 | 1 | 0 | 38 | 408 | 39 | 0.0344 | 24 |
| 2021-05-28 | 500 | 0 | 0 | 17 | 417 | 35 | 0.0378 | 19 |
| 2022-05-31 | 500 | 0 | 0 | 39 | 409 | 35 | 0.0329 | 26 |
| 2023-05-31 | 500 | 0 | 0 | 46 | 404 | 37 | 0.032 | 26 |
| 2024-05-31 | 500 | 0 | 0 | 56 | 397 | 28 | 0.0254 | 20 |
| 2025-05-30 | 500 | 0 | 0 | 51 | 393 | 29 | 0.0249 | 20 |


Per-reason counts by date are in the CSV (`reason: ...` and `missing_signal: ...` columns).
