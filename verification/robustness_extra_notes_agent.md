# v3 extra robustness: notes (script 27_v3_robustness_extra.py)

Output: output/spec_v3/robustness_extra_v3.csv. Engine copied from 22_v3_robustness.py (literal issuance, equal weight, buy and hold, pro rata exit redistribution, one-sided reinvestment charge, TRANSACTION_COST_BPS, FLAT = NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2"], High vs all-included benchmark). Headline row reproduces portfolio_returns_v2.csv (atol 1e-10): High CAGR 12.00%, benchmark 10.79%, mean gap x12 +1.42%, t 1.03. Every variant High series is asserted different from the headline. Any null return in a held window not covered by an approved hold-flat month stops the run (none occurred).

| variant | High CAGR | Bench CAGR | CAGR gap | mean gap x12 | t |
|---|---|---|---|---|---|
| headline | 12.00% | 10.79% | +1.21% | +1.42% | 1.03 |
| sector_neutral | 12.61% | 10.79% | +1.82% | +1.80% | 1.33 |
| value_filter_B | 7.92% | 10.42% | -2.50% | -1.16% | -0.51 |
| profitability_screen | 12.20% | 10.66% | +1.53% | +1.71% | 1.21 |
| universe_buffer | 11.99% | 10.89% | +1.10% | +1.34% | 0.94 |
| eight_signal_no_liquidity | 11.83% | 10.79% | +1.04% | +1.25% | 0.91 |

## Definitions and interpretations
- sector_neutral: weights for High and benchmark = benchmark (all included that date) sector share, equal within sector, empty sector dropped (pro rata). The benchmark is equal weight already, so its series is identical to the headline benchmark by construction (the assert is on High). gsector null (none among included rows) would be a separate "NA" sector.
- value_filter_B: book equity = ceq + txditc (null = 0) from the same fiscal year as the score; btm = book equity / formation market cap; ranked = scored and USD and btm not null; cheapest third = btm >= exact 2/3 quantile (Fraction 1/3, boundary included, as 05_align.py). High = High bucket inside this set; benchmark = the whole cheapest-third set (own set, as v1). Unscored names cannot be ranked, so they are not in it. Thin: High has as few as 3 names on a date (High_min_names_per_date column); v1 flagged thin buckets the same way.
- profitability_screen: v1 function copied unchanged (niq, latest four consecutive quarters by datadate, quarterly filing date else datadate + 120 days, unconfirmed = fail, latest quarter not older than 18 months). INTERPRETATION: v1 held only scored rows, so its benchmark was scored-only; under v3 the benchmark is all included, so I applied the screen to every included row (scored or not) and the benchmark is the screened all-included set. The quarterly availability rule keeps v1's (filed on or before the formation date, no 3-day buffer, 120-day fallback), because the v3 buffer is defined for annual 10-K dates only.
- universe_buffer: WRDS is unreachable and raw CRSP holds only the top-500-ever names, so the universe was NOT rebuilt. I read output/robustness/universe_buffer/universe.parquet (v1 output; v1 asserted its rebuild path reproduced the headline universe; all its permnos are in crsp_msf_v2 and 99.99% of gvkeys in fundamentals_clean). Rule as locked: first list top 500, then enter at rank <= 450, stay until rank > 550. Scores re-aligned with the v3 literal scores; benchmark = all included names of that universe. Comverse (10942) Feb to May 2007 held flat, the v1 approved rule, added for this variant only.
- eight_signal_no_liquidity: v1 rule under v3 scoring: firm-years with F_SCORE null, F_DLIQUID null and the other 8 signals all computable (plus, to stay in the v3 spec, a real 10-K filing date and not a stub year) get F_SCORE = sum of the 8. Eight-signal buckets: High 8, Low 0-3, Middle 4-7 (config EIGHT_SIGNAL_*); nine-signal rows use the standard High/Low from v3. 644 list rows use 8 signals (High 8, Middle 571, Low 65). Benchmark = all included, so it is unchanged and equals the headline benchmark.

## Constants defined at top of the script (config.py untouched)
EIGHT_SIGNALS (from 08_robustness.py), EIGHT_HIGH = [8], EIGHT_LOW = [0,1,2,3] (config values), VALUE_Q = Fraction(config.VALUE_FILTER_QUANTILE), BUFFER_FLAT = Comverse 10942 for 2007-02 to 2007-05 (config NULL_RETURN_HOLD_FLAT_MONTHS["universe_buffer"]).

## Not done
Universe rebuild from WRDS for the buffer (see above). No scored-only-benchmark variant of the profitability screen (would be an invented variant). Nothing chosen by returns.
