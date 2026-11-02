> **Superseded.** This is the first specification (v1) of the Piotroski F-score test, kept for the record and unchanged apart from this note. The headline is now spec_v2: see `output/writeup.md`. 

# Checkpoint 3 results: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

## Checks

**0 check failure(s).** 247 months, 2005-06 to 2025-12. Factors available to 2026-09, cut to the last return month and joined on month.

**Significance at |t| = 2.** Full period: none. Subperiods: 2015-06 to 2025-12, one High alpha. Read it with the context below.

> High's alpha for June 2015 to December 2025 was -3.8% a year, t -4.10 with the pre-set 12 lags (-2.47 without adjustment; -3.06 with 4 lags). In simulations, 12 lags on 127 months overstate significance somewhat, implying a t nearer -3.4 to -4.0. Randomly chosen portfolios from the same universe also averaged -1.3%, and 19% of them reached |t| of 2 or more. The alpha falls in the lowest 1.5% of random selections, but the lowest 11% if the random selections keep High's sector mix. The full-period alpha is -0.8%, t -0.71, and 2005-15 has the opposite sign.


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


## Performance (returns are net of costs unless marked gross; RSP and SPY are fund returns)

| portfolio | basis | months | CAGR | volatility | sharpe | max_drawdown | avg_turnover_two_way | avg_turnover_one_way | avg_annual_cost |
|---|---|---|---|---|---|---|---|---|---|
| High | net | 247 | 0.1091 | 0.1679 | 0.6049 | -0.4436 | 1.6388 | 0.8194 | 0.0016 |
| Middle | net | 247 | 0.1126 | 0.1585 | 0.6505 | -0.4981 | 0.811 | 0.4055 | 0.0008 |
| Low | net | 247 | 0.1093 | 0.1985 | 0.539 | -0.6099 | 1.7579 | 0.879 | 0.0018 |
| Benchmark | net | 247 | 0.1135 | 0.1617 | 0.6458 | -0.4909 | 0.3413 | 0.1706 | 0.0003 |
| RSP | fund return | 247 | 0.0985 | 0.17 | 0.5423 | -0.5559 |  |  |  |
| SPY | fund return | 247 | 0.1088 | 0.149 | 0.66 | -0.508 |  |  |  |
| High | gross | 247 | 0.1109 | 0.1678 | 0.615 | -0.4426 |  |  |  |
| Middle | gross | 247 | 0.1135 | 0.1585 | 0.6559 | -0.4976 |  |  |  |
| Low | gross | 247 | 0.1113 | 0.1985 | 0.5479 | -0.6084 |  |  |  |
| Benchmark | gross | 247 | 0.1139 | 0.1617 | 0.6482 | -0.4907 |  |  |  |


Spread: -0.57% a year net, -0.58% gross, volatility 10.26%, largest drawdown -65.92%.


High beat the Benchmark in 10 of 20 complete holding years = 50%. 2025 partial (7 of 12 months): beat, shown separately.


## Versus the Benchmark

| portfolio | versus | excess_return_annual | cagr_difference | tracking_error | information_ratio | excess_t_newey_west |
|---|---|---|---|---|---|---|
| High | Benchmark | -0.0029 | -0.0044 | 0.0369 | -0.0795 | -0.34 |
| Middle | Benchmark | -0.0013 | -0.0009 | 0.013 | -0.1029 | -0.5786 |
| Low | Benchmark | 0.0027 | -0.0042 | 0.0828 | 0.033 | 0.1136 |
| High, gross | Benchmark_gross | -0.0017 | -0.003 | 0.0368 | -0.0456 | -0.1946 |
| RSP | Benchmark | -0.0122 | -0.0149 | 0.0376 | -0.3255 | -1.3845 |
| SPY | Benchmark | -0.0062 | -0.0046 | 0.0423 | -0.1467 | -0.6167 |


## Factor regressions (Mkt-RF, SMB, HML, RMW, CMA, MOM; Newey-West, 12 lags)

| series | basis | months | alpha_annual | alpha_t | r_squared | beta_Mkt-RF | t_Mkt-RF | beta_SMB | t_SMB | beta_HML | t_HML | beta_RMW | t_RMW | beta_CMA | t_CMA | beta_MOM | t_MOM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| High excess of risk-free | net | 247 | -0.008 | -0.715 | 0.913 | 1.022 | 42.205 | 0.184 | 4.34 | -0.052 | -0.787 | 0.192 | 3.409 | 0.041 | 0.392 | 0.001 | 0.029 |
| High excess of risk-free | gross | 247 | -0.006 | -0.563 | 0.914 | 1.021 | 42.281 | 0.188 | 4.414 | -0.054 | -0.832 | 0.193 | 3.424 | 0.041 | 0.391 | 0.001 | 0.04 |
| Spread (High minus Low) | net | 247 | -0.02 | -0.724 | 0.166 | -0.015 | -0.197 | -0.143 | -1.6 | 0.075 | 0.783 | 0.473 | 3.339 | 0.039 | 0.297 | 0.074 | 2.05 |
| Spread (High minus Low) | gross | 247 | -0.021 | -0.728 | 0.166 | -0.015 | -0.196 | -0.144 | -1.606 | 0.075 | 0.783 | 0.473 | 3.337 | 0.039 | 0.298 | 0.074 | 2.046 |
| High minus Benchmark (added) | net | 247 | -0.01 | -1.023 | 0.062 | 0.019 | 0.886 | 0.017 | 0.555 | 0.017 | 0.449 | 0.145 | 3.143 | -0.025 | -0.408 | 0.011 | 0.82 |
| Low excess of risk-free (added) | net | 247 | 0.013 | 0.548 | 0.822 | 1.037 | 14.556 | 0.327 | 4.541 | -0.126 | -1.408 | -0.281 | -2.181 | 0.003 | 0.028 | -0.073 | -2.227 |
| Benchmark excess of risk-free (added) | net | 247 | 0.002 | 0.255 | 0.962 | 1.003 | 53.541 | 0.167 | 6.983 | -0.069 | -1.559 | 0.047 | 1.361 | 0.066 | 1.1 | -0.011 | -0.449 |


The rows marked (added) go beyond the brief, for context.


## Returns by individual score (gross, complete years)

| F_SCORE | avg_annual_return | complete_years | avg_names | partial_2025_return | under_minimum_names |
|---|---|---|---|---|---|
| 0 |  | 1 | 1.0 |  | True |
| 1 | 0.0381 | 6 | 1.6667 |  | True |
| 2 | 0.1968 | 14 | 2.5714 |  | True |
| 3 | 0.1439 | 20 | 7.75 |  | True |
| 4 | 0.136 | 20 | 24.65 | 0.1512 | False |
| 5 | 0.126 | 20 | 67.85 | 0.1547 | False |
| 6 | 0.1175 | 20 | 94.25 | 0.1196 | False |
| 7 | 0.1334 | 20 | 89.65 | 0.0476 | False |
| 8 | 0.1203 | 20 | 59.75 | 0.0961 | False |
| 9 | 0.1363 | 20 | 14.1 | 0.1871 | False |


Rank correlation of score with average return: -0.32, across 10 scores. **Treat this with caution:** it includes scores [0, 1, 2, 3], which average under 10 names, and score 0 has a single name in a single year. It is +0.14 across the 6 scores with enough names, and neither figure is a test of significance.


## Year by year (net)

| holding_year | months | High_names | Low_names | High | Low | Spread | Benchmark | High_minus_Benchmark | High_beats_Benchmark |
|---|---|---|---|---|---|---|---|---|---|
| 2005-06 | 12 | 96 | 20 | 0.1958 | 0.1245 | 0.0713 | 0.1656 | 0.0303 | True |
| 2006-07 | 12 | 92 | 22 | 0.2246 | 0.1282 | 0.0964 | 0.2202 | 0.0044 | True |
| 2007-08 | 12 | 79 | 23 | 0.0612 | -0.1413 | 0.2024 | -0.0002 | 0.0613 | True |
| 2008-09 | 12 | 68 | 31 | -0.2953 | -0.3844 | 0.0892 | -0.3244 | 0.0291 | True |
| 2009-10 | 12 | 62 | 49 | 0.2571 | 0.4135 | -0.1564 | 0.2907 | -0.0336 | False |
| 2010-11 | 12 | 74 | 41 | 0.377 | 0.3357 | 0.0413 | 0.3465 | 0.0305 | True |
| 2011-12 | 12 | 127 | 21 | -0.0383 | -0.0739 | 0.0356 | -0.0495 | 0.0112 | True |
| 2012-13 | 12 | 88 | 20 | 0.2858 | 0.2444 | 0.0414 | 0.2902 | -0.0045 | False |
| 2013-14 | 12 | 52 | 39 | 0.2195 | 0.3417 | -0.1223 | 0.2461 | -0.0267 | False |
| 2014-15 | 12 | 69 | 23 | 0.1192 | 0.2613 | -0.1421 | 0.1366 | -0.0174 | False |
| 2015-16 | 12 | 71 | 38 | -0.006 | -0.0872 | 0.0812 | -0.0094 | 0.0034 | True |
| 2016-17 | 12 | 43 | 57 | 0.1521 | 0.1365 | 0.0156 | 0.1871 | -0.035 | False |
| 2017-18 | 12 | 73 | 31 | 0.1107 | 0.2864 | -0.1757 | 0.1615 | -0.0508 | False |
| 2018-19 | 12 | 80 | 21 | -0.0514 | -0.0198 | -0.0317 | 0.02 | -0.0715 | False |
| 2019-20 | 12 | 62 | 20 | 0.0788 | 0.3585 | -0.2796 | 0.1299 | -0.051 | False |
| 2020-21 | 12 | 52 | 53 | 0.3532 | 0.6531 | -0.3 | 0.4591 | -0.1059 | False |
| 2021-22 | 12 | 51 | 71 | -0.005 | -0.0918 | 0.0868 | -0.0498 | 0.0448 | True |
| 2022-23 | 12 | 101 | 28 | -0.0412 | 0.0954 | -0.1366 | -0.0041 | -0.0371 | False |
| 2023-24 | 12 | 52 | 50 | 0.2323 | 0.1647 | 0.0676 | 0.2017 | 0.0306 | True |
| 2024-25 | 12 | 85 | 37 | 0.1437 | -0.1094 | 0.2531 | 0.0932 | 0.0506 | True |
| 2025 partial (7 of 12 months) | 7 | 76 | 33 | 0.112 | 0.1304 | -0.0184 | 0.1037 | 0.0083 | True |


## Subperiods (net)

| period | months | High_CAGR | Low_CAGR | Benchmark_CAGR | High_sharpe | Benchmark_sharpe | High_excess_annual | information_ratio | Spread_annual | High_alpha_annual | High_alpha_t | Spread_alpha_annual | Spread_alpha_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2005-06 to 2015-05 | 120 | 0.123 | 0.095 | 0.112 | 0.711 | 0.658 | 0.01 | 0.305 | 0.021 | 0.025 | 1.764 | 0.021 | 0.511 |
| 2015-06 to 2025-12 | 127 | 0.096 | 0.123 | 0.115 | 0.506 | 0.632 | -0.015 | -0.386 | -0.031 | -0.038 | -4.104 | -0.057 | -1.489 |


Subperiods with an alpha at or beyond |t| = 2: 2015-06 to 2025-12. High's alpha for June 2015 to December 2025 was -3.8% a year, t -4.10 with the pre-set 12 lags (-2.47 without adjustment; -3.06 with 4 lags). In simulations, 12 lags on 127 months overstate significance somewhat, implying a t nearer -3.4 to -4.0. Randomly chosen portfolios from the same universe also averaged -1.3%, and 19% of them reached |t| of 2 or more. The alpha falls in the lowest 1.5% of random selections, but the lowest 11% if the random selections keep High's sector mix. The full-period alpha is -0.8%, t -0.71, and 2005-15 has the opposite sign.
