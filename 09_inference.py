"""
Stage 09: inference (output/prereg_main.md, sections A-D). Reads the portfolio returns for both issuance rules and writes output/results/.

Primary rule = the paper's literal issuance test (prereg D); the net rule is a labelled sensitivity.
Primary family (prereg A.2, Holm over three): (a) High minus all-included benchmark, mean; (b) same on Mkt-RF, SMB, HML, MOM (alpha);
(c) High minus Low on the four factors (alpha). The 2015-05 split and the earlier family of six are POST-HOC and exploratory.
HAC lag = floor(4 (T/100)^(2/9)); t(T-k) p-values; lags 4/6/12 side by side.

Usage: python 09_inference.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

import config as cfg

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "results"
OUT.mkdir(parents=True, exist_ok=True)
SRC = {"literal (primary)": ROOT / "output" / "core", "net (sensitivity)": ROOT / "output" / "core" / "net_sensitivity"}
FC = {"Mkt-RF": "mktrf", "SMB": "smb", "HML": "hml", "MOM": "umd"}
F4 = list(FC.values())
LAGS = [None, 6, 12]  # None = formula
ALPHA, POWER = cfg.PIPELINE["alpha_level"], cfg.PIPELINE["power_level"]
POST_HOC_SPLIT = cfg.SUBPERIODS


def lag_formula(T):
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def fit(y, x, lags):
    X = sm.add_constant(x.astype(float)) if x is not None else pd.DataFrame({"const": np.ones(len(y))}, index=y.index)
    f = sm.OLS(y.astype(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    df = int(f.nobs) - X.shape[1]
    t = f.params["const"] / f.bse["const"]
    return f.params["const"] * 12, f.bse["const"] * 12, t, 2 * st.t.sf(abs(t), df), df


def holm(p):
    p = np.asarray(p)
    order = np.argsort(p)
    adj = np.empty(len(p))
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def cagr(r):
    return (1 + r).prod() ** (12 / len(r)) - 1


ff = pd.read_parquet(ROOT / "data" / "raw" / "ff_factors.parquet")
ff.index = pd.PeriodIndex(ff.month, freq="M")

rows, fam_rows = [], []
for rule, d in SRC.items():
    p = pd.read_csv(d / "portfolio_returns.csv")
    p.index = pd.PeriodIndex(p.month, freq="M")
    f = ff.reindex(p.index)
    rf = f.rf.astype(float)
    T = len(p)
    spans = [("full", p.index[0], p.index[-1])] + [(f"{a} to {b} (POST-HOC split)", pd.Period(a, "M"), pd.Period(b, "M")) for a, b in POST_HOC_SPLIT]
    for label, a, b in spans:
        w = p.loc[a:b]
        fw = f.loc[w.index, F4].astype(float)
        series = {
            "(a) High - Benchmark(all included), mean": (w.High - w.Benchmark, None),
            "(b) High - Benchmark(all included), 4-factor alpha": (w.High - w.Benchmark, fw),
            "(c) High - Low, 4-factor alpha": (w.High - w.Low, fw),
            "(d) High - BenchmarkScored, mean (like-for-like)": (w.High - w.BenchmarkScored, None),
            "(e) High excess of rf, 4-factor alpha": (w.High - f.loc[w.index, "rf"].astype(float), fw),
            "(f) Benchmark(all included) excess of rf, 4-factor alpha": (w.Benchmark - f.loc[w.index, "rf"].astype(float), fw),
        }
        for name, (y, x) in series.items():
            for lg in LAGS:
                L = lag_formula(len(w)) if lg is None else lg
                est, se, t, pv, df = fit(y, x, L)
                rows.append({"rule": rule, "period": label, "test": name, "hac_lags": L, "lag_kind": "formula" if lg is None else "sensitivity", "months": len(w),
                             "estimate_annual": est, "se_annual": se, "t": t, "p": pv,
                             "mde_80pct": (st.t.ppf(1 - ALPHA / 2, df) + st.t.ppf(POWER, df)) * se})
res = pd.DataFrame(rows)

# primary family: three tests, full period, formula lag, within each rule
prim = ["(a) High - Benchmark(all included), mean", "(b) High - Benchmark(all included), 4-factor alpha", "(c) High - Low, 4-factor alpha"]
res["in_primary_family"] = res.period.eq("full") & res.test.isin(prim) & res.lag_kind.eq("formula")
res["holm_p_primary_family"] = np.nan
for rule in SRC:
    m = res.in_primary_family & res.rule.eq(rule)
    res.loc[m, "holm_p_primary_family"] = holm(res.loc[m, "p"].values)
res["status"] = np.where(res.in_primary_family, "primary (pre-specified in prereg_main, written after seeing the earlier results)", np.where(res.period.str.contains("POST-HOC"), "POST-HOC exploratory", "secondary"))
res.to_csv(OUT / "tests.csv", index=False)

# trial count: an APPROXIMATE UPPER BOUND, not a count of independent trials. Prior: about 250 t-statistics from the earlier review (taken from CLAUDE.md and the reviewers' figure; not
# re-derivable from the CSVs with one rule). This run: every t in tests.csv (the same test at three lag conventions is not three independent trials).
n_tests = len(res)
RES = ROOT / 'output' / 'results'
n_variants = 0
for _f in ('robustness.csv', 'robustness_exit_rule.csv', 'robustness_extra.csv', 'bm_replication.csv'):
    _p = RES / _f
    if _p.exists():
        n_variants += len(pd.read_csv(_p))
trials = 250 + n_tests + n_variants
crit = st.norm.ppf(1 - 0.05 / 2 / trials)
(OUT / "trial_count.md").write_text(
    f"# Trial count (approximate)\n\nEarlier t-statistics (before this specification): about 250, the reviewers' figure; not re-derivable from the CSVs with a single rule.\n"
    f"This run adds {n_tests} t-statistics in `tests.csv` (tests x rules x periods x three lag conventions; the same test at three lags is not three independent trials), plus {n_variants} robustness and replication rows in `robustness.csv` and its exit-rule copy.\n"
    f"Bonferroni-equivalent two-sided 5% critical |t| at {trials} trials (normal approximation): {crit:.2f}. Read this as approximate: the earlier 250 is not re-derivable.\n"
    f"Only the 3-test primary family has a defensible Holm adjustment. The earlier family of six is post-hoc.\n", encoding="utf-8")

# headline both ways: arithmetic gap, compounded gap, sharpe, both benchmarks
head = []
for rule, d in SRC.items():
    p = pd.read_csv(d / "portfolio_returns.csv")
    p.index = pd.PeriodIndex(p.month, freq="M")
    rf = ff.reindex(p.index).rf.astype(float)
    sh = lambda r: ((r - rf).mean() * 12) / ((r - rf).std() * 12 ** 0.5)
    for base in ["Benchmark", "BenchmarkScored"]:
        head.append({"rule": rule, "benchmark": base, "High_CAGR": cagr(p.High), f"{base}_CAGR": cagr(p[base]), "cagr_gap": cagr(p.High) - cagr(p[base]),
                     "mean_monthly_gap_x12": (p.High - p[base]).mean() * 12, "High_sharpe": sh(p.High), "benchmark_sharpe": sh(p[base]), "months": len(p)})
pd.DataFrame(head).to_csv(OUT / "headline.csv", index=False)

# per-year High count and pass rates, both rules
yrs = []
for rule, d in SRC.items():
    bc = pd.read_csv(d / "bucket_counts.csv", parse_dates=["formation_date"])
    hc = bc[bc.portfolio == "High"].set_index("formation_date").names
    yrs.append(hc.rename(f"High_names_{rule}"))
pass_net = pd.read_csv(ROOT / "output" / "core" / "net_sensitivity" / "eq_offer_pass_by_year.csv").set_index("fyear")
pass_lit = pd.read_csv(ROOT / "output" / "core" / "eq_offer_pass_by_year.csv").set_index("fyear")
py = pd.concat(yrs, axis=1)
py["fyear"] = py.index.year - 1
py["pass_pct_scored_net"] = py.fyear.map(pass_net.eq_offer_pass_pct_scored)
py["pass_pct_scored_literal"] = py.fyear.map(pass_lit.eq_offer_pass_pct_scored)
py.to_csv(OUT / "high_count_and_passrate_by_year.csv")
print(pd.read_csv(OUT / "headline.csv").round(4).to_string())
print(res[res.in_primary_family][["rule", "test", "estimate_annual", "t", "p", "holm_p_primary_family", "mde_80pct"]].round(4).to_string())
print(res[(res.period != "full") & res.test.str.startswith(("(e)", "(f)", "(b)")) & res.lag_kind.eq("formula")][["rule", "period", "test", "estimate_annual", "t", "p"]].round(4).to_string())
print(py.round(2).to_string())
print(open(OUT / "trial_count.md").read())
