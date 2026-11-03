# Number check (net): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

75 numbers recomputed with numpy/scipy only; **0 differ**.

| check | recomputed | in the tables | ok |
|---|---|---|---|
| High_CAGR | 0.10621885 | 0.10621885 | yes |
| High_volatility | 0.16931235 | 0.16931235 | yes |
| High_sharpe | 0.5856478 | 0.5856478 | yes |
| High_max_drawdown | -0.45614058 | -0.45614058 | yes |
| Middle_CAGR | 0.11409722 | 0.11409722 | yes |
| Middle_volatility | 0.15854021 | 0.15854021 | yes |
| Middle_sharpe | 0.65931959 | 0.65931959 | yes |
| Middle_max_drawdown | -0.48937338 | -0.48937338 | yes |
| Low_CAGR | 0.10321542 | 0.10321542 | yes |
| Low_volatility | 0.19226786 | 0.19226786 | yes |
| Low_sharpe | 0.52190403 | 0.52190403 | yes |
| Low_max_drawdown | -0.56580206 | -0.56580206 | yes |
| Benchmark_CAGR | 0.10788998 | 0.10788998 | yes |
| Benchmark_volatility | 0.16261501 | 0.16261501 | yes |
| Benchmark_sharpe | 0.61214657 | 0.61214657 | yes |
| Benchmark_max_drawdown | -0.50644278 | -0.50644278 | yes |
| BenchmarkScored_CAGR | 0.1135325 | 0.1135325 | yes |
| BenchmarkScored_volatility | 0.16162202 | 0.16162202 | yes |
| BenchmarkScored_sharpe | 0.64640253 | 0.64640253 | yes |
| BenchmarkScored_max_drawdown | -0.49032759 | -0.49032759 | yes |
| full | raw excess vs primary benchmark (all included) | estimate | -0.00041209009 | -0.00041209009 | yes |
| full | raw excess vs primary benchmark (all included) | se | 0.0075983729 | 0.0075983729 | yes |
| full | raw excess vs primary benchmark (all included) | t | -0.054233991 | -0.054233991 | yes |
| full | raw excess vs primary benchmark (all included) | p | 0.95679276 | 0.95679276 | yes |
| full | raw excess vs primary benchmark (all included) | mde | 0.02137224 | 0.02137224 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | -0.0027984706 | -0.0027984706 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.01131184 | 0.01131184 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | -0.24739305 | -0.24739305 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.80481382 | 0.80481382 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.031819349 | 0.031819349 | yes |
| full | raw excess vs primary benchmark (all included) | lag6_t | -0.059325648 | -0.059325648 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | -0.26597412 | -0.26597412 | yes |
| full | raw excess vs primary benchmark (all included) | lag_corr_t | -0.054124094 | -0.054124094 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | -0.24487627 | -0.24487627 | yes |
| full | raw excess | lag12 t | -0.060797515 | -0.060797515 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | estimate | 0.0085305737 | 0.0085305737 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | se | 0.010143287 | 0.010143287 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | t | 0.84100685 | 0.84100685 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | p | 0.40203085 | 0.40203085 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | mde | 0.02865227 | 0.02865227 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | 0.020117008 | 0.020117008 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.014499309 | 0.014499309 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | 1.387446 | 1.387446 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.16798862 | 0.16798862 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.040968748 | 0.040968748 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag6_t | 0.9519967 | 0.9519967 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | 1.4995247 | 1.4995247 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag_corr_t | 0.83749532 | 0.83749532 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | 1.3582333 | 1.3582333 | yes |
| 2005-06 to 2015-05 | raw excess | lag12 t | 1.0401577 | 1.0401577 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | estimate | -0.0088618511 | -0.0088618511 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | se | 0.010939014 | 0.010939014 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | t | -0.81011427 | -0.81011427 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | p | 0.41940188 | 0.41940188 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | mde | 0.030885801 | 0.030885801 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | -0.033552665 | -0.033552665 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.012567026 | 0.012567026 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | -2.6698969 | -2.6698969 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.0086211646 | 0.0086211646 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.03549151 | 0.03549151 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag6_t | -0.88267707 | -0.88267707 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | -2.9047028 | -2.9047028 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag_corr_t | -0.80691854 | -0.80691854 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | -2.6168122 | -2.6168122 | yes |
| 2015-06 to 2025-12 | raw excess | lag12 t | -0.91013183 | -0.91013183 | yes |
| Holm | full | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 1 | 1 | yes |
| Holm | 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 0.83994309 | 0.83994309 | yes |
| Holm | 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 0.051726987 | 0.051726987 | yes |
| hac_lags_full | 4 | 4 | yes |
| hit_rate_complete_years_primary | 0.45 | 0.45 | yes |
| complete_years | 20 | 20 | yes |
| report prints every headline value to 4 places | 1 | 1 | yes |
