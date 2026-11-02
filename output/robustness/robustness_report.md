# Robustness: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

One setting changes in each row. All figures are net of costs, June 2005 to December 2025; the 2025 portfolio is partial (7 of 12 months). The headline stays the headline whatever these show. The variant definitions were set after headline returns existed. Earlier variant runs, whose results by the coordinator's record reached no one but their authors, existed before two later rules were settled: the Comverse hold-flat rule and the instruction to use the quantile boundary for version B.

## Terms

- **F-score:** a 0-9 count of financial-health tests a company passes, from its latest annual report.
- **Net / gross:** after / before trading costs (10 bps, or 0.10%, on each dollar traded at each rebalance).
- **Benchmark:** every scored company in the universe, equally weighted, run the same way and charged the same costs.
- **CAGR:** the constant yearly growth rate that gives the same end value.
- **Volatility:** how much monthly returns swing, stated per year.
- **Sharpe ratio:** return above the risk-free rate per unit of volatility. Higher is better.
- **Max drawdown:** the largest peak-to-trough fall.
- **Turnover:** the share of the portfolio traded at a rebalance. Two-way counts buys and sells; one-way is half that.
- **Excess return:** return above the benchmark, here the average monthly gap times 12.
- **Tracking error:** how much the return gap to the benchmark swings, per year.
- **Information ratio:** excess return divided by tracking error.
- **Factor:** a broad return pattern. Mkt-RF is the market above cash, SMB small vs large companies, HML cheap vs expensive, RMW profitable vs unprofitable, CMA low vs high asset growth, MOM recent winners vs losers.
- **Alpha:** return left after accounting for those factors, stated per year.
- **t-stat:** how many standard errors a number is from zero. Beyond 2 in either direction is treated as significant here.
- **Newey-West:** standard errors adjusted for returns that are correlated over time, here over 12 months.
- **Spread:** High minus Low. A diagnostic only, with no shorting costs.
- **Variant:** a rerun with one setting changed.

Results reported: 9 of 9 variants. Stopped: none. Not run: none.

## Comparison

| variant | High_alpha_annual | High_alpha_t | High_minus_Benchmark_annual | High_sharpe | Benchmark_sharpe | High_CAGR | Benchmark_CAGR | Spread_alpha_annual | Spread_alpha_t |
|---|---|---|---|---|---|---|---|---|---|
| headline | -0.0078 | -0.7146 | -0.0029 | 0.6049 | 0.6458 | 0.1091 | 0.1135 | -0.0204 | -0.7238 |
| high_cutoff_7plus | -0.0022 | -0.2972 | 0.0009 | 0.6514 | 0.6458 | 0.1145 | 0.1135 | -0.0148 | -0.6001 |
| value_filter_B | -0.0111 | -0.5861 | -0.0 | 0.4986 | 0.551 | 0.0996 | 0.1035 | -0.0203 | -0.5262 |
| cap_weighted | -0.0078 | -0.5378 | -0.0099 | 0.6325 | 0.7788 | 0.1123 | 0.1264 | -0.0403 | -1.3593 |
| sector_neutral | -0.0048 | -0.5501 | -0.0018 | 0.6112 | 0.6458 | 0.1103 | 0.1135 | -0.0153 | -0.7061 |
| lag_90_days | -0.0078 | -0.7146 | -0.0029 | 0.6049 | 0.6458 | 0.1091 | 0.1135 | -0.0204 | -0.7238 |
| cost_25bps | -0.0102 | -0.9426 | -0.0048 | 0.5897 | 0.6422 | 0.1064 | 0.1128 | -0.0202 | -0.7168 |
| eight_signal_no_liquidity | -0.0097 | -0.9029 | -0.0011 | 0.5936 | 0.619 | 0.107 | 0.1091 | -0.0187 | -0.6793 |
| universe_buffer | -0.0072 | -0.6428 | -0.0033 | 0.6072 | 0.6482 | 0.1093 | 0.114 | -0.0149 | -0.5622 |
| profitability_screen | -0.0078 | -0.701 | -0.0003 | 0.6099 | 0.6491 | 0.1091 | 0.1112 | -0.0087 | -0.3243 |


## Names per bucket

| variant | High_names_median | High_names_min | High_dates_under_minimum | Middle_names_median | Low_names_median | Low_names_min | Low_dates_under_minimum | Benchmark_names_median | Benchmark_names_min |
|---|---|---|---|---|---|---|---|---|---|
| headline | 73.0 | 43 | 0 | 255.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| high_cutoff_7plus | 170.0 | 113 | 0 | 167.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| value_filter_B | 23.0 | 8 | 1 | 85.0 | 13.0 | 4 | 8 | 122.0 | 106 |
| cap_weighted | 73.0 | 43 | 0 | 255.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| sector_neutral | 73.0 | 43 | 0 | 255.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| lag_90_days | 73.0 | 43 | 0 | 255.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| cost_25bps | 73.0 | 43 | 0 | 255.0 | 31.0 | 20 | 0 | 365.0 | 318 |
| eight_signal_no_liquidity | 73.0 | 46 | 0 | 283.0 | 32.0 | 20 | 0 | 395.0 | 351 |
| universe_buffer | 68.0 | 42 | 0 | 253.0 | 32.0 | 20 | 0 | 359.0 | 318 |
| profitability_screen | 70.0 | 43 | 0 | 226.0 | 18.0 | 8 | 2 | 316.0 | 283 |


Buckets under 10 names are flagged. Thin buckets make Low and the spread noisy. Every case is in `thin_buckets.csv`: 11 bucket-dates, {'profitability_screen': 2, 'value_filter_B': 9}.


## Subperiods

| variant | period | months | High_alpha_annual | High_alpha_t | High_minus_Benchmark_annual | High_sharpe | Benchmark_sharpe | Spread_alpha_annual | Spread_alpha_t |
|---|---|---|---|---|---|---|---|---|---|
| headline | 2005-06 to 2015-05 | 120 | 0.025 | 1.764 | 0.01 | 0.711 | 0.658 | 0.021 | 0.511 |
| headline | 2015-06 to 2025-12 | 127 | -0.038 | -4.104 | -0.015 | 0.506 | 0.632 | -0.057 | -1.489 |
| high_cutoff_7plus | 2005-06 to 2015-05 | 120 | 0.017 | 1.889 | 0.002 | 0.674 | 0.658 | 0.013 | 0.39 |
| high_cutoff_7plus | 2015-06 to 2025-12 | 127 | -0.021 | -2.611 | -0.0 | 0.628 | 0.632 | -0.04 | -1.078 |
| value_filter_B | 2005-06 to 2015-05 | 120 | 0.032 | 1.369 | 0.019 | 0.72 | 0.653 | 0.011 | 0.239 |
| value_filter_B | 2015-06 to 2025-12 | 127 | -0.055 | -2.912 | -0.018 | 0.31 | 0.454 | -0.059 | -1.007 |
| cap_weighted | 2005-06 to 2015-05 | 120 | -0.001 | -0.067 | -0.009 | 0.554 | 0.686 | -0.015 | -0.364 |
| cap_weighted | 2015-06 to 2025-12 | 127 | -0.017 | -0.872 | -0.01 | 0.698 | 0.857 | -0.07 | -2.034 |
| sector_neutral | 2005-06 to 2015-05 | 120 | 0.017 | 1.513 | 0.006 | 0.674 | 0.658 | -0.005 | -0.138 |
| sector_neutral | 2015-06 to 2025-12 | 127 | -0.029 | -3.359 | -0.009 | 0.55 | 0.632 | -0.031 | -1.033 |
| lag_90_days | 2005-06 to 2015-05 | 120 | 0.025 | 1.764 | 0.01 | 0.711 | 0.658 | 0.021 | 0.511 |
| lag_90_days | 2015-06 to 2025-12 | 127 | -0.038 | -4.104 | -0.015 | 0.506 | 0.632 | -0.057 | -1.489 |
| cost_25bps | 2005-06 to 2015-05 | 120 | 0.022 | 1.574 | 0.009 | 0.695 | 0.654 | 0.021 | 0.519 |
| cost_25bps | 2015-06 to 2025-12 | 127 | -0.041 | -4.449 | -0.017 | 0.491 | 0.629 | -0.057 | -1.487 |
| eight_signal_no_liquidity | 2005-06 to 2015-05 | 120 | 0.023 | 1.676 | 0.012 | 0.701 | 0.624 | 0.026 | 0.67 |
| eight_signal_no_liquidity | 2015-06 to 2025-12 | 127 | -0.04 | -4.33 | -0.014 | 0.494 | 0.611 | -0.058 | -1.567 |
| universe_buffer | 2005-06 to 2015-05 | 120 | 0.024 | 1.557 | 0.008 | 0.709 | 0.667 | 0.023 | 0.654 |
| universe_buffer | 2015-06 to 2025-12 | 127 | -0.036 | -3.413 | -0.014 | 0.513 | 0.627 | -0.052 | -1.397 |
| profitability_screen | 2005-06 to 2015-05 | 120 | 0.027 | 1.935 | 0.013 | 0.731 | 0.668 | 0.032 | 0.883 |
| profitability_screen | 2015-06 to 2025-12 | 127 | -0.04 | -4.174 | -0.013 | 0.498 | 0.629 | -0.044 | -1.28 |


## Rows and companies

| variant | held_rows | unique_companies | unique_gvkeys | first_formation | last_formation | first_month | last_month | months | included_rows | rows_dropped | drop_reason | mid_period_exits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| headline | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| high_cutoff_7plus | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| value_filter_B | 2530 | 435 | 433 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 5884 | no valid score, or outside the cheapest third, or not USD | 73 |
| cap_weighted | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| sector_neutral | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| lag_90_days | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| cost_25bps | 7571 | 852 | 843 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 843 | no score known by the date, or score too old | 179 |
| eight_signal_no_liquidity | 8212 | 914 | 903 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 202 | no score known by the date, or score too old | 186 |
| universe_buffer | 7469 | 776 | 766 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8267 | 798 | no score known by the date, or score too old | 168 |
| profitability_screen | 6582 | 787 | 779 | 2005-05-31 | 2025-05-30 | 2005-06 | 2025-12 | 247 | 8414 | 1832 | no valid score, or failed or unconfirmed on the profitability screen | 151 |


Also in `output/logs/robustness_log.csv`.


## What each variant changed

- **headline**: None. Same numbers as the published headline; files here are a copy for comparison. Mid-period exits: 179.
- **high_cutoff_7plus**: High = scores [7, 8, 9]; Middle = 5-6.  Mid-period exits: 179.
- **value_filter_B**: Only the cheapest third by book-to-market (USD rows). The closest variant to Piotroski's sample, which studied cheap stocks. Mid-period exits: 73.
- **cap_weighted**: Weights by formation market cap, then drift, in every bucket and the benchmark.  Mid-period exits: 179.
- **sector_neutral**: Each bucket holds the benchmark's sector weights, equal weight within sector.  Mid-period exits: 179.
- **lag_90_days**: Fallback availability = year-end + 90 days, not 120. Rows that differ from the headline: 0. Mid-period exits: 179.
- **cost_25bps**: 25 bps a side, not 10.  Mid-period exits: 179.
- **eight_signal_no_liquidity**: Firms with no liquidity signal scored out of 8 (High 8, Low 0-3, Middle 4-7); the benchmark gains those firms. 641 list rows use 8 signals: {'Middle': 578, 'Low': 32, 'High': 31}. Set after headline returns. Null return rule `hold_flat` for General Growth Properties, May 2009. Held flat: [{'formation_date': datetime.date(2008, 5, 30), 'permno': np.int64(79129), 'month': '2009-05', 'treatment': 'held flat: no return, not an exit'}]. Mid-period exits: 186.
- **universe_buffer**: Enter at rank <= 450, stay until rank > 550; first list is the top 500. List size 481-501 before exclusions; scored names 318-377. Null return rule `hold_flat` for Comverse Technology, February to May 2007: held flat, not an exit, and sold at its last value at the 2007 rebalance. Held flat: [{'formation_date': datetime.date(2006, 5, 31), 'permno': np.int64(10942), 'month': '2007-02', 'treatment': 'held flat: no return, not an exit'}, {'formation_date': datetime.date(2006, 5, 31), 'permno': np.int64(10942), 'month': '2007-03', 'treatment': 'held flat: no return, not an exit'}, {'formation_date': datetime.date(2006, 5, 31), 'permno': np.int64(10942), 'month': '2007-04', 'treatment': 'held flat: no return, not an exit'}, {'formation_date': datetime.date(2006, 5, 31), 'permno': np.int64(10942), 'month': '2007-05', 'treatment': 'held flat: no return, not an exit'}]. Mid-period exits: 168.
- **profitability_screen**: Require positive trailing-four-quarter and latest-quarter earnings, on every bucket and the benchmark; it overlaps with F_ROA. Headline rows 7571: {'pass': 6582, 'failed: earnings not positive': 973, 'unconfirmed: null earnings': 14, 'unconfirmed: quarters not consecutive': 2}. Unconfirmed rows count as failed and are a disclosure. Mid-period exits: 151.