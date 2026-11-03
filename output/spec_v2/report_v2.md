# spec_v2 results, net issuance rule (primary): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**0 check failure(s).** 247 months, 2005-06 to 2025-12; last portfolio partial (7 of 12 months). Returns are net of costs; RSP and SPY are fund returns. Primary benchmark = every included name, equal weight, charged like the buckets; BenchmarkScored = scored names only (v1's benchmark).


**Coverage.** 8414 included list rows from 930 unique companies on 21 formation dates (2005-05-31 to 2025-05-30); 7614 scored list rows from 857 unique companies. Unique companies by bucket: High 547, Middle 790, Low 441. Monthly returns 2005-06 to 2025-12 (247 months). No rows are dropped by this script.

## Headline: v2 beside v1

| portfolio | v2_months | v2_CAGR | v2_volatility | v2_sharpe | v2_max_drawdown | v2_avg_turnover_two_way | v1_CAGR | v1_volatility | v1_sharpe | v1_max_drawdown | v1_avg_turnover_two_way |
|---|---|---|---|---|---|---|---|---|---|---|---|
| High | 247 | 0.1075 | 0.1696 | 0.5917 | -0.4572 | 1.6567 | 0.1091 | 0.1679 | 0.6049 | -0.4436 | 1.6388 |
| Middle | 247 | 0.1141 | 0.1588 | 0.6586 | -0.4908 | 0.7978 | 0.1126 | 0.1585 | 0.6505 | -0.4981 | 0.811 |
| Low | 247 | 0.1019 | 0.1889 | 0.5213 | -0.5687 | 1.7354 | 0.1093 | 0.1985 | 0.539 | -0.6099 | 1.7579 |
| Benchmark | 247 | 0.1079 | 0.1626 | 0.6121 | -0.5064 | 0.3318 |  |  |  |  |  |
| BenchmarkScored | 247 | 0.1136 | 0.1617 | 0.6464 | -0.4918 | 0.3422 | 0.1135 | 0.1617 | 0.6458 | -0.4909 | 0.3413 |
| RSP | 247 | 0.0985 | 0.17 | 0.5423 | -0.5559 |  | 0.0985 | 0.17 | 0.5423 | -0.5559 |  |
| SPY | 247 | 0.1088 | 0.149 | 0.66 | -0.508 |  | 0.1088 | 0.149 | 0.66 | -0.508 |  |


v1 'Benchmark' = scored names only, so it sits beside `BenchmarkScored`. v1 rows use v1's costs (no charge on mid-period reinvestment).

## Primary tests, High, full period (Newey-West, automatic lag 4; t distribution, T - k df; annualised)

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0992 | 0.921 | 0.1088 | 0.9135 | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0008 | 0.0076 | 0.0994 | 0.9209 | 246 | 0.0213 | 0.1108 | 0.9119 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.1293 | 0.8972 | -0.1401 | 0.8887 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0015 | 0.0114 | -0.1307 | 0.8961 | 242 | 0.0319 | -0.1422 | 0.8871 | 1.0 | 1.0 | 1.0 | 1.0 |
| 1.1283 | 0.2614 | 1.2995 | 0.1963 | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.0113 | 0.01 | 1.1331 | 0.2595 | 119 | 0.0282 | 1.4039 | 0.163 | 1.0 | 1.0 | 0.7851 | 0.6518 |
| 1.5284 | 0.1292 | 1.6762 | 0.0964 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0228 | 0.0146 | 1.5613 | 0.1212 | 115 | 0.0412 | 1.9438 | 0.0544 | 0.606 | 0.6458 | 0.4821 | 0.2718 |
| -0.8435 | 0.4005 | -0.9208 | 0.3589 | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | -0.0092 | 0.0109 | -0.8469 | 0.3987 | 126 | 0.0308 | -0.958 | 0.3399 | 1.0 | 1.0 | 1.0 | 1.0 |
| -2.6498 | 0.0091 | -2.938 | 0.004 | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0338 | 0.0125 | -2.7036 | 0.0078 | 122 | 0.0353 | -3.7237 | 0.0003 | 0.047 | 0.0547 | 0.0237 | 0.0018 |


Holm adjustment is over these six p-values (two tests x full period and the two subperiods). `mde_80pct_power_annual` is the smallest true effect detectable with 80% power at 5% two-sided, given this sample's standard error.

## Sensitivity of the primary tests to the standard-error convention

Every primary test, High, under four conventions: as run (Newey-West, automatic lag floor(4 * (T / 100) ** (2 / 9)) = 4 for the full period, no small-sample correction; the convention SPEC_V2 locks), the same lag 4 with the covariance multiplied by T / (T - k), lag 6, and lag 12. p-values use t with T - k degrees of freedom. Holm is over the same six tests within each convention. Reported beside; none was used to choose.

| test | period | estimate_annual | t_as_run | p_as_run | holm_as_run | lag_corr_t | lag_corr_p | holm_p_lag_corrected | lag6_t | lag6_p | holm_p_lag6 | lag12_t | lag12_p | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw excess | full | 0.0008 | 0.0994 | 0.9209 | 1.0 | 0.0992 | 0.921 | 1.0 | 0.1088 | 0.9135 | 1.0 | 0.1108 | 0.9119 | 1.0 |
| 4-factor alpha | full | -0.0015 | -0.1307 | 0.8961 | 1.0 | -0.1293 | 0.8972 | 1.0 | -0.1401 | 0.8887 | 1.0 | -0.1422 | 0.8871 | 1.0 |
| raw excess | 2005-06 to 2015-05 | 0.0113 | 1.1331 | 0.2595 | 1.0 | 1.1283 | 0.2614 | 1.0 | 1.2995 | 0.1963 | 0.7851 | 1.4039 | 0.163 | 0.6518 |
| 4-factor alpha | 2005-06 to 2015-05 | 0.0228 | 1.5613 | 0.1212 | 0.606 | 1.5284 | 0.1292 | 0.6458 | 1.6762 | 0.0964 | 0.4821 | 1.9438 | 0.0544 | 0.2718 |
| raw excess | 2015-06 to 2025-12 | -0.0092 | -0.8469 | 0.3987 | 1.0 | -0.8435 | 0.4005 | 1.0 | -0.9208 | 0.3589 | 1.0 | -0.958 | 0.3399 | 1.0 |
| 4-factor alpha | 2015-06 to 2025-12 | -0.0338 | -2.7036 | 0.0078 | 0.047 | -2.6498 | 0.0091 | 0.0547 | -2.938 | 0.004 | 0.0237 | -3.7237 | 0.0003 | 0.0018 |


Tests rejecting at 5% after Holm adjustment, by convention:

- as run: 4-factor alpha 2015-06 to 2025-12
- lag 4 with the T / (T - k) correction: none
- lag 6: 4-factor alpha 2015-06 to 2025-12
- lag 12: 4-factor alpha 2015-06 to 2025-12

The lag rule used is the formula floor(4 * (T / 100) ** (2 / 9)), which is what SPEC_V2 locks. It is not the data-dependent Newey-West (1994) bandwidth, which is unstable at T = 127 (one independent check found it picking a lag near 59 there). Read plainly: the only primary test that rejects at 5% after Holm is the 2015-06 to 2025-12 four-factor alpha, and its margin is thin. Holm p is 0.047 as run, 0.055 with the T / (T - k) correction (no rejection), 0.024 at lag 6 and 0.0018 at lag 12. No other primary test rejects under any convention.

## All tests

| lag_corr_t | lag_corr_p | lag6_t | lag6_p | series | test | period | months | hac_lags | estimate_annual | se_annual | t | p_value | df | mde_80pct_power_annual | lag12_t | lag12_p | r_squared | holm_adjusted_p | holm_p_lag_corrected | holm_p_lag6 | holm_p_lag12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0992 | 0.921 | 0.1088 | 0.9135 | High | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.0008 | 0.0076 | 0.0994 | 0.9209 | 246 | 0.0213 | 0.1108 | 0.9119 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.1293 | 0.8972 | -0.1401 | 0.8887 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0015 | 0.0114 | -0.1307 | 0.8961 | 242 | 0.0319 | -0.1422 | 0.8871 | 0.9033 | 1.0 | 1.0 | 1.0 | 1.0 |
| -0.5598 | 0.5761 | -0.6071 | 0.5444 | High | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.0042 | 0.0075 | -0.561 | 0.5753 | 246 | 0.0211 | -0.6017 | 0.5479 |  |  |  |  |  |
| -0.7387 | 0.4608 | -0.8015 | 0.4236 | High | alpha, six factors (secondary) | full | 247 | 4 | -0.0086 | 0.0114 | -0.7494 | 0.4544 | 240 | 0.0321 | -0.8326 | 0.4059 | 0.9078 |  |  |  |  |
| 1.5147 | 0.1311 | 1.5054 | 0.1335 | Middle | raw excess vs primary benchmark (all included) | full | 247 | 4 | 0.005 | 0.0033 | 1.5178 | 0.1304 | 246 | 0.0093 | 1.5143 | 0.1312 |  |  |  |  |  |
| 0.6346 | 0.5263 | 0.6996 | 0.4849 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | 0.005 | 0.0078 | 0.6411 | 0.5221 | 242 | 0.022 | 0.7472 | 0.4557 | 0.958 |  |  |  |  |
| 0.0193 | 0.9846 | 0.0194 | 0.9845 | Middle | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | 0.0001 | 0.0029 | 0.0194 | 0.9846 | 246 | 0.0083 | 0.0207 | 0.9835 |  |  |  |  |  |
| 0.1244 | 0.9011 | 0.1354 | 0.8924 | Middle | alpha, six factors (secondary) | full | 247 | 4 | 0.001 | 0.0078 | 0.1262 | 0.8997 | 240 | 0.022 | 0.1509 | 0.8802 | 0.9597 |  |  |  |  |
| -0.0469 | 0.9626 | -0.0448 | 0.9643 | Low | raw excess vs primary benchmark (all included) | full | 247 | 4 | -0.0009 | 0.0196 | -0.047 | 0.9626 | 246 | 0.0552 | -0.0416 | 0.9668 |  |  |  |  |  |
| -0.0739 | 0.9412 | -0.0736 | 0.9414 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | full | 247 | 4 | -0.0016 | 0.0216 | -0.0746 | 0.9406 | 242 | 0.0609 | -0.0718 | 0.9428 | 0.8106 |  |  |  |  |
| -0.3061 | 0.7598 | -0.2926 | 0.7701 | Low | raw excess vs scored-only benchmark (sensitivity) | full | 247 | 4 | -0.0059 | 0.0192 | -0.3067 | 0.7594 | 246 | 0.054 | -0.2711 | 0.7865 |  |  |  |  |  |
| 0.3034 | 0.7619 | 0.2976 | 0.7663 | Low | alpha, six factors (secondary) | full | 247 | 4 | 0.0068 | 0.022 | 0.3078 | 0.7585 | 240 | 0.0619 | 0.2796 | 0.78 | 0.8162 |  |  |  |  |
| 0.0707 | 0.9437 | 0.0687 | 0.9453 | Spread (High minus Low) | raw mean, net (diagnostic) | full | 247 | 4 | 0.0017 | 0.0236 | 0.0708 | 0.9436 | 246 | 0.0665 | 0.0628 | 0.95 |  |  |  |  |  |
| 0.0059 | 0.9953 | 0.0058 | 0.9954 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | full | 247 | 4 | 0.0001 | 0.0221 | 0.006 | 0.9952 | 242 | 0.0621 | 0.0053 | 0.9958 | 0.0521 |  |  |  |  |
| -0.6662 | 0.5059 | -0.641 | 0.5221 | Spread (High minus Low) | alpha, six factors (secondary) | full | 247 | 4 | -0.0153 | 0.0227 | -0.6758 | 0.4998 | 240 | 0.0638 | -0.562 | 0.5746 | 0.1203 |  |  |  |  |
| -0.073 | 0.9419 | -0.0782 | 0.9377 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | full | 247 | 4 | -0.0006 | 0.0084 | -0.0737 | 0.9413 | 242 | 0.0238 | -0.0814 | 0.9352 | 0.9614 |  |  |  |  |
| 1.1283 | 0.2614 | 1.2995 | 0.1963 | High | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | 0.0113 | 0.01 | 1.1331 | 0.2595 | 119 | 0.0282 | 1.4039 | 0.163 |  | 1.0 | 1.0 | 0.7851 | 0.6518 |
| 1.5284 | 0.1292 | 1.6762 | 0.0964 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0228 | 0.0146 | 1.5613 | 0.1212 | 115 | 0.0412 | 1.9438 | 0.0544 | 0.922 | 0.606 | 0.6458 | 0.4821 | 0.2718 |
| 0.7769 | 0.4387 | 0.9078 | 0.3658 | High | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | 0.0074 | 0.0095 | 0.7802 | 0.4368 | 119 | 0.0268 | 0.9629 | 0.3375 |  |  |  |  |  |
| 1.3873 | 0.1681 | 1.5432 | 0.1256 | High | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0215 | 0.0151 | 1.4297 | 0.1556 | 113 | 0.0426 | 1.6515 | 0.1014 | 0.9234 |  |  |  |  |
| -0.0264 | 0.979 | -0.0257 | 0.9795 | Middle | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0001 | 0.0048 | -0.0265 | 0.9789 | 119 | 0.0137 | -0.0264 | 0.979 |  |  |  |  |  |
| 1.4106 | 0.1611 | 1.492 | 0.1384 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | 0.0139 | 0.0096 | 1.441 | 0.1523 | 115 | 0.0273 | 1.6856 | 0.0946 | 0.9726 |  |  |  |  |
| -1.0655 | 0.2888 | -1.0799 | 0.2824 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.0041 | 0.0038 | -1.0699 | 0.2868 | 119 | 0.0107 | -1.2676 | 0.2074 |  |  |  |  |  |
| 1.0375 | 0.3017 | 1.0929 | 0.2767 | Middle | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0109 | 0.0102 | 1.0691 | 0.2873 | 113 | 0.0289 | 1.1756 | 0.2422 | 0.9747 |  |  |  |  |
| -0.3129 | 0.7549 | -0.3058 | 0.7603 | Low | raw excess vs primary benchmark (all included) | 2005-06 to 2015-05 | 120 | 4 | -0.0073 | 0.0233 | -0.3143 | 0.7539 | 119 | 0.0659 | -0.3091 | 0.7578 |  |  |  |  |  |
| -0.0018 | 0.9986 | -0.0018 | 0.9985 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2005-06 to 2015-05 | 120 | 4 | -0.0001 | 0.0294 | -0.0018 | 0.9986 | 115 | 0.0831 | -0.002 | 0.9984 | 0.8171 |  |  |  |  |
| -0.4819 | 0.6308 | -0.4666 | 0.6416 | Low | raw excess vs scored-only benchmark (sensitivity) | 2005-06 to 2015-05 | 120 | 4 | -0.0113 | 0.0233 | -0.4839 | 0.6294 | 119 | 0.0657 | -0.4643 | 0.6433 |  |  |  |  |  |
| 0.2728 | 0.7855 | 0.2869 | 0.7747 | Low | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0085 | 0.0301 | 0.2811 | 0.7792 | 113 | 0.085 | 0.3233 | 0.7471 | 0.8196 |  |  |  |  |
| 0.67 | 0.5041 | 0.6731 | 0.5022 | Spread (High minus Low) | raw mean, net (diagnostic) | 2005-06 to 2015-05 | 120 | 4 | 0.0186 | 0.0277 | 0.6728 | 0.5024 | 119 | 0.0783 | 0.6537 | 0.5146 |  |  |  |  |  |
| 0.8082 | 0.4206 | 0.841 | 0.4021 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2005-06 to 2015-05 | 120 | 4 | 0.0228 | 0.0276 | 0.8256 | 0.4108 | 115 | 0.0781 | 0.8368 | 0.4044 | 0.02 |  |  |  |  |
| 0.419 | 0.676 | 0.4324 | 0.6663 | Spread (High minus Low) | alpha, six factors (secondary) | 2005-06 to 2015-05 | 120 | 4 | 0.0131 | 0.0303 | 0.4317 | 0.6668 | 113 | 0.0857 | 0.4446 | 0.6575 | 0.0331 |  |  |  |  |
| 1.1257 | 0.2626 | 1.1984 | 0.2332 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2005-06 to 2015-05 | 120 | 4 | 0.0121 | 0.0105 | 1.1499 | 0.2526 | 115 | 0.0296 | 1.4009 | 0.1639 | 0.973 |  |  |  |  |
| -0.8435 | 0.4005 | -0.9208 | 0.3589 | High | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | -0.0092 | 0.0109 | -0.8469 | 0.3987 | 126 | 0.0308 | -0.958 | 0.3399 |  | 1.0 | 1.0 | 1.0 | 1.0 |
| -2.6498 | 0.0091 | -2.938 | 0.004 | High | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0338 | 0.0125 | -2.7036 | 0.0078 | 122 | 0.0353 | -3.7237 | 0.0003 | 0.9139 | 0.047 | 0.0547 | 0.0237 | 0.0018 |
| -1.365 | 0.1747 | -1.4631 | 0.1459 | High | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0152 | 0.0111 | -1.3704 | 0.173 | 126 | 0.0313 | -1.4875 | 0.1394 |  |  |  |  |  |
| -2.9236 | 0.0041 | -3.2697 | 0.0014 | High | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0379 | 0.0126 | -3.0076 | 0.0032 | 120 | 0.0356 | -4.0776 | 0.0001 | 0.919 |  |  |  |  |
| 2.2951 | 0.0234 | 2.4026 | 0.0177 | Middle | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0099 | 0.0043 | 2.3042 | 0.0228 | 126 | 0.0121 | 2.5301 | 0.0126 |  |  |  |  |  |
| -0.8667 | 0.3878 | -0.9616 | 0.3382 | Middle | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | -0.0082 | 0.0092 | -0.8843 | 0.3783 | 122 | 0.0261 | -0.975 | 0.3315 | 0.956 |  |  |  |  |
| 0.9157 | 0.3616 | 0.9311 | 0.3536 | Middle | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | 0.0039 | 0.0043 | 0.9193 | 0.3597 | 126 | 0.0121 | 0.9705 | 0.3337 |  |  |  |  |  |
| -1.0903 | 0.2777 | -1.2339 | 0.2196 | Middle | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0099 | 0.0088 | -1.1217 | 0.2642 | 120 | 0.0248 | -1.3563 | 0.1776 | 0.958 |  |  |  |  |
| 0.164 | 0.87 | 0.1552 | 0.8769 | Low | raw excess vs primary benchmark (all included) | 2015-06 to 2025-12 | 127 | 4 | 0.0051 | 0.0312 | 0.1646 | 0.8695 | 126 | 0.088 | 0.139 | 0.8897 |  |  |  |  |  |
| 0.0526 | 0.9582 | 0.0505 | 0.9598 | Low | alpha, Mkt-RF+SMB+HML+MOM (excess of rf) | 2015-06 to 2025-12 | 127 | 4 | 0.0015 | 0.0273 | 0.0536 | 0.9573 | 122 | 0.0771 | 0.0445 | 0.9646 | 0.8205 |  |  |  |  |
| -0.0266 | 0.9788 | -0.0253 | 0.9798 | Low | raw excess vs scored-only benchmark (sensitivity) | 2015-06 to 2025-12 | 127 | 4 | -0.0008 | 0.0302 | -0.0267 | 0.9787 | 126 | 0.0852 | -0.0226 | 0.982 |  |  |  |  |  |
| 0.2811 | 0.7791 | 0.2665 | 0.7903 | Low | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | 0.0083 | 0.0285 | 0.2892 | 0.773 | 120 | 0.0806 | 0.229 | 0.8193 | 0.8309 |  |  |  |  |
| -0.3807 | 0.7041 | -0.3662 | 0.7149 | Spread (High minus Low) | raw mean, net (diagnostic) | 2015-06 to 2025-12 | 127 | 4 | -0.0144 | 0.0376 | -0.3822 | 0.703 | 126 | 0.1061 | -0.3279 | 0.7436 |  |  |  |  |  |
| -1.1338 | 0.2591 | -1.1291 | 0.2611 | Spread (High minus Low) | alpha, Mkt-RF+SMB+HML+MOM | 2015-06 to 2025-12 | 127 | 4 | -0.0353 | 0.0305 | -1.1568 | 0.2496 | 122 | 0.0861 | -1.0263 | 0.3068 | 0.1552 |  |  |  |  |
| -1.3652 | 0.1747 | -1.3175 | 0.1902 | Spread (High minus Low) | alpha, six factors (secondary) | 2015-06 to 2025-12 | 127 | 4 | -0.0462 | 0.0329 | -1.4045 | 0.1628 | 120 | 0.0928 | -1.1383 | 0.2573 | 0.2413 |  |  |  |  |
| -1.844 | 0.0676 | -1.9533 | 0.0531 | Benchmark (primary) | alpha, Mkt-RF+SMB+HML+MOM (context) | 2015-06 to 2025-12 | 127 | 4 | -0.017 | 0.009 | -1.8814 | 0.0623 | 122 | 0.0255 | -1.9205 | 0.0571 | 0.9623 |  |  |  |  |


## Subperiods (net)

| period | months | High_CAGR | High_sharpe | Middle_CAGR | Middle_sharpe | Low_CAGR | Low_sharpe | Benchmark_CAGR | Benchmark_sharpe | BenchmarkScored_CAGR | BenchmarkScored_sharpe | High_minus_Benchmark_annual | Spread_annual |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2005-06 to 2015-05 | 120 | 0.1202 | 0.6883 | 0.1087 | 0.646 | 0.0954 | 0.5134 | 0.1079 | 0.626 | 0.1127 | 0.6599 | 0.0113 | 0.0186 |
| 2015-06 to 2025-12 | 127 | 0.0955 | 0.5018 | 0.1193 | 0.6681 | 0.1081 | 0.5267 | 0.1079 | 0.5963 | 0.1144 | 0.631 | -0.0092 | -0.0144 |


## Holding years

High beat the primary benchmark in 9 of 20 complete holding years = 45%; beat the scored-only benchmark in 10 of 20 = 50%. The partial year is shown separately.

| months | High | Middle | Low | Benchmark | BenchmarkScored | holding_year | High_minus_Benchmark | High_beats_Benchmark | High_beats_BenchmarkScored | Spread | High_names | Low_names |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 0.1806 | 0.1583 | 0.1712 | 0.1469 | 0.1649 | 2005-06 | 0.0337 | True | True | 0.0095 | 78 | 27 |
| 12 | 0.231 | 0.2385 | 0.0612 | 0.2315 | 0.2241 | 2006-07 | -0.0005 | False | True | 0.1698 | 87 | 26 |
| 12 | -0.0023 | 0.0012 | -0.0456 | -0.0203 | -0.0019 | 2007-08 | 0.018 | True | False | 0.0433 | 68 | 23 |
| 12 | -0.307 | -0.3216 | -0.3835 | -0.3342 | -0.3252 | 2008-09 | 0.0272 | True | True | 0.0765 | 59 | 37 |
| 12 | 0.2709 | 0.2693 | 0.3982 | 0.3022 | 0.2907 | 2009-10 | -0.0313 | False | False | -0.1273 | 57 | 59 |
| 12 | 0.4083 | 0.3289 | 0.3545 | 0.3439 | 0.3459 | 2010-11 | 0.0644 | True | True | 0.0538 | 52 | 66 |
| 12 | -0.0395 | -0.0465 | -0.11 | -0.0438 | -0.0474 | 2011-12 | 0.0043 | True | True | 0.0705 | 109 | 26 |
| 12 | 0.3159 | 0.2867 | 0.2619 | 0.2885 | 0.2923 | 2012-13 | 0.0273 | True | True | 0.0539 | 80 | 27 |
| 12 | 0.2067 | 0.2316 | 0.3365 | 0.2336 | 0.2449 | 2013-14 | -0.0269 | False | False | -0.1298 | 49 | 56 |
| 12 | 0.1344 | 0.1302 | 0.196 | 0.1366 | 0.1378 | 2014-15 | -0.0022 | False | False | -0.0616 | 63 | 34 |
| 12 | -0.0072 | 0.0035 | -0.0993 | -0.0066 | -0.0094 | 2015-16 | -0.0006 | False | True | 0.0921 | 67 | 41 |
| 12 | 0.1567 | 0.2057 | 0.1324 | 0.1734 | 0.1879 | 2016-17 | -0.0167 | False | False | 0.0243 | 46 | 64 |
| 12 | 0.1385 | 0.1514 | 0.2645 | 0.1444 | 0.1608 | 2017-18 | -0.0059 | False | False | -0.1259 | 65 | 34 |
| 12 | -0.0297 | 0.0374 | -0.006 | 0.0286 | 0.0209 | 2018-19 | -0.0582 | False | False | -0.0237 | 79 | 24 |
| 12 | 0.0586 | 0.1275 | 0.2859 | 0.1021 | 0.1278 | 2019-20 | -0.0435 | False | False | -0.2273 | 58 | 25 |
| 12 | 0.378 | 0.4327 | 0.6395 | 0.4628 | 0.4604 | 2020-21 | -0.0849 | False | False | -0.2615 | 47 | 60 |
| 12 | -0.0224 | -0.052 | -0.0734 | -0.0561 | -0.0517 | 2021-22 | 0.0337 | True | True | 0.051 | 48 | 75 |
| 12 | -0.0599 | 0.0011 | 0.121 | -0.0139 | -0.0041 | 2022-23 | -0.046 | False | False | -0.1809 | 93 | 29 |
| 12 | 0.2145 | 0.2059 | 0.1632 | 0.1955 | 0.202 | 2023-24 | 0.019 | True | True | 0.0513 | 47 | 51 |
| 12 | 0.1439 | 0.1133 | -0.1344 | 0.0951 | 0.093 | 2024-25 | 0.0488 | True | True | 0.2783 | 83 | 43 |
| 7 | 0.1117 | 0.1075 | 0.0488 | 0.0975 | 0.1041 | 2025 partial (7 of 12 months) | 0.0142 | True | True | 0.0629 | 73 | 31 |
