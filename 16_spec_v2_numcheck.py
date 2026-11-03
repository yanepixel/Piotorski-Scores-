"""
spec_v2, step 6: number check. Recomputes the headline numbers and the High primary tests from the monthly return file with plain numpy / scipy (no statsmodels), and compares
them with headline_v2_numbers.csv, tests_v2.csv and the numbers printed in report_v2.md.

Usage:  python 16_spec_v2_numcheck.py [--rule net|literal]
Output: <out>/numcheck_v2.md. Exit code is 1 if any number differs by more than the tolerance (1e-8 relative on levels, 1e-6 on t statistics and p-values).
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
F4 = ["mktrf", "smb", "hml", "umd"]
TOL_LEVEL, TOL_T = 1e-8, 1e-6
LAG_A, LAG_B = cfg.SPEC_V2["sensitivity_lags"]   # extra lag counts reported beside the automatic lag


def nw_ols(y, X, lags):
    """OLS coefficients and Newey-West (Bartlett) covariance: (X'X)^-1 S (X'X)^-1, S = sum_{l=-L..L} w_l Gamma_l, w_l = 1 - |l| / (L + 1). No small-sample correction."""
    y = np.asarray(y, float)
    X = np.asarray(X, float)
    n = len(y)
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    Z = X * e[:, None]
    S = Z.T @ Z
    for l in range(1, lags + 1):
        G = Z[l:].T @ Z[:-l]
        S += (1 - l / (lags + 1)) * (G + G.T)
    V = XtXi @ S @ XtXi
    return b, np.sqrt(np.diag(V)), n - X.shape[1]


def dd_n(n, X):
    """T - k for the small-sample correction factor T / (T - k)."""
    return n - X.shape[1]


def auto_lag(T):
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def holm(p):
    p = np.asarray(p)
    order = np.argsort(p)
    adj, run = np.empty(len(p)), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(p) - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rule", choices=["net", "literal"], default="net")
    rule = ap.parse_args().rule
    out = ROOT / cfg.SPEC_V2["output_dir"] / ("" if rule == "net" else "literal_sensitivity")
    p = pd.read_csv(out / "portfolio_returns_v2.csv")
    ff = pd.read_parquet(RAW / "ff_factors.parquet")
    ff["m"] = pd.PeriodIndex(ff.month, freq="M").astype(str)
    ff = ff.set_index("m").reindex(p.month)
    rf = ff.rf.astype(float).values
    T = len(p)
    shown = pd.read_csv(out / "headline_v2_numbers.csv").set_index("metric").value
    tests = pd.read_csv(out / "tests_v2.csv")
    checks = []

    def cmp(name, mine, theirs, tol):
        ok = bool(np.isclose(mine, theirs, rtol=tol, atol=tol))
        checks.append((name, mine, theirs, ok))

    for nm in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored"]:
        r = p[nm].values
        cmp(f"{nm}_CAGR", np.prod(1 + r) ** (12 / T) - 1, shown[f"{nm}_CAGR"], TOL_LEVEL)
        cmp(f"{nm}_volatility", np.std(r, ddof=1) * np.sqrt(12), shown[f"{nm}_volatility"], TOL_LEVEL)
        ex = r - rf
        cmp(f"{nm}_sharpe", ex.mean() * 12 / (np.std(ex, ddof=1) * np.sqrt(12)), shown[f"{nm}_sharpe"], TOL_LEVEL)
        w = np.cumprod(1 + r)
        peak = np.maximum.accumulate(np.concatenate([[1.0], w]))[1:]
        cmp(f"{nm}_max_drawdown", (w / peak - 1).min(), shown[f"{nm}_max_drawdown"], TOL_LEVEL)

    periods = [("full", 0, T)]
    for a, b in cfg.SUBPERIODS:
        i0 = int(np.where(p.month.values == a)[0][0])
        i1 = int(np.where(p.month.values == b)[0][0]) + 1
        periods.append((f"{a} to {b}", i0, i1))
    fam_p = []
    for label, i0, i1 in periods:
        n = i1 - i0
        L = auto_lag(n)
        y1 = (p.High - p.Benchmark).values[i0:i1]
        b1, se1, df1 = nw_ols(y1, np.ones((n, 1)), L)
        t1 = b1[0] / se1[0]
        p1 = 2 * st.t.sf(abs(t1), df1)
        y2 = (p.High.values - rf)[i0:i1]
        X2 = np.column_stack([np.ones(n), ff[F4].astype(float).values[i0:i1]])
        b2, se2, df2 = nw_ols(y2, X2, L)
        t2 = b2[0] / se2[0]
        p2 = 2 * st.t.sf(abs(t2), df2)
        fam_p += [p1, p2]
        mde1 = (st.t.ppf(1 - cfg.SPEC_V2['alpha_level'] / 2, df1) + st.t.ppf(cfg.SPEC_V2['power_level'], df1)) * se1[0] * 12
        mde2 = (st.t.ppf(1 - cfg.SPEC_V2['alpha_level'] / 2, df2) + st.t.ppf(cfg.SPEC_V2['power_level'], df2)) * se2[0] * 12
        for test, est, se, t, pv, mde_v in [("raw excess vs primary benchmark (all included)", b1[0] * 12, se1[0] * 12, t1, p1, mde1), ("alpha, Mkt-RF+SMB+HML+MOM (excess of rf)", b2[0] * 12, se2[0] * 12, t2, p2, mde2)]:
            row = tests[(tests.series == "High") & (tests.test == test) & (tests.period == label)].iloc[0]
            cmp(f"{label} | {test} | estimate", est, row.estimate_annual, TOL_LEVEL)
            cmp(f"{label} | {test} | se", se, row.se_annual, TOL_LEVEL)
            cmp(f"{label} | {test} | t", t, row.t, TOL_T)
            cmp(f"{label} | {test} | p", pv, row.p_value, TOL_T)
            cmp(f"{label} | {test} | mde", mde_v, row.mde_80pct_power_annual, TOL_LEVEL)
        for lg, tc, pc in [(LAG_A, f"lag{LAG_A}_t", f"lag{LAG_A}_p")]:
            for test, y, X in [("raw excess vs primary benchmark (all included)", y1, np.ones((n, 1))), ("alpha, Mkt-RF+SMB+HML+MOM (excess of rf)", y2, X2)]:
                bb, ss, dd = nw_ols(y, X, lg)
                row = tests[(tests.series == "High") & (tests.test == test) & (tests.period == label)].iloc[0]
                cmp(f"{label} | {test} | {tc}", bb[0] / ss[0], row[tc], TOL_T)
        for test, y, X in [("raw excess vs primary benchmark (all included)", y1, np.ones((n, 1))), ("alpha, Mkt-RF+SMB+HML+MOM (excess of rf)", y2, X2)]:
            bb, ss, dd = nw_ols(y, X, L)
            ss = ss * np.sqrt(n / dd_n(n, X))
            row = tests[(tests.series == "High") & (tests.test == test) & (tests.period == label)].iloc[0]
            cmp(f"{label} | {test} | lag_corr_t", bb[0] / ss[0], row.lag_corr_t, TOL_T)
        # lag-12 sensitivity
        b12, se12, _ = nw_ols(y1, np.ones((n, 1)), LAG_B)
        row = tests[(tests.series == "High") & (tests.test == "raw excess vs primary benchmark (all included)") & (tests.period == label)].iloc[0]
        cmp(f"{label} | raw excess | lag{LAG_B} t", b12[0] / se12[0], row[f"lag{LAG_B}_t"], TOL_T)
    adj = holm(fam_p)
    fam = tests[tests.in_holm_family]
    order = [(per[0], tst) for per in periods for tst in ["raw excess vs primary benchmark (all included)", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)"]]
    for k, (per, tst) in enumerate(order):
        row = fam[(fam.period == per) & (fam.test == tst)].iloc[0]
        cmp(f"Holm | {per} | {tst}", adj[k], row.holm_adjusted_p, TOL_T)
    cmp("hac_lags_full", auto_lag(T), shown["hac_lags_full"], 0)

    # Hit rate on complete years, recomputed from monthly returns by cohort
    yrs = p.groupby("formation_date")
    complete = [g for _, g in yrs if len(g) == cfg.HOLDING_MONTHS]
    hits = np.mean([np.prod(1 + g.High) > np.prod(1 + g.Benchmark) for g in complete])
    cmp("hit_rate_complete_years_primary", hits, shown["hit_rate_complete_years_primary"], TOL_LEVEL)
    cmp("complete_years", len(complete), shown["complete_years"], 0)

    # Numbers printed in report_v2.md: every cell of the headline table must equal the CSV rounded to 4 places
    report = (out / "report_v2.md").read_text(encoding="utf-8")
    head = pd.read_csv(out / "headline_v2.csv")
    printed_ok = True
    for r in head.itertuples():
        for col in ["v2_CAGR", "v2_volatility", "v2_sharpe", "v2_max_drawdown"]:
            if f"| {round(getattr(r, col), 4)} |" not in report and f" {round(getattr(r, col), 4)} " not in report:
                printed_ok = False
                checks.append((f"report prints {r.portfolio} {col}", getattr(r, col), np.nan, False))
    checks.append(("report prints every v2 headline value to 4 places", 1.0, 1.0, printed_ok))
    if "Top 500 US common stocks by market cap" not in report:
        checks.append(("report carries the universe label", 0, 1, False))

    bad = [c for c in checks if not c[3]]
    L = [f"# spec_v2 number check ({rule}): {cfg.UNIVERSE_LABEL}\n", f"{len(checks)} numbers recomputed with numpy/scipy only; **{len(bad)} differ**.\n", "| check | recomputed | in the tables | ok |", "|---|---|---|---|"]
    L += [f"| {n} | {m:.8g} | {t:.8g} | {'yes' if ok else 'NO'} |" for n, m, t, ok in checks]
    (out / "numcheck_v2.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"rule={rule} checked={len(checks)} differ={len(bad)}")
    for n, m, t, _ in bad:
        print("DIFF:", n, m, t)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
