# Extension to May 2026 (Compustat returns from January 2026): Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**Labelled extension, not the headline.** The January-May 2026 extension uses Compustat monthly returns because CRSP data on this account ends in December 2025. It is reported separately and does not change any headline figure. On 15,752 earlier held months, Compustat agrees with CRSP within 1% on 99.96%, but it differs at spin-offs (up to 8.4 points on a single stock) and at delistings. Two spin-offs (Becton Dickinson, Comcast) and two acquisitions (Hologic, Coterra) fall in the window. No bankruptcies do.

**Terms.** **CAGR** is the constant yearly growth rate. **Sharpe** is return above the risk-free rate per unit of volatility. **Alpha** is return left after six factors (market, size, value, profitability, investment, momentum), with Newey-West standard errors over 12 months. A **t-stat** beyond about 2 is treated as significant. A **spin-off** is a company distributing shares of a subsidiary. **bp** is 0.01%.

**Mechanics.** The 2025 portfolio keeps its CRSP December 2025 weights and drifts for five more months, with no new rebalance and no new cost. Returns are net of costs through the existing rebalance charges. Hologic stops after April 2026 and Coterra after May 2026 by rule, with their value going pro rata afterwards. `secstat` is not used. Any other null, missing row or exit stops the run; none occurred. No portfolio is rebalanced in June 2026.

**Headline unchanged:** files hashed before and after this run: all identical. The June-December 2025 series reproduces the published file to 9.9e-17.

## Performance

| period | portfolio | months | CAGR | volatility | sharpe | max_drawdown |
|---|---|---|---|---|---|---|
| Headline: June 2005 to December 2025 (CRSP) | High | 247 | 0.1091 | 0.1679 | 0.6049 | -0.4436 |
| Headline: June 2005 to December 2025 (CRSP) | Middle | 247 | 0.1126 | 0.1585 | 0.6505 | -0.4981 |
| Headline: June 2005 to December 2025 (CRSP) | Low | 247 | 0.1093 | 0.1985 | 0.539 | -0.6099 |
| Headline: June 2005 to December 2025 (CRSP) | Benchmark | 247 | 0.1135 | 0.1617 | 0.6458 | -0.4909 |
| Headline: June 2005 to December 2025 (CRSP) | RSP | 247 | 0.0985 | 0.17 | 0.5423 | -0.5559 |
| Headline: June 2005 to December 2025 (CRSP) | SPY | 247 | 0.1088 | 0.149 | 0.66 | -0.508 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | High | 252 | 0.1144 | 0.1692 | 0.6279 | -0.4436 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Middle | 252 | 0.1158 | 0.1584 | 0.6671 | -0.4981 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Low | 252 | 0.1268 | 0.2021 | 0.6091 | -0.6099 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Benchmark | 252 | 0.1186 | 0.1621 | 0.6712 | -0.4909 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | RSP | 252 | 0.1012 | 0.1696 | 0.5557 | -0.5559 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | SPY | 252 | 0.1122 | 0.1499 | 0.6749 | -0.508 |


## High against the Benchmark

| period | months | High_minus_Benchmark_annual | CAGR_difference | tracking_error | information_ratio |
|---|---|---|---|---|---|
| Headline: June 2005 to December 2025 (CRSP) | 247 | -0.0029 | -0.0044 | 0.0369 | -0.0795 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | 252 | -0.0026 | -0.0042 | 0.0375 | -0.0697 |


High beat the Benchmark in **11 of 21 complete holding years**. The headline counted 10 of 20 complete years, with 2025 shown separately as partial.


## Six-factor regressions, net

| period | series | months | alpha_annual | alpha_t | r_squared | beta_Mkt-RF | beta_SMB | beta_HML | beta_RMW | beta_CMA | beta_MOM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Headline: June 2005 to December 2025 (CRSP) | High minus risk-free | 247 | -0.008 | -0.715 | 0.913 | 1.022 | 0.184 | -0.052 | 0.192 | 0.041 | 0.001 |
| Headline: June 2005 to December 2025 (CRSP) | Spread | 247 | -0.02 | -0.724 | 0.166 | -0.015 | -0.143 | 0.075 | 0.473 | 0.039 | 0.074 |
| Headline: June 2005 to December 2025 (CRSP) | High minus Benchmark | 247 | -0.01 | -1.023 | 0.062 | 0.019 | 0.017 | 0.017 | 0.145 | -0.025 | 0.011 |
| Headline: June 2005 to December 2025 (CRSP) | Low minus risk-free | 247 | 0.013 | 0.548 | 0.822 | 1.037 | 0.327 | -0.126 | -0.281 | 0.003 | -0.073 |
| Headline: June 2005 to December 2025 (CRSP) | Benchmark minus risk-free | 247 | 0.002 | 0.255 | 0.962 | 1.003 | 0.167 | -0.069 | 0.047 | 0.066 | -0.011 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | High minus risk-free | 252 | -0.005 | -0.422 | 0.907 | 1.028 | 0.171 | -0.067 | 0.161 | 0.088 | -0.002 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Spread | 252 | -0.028 | -1.008 | 0.16 | -0.022 | -0.171 | 0.02 | 0.459 | 0.103 | 0.028 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | High minus Benchmark | 252 | -0.009 | -0.911 | 0.045 | 0.026 | 0.001 | 0.011 | 0.113 | -0.014 | 0.011 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Low minus risk-free | 252 | 0.024 | 1.01 | 0.811 | 1.05 | 0.343 | -0.087 | -0.297 | -0.015 | -0.03 |
| Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026) | Benchmark minus risk-free | 252 | 0.004 | 0.588 | 0.959 | 1.002 | 0.171 | -0.078 | 0.049 | 0.102 | -0.013 |


## Subperiods

| run | period | months | High_CAGR | Low_CAGR | Benchmark_CAGR | High_sharpe | Benchmark_sharpe | High_excess_annual | Spread_annual | High_alpha_annual | High_alpha_t | High_minus_Benchmark_alpha | High_minus_Benchmark_alpha_t | Spread_alpha_annual | Spread_alpha_t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Headline | 2005-06 to 2015-05 | 120 | 0.1233 | 0.0946 | 0.1124 | 0.7109 | 0.6576 | 0.0102 | 0.0208 | 0.0248 | 1.7643 | 0.0099 | 0.8017 | 0.0205 | 0.5111 |
| Headline | 2015-06 to 2025-12 | 127 | 0.0958 | 0.1234 | 0.1145 | 0.5065 | 0.6319 | -0.0153 | -0.0306 | -0.0383 | -4.1041 | -0.0263 | -2.2981 | -0.0572 | -1.4893 |
| Extension | 2015-06 to 2026-05 | 132 | 0.1063 | 0.1569 | 0.1243 | 0.5543 | 0.6811 | -0.0143 | -0.0515 | -0.0325 | -3.1647 | -0.0251 | -2.3123 | -0.0679 | -1.8373 |


For the 2015-06 onward row, the audit's caution about the t-stat applies: Newey-West with 12 lags on this few months overstates significance somewhat, and random portfolios from this universe also averaged a negative alpha in the shorter window. The audit reran that testing on this window: a fair t is about -2.7 to -3.25, and the alpha sits at 1.7% of random portfolios but 12.5% of those keeping High's sector mix (verification/data_audit_post_writeup.md).


## Year by year

| holding_year | months | High | Middle | Low | Spread | Benchmark | High_minus_Benchmark | High_beats_Benchmark |
|---|---|---|---|---|---|---|---|---|
| 2005-06 | 12 | 0.1958 | 0.1558 | 0.1245 | 0.0713 | 0.1656 | 0.0303 | True |
| 2006-07 | 12 | 0.2246 | 0.2261 | 0.1282 | 0.0964 | 0.2202 | 0.0044 | True |
| 2007-08 | 12 | 0.0612 | -0.0086 | -0.1413 | 0.2024 | -0.0002 | 0.0613 | True |
| 2008-09 | 12 | -0.2953 | -0.3252 | -0.3844 | 0.0892 | -0.3244 | 0.0291 | True |
| 2009-10 | 12 | 0.2571 | 0.2742 | 0.4135 | -0.1564 | 0.2907 | -0.0336 | False |
| 2010-11 | 12 | 0.377 | 0.3378 | 0.3357 | 0.0413 | 0.3465 | 0.0305 | True |
| 2011-12 | 12 | -0.0383 | -0.0556 | -0.0739 | 0.0356 | -0.0495 | 0.0112 | True |
| 2012-13 | 12 | 0.2858 | 0.2938 | 0.2444 | 0.0414 | 0.2902 | -0.0045 | False |
| 2013-14 | 12 | 0.2195 | 0.2369 | 0.3417 | -0.1223 | 0.2461 | -0.0267 | False |
| 2014-15 | 12 | 0.1192 | 0.1295 | 0.2613 | -0.1421 | 0.1366 | -0.0174 | False |
| 2015-16 | 12 | -0.006 | 0.0005 | -0.0872 | 0.0812 | -0.0094 | 0.0034 | True |
| 2016-17 | 12 | 0.1521 | 0.2024 | 0.1365 | 0.0156 | 0.1871 | -0.035 | False |
| 2017-18 | 12 | 0.1107 | 0.1598 | 0.2864 | -0.1757 | 0.1615 | -0.0508 | False |
| 2018-19 | 12 | -0.0514 | 0.0433 | -0.0198 | -0.0317 | 0.02 | -0.0715 | False |
| 2019-20 | 12 | 0.0788 | 0.1239 | 0.3585 | -0.2796 | 0.1299 | -0.051 | False |
| 2020-21 | 12 | 0.3532 | 0.4394 | 0.6531 | -0.3 | 0.4591 | -0.1059 | False |
| 2021-22 | 12 | -0.005 | -0.048 | -0.0918 | 0.0868 | -0.0498 | 0.0448 | True |
| 2022-23 | 12 | -0.0412 | -0.0012 | 0.0954 | -0.1366 | -0.0041 | -0.0371 | False |
| 2023-24 | 12 | 0.2323 | 0.2015 | 0.1647 | 0.0676 | 0.2017 | 0.0306 | True |
| 2024-25 | 12 | 0.1437 | 0.104 | -0.1094 | 0.2531 | 0.0932 | 0.0506 | True |
| 2025-26 (CRSP to Dec 2025, Compustat Jan-May 2026) | 12 | 0.2828 | 0.2186 | 0.6399 | -0.3572 | 0.2709 | 0.0118 | True |


## January-May 2026 alone

**Five months say little.** They are one short window, in a later part of a single holding year, from a different data source, and with no test of significance.

| portfolio | jan_may_2026 | 2026-01 | 2026-02 | 2026-03 | 2026-04 | 2026-05 |
|---|---|---|---|---|---|---|
| High | 0.1536 | 0.0348 | 0.0385 | -0.0836 | 0.081 | 0.0836 |
| Middle | 0.1112 | 0.021 | 0.0331 | -0.0569 | 0.0669 | 0.047 |
| Low | 0.4507 | 0.0853 | 0.0448 | -0.0032 | 0.2014 | 0.0683 |
| Benchmark | 0.1516 | 0.0298 | 0.0354 | -0.057 | 0.0839 | 0.0567 |
| Spread | -0.2971 | -0.0506 | -0.0063 | -0.0804 | -0.1204 | 0.0153 |


## Named events

| name | month | event | bucket | rows_after_in_raw |
|---|---|---|---|---|
| COMCAST CORP | 2026-01 | spin-off (used as given) | Middle |  |
| BECTON DICKINSON & CO | 2026-02 | spin-off (used as given) | Middle |  |
| HOLOGIC INC | 2026-04 | acquisition: final return, then pro rata | High | 0.0 |
| COTERRA ENERGY INC | 2026-05 | acquisition: final return, then pro rata | Middle | 0.0 |


Becton Dickinson's and Comcast's spin-off months are used as given. Compustat and CRSP differ at such months, and CRSP cannot check these two. Whether each is a spin-off is from the audit's reading.


## Sensitivities (reported only; no rule changes)

| run | High_jan_may | Low_jan_may | Benchmark_jan_may | High_CAGR | Benchmark_CAGR | High_minus_Benchmark_annual | High_alpha_annual | High_alpha_t | Spread_alpha_annual | Spread_alpha_t | alpha_2015_on | alpha_2015_on_t | hit_years |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base | 0.1536 | 0.4507 | 0.1516 | 0.1144 | 0.1186 | -0.0026 | -0.0047 | -0.4219 | -0.0283 | -1.0085 | -0.0325 | -3.1647 | 11 |
| Spin-off months at price-only return | 0.1536 | 0.4507 | 0.1509 | 0.1144 | 0.1186 | -0.0026 | -0.0047 | -0.4219 | -0.0283 | -1.0085 | -0.0325 | -3.1647 | 11 |
| Hologic and Coterra final returns +494 bp | 0.1544 | 0.4507 | 0.1519 | 0.1144 | 0.1186 | -0.0026 | -0.0046 | -0.4197 | -0.0282 | -1.0078 | -0.0324 | -3.1645 | 11 |
| Hologic and Coterra final returns -494 bp | 0.1528 | 0.4507 | 0.1512 | 0.1143 | 0.1186 | -0.0026 | -0.0047 | -0.424 | -0.0283 | -1.0091 | -0.0325 | -3.1648 | 11 |


Price-only ignores the distribution altogether, so it is a deliberately harsh lower case for the two spin-off months, not an estimate. The 494 bp is the 95th percentile of absolute gaps at past exits, from `validation.md`, applied to both final returns at once.


## Limits

- Compustat 2026 rows can be revised, and they cannot be compared with CRSP until CRSP covers 2026.
- The extended full-period figures mix two sources. Use the headline as the result of record.
- Adding a few months to a 20-year test can't change much by itself; the new information is only these five months.
