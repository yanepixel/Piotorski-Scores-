"""
Piotroski F-Score Backtest â€” Top-500 S&P 500 proxy (WRDS)
Locked rules. Do not edit after seeing results; any change = a new, labelled run.

Descriptive only, not read by any script: DATA_SOURCE, UNIVERSE, UNIVERSE_BUFFER, HEADLINE_VERSION,
LONG_SHORT_SPREAD, HEADLINE_RETURNS, PRIMARY_BENCHMARK, STANDARD_ERRORS, PROFITABILITY_SCREEN, HEADLINE_SPEC.
NEWEY_WEST_LAGS and SIGNIFICANCE_T_STAT belong to v1; the spec_v2 scripts do not read them (see SPEC_V2).
SPEC_V2 keys fallback_availability, primary_benchmark, hac_lag_rule, small_sample, primary_tests, multiple_testing and
report_power each name the one behaviour the v2 code implements; scripts 12b and 14 check them with assertions and stop if
they differ, so they are read but cannot switch a behaviour. All other SPEC_V2 keys are read and used.
Additions after the first v2 returns (keys and comments only, no existing value changed): SPEC_V2 alpha_level, power_level,
sensitivity_lags, sensitivity_small_sample_correction; HEADLINE_SPEC in the list above.
"""

# ---------- Data source ----------
DATA_SOURCE = "WRDS"            # Compustat (fundamentals) + CRSP (returns)

# ---------- Universe ----------
# Replaces INDEX = "S&P 500": crsp.msp500list is not accessible (CLAUDE.md section 4).
UNIVERSE = "top500_us_mktcap"
UNIVERSE_SIZE = 500
UNIVERSE_LABEL = "Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy)"
UNIVERSE_BUFFER = None          # headline: no buffer; robustness variant: entry <= 450, exit > 550
EXCLUDED_GICS_SECTORS = ["40", "55"]   # 40 = Financials, 55 = Utilities
KEEP_REITS_ON_ALL_DATES = True         # equity REITs stay in on all dates, including while GICS classed them in sector 40
REIT_ISSUER_TYPE = "REIT"              # crsp.msf_v2 issuertype, row-level value on the formation date
EXCLUDE_MORTGAGE_REITS = True          # lenders: excluded on all dates, after ranking (Checkpoint 1)
MORTGAGE_REIT_GICS_SUBINDUSTRIES = ("40402030", "40204010")  # comp.co_hgic gsubind valid on the formation date
MORTGAGE_REIT_NAMED_EXCEPTIONS = {("ISTAR FINANCIAL INC", 2005)}  # (issuernm, formation year): generic GICS code; a judgment call

# ---------- Security filters: crsp.msf_v2 row-level values (Checkpoint 1) ----------
US_INCORPORATED_FLAG = "Y"             # usincflg
SECURITY_TYPE = "EQTY"                 # securitytype
SECURITY_SUBTYPE = "COM"               # securitysubtype
LISTING_EXCHANGES = ("N", "Q", "A")    # primaryexch: NYSE, Nasdaq, NYSE American; excludes Cboe (B)
ORDINARY_SHARE_TYPE = "NS"             # sharetype; UG (partnership units) is excluded
REIT_SHARE_TYPE = "SB"                 # shares of beneficial interest; kept only when issuertype is REIT
ACTIVE_DELISTING_FLAG = "N"            # mthdelflg <> this and mthprcdt < mthcaldt: stopped trading, removed before ranking

# ---------- CRSP-Compustat link filters (CLAUDE.md section 4) ----------
LINK_TYPES = ("LC", "LU")
LINK_PRIMARY = ("P", "C")
SIBLING_CLASS_LINK = True              # no link on held class: use the PERMCO's gvkey if exactly one; log each use

# ---------- Universe checks (CLAUDE.md Phase 1a; revised at Checkpoint 1) ----------
MIN_LINK_RATE = 0.98                   # applies by name count and by market cap
INCLUDED_COUNT_RANGE = (375, 425)      # sanity range for names per date after exclusions
MAX_CUTOFF_MKTCAP_CHANGE = 0.50        # flag, not fail: larger year-over-year moves in the 500th company's market cap
CUTOFF_DIP_YEAR_REQUIRED = 2009        # the 500th company's market cap must fall in this year
CUTOFF_DIP_YEAR_REPORTED = 2020        # report-only: May formation misses the March 2020 low
SP500_GVKEYX = "000003"                # comp.idxcst_his index ID; used only to compare the 2025 list
REQUIRED_EARLY_NAMES = ["Lehman Brothers", "Sears Holdings", "Bear Stearns", "Merrill Lynch", "Washington Mutual"]  # must be in the 2005 list

# ---------- Test period ----------
FIRST_FUNDAMENTAL_FY = 2002     # 2 extra years needed for lagged ROA / beginning assets
LAST_FUNDAMENTAL_FY = 2025      # pull range per CLAUDE.md Phase 1b
FIRST_SCORE_FY = 2004
LAST_SCORE_FY = 2024
FIRST_FORMATION_YEAR = 2005
LAST_FORMATION_YEAR = 2025      # partial holding period: returns end before its 12 months are complete
RETURNS_START = "2005-01-01"
RETURNS_END = "2025-12-31"      # crsp.msf_v2 ends here; the 2025 portfolio is labelled partial (7 of 12 months)

# ---------- Data pull (CLAUDE.md Phase 1b) ----------
FUNDA_FILTERS = {"indfmt": "INDL", "datafmt": "STD", "popsrc": "D", "consol": "C"}
FUNDA_FIELDS = ["gvkey", "datadate", "fyear", "fyr", "ni", "at", "oancf", "dltt", "act", "lct",
                "sale", "cogs", "csho", "ajex", "sstk", "ceq", "txditc", "pstk", "prcc_f",
                "curcd"]  # curcd added to the brief's list: 2 gvkeys report in CAD
FILING_SRCTYPES = ("10K",)            # comp.co_filedate srctype; amendments (10K/A) excluded
BENCHMARK_TICKERS = ["RSP", "SPY"]    # secondary benchmarks, returns from crsp.msf_v2
BENCHMARK_PERMNOS = {"RSP": [89734, 17746], "SPY": [84398]}  # tickers alone are unsafe; RSP changed PERMNO in April 2018
BENCHMARK_SECURITY_TYPE = "FUND"      # pull validation only: fail if a benchmark row is not this
BENCHMARK_SECURITY_SUBTYPE = "ETF"    # pull validation only: fail if a benchmark row is not this
MSF_FIELDS = ["permno", "permco", "mthcaldt", "mthret", "mthretx", "mthretflg", "mthprc", "mthprcdt", "mthprcflg",
              "mthdelflg", "shrout", "mthcap", "ticker", "issuernm", "cusip", "usincflg", "issuertype",
              "securitytype", "securitysubtype", "sharetype", "primaryexch"]
FF5_FIELDS = ["date", "dateff", "mktrf", "smb", "hml", "rmw", "cma", "rf"]
UMD_FIELDS = ["date", "umd"]

# ---------- Timing ----------
FORMATION_MONTH = 5             # last trading day of May each year
HOLDING_MONTHS = 12
USE_ACTUAL_FILING_DATE = True   # Compustat filing dates where available
FALLBACK_LAG_DAYS = 120         # fiscal year-end + 120 days if no filing date
MAX_SCORE_AGE_MONTHS = 18       # older scores at formation are dropped as stale
SCORE_AGE_BASIS = "fiscal_year_end"   # age = calendar months from fiscal year-end to formation date

# ---------- Signal definitions ----------
ZERO_DEBT_COUNTS_AS_PASS = True       # no LT debt in both years -> leverage test passes
SHARE_ISSUANCE_TOLERANCE = 0.02       # split-adjusted shares up > 2% -> fails "no issuance"
MISSING_SIGNAL_RULE = "drop"          # any of 9 signals uncomputable -> drop company-year (report count)

# ---------- Cleaning rules not specified by the brief (set before any returns; approved at Checkpoint 2) ----------
STUB_MIN_DAYS = 350                   # days between consecutive year-ends; outside this range = fiscal-year change or stub
STUB_MAX_DAYS = 380                   # no gaps fall in 338-395, so results don't depend on these exact values
STUB_EXCLUSION = "both_sides"         # no year-over-year comparison into or out of a flagged year
OUTLIER_YOY_RATIO = 10                # flag for review, never drop: at, sale or adjusted shares move > 10x up or down in a year
MIN_SALE_FOR_MARGIN = 0               # margin uncomputable when sale <= this
MIN_CSHO_FOR_SHARE_TEST = 1           # millions; F_EQ_OFFER uncomputable below this in either year (Compustat placeholders)
FILING_LATE_LOG_DAYS = (120, 365)     # log labels only

# ---------- Portfolios ----------
HIGH_SCORES = [8, 9]
LOW_SCORES = [0, 1, 2, 3, 4]          # was [0, 1, 2]: median 2 names a date, empty in 3 years; changed at Checkpoint 2 on counts only, before any returns
HEADLINE_VERSION = "A"                # A = full universe (headline); B = cheapest third by book-to-market
VALUE_FILTER_QUANTILE = 1 / 3         # used for version B only
VERSION_B_CURRENCY = "USD"            # version B excludes rows reported in other currencies (curcd); no FX conversion
WEIGHTING = "equal_buy_and_hold"      # equal weights at formation, drift with prices for 12 months
DELISTING_RULE = "reinvest_pro_rata"  # delisting return included, proceeds spread across remaining holdings
TRANSACTION_COST_BPS = 10             # per trade, charged on turnover at each rebalance
LONG_SHORT_SPREAD = "diagnostic_only" # High minus Low, no shorting costs; long-only context
MIN_BUCKET_NAMES = 10                 # flag any portfolio bucket smaller than this (CLAUDE.md Phase 5)

# ---------- Portfolio mechanics not specified by the brief (set before any returns) ----------
BOOK_EQUITY_RULE = "ceq_plus_txditc"  # version B only; null txditc = 0; non-positive stays ranked (never cheapest), null is unranked
TURNOVER_BASIS = "two_way"            # sum of |target - drifted weight|; buys and sells each charged TRANSACTION_COST_BPS; one-way also reported
FIRST_PORTFOLIO_TURNOVER = 1.0        # June 2005 is charged as buying from cash
CHARGE_MIDPERIOD_REINVESTMENT = False # brief charges only "at each rebalance"; includes formation-date delisters' weight
COST_TIMING = "first_holding_month"   # net = (1 + gross) x (1 - cost) - 1
CHARGE_PRIMARY_BENCHMARK = True       # charged like the buckets; RSP and SPY carry no extra charge
HEADLINE_RETURNS = "net"              # headline tables and regressions are net, gross alongside; monotonicity is gross
HIT_RATE_COMPLETE_YEARS_ONLY = True   # % of years High beats benchmark: 20 complete June-May years; partial 2025 shown separately

# ---------- Benchmarks ----------
PRIMARY_BENCHMARK = "equal_weighted_eligible_universe"   # same stocks, same weighting, no F-score
SECONDARY_BENCHMARKS = ["RSP", "SPY"]

# ---------- Evaluation ----------
FACTOR_MODEL = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"]   # Fama-French 5 + momentum
STANDARD_ERRORS = "newey_west"
NEWEY_WEST_LAGS = 12                  # v1's fixed lag count; spec_v2 uses the automatic rule in SPEC_V2['hac_lag_rule'] and does not read this
SIGNIFICANCE_T_STAT = 2.0
SUBPERIODS = [("2005-06", "2015-05"), ("2015-06", "2025-12")]  # second period was to 2026-05; returns end 2025-12

# ---------- Robustness grid (run after headline; one change at a time) ----------
ROBUSTNESS = {
    "high_cutoff_7plus": {"HIGH_SCORES": [7, 8, 9]},
    "value_filter_B": {"HEADLINE_VERSION": "B"},
    "cap_weighted": {"WEIGHTING": "cap_buy_and_hold"},
    "sector_neutral": {"WEIGHTING": "equal_sector_neutral"},
    "lag_90_days": {"FALLBACK_LAG_DAYS": 90},
    "cost_25bps": {"TRANSACTION_COST_BPS": 25},
    "eight_signal_no_liquidity": {"MISSING_SIGNAL_RULE": "eight_signals_if_no_liquidity"},
    "universe_buffer": {"UNIVERSE_BUFFER": {"entry_rank": 450, "exit_rank": 550}},
    "profitability_screen": {"PROFITABILITY_SCREEN": True},
}

# ---------- Robustness definitions (set after headline returns; timing qualified in output/writeup.md) ----------
EIGHT_SIGNAL_HIGH_SCORES = [8]        # firms with no liquidity signal, out of 8; proportional to the 9-signal cutoffs
EIGHT_SIGNAL_LOW_SCORES = [0, 1, 2, 3]  # Middle is therefore 4-7
EIGHT_SIGNAL_NULL_RETURN_RULE = "hold_flat"  # no return, not an exit: General Growth, May 2009
NULL_RETURN_HOLD_FLAT_MONTHS = {      # the only approved cases, by variant and PERMNO; any other held null stops the run
    "eight_signal_no_liquidity": {79129: ["2009-05"]},  # General Growth
    "reit_liquidity_substitute": {79129: ["2009-05"]},  # General Growth
    "universe_buffer": {10942: ["2007-02", "2007-03", "2007-04", "2007-05"]},  # Comverse Technology
    "spec_v2_reruns": {79129: ["2009-05"], 11896: ["2007-11", "2007-12", "2008-01", "2008-02", "2008-03", "2008-04", "2008-05"]},  # added 2026-11-02 before any rerun result; General Growth if held in a REIT-rerun bucket, Maxim as in spec_v2
    "spec_v2": {11896: ["2007-11", "2007-12", "2008-01", "2008-02", "2008-03", "2008-04", "2008-05"],  # Maxim Integrated, unscored, all-included benchmark only
                79129: ["2009-05"]},  # General Growth, unscored in v2, all-included benchmark only; held flat, no charge, set before any v2 return
}
CAP_WEIGHT_BASIS = "formation_mktcap" # then drift; applies to all buckets and the benchmark
SECTOR_NEUTRAL_WEIGHTS = "benchmark_sector_weights"  # equal weight within sector; sector weights from the benchmark on that date
SECTOR_NEUTRAL_EMPTY_SECTOR = "spread_pro_rata"      # a bucket with no names in a sector spreads that weight across the others
PROFITABILITY_SCREEN = False          # headline off; variant requires positive trailing-four-quarter and latest-quarter earnings
PROFITABILITY_SCREEN_SCOPE = "all_scored"  # applies to every bucket and the benchmark, so the benchmark changes
QTR_FILING_SRCTYPES = ("10Q", "10K")  # earliest filing after quarter end, else quarter end + FALLBACK_LAG_DAYS; not rdq
QTR_EARNINGS_FIELD = "niq"            # net income, matching ni in F_ROA
QTR_SELECTION = "latest_four_consecutive_by_datadate"  # one row per gvkey-datadate (non-null niq, then later fyearq), 3 calendar months apart
QTR_UNCONFIRMED_RULE = "fail"         # < 4 quarters, non-consecutive, null earnings or latest quarter older than MAX_SCORE_AGE_MONTHS: fails, logged
QTR_PULL_FIELDS = ["gvkey", "datadate", "fyearq", "fqtr", "fyr", "niq", "curcdq"]  # 08_robustness.py, comp.fundq
QTR_FILING_PULL_FIELDS = ["gvkey", "consol", "popsrc", "srctype", "filedatetime", "datadate", "filedate"]  # 08_robustness.py, comp.co_filedate
REIT_PULL_FIELDS = ["gvkey", "datadate", "fyear", "che", "lt"]  # 09_reit_liquidity.py, comp.funda
EXTENSION_PULL = {                    # 09a_extension_pull.py; comp.secm for the 2025 list and the two funds
    "start": "2025-01-01",
    "end": "2026-06-30",
    "fields": ["gvkey", "iid", "datadate", "conm", "tic", "cusip", "trt1m", "prccm", "ajexm", "trfm", "secstat",
               "primiss", "curcdm", "exchg", "tpci", "cshtrm"],  # secstat is pulled for reporting only, never as a filter
    "benchmark_cusips": {"RSP": ("46137V35", 17746), "SPY": ("78462F10", 84398)},  # 8-digit CUSIP, CRSP PERMNO
}
EXTENSION_2026 = {                    # post-write-up labelled extension; CRSP through RETURNS_END, Compustat after; the headline is unchanged
    "label": "extension_2026",
    "end": "2026-05-31",
    "return_field": "trt1m",          # comp.secm, in percent, on the mapped gvkey-iid; secstat is current-only, so never filter on it
    "exits": {"Hologic": "2026-04", "Coterra": "2026-05"},  # final returns taken from these rows, then DELISTING_RULE; later rows are ignored
    "report_spinoff_months": {"Comcast": "2026-01", "Becton Dickinson": "2026-02"},  # used as given, reported with sensitivity
    "benchmark_lines": {"SPY": ("108132", "01"), "RSP": ("153772", "01")},  # gvkey, iid
}
LONG_SHORT_100_100 = {                # post-write-up labelled variant; the headline Spread stays a diagnostic
    "label": "long_short_100_100",
    "long_scores": HIGH_SCORES,
    "short_scores": LOW_SCORES,
    "reset": "annual_at_rebalance",   # long = short = NAV each June; legs drift within the year
    "borrow_fee_annual": 0.0050,      # flat assumption on short market value, not data
    "borrow_fee_stress_annual": 0.0200,
    "short_side_costs": "charged",    # Low's trading costs reduce this return, unlike the net Spread column
    "cash_interest": "rf",            # earned on cash = NAV - long value + short value
    "sensitivity_reset": "monthly",   # legs reset to equal each month; reported only, free of charge and charged at TRANSACTION_COST_BPS
}
REIT_LIQUIDITY_SUBSTITUTE = {         # post-write-up labelled variant, not in ROBUSTNESS; the headline is unchanged
    "label": "reit_liquidity_substitute",
    "applies_to": "row-level REIT on the formation date with F_DLIQUID uncomputable",  # other firms stay dropped
    "ratio": "che / lt",              # signal passes if cash to total liabilities rose, on the same one-year gap rules
    "buckets": "standard",            # 0-9 scale, so HIGH_SCORES and LOW_SCORES apply
    "null_return_rule": "hold_flat",  # General Growth, May 2009 only; any other held null stops the run
}
EXPECTED_SPAN_GVKEYS = 20          # data-quality guard in 04_scores.py: gvkeys whose rows span two PERMCOs; moved here from a hard-coded 20 (v3 review H5)
HEADLINE_SPEC = "spec_v3"             # v3 corrections (output/prereg_v3.md) sit on the spec_v2 pipeline; SPEC_V2 below still defines its mechanics             # designated by the user on 2026-11-02; v1 outputs are kept unchanged as the superseded first specification
SPEC_V2 = {                           # re-specification after external review; now the headline; v1 outputs stay untouched
    "label": "spec_v2",
    "output_dir": "output/spec_v2",
    "profit_field": "ib",             # net income before extraordinary items, as in the paper, replaces ni in ROA, CFO-ROA accruals and DROA; new raw pull
    "issuance_field": "sstk_net_of_prstkc",   # REVISED before any v2 return: F_EQ_OFFER = 1 if sstk - prstkc <= 0 (null counts 0), else 0. Literal sstk > 0 flagged 77% of firm-years (option-exercise proceeds), pass rate 20% against 81% in v1; it is kept as a reported sensitivity
    "issuance_sensitivity": "sstk_literal",   # F_EQ_OFFER = 1 only if sstk is 0 or null; run and reported beside, never chosen from
    "zero_debt_requires_lag2": True,  # ZERO_DEBT_COUNTS_AS_PASS stays, but only where the prior-year inputs for the change exist
    "fallback_availability": "exclude",  # a firm-year with no real 10-K filing date is unscorable; no 120-day fallback
    "availability_buffer_days": 3,    # filing date + this many calendar days must be on or before the formation date; an assumption
    "primary_benchmark": "equal_weight_all_included",   # scored and unscored included names; the scored-only benchmark is reported beside it
    "charge_every_trade": True,       # mid-period reinvestment after an exit is charged TRANSACTION_COST_BPS on the value reinvested, one side (the purchase), in the exit month; the exit itself is not a trade and an exit in the final holding month needs no reinvestment (CLAUDE.md 8f clarifications 7 and 10)
    "hac_lag_rule": "hac_lag_formula_floor_4_T_over_100_pow_2_9",        # the fixed formula floor(4 * (T / 100) ** (2 / 9)), which replaces the fixed 12 lags; NOT the data-dependent Newey-West (1994) bandwidth the key name suggests
    "small_sample": "t_distribution_T_minus_k",         # critical values and p-values from t with T - k degrees of freedom
    "primary_tests": ["raw_excess_vs_primary_benchmark", "mkt_smb_hml_mom"],   # six-factor alpha is secondary because RMW overlaps the screen
    "multiple_testing": "holm_over_prespecified_family",   # family: full period and the two SUBPERIODS from the original config
    "report_power": True,             # minimum detectable excess return and alpha at 80% power, 5% two-sided
    "sensitivities": ["hac_lag_12", "scored_only_benchmark"],   # as locked; the run also reports lag 6 and the T/(T-k) correction (keys below), all reported beside, never used to choose
    "alpha_level": 0.05,             # added after the first v2 returns, value already used by script 14: size of the power calculation
    "power_level": 0.80,             # added after the first v2 returns, value already used by script 14
    "sensitivity_lags": [6, 12],     # added after the first v2 returns: the two extra lag counts that script 14 reports beside the automatic lag
    "sensitivity_small_sample_correction": True,   # added after the first v2 returns: also report the automatic lag with covariance multiplied by T / (T - k)
}
V2_RERUNS = {                         # the three labelled v1-specification runs, rerun on spec_v2 inputs; locked 2026-11-02 before any rerun result
    "label": "spec_v2_reruns",
    "rule": "same definitions as EXTENSION_2026, REIT_LIQUIDITY_SUBSTITUTE and LONG_SHORT_100_100; only the inputs change to the spec_v2 scores, lists, benchmark and cost mechanics",
    "output_dirs": {"extension": "output/spec_v2/extension_2026", "reit": "output/spec_v2/reit_liquidity_substitute", "long_short": "output/spec_v2/long_short_100_100"},
    "extension_portfolio": "spec_v2 net rule, 2025 list, weights drifted to end-2025, held January-May 2026 with comp.secm trt1m under the four EXTENSION_2026 conditions",
    "reit_applies_to": "spec_v2 REIT rows where F_DLIQUID is the only uncomputable signal; ratio che / lt as in REIT_LIQUIDITY_SUBSTITUTE; ib, net issuance and the v2 availability rules apply to the other signals",
    "long_short_series": "gross High and gross Low from the spec_v2 net-rule run, with the LONG_SHORT_100_100 mechanics (annual reset at 0.50% and 2.00% borrow, monthly reset charged view, spread comparison), to December 2025 and to May 2026",
    "tests": "descriptive only: reported beside the v1-specification versions; not added to the Holm family; counted in the trial log",
    "no_new_rules": True,             # anything a rerun needs that no rule covers stops the run and goes to the master
}
BUFFER_FIRST_LIST = "top_500"      # 2005 has no history; membership tracks PERMCO on the pre-exclusion ranking
BUFFER_NULL_RETURN_RULE = "hold_flat" # no return, not an exit; sold at last value at the next rebalance: Comverse Technology, 2007-02 to 2007-05
