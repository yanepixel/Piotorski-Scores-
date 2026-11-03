# Piotroski F-score test: write-up (headline specification: spec_v2)

**Universe:** Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)

**Test period:** June 2005 to December 2025. The test ends before 2026, and the last portfolio is partial (7 of its 12 months).

This repository holds the code, the write-up and summary tables only. Licensed WRDS data is not included, and neither are the detailed files derived from it. Files named in the text but not present here, such as logs and monthly or company-level tables, are produced when you run the scripts with your own WRDS access. A few company-level cells were removed from the published summaries, so a rerun will show more than this copy does. The spec_v2 stock-level files (monthly portfolio returns, exits, turnover, formation lists, scores and the per-company reasons behind the drop counts) are likewise not included; the scripts `12a` to `17` produce them. Audit reports and the scripts that produced them, named in the text, are not all here. Do not commit reruns from a copy of this repository, because a rerun restores detail files and values left out here.

**Status of this document.** spec_v2 is the headline. It re-specifies the first version (v1) after an external review; v1 is kept unchanged as the superseded first specification in `output/archive_v1/` and is compared with v2 below. The three later runs (2026 extension, REIT liquidity substitute, 100/100 long/short) were run on the v1 specification and have not been rerun under v2.

## The answer

No. Buying the financially strongest companies in this universe, those with an F-score (a 0-9 count of financial-health tests a company passes) of 8 or 9, did not beat the market of the same stocks. Measured against an equal-weighted portfolio of every included company, High (the portfolio of companies scoring 8 or 9) earned +0.08% a year more after costs (t-stat, the number of standard errors the estimate sits from zero, +0.10; p-value, the chance of a result at least this far from zero if the true edge were zero, 0.92). After accounting for market, size, value and momentum, its alpha (the return left over once those patterns are removed) was -0.15% a year (t -0.13). Neither is distinguishable from zero, and this test could not have seen a small edge: at 80% power (the smallest true effect the test would detect 80% of the time) the smallest excess return it could reliably detect is 2.13% a year, and the 95% range for the excess is -1.42% to +1.57%, so a true edge of up to about +1.6% a year cannot be ruled out. The benchmark choice matters to the sign: against scored companies only, High's excess is -0.42% a year (t -0.56), because the unscored companies (mostly REITs and real estate) lagged. High beat the all-included benchmark in 9 of 20 complete years. In the second half, June 2015 to December 2025, High's four-factor alpha was -3.38% a year (t -2.70); it is the only one of the six pre-specified tests that survives the Holm adjustment (a correction for looking at several tests at once; adjusted p 0.047), narrowly, and not under every way of computing the standard error (Newey-West, which allows for returns correlated over time, with a choice of how many months to allow; see Results). With the opposite sign in 2005-15, that is weak evidence of a later-period shortfall, not a finding of failure. This tests large US companies, not the cheap, smaller companies Piotroski studied, so it does not test his original claim.

## Terms

- **F-score:** a 0-9 count of financial-health tests a company passes, from its latest annual report.
- **High, Middle, Low:** portfolios of scores 8-9, 5-7 and 0-4.
- **All-included benchmark (primary):** every company on the list, scored or not, equally weighted, run the same way and charged the same costs.
- **Scored-only benchmark:** the scored companies only. This is the v1 benchmark; both are shown together throughout.
- **Net / gross:** after / before trading costs.
- **CAGR:** the constant yearly growth rate that gives the same end value.
- **Volatility:** how much monthly returns swing, stated per year.
- **Sharpe ratio:** return above the risk-free rate per unit of volatility. Higher is better.
- **Max drawdown:** the largest peak-to-trough fall.
- **Turnover:** the share of a portfolio traded at a rebalance. Two-way counts buys and sells.
- **Excess return:** return above the benchmark, here the average monthly gap times 12.
- **Tracking error / information ratio:** how much the gap swings per year; excess return divided by that.
- **Factor:** a broad return pattern: market (Mkt-RF), size (SMB), value (HML), momentum (MOM); profitability (RMW) and investment (CMA) enter only the secondary six-factor version.
- **Alpha:** return left after accounting for those factors, stated per year.
- **t-stat / p-value:** how many standard errors a number is from zero; the chance of a result at least this far from zero if the true value were zero.
- **Newey-West (HAC):** standard errors adjusted for returns that are correlated over time. The number of months allowed (the lag) is set by a formula, 4 here.
- **Degrees of freedom / t distribution:** the t distribution is the bell-shaped curve used to turn a t-stat into a p-value when the sample is limited; its degrees of freedom, T - k, are the T months less the k coefficients estimated, and fewer degrees of freedom mean fatter tails.
- **T/(T-k) correction:** an optional small-sample adjustment that multiplies the variance of the estimates by T / (T - k); it is reported as a sensitivity, not used in the headline.
- **Compustat / CRSP:** two commercial databases, accessed through WRDS: Compustat holds company accounts (the annual reports), and CRSP (Center for Research in Security Prices) holds monthly stock prices and returns, including delistings.
- **RSP and SPY:** exchange-traded funds that track the equal-weighted and the cap-weighted S&P 500, shown for context only.
- **Formation date / list row:** the formation date is the last trading day of May, when the portfolios are formed; a list row is one company on one formation date's list.
- **Holm adjustment:** a correction for looking at several tests at once; it raises p-values so that the chance of any false positive in the family stays at 5%.
- **Power / minimum detectable effect:** the smallest true effect the test would detect 80% of the time at the 5% level.
- **REIT:** real estate investment trust, a company that mainly owns property or property loans and passes most income to shareholders.
- **GICS:** the Global Industry Classification Standard, the sector system used here.
- **Availability date:** the first date a number could be used: the 10-K filing date plus 3 calendar days. A firm-year with no real filing date is not scored.
- **Stub year:** a fiscal year with an unusual length, usually from changing the year-end.
- **Spread:** High minus Low, a diagnostic only, with no shorting costs.

## Method

All rules are in `config.py` (`SPEC_V2`) and the decisions in `CLAUDE.md` section 8f, which were committed before any v2 return was read; the exact sequence is under Timing of the specification. The universe, formation dates, buckets and holding period are unchanged from v1.

- **Universe:** on the last trading day of each May, 2005-2025, the top 500 US-incorporated common stocks on NYSE, Nasdaq or NYSE American by market cap, rebuilt from data on that date. Financials and utilities are removed after ranking.
- **Scores:** the nine Piotroski tests from Compustat annual data (company accounts), fiscal years 2004-2024, with five changes from v1: (1) profitability and accruals use income before extraordinary items (`ib`), as in the paper, not net income; (2) the no-issuance test is passed when common stock issued less common stock repurchased (`sstk - prstkc`) is zero or negative, with a missing value counting as zero and negative values used as reported, instead of v1's share-count test with a 2% tolerance; (3) a no-debt company passes the leverage test only where the prior-year change is computable; (4) a firm-year with no real 10-K filing date is not scored, with no year-end-plus-120-days fallback; (5) a filing counts only if its date plus 3 calendar days is on or before the formation date (an assumption). If the newest year fails the date test, the latest earlier scored year is used if no more than 18 calendar months old. Leverage uses long-term debt only, as in v1. Any uncomputable signal still drops the company-year.
- **Portfolios:** equal weight at formation, held 12 months from June. Returns come from CRSP (monthly stock prices) and include delisting returns, and a delisted stock's value goes pro rata to the rest.
- **Costs:** 10 basis points (0.10%) on each dollar bought or sold at each rebalance, and also on the value reinvested after a mid-period exit, charged one side in the exit month (v1 did not charge this). High's costs averaged 0.17% a year, of which 0.002% is reinvestment.
- **Benchmarks:** primary = all included names, scored or not, held with their actual returns and charged like the buckets; the scored-only benchmark is reported beside it. RSP and SPY are fund returns (exchange-traded funds tracking the equal-weighted and the cap-weighted S&P 500). Two included names with no return for some months and no exit (Maxim Integrated, November 2007 to May 2008; General Growth Properties, May 2009) are held flat at 0%, uncharged, in the all-included benchmark only; any other missing return would have stopped the run.
- **Tests:** two primary tests of High, set in `SPEC_V2`: (1) its raw annualised excess return over the all-included benchmark; (2) its alpha on market, size, value and momentum. Standard errors are Newey-West with the automatic lag floor(4 x (T/100)^(2/9)), which is 4 for the full period and for each subperiod (T = 247 months in total), with p-values from a t distribution with T - k degrees of freedom (the T months less the k coefficients estimated). Holm adjustment is over one family of six p-values: the two tests times the full period and the two subperiods. The six-factor alpha is secondary because the profitability factor overlaps the screen. Power is reported at 80% and 5% two-sided.

## Results

All figures are net of costs. June 2005 to December 2025, 247 months. Both benchmarks are shown together; v1 is the first specification.

| Portfolio | CAGR | Volatility | Sharpe | Max drawdown | Average two-way turnover | v1 CAGR | v1 Sharpe |
|---|---|---|---|---|---|---|---|
| High (8-9) | 10.75% | 16.96% | 0.59 | -45.7% | 166% | 10.91% | 0.60 |
| Middle (5-7) | 11.41% | 15.88% | 0.66 | -49.1% | 80% | 11.26% | 0.65 |
| Low (0-4) | 10.19% | 18.89% | 0.52 | -56.9% | 174% | 10.93% | 0.54 |
| All-included benchmark | 10.79% | 16.26% | 0.61 | -50.6% | 33% | n/a | n/a |
| Scored-only benchmark | 11.36% | 16.17% | 0.65 | -49.2% | 34% | 11.35% | 0.65 |
| RSP | 9.85% | 17.00% | 0.54 | -55.6% | n/a | 9.85% | 0.54 |
| SPY | 10.88% | 14.90% | 0.66 | -50.8% | n/a | 10.88% | 0.66 |

v1's 'Benchmark' is the scored-only benchmark, so it sits beside that row. v1 does not charge the reinvestment of mid-period exits.

| Portfolio | Excess vs all-included | t | Tracking error | Information ratio | Excess vs scored-only | t |
|---|---|---|---|---|---|---|
| High | +0.08% | +0.10 | 4.13% | +0.02 | -0.42% | -0.56 |
| Middle | +0.50% | +1.52 | 1.47% | +0.34 | +0.01% | +0.02 |
| Low | -0.09% | -0.05 | 7.68% | -0.01 | -0.59% | -0.31 |


High won 9 of 20 complete years against the all-included benchmark and 10 of 20 against the scored-only one. The partial 2025 year (7 of 12 months): High 11.17%, all-included benchmark 9.75%, scored-only 10.41%. The year-by-year table is `output/spec_v2/year_by_year_v2.csv`.

### Factor regressions (market, size, value, momentum; Newey-West lag 4)

| Series | Model | Alpha a year | t | Market | SMB | HML | MOM | RMW | CMA |
|---|---|---|---|---|---|---|---|---|---|
| High minus risk-free rate | 4-factor | -0.15% | -0.13 | 1.01 | 0.13 | -0.03 | -0.02 | - | - |
| High minus risk-free rate | 6-factor | -0.86% | -0.75 | 1.02 | 0.18 | -0.07 | -0.02 | 0.18 | 0.04 |
| Spread (High minus Low) | 4-factor | +0.01% | +0.01 | 0.01 | -0.23 | 0.11 | 0.04 | - | - |
| Spread (High minus Low) | 6-factor | -1.53% | -0.68 | 0.03 | -0.13 | 0.08 | 0.05 | 0.42 | 0.01 |


### The pre-specified tests, full period and subperiods

| Test (High) | Period | Estimate a year | Std error | t | p | Holm-adjusted p | Minimum detectable effect, 80% power |
|---|---|---|---|---|---|---|---|
| Raw excess vs all-included | full | +0.08% | 0.76% | +0.10 | 0.921 | 1.000 | 2.13% |
| Four-factor alpha | full | -0.15% | 1.14% | -0.13 | 0.896 | 1.000 | 3.19% |
| Raw excess vs all-included | 2005-06 to 2015-05 | +1.13% | 1.00% | +1.13 | 0.259 | 1.000 | 2.82% |
| Four-factor alpha | 2005-06 to 2015-05 | +2.28% | 1.46% | +1.56 | 0.121 | 0.606 | 4.12% |
| Raw excess vs all-included | 2015-06 to 2025-12 | -0.92% | 1.09% | -0.85 | 0.399 | 1.000 | 3.08% |
| Four-factor alpha | 2015-06 to 2025-12 | -3.38% | 1.25% | -2.70 | 0.008 | 0.047 | 3.53% |


Only the second-half four-factor alpha is below 0.05 after adjustment, and it is one subperiod in a family of six, with the opposite sign in 2005-15 (+2.28%, t +1.56). Six-factor alpha: -0.86% (t -0.75) over the full period; -3.79% (t -3.01) in 2015-25.

### How much the second-half result depends on the standard-error convention

| Test (High) | Period | t as run (lag 4) | Holm p | t lag 4 with T/(T-k) correction | Holm p | t lag 6 | Holm p | t lag 12 | Holm p |
|---|---|---|---|---|---|---|---|---|---|
| Raw excess | full | +0.10 | 1.000 | +0.10 | 1.000 | +0.11 | 1.000 | +0.11 | 1.000 |
| Four-factor alpha | full | -0.13 | 1.000 | -0.13 | 1.000 | -0.14 | 1.000 | -0.14 | 1.000 |
| Raw excess | 2005-06 to 2015-05 | +1.13 | 1.000 | +1.13 | 1.000 | +1.30 | 0.785 | +1.40 | 0.652 |
| Four-factor alpha | 2005-06 to 2015-05 | +1.56 | 0.606 | +1.53 | 0.646 | +1.68 | 0.482 | +1.94 | 0.272 |
| Raw excess | 2015-06 to 2025-12 | -0.85 | 1.000 | -0.84 | 1.000 | -0.92 | 1.000 | -0.96 | 1.000 |
| Four-factor alpha | 2015-06 to 2025-12 | -2.70 | 0.047 | -2.65 | 0.055 | -2.94 | 0.024 | -3.72 | 0.002 |


The convention locked before returns was the automatic lag with no small-sample correction (column 'as run'). The second-half four-factor alpha is below 0.05 after Holm as run, at lag 6 and at lag 12, and not with the T/(T-k) correction at lag 4 (Holm 0.055). No other pre-specified test is below 0.05 under any of the four. These are shown side by side and were not used to choose. The automatic lag is the formula, not the data-dependent Newey-West (1994) bandwidth, which is unstable at 127 months. So read the second-half result as weak evidence: one subperiod in a family of six, borderline under one reasonable convention, with the opposite sign in the first half.

### Subperiods

| Period | Months | High CAGR | All-included benchmark CAGR | Scored-only benchmark CAGR | High excess vs all-included | Spread a year |
|---|---|---|---|---|---|---|
| 2005-06 to 2015-05 | 120 | 12.02% | 10.79% | 11.27% | +1.13% | +1.86% |
| 2015-06 to 2025-12 | 127 | 9.55% | 10.79% | 11.44% | -0.92% | -1.44% |


## How many tests were run

The Holm adjustment above covers six tests chosen in advance. It does not cover everything the project has looked at. In all, the project has reported about 250 alpha or excess-return t-statistics in its own tables (252 distinct ones, plus 288 re-estimates of the v2 tests under other standard-error conventions), and about 400 counting audit runs, most of them on the same few return series, so they are far from independent. The table gives the critical |t| for a 5% family-wise level (Bonferroni, t distribution with the second-half degrees of freedom) if that many tests were counted.

| Tests counted | Critical |t| |
|---|---|
| 1 | 1.98 |
| 6 | 2.68 |
| 20 | 3.09 |
| 50 | 3.37 |
| 100 | 3.58 |
| 250 | 3.84 |


The second-half four-factor alpha as run has t -2.70, which clears the six-test threshold (2.68) and not a threshold of about 3, which is where 20 or more counted tests would put it. Its t is -2.65 with the T/(T-k) correction, -2.94 at lag 6 and -3.72 at lag 12. All the |t| values of 3 or more in the project are shortfalls of High against the benchmark or the factor model, none is an edge, and most are variants of the same second-half series.

**No period was held out.** The whole of June 2005 to December 2025 was seen in v1 before v2 was specified, and the January to May 2026 extension (a v1-specification run) was added after the v1 results and after the second-half weakness was known, so it is not an untouched test; at five months it could not support an alpha test anyway. The order in which v1's rules and results were set rests on the project lead's account, and no file can show it. The v2 specification and its test family were committed before any v2 return was read (see the Timing section).

## The two benchmarks

The all-included benchmark holds 800 list rows that have no score (of 8,414). They sit in the benchmark with their actual returns but cannot be in High, Middle or Low, and 53.9% of them are in GICS sectors 40 and 60 (REITs, which have no current assets or liabilities to score, and real estate). Over 2015-25 they ran -5.29% a year behind the all-included benchmark, a gross figure (before costs): a CAGR of 4.88% against 10.83% (computed by an audit script that is not included in this repository, not by the scripts that write the v2 tables). The effect is that the all-included benchmark runs 0.50% a year below the scored-only one in mean annual excess return (the gap in compound growth, CAGR, is 0.57%), so it flatters every scored bucket by about that much: High's excess is +0.08% against the first and -0.42% against the second. Neither is significant. Report both together; neither is the 'right' one. The scored-only benchmark compares like with like; the all-included one is the market of everything on the list.

**Middle's 2015-25 result is mostly the benchmark.** Middle beat the all-included benchmark by +0.99% a year in 2015-25 (t +2.30, unadjusted and outside the Holm family), but only +0.39% (t +0.92) against the scored-only benchmark. It is not evidence that middle scores do well.

## The issuance signal and the literal-rule sensitivity

The first draft of v2 passed the no-issuance test only if common stock issued (`sstk`) was zero or missing. Before any return was read, it was found to fail most firm-years, because `sstk` includes option-exercise proceeds: the pass rate was 20.1% against 80.7% in v1, and High fell from 1,553 to 620 list rows. The rule was revised to net issuance (`sstk - prstkc`), which passes 67.9% and leaves High at 1,408 rows. That revision was made after seeing a pass rate and before any return; the literal rule is kept as a reported sensitivity and was never chosen from.

| Portfolio | Net rule CAGR | Excess vs all-included | Literal rule CAGR | Excess vs all-included |
|---|---|---|---|---|
| High | 10.75% | +0.08% | 11.74% | +1.19% |
| Middle | 11.41% | +0.50% | 11.16% | +0.27% |
| Low | 10.19% | -0.09% | 10.86% | +0.19% |


Under the literal rule High's excess is +1.19% (t +0.86) and its four-factor alpha +0.77% (t +0.53); High beat the all-included benchmark in 10 of 20 complete years. That High bucket is thin and unusual (it selects firms that issued nothing; 620 list rows against 1,408 under the net rule), so the sign here says little. In the project folder the full tables are in `output/spec_v2/literal_sensitivity/`; the public repository carries only `headline_v2.csv` and `tests_v2.csv` from it.

**The net signal drifts with the year.** Its pass rate over scored company-years was 43.0% for fiscal 2004 and 83.0% for fiscal 2022 (82.5% for 2024), probably because buybacks grew. It is not degenerate in level, but part of what it separates is the filing year, not the company within a year. Missing `prstkc` with positive `sstk` counts as no buyback, so those rows fail; the scores report sizes that choice.

## v1 and v2: what changed, and why the sign of the excess flipped

v1 reported High at 10.91% a year against 11.35% for its scored-only benchmark, an excess of -0.29% a year. v2 reports High at 10.75%, with an excess of +0.08% against the all-included benchmark and -0.42% against the scored-only one. The sign of the headline excess flipped from negative to slightly positive because the primary benchmark changed, not because High changed: High's own return moved by -0.16% of CAGR, while the benchmark that includes unscored names is 0.50% a year lower. Against the same kind of benchmark as v1, the excess is still negative and not significant. The archived v1 write-up had already shown the all-included comparison, so the flip is a change of which benchmark is primary, not a new finding.

What changed, and the reason for each:

- profit measure: `ib` (income before extraordinary items) instead of net income, because the paper uses it; ROA, CFO-minus-ROA accruals and the change in ROA move.
- issuance test: net issuance instead of the share-count test with a 2% tolerance, because the paper tests whether common equity was issued; the first literal draft was rejected on a pass rate before any return.
- availability: no 120-day fallback and a 3-day buffer, so a number is used only after a real filing date. In v1 only 6 chosen list rows used a fallback; the buffer moves 43 list rows to an earlier year.
- zero-debt override only where the prior-year change is computable.
- primary benchmark: all included names, so the unscored companies, which v1's benchmark left out, are part of the headline comparison. v1 had already reported this comparison as a post-hoc sensitivity (High +0.19% a year against all included names, t 0.22), and v2 makes it the primary one.
- earlier-year fallback: if a company's newest annual report fails the date test, the latest earlier scored year is used (v1 had no buffer and used the newest year); this moves 43 list rows to an earlier year and leaves 4 stale and 3 with no earlier scored year.
- costs: the reinvestment of mid-period exits is charged.
- statistics: automatic lag, t distribution, Holm adjustment over a pre-specified family, and reported power, instead of 12 fixed lags and a fixed |t| of 2.

Across the 8,414 included list rows, High goes from 1,553 to 1,408, Middle from 5,290 to 5,348, Low from 728 to 858, and unscored from 843 to 800.

v2 was specified after v1's results were known, after the external review, so it is a re-specification, not a blind second test. What is pre-specified is the set of v2 rules and tests, committed before any v2 return was read. The v1 write-up and its robustness runs remain in `output/archive_v1/` and the v1 files.

## Against Piotroski's paper

- Profitability: the paper uses income before extraordinary items; v2 does too (v1 used net income).
- Equity issuance: the paper tests that no common equity was issued; v2 tests net issuance, `sstk - prstkc`, not exactly the paper's rule. v1's 2% share-count tolerance is dropped.
- Leverage: the paper counts current-portion debt as well as long-term debt. Neither v1 nor v2 does: this is a deviation in both specifications.
- Low: the paper's main weak group is scores 0-1, with 0-2 as a footnote alternative and below 5 in an appendix. This project's Low is 0-4 (changed from 0-2 on name counts before any return), so it is broader than the paper's.
- The paper's own Table 4 finds the effect weak in the largest firms: High minus All +0.017 for large firms (t 0.872), against +0.088 for small firms (t 2.456).
- Our result, no detectable edge among the largest companies, is consistent with the weak large-firm result, but it is not strictly comparable. The paper's large-firm difference of +0.017 (1.7 points) sits just outside our 95% range for High's excess (-1.42% to +1.57%), and the subperiod tests could only detect about 2.8% to 3.1% a year or more. Further: the paper uses pooled one-year market-adjusted returns on a high book-to-market sample, and this project uses annual portfolios of the 500 largest companies, factor-adjusted and net of costs.

## Drop counts

Per formation date, v1 beside v2, is in `output/spec_v2/drops_by_date_v2.csv`; one row per unscored name is `drops_reasons_v2.csv`; the summary is `drops_summary_v2.md`.

| Stage | Count | Detail |
|---|---|---|
| Companies on the 21 lists | 10,500 | Exactly 500 a date |
| No GVKEY link | 13 | Eaton, Dell, Liberty, Ceridian |
| No sector | 13 | Yahoo |
| Securities removed as stopped trading, before ranking | 727 | security-dates |
| Included company-dates | 8,414 | After sector exclusions |
| Unscored in v1 | 843 (10.0%) | missing or too old |
| Unscored in v2 | 800 (9.5%) | reasons below |
| Held company-dates in the buckets (v2) | 7,614 |  |


Why the v2 unscored names are unscored (list rows):

| Reason | List rows | Share of unscored |
|---|---|---|
| missing signal | 689 | 86.1% |
| unscorable t-2 (no consecutive prior years) | 54 | 6.8% |
| no 10-K filing date | 25 | 3.1% |
| stale score | 15 | 1.9% |
| no usable fiscal year | 13 | 1.6% |
| stub or fiscal-year change | 4 | 0.5% |


Missing-signal cases are mostly the liquidity signal: 647 of the 689 (REITs and finance-arm firms have no current assets or liabilities). Unscored names in sectors 40 and 60: v1 431 of 843; v2 431 of 800. Firm-years with no real 10-K filing date: 633, of which 112 would otherwise have a score. 13 list rows use an older year because the newest filed year is unscorable and 43 because the newest filing fell inside the buffer. Counting v1's scored rows, the 44 buffer cases are 43 scored from an earlier year and 1 stale; the 6 fallback-dated cases are 3 stale and 3 with no earlier scored year. Together: 43 scored from an earlier year, 4 stale and 3 with no earlier scored year. The scores report counts differently: every included row with a scorable filing inside the buffer, whether or not v1 scored it, which gives 45 (43 older year, 1 stale, 1 unscored in v1 and v2 alike). v1 had 15 scored list rows filed on the formation date itself and 44 within 3 days.

## Limitations and disclosures

*The next block, on the universe and who is in and out, is carried unchanged from the v1 write-up because the universe is unchanged.*

**The universe is a proxy.**

- It is not the official S&P 500, because S&P membership history was not available. The 2025 list holds 418 of the 500 current S&P members, an overlap of 83.6%. That membership is as of October 2026, not May 2025. Of the 82 missing, 47 rank below 500, 29 are incorporated outside the US (such as Linde, Accenture and Medtronic), 5 have no valid link, and 1 is Cboe, whose listing is excluded by rule.
- Partnerships coded as units, such as Enterprise Products, are excluded.
- The check on 375-425 names per date was set after the counts were known, before any returns, and is a sanity check only. Actual range: 378-417.
- 500th-company market cap: the 2021 move of +63.6% is flagged and looks market-wide. The May date shows no 2020 dip (+0.8%), though the same cutoff fell in March 2020.

**Who is in and out.**

- Equity REITs stay in on all dates, including while GICS classed them in Financials. Mortgage REITs (lenders) are excluded on all dates, by dated GICS sub-industry plus one named exception, iStar 2005, which carries a generic code. That exception is a judgment call. 19 company-dates are affected.
- Visa, Mastercard and PayPal leave the universe when GICS moved them to Financials in March 2023.
- CBRE, which is not a REIT, is excluded through 2016 and included from 2017 after the Real Estate sector change.
- If the held share class has no valid link, the GVKEY comes from the same PERMCO when it has exactly one, and returns still come from the held class. This was used 34 times across 8 companies, including Alphabet 2014-2022.
- Eaton 2005-2012 and Ceridian 2020 drop out under the link filter. Dell 2017-18 and Liberty Media LSXMK 2016-17 have no GVKEY and are excluded.
- Yahoo 2005-2017 has no sector on the date and is excluded.
- Securities that stopped trading before the formation date are removed before ranking.


**The test effectively excludes some companies.** A company-year with any uncomputable signal is dropped: 800 list rows are unscored, 53.9% of them in sectors 40 and 60. That effectively excludes traditional REITs, most homebuilders and finance-arm firms, so the result describes the rest of the large-company universe. The v1-specification REIT run below shows the effect of including REITs.

**Low is broader than Piotroski's weak group** (see the paper comparison). Middle is therefore 5-7.

**Data limits.**

- Restatements: fundamentals come from the current Compustat database, not a record of what was reported at the time, while availability dates use original 10-K filing dates. In a test on a sample of 1,480 companies for 2005-2015, 98.5% of F-scores matched those computable at the time and 0.2% changed bucket; only 55 of those companies are in this project, where 97.3% matched and 0.45% changed bucket. That test used the v1 scores and net income. It could not be extended to fiscal 2015 to 2024, because the point-in-time snapshot table (`comp_snapshot`) is not available to this account. So any look-ahead from restated figures is unmeasured for the later years, which include the second half where the one nominally significant result sits.
- Returns end in December 2025, so the 2025 portfolio is partial, and the last subperiod ends then.
- Two companies report in Canadian dollars; they are not converted, and ratios are unaffected.
- Merger and separation years are kept: assets or sales move 2x-10x on some list rows, and comparisons across a change of CRSP company are not always valid. See `output/tables/permco_joins_review.csv` (v1 file, same fundamentals).

**Timing of the specification.**

- The v2 rules were first committed in the project's working repository (those commits are not part of this public repository's history) on 2026-11-01 at 23:01, before any v2 return existed. Between the pre-return score report and the first v2 return file (created 2026-11-02 17:25:08) three more commits changed the specification: one at 17:18 revised the issuance rule from `sstk > 0` to `sstk` net of `prstkc`, because the literal rule flagged 77% of firm-years as issuers (option-exercise proceeds); one at 17:19 locked clarifications raised by the independent rebuild; and one at 17:22 locked the hold-flat treatment of Maxim (2007-11 to 2008-05) and General Growth (2009-05) in the benchmark. No v2 return existed before 17:25. Since the 17:22 commit, `config.py` changed only by the `HEADLINE_SPEC` line and a comment on the `SPEC_V2` line (a later commit at 17:42). The small-sample correction for the standard errors, T/(T-k), was suggested during review but was not in the locked configuration, so it is a reported sensitivity, not the as-run convention. The 3-day buffer is an assumption, not a derived number. Some auditors compared v1 returns of dropped rows before the older-year clarification was settled; no v2 return was read.
- v2 itself was specified after v1's results were known, so it is not a blind test of a fresh hypothesis. The claims in the archived v1 write-up about when its own rules were set rest on the project lead's account, as that write-up says; no file can show the order of events.
- The builds share the same data and several of the same rules, so an independent rebuild checks the arithmetic and the implementation, not whether the rules are the right ones or the data true.

**Portfolio mechanics.**

- 191 mid-period exits across the all-included benchmark and buckets (Middle 125, Low 28, High 27, Unscored 11, each name counted under its own bucket); proceeds are reinvested pro rata and the reinvestment is charged one side in the exit month. 4 included names delist on the formation date (CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017): they count at 1/N in the target, are charged as buys, earn nothing, and their weight is respread uncharged.
- Maxim Integrated (November 2007 to May 2008) and General Growth Properties (May 2009) have no return for some months and no exit; they are held flat at 0%, uncharged, in the all-included benchmark only. The choice was fixed before any v2 return, and moves the benchmark slightly; a different rule is not tested.
- RSP has two rows for April 2018 and they are chained into one return.
- No size-dependent trading costs are modelled: every trade pays 10 basis points whatever the company's size or liquidity, and the shorting costs of the Spread are not modelled.
- REIT and real estate coverage is thin by construction (see above): 53.9% of unscored names sit in sectors 40 and 60.

## Verification

Every number in the results tables was recomputed from the monthly return file with separate numpy/scipy code (`16_spec_v2_numcheck.py`; reports in `output/spec_v2/numcheck_v2.md`), and the figures in this write-up are generated from the v2 files by `17_spec_v2_writeup.py`, with their sources in `output/spec_v2/writeup_figures_v2.csv`. Checked at the end state in the project folder: git shows no change to scripts 01 to 11 or to the v1 outputs since the v1 commit, and the earlier raw files match the hash values logged for them (in the project's `output/logs/pull_raw_hashes.csv` and the two v2 pull logs, which are not in the public repository, and in `output/logs/raw_hashes_added.csv`, which is; the last was recorded after the fact). There is no per-stage hash record for the cleaned data in `data/clean`. `00_test_wrds.py`, `requirements.txt`, `config.py` and `CLAUDE.md` were edited after the v2 returns, for additions and wording only. The data files are licensed and are not in the public repository, so the raw-file hashes cannot be checked from the public copy. Independent rebuilds and audits of v2 are separate reports in `verification/`; this write-up uses one figure from them (the unscored names' return, above), and the audit scripts are not included in this repository. A rebuild does not test the rules and data the builds share.

## Runs after the v1 write-up: run on the v1 specification, not rerun under v2

The user asked for three further runs after the v1 write-up was finished. **None of them is the headline, none was rerun under v2, and none changes a figure or the answer above.** They used the v1 scores, the v1 scored-only benchmark and v1 costs, so in the tables below 'Headline' means the v1 headline. **Benchmark caveat:** they compare with the scored-only benchmark, as v1 did; under v2 that benchmark runs 0.50% a year above the all-included one, so these excesses would look about that much better against all included names, and the all-included comparison was not computed for them. Each has its own folder, and new data went into new files. All are for the same universe, the Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy), and all figures are net of costs.

*The rest of this section is carried unchanged from the v1 write-up.*

Each run's monthly returns were independently rebuilt or audited (`verification/data_audit_post_writeup.md`, `verification/data_audit_long_short.md`). A rebuild shows the arithmetic is right, not that a rule is the right one.

### 2026 extension: not the headline

This holds the 2025 portfolio through May 2026, so that 2025-26 becomes a complete year, with no new rebalance or cost.

The January-May 2026 extension uses Compustat monthly returns because CRSP data on this account ends in December 2025. It is reported separately and does not change any v1 headline figure. On 15,752 earlier held months, Compustat agrees with CRSP within 1% on 99.96%, but it differs at spin-offs and at delistings (the gaps are listed in the project's `output/extension_2026/validation.md`, which the public repository does not include). Two spin-offs (Becton Dickinson, Comcast) and two acquisitions (Hologic, Coterra) fall in the window. No bankruptcies do.

| | v1 headline, to December 2025 | Extended, to May 2026 |
|---|---|---|
| High CAGR | 10.91% | 11.44% |
| Benchmark CAGR | 11.35% | 11.86% |
| High minus Benchmark, a year | -0.29% | -0.26% |
| High alpha (t) | -0.78% (-0.71) | -0.47% (-0.42) |
| High minus Benchmark alpha (t) | -0.95% (-1.02) | -0.85% (-0.91) |
| Spread alpha (t) | -2.04% (-0.72) | -2.83% (-1.01) |
| Average Spread a year | -0.57% | -1.71% |
| High alpha from June 2015 (t) | -3.83% (-4.10) | -3.25% (-3.16) |
| Complete years High won | 10 of 20 | 11 of 21 |

January-May 2026 alone: High +15.36%, Middle +11.12%, Low +45.07%, Benchmark +15.16%, RSP +9.48%, SPY +11.24%.

- **Few names carry it.** Western Digital and Intel supply 29.4 of Low's 45.07 points, and Micron 9.06 of High's 15.36. Those positions were large because the fixed 12-month hold let them drift there. The rest is breadth: 84.8% of Low rose against 51.4% of High, with a median stock of +16.7% against +0.3%.
- **Five months say little.** The window adds no real evidence on whether the F-score works. It is one narrow episode, part of one holding year, about one sector-driven market move, and it should not strengthen or weaken the v1 headline in either direction. Average Spread three times larger after 5 of 252 months should not be read as a stronger trend.
- **The t of -3.16 needs the same lag caution.** It is about -2.7 to -3.2, and about -2 with no lag allowance. The alpha falls in the lowest 1.7% of random selections, but the lowest 12.5% if they keep High's sector mix.
- **Data.** The prices were confirmed against a separate vendor, but month-end prices and spin-off treatment have only S&P sources. CRSP cannot check these months yet, and they should be compared with it when it can.

Source files: `output/extension_2026/results.md`, `validation.md`, `returns.csv`, `contributors_jan_may_2026.csv`; `09a_extension_pull.py`, `10_extension_2026.py`, `10a_extension_contributors.py`; `data/raw/comp_secm_extension.parquet`.

### REIT liquidity substitute: not the headline, not a blind test

The v1 headline effectively excludes traditional REITs, because they have no current ratio. Here a row-level REIT with no liquidity signal uses a rise in cash to total liabilities (`che / lt`) instead, on the same 0-9 scale and buckets. The rule was set after similar variants had been seen. It covers June 2005 to December 2025 on CRSP.

| | v1 headline | REIT substitute |
|---|---|---|
| Scored REIT rows | 80 of 512 (15.6%) | 510 of 512 (99.6%) |
| High CAGR | 10.91% | 10.63% |
| Benchmark CAGR | 11.35% | 11.06% |
| High minus Benchmark, a year | -0.29% | -0.30% |
| High alpha (t) | -0.78% (-0.71) | -1.01% (-0.91) |
| High minus Benchmark alpha (t) | -0.95% (-1.02) | -0.96% (-1.00) |
| 2015-25 High alpha (t) | -3.83% (-4.10) | -4.24% (-4.40) |

It adds 430 list rows (High 61, Middle 302, Low 67) across 44 companies. The signal passes 48.1% of the time.

- **This is the same result, not new evidence.** Its monthly returns correlate 0.9989 with the v1 headline's. Most of the fall in alpha comes from adding REITs of any kind, in both High and the Benchmark, so the score is not choosing worse REITs. The variant shows that the v1 headline result holds when most missing REITs are added, and that REITs were weak in that decade. The rise in t from -4.10 to -4.40 should not be quoted as stronger evidence, and the same lag caution applies.
- **The signal is noisy.** The median REIT holds cash of 2.75% of liabilities, so it mostly reflects year-end cash timing.
- **Still dropped.** 211 included rows still miss only the liquidity signal, all non-REITs. 2 REIT rows miss another signal.

Source files: `output/reit_liquidity_substitute/results.md`, `rows_added.csv`, `portfolio_returns.csv`; `09_reit_liquidity.py`; `data/raw/comp_funda_reit_fields.parquet`.

### 100/100 long/short: not the headline, not a blind test

This holds 100% long High and 100% short Low against NAV (net asset value, the capital in the strategy), with cash earning the risk-free rate. The Spread had already been seen, so it is not a blind test. **The borrow fee is an assumption, not data.** Gross exposure is (long + short) / NAV and net exposure is (long - short) / NAV.

It is shown both ways, and the two should be read together. The annual reset is the locked rule: a position opened 100/100 and left alone for 12 months. The monthly reset is a second view of a book held near 100/100, charged 10 basis points on each resize. The charged version was added after the locked result had been seen.

| June 2005 to December 2025, CRSP | CAGR | Volatility | Sharpe | Max drawdown | Alpha (t) |
|---|---|---|---|---|---|
| **Annual reset (locked), 0.50% borrow** | -1.80% | 12.27% | -0.22 | -75.8% | -4.53% (-1.48) |
| Annual reset, 2.00% borrow | -3.43% | 12.42% | -0.35 | -80.7% | -6.18% (-1.98) |
| **Monthly reset, charged, 0.50% borrow** | -0.42% | 10.41% | -0.15 | -67.5% | -3.00% (-1.06) |
| Monthly reset, charged, 2.00% borrow | -1.90% | 10.41% | -0.29 | -73.5% | -4.50% (-1.60) |
| Long-only High | 10.91% | 16.79% | 0.60 | -44.4% | -0.78% (-0.71) |
| Benchmark | 11.35% | 16.17% | 0.65 | -49.1% | +0.18% (0.25) |

| To May 2026, Compustat from January 2026 | CAGR | Alpha (t) |
|---|---|---|
| Annual reset, 0.50% borrow | -3.59% | -5.80% (-1.86) |
| Annual reset, 2.00% borrow | -5.23% | -7.49% (-2.35) |
| Monthly reset, charged, 0.50% borrow | -1.55% | -3.78% (-1.35) |
| Monthly reset, charged, 2.00% borrow | -3.02% | -5.28% (-1.89) |

- **"100/100" describes June only under the annual reset.** Gross exposure peaked at 5.0x, with net -0.70, at the end of February 2021. At the end of May 2026 the short is 243% of NAV, and Western Digital alone 46%. Few managers or brokers would let a book run to that size, and no margin limit is modelled.
- **The reset choice is much of the loss, but it does not create the negative result.** The annual reset accounts for 1.38 of the 1.80 points, measured against the charged monthly reset. CAGR stays below zero and alpha negative at every reset frequency tested.
- **Against the Spread.** The Spread with both legs charged is -0.92% a year. Return above cash falls further, to -2.71%, because of the 0.53-point borrow fee and 1.25 points from the annual reset: a size effect of -0.60 (legs larger than NAV) and a net-exposure effect of -0.65 (the book largest and most net short when Low runs ahead).
- **Significance.** No alpha over the main period reaches |t| of 2, and neither t of -2.35 is evidence about the F-score. Those are the 0.50% annual reset for June 2015 to May 2026 and the 2.00% annual reset for June 2005 to May 2026, both including Compustat months. Shuffled scores within sectors average t -2.11 for the first window, and 56.5% of them pass |t| of 2.
- **2025-26's -32.65% is mostly two Compustat-era names.** Without Western Digital and Intel it is +9.0%. Without those two and Micron it is -3.6%. This one year moves CAGR from -1.80% to -3.59%, which is too much weight on one year and one data source.
- **Real terms would differ.** Cash earning less than the risk-free rate would lower the result by about 1 point of CAGR for each point of haircut. A retail account with no interest on short proceeds would see about -3.43%. The audit's other tests on fees and on delisted shorts are in its report; recalls and borrow-fee spikes are not captured.

Source files: `output/long_short_100_100/results.md`, `performance.csv`, `exposure.csv`, `sensitivity_monthly_reset.csv`, `spread_both_legs_charged.csv`, `nav_main.csv`, `nav_extension.csv`; `11_long_short.py`.

