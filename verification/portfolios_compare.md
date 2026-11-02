# Portfolio cross-check: independent Phases 4-6 vs Agent 1

**Result:** no monthly return differs by more than 1 basis point (bp; 1 bp = 0.01%) in any column. Formation membership is identical on all 21 dates and gross returns match exactly. Net returns differ by at most 0.57 bp, in one month, because the builds treat a name that delists in the last month before a rebalance differently. I think Agent 1's version fits the config wording better. The difference changes no conclusion.

**Files compared:** `output/tables/portfolio_returns.csv` (SHA-256 starts B8D0F94A) and `data/clean/formation.parquet` (2EAE1EB7). The hash of `portfolio_returns.csv` was the same when the comparison finished.

**Order of work:** my numbers were final before I saw Agent 1's outputs. I changed no rule afterwards, so the difference below stays in my run.

## 1. Headline results (mine, net of costs)

June 2005 to December 2025, 247 months. Universe: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy). The 2025 portfolio is partial (7 of 12 months).

| Portfolio | CAGR | Volatility | Sharpe | Max drawdown |
|---|---|---|---|---|
| High (scores 8-9) | 10.91% | 16.79% | 0.60 | -44.4% |
| Middle (5-7) | 11.26% | 15.85% | 0.65 | -49.8% |
| Low (0-4) | 10.93% | 19.85% | 0.54 | -61.0% |
| Benchmark (all scored names) | 11.35% | 16.17% | 0.65 | -49.1% |
| RSP (equal-weight S&P 500 fund) | 9.85% | 17.00% | 0.54 | -55.6% |
| SPY (S&P 500 fund) | 10.88% | 14.90% | 0.66 | -50.8% |

CAGR is the compound annual growth rate. Sharpe is excess return per unit of risk. Alpha below is the return left after accounting for the market, size, value, profitability, investment and momentum factors. A t-stat beyond about ±2 is conventionally significant.

| Measure, net | Full period | 2005-06 to 2015-05 | 2015-06 to 2025-12 |
|---|---|---|---|
| High alpha, annual (t-stat) | -0.78% (-0.71) | +2.48% (+1.76) | -3.83% (-4.10) |
| Spread (High minus Low) alpha, annual (t-stat) | -2.04% (-0.72) | +2.05% (+0.51) | -5.72% (-1.49) |
| Benchmark alpha, annual (t-stat) | +0.18% (+0.25) | +1.49% (+1.67) | -1.20% (-1.63) |

- **High against the Benchmark:** -0.29% a year (arithmetic), information ratio -0.08. High beat the Benchmark in 10 of 20 complete years, and also in partial 2025.
- **By score:** average annual return is not monotonic, meaning it does not rise steadily with the score. Scores 3 to 9 give 14.4%, 13.6%, 12.6%, 11.7%, 13.3%, 12.0%, 13.6%. Scores 0 to 2 average under 3 names and are too thin to read.

**Plain reading:** buying the highest F-score names did not beat the equal-weighted universe over the full period, and no alpha survives the factor adjustment. The first decade is mildly positive but not significant. The second decade is significantly negative for High. Part of that negative figure is shared by the Benchmark, whose own alpha was also negative in that decade.

## 2. Comparison

| Item | Result |
|---|---|
| Formation membership, 8,414 list rows on 21 dates | Identical |
| Score, fiscal year, score age, availability date, valid/missing/stale status | 0 differences (7,571 / 794 / 49) |
| Book-to-market | 0 differences |
| Value tercile (version B only) | Labels reversed, plus 13 boundary names, see section 4 |
| Gross monthly returns: High, Middle, Low, Benchmark, Spread | Match to machine precision |
| RSP and SPY monthly | Exact match |
| Net monthly returns | Largest 0.57 bp; 0 months over 1 bp; 21 column-months over 0.01 bp |
| Turnover | 84 values compared, 19 differ, see section 3 |
| Factor regressions, full period | Alphas match to 6 decimals; High net t-stat -0.7145 vs -0.7146; betas within 0.00002 |
| Subperiod High and Spread alphas | Match to rounding |
| Performance table | CAGR within 0.03 bp; volatility and drawdown effectively identical; Sharpe within 0.00002 |
| Year-by-year | Largest 0.52 bp (Low and Spread); no change in which years High beat the Benchmark |
| By-score returns, gross, complete years | Match |

The only reported gaps come from definitions, not calculations:
- **Average turnover:** my `portfolio_performance.csv` includes the 2005 purchase and Agent 1's excludes it. Without 2005, mine are High 1.638, Middle 0.811, Low 1.761, Benchmark 0.341; Agent 1's are 1.639, 0.811, 1.758, 0.341.
- **2005 one-way turnover:** Agent 1 reports 1.0 and I report 0.5. Agent 1's is the sensible figure, since buying from cash is all one way. Costs are unaffected, because both use two-way turnover of 1.0.

## 3. The one calculation difference: delisting in the last month before a rebalance

**Cause:** a name can delist during the final May of a holding year, earning its last return in that same month.
- **My build** removes it from the prior weights, so its value spreads to the rest before turnover is measured.
- **Agent 1's build** keeps it in the end-of-May drifted weights, so the rebalance treats it as a sale.

I read only the relevant lines of `06_portfolios.py`, not the whole script. Its logic is consistent with this cause, and all 19 turnover differences fall on exactly the bucket-years with such a name:

| Rebalance | Names | Buckets affected |
|---|---|---|
| 2006 | Liberty Media | Middle, Benchmark |
| 2007 | Kinder Morgan Inc Kansas | Middle, Benchmark |
| 2010 | CNX Gas | High, Benchmark |
| 2011 | Pride International | Low, Benchmark |
| 2012 | El Paso | Middle, Benchmark |
| 2015 | TRW Automotive | Middle, Benchmark |
| 2016 | Time Warner Cable; Coca-Cola Enterprises and others | High, Middle, Benchmark |
| 2017 | Valspar | Middle, Benchmark |
| 2024 | Pioneer Natural Resources | Middle, Benchmark |

**Largest effect:** Low in June 2011, -0.57 bp in my net return. Pride was in Low in both 2010 and 2011 and delisted in May 2011. My build counts its 1/21 target as a fresh purchase (turnover 1.848). Agent 1 sees it as already held (1.792). All other months are under 0.08 bp.

**Which follows the config:** Agent 1's, in my view. `TURNOVER_BASIS` says "sum of |target - drifted weight|", and an end-of-May weight is a drifted weight. Agent 1's treatment also avoids charging a full purchase on a formation-date delister that was already held, which suits the comment on `CHARGE_MIDPERIOD_REINVESTMENT`. My treatment is a defensible reading of `DELISTING_RULE`, but I would use Agent 1's. Its cost: Agent 1's version charges a "sale" of a stock that has already gone. Across the test, the choice moves Low's CAGR by 0.03 bp and High's by under 0.01 bp.

## 4. Value terciles (version B only, no effect on the headline)

- **Labels:** my tercile 3 is the highest book-to-market; Agent 1's tercile 1 is. Each is internally consistent, and Agent 1's `in_version_b` correctly takes its tercile 1.
- **13 boundary names differ after reversing labels:** my rule rounds ranks differently when a date's count does not divide by 3. In my cheapest third but not Agent 1's (7): Coventry 2007, Bath & Body Works 2008, Constellation Brands 2014, Target 2016, Cerner 2021, AMD 2023, TransUnion 2025. In my middle third but Agent 1's most expensive (6): Dollar Tree 2010, DuPont 2013, Texas Instruments 2015, Fortive 2018, Tractor Supply 2019, Visa 2022.
- **Which follows the brief:** neither; config says one-third and sets no boundary rule. The version-B run should state Agent 1's rule. Its cheapest third has 2,523 list rows against my 2,530.

## 5. Assumptions and ambiguities

The two builds reached the same answer on all of these separately, except where section 3 says otherwise.

| Issue | Treatment |
|---|---|
| First holding month | The month after formation; holding runs June to May |
| Partial 2025 | June to December 2025; no sale or exit cost at the end; excluded from the 20-year hit rate and by-score averages |
| Drift | Value x (1 + monthly return); monthly return is the value-weighted average of names with a row that month |
| Mid-period exit | Final return includes the delisting return; value then spreads pro-rata by current value, uncharged |
| Not-trading rows (null return) | Mine: held at 0 return. No held name hits one, so this has no effect |
| Formation-date delisters (CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017) | Count at 1/N in the turnover target, earn nothing, weight respreads free. Waste Connections continues under a new PERMNO and neither build follows it |
| Most recent score | Scored years only. 13 list rows use an older year because the later year has no score |
| Spread regression | High minus Low with no risk-free deduction |
| Newey-West standard errors | Lag 12, no small-sample correction. Agent 1's t-stats match mine, so the setting appears the same |

**Open items:**
- Charging a 1/N purchase on a formation-date delister follows my reading of a comment in config. Both builds do it, and it is a small cost.
- Waste Connections 2016 is treated as an exit although the company continued, with cash spread to the rest. Both builds do this. Its effect on returns was not measured.

## 6. Limits

- Both builds use the same scores, universe and locked mechanics, so the match shows the calculations are consistent. It does not test the rules themselves or the source data.
- My script was written without reading Agent 1's Phase 4-6 code, but the coordinator locked several mechanics in config during my build. Those choices were not independent.
- Sharpe and drawdown use my stated definitions, and they match Agent 1's.
- I did not start `08_robustness.py`. No Agent 1 file, `CLAUDE.md`, `config.py` or `data/` file was changed.

## 7. Files

In `verification/`: `verify_portfolios.py`, `compare_portfolios.py`, `portfolios_compare_raw.txt`, `portfolio_independent_log.txt`, and the `portfolio_*` output tables.
