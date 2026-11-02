# Piotroski F-Score Backtest — Project Brief

You are the build agent for this project. Read this file fully before doing anything. `config.py` holds the locked rules; this file explains what to build, in what order, and where to stop for human review.

## 1. The question

In large US companies, did buying the financially strongest ones — measured by the Piotroski F-score — beat an equal-weighted universe of the same stocks from 2005 to 2026, and does any outperformance survive after accounting for known factors (market, size, value, profitability, investment, momentum)?

This is a research test, not a trading system. The honest answer may be "no" — that is a valid result. Never tune rules to improve results.

## 2. Ground rules (non-negotiable)

1. **No look-ahead.** A fundamental number may only be used on or after its availability date (10-K filing date, or fiscal year-end + 120 days if missing).
2. **No survivorship bias.** The universe is rebuilt on each formation date from data as it existed then. Never start from today's constituents.
3. **Config-driven.** Every parameter comes from `config.py`. No magic numbers in scripts. If a rule is missing from the config, stop and ask — do not invent one.
4. **Raw data is immutable.** Files in `data/raw/` are written once by the pull script and never edited. All cleaning writes to `data/clean/`.
5. **Rules are locked.** Do not change `config.py` values after results exist. A changed setting is a new, labelled robustness run.
6. **Log everything.** Each script writes row counts, unique-company counts, date ranges, and drop counts (with reasons) to `output/logs/`.
7. **Report, don't hide.** Any dropped company-years, failed links, or fallback lags are counted and reported in the final write-up.
8. **Explain in plain English.** The user wants technical terms defined briefly the first time they appear in any output or summary.

## 3. Data access (confirmed via `00_test_wrds.py`)

Connection: `wrds` Python package; credentials saved in `.pgpass` (no password prompts needed).

| Need | Table | Status |
|---|---|---|
| Annual fundamentals | `comp.funda` | OK |
| 10-K filing dates | `comp.co_filedate` | OK |
| Historical GICS sectors | `comp.co_hgic` | OK |
| Monthly returns incl. delisting | `crsp.msf_v2` (CIZ format) | OK — use this |
| Legacy returns / delistings | `crsp.msf`, `crsp.msedelist` | OK — fallback only |
| CRSP–Compustat link | `crsp.ccmxpf_lnkhist` | OK |
| Fama-French 5 factors + RF | `ff.fivefactors_monthly` | OK |
| Momentum (UMD) | `ff.factors_monthly` | OK |
| S&P 500 membership | `crsp.msp500list` | **NO ACCESS** |
| S&P 500 membership (Compustat) | `comp.idxcst_his` | Readable but **current members only** (no end dates) — unusable for history; usable only to compare today's list |

**Before querying any table, inspect its columns** (e.g. `db.describe_table`). Column names in CIZ tables differ from legacy CRSP. Do not assume names — verify.

## 4. Universe: Top-500 proxy (replaces S&P 500)

Because S&P 500 history is unavailable, the universe is:

> **Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy).**

Use this exact label in every table, chart, and the write-up.

Construction on each formation date (last trading day of May, 2005–2025):

1. Take all CRSP securities with data on that date from `crsp.msf_v2`.
2. Keep only US-incorporated ordinary common stock listed on NYSE, Nasdaq, or NYSE American. Exclude ETFs, ADRs, preferreds, closed-end funds, units. **REITs stay in** (the S&P 500 includes them).
3. Group share classes by PERMCO (company-level ID); company market cap = sum across classes (price × shares outstanding, absolute value of price).
4. Rank companies by market cap; keep the top 500.
5. For each, the held security = the share class with the largest market cap.
6. Link to GVKEY via `crsp.ccmxpf_lnkhist` (linktype in LC/LU, linkprim in P/C, link valid on the formation date).
7. Attach GICS sector valid on that date from `comp.co_hgic`; flag and exclude sectors 40 (Financials) and 55 (Utilities) **after** ranking.

Output: `data/clean/universe.parquet` — formation_date, permno, permco, gvkey, mktcap, rank, gsector, included (bool).

**Add these to `config.py`** (with comments) before building:
- `UNIVERSE = "top500_us_mktcap"`, `UNIVERSE_SIZE = 500`, `UNIVERSE_LABEL` = the label above
- `UNIVERSE_BUFFER = None` (headline: no buffer); robustness variant uses entry ≤ 450 / exit > 550
- Remove/replace `INDEX = "S&P 500"`

## 5. Pipeline — build in this order

Each phase is its own script, runs end-to-end from the previous phase's outputs, and is re-runnable.

```
piotroski_backtest/
├── CLAUDE.md
├── config.py
├── 00_test_wrds.py          (done)
├── 01_build_universe.py
├── 02_pull_data.py
├── 03_clean.py
├── 04_scores.py
├── 05_align.py
├── 06_portfolios.py
├── 07_evaluate.py
├── 08_robustness.py
├── data/raw/   data/clean/
└── output/  (logs/, tables/, charts/)
```

### Phase 1a — `01_build_universe.py`
Build the universe per Section 4.

Checks (log all; fail loudly if violated):
- Exactly 500 companies per date before exclusions; ~400–430 after.
- 500th-company market cap trends up over time with dips around 2009 and 2020; flag any year-over-year jump/collapse > 50%.
- GVKEY link rate ≥ 98%; list every failure with name.
- Overlap of the 2025 list with current S&P 500 members from `comp.idxcst_his` (gvkeyx = '000003') — report %.
- Year-over-year name turnover.
- Confirm known later-failed/acquired names appear in early lists (e.g., Lehman Brothers before the financial exclusion; Sears ~2005).

**🛑 CHECKPOINT 1:** Stop. Show the user the checks summary and the overlap %. Wait for approval.

### Phase 1b — `02_pull_data.py`
Master ID list = union of all companies across all 21 universe lists.

Pull to `data/raw/` (parquet, one file per table):
- `comp.funda`, FY2002–FY2025, filters `indfmt='INDL'`, `datafmt='STD'`, `popsrc='D'`, `consol='C'`. Fields: gvkey, datadate, fyear, fyr, ni, at, oancf, dltt, act, lct, sale, cogs, csho, ajex, sstk, ceq, txditc, pstk, prcc_f.
- `comp.co_filedate`: 10-K filings only for these gvkeys.
- `comp.co_hgic`: full sector history for these gvkeys.
- `crsp.msf_v2`: monthly total return, price, shares outstanding, Jan 2005 → latest, for all linked PERMNOs.
- RSP and SPY monthly returns from `crsp.msf_v2` (secondary benchmarks).
- Fama-French 5 factors + RF (`ff.fivefactors_monthly`) and UMD (`ff.factors_monthly`), merged on month; check same coverage.

Write `output/logs/pull_log.csv`: table, pull timestamp, rows, unique IDs, date range.

### Phase 2 — `03_clean.py`
- Standardize names/units (USD millions).
- One row per gvkey-fiscal year; if duplicates, keep original over amendment.
- Flag fiscal-year changes / stub years (fiscal period ≠ ~12 months); exclude stubs from year-over-year comparisons.
- Availability date: earliest 10-K filedate for that gvkey-datadate; else datadate + `FALLBACK_LAG_DAYS`. Log % using fallback.
- Sanity: no negative assets/revenue; flag extreme outliers (likely unit errors) for review rather than silently dropping.
- Output: `data/clean/fundamentals_clean.parquet`.

### Phase 3 — `04_scores.py`
Sort by gvkey, fiscal year. Build lag-1 and lag-2 values **only where the gap is exactly one fiscal year**; otherwise null.

Definitions (t = current FY, t−1 prior):
- ROA = ni_t / at_{t−1}
- CFO = oancf_t / at_{t−1}
- ΔROA = ROA_t − ROA_{t−1} (needs at_{t−2})
- ACCRUAL = CFO − ROA
- LEVER = dltt / average(at_t, at_{t−1}); ΔLEVER = LEVER_t − LEVER_{t−1}
- LIQUID = act / lct; ΔLIQUID = LIQUID_t − LIQUID_{t−1}
- Adjusted shares = csho × ajex; EQ growth = adj_shares_t / adj_shares_{t−1} − 1
- MARGIN = (sale − cogs) / sale; ΔMARGIN = MARGIN_t − MARGIN_{t−1}
- TURN = sale / at_{t−1}; ΔTURN = TURN_t − TURN_{t−1}

Signals (1 = pass):
1. F_ROA: ROA > 0
2. F_CFO: CFO > 0
3. F_ΔROA: ΔROA > 0
4. F_ACCRUAL: CFO > ROA
5. F_ΔLEVER: ΔLEVER < 0; if dltt = 0 in both years → pass (`ZERO_DEBT_COUNTS_AS_PASS`)
6. F_ΔLIQUID: ΔLIQUID > 0
7. F_EQ_OFFER: EQ growth ≤ `SHARE_ISSUANCE_TOLERANCE`
8. F_ΔMARGIN: ΔMARGIN > 0
9. F_ΔTURN: ΔTURN > 0

F_SCORE = sum. If any signal is uncomputable → drop the company-year (`MISSING_SIGNAL_RULE = "drop"`); log count and reason by signal.

Keep all nine signal columns plus inputs in `data/clean/fscores.parquet`.

Validation outputs:
- Histogram of F_SCORE across all company-years (expect roughly bell-shaped around 5; a spike at 0 = bug).
- `output/tables/handcheck_sample.csv`: 4 companies × 1 fiscal year each (choose varied sectors), with every raw input, ratio, and signal shown, so the user can compare against the actual 10-K.

**🛑 CHECKPOINT 2:** Stop. The user hand-checks the sample against the 10-Ks. Do not proceed until they confirm the scores match.

### Phase 4 — `05_align.py`
For each formation date: take included universe members; attach the most recent F_SCORE with availability date ≤ formation date (`pandas.merge_asof`, by gvkey); drop scores older than `MAX_SCORE_AGE_MONTHS`. Also compute book-to-market (book equity from the same FY ÷ market cap on formation date) and its tercile, for the version-B robustness run.

Output: `data/clean/formation.parquet`. Log per date: universe size, # with valid score, # dropped as stale/missing.

### Phase 5 — `06_portfolios.py`
- Buckets: High (`HIGH_SCORES`), Low (`LOW_SCORES`), Middle; benchmark = all scored, included names.
- Log count per bucket per year; flag any bucket < 10 names.
- Equal weight at formation, buy-and-hold drift for `HOLDING_MONTHS`.
- Monthly portfolio return = weighted average of member returns (msf_v2 returns include delisting). If a stock exits mid-year, reinvest pro-rata across remaining holdings.
- Turnover at each rebalance; deduct turnover × `TRANSACTION_COST_BPS`.
- Long/short spread = High − Low (diagnostic only, no shorting costs).

Output: `output/tables/portfolio_returns.csv` — monthly High, Middle, Low, Spread, Benchmark, RSP, SPY.

### Phase 6 — `07_evaluate.py`
- Performance table: CAGR, annualized volatility, Sharpe, max drawdown, avg turnover, % years High beats benchmark.
- Versus primary benchmark: excess return, tracking error, information ratio.
- Factor regression of High and Spread excess returns on Mkt-RF, SMB, HML, RMW, CMA, MOM with Newey-West standard errors (`NEWEY_WEST_LAGS`). Report alpha (annualized), t-stats, loadings.
- Monotonicity: average annual return by individual score 0–9.
- Year-by-year spread table; subperiod split per `SUBPERIODS`.
- Charts: cumulative returns (log scale) High vs Low vs Benchmark; drawdowns; returns by score.

**🛑 CHECKPOINT 3:** Stop. Present headline results with plain-English interpretation. Wait before robustness.

### Phase 7 — `08_robustness.py`
Rerun Phases 4–6 changing one setting at a time per `ROBUSTNESS` in config, plus:
- `universe_buffer`: 450/550 entry/exit rule
- `profitability_screen`: require positive trailing-four-quarter earnings and positive latest-quarter earnings (Compustat quarterly, same filing-lag logic) — note it overlaps with F_ROA

Output one comparison table: alpha, t-stat, High-minus-benchmark excess return, Sharpe for each variant vs headline.

## 6. Final deliverables

1. All scripts, runnable in order from a fresh `data/` folder.
2. `output/tables/` and `output/charts/` as above.
3. A short write-up (`output/writeup.md`): the answer in one paragraph; method (point to config); results table and key charts; robustness summary; limitations (top-500 proxy not the official S&P 500 and the 2025 overlap %; fallback-lag share; dropped company-years; no shorting costs on the spread).

## 7. How to work with the user

- Define technical terms briefly on first use.
- Stop at each 🛑 checkpoint. Between checkpoints, work without asking unless a rule is genuinely missing or data contradicts this brief.
- If something looks too good (e.g., large, highly significant alpha in large caps), suspect a look-ahead or survivorship bug first — re-check Phase 2 availability dates and Phase 4 alignment before reporting it.

## 8. Decisions approved by the user at Checkpoint 1 (2026-11-01, before any returns were calculated)

These override the sections above where they differ. Values are in `config.py`.

1. Equity REITs stay in on all dates, including while GICS classed them in sector 40. Mortgage REITs (lenders) are excluded on all dates, after ranking, by dated GICS sub-industry plus one named exception (iStar 2005, which carries a generic code; a judgment call to disclose in the write-up).
2. If the held share class has no valid link, use the gvkey from the same PERMCO when it has exactly one; returns still come from the held class. Log each use.
3. The LC/LU link filter stays as written. Eaton 2005–2012 and Ceridian 2020 drop out and are reported.
4. Companies with no valid sector on the date are excluded and reported. Do not fill sectors from current-only fields.
5. Securities that stopped trading before the formation date are removed before ranking.
6. Security filter codes live in `config.py`. Partnerships coded UG and Cboe listings are excluded.
7. Included count check is a 375–425 sanity range. The 50% cutoff move is a flag, with 2021 explained as market-wide. The 2020 dip is reported, not a failure.
8. Link rate is checked by market cap as well as by name, and the required early names are in `config.py`.
9. The secondary benchmarks are RSP and SPY.

Disclose in the write-up: Visa, Mastercard and PayPal leave the universe when GICS moved them to sector 40 in March 2023; CBRE (not a REIT) is excluded through 2016 and included from 2017 after the Real Estate sector change; the 375–425 range was set after the counts were known, before any returns, and is a sanity check only; Dell 2017–18 and Liberty Media LSXMK 2016–17 have no GVKEY and are excluded.

## 8b. Decisions approved by the user at Checkpoint 2 (2026-11-01, before any returns were calculated)

These override the sections above where they differ. Values are in `config.py`. The user's 10-K hand-check was a separate gate: the user confirmed "scores match" on 2026-11-01 in the master session, after these decisions and before Phase 4 started.

1. `LOW_SCORES` is 0–4, changed from 0–2 on name counts only (median 2 names a date, empty in 2006, 2007, 2011). Middle is therefore 5–7. Disclose the change and that Low is broader than Piotroski's weak group.
2. `MISSING_SIGNAL_RULE` stays "drop" for the headline. Disclose that the test effectively excludes traditional REITs, most homebuilders and finance-arm firms. An 8-signal version is a labelled robustness run; define its bucket placement before any returns exist.
3. The 2025 portfolio is kept through December 2025, labelled partial (7 of 12 months); the last subperiod ends 2025-12. Disclose that the test ends before 2026.
4. Rows reported in non-USD currencies are excluded from version B only, with no conversion, and reported.
5. Score age is calendar months from fiscal year-end to formation date.
6. The thin May 2005 list (25 companies with January–May year-ends and no score) is disclosed; the pull is not extended.
7. Merger and separation years are kept and disclosed, including the 270 list rows with 2x–10x moves and the likely invalid comparisons in `output/tables/permco_joins_review.csv`.
8. The cleaning rules in `config.py` (stub test, outlier flag, margin rule, 1 million share floor) are approved.

## 8c. Decisions approved by the user at Checkpoint 3 (2026-11-01)

Robustness definitions are in `config.py`. They were set after headline returns existed and before their own results were reported. The Comverse hold-flat rule and the version B boundary instruction were settled after first variant runs existed, though those results had reached only their authors; disclose that timing. The headline stays the headline whatever these runs show. Report the 2015–25 High alpha with its context (t about -2.5 to -3.6 is defensible, not -4.10 alone), using the wording in `verification/data_audit_phase4_6.md`.

## 8d. Post-write-up runs requested by the user (2026-11-01)

These are separate labelled runs after the final write-up. They never change headline files, tables or `output/writeup.md`'s headline. Outputs go in their own folders, and new raw data goes in new files.

1. `extension_2026`: January–May 2026 for the 2025 portfolio using `comp.secm`, because CRSP ends 2025-12-31. Portfolio returns only after the overlap validation has been reviewed.
2. `reit_liquidity_substitute` (user chose option A): defined in `config.py`. It was set after similar variants were seen, so it is not a blind test; disclose that.
3. Possible later run, not yet requested (option C): an ex-REIT universe, removing REITs on all dates and relabelling the universe.
4. `long_short_100_100`: 100% long High, 100% short Low, defined in `config.py`, reported beside long-only High. The spread had already been seen, so it is not a blind test, and the borrow fee is an assumption. Disclose both. The headline net Spread column credits Low's trading costs to the spread; it stays as published, but disclose this.

## 8e. Re-audit fixes approved by the user (2026-11-01)

No rule, score or return changes. The issuance and zero-debt sensitivities and the all-included benchmark comparison are disclosures only, seen after results, and are not reasons to change a rule. The run order is in `README.md`.

## 9. Carried forward from the Phase 1a audit (`verification/data_audit_phase1a_v2.md`)

- All WRDS scripts: `wrds.Connection()` must receive `wrds_username` (from `PGUSER` or `pgpass.conf`), as in `01_build_universe.py`, because the Windows username differs. Never print or store the password.
- Phase 3: 20 GVKEYs span two PERMCOs over time (e.g. Dow to DuPont, IAC to Match, Dell). Check that year-over-year comparisons across those joins are valid.
- Phase 5: 4 included names delist on the formation date (CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017) and have no later returns. Handle them under `DELISTING_RULE` and report them.
- Phase 2: 2 gvkeys report in CAD (11 rows). Report them via `curcd`; see section 8b item 4.
- Phase 2: log filing dates more than 120 days after year-end (0.5%) and later than a year (13); they are real dates, not errors.
- Phase 5: RSP has two rows for April 2018 (PERMNO 89734 to 04-06, 17746 from 04-09). Chain them into one April return; a plain join double-counts the month.
- Phase 4: break availability-date ties on datadate (Maxim, United Rentals); availability order inverts for H&R Block FY2021 and Super Micro FY2017; report the 13 list rows using an older year and the 15 filed on the formation date.
- Write-up: disclose the restatement limit using the text in `verification/data_audit_phase2_3.md`, and the 270 list rows with 2x–10x asset or sales moves.
- Phase 5: `crsp.msf_v2` ends 2025-12-31, so the 2025 portfolio has only 7 of its 12 months; see section 8b item 3.
