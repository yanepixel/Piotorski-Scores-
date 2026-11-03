# Results, literal issuance rule (primary): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**0 check failure(s).** 247 months, 2005-06 to 2025-12; last portfolio partial (7 of 12 months). Returns are net of costs; RSP and SPY are fund returns. Primary benchmark = every included name, equal weight, charged like the buckets; BenchmarkScored = scored names only (the like-for-like benchmark).


**Coverage.** 8414 included list rows from 930 unique companies on 21 formation dates (2005-05-31 to 2025-05-30); 7614 scored list rows from 857 unique companies. Unique companies by bucket: High 356, Middle 807, Low 577. Monthly returns 2005-06 to 2025-12 (247 months). No rows are dropped by this script.

## Headline

| portfolio | months | CAGR | volatility | sharpe | max_drawdown | avg_turnover_two_way |
|---|---|---|---|---|---|---|
| High | 247 | 0.12 | 0.1815 | 0.6275 | -0.4594 | 1.8001 |
| Middle | 247 | 0.1115 | 0.1587 | 0.644 | -0.4874 | 0.7968 |
| Low | 247 | 0.1084 | 0.1705 | 0.5934 | -0.523 | 1.6025 |
| Benchmark | 247 | 0.1079 | 0.1626 | 0.6121 | -0.5064 | 0.3318 |
| BenchmarkScored | 247 | 0.1136 | 0.1617 | 0.6464 | -0.4918 | 0.3422 |
| RSP | 247 | 0.0985 | 0.17 | 0.5423 | -0.5559 |  |
| SPY | 247 | 0.1088 | 0.149 | 0.66 | -0.508 |  |

## Primary tests, High, full period (Newey-West, automatic lag 4; t distribution, T - k df; annualised)

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0292 | 0.3044 | 1.0759 | 0.283 | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0142 | 0.0138 | 1.0313 | 0.3034 | 246 | 0.0388 | 1.0963 | 0.274 | 1.0 | 1.0 | 1.0 | 1.0 |
| 0.6947 | 0.4879 | 0.7512 | 0.4533 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.0099 | 0.0142 | 0.7019 | 0.4834 | 242 | 0.0399 | 0.8275 | 0.4088 | 1.0 | 1.0 | 1.0 | 1.0 |
| 1.4597 | 0.147 | 1.6444 | 0.1027 | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.025 | 0.0171 | 1.4658 | 0.1453 | 119 | 0.0482 | 1.934 | 0.0555 | 0.872 | 0.8821 | 0.6164 | 0.3329 |
| 1.4134 | 0.1602 | 1.5372 | 0.127 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0293 | 0.0203 | 1.4438 | 0.1515 | 115 | 0.0574 | 1.6676 | 0.0981 | 0.872 | 0.8821 | 0.635 | 0.4906 |
| 0.1916 | 0.8484 | 0.1964 | 0.8446 | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.004 | 0.0208 | 0.1924 | 0.8478 | 126 | 0.0587 | 0.1913 | 0.8486 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.7604 | 0.4485 | -0.8252 | 0.4109 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0141 | 0.0182 | -0.7758 | 0.4394 | 122 | 0.0514 | -0.9664 | 0.3357 | 1.0 | 1.0 | 1.0 | 1.0 |


Holm adjustment is over these six p-values (two tests x full period and the two subperiods). `mde_80pct_power_annual` is the smallest true effect detectable with 80% power at 5% two-sided, given this sample's standard error.

## Sensitivity of the primary tests to the standard-error convention

Every primary test, High, under four conventions: as run (Newey-West, automatic lag floor(4 * (T / 100) ** (2 / 9)) = 4 for the full period, no small-sample correction; the convention PIPELINE locks), the same lag 4 with the covariance multiplied by T / (T - k), lag 6, and lag 12. p-values use t with T - k degrees of freedom. Holm is over the same six tests within each convention. Reported beside; none was used to choose.

| test | period | estimate_annual | t_as_run | p_as_run | holm_as_run | lag_corr_t | lag_corr_p | holm_p_lag_corrected | lag6_t | lag6_p | holm_p_lag6 | lag12_t | lag12_p | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw excess | full | 0.0142 | 1.0313 | 0.3034 | 1.0 | 1.0292 | 0.3044 | 1.0 | 1.0759 | 0.283 | 1.0 | 1.0963 | 0.274 | 1.0 |
| 4-factor alpha | full | 0.0099 | 0.7019 | 0.4834 | 1.0 | 0.6947 | 0.4879 | 1.0 | 0.7512 | 0.4533 | 1.0 | 0.8275 | 0.4088 | 1.0 |
| raw excess | 2005-06 to 2015-05 | 0.025 | 1.4658 | 0.1453 | 0.872 | 1.4597 | 0.147 | 0.8821 | 1.6444 | 0.1027 | 0.6164 | 1.934 | 0.0555 | 0.3329 |
| 4-factor alpha | 2005-06 to 2015-05 | 0.0293 | 1.4438 | 0.1515 | 0.872 | 1.4134 | 0.1602 | 0.8821 | 1.5372 | 0.127 | 0.635 | 1.6676 | 0.0981 | 0.4906 |
| raw excess | 2015-06 to 2025-12 | 0.004 | 0.1924 | 0.8478 | 1.0 | 0.1916 | 0.8484 | 1.0 | 0.1964 | 0.8446 | 1.0 | 0.1913 | 0.8486 | 1.0 |
| 4-factor alpha | 2015-06 to 2025-12 | -0.0141 | -0.7758 | 0.4394 | 1.0 | -0.7604 | 0.4485 | 1.0 | -0.8252 | 0.4109 | 1.0 | -0.9664 | 0.3357 | 1.0 |


Tests rejecting at 5% after Holm adjustment, by convention:

- as run: none
- lag 4 with the T / (T - k) correction: none
- lag 6: none
- lag 12: none

The lag rule used is the formula floor(4 * (T / 100) ** (2 / 9)), which is what PIPELINE locks. It is not the data-dependent Newey-West (1994) bandwidth, which is unstable at T = 127 (one independent check found it picking a lag near 59 there). Read plainly: this family of six (two tests, full period and two periods split after results were seen) is post-hoc and exploratory, not the project's primary inference family (see 09_inference.py). For the 2015-06 to 2025-12 four-factor alpha, Holm p is 1.000 as run, 1.000 with the T / (T - k) correction, 1.000 at lag 6 and 1.0000 at lag 12. Tests rejecting at 5% as run: none.

## All tests

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | series | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | r_squared | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0292 | 0.3044 | 1.0759 | 0.283 | High | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0142 | 0.0138 | 1.0313 | 0.3034 | 246 | 0.0388 | 1.0963 | 0.274 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| 0.6947 | 0.4879 | 0.7512 | 0.4533 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.0099 | 0.0142 | 0.7019 | 0.4834 | 242 | 0.0399 | 0.8275 | 0.4088 | 0.8476 | 1.0 | 1.0 | 1.0 | 1.0 |
| 0.6837 | 0.4948 | 0.716 | 0.4747 | High | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | 0.0092 | 0.0135 | 0.6851 | 0.4939 | 246 | 0.038 | 0.731 | 0.4655 |  |  |  |  |  |
| 0.4702 | 0.6386 | 0.5031 | 0.6153 | High | alpha, six factors (secondary) | full | 247 | 4 | 0.007 | 0.0147 | 0.477 | 0.6338 | 240 | 0.0414 | 0.5292 | 0.5972 | 0.8483 |  |  |  |  |
| 0.7174 | 0.4738 | 0.7113 | 0.4776 | Middle | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0026 | 0.0037 | 0.7188 | 0.4729 | 246 | 0.0103 | 0.7583 | 0.449 |  |  |  |  |  |
| 0.303 | 0.7622 | 0.3311 | 0.7409 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.0025 | 0.0083 | 0.3061 | 0.7598 | 242 | 0.0234 | 0.3607 | 0.7186 | 0.9571 |  |  |  |  |
| -0.6905 | 0.4906 | -0.6821 | 0.4958 | Middle | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.0023 | 0.0034 | -0.6919 | 0.4897 | 246 | 0.0094 | -0.7247 | 0.4693 |  |  |  |  |  |
| -0.2102 | 0.8337 | -0.2263 | 0.8211 | Middle | alpha, six factors (secondary) | full | 247 | 4 | -0.0018 | 0.0085 | -0.2132 | 0.8314 | 240 | 0.0238 | -0.2577 | 0.7968 | 0.9591 |  |  |  |  |
| 0.1551 | 0.8769 | 0.151 | 0.8801 | Low | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0017 | 0.0112 | 0.1554 | 0.8766 | 246 | 0.0315 | 0.1429 | 0.8865 |  |  |  |  |  |
| 0.2051 | 0.8377 | 0.2083 | 0.8352 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.003 | 0.0144 | 0.2072 | 0.836 | 242 | 0.0406 | 0.2005 | 0.8412 | 0.8969 |  |  |  |  |
| -0.2948 | 0.7684 | -0.2878 | 0.7738 | Low | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.0032 | 0.0109 | -0.2954 | 0.7679 | 246 | 0.0307 | -0.2737 | 0.7845 |  |  |  |  |  |
| 0.3056 | 0.7602 | 0.306 | 0.7598 | Low | alpha, six factors (secondary) | full | 247 | 4 | 0.0045 | 0.0146 | 0.31 | 0.7568 | 240 | 0.0409 | 0.2915 | 0.7709 | 0.898 |  |  |  |  |
| 0.6346 | 0.5263 | 0.6485 | 0.5173 | Spread (High minus Low) | raw mean, net (diagnostic) | full | 247 | 4 | 0.0125 | 0.0196 | 0.6359 | 0.5255 | 246 | 0.0552 | 0.5964 | 0.5515 |  |  |  |  |  |
| 0.3611 | 0.7183 | 0.3747 | 0.7082 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | full | 247 | 4 | 0.007 | 0.0191 | 0.3648 | 0.7156 | 242 | 0.0536 | 0.3504 | 0.7264 | 0.0141 |  |  |  |  |
| 0.122 | 0.903 | 0.1242 | 0.9013 | Spread (High minus Low) | alpha, six factors (secondary) | full | 247 | 4 | 0.0025 | 0.0203 | 0.1237 | 0.9016 | 240 | 0.057 | 0.113 | 0.9101 | 0.0261 |  |  |  |  |
| -0.073 | 0.9419 | -0.0782 | 0.9377 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | full | 247 | 4 | -0.0006 | 0.0084 | -0.0737 | 0.9413 | 242 | 0.0238 | -0.0814 | 0.9352 | 0.9614 |  |  |  |  |
| 1.4597 | 0.147 | 1.6444 | 0.1027 | High | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.025 | 0.0171 | 1.4658 | 0.1453 | 119 | 0.0482 | 1.934 | 0.0555 |  | 0.872 | 0.8821 | 0.6164 | 0.3329 |
| 1.4134 | 0.1602 | 1.5372 | 0.127 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0293 | 0.0203 | 1.4438 | 0.1515 | 115 | 0.0574 | 1.6676 | 0.0981 | 0.8708 | 0.872 | 0.8821 | 0.635 | 0.4906 |
| 1.2769 | 0.2041 | 1.4622 | 0.1463 | High | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | 0.0211 | 0.0164 | 1.2822 | 0.2023 | 119 | 0.0464 | 1.7545 | 0.0819 |  |  |  |  |  |
| 1.121 | 0.2647 | 1.2196 | 0.2251 | High | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0274 | 0.0238 | 1.1552 | 0.2504 | 113 | 0.0671 | 1.2907 | 0.1994 | 0.8721 |  |  |  |  |
| -0.0081 | 0.9935 | -0.008 | 0.9936 | Middle | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0 | 0.0048 | -0.0082 | 0.9935 | 119 | 0.0135 | -0.0085 | 0.9932 |  |  |  |  |  |
| 1.3822 | 0.1696 | 1.473 | 0.1435 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0142 | 0.0101 | 1.4119 | 0.1607 | 115 | 0.0284 | 1.6929 | 0.0932 | 0.9728 |  |  |  |  |
| -1.0913 | 0.2773 | -1.1113 | 0.2687 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.004 | 0.0036 | -1.0959 | 0.2753 | 119 | 0.0102 | -1.2416 | 0.2168 |  |  |  |  |  |
| 1.2218 | 0.2243 | 1.2948 | 0.198 | Middle | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0128 | 0.0102 | 1.2591 | 0.2106 | 113 | 0.0287 | 1.4035 | 0.1632 | 0.9749 |  |  |  |  |
| -0.103 | 0.9182 | -0.1062 | 0.9156 | Low | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0012 | 0.0117 | -0.1034 | 0.9178 | 119 | 0.033 | -0.1087 | 0.9137 |  |  |  |  |  |
| 0.645 | 0.5202 | 0.6946 | 0.4887 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0118 | 0.0179 | 0.6589 | 0.5113 | 115 | 0.0506 | 0.7981 | 0.4265 | 0.9063 |  |  |  |  |
| -0.437 | 0.6629 | -0.445 | 0.6571 | Low | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.0051 | 0.0117 | -0.4389 | 0.6615 | 119 | 0.0331 | -0.4522 | 0.6519 |  |  |  |  |  |
| 0.4746 | 0.636 | 0.5111 | 0.6103 | Low | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0093 | 0.0191 | 0.4891 | 0.6257 | 113 | 0.0539 | 0.5792 | 0.5636 | 0.9065 |  |  |  |  |
| 1.1369 | 0.2579 | 1.2819 | 0.2024 | Spread (High minus Low) | raw mean, net (diagnostic) | 2005-06 to 2015-05 | 120 | 4 | 0.0262 | 0.023 | 1.1417 | 0.2559 | 119 | 0.0649 | 1.3539 | 0.1783 |  |  |  |  |  |
| 0.6498 | 0.5171 | 0.718 | 0.4742 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2005-06 to 2015-05 | 120 | 4 | 0.0175 | 0.0264 | 0.6638 | 0.5081 | 115 | 0.0746 | 0.7282 | 0.468 | 0.0323 |  |  |  |  |
| 0.5876 | 0.558 | 0.631 | 0.5293 | Spread (High minus Low) | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0181 | 0.0299 | 0.6055 | 0.5461 | 113 | 0.0845 | 0.6359 | 0.5261 | 0.0374 |  |  |  |  |
| 1.1257 | 0.2626 | 1.1984 | 0.2332 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2005-06 to 2015-05 | 120 | 4 | 0.0121 | 0.0105 | 1.1499 | 0.2526 | 115 | 0.0296 | 1.4009 | 0.1639 | 0.973 |  |  |  |  |
| 0.1916 | 0.8484 | 0.1964 | 0.8446 | High | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.004 | 0.0208 | 0.1924 | 0.8478 | 126 | 0.0587 | 0.1913 | 0.8486 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.7604 | 0.4485 | -0.8252 | 0.4109 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0141 | 0.0182 | -0.7758 | 0.4394 | 122 | 0.0514 | -0.9664 | 0.3357 | 0.8528 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.0942 | 0.9251 | -0.0964 | 0.9233 | High | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0019 | 0.0205 | -0.0946 | 0.9248 | 126 | 0.0579 | -0.0939 | 0.9253 |  |  |  |  |  |
| -0.7824 | 0.4355 | -0.8454 | 0.3996 | High | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0151 | 0.0187 | -0.8049 | 0.4225 | 120 | 0.0529 | -0.9383 | 0.35 | 0.8531 |  |  |  |  |
| 0.9399 | 0.3491 | 0.9404 | 0.3488 | Middle | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0052 | 0.0055 | 0.9436 | 0.3472 | 126 | 0.0155 | 1.0152 | 0.3119 |  |  |  |  |  |
| -1.451 | 0.1493 | -1.5851 | 0.1155 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0144 | 0.0097 | -1.4804 | 0.1413 | 122 | 0.0275 | -1.7215 | 0.0877 | 0.956 |  |  |  |  |
| -0.1373 | 0.891 | -0.1346 | 0.8932 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0008 | 0.0056 | -0.1379 | 0.8905 | 126 | 0.0157 | -0.1406 | 0.8884 |  |  |  |  |  |
| -1.6718 | 0.0972 | -1.8437 | 0.0677 | Middle | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0165 | 0.0096 | -1.7199 | 0.088 | 120 | 0.0271 | -2.1764 | 0.0315 | 0.9585 |  |  |  |  |
| 0.2392 | 0.8113 | 0.2288 | 0.8194 | Low | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0045 | 0.0188 | 0.2402 | 0.8106 | 126 | 0.0532 | 0.2116 | 0.8328 |  |  |  |  |  |
| -0.2047 | 0.8381 | -0.1992 | 0.8424 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0041 | 0.0195 | -0.2089 | 0.8349 | 122 | 0.055 | -0.1738 | 0.8623 | 0.8994 |  |  |  |  |
| -0.0775 | 0.9383 | -0.0746 | 0.9406 | Low | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0014 | 0.0182 | -0.0778 | 0.9381 | 126 | 0.0514 | -0.0693 | 0.9449 |  |  |  |  |  |
| -0.0637 | 0.9493 | -0.062 | 0.9506 | Low | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0013 | 0.0193 | -0.0656 | 0.9478 | 120 | 0.0546 | -0.0539 | 0.9571 | 0.9023 |  |  |  |  |
| -0.0169 | 0.9866 | -0.0167 | 0.9867 | Spread (High minus Low) | raw mean, net (diagnostic) | 2015-06 to 2025-12 | 127 | 4 | -0.0005 | 0.0308 | -0.0169 | 0.9865 | 126 | 0.0871 | -0.0147 | 0.9883 |  |  |  |  |  |
| -0.3582 | 0.7208 | -0.3676 | 0.7138 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2015-06 to 2025-12 | 127 | 4 | -0.01 | 0.0275 | -0.3654 | 0.7154 | 122 | 0.0776 | -0.33 | 0.742 | 0.0446 |  |  |  |  |
| -0.4644 | 0.6432 | -0.4726 | 0.6373 | Spread (High minus Low) | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0138 | 0.0289 | -0.4778 | 0.6337 | 120 | 0.0816 | -0.4174 | 0.6771 | 0.0634 |  |  |  |  |
| -1.844 | 0.0676 | -1.9533 | 0.0531 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2015-06 to 2025-12 | 127 | 4 | -0.017 | 0.009 | -1.8814 | 0.0623 | 122 | 0.0255 | -1.9205 | 0.0571 | 0.9623 |  |  |  |  |


## Subperiods (net)

| period | months | High_CAGR | High_sharpe | Middle_CAGR | Middle_sharpe | Low_CAGR | Low_sharpe | Benchmark_CAGR | Benchmark_sharpe | BenchmarkScored_CAGR | BenchmarkScored_sharpe | High_minus_Benchmark_annual | Spread_annual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2005-06 to 2015-05 | 120 | 0.1319 | 0.693 | 0.1091 | 0.6522 | 0.1054 | 0.5998 | 0.1079 | 0.626 | 0.1127 | 0.6599 | 0.025 | 0.0262 |
| 2015-06 to 2025-12 | 127 | 0.109 | 0.561 | 0.1138 | 0.6338 | 0.1111 | 0.5851 | 0.1079 | 0.5963 | 0.1144 | 0.631 | 0.004 | -0.0005 |


## Holding years

High beat the primary benchmark in 10 of 20 complete holding years = 50%; beat the scored-only benchmark in 10 of 20 = 50%. The partial year is shown separately.

| months | High | Middle | Low | Benchmark | BenchmarkScored | holding_year | High_minus_Benchmark | High_beats_Benchmark | High_beats_BenchmarkScored | Spread | High_names | Low_names |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 0.2234 | 0.1599 | 0.1345 | 0.1469 | 0.1649 | 2005-06 | 0.0764 | True | True | 0.0889 | 43 | 44 |
| 12 | 0.2145 | 0.2427 | 0.1418 | 0.2315 | 0.2241 | 2006-07 | -0.0171 | False | False | 0.0726 | 36 | 55 |
| 12 | 0.041 | -0.0087 | 0.0074 | -0.0203 | -0.0019 | 2007-08 | 0.0613 | True | True | 0.0337 | 24 | 56 |
| 12 | -0.3237 | -0.3156 | -0.3589 | -0.3342 | -0.3252 | 2008-09 | 0.0105 | True | True | 0.0352 | 21 | 79 |
| 12 | 0.2594 | 0.2634 | 0.3504 | 0.3022 | 0.2907 | 2009-10 | -0.0429 | False | False | -0.0911 | 25 | 115 |
| 12 | 0.4567 | 0.337 | 0.3384 | 0.3439 | 0.3459 | 2010-11 | 0.1128 | True | True | 0.1183 | 23 | 88 |
| 12 | -0.0757 | -0.0401 | -0.0598 | -0.0438 | -0.0474 | 2011-12 | -0.0319 | False | False | -0.0159 | 59 | 51 |
| 12 | 0.3879 | 0.2841 | 0.2792 | 0.2885 | 0.2923 | 2012-13 | 0.0994 | True | True | 0.1088 | 29 | 61 |
| 12 | 0.2547 | 0.2214 | 0.2932 | 0.2336 | 0.2449 | 2013-14 | 0.0212 | True | True | -0.0384 | 16 | 110 |
| 12 | 0.1171 | 0.1322 | 0.1588 | 0.1366 | 0.1378 | 2014-15 | -0.0195 | False | False | -0.0417 | 23 | 77 |
| 12 | -0.0497 | 0.0079 | -0.0602 | -0.0066 | -0.0094 | 2015-16 | -0.043 | False | False | 0.0106 | 23 | 76 |
| 12 | 0.173 | 0.1996 | 0.1594 | 0.1734 | 0.1879 | 2016-17 | -0.0004 | False | False | 0.0136 | 15 | 106 |
| 12 | 0.196 | 0.1382 | 0.216 | 0.1444 | 0.1608 | 2017-18 | 0.0516 | True | True | -0.02 | 25 | 81 |
| 12 | -0.092 | 0.033 | 0.0391 | 0.0286 | 0.0209 | 2018-19 | -0.1206 | False | False | -0.1311 | 41 | 55 |
| 12 | 0.0484 | 0.1347 | 0.1317 | 0.1021 | 0.1278 | 2019-20 | -0.0537 | False | False | -0.0833 | 28 | 59 |
| 12 | 0.426 | 0.395 | 0.6261 | 0.4628 | 0.4604 | 2020-21 | -0.0368 | False | False | -0.2001 | 14 | 101 |
| 12 | -0.046 | -0.0491 | -0.0603 | -0.0561 | -0.0517 | 2021-22 | 0.0101 | True | True | 0.0143 | 21 | 122 |
| 12 | -0.0566 | -0.0095 | 0.0681 | -0.0139 | -0.0041 | 2022-23 | -0.0427 | False | False | -0.1247 | 54 | 55 |
| 12 | 0.2622 | 0.2095 | 0.16 | 0.1955 | 0.202 | 2023-24 | 0.0668 | True | True | 0.1022 | 31 | 95 |
| 12 | 0.1897 | 0.1267 | -0.0863 | 0.0951 | 0.093 | 2024-25 | 0.0946 | True | True | 0.2761 | 41 | 73 |
| 7 | 0.2215 | 0.0838 | 0.1316 | 0.0975 | 0.1041 | 2025 partial (7 of 12 months) | 0.124 | True | True | 0.0899 | 33 | 58 |
