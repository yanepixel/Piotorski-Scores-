# spec_v2 number check (net): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

75 numbers recomputed with numpy/scipy only; **0 differ**.

| check | recomputed | in the tables | ok |
|---|---|---|---|
| High_CAGR | 0.10745673 | 0.10745673 | yes |
| High_volatility | 0.16955505 | 0.16955505 | yes |
| High_sharpe | 0.59168329 | 0.59168329 | yes |
| High_max_drawdown | -0.45715361 | -0.45715361 | yes |
| Middle_CAGR | 0.11411943 | 0.11411943 | yes |
| Middle_volatility | 0.15881496 | 0.15881496 | yes |
| Middle_sharpe | 0.6586396 | 0.6586396 | yes |
| Middle_max_drawdown | -0.49080422 | -0.49080422 | yes |
| Low_CAGR | 0.10191228 | 0.10191228 | yes |
| Low_volatility | 0.18886991 | 0.18886991 | yes |
| Low_sharpe | 0.5213018 | 0.5213018 | yes |
| Low_max_drawdown | -0.56865101 | -0.56865101 | yes |
| Benchmark_CAGR | 0.10788998 | 0.10788998 | yes |
| Benchmark_volatility | 0.16261501 | 0.16261501 | yes |
| Benchmark_sharpe | 0.61214657 | 0.61214657 | yes |
| Benchmark_max_drawdown | -0.50644278 | -0.50644278 | yes |
| BenchmarkScored_CAGR | 0.11355698 | 0.11355698 | yes |
| BenchmarkScored_volatility | 0.16166009 | 0.16166009 | yes |
| BenchmarkScored_sharpe | 0.64644348 | 0.64644348 | yes |
| BenchmarkScored_max_drawdown | -0.49175061 | -0.49175061 | yes |
| full | raw excess vs primary benchmark (all included) | estimate | 0.0007533552 | 0.0007533552 | yes |
| full | raw excess vs primary benchmark (all included) | se | 0.0075756141 | 0.0075756141 | yes |
| full | raw excess vs primary benchmark (all included) | t | 0.099444769 | 0.099444769 | yes |
| full | raw excess vs primary benchmark (all included) | p | 0.92086613 | 0.92086613 | yes |
| full | raw excess vs primary benchmark (all included) | mde | 0.021308225 | 0.021308225 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | -0.0014835246 | -0.0014835246 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.011353448 | 0.011353448 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | -0.13066731 | -0.13066731 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.89614705 | 0.89614705 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.031936389 | 0.031936389 | yes |
| full | raw excess vs primary benchmark (all included) | lag6_t | 0.10879811 | 0.10879811 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | -0.14014095 | -0.14014095 | yes |
| full | raw excess vs primary benchmark (all included) | lag_corr_t | 0.09924326 | 0.09924326 | yes |
| full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | -0.12933801 | -0.12933801 | yes |
| full | raw excess | lag12 t | 0.11077643 | 0.11077643 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | estimate | 0.011319903 | 0.011319903 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | se | 0.0099904368 | 0.0099904368 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | t | 1.1330739 | 1.1330739 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | p | 0.25946093 | 0.25946093 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | mde | 0.028220507 | 0.028220507 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | 0.022758681 | 0.022758681 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.014577021 | 0.014577021 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | 1.5612711 | 1.5612711 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.12120758 | 0.12120758 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.041188328 | 0.041188328 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag6_t | 1.2994912 | 1.2994912 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | 1.6762222 | 1.6762222 | yes |
| 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | lag_corr_t | 1.1283429 | 1.1283429 | yes |
| 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | 1.5283985 | 1.5283985 | yes |
| 2005-06 to 2015-05 | raw excess | lag12 t | 1.4038769 | 1.4038769 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | estimate | -0.0092307848 | -0.0092307848 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | se | 0.010899623 | 0.010899623 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | t | -0.84689027 | -0.84689027 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | p | 0.39866196 | 0.39866196 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | mde | 0.030774583 | 0.030774583 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | estimate | -0.033810181 | -0.033810181 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | se | 0.012505721 | 0.012505721 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | t | -2.7035771 | -2.7035771 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | p | 0.0078391932 | 0.0078391932 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | mde | 0.035318372 | 0.035318372 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag6_t | -0.92079778 | -0.92079778 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag6_t | -2.9379586 | -2.9379586 | yes |
| 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | lag_corr_t | -0.84354947 | -0.84354947 | yes |
| 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | lag_corr_t | -2.6498227 | -2.6498227 | yes |
| 2015-06 to 2025-12 | raw excess | lag12 t | -0.95799803 | -0.95799803 | yes |
| Holm | full | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | full | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 1 | 1 | yes |
| Holm | 2005-06 to 2015-05 | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | 2005-06 to 2015-05 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 0.60603792 | 0.60603792 | yes |
| Holm | 2015-06 to 2025-12 | raw excess vs primary benchmark (all included) | 1 | 1 | yes |
| Holm | 2015-06 to 2025-12 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 0.047035159 | 0.047035159 | yes |
| hac_lags_full | 4 | 4 | yes |
| hit_rate_complete_years_primary | 0.45 | 0.45 | yes |
| complete_years | 20 | 20 | yes |
| report prints every v2 headline value to 4 places | 1 | 1 | yes |
