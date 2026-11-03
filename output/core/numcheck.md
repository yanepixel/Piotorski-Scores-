# Number check (literal): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

75 numbers recomputed with numpy/scipy only; **0 differ**.

| check | recomputed | in the tables | ok |
|---|---|---|---|
| High_CAGR | 0.12002545 | 0.12002545 | yes |
| High_volatility | 0.18146074 | 0.18146074 | yes |
| High_sharpe | 0.62746896 | 0.62746896 | yes |
| High_max_drawdown | -0.45944517 | -0.45944517 | yes |
| Middle_CAGR | 0.11152457 | 0.11152457 | yes |
| Middle_volatility | 0.15871486 | 0.15871486 | yes |
| Middle_sharpe | 0.64403967 | 0.64403967 | yes |
| Middle_max_drawdown | -0.48739202 | -0.48739202 | yes |
| Low_CAGR | 0.10835502 | 0.10835502 | yes |
| Low_volatility | 0.17046067 | 0.17046067 | yes |
| Low_sharpe | 0.59340544 | 0.59340544 | yes |
| Low_max_drawdown | -0.52298877 | -0.52298877 | yes |
| Benchmark_CAGR | 0.10788998 | 0.10788998 | yes |
| Benchmark_volatility | 0.16261501 | 0.16261501 | yes |
| Benchmark_sharpe | 0.61214657 | 0.61214657 | yes |
| Benchmark_max_drawdown | -0.50644278 | -0.50644278 | yes |
| BenchmarkScored_CAGR | 0.11355698 | 0.11355698 | yes |
| BenchmarkScored_volatility | 0.16166009 | 0.16166009 | yes |
| BenchmarkScored_sharpe | 0.64644348 | 0.64644348 | yes |
| BenchmarkScored_max_drawdown | -0.49175061 | -0.49175061 | yes |
| full | raw excess vs primary benchmark (all included) | estimate | 0.014207734 | 0.014207734 | yes |
| full | raw excess vs primary benchmark (all included) | se | 0.013776782 | 0.013776782 | yes |
| full | raw excess vs primary benchmark (all included) | t | 1.031281 | 1.031281 | yes |
| full | raw excess vs primary benchmark (all included) | p | 0.3034219 | 0.3034219 | yes |
| full | raw excess vs primary benchmark (all included) | mde | 0.038750492 | 0.038750492 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | 0.0099474865 | 0.0099474865 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.014172488 | 0.014172488 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | 0.7018871 | 0.7018871 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.48342405 | 0.48342405 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.039866134 | 0.039866134 | yes |
| full | raw excess vs primary benchmark (all included) | lag6_t | 1.0758699 | 1.0758699 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | 0.75118699 | 0.75118699 | yes |
| full | raw excess vs primary benchmark (all included) | lag_corr_t | 1.0291913 | 1.0291913 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | 0.69474666 | 0.69474666 | yes |
| full | raw excess | lag12 t | 1.0962864 | 1.0962864 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | estimate | 0.025010887 | 0.025010887 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | se | 0.017062843 | 0.017062843 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | t | 1.4658101 | 1.4658101 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | p | 0.14533743 | 0.14533743 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | mde | 0.048198301 | 0.048198301 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | 0.029323481 | 0.029323481 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.020310409 | 0.020310409 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | 1.4437662 | 1.4437662 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.15152351 | 0.15152351 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.057388392 | 0.057388392 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag6_t | 1.6443928 | 1.6443928 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | 1.5372009 | 1.5372009 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag_corr_t | 1.4596897 | 1.4596897 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | 1.4133677 | 1.4133677 | yes |
| 2005-06 to 2015-05 | raw excess | lag12 t | 1.9339862 | 1.9339862 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | estimate | 0.0040000299 | 0.0040000299 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | se | 0.020794506 | 0.020794506 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | t | 0.19235994 | 0.19235994 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | p | 0.84776996 | 0.84776996 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | mde | 0.058712328 | 0.058712328 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | -0.014118995 | -0.014118995 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.018199088 | 0.018199088 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | -0.7758078 | -0.7758078 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.4393638 | 0.4393638 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.051397452 | 0.051397452 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag6_t | 0.1963652 | 0.1963652 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | -0.82518013 | -0.82518013 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag_corr_t | 0.19160112 | 0.19160112 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | -0.76038264 | -0.76038264 | yes |
| 2015-06 to 2025-12 | raw excess | lag12 t | 0.19126713 | 0.19126713 | yes |
| Holm | full | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 1 | 1 | yes |
| Holm | 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | 0.87202455 | 0.87202455 | yes |
| Holm | 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 0.87202455 | 0.87202455 | yes |
| Holm | 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 1 | 1 | yes |
| hac_lags_full | 4 | 4 | yes |
| hit_rate_complete_years_primary | 0.5 | 0.5 | yes |
| complete_years | 20 | 20 | yes |
| report prints every headline value to 4 places | 1 | 1 | yes |
