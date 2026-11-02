# REIT liquidity substitute cross-check: independent build vs Agent 1

**Result:** the two builds match. No month differs by more than 1 basis point (bp; 1 bp = 0.01%), so there are no differences to explain.

**Status of this run:** a labelled variant, not the headline and not a blind test, because the rule was set after similar variants had been seen. June 2005 to December 2025 on CRSP; the 2025 portfolio is partial. **Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy).

**Files compared:** `output/reit_liquidity_substitute/portfolio_returns.csv` (SHA-256 starts 606E5717; unchanged at the end), `formation.parquet`, `rows_added.csv` and the other tables. My numbers were final before I opened them. I did not read `09_reit_liquidity.py`.

**Terms:** a REIT is a real estate investment trust. `che` is cash and short-term investments; `lt` is total liabilities. Alpha is the annual return left after six factors. A t-stat beyond about ±2 is conventionally significant.

## 1. Comparison

| Item | Result |
|---|---|
| Membership, 8,001 list rows on 21 dates | Identical |
| Bucket, score, fiscal year, availability date, REIT flag | 0 differences |
| REIT rows added | 430 in both, same rows and scores |
| Headline rows changed by the variant | None in either build: all 7,571 keep their score and year |
| Monthly gross and net: High, Middle, Low, Benchmark, Spread | Largest gap about 0.000000000003 bp; 0 months over 1 bp |
| Turnover, 84 values | Match |
| Full-period and subperiod alphas and t-stats | Match to rounding |
| Hit rate | 10 of 20 complete years in both; High also beats the Benchmark in partial 2025 on my numbers |

## 2. Numbers (net of costs, identical in both builds)

| Measure | Headline | Variant |
|---|---|---|
| High alpha, annual (t) | -0.78% (-0.71) | -1.01% (-0.91) |
| High alpha, 2005-06 to 2015-05 (t) | +2.48% (+1.76) | +2.43% (+1.75) |
| High alpha, 2015-06 to 2025-12 (t) | -3.83% (-4.10) | -4.24% (-4.40) |
| Spread alpha (t) | -2.04% (-0.72) | -2.21% (-0.82) |
| Spread alpha, 2015-06 to 2025-12 (t) | -5.72% (-1.49) | -6.08% (-1.64) |
| High minus Benchmark, annual | -0.29% | -0.30% |
| High CAGR | 10.91% | 10.63% |
| Benchmark CAGR | 11.35% | 11.06% |
| High Sharpe | 0.60 | 0.59 |
| Benchmark Sharpe | 0.65 | 0.63 |
| High beats Benchmark, complete years | 10 of 20 | 10 of 20 |

**Plain reading:** adding back most REITs does not change the answer. High still shows no significant full-period alpha, and the gap to the Benchmark barely moves, because the REITs lower both High and the Benchmark by similar amounts. Section 8c's caution on the 2015-25 t-stat applies. The random-portfolio work behind it was not rerun on this variant.

## 3. REIT rows added

430 rows, 44 companies: High 61, Middle 302, Low 67.

| Rows | Companies |
|---|---|
| 21 | AvalonBay, Simon Property, Prologis, Equity Residential, Public Storage |
| 16-18 | BXP, Ventas, Healthpeak, Host Hotels, Welltower, Digital Realty, Kimco |
| 10-15 | Vornado, Realty Income, Brookfield Property REIT, Essex, Extra Space, UDR, Macerich, Federal Realty, Mid-America, SL Green |
| 5-8 | Alexandria, Sun Communities, Duke Realty, Invitation Homes, VICI, Camden, Regency Centers, Weyerhaeuser, W. P. Carey |
| 1-4 | SITE Centers, AMB Property, Equity LifeStyle, American Homes 4 Rent, Archstone, VEREIT, Equity Office, Nationwide Health, Brixmor, NNN REIT, Medical Properties Trust, Gaming & Leisure, Rexford |

Names are Compustat's current names, so some differ from the name in use at the time. The full list by date is in `output/reit_liquidity_substitute/rows_added.csv`, which matches my `reit_formation.parquet`.

**Still unscored:** 2 of the 512 included REIT rows, in both builds: Invitation Homes 2018 and VICI Properties 2019. Another signal cannot be computed for each. The null `che` and non-positive `lt` rule drops nothing, because no eligible company-year fails it.

## 4. Spot checks from raw values

The results below were computed from raw Compustat values with each formula written out, and they match the build. Detail is in `reit_spot_checks.txt`.

| Company | Formation | Fiscal year | `che` / `lt` against prior year | Substitute signal | Score |
|---|---|---|---|---|---|
| Simon Property | 2015 | 2014 | Fell | 0 | 7, Middle |
| Equity Residential | 2020 | 2019 | Fell | 0 | 7, Middle |
| Public Storage | 2010 | 2009 | Rose | 1 | 8, High |

These catch arithmetic and data errors. They use the same reading of the rule as the build, so they would not catch a misreading. They were not compared with the 10-Ks. Simon's fall in `che` is large, which shows how much the signal can move with financing and deal timing.

## 5. Ambiguities and assumptions

- **Single missing signal:** a year uses the substitute only if F_DLIQUID is the only missing signal.
- **REIT status by date:** this comes from the held security's CRSP issuer type on the formation date, so a company coded as a corporation stays dropped. I have not listed names this affects.
- **Choice of year:** the most recent usable year, with the headline's availability, tie and 18-month age rules.
- **General Growth, May 2009:** held flat in Middle and Benchmark in both builds, the only held null.
- **Measure:** `che` / `lt` is a weaker liquidity measure than the current ratio, because cash can move with financing timing. That is a limit of the approved rule.

## 6. Limits

- I pulled `che` and `lt` myself from WRDS, read-only, but I do not know whether Agent 1's pull used the same query. The matching results suggest the values agree on rows that matter.
- Both builds follow the same written rule, so a shared misreading would still match. Earlier rounds showed that two builds can match while sharing an error, so this result shows consistent implementation only.
- No Agent 1 file, `CLAUDE.md`, `config.py`, `data/` or `output/` file was changed.

**Files:** `verify_reit_liquidity.py`, `compare_labelled_runs.py`, `labelled_runs_compare_raw.txt`, `reit_spot_checks.txt` and the `reit_*` outputs, all in `verification/`.
