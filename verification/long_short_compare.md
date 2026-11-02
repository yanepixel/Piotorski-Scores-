# Long/short 100/100 cross-check: independent build vs Agent 1

**Result:** the two builds match. No month differs by more than 1 basis point (bp; 1 bp = 0.01%) in any monthly series Agent 1 published. Both follow config, using NAV before the charge as the June cost base.

**One correction on my side:** the comparison caught a bug in my script, which I then fixed. For the window to May 2026, my 2015-on alpha stopped at December 2025 instead of May 2026. Agent 1's figures were right, and my corrected figures match them. See section 3.

**Status of this run:** a labelled variant, not the headline and not a blind test, because the spread had already been seen. The borrow fee is a flat assumption, not data. Returns from January 2026 are Compustat's. **Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy).

**Files compared:** `output/long_short_100_100/`: `results.md` (FB6CDCC7), `nav_main.csv` (B54BDC0D), `nav_extension.csv` (62F1B0C1), all unchanged at the end, and its other tables. I did not read `11_long_short.py`.

**Terms:** NAV is the capital in the strategy. CAGR is compound annual growth. Sharpe is return above the risk-free rate per unit of risk. Alpha is the annual return left after six factors. A t-stat beyond about ±2 is conventionally significant. Drawdown is the largest peak-to-trough fall.

## 1. Comparison

| Item | Result |
|---|---|
| Monthly returns: 0.50% and 2.00% fee, annual reset, both windows | Largest gap about 0.000000000005 bp; 0 months over 1 bp |
| Monthly returns: 0.50% fee, monthly reset, to December 2025 | Same |
| Cost, long, short, cash and NAV values each month, 0.50%, to May 2026 | Match to rounding |
| Performance and alpha: all 4 runs at each of both windows, plus long-only High | Match to rounding |
| Subperiods | Match after the correction in section 3 |
| Drags: costs, borrow, stress borrow, shares of NAV | Match |
| Year by year: return and all five pieces, both windows | Match |

**Not compared month by month:** Agent 1's files have no monthly series for the monthly-reset runs at 2.00%, or for monthly reset in the window to May 2026. Those runs match on summary figures only. I also did not check every column of `spread_comparison.csv`.

## 2. Numbers (identical in both builds, after the correction)

| Run, annual reset unless stated | CAGR | Volatility | Sharpe | Max drawdown | Alpha (t) | $1 becomes |
|---|---|---|---|---|---|---|
| **To December 2025 (CRSP)** | | | | | | |
| Long/short, 0.50% fee | -1.80% | 12.27% | -0.22 | -75.8% | -4.53% (-1.48) | $0.69 |
| Long/short, 2.00% fee | -3.43% | 12.42% | -0.35 | -80.7% | -6.18% (-1.98) | $0.49 |
| Monthly reset, 0.50% fee | -0.31% | 10.41% | -0.14 | -67.0% | -2.89% (-1.03) | $0.94 |
| Monthly reset, 2.00% fee | -1.79% | 10.41% | -0.28 | -73.0% | -4.39% (-1.56) | $0.69 |
| Long-only High | 10.91% | 16.79% | 0.60 | -44.4% | -0.78% (-0.71) | $8.42 |
| **To May 2026 (Compustat from January 2026)** | | | | | | |
| Long/short, 0.50% fee | -3.59% | 13.11% | -0.34 | -75.8% | -5.80% (-1.86) | $0.46 |
| Long/short, 2.00% fee | -5.23% | 13.28% | -0.47 | -80.7% | -7.49% (-2.35) | $0.32 |
| Monthly reset, 0.50% fee | -1.44% | 10.81% | -0.24 | -67.0% | -3.67% (-1.31) | $0.74 |
| Monthly reset, 2.00% fee | -2.91% | 10.81% | -0.38 | -73.0% | -5.17% (-1.85) | $0.54 |
| Long-only High | 11.44% | 16.92% | 0.63 | -44.4% | -0.47% (-0.42) | $9.72 |

| Alpha, annual reset (t) | 2005-06 to 2015-05 | 2015-06 to 2025-12 | 2015-06 to 2026-05 |
|---|---|---|---|
| Long/short, 0.50% fee | +0.02% (+0.00) | -8.68% (-1.95) | -10.31% (-2.35) |
| Long/short, 2.00% fee | -1.56% (-0.37) | -10.42% (-2.29) | -12.09% (-2.69) |

| Drag a year | To Dec 2025 | To May 2026 |
|---|---|---|
| Trading costs | 33.5 bp | 32.2 bp |
| Borrow at 0.50% | 54.2 bp | 54.7 bp |
| Borrow at 2.00% | 216.9 bp | 219.0 bp |
| CAGR with no costs and no fee | -0.92% | -2.72% |

**Year by year:** return was positive in 12 of 20 complete years to December 2025 (11 of 20 at 2.00%), and 12 of 21 to May 2026 (11 of 21). The worst complete year to December 2025 is 2020-21 at -30.9%. To May 2026 it is 2025-26 at -32.7%, when the short leg cost 64 points. The full table is in `results.md`, and matches mine.

**Loadings to December 2025, 0.50% fee:** market 0.00, size -0.25, value 0.06, profitability 0.52, investment 0.07, momentum 0.03, R² 0.16. So the position is close to market-neutral, with a tilt toward profitable companies.

**Plain reading:** the strategy lost money even before fees and costs. Its full-period alpha is negative, and significant only at the 2.00% fee in the window to May 2026. Most of the loss comes in the second decade, when the Low stocks being shorted rose strongly. Long-only High did far better in absolute terms because it kept market exposure, and this variant removes that exposure. Five extra months make a large difference only because Low rose about 45% in them, and that came largely from two stocks (see `extension_2026_compare.md`). Section 8c's caution on subperiod t-stats applies, and the random-portfolio test was not rerun here.

## 3. The correction

| 2015-06 to 2026-05 alpha | My first run (wrong) | Corrected, equal to Agent 1 |
|---|---|---|
| 0.50% fee | -8.68% (-1.95) | -10.31% (-2.35) |
| 2.00% fee | -10.42% (-2.29) | -12.09% (-2.69) |

**Cause:** my script capped the last subperiod at the config's December 2025 date in every window, although my stated assumption was "to the end of each run". The gap was about 162 to 167 bp a year of alpha. No other summary column changed; I compared the runs to confirm. No monthly return was affected, and I had not sent these figures to anyone.

**Which follows config:** Agent 1's. The first run is on record in `ls_summary_run1_subperiod_bug.csv` and `long_short_compare_raw_run1.txt`.

This shows why the comparison is useful, but my numbers in that one column were not final before I saw Agent 1's tables.

## 4. Checks against a shared wrong formula

- **Dollar hand-checks** (`ls_hand_check.txt`), from a $100,000,000 base:
  - June 2009: cost on each leg, NAV after the charge, then long gain, short loss, interest and fee. Matches to within $0.01.
  - March 2009: drifted legs of about $50.4m long and $41.1m short against $100m NAV, so cash is about $90.8m. Matches to within $0.01.
- **Balance-sheet ledger:** moving each position separately agrees with the P&L formula to about 2e-15.
- **Mechanics test:** with free monthly reset and no fee or cost, return above the risk-free rate equals gross High minus Low to 1.9e-16. Agent 1 reports the same test.

These confirm the accounting does what the brief says. They use my reading of the rule, so they would not catch a shared misreading, and they cannot show that the rule itself is realistic.

## 5. Assumptions and what favours the result

Both builds made the same choices on all of these.

| Issue | Treatment | Direction |
|---|---|---|
| June cost base | NAV before the charge | Basing cost on pre-reset leg values instead lowers CAGR by about 5.5-6.3 bp a year |
| Resizing legs to NAV each June | No separate charge, per the brief | Favourable; the legs can be far from NAV by May |
| Cash interest | Full risk-free rate, including on short proceeds; no margin or recall | Favourable; a real prime broker keeps part of this |
| Borrow fee | Flat rate for every name and date | Probably favourable; hard-to-borrow names cost more |
| Monthly reset | Free outside June | Favourable by definition; reported only |
| Exposure between Junes | Legs drift, so not 100/100 except at reset | In March 2009, for example, long and short were well below NAV |
| Short delisting | Taken at face value through Low's return | Neither way in general |
| End of test | No closing cost and no June 2026 rebalance | Slightly favourable |

Alpha here uses return minus the risk-free rate, because this is a funded account. The headline Spread alpha makes no such deduction, so the two are not directly comparable. As `results.md` says, the published net Spread column also credits Low's trading costs, while this run charges them.

## 6. Limits

- Both builds use the same verified High and Low series, turnover, factor file and written rule. A shared misreading or an error upstream would still match.
- The window to May 2026 mixes two data sources. Compustat 2026 returns cannot be checked against CRSP, and the short leg's result in that window relies heavily on a few large moves.
- No Agent 1 file, `CLAUDE.md`, `config.py`, `data/` or `output/` file was changed.

**Files:** `verify_long_short.py`, `compare_long_short.py`, `long_short_compare_raw.txt`, `ls_hand_check.txt`, and the `ls_*` outputs, all in `verification/`.
