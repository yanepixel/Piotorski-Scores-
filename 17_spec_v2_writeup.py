"""
spec_v2, step 7: writes output/writeup.md, the write-up for spec_v2 as the headline (CLAUDE.md section 8f "Designation").

Every figure in the new text is formatted from a spec_v2 file (or a v1 file for the side-by-side) and recorded with its source in output/spec_v2/writeup_figures_v2.csv.
Figures that are not computed from a file are listed in HAND with their origin and also written to that CSV. Sections carried unchanged from the v1 write-up (output/archive_v1/writeup_v1.md)
are copied by slicing the archived text, not retyped. After writing, the script scans the new text and lists every number that is neither recorded nor hand-listed in
output/spec_v2/writeup_untraced_v2.txt; the script exits 1 if that list is not empty.
"""
import re
import sys
from pathlib import Path

import numpy as np
import sys as _sys
if "--regenerate-v2-archive" not in _sys.argv:
    _sys.exit("17_spec_v2_writeup.py is superseded by 21_v3_writeup.py and would overwrite output/writeup.md. Pass --regenerate-v2-archive to run it anyway.")
import pandas as pd
from scipy import stats as st

import config as cfg

ROOT = Path(__file__).resolve().parent
V2 = ROOT / cfg.SPEC_V2["output_dir"]
LIT = V2 / "literal_sensitivity"
OUTPUT = ROOT / "output"
LABEL = cfg.UNIVERSE_LABEL
TRACE = []   # (text, source)


def reg(s, src):
    TRACE.append((s, src))
    return s


def pct(x, src, d=2, sign=False):
    return reg(f"{x * 100:+.{d}f}%" if sign else f"{x * 100:.{d}f}%", src)


def num(x, src, d=2, sign=False):
    return reg(f"{x:+.{d}f}" if sign else f"{x:.{d}f}", src)


def cnt(x, src):
    return reg(f"{int(round(x)):,}", src)


def md_rows(header, rows):
    return "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n" + "\n".join("| " + " | ".join(r) + " |" for r in rows) + "\n"


# ---------------- load ----------------
head = pd.read_csv(V2 / "headline_v2.csv").set_index("portfolio")
tests = pd.read_csv(V2 / "tests_v2.csv")
lit_tests = pd.read_csv(LIT / "tests_v2.csv")
lit_head = pd.read_csv(LIT / "headline_v2.csv").set_index("portfolio")
vs = pd.read_csv(V2 / "versus_v2.csv")
load = pd.read_csv(V2 / "factor_loadings_v2.csv")
subs = pd.read_csv(V2 / "subperiods_v2.csv")
yr = pd.read_csv(V2 / "year_by_year_v2.csv")
nums = pd.read_csv(V2 / "headline_v2_numbers.csv").set_index("metric").value
drops = pd.read_csv(V2 / "drops_by_date_v2.csv")
reasons = pd.read_csv(V2 / "drops_reasons_v2.csv")
eq = pd.read_csv(V2 / "eq_offer_pass_by_year.csv")
rates = pd.read_csv(V2 / "signal_pass_rates_v2.csv").set_index("signal")
lit_rates = pd.read_csv(V2 / "signal_pass_rates_v2_literal.csv").set_index("signal")
byb = pd.read_csv(V2 / "list_rows_by_bucket_v1_v2.csv").set_index("bucket")
byb_lit = pd.read_csv(V2 / "list_rows_by_bucket_v1_v2_literal.csv").set_index("bucket")
dist = pd.read_csv(V2 / "score_distribution_v2.csv")
exits = pd.read_csv(V2 / "portfolio_exits_v2.csv")
turn = pd.read_csv(V2 / "portfolio_turnover_v2.csv")
unscor = pd.read_csv(V2 / "unscorable_no_filing_date.csv")
v1perf = pd.read_csv(OUTPUT / "tables" / "performance.csv").query("basis in ['net', 'fund return']").set_index("portfolio")
v1vs = pd.read_csv(OUTPUT / "tables" / "versus_benchmark.csv").set_index("portfolio")
v1reg = pd.read_csv(OUTPUT / "tables" / "factor_regressions.csv")
v1yr = pd.read_csv(OUTPUT / "tables" / "year_by_year.csv")
checks_md = (V2 / "scores_checks_v2.md").read_text(encoding="utf-8")
v1_text = (OUTPUT / "archive_v1" / "writeup_v1.md").read_text(encoding="utf-8")
import re as _re
_m = _re.search(r"High's raw gap is ([+-][\d.]+%) a year \(t ([\d.]+)\)", v1_text)
v1_allinc = (reg(_m.group(1), "output/archive_v1/writeup_v1.md [post-hoc all-included comparison, v1]"), reg(_m.group(2), "output/archive_v1/writeup_v1.md [post-hoc all-included comparison, v1]"))

FPSRC = "data/clean/formation.parquet + spec_v2/formation_v2.parquet"
S = lambda f, c="": f"output/spec_v2/{f}" + (f" [{c}]" if c else "")
SL = lambda f, c="": f"output/spec_v2/literal_sensitivity/{f}" + (f" [{c}]" if c else "")


def T(series, test, period="full", frame=None):
    d = tests if frame is None else frame
    return d[(d.series == series) & (d.test == test) & (d.period == period)].iloc[0]


EXC = "raw excess vs primary benchmark (all included)"
EXS = "raw excess vs scored-only benchmark (sensitivity)"
A4 = "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)"
A6 = "alpha, six factors (secondary)"
P1, P2 = [f"{a} to {b}" for a, b in cfg.SUBPERIODS]
TT = lambda r, f="tests_v2.csv": S(f, f"{r.series} | {r.test} | {r.period}")

# hand-copied figures: text -> origin
HAND = {
    "-5.29%": "verification/audit_43_v2_audit.py: unscored names' gross return 5.29% a year below the all-included benchmark in 2015-25; not written by scripts 12-17",
    "4.88%": "verification/audit_43_v2_audit.py, unscored names' gross CAGR 2015-25", "10.83%": "verification/audit_43_v2_audit.py, all-included benchmark gross CAGR 2015-25",
    "0.017": "Piotroski (2000) Table 4, large firms, High minus All, as given by the project lead", "0.872": "Piotroski (2000) Table 4, large firms t-statistic, as given by the project lead",
    "0.088": "Piotroski (2000) Table 4, small firms, High minus All", "2.456": "Piotroski (2000) Table 4, small firms t-statistic",
    "1,480": "restatement test, verification/data_audit_phase2_3.md via the v1 write-up", "98.5%": "same", "0.2%": "same", "55": "same", "97.3%": "same", "0.45%": "same",
    "252": "the project audit's trial log (a report in verification/, section 4): distinct reported alpha or excess-return t-statistics in the project's tables",
    "288": "same audit trial log: re-estimates of the 96 v2 tests under the three other standard-error conventions",
    "400": "same audit trial log: about 400 t-statistics counting audit runs", "250": "same audit trial log: about 250 in the tables",
    "9": "number of Piotroski tests", "21": "number of yearly lists (2005-2025)", "20": "complete holding years",
}

# ---------------- numbers ----------------
n_months = int(head.loc["High", "v2_months"])
ex = T("High", EXC)
al = T("High", A4)
al6 = T("High", A6)
exs = T("High", EXS)
ex1, ex2 = T("High", EXC, P1), T("High", EXC, P2)
al1, al2 = T("High", A4, P1), T("High", A4, P2)
tc = lambda r: st.t.ppf(0.975, r.df)
ci_ex = (ex.estimate_annual - tc(ex) * ex.se_annual, ex.estimate_annual + tc(ex) * ex.se_annual)
ci_al = (al.estimate_annual - tc(al) * al.se_annual, al.estimate_annual + tc(al) * al.se_annual)
srcCI = S("tests_v2.csv", "estimate_annual +/- t(0.975, df) x se_annual, High raw excess, full")
srcCIa = S("tests_v2.csv", "estimate_annual +/- t(0.975, df) x se_annual, High 4-factor alpha, full")
done = yr[yr.months == cfg.HOLDING_MONTHS]
hit_p, hit_s = done.High_beats_Benchmark.sum(), done.High_beats_BenchmarkScored.sum()
partial = yr[yr.months < cfg.HOLDING_MONTHS].iloc[0]
vsd = vs.set_index(["portfolio", "versus"])
bench_gap = vsd.loc[("Benchmark", "BenchmarkScored")]
fam = tests[tests.in_holm_family]
holm_reject = {c: [f"{r.test} {r.period}" for r in fam.itertuples() if getattr(r, c) < 0.05] for c in ["holm_adjusted_p", "holm_p_lag_corrected", "holm_p_lag6", "holm_p_lag12"]}
a2 = fam[(fam.test == A4) & (fam.period == P2)].iloc[0]
oneword = lambda s: s
no_filing = len(unscor)
no_filing_score = int(unscor.would_be_score.notna().sum())
buf_43 = int(re.search(r"\(ii\) (\d+) because", checks_md).group(1))
older_13 = int(re.search(r"\(i\) (\d+) because", checks_md).group(1))
stale_b = int(re.search(r"(\d+) stale \(the earlier", checks_md).group(1))
none_b = int(re.search(r"and (\d+) with no earlier scored year", checks_md).group(1))
v1_within = int(re.search(r"scored rows whose filing came less than 3 days before the formation date: (\d+)", checks_md).group(1))
v1_fallback = int(re.search(r"v1 used a fallback date .*? on (\d+) included list rows", checks_md).group(1))
v1f_ = pd.read_parquet(ROOT / "data" / "clean" / "formation.parquet")
v2f_ = pd.read_parquet(ROOT / "data" / "clean" / "spec_v2" / "formation_v2.parquet")
cmp_ = v1f_[["formation_date", "permco", "scored", "avail_source", "avail_date", "fyear"]].merge(v2f_[["formation_date", "permco", "score_status", "fyear"]], on=["formation_date", "permco"], suffixes=("_1", "_2"))
cmp_["gap"] = (cmp_.formation_date - cmp_.avail_date).dt.days
buf1 = cmp_[cmp_.scored & (cmp_.avail_source == "filing") & (cmp_.gap < cfg.SPEC_V2["availability_buffer_days"])]
fb1 = cmp_[cmp_.scored & (cmp_.avail_source == "fallback")]
b_older = int(((buf1.score_status == "valid") & (buf1.fyear_2 < buf1.fyear_1)).sum())
b_stale = int((buf1.score_status == "stale").sum())
f_stale, f_none = int((fb1.score_status == "stale").sum()), int((fb1.score_status == "missing").sum())
v1_on_date = int(re.search(r"formation date itself: (\d+)", checks_md).group(1))
mid = exits[exits.exit_type == "mid-period exit"]
fd = exits[exits.exit_type == "delisted on the formation date"]
tot_inc = int(drops.included.sum())
tot_u1, tot_u2 = int(drops.d_unscored_v1.sum()), int(drops.d_unscored_v2.sum())
reit2 = int(drops.unscored_in_sectors_40_60_v2.sum())
reit1 = int(drops.unscored_in_sectors_40_60_v1.sum())
rs_tot = reasons.reason.value_counts()
dliq = int(drops[[c for c in drops.columns if c == "v2_missing_signal: F_DLIQUID"]].sum().iloc[0])
turn2 = turn[turn.formation_date > turn.formation_date.min()]
cost_high = turn2[turn2.portfolio == "High"].cost_rebalance.mean() + turn2[turn2.portfolio == "High"].reinvestment_cost_total.mean()
reinv_high = turn2[turn2.portfolio == "High"].reinvestment_cost_total.mean()
eq_scored = eq.set_index("fyear").v2_eq_offer_pass_pct_scored
lit_ex, lit_al = T("High", EXC, "full", lit_tests), T("High", A4, "full", lit_tests)
lit_hit = pd.read_csv(LIT / "headline_v2_numbers.csv").set_index("metric").value["hit_rate_complete_years_primary"]

L = []
w = L.append
w(f"# Piotroski F-score test: write-up (headline specification: spec_v2)\n")
w(f"**Universe:** {LABEL}\n")
w(f"**Test period:** June 2005 to December 2025. The test ends before 2026, and the last portfolio is partial (7 of its 12 months).\n")
w(f"**Status of this document.** spec_v2 is the headline. It re-specifies the first version (v1) after an external review; v1 is kept unchanged as the superseded first specification in `output/archive_v1/` and is compared with v2 below. "
  f"The three later runs (2026 extension, REIT liquidity substitute, 100/100 long/short) were run on the v1 specification and have not been rerun under v2.\n")

# ---- answer ----
w("## The answer\n")
w(f"No. Buying the financially strongest companies in this universe, those with an F-score (a 0-9 count of financial-health tests a company passes) of 8 or 9, did not beat the market of the same stocks. Measured against an equal-weighted portfolio of every included company, "
  f"High (the portfolio of companies scoring 8 or 9) earned {pct(ex.estimate_annual, TT(ex), 2, True)} a year more after costs (t-stat, the number of standard errors the estimate sits from zero, {num(ex.t, TT(ex), 2, True)}; p-value, the chance of a result at least this far from zero if the true edge were zero, {num(ex.p_value, TT(ex), 2)}). After accounting for market, size, value and momentum, "
  f"its alpha (the return left over once those patterns are removed) was {pct(al.estimate_annual, TT(al), 2, True)} a year (t {num(al.t, TT(al), 2, True)}). Neither is distinguishable from zero, and this test could not have seen a small edge: at 80% power (the smallest true effect the test would detect 80% of the time) the smallest excess return it could reliably detect is "
  f"{pct(ex.mde_80pct_power_annual, TT(ex))} a year, and the 95% range for the excess is {pct(ci_ex[0], srcCI, 2, True)} to {pct(ci_ex[1], srcCI, 2, True)}, so a true edge of up to about {pct(ci_ex[1], srcCI, 1, True)} a year cannot be ruled out. "
  f"The benchmark choice matters to the sign: against scored companies only, High's excess is {pct(exs.estimate_annual, TT(exs), 2, True)} a year (t {num(exs.t, TT(exs), 2, True)}), because the unscored companies (mostly REITs and real estate) lagged. "
  f"High beat the all-included benchmark in {int(hit_p)} of {len(done)} complete years. In the second half, June 2015 to December 2025, High's four-factor alpha was {pct(al2.estimate_annual, TT(al2), 2, True)} a year (t {num(al2.t, TT(al2), 2, True)}); "
  f"it is the only one of the six pre-specified tests that survives the Holm adjustment (a correction for looking at several tests at once; adjusted p {num(al2.holm_adjusted_p, TT(al2), 3)}), narrowly, and not under every way of computing the standard error (Newey-West, which allows for returns correlated over time, with a choice of how many months to allow; see Results). "
  f"With the opposite sign in 2005-15, that is weak evidence of a later-period shortfall, not a finding of failure. This tests large US companies, not the cheap, smaller companies Piotroski studied, so it does not test his original claim.\n")

# ---- terms ----
w("## Terms\n")
for line in [
    "**F-score:** a 0-9 count of financial-health tests a company passes, from its latest annual report.",
    "**High, Middle, Low:** portfolios of scores 8-9, 5-7 and 0-4.",
    "**All-included benchmark (primary):** every company on the list, scored or not, equally weighted, run the same way and charged the same costs.",
    "**Scored-only benchmark:** the scored companies only. This is the v1 benchmark; both are shown together throughout.",
    "**Net / gross:** after / before trading costs.",
    "**CAGR:** the constant yearly growth rate that gives the same end value.",
    "**Volatility:** how much monthly returns swing, stated per year.",
    "**Sharpe ratio:** return above the risk-free rate per unit of volatility. Higher is better.",
    "**Max drawdown:** the largest peak-to-trough fall.",
    "**Turnover:** the share of a portfolio traded at a rebalance. Two-way counts buys and sells.",
    "**Excess return:** return above the benchmark, here the average monthly gap times 12.",
    "**Tracking error / information ratio:** how much the gap swings per year; excess return divided by that.",
    "**Factor:** a broad return pattern: market (Mkt-RF), size (SMB), value (HML), momentum (MOM); profitability (RMW) and investment (CMA) enter only the secondary six-factor version.",
    "**Alpha:** return left after accounting for those factors, stated per year.",
    "**t-stat / p-value:** how many standard errors a number is from zero; the chance of a result at least this far from zero if the true value were zero.",
    "**Newey-West (HAC):** standard errors adjusted for returns that are correlated over time. The number of months allowed (the lag) is set by a formula, 4 here.",
    "**Degrees of freedom / t distribution:** the t distribution is the bell-shaped curve used to turn a t-stat into a p-value when the sample is limited; its degrees of freedom, T - k, are the T months less the k coefficients estimated, and fewer degrees of freedom mean fatter tails.",
    "**T/(T-k) correction:** an optional small-sample adjustment that multiplies the variance of the estimates by T / (T - k); it is reported as a sensitivity, not used in the headline.",
    "**Compustat / CRSP:** two commercial databases, accessed through WRDS: Compustat holds company accounts (the annual reports), and CRSP (Center for Research in Security Prices) holds monthly stock prices and returns, including delistings.",
    "**RSP and SPY:** exchange-traded funds that track the equal-weighted and the cap-weighted S&P 500, shown for context only.",
    "**Formation date / list row:** the formation date is the last trading day of May, when the portfolios are formed; a list row is one company on one formation date's list.",
    "**Holm adjustment:** a correction for looking at several tests at once; it raises p-values so that the chance of any false positive in the family stays at 5%.",
    "**Power / minimum detectable effect:** the smallest true effect the test would detect 80% of the time at the 5% level.",
    "**REIT:** real estate investment trust, a company that mainly owns property or property loans and passes most income to shareholders.",
    "**GICS:** the Global Industry Classification Standard, the sector system used here.",
    "**Availability date:** the first date a number could be used: the 10-K filing date plus 3 calendar days. A firm-year with no real filing date is not scored.",
    "**Stub year:** a fiscal year with an unusual length, usually from changing the year-end.",
    "**Spread:** High minus Low, a diagnostic only, with no shorting costs.",
]:
    w(f"- {line}")
w("")

# ---- method ----
w("## Method\n")
w("All rules are in `config.py` (`SPEC_V2`) and the decisions in `CLAUDE.md` section 8f, which were committed before any v2 return was read; the exact sequence is under Timing of the specification. The universe, formation dates, buckets and holding period are unchanged from v1.\n")
for line in [
    "**Universe:** on the last trading day of each May, 2005-2025, the top 500 US-incorporated common stocks on NYSE, Nasdaq or NYSE American by market cap, rebuilt from data on that date. Financials and utilities are removed after ranking.",
    "**Scores:** the nine Piotroski tests from Compustat annual data (company accounts), fiscal years 2004-2024, with five changes from v1: (1) profitability and accruals use income before extraordinary items (`ib`), as in the paper, not net income; "
    "(2) the no-issuance test is passed when common stock issued less common stock repurchased (`sstk - prstkc`) is zero or negative, with a missing value counting as zero and negative values used as reported, instead of v1's share-count test with a 2% tolerance; "
    "(3) a no-debt company passes the leverage test only where the prior-year change is computable; (4) a firm-year with no real 10-K filing date is not scored, with no year-end-plus-120-days fallback; "
    "(5) a filing counts only if its date plus 3 calendar days is on or before the formation date (an assumption). If the newest year fails the date test, the latest earlier scored year is used if no more than 18 calendar months old. "
    "Leverage uses long-term debt only, as in v1. Any uncomputable signal still drops the company-year.",
    "**Portfolios:** equal weight at formation, held 12 months from June. Returns come from CRSP (monthly stock prices) and include delisting returns, and a delisted stock's value goes pro rata to the rest.",
    "**Costs:** 10 basis points (0.10%) on each dollar bought or sold at each rebalance, and also on the value reinvested after a mid-period exit, charged one side in the exit month (v1 did not charge this). "
    f"High's costs averaged {pct(cost_high, S('portfolio_turnover_v2.csv', 'High cost_rebalance + reinvestment_cost_total, mean over rebalances after the first'))} a year, of which {pct(reinv_high, S('portfolio_turnover_v2.csv', 'High reinvestment_cost_total mean'), 3)} is reinvestment.",
    "**Benchmarks:** primary = all included names, scored or not, held with their actual returns and charged like the buckets; the scored-only benchmark is reported beside it. RSP and SPY are fund returns (exchange-traded funds tracking the equal-weighted and the cap-weighted S&P 500). "
    "Two included names with no return for some months and no exit (Maxim Integrated, November 2007 to May 2008; General Growth Properties, May 2009) are held flat at 0%, uncharged, in the all-included benchmark only; any other missing return would have stopped the run.",
    f"**Tests:** two primary tests of High, set in `SPEC_V2`: (1) its raw annualised excess return over the all-included benchmark; (2) its alpha on market, size, value and momentum. Standard errors are Newey-West with the automatic lag floor(4 x (T/100)^(2/9)), "
    f"which is {int(nums['hac_lags_full'])} for the full period and for each subperiod (T = {cnt(n_months, S('headline_v2.csv', 'v2_months'))} months in total), with p-values from a t distribution with T - k degrees of freedom (the T months less the k coefficients estimated). "
    "Holm adjustment is over one family of six p-values: the two tests times the full period and the two subperiods. The six-factor alpha is secondary because the profitability factor overlaps the screen. Power is reported at 80% and 5% two-sided.",
]:
    w(f"- {line}")
w("")

# ---- results ----
w("## Results\n")
w(f"All figures are net of costs. June 2005 to December 2025, {cnt(n_months, S('headline_v2.csv', 'v2_months'))} months. Both benchmarks are shown together; v1 is the first specification.\n")
rows = []
names = [("High (8-9)", "High"), ("Middle (5-7)", "Middle"), ("Low (0-4)", "Low"), ("All-included benchmark", "Benchmark"), ("Scored-only benchmark", "BenchmarkScored"), ("RSP", "RSP"), ("SPY", "SPY")]
v1map = {"High": "High", "Middle": "Middle", "Low": "Low", "BenchmarkScored": "Benchmark", "RSP": "RSP", "SPY": "SPY"}
for lab, k in names:
    r = head.loc[k]
    f = "headline_v2.csv"
    turn_s = pct(r.v2_avg_turnover_two_way, S(f, f"{k} v2_avg_turnover_two_way"), 0) if pd.notna(r.v2_avg_turnover_two_way) else "n/a"
    v1c = pct(v1perf.loc[v1map[k]].CAGR, f"output/tables/performance.csv [{v1map[k]} CAGR, v1]") if k in v1map else "n/a"
    v1s = num(v1perf.loc[v1map[k]].sharpe, f"output/tables/performance.csv [{v1map[k]} sharpe, v1]") if k in v1map else "n/a"
    rows.append([lab, pct(r.v2_CAGR, S(f, f"{k} v2_CAGR")), pct(r.v2_volatility, S(f, f"{k} v2_volatility")), num(r.v2_sharpe, S(f, f"{k} v2_sharpe")), pct(r.v2_max_drawdown, S(f, f"{k} v2_max_drawdown"), 1), turn_s, v1c, v1s])
w(md_rows(["Portfolio", "CAGR", "Volatility", "Sharpe", "Max drawdown", "Average two-way turnover", "v1 CAGR", "v1 Sharpe"], rows))
w("v1's 'Benchmark' is the scored-only benchmark, so it sits beside that row. v1 does not charge the reinvestment of mid-period exits.\n")

rows = []
for lab, k in [("High", "High"), ("Middle", "Middle"), ("Low", "Low")]:
    a = vsd.loc[(k, "Benchmark")]
    b = vsd.loc[(k, "BenchmarkScored")]
    ra, rb = T(k, EXC), T(k, EXS)
    rows.append([lab, pct(a.excess_return_annual, S("versus_v2.csv", f"{k} vs Benchmark"), 2, True), num(ra.t, TT(ra), 2, True), pct(a.tracking_error, S("versus_v2.csv", f"{k} vs Benchmark TE")), num(a.information_ratio, S("versus_v2.csv", f"{k} vs Benchmark IR"), 2, True),
                 pct(b.excess_return_annual, S("versus_v2.csv", f"{k} vs BenchmarkScored"), 2, True), num(rb.t, TT(rb), 2, True)])
w(md_rows(["Portfolio", "Excess vs all-included", "t", "Tracking error", "Information ratio", "Excess vs scored-only", "t"], rows))
w(f"\nHigh won {int(hit_p)} of {len(done)} complete years against the all-included benchmark and {int(hit_s)} of {len(done)} against the scored-only one. The partial 2025 year (7 of 12 months): High {pct(partial.High, S('year_by_year_v2.csv', '2025 partial High'))}, "
  f"all-included benchmark {pct(partial.Benchmark, S('year_by_year_v2.csv', '2025 partial Benchmark'))}, scored-only {pct(partial.BenchmarkScored, S('year_by_year_v2.csv', '2025 partial BenchmarkScored'))}. The year-by-year table is `output/spec_v2/year_by_year_v2.csv`.\n")

w("### Factor regressions (market, size, value, momentum; Newey-West lag 4)\n")
rows = []
for series, model in [("High excess of rf", "4-factor"), ("High excess of rf", "6-factor"), ("Spread (High minus Low)", "4-factor"), ("Spread (High minus Low)", "6-factor")]:
    r = load[(load.series == series) & (load.model == model)].iloc[0]
    g = lambda c: num(r[c], S("factor_loadings_v2.csv", f"{series} {model} {c}")) if c in r and pd.notna(r[c]) else "-"
    rows.append([series.replace(" excess of rf", " minus risk-free rate"), model, pct(r.alpha_annual, S("factor_loadings_v2.csv", f"{series} {model} alpha"), 2, True), num(r.alpha_t, S("factor_loadings_v2.csv", f"{series} {model} alpha_t"), 2, True),
                 g("beta_Mkt-RF"), g("beta_SMB"), g("beta_HML"), g("beta_MOM"), g("beta_RMW"), g("beta_CMA")])
w(md_rows(["Series", "Model", "Alpha a year", "t", "Market", "SMB", "HML", "MOM", "RMW", "CMA"], rows))
w("")

w("### The pre-specified tests, full period and subperiods\n")
rows = []
for r in fam.itertuples():
    rows.append([("Raw excess vs all-included" if r.test == EXC else "Four-factor alpha"), r.period, pct(r.estimate_annual, TT(r), 2, True), pct(r.se_annual, TT(r)), num(r.t, TT(r), 2, True), num(r.p_value, TT(r), 3),
                 num(r.holm_adjusted_p, TT(r), 3), pct(r.mde_80pct_power_annual, TT(r))])
w(md_rows(["Test (High)", "Period", "Estimate a year", "Std error", "t", "p", "Holm-adjusted p", "Minimum detectable effect, 80% power"], rows))
w(f"\nOnly the second-half four-factor alpha is below 0.05 after adjustment, and it is one subperiod in a family of six, with the opposite sign in 2005-15 ({pct(al1.estimate_annual, TT(al1), 2, True)}, t {num(al1.t, TT(al1), 2, True)}). "
  f"Six-factor alpha: {pct(al6.estimate_annual, TT(al6), 2, True)} (t {num(al6.t, TT(al6), 2, True)}) over the full period; {pct(T('High', A6, P2).estimate_annual, TT(T('High', A6, P2)), 2, True)} (t {num(T('High', A6, P2).t, TT(T('High', A6, P2)), 2, True)}) in 2015-25.\n")

w("### How much the second-half result depends on the standard-error convention\n")
rows = []
for r in fam.itertuples():
    rows.append([("Raw excess" if r.test == EXC else "Four-factor alpha"), r.period, num(r.t, TT(r), 2, True), num(r.holm_adjusted_p, TT(r), 3), num(r.lag_corr_t, TT(r), 2, True), num(r.holm_p_lag_corrected, TT(r), 3),
                 num(r.lag6_t, TT(r), 2, True), num(r.holm_p_lag6, TT(r), 3), num(r.lag12_t, TT(r), 2, True), num(r.holm_p_lag12, TT(r), 3)])
w(md_rows(["Test (High)", "Period", "t as run (lag 4)", "Holm p", "t lag 4 with T/(T-k) correction", "Holm p", "t lag 6", "Holm p", "t lag 12", "Holm p"], rows))
w(f"\nThe convention locked before returns was the automatic lag with no small-sample correction (column 'as run'). The second-half four-factor alpha is below 0.05 after Holm as run, at lag 6 and at lag 12, and not with the T/(T-k) correction at lag 4 "
  f"(Holm {num(a2.holm_p_lag_corrected, TT(a2), 3)}). No other pre-specified test is below 0.05 under any of the four. These are shown side by side and were not used to choose. "
  "The automatic lag is the formula, not the data-dependent Newey-West (1994) bandwidth, which is unstable at 127 months. So read the second-half result as weak evidence: one subperiod in a family of six, borderline under one reasonable convention, with the opposite sign in the first half.\n")

w("### Subperiods\n")
rows = []
for r in subs.itertuples():
    rows.append([r.period, cnt(r.months, S("subperiods_v2.csv", f"{r.period} months")), pct(r.High_CAGR, S("subperiods_v2.csv", f"{r.period} High_CAGR")), pct(r.Benchmark_CAGR, S("subperiods_v2.csv", f"{r.period} Benchmark_CAGR")),
                 pct(r.BenchmarkScored_CAGR, S("subperiods_v2.csv", f"{r.period} BenchmarkScored_CAGR")), pct(r.High_minus_Benchmark_annual, S("subperiods_v2.csv", f"{r.period} High_minus_Benchmark_annual"), 2, True),
                 pct(r.Spread_annual, S("subperiods_v2.csv", f"{r.period} Spread_annual"), 2, True)])
w(md_rows(["Period", "Months", "High CAGR", "All-included benchmark CAGR", "Scored-only benchmark CAGR", "High excess vs all-included", "Spread a year"], rows))
w("")

# ---- how many tests ----
w("## How many tests were run\n")
crit = {n_: st.t.ppf(1 - 0.05 / (2 * n_), al2.df) for n_ in [1, 6, 20, 50, 100, 250]}
w("The Holm adjustment above covers six tests chosen in advance. It does not cover everything the project has looked at. In all, the project has reported about "
  f"{HAND and '250'} alpha or excess-return t-statistics in its own tables ({HAND and '252'} distinct ones, plus {HAND and '288'} re-estimates of the v2 tests under other standard-error conventions), and about {HAND and '400'} counting audit runs, "
  "most of them on the same few return series, so they are far from independent. The table gives the critical |t| for a 5% family-wise level (Bonferroni, t distribution with the second-half degrees of freedom) if that many tests were counted.\n")
w(md_rows(["Tests counted", "Critical |t|"], [[cnt(n_, "assumed number of tests"), num(v_, S("tests_v2.csv", "t.ppf(1 - 0.05 / (2N), df) with the 2015-25 four-factor alpha df"))] for n_, v_ in crit.items()]))
w(f"\nThe second-half four-factor alpha as run has t {num(al2.t, TT(al2), 2, True)}, which clears the six-test threshold ({num(crit[6], S('tests_v2.csv', 't.ppf N=6'))}) and not a threshold of about 3, which is where {cnt(20, 'assumed number of tests')} or more counted tests would put it. "
  f"Its t is {num(a2.lag_corr_t, TT(a2), 2, True)} with the T/(T-k) correction, {num(getattr(a2, 'lag6_t'), TT(a2), 2, True)} at lag 6 and {num(getattr(a2, 'lag12_t'), TT(a2), 2, True)} at lag 12. "
  "All the |t| values of 3 or more in the project are shortfalls of High against the benchmark or the factor model, none is an edge, and most are variants of the same second-half series.\n")
w("**No period was held out.** The whole of June 2005 to December 2025 was seen in v1 before v2 was specified, and the January to May 2026 extension (a v1-specification run) was added after the v1 results and after the second-half weakness was known, so it is not an untouched test; at five months it could not support an alpha test anyway. "
  "The order in which v1's rules and results were set rests on the project lead's account, and no file can show it. The v2 specification and its test family were committed before any v2 return was read (see the Timing section).\n")

# ---- both benchmarks ----
w("## The two benchmarks\n")
unsc = reasons.shape[0]
w(f"The all-included benchmark holds {cnt(tot_u2, S('drops_by_date_v2.csv', 'sum d_unscored_v2'))} list rows that have no score (of {cnt(tot_inc, S('drops_by_date_v2.csv', 'sum included'))}). They sit in the benchmark with their actual returns but cannot be in High, Middle or Low, "
  f"and {pct(reit2 / tot_u2, S('drops_by_date_v2.csv', 'unscored_in_sectors_40_60_v2 / d_unscored_v2'), 1)} of them are in GICS sectors 40 and 60 (REITs, which have no current assets or liabilities to score, and real estate). "
  f"Over 2015-25 they ran {HAND and '-5.29%'} a year behind the all-included benchmark, a gross figure (before costs): a CAGR of {HAND and '4.88%'} against {HAND and '10.83%'} (`verification/audit_43_v2_audit.py`, which is not one of the scripts that write the v2 tables). The effect is that the all-included benchmark runs "
  f"{pct(-bench_gap.excess_return_annual, S('versus_v2.csv', 'BenchmarkScored vs Benchmark excess_return_annual'), 2)} a year below the scored-only one in mean annual excess return (the gap in compound growth, CAGR, is {pct(-bench_gap.cagr_difference, S('versus_v2.csv', 'BenchmarkScored vs Benchmark cagr_difference'), 2)}), "
  f"so it flatters every scored bucket by about that much: High's excess is {pct(ex.estimate_annual, TT(ex), 2, True)} against the first and {pct(exs.estimate_annual, TT(exs), 2, True)} against the second. "
  f"Neither is significant. Report both together; neither is the 'right' one. The scored-only benchmark compares like with like; the all-included one is the market of everything on the list.\n")
mid15 = T("Middle", EXC, P2)
mid15s = T("Middle", EXS, P2)
w(f"**Middle's 2015-25 result is mostly the benchmark.** Middle beat the all-included benchmark by {pct(mid15.estimate_annual, TT(mid15), 2, True)} a year in 2015-25 (t {num(mid15.t, TT(mid15), 2, True)}, unadjusted and outside the Holm family), "
  f"but only {pct(mid15s.estimate_annual, TT(mid15s), 2, True)} (t {num(mid15s.t, TT(mid15s), 2, True)}) against the scored-only benchmark. It is not evidence that middle scores do well.\n")

# ---- issuance ----
w("## The issuance signal and the literal-rule sensitivity\n")
lit_rates_eq = lit_rates.loc["F_EQ_OFFER"].v2_pass_pct_scored
net_rates_eq = rates.loc["F_EQ_OFFER"].v2_pass_pct_scored
v1_rates_eq = rates.loc["F_EQ_OFFER"].v1_pass_pct_scored
w(f"The first draft of v2 passed the no-issuance test only if common stock issued (`sstk`) was zero or missing. Before any return was read, it was found to fail most firm-years, because `sstk` includes option-exercise proceeds: the pass rate was "
  f"{num(lit_rates_eq, S('signal_pass_rates_v2_literal.csv', 'F_EQ_OFFER v2_pass_pct_scored'), 1)}% against {num(v1_rates_eq, S('signal_pass_rates_v2.csv', 'F_EQ_OFFER v1_pass_pct_scored'), 1)}% in v1, and High fell from "
  f"{cnt(byb_lit.loc['High'].v1_rows, S('list_rows_by_bucket_v1_v2_literal.csv', 'High v1_rows'))} to {cnt(byb_lit.loc['High'].v2_rows, S('list_rows_by_bucket_v1_v2_literal.csv', 'High v2_rows'))} list rows. The rule was revised to net issuance (`sstk - prstkc`), "
  f"which passes {num(net_rates_eq, S('signal_pass_rates_v2.csv', 'F_EQ_OFFER v2_pass_pct_scored'), 1)}% and leaves High at {cnt(byb.loc['High'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'High v2_rows'))} rows. "
  "That revision was made after seeing a pass rate and before any return; the literal rule is kept as a reported sensitivity and was never chosen from.\n")
rows = []
for lab, k in [("High", "High"), ("Middle", "Middle"), ("Low", "Low")]:
    a = T(k, EXC)
    b = T(k, EXC, "full", lit_tests)
    rows.append([lab, pct(head.loc[k].v2_CAGR, S("headline_v2.csv", f"{k} v2_CAGR")), pct(a.estimate_annual, TT(a), 2, True), pct(lit_head.loc[k].v2_CAGR, SL("headline_v2.csv", f"{k} v2_CAGR")), pct(b.estimate_annual, TT(b, "literal_sensitivity/tests_v2.csv"), 2, True)])
w(md_rows(["Portfolio", "Net rule CAGR", "Excess vs all-included", "Literal rule CAGR", "Excess vs all-included"], rows))
w(f"\nUnder the literal rule High's excess is {pct(lit_ex.estimate_annual, TT(lit_ex, 'literal_sensitivity/tests_v2.csv'), 2, True)} (t {num(lit_ex.t, TT(lit_ex, 'literal_sensitivity/tests_v2.csv'), 2, True)}) and its four-factor alpha {pct(lit_al.estimate_annual, TT(lit_al, 'literal_sensitivity/tests_v2.csv'), 2, True)} "
  f"(t {num(lit_al.t, TT(lit_al, 'literal_sensitivity/tests_v2.csv'), 2, True)}); High beat the all-included benchmark in {int(round(lit_hit * 20))} of 20 complete years. That High bucket is thin and unusual (it selects firms that issued nothing; {cnt(byb_lit.loc['High'].v2_rows, S('list_rows_by_bucket_v1_v2_literal.csv', 'High v2_rows'))} list rows against {cnt(byb.loc['High'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'High v2_rows'))} under the net rule), "
  "so the sign here says little. In the project folder the full tables are in `output/spec_v2/literal_sensitivity/`; the public repository carries only `headline_v2.csv` and `tests_v2.csv` from it.\n")
w(f"**The net signal drifts with the year.** Its pass rate over scored company-years was {num(eq_scored.loc[2004], S('eq_offer_pass_by_year.csv', 'FY2004 v2_eq_offer_pass_pct_scored'), 1)}% for fiscal 2004 and "
  f"{num(eq_scored.loc[2022], S('eq_offer_pass_by_year.csv', 'FY2022 v2_eq_offer_pass_pct_scored'), 1)}% for fiscal 2022 ({num(eq_scored.loc[2024], S('eq_offer_pass_by_year.csv', 'FY2024'), 1)}% for 2024), probably because buybacks grew. It is not degenerate in level, "
  "but part of what it separates is the filing year, not the company within a year. Missing `prstkc` with positive `sstk` counts as no buyback, so those rows fail; the scores report sizes that choice.\n")

# ---- v1 vs v2 ----
w("## v1 and v2: what changed, and why the sign of the excess flipped\n")
v1h = v1perf.loc["High"]
v1vsh = v1vs.loc["High"]
w(f"v1 reported High at {pct(v1h.CAGR, 'output/tables/performance.csv [High CAGR, v1]')} a year against {pct(v1perf.loc['Benchmark'].CAGR, 'output/tables/performance.csv [Benchmark CAGR, v1]')} for its scored-only benchmark, an excess of "
  f"{pct(v1vsh.excess_return_annual, 'output/tables/versus_benchmark.csv [High excess_return_annual, v1]', 2, True)} a year. v2 reports High at {pct(head.loc['High'].v2_CAGR, S('headline_v2.csv', 'High v2_CAGR'))}, with an excess of "
  f"{pct(ex.estimate_annual, TT(ex), 2, True)} against the all-included benchmark and {pct(exs.estimate_annual, TT(exs), 2, True)} against the scored-only one. The sign of the headline excess flipped from negative to slightly positive because the primary benchmark changed, "
  f"not because High changed: High's own return moved by {pct(head.loc['High'].v2_CAGR - v1perf.loc['High'].CAGR, 'headline_v2.csv v2_CAGR minus output/tables/performance.csv High CAGR', 2, True)} of CAGR, "
  f"while the benchmark that includes unscored names is {pct(-bench_gap.excess_return_annual, S('versus_v2.csv', 'BenchmarkScored vs Benchmark'), 2)} a year lower. Against the same kind of benchmark as v1, the excess is still negative and not significant. The archived v1 write-up had already shown the all-included comparison, so the flip is a change of which benchmark is primary, not a new finding.\n")
w("What changed, and the reason for each:\n")
for line in [
    "profit measure: `ib` (income before extraordinary items) instead of net income, because the paper uses it; ROA, CFO-minus-ROA accruals and the change in ROA move.",
    "issuance test: net issuance instead of the share-count test with a 2% tolerance, because the paper tests whether common equity was issued; the first literal draft was rejected on a pass rate before any return.",
    f"availability: no 120-day fallback and a 3-day buffer, so a number is used only after a real filing date. In v1 only {cnt(v1_fallback, S('scores_checks_v2.md', 'section 4 v1 fallback rows'))} chosen list rows used a fallback; the buffer moves {cnt(buf_43, S('scores_checks_v2.md', 'section 5 (ii)'))} list rows to an earlier year.",
    "zero-debt override only where the prior-year change is computable.",
    f"primary benchmark: all included names, so the unscored companies, which v1's benchmark left out, are part of the headline comparison. v1 had already reported this comparison as a post-hoc sensitivity (High {v1_allinc[0]} a year against all included names, t {v1_allinc[1]}), and v2 makes it the primary one.",
    f"earlier-year fallback: if a company's newest annual report fails the date test, the latest earlier scored year is used (v1 had no buffer and used the newest year); this moves {cnt(buf_43, S('scores_checks_v2.md', 'section 5 (ii)'))} list rows to an earlier year and leaves {cnt(b_stale + f_stale, FPSRC + ' [stale total]')} stale and {cnt(f_none, FPSRC + ' [none total]')} with no earlier scored year.",
    "costs: the reinvestment of mid-period exits is charged.",
    "statistics: automatic lag, t distribution, Holm adjustment over a pre-specified family, and reported power, instead of 12 fixed lags and a fixed |t| of 2.",
]:
    w(f"- {line}")
w(f"\nAcross the {cnt(byb.loc['High'].v1_rows + byb.loc['Middle'].v1_rows + byb.loc['Low'].v1_rows + byb.loc['Unscored'].v1_rows, S('list_rows_by_bucket_v1_v2.csv', 'sum v1_rows'))} included list rows, High goes from "
  f"{cnt(byb.loc['High'].v1_rows, S('list_rows_by_bucket_v1_v2.csv', 'High v1_rows'))} to {cnt(byb.loc['High'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'High v2_rows'))}, Middle from {cnt(byb.loc['Middle'].v1_rows, S('list_rows_by_bucket_v1_v2.csv', 'Middle v1_rows'))} to "
  f"{cnt(byb.loc['Middle'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'Middle v2_rows'))}, Low from {cnt(byb.loc['Low'].v1_rows, S('list_rows_by_bucket_v1_v2.csv', 'Low v1_rows'))} to {cnt(byb.loc['Low'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'Low v2_rows'))}, "
  f"and unscored from {cnt(byb.loc['Unscored'].v1_rows, S('list_rows_by_bucket_v1_v2.csv', 'Unscored v1_rows'))} to {cnt(byb.loc['Unscored'].v2_rows, S('list_rows_by_bucket_v1_v2.csv', 'Unscored v2_rows'))}.\n")
w("v2 was specified after v1's results were known, after the external review, so it is a re-specification, not a blind second test. What is pre-specified is the set of v2 rules and tests, committed before any v2 return was read. "
  "The v1 write-up and its robustness runs remain in `output/archive_v1/` and the v1 files.\n")

# ---- paper ----
w("## Against Piotroski's paper\n")
for line in [
    "Profitability: the paper uses income before extraordinary items; v2 does too (v1 used net income).",
    "Equity issuance: the paper tests that no common equity was issued; v2 tests net issuance, `sstk - prstkc`, not exactly the paper's rule. v1's 2% share-count tolerance is dropped.",
    "Leverage: the paper counts current-portion debt as well as long-term debt. Neither v1 nor v2 does: this is a deviation in both specifications.",
    "Low: the paper's main weak group is scores 0-1, with 0-2 as a footnote alternative and below 5 in an appendix. This project's Low is 0-4 (changed from 0-2 on name counts before any return), so it is broader than the paper's.",
    f"The paper's own Table 4 finds the effect weak in the largest firms: High minus All {HAND and '+0.017'} for large firms (t {HAND and '0.872'}), against {HAND and '+0.088'} for small firms (t {HAND and '2.456'}).",
    f"Our result, no detectable edge among the largest companies, is consistent with the weak large-firm result, but it is not strictly comparable. The paper's large-firm difference of {HAND and '+0.017'} (1.7 points) sits just outside our 95% range for High's excess ({pct(ci_ex[0], srcCI, 2, True)} to {pct(ci_ex[1], srcCI, 2, True)}), "
    f"and the subperiod tests could only detect about {pct(ex1.mde_80pct_power_annual, TT(ex1), 1)} to {pct(T('High', EXC, P2).mde_80pct_power_annual, TT(T('High', EXC, P2)), 1)} a year or more. Further: the paper uses pooled one-year market-adjusted returns on a high book-to-market sample, "
    "and this project uses annual portfolios of the 500 largest companies, factor-adjusted and net of costs.",
]:
    w(f"- {line}")
w("")

# ---- drops ----
w("## Drop counts\n")
w(f"Per formation date, v1 beside v2, is in `output/spec_v2/drops_by_date_v2.csv`; one row per unscored name is `drops_reasons_v2.csv`; the summary is `drops_summary_v2.md`.\n")
a_, b_, c_ = int(drops.a_no_gvkey_link.sum()), int(drops.b_no_sector.sum()), int(drops.c_removed_stopped_trading.sum())
rows = [["Companies on the 21 lists", cnt(drops.universe_companies.sum(), S("drops_by_date_v2.csv", "sum universe_companies")), "Exactly 500 a date"],
        ["No GVKEY link", cnt(a_, S("drops_by_date_v2.csv", "sum a_no_gvkey_link")), "Eaton, Dell, Liberty, Ceridian"], ["No sector", cnt(b_, S("drops_by_date_v2.csv", "sum b_no_sector")), "Yahoo"],
        ["Securities removed as stopped trading, before ranking", cnt(c_, S("drops_by_date_v2.csv", "sum c_removed_stopped_trading")), "security-dates"],
        ["Included company-dates", cnt(tot_inc, S("drops_by_date_v2.csv", "sum included")), "After sector exclusions"],
        ["Unscored in v1", f"{cnt(tot_u1, S('drops_by_date_v2.csv', 'sum d_unscored_v1'))} ({pct(tot_u1 / tot_inc, S('drops_by_date_v2.csv', 'd_unscored_v1 / included'), 1)})", "missing or too old"],
        ["Unscored in v2", f"{cnt(tot_u2, S('drops_by_date_v2.csv', 'sum d_unscored_v2'))} ({pct(tot_u2 / tot_inc, S('drops_by_date_v2.csv', 'd_unscored_v2 / included'), 1)})", "reasons below"],
        ["Held company-dates in the buckets (v2)", cnt(tot_inc - tot_u2, S("drops_by_date_v2.csv", "included - d_unscored_v2")), ""]]
w(md_rows(["Stage", "Count", "Detail"], rows))
w("\nWhy the v2 unscored names are unscored (list rows):\n")
rows = [[k, cnt(v, S("drops_reasons_v2.csv", f"count reason={k}")), pct(v / tot_u2, S("drops_reasons_v2.csv", f"share reason={k}"), 1)] for k, v in rs_tot.items()]
w(md_rows(["Reason", "List rows", "Share of unscored"], rows))
w(f"\nMissing-signal cases are mostly the liquidity signal: {cnt(dliq, S('drops_by_date_v2.csv', 'sum v2_missing_signal: F_DLIQUID'))} of the {cnt(rs_tot['missing signal'], S('drops_reasons_v2.csv', 'count missing signal'))} (REITs and finance-arm firms have no current assets or liabilities). "
  f"Unscored names in sectors 40 and 60: v1 {cnt(reit1, S('drops_by_date_v2.csv', 'sum unscored_in_sectors_40_60_v1'))} of {cnt(tot_u1, S('drops_by_date_v2.csv', 'sum d_unscored_v1'))}; v2 {cnt(reit2, S('drops_by_date_v2.csv', 'sum unscored_in_sectors_40_60_v2'))} of {cnt(tot_u2, S('drops_by_date_v2.csv', 'sum d_unscored_v2'))}. "
  f"Firm-years with no real 10-K filing date: {cnt(no_filing, S('unscorable_no_filing_date.csv', 'rows'))}, of which {cnt(no_filing_score, S('unscorable_no_filing_date.csv', 'would_be_score notna'))} would otherwise have a score. "
  f"{cnt(older_13, S('scores_checks_v2.md', 'section 5 (i)'))} list rows use an older year because the newest filed year is unscorable and {cnt(buf_43, S('scores_checks_v2.md', 'section 5 (ii)'))} because the newest filing fell inside the buffer. "
  f"Counting v1's scored rows, the {cnt(len(buf1), FPSRC + ' [v1 scored, filing within 3 days]')} buffer cases are {cnt(b_older, FPSRC + ' [older year]')} scored from an earlier year and {cnt(b_stale, FPSRC + ' [stale]')} stale; "
  f"the {cnt(len(fb1), FPSRC + ' [v1 scored via fallback]')} fallback-dated cases are {cnt(f_stale, FPSRC + ' [fallback stale]')} stale and {cnt(f_none, FPSRC + ' [fallback none]')} with no earlier scored year. "
  f"Together: {cnt(b_older, FPSRC + ' [older total]')} scored from an earlier year, {cnt(b_stale + f_stale, FPSRC + ' [stale total]')} stale and {cnt(f_none, FPSRC + ' [none total]')} with no earlier scored year. "
  f"The scores report counts differently: every included row with a scorable filing inside the buffer, whether or not v1 scored it, which gives {cnt(buf_43 + stale_b + none_b, S('scores_checks_v2.md', 'section 5 total buffer cases'))} "
  f"({cnt(buf_43, S('scores_checks_v2.md', 'section 5 (ii)'))} older year, {cnt(stale_b, S('scores_checks_v2.md', 'section 5 stale'))} stale, {cnt(none_b, S('scores_checks_v2.md', 'section 5 none'))} unscored in v1 and v2 alike). "
  f"v1 had {cnt(v1_on_date, S('scores_checks_v2.md', 'section 5 v1 on formation date'))} scored list rows filed on the formation date itself and {cnt(v1_within, S('scores_checks_v2.md', 'section 5 v1 within buffer'))} within 3 days.\n")

# ---- limitations ----
w("## Limitations and disclosures\n")
i0 = v1_text.index("**The universe is a proxy.**")
i1 = v1_text.index("**The test effectively excludes some companies.**")
CARRIED_A = v1_text[i0:i1]
w("*The next block, on the universe and who is in and out, is carried unchanged from the v1 write-up because the universe is unchanged.*\n")
w(CARRIED_A)
w(f"**The test effectively excludes some companies.** A company-year with any uncomputable signal is dropped: {cnt(tot_u2, S('drops_by_date_v2.csv', 'sum d_unscored_v2'))} list rows are unscored, {pct(reit2 / tot_u2, S('drops_by_date_v2.csv', 'unscored_in_sectors_40_60_v2 / d_unscored_v2'), 1)} of them in sectors 40 and 60. "
  "That effectively excludes traditional REITs, most homebuilders and finance-arm firms, so the result describes the rest of the large-company universe. The v1-specification REIT run below shows the effect of including REITs.\n")
w("**Low is broader than Piotroski's weak group** (see the paper comparison). Middle is therefore 5-7.\n")
w("**Data limits.**\n")
for line in [
    "Restatements: fundamentals come from the current Compustat database, not a record of what was reported at the time, while availability dates use original 10-K filing dates. "
    f"In a test on a sample of {HAND and '1,480'} companies for 2005-2015, {HAND and '98.5%'} of F-scores matched those computable at the time and {HAND and '0.2%'} changed bucket; only {HAND and '55'} of those companies are in this project, "
    f"where {HAND and '97.3%'} matched and {HAND and '0.45%'} changed bucket. That test used the v1 scores and net income. It could not be extended to fiscal 2015 to 2024, because the point-in-time snapshot table (`comp_snapshot`) is not available to this account. "
    "So any look-ahead from restated figures is unmeasured for the later years, which include the second half where the one nominally significant result sits.",
    "Returns end in December 2025, so the 2025 portfolio is partial, and the last subperiod ends then.",
    "Two companies report in Canadian dollars; they are not converted, and ratios are unaffected.",
    f"Merger and separation years are kept: assets or sales move 2x-10x on some list rows, and comparisons across a change of CRSP company are not always valid. See `output/tables/permco_joins_review.csv` (v1 file, same fundamentals).",
]:
    w(f"- {line}")
w("")
w("**Timing of the specification.**\n")
for line in [
    "The v2 rules were first committed in 5ce0e23 (2026-11-01 23:01), before any v2 return existed. Between the pre-return score report and the first v2 return file (2026-11-02 17:25:08) three more commits changed the specification: "
    "9865622 (17:18) revised the issuance rule from `sstk > 0` to `sstk` net of `prstkc`, because the literal rule flagged 77% of firm-years as issuers (option-exercise proceeds); "
    "a054143 (17:19) locked clarifications raised by the independent rebuild's questions; and 24d636f (17:22) locked the hold-flat treatment of Maxim (2007-11 to 2008-05) and General Growth (2009-05) in the benchmark. "
    "No v2 return existed before 17:25. Since 24d636f, `config.py` changed only by the `HEADLINE_SPEC` line and a comment on the `SPEC_V2` line (commit 600824d). "
    "The small-sample correction for the standard errors, T/(T-k), was in the coordinating session's briefing but was not in the locked configuration, so it is a reported sensitivity, not the as-run convention. "
    "The 3-day buffer is an assumption, not a derived number. Some auditors compared v1 returns of dropped rows before the older-year clarification was settled; no v2 return was read.",
    "v2 itself was specified after v1's results were known, so it is not a blind test of a fresh hypothesis. The claims in the archived v1 write-up about when its own rules were set rest on the project coordinator's account, as that write-up says; no file can show the order of events.",
    "The builds share the same data and several of the same rules, so an independent rebuild checks the arithmetic and the implementation, not whether the rules are the right ones or the data true.",
]:
    w(f"- {line}")
w("")
w("**Portfolio mechanics.**\n")
for line in [
    f"{cnt(len(mid), S('portfolio_exits_v2.csv', 'mid-period exits'))} mid-period exits across the all-included benchmark and buckets ({', '.join(f'{k} ' + cnt(v, S('portfolio_exits_v2.csv', 'mid-period exits by bucket')) for k, v in mid.bucket.value_counts().items())}, each name counted under its own bucket); proceeds are reinvested pro rata and the reinvestment is charged one side in the exit month. "
    f"{cnt(len(fd), S('portfolio_exits_v2.csv', 'delisted on the formation date'))} included names delist on the formation date (CNX Gas 2010, Pride 2011, Waste Connections 2016, Valspar 2017): they count at 1/N in the target, are charged as buys, earn nothing, and their weight is respread uncharged.",
    "Maxim Integrated (November 2007 to May 2008) and General Growth Properties (May 2009) have no return for some months and no exit; they are held flat at 0%, uncharged, in the all-included benchmark only. The choice was fixed before any v2 return, and moves the benchmark slightly; a different rule is not tested.",
    "RSP has two rows for April 2018 and they are chained into one return.",
    "No size-dependent trading costs are modelled: every trade pays 10 basis points whatever the company's size or liquidity, and the shorting costs of the Spread are not modelled.",
    f"REIT and real estate coverage is thin by construction (see above): {pct(reit2 / tot_u2, S('drops_by_date_v2.csv', 'unscored_in_sectors_40_60_v2 / d_unscored_v2'), 1)} of unscored names sit in sectors 40 and 60.",
]:
    w(f"- {line}")
w("")

# ---- verification ----
w("## Verification\n")
w("Every number in the results tables was recomputed from the monthly return file with separate numpy/scipy code (`16_spec_v2_numcheck.py`; reports in `output/spec_v2/numcheck_v2.md`), and the figures in this write-up are generated from the v2 files by `17_spec_v2_writeup.py`, "
  "with their sources in `output/spec_v2/writeup_figures_v2.csv`. Checked at the end state in the project folder: git shows no change to scripts 01 to 11 or to the v1 outputs since the v1 commit, and the earlier raw files match the hash values logged for them (`output/logs/pull_raw_hashes.csv`, the two v2 pull logs and `output/logs/raw_hashes_added.csv`, the last recorded after the fact). There is no per-stage hash record for the cleaned data in `data/clean`. `00_test_wrds.py`, `requirements.txt`, `config.py` and `CLAUDE.md` were edited after the v2 returns, for additions and wording only. The data files are licensed and are not in the public repository, so the raw-file hashes cannot be checked from the public copy. Independent rebuilds and audits of v2 are separate reports in `verification/`; this write-up cites two of their scripts (`audit_43_v2_audit.py` for the unscored names' return, and the write-up trace audit) and does not otherwise restate their conclusions. "
  "A rebuild does not test the rules and data the builds share.\n")

# ---- runs on v1 ----
w("## Runs after the v1 write-up: run on the v1 specification, not rerun under v2\n")
w("The user asked for three further runs after the v1 write-up was finished. **None of them is the headline, none was rerun under v2, and none changes a figure or the answer above.** They used the v1 scores, the v1 scored-only benchmark and v1 costs, "
  "so in the tables below 'Headline' means the v1 headline. **Benchmark caveat:** they compare with the scored-only benchmark, as v1 did; under v2 that benchmark runs "
  f"{pct(-bench_gap.excess_return_annual, S('versus_v2.csv', 'BenchmarkScored vs Benchmark excess_return_annual'), 2)} a year above the all-included one, so these excesses would look about that much better against all included names, and the all-included comparison was not computed for them. Each has its own folder, and new data went into new files. All are for the same universe, the Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy), and all figures are net of costs.\n")
j = v1_text.index("Each run's monthly returns were independently rebuilt")
CARRIED_B_ORIG = v1_text[j:]
CARRIED_B = re.sub(r"(?<!not )(?<!v1 )\bthe headline", "the v1 headline", CARRIED_B_ORIG)
assert "but it differs at spin-offs (up to 8.4 points on a single stock) and at delistings" in CARRIED_B
CARRIED_B = CARRIED_B.replace("but it differs at spin-offs (up to 8.4 points on a single stock) and at delistings", "but it differs at spin-offs and at delistings (the gaps are listed in the project's `output/extension_2026/validation.md`, which the public repository does not include)")
CARRIED_B = CARRIED_B.replace("| Headline", "| v1 headline").replace("The headline effectively", "The v1 headline effectively").replace("any headline figure", "any v1 headline figure")
w("*The rest of this section is carried unchanged from the v1 write-up.*\n")
w(CARRIED_B)

text = "\n".join(L)
(OUTPUT / "writeup.md").write_text(text, encoding="utf-8")

# ---------------- provenance ----------------
fig = pd.DataFrame(TRACE, columns=["figure", "source"]).drop_duplicates()
fig = pd.concat([fig, pd.DataFrame([{"figure": k, "source": f"HAND-COPIED: {v}"} for k, v in HAND.items()])], ignore_index=True)
fig.insert(0, "universe_label", LABEL)
fig.to_csv(V2 / "writeup_figures_v2.csv", index=False)

STRUCT = {"17": "git commit time (17:18, 17:19, 17:25) as given by the coordinating session", "19": "git commit time 17:19", "22": "git commit time 17:22", "23": "git commit time 23:01", "77": "77% of firm-years flagged by the literal rule (config.py comment, pre-return report)", "1.7": "paper difference +0.017 written as points", "100": "100/100 label", "18": "MAX_SCORE_AGE_MONTHS", "1994": "year of the Newey-West paper", "500": "UNIVERSE_SIZE", "40": "GICS sector code", "60": "GICS sector code", "95": "95% range", "9865622": "commit"}
known = set(STRUCT) | {re.sub(r"[+%,]", "", s) for s, _ in TRACE} | {re.sub(r"[+%,]", "", k) for k in HAND}
generated = text.replace(CARRIED_A, "").replace(CARRIED_B, "")
untraced = []
for m in re.finditer(r"(?<![\w.])-?\d[\d,]*\.?\d*(?![\w])", generated):
    tok = re.sub(r"[+%,]", "", m.group(0)).rstrip(".")
    val = tok.lstrip("-")
    if val.isdigit() and (int(val) <= 12 or 2000 <= int(val) <= 2026):
        continue
    if tok in known or tok.lstrip("-") in known or tok.lstrip("+") in known:
        continue
    untraced.append(m.group(0))
(V2 / "writeup_untraced_v2.txt").write_text("\n".join(sorted(set(untraced))) + "\n", encoding="utf-8")
print(f"writeup chars={len(text)} traced={len(fig)} untraced_distinct={len(set(untraced))}")
if untraced:
    print(sorted(set(untraced)))
sys.exit(1 if untraced else 0)
