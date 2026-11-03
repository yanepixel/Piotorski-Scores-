# Results, net issuance rule (sensitivity): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**0 check failure(s).** 247 months, 2005-06 to 2025-12; last portfolio partial (7 of 12 months). Returns are net of costs; RSP and SPY are fund returns. Primary benchmark = every included name, equal weight, charged like the buckets; BenchmarkScored = scored names only (the like-for-like benchmark).


**Coverage.** 8414 included list rows from 930 unique companies on 21 formation dates (2005-05-31 to 2025-05-30); 7459 scored list rows from 849 unique companies. Unique companies by bucket: High 540, Middle 783, Low 426. Monthly returns 2005-06 to 2025-12 (247 months). No rows are dropped by this script.

## Headline

| portfolio | months | CAGR | volatility | sharpe | max_drawdown | avg_turnover_two_way |
|---|---|---|---|---|---|---|
| High | 247 | 0.1062 | 0.1693 | 0.5856 | -0.4561 | 1.6453 |
| Middle | 247 | 0.1141 | 0.1585 | 0.6593 | -0.4894 | 0.7988 |
| Low | 247 | 0.1032 | 0.1923 | 0.5219 | -0.5658 | 1.7433 |
| Benchmark | 247 | 0.1079 | 0.1626 | 0.6121 | -0.5064 | 0.3318 |
| BenchmarkScored | 247 | 0.1135 | 0.1616 | 0.6464 | -0.4903 | 0.3497 |
| RSP | 247 | 0.0985 | 0.17 | 0.5423 | -0.5559 |  |
| SPY | 247 | 0.1088 | 0.149 | 0.66 | -0.508 |  |

## Primary tests, High, full period (Newey-West, automatic lag 4; t distribution, T - k df; annualised)

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -0.0541 | 0.9569 | -0.0593 | 0.9527 | raw excess vs primary benchmark (all included) | full | 247 | 4 | -0.0004 | 0.0076 | -0.0542 | 0.9568 | 246 | 0.0214 | -0.0608 | 0.9516 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.2449 | 0.8068 | -0.266 | 0.7905 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0028 | 0.0113 | -0.2474 | 0.8048 | 242 | 0.0318 | -0.2708 | 0.7868 | 1.0 | 1.0 | 1.0 | 1.0 |
| 0.8375 | 0.404 | 0.952 | 0.343 | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.0085 | 0.0101 | 0.841 | 0.402 | 119 | 0.0287 | 1.0402 | 0.3004 | 1.0 | 1.0 | 1.0 | 1.0 |
| 1.3582 | 0.177 | 1.4995 | 0.1365 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0201 | 0.0145 | 1.3874 | 0.168 | 115 | 0.041 | 1.7977 | 0.0749 | 0.8399 | 0.8852 | 0.6824 | 0.3743 |
| -0.8069 | 0.4212 | -0.8827 | 0.3791 | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | -0.0089 | 0.0109 | -0.8101 | 0.4194 | 126 | 0.0309 | -0.9101 | 0.3645 | 1.0 | 1.0 | 1.0 | 1.0 |
| -2.6168 | 0.01 | -2.9047 | 0.0044 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0336 | 0.0126 | -2.6699 | 0.0086 | 122 | 0.0355 | -3.6569 | 0.0004 | 0.0517 | 0.06 | 0.0262 | 0.0023 |


Holm adjustment is over these six p-values (two tests x full period and the two subperiods). `mde_80pct_power_annual` is the smallest true effect detectable with 80% power at 5% two-sided, given this sample's standard error.

## Sensitivity of the primary tests to the standard-error convention

Every primary test, High, under four conventions: as run (Newey-West, automatic lag floor(4 * (T / 100) ** (2 / 9)) = 4 for the full period, no small-sample correction; the convention PIPELINE locks), the same lag 4 with the covariance multiplied by T / (T - k), lag 6, and lag 12. p-values use t with T - k degrees of freedom. Holm is over the same six tests within each convention. Reported beside; none was used to choose.

| test | period | estimate_annual | t_as_run | p_as_run | holm_as_run | lag_corr_t | lag_corr_p | holm_p_lag_corrected | lag6_t | lag6_p | holm_p_lag6 | lag12_t | lag12_p | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw excess | full | -0.0004 | -0.0542 | 0.9568 | 1.0 | -0.0541 | 0.9569 | 1.0 | -0.0593 | 0.9527 | 1.0 | -0.0608 | 0.9516 | 1.0 |
| 4-factor alpha | full | -0.0028 | -0.2474 | 0.8048 | 1.0 | -0.2449 | 0.8068 | 1.0 | -0.266 | 0.7905 | 1.0 | -0.2708 | 0.7868 | 1.0 |
| raw excess | 2005-06 to 2015-05 | 0.0085 | 0.841 | 0.402 | 1.0 | 0.8375 | 0.404 | 1.0 | 0.952 | 0.343 | 1.0 | 1.0402 | 0.3004 | 1.0 |
| 4-factor alpha | 2005-06 to 2015-05 | 0.0201 | 1.3874 | 0.168 | 0.8399 | 1.3582 | 0.177 | 0.8852 | 1.4995 | 0.1365 | 0.6824 | 1.7977 | 0.0749 | 0.3743 |
| raw excess | 2015-06 to 2025-12 | -0.0089 | -0.8101 | 0.4194 | 1.0 | -0.8069 | 0.4212 | 1.0 | -0.8827 | 0.3791 | 1.0 | -0.9101 | 0.3645 | 1.0 |
| 4-factor alpha | 2015-06 to 2025-12 | -0.0336 | -2.6699 | 0.0086 | 0.0517 | -2.6168 | 0.01 | 0.06 | -2.9047 | 0.0044 | 0.0262 | -3.6569 | 0.0004 | 0.0023 |


Tests rejecting at 5% after Holm adjustment, by convention:

- as run: none
- lag 4 with the T / (T - k) correction: none
- lag 6: 4-factor alpha 2015-06 to 2025-12
- lag 12: 4-factor alpha 2015-06 to 2025-12

The lag rule used is the formula floor(4 * (T / 100) ** (2 / 9)), which is what PIPELINE locks. It is not the data-dependent Newey-West (1994) bandwidth, which is unstable at T = 127 (one independent check found it picking a lag near 59 there). Read plainly: this family of six (two tests, full period and two periods split after results were seen) is post-hoc and exploratory, not the project's primary inference family (see 09_inference.py). For the 2015-06 to 2025-12 four-factor alpha, Holm p is 0.052 as run, 0.060 with the T / (T - k) correction, 0.026 at lag 6 and 0.0023 at lag 12. Tests rejecting at 5% as run: none.

## All tests

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | series | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | r_squared | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| -0.0541 | 0.9569 | -0.0593 | 0.9527 | High | raw excess vs primary benchmark (all included) | full | 247 | 4 | -0.0004 | 0.0076 | -0.0542 | 0.9568 | 246 | 0.0214 | -0.0608 | 0.9516 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.2449 | 0.8068 | -0.266 | 0.7905 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0028 | 0.0113 | -0.2474 | 0.8048 | 242 | 0.0318 | -0.2708 | 0.7868 | 0.9046 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.7158 | 0.4748 | -0.7747 | 0.4392 | High | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.0053 | 0.0075 | -0.7173 | 0.4739 | 246 | 0.021 | -0.7689 | 0.4427 |  |  |  |  |  |
| -0.8574 | 0.3921 | -0.9353 | 0.3506 | High | alpha, six factors (secondary) | full | 247 | 4 | -0.0098 | 0.0113 | -0.8698 | 0.3853 | 240 | 0.0318 | -0.979 | 0.3286 | 0.9091 |  |  |  |  |
| 1.4724 | 0.1422 | 1.4593 | 0.1458 | Middle | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.005 | 0.0034 | 1.4754 | 0.1414 | 246 | 0.0094 | 1.4775 | 0.1408 |  |  |  |  |  |
| 0.6698 | 0.5036 | 0.74 | 0.46 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.0052 | 0.0077 | 0.6767 | 0.4992 | 242 | 0.0217 | 0.7888 | 0.431 | 0.9586 |  |  |  |  |
| 0.007 | 0.9944 | 0.0072 | 0.9943 | Middle | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | 0.0 | 0.0029 | 0.0071 | 0.9944 | 246 | 0.0081 | 0.0079 | 0.9937 |  |  |  |  |  |
| 0.1263 | 0.8996 | 0.1382 | 0.8902 | Middle | alpha, six factors (secondary) | full | 247 | 4 | 0.001 | 0.0077 | 0.1281 | 0.8982 | 240 | 0.0216 | 0.1552 | 0.8768 | 0.9605 |  |  |  |  |
| 0.0483 | 0.9615 | 0.0465 | 0.963 | Low | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0009 | 0.0192 | 0.0484 | 0.9614 | 246 | 0.054 | 0.0437 | 0.9652 |  |  |  |  |  |
| -0.0814 | 0.9352 | -0.0817 | 0.9349 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0017 | 0.0212 | -0.0822 | 0.9345 | 242 | 0.0596 | -0.0805 | 0.9359 | 0.8139 |  |  |  |  |
| -0.2109 | 0.8331 | -0.203 | 0.8393 | Low | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.004 | 0.019 | -0.2114 | 0.8328 | 246 | 0.0533 | -0.191 | 0.8487 |  |  |  |  |  |
| 0.3738 | 0.7088 | 0.3696 | 0.712 | Low | alpha, six factors (secondary) | full | 247 | 4 | 0.0081 | 0.0213 | 0.3793 | 0.7048 | 240 | 0.0601 | 0.348 | 0.7281 | 0.821 |  |  |  |  |
| -0.0575 | 0.9542 | -0.0559 | 0.9554 | Spread (High minus Low) | raw mean, net (diagnostic) | full | 247 | 4 | -0.0013 | 0.0233 | -0.0576 | 0.9541 | 246 | 0.0655 | -0.0514 | 0.959 |  |  |  |  |  |
| -0.0485 | 0.9613 | -0.0478 | 0.9619 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | full | 247 | 4 | -0.0011 | 0.0215 | -0.049 | 0.961 | 242 | 0.0606 | -0.0439 | 0.965 | 0.0604 |  |  |  |  |
| -0.8059 | 0.4211 | -0.7773 | 0.4377 | Spread (High minus Low) | alpha, six factors (secondary) | full | 247 | 4 | -0.0179 | 0.0219 | -0.8176 | 0.4144 | 240 | 0.0617 | -0.6845 | 0.4943 | 0.1402 |  |  |  |  |
| -0.073 | 0.9419 | -0.0782 | 0.9377 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | full | 247 | 4 | -0.0006 | 0.0084 | -0.0737 | 0.9413 | 242 | 0.0238 | -0.0814 | 0.9352 | 0.9614 |  |  |  |  |
| 0.8375 | 0.404 | 0.952 | 0.343 | High | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.0085 | 0.0101 | 0.841 | 0.402 | 119 | 0.0287 | 1.0402 | 0.3004 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| 1.3582 | 0.177 | 1.4995 | 0.1365 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0201 | 0.0145 | 1.3874 | 0.168 | 115 | 0.041 | 1.7977 | 0.0749 | 0.9244 | 0.8399 | 0.8852 | 0.6824 | 0.3743 |
| 0.6168 | 0.5385 | 0.7077 | 0.4805 | High | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | 0.0058 | 0.0094 | 0.6194 | 0.5368 | 119 | 0.0266 | 0.753 | 0.4529 |  |  |  |  |  |
| 1.2511 | 0.2135 | 1.4117 | 0.1608 | High | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.019 | 0.0148 | 1.2893 | 0.1999 | 113 | 0.0417 | 1.5771 | 0.1176 | 0.9256 |  |  |  |  |
| -0.2273 | 0.8206 | -0.2216 | 0.825 | Middle | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0011 | 0.005 | -0.2282 | 0.8199 | 119 | 0.0141 | -0.2335 | 0.8157 |  |  |  |  |  |
| 1.4083 | 0.1618 | 1.511 | 0.1335 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0135 | 0.0094 | 1.4386 | 0.153 | 115 | 0.0265 | 1.7558 | 0.0818 | 0.9732 |  |  |  |  |
| -0.9782 | 0.3299 | -1.0109 | 0.3141 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.0038 | 0.0039 | -0.9823 | 0.3279 | 119 | 0.011 | -1.2508 | 0.2135 |  |  |  |  |  |
| 0.9552 | 0.3415 | 1.0212 | 0.3093 | Middle | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0098 | 0.01 | 0.9844 | 0.327 | 113 | 0.0283 | 1.1254 | 0.2628 | 0.9752 |  |  |  |  |
| -0.3773 | 0.7066 | -0.3697 | 0.7123 | Low | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0089 | 0.0234 | -0.3789 | 0.7054 | 119 | 0.066 | -0.3798 | 0.7047 |  |  |  |  |  |
| -0.1644 | 0.8697 | -0.1707 | 0.8647 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | -0.0048 | 0.0285 | -0.168 | 0.8669 | 115 | 0.0804 | -0.1871 | 0.8519 | 0.8154 |  |  |  |  |
| -0.4846 | 0.6289 | -0.4705 | 0.6389 | Low | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.0116 | 0.0237 | -0.4866 | 0.6274 | 119 | 0.0671 | -0.4794 | 0.6325 |  |  |  |  |  |
| 0.2823 | 0.7783 | 0.3042 | 0.7615 | Low | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0082 | 0.0281 | 0.2909 | 0.7717 | 113 | 0.0793 | 0.3565 | 0.7221 | 0.8199 |  |  |  |  |
| 0.6229 | 0.5345 | 0.6151 | 0.5397 | Spread (High minus Low) | raw mean, net (diagnostic) | 2005-06 to 2015-05 | 120 | 4 | 0.0174 | 0.0278 | 0.6255 | 0.5328 | 119 | 0.0785 | 0.6012 | 0.5489 |  |  |  |  |  |
| 0.9377 | 0.3504 | 0.9607 | 0.3387 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2005-06 to 2015-05 | 120 | 4 | 0.0249 | 0.026 | 0.9579 | 0.3401 | 115 | 0.0734 | 0.9629 | 0.3376 | 0.0352 |  |  |  |  |
| 0.3869 | 0.6995 | 0.4003 | 0.6897 | Spread (High minus Low) | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0109 | 0.0273 | 0.3987 | 0.6908 | 113 | 0.0771 | 0.4231 | 0.673 | 0.0616 |  |  |  |  |
| 1.1257 | 0.2626 | 1.1984 | 0.2332 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2005-06 to 2015-05 | 120 | 4 | 0.0121 | 0.0105 | 1.1499 | 0.2526 | 115 | 0.0296 | 1.4009 | 0.1639 | 0.973 |  |  |  |  |
| -0.8069 | 0.4212 | -0.8827 | 0.3791 | High | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | -0.0089 | 0.0109 | -0.8101 | 0.4194 | 126 | 0.0309 | -0.9101 | 0.3645 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| -2.6168 | 0.01 | -2.9047 | 0.0044 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0336 | 0.0126 | -2.6699 | 0.0086 | 122 | 0.0355 | -3.6569 | 0.0004 | 0.9134 | 0.0517 | 0.06 | 0.0262 | 0.0023 |
| -1.4389 | 0.1527 | -1.5525 | 0.123 | High | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0159 | 0.011 | -1.4446 | 0.1511 | 126 | 0.0311 | -1.5772 | 0.1173 |  |  |  |  |  |
| -2.8949 | 0.0045 | -3.2391 | 0.0016 | High | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0378 | 0.0127 | -2.9781 | 0.0035 | 120 | 0.0358 | -4.0051 | 0.0001 | 0.9187 |  |  |  |  |
| 2.5309 | 0.0126 | 2.6616 | 0.0088 | Middle | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0107 | 0.0042 | 2.5409 | 0.0123 | 126 | 0.0119 | 2.8528 | 0.0051 |  |  |  |  |  |
| -0.7443 | 0.4581 | -0.8188 | 0.4145 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0071 | 0.0094 | -0.7594 | 0.4491 | 122 | 0.0265 | -0.8194 | 0.4141 | 0.9556 |  |  |  |  |
| 0.9089 | 0.3652 | 0.9351 | 0.3515 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | 0.0037 | 0.004 | 0.9125 | 0.3633 | 126 | 0.0114 | 0.9961 | 0.3211 |  |  |  |  |  |
| -0.9783 | 0.3299 | -1.1019 | 0.2727 | Middle | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0089 | 0.0088 | -1.0064 | 0.3162 | 120 | 0.025 | -1.2037 | 0.2311 | 0.9577 |  |  |  |  |
| 0.338 | 0.7359 | 0.3233 | 0.747 | Low | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0102 | 0.03 | 0.3394 | 0.7349 | 126 | 0.0846 | 0.2929 | 0.7701 |  |  |  |  |  |
| 0.1532 | 0.8785 | 0.1487 | 0.882 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | 0.0041 | 0.026 | 0.1563 | 0.876 | 122 | 0.0736 | 0.1324 | 0.8949 | 0.8263 |  |  |  |  |
| 0.1068 | 0.9151 | 0.1027 | 0.9184 | Low | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | 0.0031 | 0.0292 | 0.1073 | 0.9147 | 126 | 0.0823 | 0.0929 | 0.9261 |  |  |  |  |  |
| 0.3762 | 0.7074 | 0.3584 | 0.7207 | Low | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | 0.0107 | 0.0278 | 0.387 | 0.6994 | 120 | 0.0784 | 0.3087 | 0.7581 | 0.8362 |  |  |  |  |
| -0.5187 | 0.6048 | -0.505 | 0.6144 | Spread (High minus Low) | raw mean, net (diagnostic) | 2015-06 to 2025-12 | 127 | 4 | -0.019 | 0.0365 | -0.5208 | 0.6034 | 126 | 0.1032 | -0.4554 | 0.6496 |  |  |  |  |  |
| -1.238 | 0.2181 | -1.26 | 0.2101 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2015-06 to 2025-12 | 127 | 4 | -0.0376 | 0.0298 | -1.2631 | 0.209 | 122 | 0.0841 | -1.1669 | 0.2455 | 0.1417 |  |  |  |  |
| -1.4401 | 0.1524 | -1.4086 | 0.1615 | Spread (High minus Low) | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0485 | 0.0328 | -1.4815 | 0.1411 | 120 | 0.0925 | -1.2308 | 0.2208 | 0.2325 |  |  |  |  |
| -1.844 | 0.0676 | -1.9533 | 0.0531 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2015-06 to 2025-12 | 127 | 4 | -0.017 | 0.009 | -1.8814 | 0.0623 | 122 | 0.0255 | -1.9205 | 0.0571 | 0.9623 |  |  |  |  |


## Subperiods (net)

| period | months | High_CAGR | High_sharpe | Middle_CAGR | Middle_sharpe | Low_CAGR | Low_sharpe | Benchmark_CAGR | Benchmark_sharpe | BenchmarkScored_CAGR | BenchmarkScored_sharpe | High_minus_Benchmark_annual | Spread_annual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2005-06 to 2015-05 | 120 | 0.1172 | 0.6731 | 0.1077 | 0.6423 | 0.0922 | 0.4868 | 0.1079 | 0.626 | 0.1114 | 0.6531 | 0.0085 | 0.0174 |
| 2015-06 to 2025-12 | 127 | 0.096 | 0.5042 | 0.1202 | 0.6729 | 0.1137 | 0.5536 | 0.1079 | 0.5963 | 0.1156 | 0.6375 | -0.0089 | -0.019 |


## Holding years

High beat the primary benchmark in 9 of 20 complete holding years = 45%; beat the scored-only benchmark in 9 of 20 = 45%. The partial year is shown separately.

| months | High | Middle | Low | Benchmark | BenchmarkScored | holding_year | High_minus_Benchmark | High_beats_Benchmark | High_beats_BenchmarkScored | Spread | High_names | Low_names |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 0.149 | 0.1482 | 0.1967 | 0.1469 | 0.1526 | 2005-06 | 0.002 | True | False | -0.0478 | 71 | 25 |
| 12 | 0.2312 | 0.2392 | 0.0928 | 0.2315 | 0.2278 | 2006-07 | -0.0003 | False | True | 0.1384 | 85 | 23 |
| 12 | 0.0049 | -0.0028 | -0.0404 | -0.0203 | -0.0027 | 2007-08 | 0.0252 | True | True | 0.0453 | 69 | 21 |
| 12 | -0.307 | -0.321 | -0.3851 | -0.3342 | -0.3249 | 2008-09 | 0.0272 | True | True | 0.0781 | 59 | 36 |
| 12 | 0.2698 | 0.2685 | 0.4047 | 0.3022 | 0.2908 | 2009-10 | -0.0325 | False | False | -0.1349 | 56 | 57 |
| 12 | 0.4109 | 0.328 | 0.3536 | 0.3439 | 0.3458 | 2010-11 | 0.067 | True | True | 0.0573 | 54 | 61 |
| 12 | -0.0385 | -0.0435 | -0.1627 | -0.0438 | -0.0477 | 2011-12 | 0.0053 | True | True | 0.1241 | 107 | 23 |
| 12 | 0.3064 | 0.2836 | 0.2449 | 0.2885 | 0.2872 | 2012-13 | 0.0179 | True | True | 0.0616 | 81 | 24 |
| 12 | 0.2043 | 0.2303 | 0.3399 | 0.2336 | 0.2435 | 2013-14 | -0.0292 | False | False | -0.1355 | 51 | 53 |
| 12 | 0.1344 | 0.1347 | 0.1788 | 0.1366 | 0.1395 | 2014-15 | -0.0022 | False | False | -0.0444 | 63 | 33 |
| 12 | -0.0072 | 0.0022 | -0.0515 | -0.0066 | -0.0046 | 2015-16 | -0.0006 | False | False | 0.0443 | 67 | 37 |
| 12 | 0.1546 | 0.2054 | 0.1419 | 0.1734 | 0.1891 | 2016-17 | -0.0188 | False | False | 0.0127 | 47 | 62 |
| 12 | 0.1399 | 0.1543 | 0.2741 | 0.1444 | 0.1631 | 2017-18 | -0.0045 | False | False | -0.1341 | 66 | 31 |
| 12 | -0.0294 | 0.0383 | -0.0133 | 0.0286 | 0.0213 | 2018-19 | -0.058 | False | False | -0.0161 | 78 | 23 |
| 12 | 0.0586 | 0.128 | 0.2859 | 0.1021 | 0.1281 | 2019-20 | -0.0435 | False | False | -0.2273 | 58 | 25 |
| 12 | 0.378 | 0.4371 | 0.6137 | 0.4628 | 0.4592 | 2020-21 | -0.0849 | False | False | -0.2358 | 47 | 59 |
| 12 | -0.0224 | -0.0438 | -0.0696 | -0.0561 | -0.0453 | 2021-22 | 0.0337 | True | True | 0.0471 | 48 | 71 |
| 12 | -0.0599 | -0.0007 | 0.1094 | -0.0139 | -0.0071 | 2022-23 | -0.046 | False | False | -0.1693 | 93 | 27 |
| 12 | 0.2198 | 0.2051 | 0.1705 | 0.1955 | 0.2031 | 2023-24 | 0.0243 | True | True | 0.0493 | 46 | 50 |
| 12 | 0.1439 | 0.1106 | -0.1256 | 0.0951 | 0.0919 | 2024-25 | 0.0488 | True | True | 0.2695 | 83 | 43 |
| 7 | 0.1117 | 0.1071 | 0.0475 | 0.0975 | 0.104 | 2025 partial (7 of 12 months) | 0.0142 | True | True | 0.0642 | 73 | 29 |
