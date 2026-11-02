# Labelled variant `reit_liquidity_substitute`: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**Not the headline, and not a blind test.** The user chose this rule after similar variants had been seen. Terms: a **REIT** is a real estate investment trust; **F_DLIQUID** is the test that the current ratio rose, which REITs usually cannot compute; **che** is cash and short-term investments and **lt** is total liabilities; **alpha** is return left after the six factors; a **t-stat** beyond about 2 is treated as significant.

**Rule.** For an included row whose CRSP issuer type on the formation date is `REIT` and whose F_DLIQUID cannot be computed: the signal passes if che / lt rose, on the same one-year and stub rules. Null che, or null or non-positive lt, leaves it uncomputable and the company-year drops. Standard buckets, 0-9. Mortgage REITs stay excluded, and availability and age rules are unchanged. Other firms with no liquidity signal stay dropped.

June 2005 to December 2025 on CRSP, net of costs; the 2025 portfolio is partial (7 of 12 months). Separate from the 2026 extension.

**Headline unchanged:** files hashed before and after this run: all identical. The engine reproduces `portfolio_returns.csv` to 1.3e-16.

Null return rule: [{'formation_date': datetime.date(2008, 5, 30), 'permno': np.int64(79129), 'month': '2009-05', 'treatment': 'held flat: no return, not an exit'}].

## Comparison with the headline

| metric | headline | variant | change |
|---|---|---|---|
| High_alpha_annual | -0.0078 | -0.0101 | -0.0023 |
| High_alpha_t | -0.7146 | -0.9054 | -0.1908 |
| High_minus_Benchmark_annual | -0.0029 | -0.003 | -0.0001 |
| High_minus_Benchmark_alpha | -0.0095 | -0.0096 | -0.0001 |
| High_minus_Benchmark_alpha_t | -1.0229 | -1.0029 | 0.02 |
| High_sharpe | 0.6049 | 0.592 | -0.0129 |
| Benchmark_sharpe | 0.6458 | 0.6307 | -0.0151 |
| High_CAGR | 0.1091 | 0.1063 | -0.0028 |
| Benchmark_CAGR | 0.1135 | 0.1106 | -0.0028 |
| information_ratio | -0.0795 | -0.0821 | -0.0026 |
| Spread_annual | -0.0057 | -0.009 | -0.0034 |
| Spread_alpha_annual | -0.0204 | -0.0221 | -0.0017 |
| Spread_alpha_t | -0.7238 | -0.8172 | -0.0934 |
| High_beats_Benchmark_years | 10.0 | 10.0 | 0.0 |
| complete_years | 20.0 | 20.0 | 0.0 |
| High_turnover_two_way | 1.6388 | 1.6412 | 0.0024 |
| High_names_median | 73.0 | 75.0 | 2.0 |
| High_names_min | 43.0 | 48.0 | 5.0 |
| High_dates_under_minimum | 0.0 | 0.0 | 0.0 |
| Middle_names_median | 255.0 | 269.0 | 14.0 |
| Low_names_median | 31.0 | 35.0 | 4.0 |
| Low_names_min | 20.0 | 21.0 | 1.0 |
| Low_dates_under_minimum | 0.0 | 0.0 | 0.0 |
| Benchmark_names_median | 365.0 | 385.0 | 20.0 |
| Benchmark_names_min | 318.0 | 331.0 | 13.0 |


## Subperiods

| run | period | months | High_alpha_annual | High_alpha_t | High_minus_Benchmark_annual | High_sharpe | Benchmark_sharpe | Spread_alpha_annual | Spread_alpha_t |
|---|---|---|---|---|---|---|---|---|---|
| headline | 2005-06 to 2015-05 | 120 | 0.0248 | 1.7643 | 0.0102 | 0.7109 | 0.6576 | 0.0205 | 0.5111 |
| headline | 2015-06 to 2025-12 | 127 | -0.0383 | -4.1041 | -0.0153 | 0.5065 | 0.6319 | -0.0572 | -1.4893 |
| reit_liquidity_substitute | 2005-06 to 2015-05 | 120 | 0.0243 | 1.7537 | 0.0106 | 0.7087 | 0.6462 | 0.0219 | 0.6131 |
| reit_liquidity_substitute | 2015-06 to 2025-12 | 127 | -0.0424 | -4.3959 | -0.0158 | 0.4834 | 0.6133 | -0.0608 | -1.6395 |


## Rows added: 430

| bucket | rows_added |
|---|---|
| High | 61 |
| Middle | 302 |
| Low | 67 |


### By formation year

| year | High | Middle | Low | all |
|---|---|---|---|---|
| 2005 | 1 | 9 | 3 | 13 |
| 2006 | 2 | 10 | 2 | 14 |
| 2007 | 2 | 10 | 4 | 16 |
| 2008 | 1 | 10 | 4 | 15 |
| 2009 | 1 | 7 | 5 | 13 |
| 2010 | 1 | 13 | 6 | 20 |
| 2011 | 5 | 13 | 2 | 20 |
| 2012 | 2 | 17 | 3 | 22 |
| 2013 | 2 | 15 | 3 | 20 |
| 2014 | 3 | 13 | 5 | 21 |
| 2015 | 3 | 15 | 3 | 21 |
| 2016 | 5 | 19 | 3 | 27 |
| 2017 | 5 | 18 | 2 | 25 |
| 2018 | 2 | 15 | 4 | 21 |
| 2019 | 6 | 20 | 1 | 27 |
| 2020 | 1 | 20 | 3 | 24 |
| 2021 | 2 | 10 | 7 | 19 |
| 2022 | 4 | 20 | 2 | 26 |
| 2023 | 3 | 22 | 1 | 26 |
| 2024 | 6 | 13 | 1 | 20 |
| 2025 | 4 | 13 | 3 | 20 |


Every row is in `rows_added.csv`. Headline rows that changed fiscal year, score or bucket because a newer substitute score now applies: 0. Headline rows lost: 0.


## REIT coverage

Included REIT rows: 512. Scored before 80 (15.6%), after 510 (99.6%).

| gsector | reit_rows | scored_before | scored_after |
|---|---|---|---|
| 15 | 1 | 0 | 1 |
| 25 | 1 | 1 | 1 |
| 40 | 247 | 26 | 247 |
| 45 | 1 | 1 | 1 |
| 60 | 262 | 52 | 260 |



| year | reit_rows | scored_before | scored_after |
|---|---|---|---|
| 2005 | 15 | 2 | 15 |
| 2006 | 15 | 1 | 15 |
| 2007 | 17 | 1 | 17 |
| 2008 | 16 | 1 | 16 |
| 2009 | 15 | 2 | 15 |
| 2010 | 21 | 1 | 21 |
| 2011 | 22 | 2 | 22 |
| 2012 | 25 | 3 | 25 |
| 2013 | 23 | 3 | 23 |
| 2014 | 24 | 3 | 24 |
| 2015 | 25 | 4 | 25 |
| 2016 | 32 | 5 | 32 |
| 2017 | 31 | 6 | 31 |
| 2018 | 28 | 6 | 27 |
| 2019 | 34 | 6 | 33 |
| 2020 | 29 | 5 | 29 |
| 2021 | 24 | 5 | 24 |
| 2022 | 32 | 6 | 32 |
| 2023 | 32 | 6 | 32 |
| 2024 | 26 | 6 | 26 |
| 2025 | 26 | 6 | 26 |


### Why the remaining REIT rows are unscored

| reason | reit_rows |
|---|---|
| another signal uncomputable | 2 |


## Pass rate of the new signal

| set | rows | pass_pct |
|---|---|---|
| List rows that use the signal | 430 | 48.1 |
| Company-years of REIT names where it is computable | 757 | 48.1 |



| year | rows | pass_pct |
|---|---|---|
| 2005 | 13 | 46.2 |
| 2006 | 14 | 42.9 |
| 2007 | 16 | 68.8 |
| 2008 | 15 | 33.3 |
| 2009 | 13 | 61.5 |
| 2010 | 20 | 55.0 |
| 2011 | 20 | 55.0 |
| 2012 | 22 | 27.3 |
| 2013 | 20 | 60.0 |
| 2014 | 21 | 61.9 |
| 2015 | 21 | 42.9 |
| 2016 | 27 | 44.4 |
| 2017 | 25 | 52.0 |
| 2018 | 21 | 38.1 |
| 2019 | 27 | 48.1 |
| 2020 | 24 | 33.3 |
| 2021 | 19 | 57.9 |
| 2022 | 26 | 46.2 |
| 2023 | 26 | 26.9 |
| 2024 | 20 | 60.0 |
| 2025 | 20 | 65.0 |


## Substitute uncomputable, company-years of REIT names: 0

None.


Non-positive lt among those needing the signal: 0. Each case is in `substitute_uncomputable.csv`.


## F_DLIQUID-alone drops that remain

Company-years, FY2004-2024, with only F_DLIQUID missing: 3124. Of these, 430 now supply a score on an included list. The rest, 2694, stay dropped from every list: non-REITs, or REIT company-years never chosen on a date or with no computable substitute.

| set | included_rows_unscored | of_which_only_liquidity_missing |
|---|---|---|
| Headline | 843 | 641 |
| This variant, all rows | 413 | 211 |
| This variant, REIT rows | 2 | 0 |
| This variant, non-REIT rows | 411 | 211 |


## Thin buckets (under 10 names): 0

None.
