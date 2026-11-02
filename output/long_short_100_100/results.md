# Long/short, 100% long High and 100% short Low: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**Labelled variant, not the headline, and not a blind test: the Spread had already been seen.** The borrow fee is a flat assumption, not data. From January 2026, returns are Compustat's, and the main result stops at December 2025. Stopped runs: none.

**Terms.** **NAV** is net asset value, the capital in the strategy. **Long leg** owns High; **short leg** has sold Low and owes its value. **Borrow fee** is what a short seller pays to borrow the shares. **Cash** is NAV minus long value plus short value, and earns the risk-free rate. **CAGR** is the constant yearly growth rate. **Sharpe** is return above the risk-free rate per unit of volatility. **Max drawdown** is the largest peak-to-trough fall. **Alpha** is return left after six factors, with Newey-West standard errors over 12 months. A **t-stat** beyond about 2 is treated as significant. **Loading** is sensitivity to a factor. **bp** is 0.01%.

**Mechanics.** Each June, costs of 10 bp on each leg's two-way turnover come out of NAV, then long = short = NAV. Costs are measured on NAV before the charge; the first June counts as opening both legs. Resizing the two legs back to equal is not separately charged, because the rule charges each leg's turnover. Within the year the legs drift. Delisted names use the existing treatment inside each leg. A short position's return here is the opposite of Low's, including delisting returns, and no recall or margin limit is modelled.

**Mechanics test:** with free monthly reset and no fee or cost, return above rf equals the gross Spread to 2.9e-16. **Existing files:** hashed before and after this run: all identical.

## Performance

| scope | series | months | CAGR | volatility | sharpe | max_drawdown | worst_year | worst_year_label | years_positive | complete_years | alpha_annual | alpha_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | Long/short, 0.50% borrow | 247 | -0.018 | 0.1227 | -0.2224 | -0.7579 | -0.3091 | 2020 | 12 | 20 | -0.0453 | -1.4842 |
| June 2005 to December 2025 (CRSP) | Long/short, 2.00% borrow stress | 247 | -0.0343 | 0.1242 | -0.3535 | -0.8066 | -0.3291 | 2020 | 11 | 20 | -0.0618 | -1.9821 |
| June 2005 to December 2025 (CRSP) | Long-only High | 247 | 0.1091 | 0.1679 | 0.6049 | -0.4436 | -0.2953 | 2008 | 14 | 20 | -0.0078 | -0.7146 |
| June 2005 to December 2025 (CRSP) | Benchmark | 247 | 0.1135 | 0.1617 | 0.6458 | -0.4909 | -0.3244 | 2008 | 14 | 20 | 0.0018 | 0.2547 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long/short, 0.50% borrow | 252 | -0.0359 | 0.1311 | -0.3424 | -0.7579 | -0.3265 | 2025 | 12 | 21 | -0.058 | -1.8639 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long/short, 2.00% borrow stress | 252 | -0.0523 | 0.1328 | -0.4658 | -0.8066 | -0.3442 | 2025 | 11 | 21 | -0.0749 | -2.3541 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long-only High | 252 | 0.1144 | 0.1692 | 0.6279 | -0.4436 | -0.2953 | 2008 | 15 | 21 | -0.0047 | -0.4219 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Benchmark | 252 | 0.1186 | 0.1621 | 0.6712 | -0.4909 | -0.3244 | 2008 | 15 | 21 | 0.0039 | 0.5877 |


Worst year and years positive use complete June-May years. Long/short's figures are after trading costs and borrow fee.


## Factor loadings

| scope | series | r_squared | beta_Mkt-RF | t_Mkt-RF | beta_SMB | t_SMB | beta_HML | t_HML | beta_RMW | t_RMW | beta_CMA | t_CMA | beta_MOM | t_MOM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | Long/short, 0.50% borrow | 0.158 | 0.003 | 0.041 | -0.249 | -1.971 | 0.064 | 0.581 | 0.521 | 2.893 | 0.071 | 0.495 | 0.028 | 0.589 |
| June 2005 to December 2025 (CRSP) | Long/short, 2.00% borrow stress | 0.158 | 0.003 | 0.034 | -0.252 | -1.964 | 0.062 | 0.56 | 0.525 | 2.897 | 0.075 | 0.516 | 0.027 | 0.548 |
| June 2005 to December 2025 (CRSP) | Long-only High | 0.913 | 1.022 | 42.205 | 0.184 | 4.34 | -0.052 | -0.787 | 0.192 | 3.409 | 0.041 | 0.392 | 0.001 | 0.029 |
| June 2005 to December 2025 (CRSP) | Benchmark | 0.962 | 1.003 | 53.541 | 0.167 | 6.983 | -0.069 | -1.559 | 0.047 | 1.361 | 0.066 | 1.1 | -0.011 | -0.449 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long/short, 0.50% borrow | 0.168 | -0.018 | -0.23 | -0.261 | -2.037 | -0.015 | -0.114 | 0.556 | 3.455 | 0.171 | 1.03 | -0.042 | -0.554 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long/short, 2.00% borrow stress | 0.168 | -0.019 | -0.242 | -0.263 | -2.024 | -0.018 | -0.134 | 0.563 | 3.472 | 0.176 | 1.05 | -0.045 | -0.58 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Long-only High | 0.907 | 1.028 | 42.533 | 0.171 | 3.964 | -0.067 | -0.995 | 0.161 | 2.747 | 0.088 | 0.813 | -0.002 | -0.062 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Benchmark | 0.959 | 1.002 | 53.864 | 0.171 | 7.16 | -0.078 | -1.792 | 0.049 | 1.498 | 0.102 | 1.56 | -0.013 | -0.583 |


## Subperiods

| scope | period | series | months | CAGR | volatility | sharpe | max_drawdown | alpha_annual | alpha_t |
|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Long/short, 0.50% borrow | 120 | 0.0125 | 0.0933 | 0.0393 | -0.3516 | 0.0002 | 0.0049 |
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Long/short, 2.00% borrow stress | 120 | -0.0034 | 0.0942 | -0.1306 | -0.4201 | -0.0156 | -0.3701 |
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Long-only High | 120 | 0.1233 | 0.165 | 0.7109 | -0.4436 | 0.0248 | 1.7643 |
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Benchmark | 120 | 0.1124 | 0.1628 | 0.6576 | -0.4909 | 0.0149 | 1.6719 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Long/short, 0.50% borrow | 127 | -0.0459 | 0.1451 | -0.3887 | -0.656 | -0.0868 | -1.9529 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Long/short, 2.00% borrow stress | 127 | -0.0625 | 0.147 | -0.5014 | -0.6855 | -0.1042 | -2.2915 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Long-only High | 127 | 0.0958 | 0.1713 | 0.5065 | -0.2713 | -0.0383 | -4.1041 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Benchmark | 127 | 0.1145 | 0.1614 | 0.6319 | -0.237 | -0.012 | -1.6321 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Long/short, 0.50% borrow | 132 | -0.0779 | 0.1572 | -0.5648 | -0.656 | -0.1031 | -2.3508 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Long/short, 2.00% borrow stress | 132 | -0.0948 | 0.1594 | -0.6697 | -0.6855 | -0.1209 | -2.6941 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Long-only High | 132 | 0.1063 | 0.1735 | 0.5543 | -0.2713 | -0.0325 | -3.1647 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Benchmark | 132 | 0.1243 | 0.162 | 0.6811 | -0.237 | -0.0073 | -1.0621 |


**Caution on significance.** At |t| of 2 or more, in subperiods: Long/short, 2.00% borrow stress, 2015-06 to 2025-12 (127 months), t -2.29; Long-only High, 2015-06 to 2025-12 (127 months), t -4.10; Long/short, 0.50% borrow, 2015-06 to 2026-05 (132 months), t -2.35; Long/short, 2.00% borrow stress, 2015-06 to 2026-05 (132 months), t -2.69; Long-only High, 2015-06 to 2026-05 (132 months), t -3.16. Over a full window: Long/short, 2.00% borrow stress, June 2005 to May 2026 (CRSP, then Compustat from January 2026) (252 months), t -2.35. The main-result stress t is -1.98, so no full-period alpha in the main result reaches 2.


The audit (`verification/data_audit_long_short.md`) ran the random-portfolio tests on this series. The two t's of -2.35 are not evidence about the F-score: for 2015-06 to 2026-05, shuffled scores within sectors average t -2.11, and 56.5% of them pass |t| of 2. By t, the result is ordinary for same-sector portfolios, at 40% or more of draws at or below it in each row tested. The test also oversizes: |t| of 2 is more like 2.3-2.5 for a true 5% level, and no row is clearly significant at 5% under all checks. The -2.5 to -3.6 range belongs to long-only High in 2015-25, not to this series.


## How large the book became

"100/100" holds only at each June reset. Gross is (long + short) / NAV and net is (long - short) / NAV, at month-ends.

| scope | peak_gross | peak_gross_month | net_at_that_month | lowest_net | lowest_net_month | peak_short_share_of_NAV | last_month | last_gross | last_net | last_short_share_of_NAV |
|---|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | 5.02 | 2021-02 | -0.7 | -0.7 | 2021-02 | 2.86 | 2025-12 | 2.24 | -0.02 | 1.13 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 5.02 | 2021-02 | -0.7 | -0.7 | 2021-02 | 2.86 | 2026-05 | 4.33 | -0.53 | 2.43 |


The audit also found Western Digital alone at 46% of NAV and Intel at 26% at the end of May 2026. Few managers or brokers would let such a book run to this size, and no margin limit is modelled. Forced cuts could have helped or hurt, depending on the trigger.


## Monthly reset with charges: a second view beside the locked result

The annual reset stays the locked result. It tests a position opened 100/100 and left alone for 12 months. This second view holds the book near 100/100: each non-June month, each leg is resized pro rata back to NAV, with 10 bp on each dollar of that resize. June keeps the same turnover charge as the locked result, with no extra resize charge. Read the two together.

| scope | series | CAGR | volatility | sharpe | max_drawdown | worst_year | alpha_annual | alpha_t |
|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | Annual reset (locked result) | -0.018 | 0.1227 | -0.2224 | -0.7579 | -0.3091 | -0.0453 | -1.4842 |
| June 2005 to December 2025 (CRSP) | Monthly reset, charged | -0.0042 | 0.1041 | -0.1483 | -0.6749 | -0.2326 | -0.03 | -1.0631 |
| June 2005 to December 2025 (CRSP) | Annual reset (locked result), 2.00% borrow | -0.0343 | 0.1242 | -0.3535 | -0.8066 | -0.3291 | -0.0618 | -1.9821 |
| June 2005 to December 2025 (CRSP) | Monthly reset, charged, 2.00% borrow | -0.019 | 0.1041 | -0.294 | -0.7346 | -0.2443 | -0.045 | -1.5951 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Annual reset (locked result) | -0.0359 | 0.1311 | -0.3424 | -0.7579 | -0.3265 | -0.058 | -1.8639 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, charged | -0.0155 | 0.1081 | -0.2486 | -0.6749 | -0.2326 | -0.0378 | -1.3499 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Annual reset (locked result), 2.00% borrow | -0.0523 | 0.1328 | -0.4658 | -0.8066 | -0.3442 | -0.0749 | -2.3541 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, charged, 2.00% borrow | -0.0302 | 0.1081 | -0.3885 | -0.7346 | -0.2443 | -0.0528 | -1.8851 |



| scope | period | series | months | CAGR | volatility | sharpe | max_drawdown | alpha_annual | alpha_t |
|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Monthly reset, charged | 120 | 0.0205 | 0.0905 | 0.1263 | -0.357 | 0.0108 | 0.2669 |
| June 2005 to December 2025 (CRSP) | 2005-06 to 2015-05 | Monthly reset, charged, 2.00% borrow | 120 | 0.0053 | 0.0905 | -0.0423 | -0.4164 | -0.0042 | -0.1043 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Monthly reset, charged | 127 | -0.0269 | 0.1155 | -0.352 | -0.5308 | -0.0669 | -1.7437 |
| June 2005 to December 2025 (CRSP) | 2015-06 to 2025-12 | Monthly reset, charged, 2.00% borrow | 127 | -0.0415 | 0.1155 | -0.483 | -0.5702 | -0.0819 | -2.1348 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Monthly reset, charged | 132 | -0.0472 | 0.1217 | -0.505 | -0.5308 | -0.0776 | -2.1022 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 2015-06 to 2026-05 | Monthly reset, charged, 2.00% borrow | 132 | -0.0615 | 0.1217 | -0.6291 | -0.5702 | -0.0926 | -2.5083 |


The same caution on significance applies to any t here at or beyond 2. In the audit's tests, the free monthly reset is unremarkable against random portfolios; so is the charged series at 0.50% borrow (t -1.06 at 35.9% of random draws, 63.3% within sector), which differs from it by about 0.11 points of CAGR a year.


All charges in this view, averaged a year (share of NAV): [0.0045, 0.0045], against [0.0034, 0.0033] for the locked result, in the two windows above.


## Cost and borrow drag

| scope | CAGR_main | CAGR_no_costs | cost_drag_a_year | CAGR_no_fee | borrow_drag_a_year | CAGR_neither | stress_borrow_drag_a_year | total_cost_share_of_NAV | total_fee_share_of_NAV |
|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | -0.018 | -0.0146 | 0.0033 | -0.0126 | 0.0054 | -0.0092 | 0.0217 | 0.0699 | 0.11 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | -0.0359 | -0.0327 | 0.0032 | -0.0304 | 0.0055 | -0.0272 | 0.0219 | 0.0699 | 0.1131 |


Drag a year is the CAGR without that charge minus the CAGR with it, at the main settings. `total_..._share_of_NAV` sums each charge as a share of NAV.


## Short-leg contribution by year, main result

Each piece is its dollars over NAV at the start of that holding year, so they add to `return`.

| holding_year | months | return | long_leg | short_leg | cash_interest | borrow_fee | trading_cost | stress_return | long_only_High | Benchmark |
|---|---|---|---|---|---|---|---|---|---|---|
| 2005-06 | 12 | 0.1023 | 0.1966 | -0.1254 | 0.0386 | -0.0055 | -0.002 | 0.0856 | 0.1958 | 0.1656 |
| 2006-07 | 12 | 0.1378 | 0.2257 | -0.1299 | 0.0505 | -0.0051 | -0.0034 | 0.1221 | 0.2246 | 0.2202 |
| 2007-08 | 12 | 0.2277 | 0.0625 | 0.1392 | 0.0337 | -0.0045 | -0.0032 | 0.2142 | 0.0612 | -0.0002 |
| 2008-09 | 12 | 0.0893 | -0.293 | 0.3818 | 0.0075 | -0.0033 | -0.0037 | 0.0794 | -0.2953 | -0.3244 |
| 2009-10 | 12 | -0.165 | 0.2583 | -0.4145 | 0.0008 | -0.0062 | -0.0033 | -0.1837 | 0.2571 | 0.2907 |
| 2010-11 | 12 | 0.0332 | 0.378 | -0.3369 | 0.001 | -0.0055 | -0.0034 | 0.0165 | 0.377 | 0.3465 |
| 2011-12 | 12 | 0.0274 | -0.0365 | 0.072 | 0.0002 | -0.0048 | -0.0035 | 0.0131 | -0.0383 | -0.0495 |
| 2012-13 | 12 | 0.0325 | 0.2867 | -0.2459 | 0.0005 | -0.0054 | -0.0034 | 0.0163 | 0.2858 | 0.2902 |
| 2013-14 | 12 | -0.1315 | 0.2207 | -0.343 | 0.0 | -0.0057 | -0.0035 | -0.1487 | 0.2195 | 0.2461 |
| 2014-15 | 12 | -0.1511 | 0.1206 | -0.2627 | 0.0 | -0.0056 | -0.0034 | -0.1678 | 0.1192 | 0.1366 |
| 2015-16 | 12 | 0.0741 | -0.0044 | 0.0855 | 0.0008 | -0.0046 | -0.0032 | 0.0604 | -0.006 | -0.0094 |
| 2016-17 | 12 | 0.0105 | 0.1534 | -0.1379 | 0.0036 | -0.0054 | -0.0032 | -0.0059 | 0.1521 | 0.1871 |
| 2017-18 | 12 | -0.1724 | 0.1121 | -0.2876 | 0.0119 | -0.0056 | -0.0032 | -0.1894 | 0.1107 | 0.1615 |
| 2018-19 | 12 | -0.0186 | -0.0496 | 0.0179 | 0.0218 | -0.0051 | -0.0036 | -0.0341 | -0.0514 | 0.02 |
| 2019-20 | 12 | -0.2735 | 0.0803 | -0.3598 | 0.015 | -0.0055 | -0.0035 | -0.29 | 0.0788 | 0.1299 |
| 2020-21 | 12 | -0.3091 | 0.3543 | -0.6538 | 0.0007 | -0.0067 | -0.0036 | -0.3291 | 0.3532 | 0.4591 |
| 2021-22 | 12 | 0.0792 | -0.0034 | 0.0903 | 0.0004 | -0.005 | -0.003 | 0.0642 | -0.005 | -0.0498 |
| 2022-23 | 12 | -0.1136 | -0.0394 | -0.0971 | 0.0315 | -0.005 | -0.0037 | -0.1289 | -0.0412 | -0.0041 |
| 2023-24 | 12 | 0.1126 | 0.2335 | -0.1661 | 0.054 | -0.0055 | -0.0033 | 0.0957 | 0.2323 | 0.2017 |
| 2024-25 | 12 | 0.2919 | 0.1453 | 0.1075 | 0.0474 | -0.0048 | -0.0035 | 0.2772 | 0.1437 | 0.0932 |
| 2025 partial (7 of 12 months) | 7 | -0.0006 | 0.1134 | -0.1318 | 0.0241 | -0.0031 | -0.0032 | -0.0101 | 0.112 | 0.1037 |


## Year by year with the extension

| holding_year | months | return | long_leg | short_leg | cash_interest | borrow_fee | trading_cost | stress_return | long_only_High | Benchmark |
|---|---|---|---|---|---|---|---|---|---|---|
| 2024-25 | 12 | 0.2919 | 0.1453 | 0.1075 | 0.0474 | -0.0048 | -0.0035 | 0.2772 | 0.1437 | 0.0932 |
| 2025-26 | 12 | -0.3265 | 0.2839 | -0.6405 | 0.0392 | -0.0058 | -0.0032 | -0.3442 | 0.2828 | 0.2709 |


## Against the Spread column

Annual simple means. `Spread_column_net` is the published column: High's net return minus Low's net return. Low's cost makes Low's return lower, and subtracting it adds to the spread, so that column credits Low's cost instead of charging it. Here both legs pay.

| scope | Spread_column_net | Spread_gross | low_cost_credit_in_column | both_legs_charged | cost_treatment_effect | borrow_fee | NAV_return_minus_rf | size_and_net_exposure_effect | size_effect | net_exposure_effect | High_cost_a_year | Low_cost_a_year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | -0.0057 | -0.0058 | 0.0018 | -0.0092 | -0.0035 | -0.0053 | -0.0271 | -0.0125 | -0.006 | -0.0065 | 0.0016 | 0.0018 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | -0.0171 | -0.0172 | 0.0017 | -0.0206 | -0.0035 | -0.0054 | -0.0446 | -0.0187 | -0.0091 | -0.0096 | 0.0016 | 0.0017 |


`cost_treatment_effect` is `both_legs_charged` minus `Spread_column_net`, which is twice Low's cost. `size_and_net_exposure_effect` is the rest, and it comes from the annual reset: `size_effect` is the legs being larger than NAV, times the spread, and `net_exposure_effect` is the book being net short or long, times the legs' return above rf. They are mostly timing: average exposures are close to neutral, but the book is largest and most net short when Low runs ahead.


### The Spread, correctly charged

The published net Spread column credits Low's trading costs by about 0.35 points a year. It stays as published. With both legs charged:

| scope | series | mean_annual | alpha_annual | alpha_t |
|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | Published net Spread column (credits Low's costs) | -0.0057 | -0.0204 | -0.7238 |
| June 2005 to December 2025 (CRSP) | Spread with both legs charged | -0.0092 | -0.0239 | -0.8492 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Published net Spread column (credits Low's costs) | -0.0171 | -0.0283 | -1.0085 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Spread with both legs charged | -0.0206 | -0.0318 | -1.1335 |


## Monthly-reset sensitivity (reported only)

All monthly views, free and charged, beside the locked result.

| scope | series | CAGR | volatility | sharpe | max_drawdown | worst_year | alpha_annual | alpha_t |
|---|---|---|---|---|---|---|---|---|
| June 2005 to December 2025 (CRSP) | Annual reset (locked result) | -0.018 | 0.1227 | -0.2224 | -0.7579 | -0.3091 | -0.0453 | -1.4842 |
| June 2005 to December 2025 (CRSP) | Monthly reset, free | -0.0031 | 0.1041 | -0.1376 | -0.6704 | -0.2312 | -0.0289 | -1.0259 |
| June 2005 to December 2025 (CRSP) | Monthly reset, charged | -0.0042 | 0.1041 | -0.1483 | -0.6749 | -0.2326 | -0.03 | -1.0631 |
| June 2005 to December 2025 (CRSP) | Annual reset (locked result), 2.00% borrow | -0.0343 | 0.1242 | -0.3535 | -0.8066 | -0.3291 | -0.0618 | -1.9821 |
| June 2005 to December 2025 (CRSP) | Monthly reset, free, 2.00% borrow | -0.0179 | 0.1041 | -0.2833 | -0.7298 | -0.2429 | -0.0439 | -1.5581 |
| June 2005 to December 2025 (CRSP) | Monthly reset, charged, 2.00% borrow | -0.019 | 0.1041 | -0.294 | -0.7346 | -0.2443 | -0.045 | -1.5951 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Annual reset (locked result) | -0.0359 | 0.1311 | -0.3424 | -0.7579 | -0.3265 | -0.058 | -1.8639 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, free | -0.0144 | 0.1081 | -0.2381 | -0.6704 | -0.2312 | -0.0367 | -1.3114 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, charged | -0.0155 | 0.1081 | -0.2486 | -0.6749 | -0.2326 | -0.0378 | -1.3499 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Annual reset (locked result), 2.00% borrow | -0.0523 | 0.1328 | -0.4658 | -0.8066 | -0.3442 | -0.0749 | -2.3541 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, free, 2.00% borrow | -0.0291 | 0.1081 | -0.3779 | -0.7298 | -0.2429 | -0.0517 | -1.8468 |
| June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Monthly reset, charged, 2.00% borrow | -0.0302 | 0.1081 | -0.3885 | -0.7346 | -0.2443 | -0.0528 | -1.8851 |


## Thin dates (under 10 names in a leg): 0

None. High's smallest count is 43 and Low's is 20.


## Limits

- The borrow fee is one flat rate for every name and date. Low's stocks can be costly or impossible to borrow, especially in stress, and the 2.00% stress does not capture that fully.
- Dividends on shorted stock are inside Low's total return, so they are paid. No margin, recall or financing spread is modelled, and cash earns the full risk-free rate.
- Low is scores 0-4, broader than Piotroski's weak group, and traditional REITs are effectively excluded.
- The 2025 portfolio is partial in the main result. The extension's last five months use Compustat returns.
