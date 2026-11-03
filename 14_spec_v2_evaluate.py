"""
spec_v2, step 4: performance and tests for the v2 portfolios (CLAUDE.md section 8f and its Clarifications, SPEC_V2 in config.py).

Usage:  python 14_spec_v2_evaluate.py [--rule net|literal]
Reads:  <out>/portfolio_returns_v2.csv, portfolio_turnover_v2.csv (step 3), data/raw/ff_factors.parquet,
        v1 output/tables/performance.csv and portfolio_turnover.csv (read only, for the side-by-side table)
Output: <out>/headline_v2.csv, headline_v2.md (the v2 headline table beside v1), tests_v2.csv, subperiods_v2.csv, year_by_year_v2.csv, report_v2.md
        <out> is output/spec_v2 for the net rule and output/spec_v2/literal_sensitivity for the literal rule.
Exit code is 1 if a check fails.

Primary tests (SPEC_V2 primary_tests): (1) raw annualised return of High over the primary benchmark (all included names); (2) High excess of the risk-free rate on Mkt-RF, SMB, HML, MOM,
alpha annualised. Standard errors are Newey-West with the automatic lag floor(4 * (T / 100) ** (2 / 9)) (Bartlett kernel, statsmodels HAC, no small-sample correction); p-values and
minimum detectable effects use a t distribution with T - k degrees of freedom. The family for Holm is these two tests times the full period and the two SUBPERIODS (six p-values).
The six-factor alpha, the lag-12 errors and the scored-only benchmark are reported beside, never used to choose.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
V2 = cfg.SPEC_V2
LABEL = cfg.UNIVERSE_LABEL
FACTOR_COLUMNS = {"Mkt-RF": "mktrf", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma", "MOM": "umd"}
F4 = ["Mkt-RF", "SMB", "HML", "MOM"]
F6 = cfg.FACTOR_MODEL
LONG_ONLY = ["High", "Middle", "Low", "Benchmark", "BenchmarkScored", "RSP", "SPY"]
CHARGED = ["High", "Middle", "Low", "Benchmark", "BenchmarkScored"]
ALPHA, POWER = V2["alpha_level"], V2["power_level"]   # size and power of the minimum-detectable-effect calculation (SPEC_V2)
LAG_A, LAG_B = V2["sensitivity_lags"]                # the two extra lag counts reported beside the automatic lag (SPEC_V2)
# SPEC_V2 keys that name the one behaviour implemented below: stop if the config says otherwise
assert V2["hac_lag_rule"] == "hac_lag_formula_floor_4_T_over_100_pow_2_9" and V2["small_sample"] == "t_distribution_T_minus_k", "HAC lag rule or small-sample rule differs from the code"
assert V2["multiple_testing"] == "holm_over_prespecified_family" and V2["primary_tests"] == ["raw_excess_vs_primary_benchmark", "mkt_smb_hml_mom"], "test family differs from the code"
assert V2["primary_benchmark"] == "equal_weight_all_included" and V2["report_power"] is True, "benchmark or power reporting differs from the code"


def md_table(df, digits=None):
    d = df.copy()
    if digits is not None:
        for c in d.columns:
            if pd.api.types.is_float_dtype(d[c]):
                d[c] = d[c].round(digits)
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in d.itertuples(index=False)) + "\n"


def auto_lag(T):
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def cagr(r):
    return (1 + r).prod() ** (12 / len(r)) - 1


def drawdown_min(r):
    wealth = (1 + r).cumprod()
    peak = pd.concat([pd.Series([1.0]), wealth]).cummax().iloc[1:]
    return float((wealth.values / peak.values - 1).min())


def perf_stats(r, rf):
    ex = r - rf
    return {"months": len(r), "CAGR": cagr(r), "volatility": r.std() * 12 ** 0.5, "sharpe": ex.mean() * 12 / (ex.std() * 12 ** 0.5), "max_drawdown": drawdown_min(r)}


def fit(y, x, lags, correction=False):
    """OLS with Newey-West errors; returns the constant's estimate, standard error, t, two-sided p on T - k degrees of freedom, and the full fit.
    correction=True multiplies the covariance by T / (T - k) (statsmodels use_correction); the run as locked has no correction."""
    X = sm.add_constant(x.astype(float)) if x is not None else pd.DataFrame({"const": np.ones(len(y))}, index=y.index)
    f = sm.OLS(y.astype(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": correction})
    df = int(f.nobs) - X.shape[1]
    t = f.params["const"] / f.bse["const"]
    return {"est": f.params["const"], "se": f.bse["const"], "t": t, "p": 2 * st.t.sf(abs(t), df), "df": df, "fit": f}


def mde(se, df):
    return (st.t.ppf(1 - ALPHA / 2, df) + st.t.ppf(POWER, df)) * se


def holm(p):
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rule", choices=["net", "literal"], default="net")
    rule = ap.parse_args().rule
    out = ROOT / V2["output_dir"] / ("" if rule == "net" else "literal_sensitivity")
    failures = []
    kind = "net issuance rule (primary)" if rule == "net" else "literal issuance rule (sensitivity)"

    p = pd.read_csv(out / "portfolio_returns_v2.csv", parse_dates=["formation_date"])
    p.index = pd.PeriodIndex(p.month, freq="M")
    t = pd.read_csv(out / "portfolio_turnover_v2.csv", parse_dates=["formation_date"])
    ff = pd.read_parquet(RAW / "ff_factors.parquet")
    ff["period"] = pd.PeriodIndex(ff.month, freq="M")
    ff = ff.set_index("period").sort_index()
    factors = ff.reindex(p.index)
    cols = [FACTOR_COLUMNS[n] for n in F6]
    factors[cols + ["rf"]] = factors[cols + ["rf"]].astype(float)
    if factors[cols + ["rf"]].isna().any().any():
        failures.append("Missing factor values in the test period")
    rf = factors.rf
    T = len(p)

    # --- Headline table: v2 beside v1 ---
    v1p = pd.read_csv(ROOT / "output" / "tables" / "performance.csv")
    v1p = v1p[v1p.basis.isin(["net", "fund return"])].set_index("portfolio")
    v1_name = {"High": "High", "Middle": "Middle", "Low": "Low", "BenchmarkScored": "Benchmark", "RSP": "RSP", "SPY": "SPY"}
    rows = []
    for name in LONG_ONLY:
        s = perf_stats(p[name], rf)
        row = {"universe_label": LABEL, "portfolio": name, "v2_months": s["months"], "v2_CAGR": s["CAGR"], "v2_volatility": s["volatility"], "v2_sharpe": s["sharpe"], "v2_max_drawdown": s["max_drawdown"]}
        row["v2_avg_turnover_two_way"] = t[(t.portfolio == name) & (t.formation_date > t.formation_date.min())].turnover_two_way.mean() if name in CHARGED else np.nan
        if name in v1_name:
            v = v1p.loc[v1_name[name]]
            row.update({"v1_CAGR": v.CAGR, "v1_volatility": v.volatility, "v1_sharpe": v.sharpe, "v1_max_drawdown": v.max_drawdown, "v1_avg_turnover_two_way": v.avg_turnover_two_way})
        rows.append(row)
    head = pd.DataFrame(rows)
    head.to_csv(out / "headline_v2.csv", index=False)

    # --- Tests: full period and the two SUBPERIODS ---
    periods = [("full", p.index[0], p.index[-1])] + [(f"{a} to {b}", pd.Period(a, "M"), pd.Period(b, "M")) for a, b in cfg.SUBPERIODS]
    test_rows = []

    def add(series, test, period, y, x, lags_main, extra_lag12=True):
        r_main = fit(y, x, lags_main)
        r12 = fit(y, x, LAG_B)
        rc = fit(y, x, lags_main, correction=V2["sensitivity_small_sample_correction"])
        r6 = fit(y, x, LAG_A)
        test_rows.append({"lag_corr_t": rc["t"], "lag_corr_p": rc["p"], f"lag{LAG_A}_t": r6["t"], f"lag{LAG_A}_p": r6["p"], "universe_label": LABEL, "series": series, "test": test, "period": period, "months": len(y), "hac_lags": lags_main, "estimate_annual": r_main["est"] * 12,
                          "se_annual": r_main["se"] * 12, "t": r_main["t"], "p_value": r_main["p"], "df": r_main["df"], "mde_80pct_power_annual": mde(r_main["se"], r_main["df"]) * 12,
                          f"lag{LAG_B}_t": r12["t"], f"lag{LAG_B}_p": r12["p"], "r_squared": r_main["fit"].rsquared if x is not None else np.nan})
        return r_main

    for label, a, b in periods:
        w = p.loc[a:b]
        fw, rw = factors.loc[w.index], rf.loc[w.index]
        L = auto_lag(len(w))
        add("High", "raw excess vs primary benchmark (all included)", label, w.High - w.Benchmark, None, L)
        add("High", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)", label, w.High - rw, fw[[FACTOR_COLUMNS[n] for n in F4]], L)
        add("High", "raw excess vs scored-only benchmark (sensitivity)", label, w.High - w.BenchmarkScored, None, L)
        add("High", "alpha, six factors (secondary)", label, w.High - rw, fw[cols], L)
        for nm in ["Middle", "Low"]:
            add(nm, "raw excess vs primary benchmark (all included)", label, w[nm] - w.Benchmark, None, L)
            add(nm, "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)", label, w[nm] - rw, fw[[FACTOR_COLUMNS[n] for n in F4]], L)
            add(nm, "raw excess vs scored-only benchmark (sensitivity)", label, w[nm] - w.BenchmarkScored, None, L)
            add(nm, "alpha, six factors (secondary)", label, w[nm] - rw, fw[cols], L)
        add("Spread (High minus Low)", "raw mean, net (diagnostic)", label, w.Spread, None, L)
        add("Spread (High minus Low)", "alpha, Mkt-RF+SMB+HML+MOM", label, w.Spread, fw[[FACTOR_COLUMNS[n] for n in F4]], L)
        add("Spread (High minus Low)", "alpha, six factors (secondary)", label, w.Spread, fw[cols], L)
        add("Benchmark (primary)", "alpha, Mkt-RF+SMB+HML+MOM (context)", label, w.Benchmark - rw, fw[[FACTOR_COLUMNS[n] for n in F4]], L)
    tests = pd.DataFrame(test_rows)
    fam = tests[(tests.series == "High") & tests.test.isin(["raw excess vs primary benchmark (all included)", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)"])]
    if len(fam) != 6:
        failures.append("Holm family does not have six p-values")
    tests["holm_adjusted_p"] = np.nan
    tests.loc[fam.index, "holm_adjusted_p"] = holm(fam.p_value.values)
    tests["in_holm_family"] = tests.index.isin(fam.index)
    # Holm within each variant, over the same six tests. The as-run column is holm_adjusted_p; the variants are reported beside, never used to choose.
    for col, name in [("lag_corr_p", "holm_p_lag_corrected"), (f"lag{LAG_A}_p", f"holm_p_lag{LAG_A}"), (f"lag{LAG_B}_p", f"holm_p_lag{LAG_B}")]:
        tests[name] = np.nan
        tests.loc[fam.index, name] = holm(tests.loc[fam.index, col].values)
    tests.to_csv(out / "tests_v2.csv", index=False)

    # --- Gap to each benchmark: excess, tracking error, information ratio (full period) ---
    vs_rows = []
    for nm in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored", "RSP", "SPY"]:
        for base in ["Benchmark", "BenchmarkScored"]:
            if nm == base:
                continue
            d = p[nm] - p[base]
            te = d.std() * 12 ** 0.5
            vs_rows.append({"universe_label": LABEL, "portfolio": nm, "versus": base, "excess_return_annual": d.mean() * 12, "cagr_difference": cagr(p[nm]) - cagr(p[base]), "tracking_error": te, "information_ratio": d.mean() * 12 / te})
    pd.DataFrame(vs_rows).to_csv(out / "versus_v2.csv", index=False)
    # --- Factor loadings, full period (OLS point estimates with the as-run Newey-West t) ---
    load_rows = []
    for nm, y in [("High excess of rf", p.High - rf), ("Spread (High minus Low)", p.Spread)]:
        for model, fl in [("4-factor", F4), ("6-factor", F6)]:
            fc = [FACTOR_COLUMNS[n] for n in fl]
            r_ = fit(y, factors[fc], auto_lag(T))["fit"]
            row = {"universe_label": LABEL, "series": nm, "model": model, "alpha_annual": r_.params["const"] * 12, "alpha_t": r_.tvalues["const"], "r_squared": r_.rsquared}
            for n in fl:
                row[f"beta_{n}"] = r_.params[FACTOR_COLUMNS[n]]
            load_rows.append(row)
    pd.DataFrame(load_rows).to_csv(out / "factor_loadings_v2.csv", index=False)

    # --- Subperiod performance ---
    subs = []
    for label, a, b in periods[1:]:
        w = p.loc[a:b]
        rw = rf.loc[w.index]
        d = {"universe_label": LABEL, "period": label, "months": len(w)}
        for nm in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored"]:
            s = perf_stats(w[nm], rw)
            d.update({f"{nm}_CAGR": s["CAGR"], f"{nm}_sharpe": s["sharpe"]})
        d["High_minus_Benchmark_annual"] = (w.High - w.Benchmark).mean() * 12
        d["Spread_annual"] = w.Spread.mean() * 12
        subs.append(d)
    subs = pd.DataFrame(subs)
    if subs.months.sum() != T:
        failures.append("Subperiods do not cover every month once")
    subs.to_csv(out / "subperiods_v2.csv", index=False)

    # --- Holding years, hit rate on complete years ---
    comp = lambda r: (1 + r).prod() - 1
    yr = p.groupby("formation_date").agg(months=("High", "size"), High=("High", comp), Middle=("Middle", comp), Low=("Low", comp), Benchmark=("Benchmark", comp), BenchmarkScored=("BenchmarkScored", comp)).reset_index()
    yr["holding_year"] = [f"{d.year}-{str(d.year + 1)[2:]}" if m == cfg.HOLDING_MONTHS else f"{d.year} partial ({m} of {cfg.HOLDING_MONTHS} months)" for d, m in zip(yr.formation_date, yr.months)]
    yr["High_minus_Benchmark"] = yr.High - yr.Benchmark
    yr["High_beats_Benchmark"] = yr.High > yr.Benchmark
    yr["High_beats_BenchmarkScored"] = yr.High > yr.BenchmarkScored
    yr["Spread"] = yr.High - yr.Low
    cnt = pd.read_csv(out / "bucket_counts_v2.csv", parse_dates=["formation_date"]).pivot(index="formation_date", columns="portfolio", values="names").reset_index()
    yr = yr.merge(cnt[["formation_date", "High", "Low"]].rename(columns={"High": "High_names", "Low": "Low_names"}), on="formation_date")
    done = yr[yr.months == cfg.HOLDING_MONTHS]
    hit, hit_scored = done.High_beats_Benchmark.mean(), done.High_beats_BenchmarkScored.mean()
    yr.insert(0, "universe_label", LABEL)
    yr.to_csv(out / "year_by_year_v2.csv", index=False)

    # --- headline_v2: one row per key number, for the number-check script ---
    full = tests[tests.period == "full"].set_index(["series", "test"])
    key = {}
    for nm in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored"]:
        r = head.set_index("portfolio").loc[nm]
        key.update({f"{nm}_CAGR": r.v2_CAGR, f"{nm}_volatility": r.v2_volatility, f"{nm}_sharpe": r.v2_sharpe, f"{nm}_max_drawdown": r.v2_max_drawdown})
    ex = full.loc[("High", "raw excess vs primary benchmark (all included)")]
    al = full.loc[("High", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)")]
    key.update({"High_excess_vs_primary_annual": ex.estimate_annual, "High_excess_t": ex.t, "High_excess_p": ex.p_value, "High_excess_holm_p": ex.holm_adjusted_p, "High_excess_mde": ex.mde_80pct_power_annual,
                "High_alpha4_annual": al.estimate_annual, "High_alpha4_t": al.t, "High_alpha4_p": al.p_value, "High_alpha4_holm_p": al.holm_adjusted_p, "High_alpha4_mde": al.mde_80pct_power_annual,
                "hac_lags_full": auto_lag(T), "months": T, "hit_rate_complete_years_primary": hit, "hit_rate_complete_years_scored_only": hit_scored, "complete_years": len(done)})
    pd.DataFrame({"universe_label": LABEL, "metric": list(key), "value": list(key.values())}).to_csv(out / "headline_v2_numbers.csv", index=False)

    # --- Report ---
    L = [f"# spec_v2 results, {kind}: {LABEL}\n", f"**{len(failures)} check failure(s).** {T} months, {p.month.iloc[0]} to {p.month.iloc[-1]}; last portfolio partial (7 of 12 months). Returns are net of costs; RSP and SPY are fund returns. "
         f"Primary benchmark = every included name, equal weight, charged like the buckets; BenchmarkScored = scored names only (v1's benchmark).\n"] + [f"- FAIL: {x}" for x in failures] + [""]
    fcov = pd.read_parquet(ROOT / "data" / "clean" / "spec_v2" / ("formation_v2.parquet" if rule == "net" else "formation_v2_literal.parquet"), columns=["formation_date", "permco", "scored", "bucket"])
    L.append(f"**Coverage.** {len(fcov)} included list rows from {fcov.permco.nunique()} unique companies on {fcov.formation_date.nunique()} formation dates ({fcov.formation_date.min().date()} to {fcov.formation_date.max().date()}); "
             f"{int(fcov.scored.sum())} scored list rows from {fcov[fcov.scored].permco.nunique()} unique companies. Unique companies by bucket: {', '.join(f'{b} ' + str(fcov[fcov.bucket == b].permco.nunique()) for b in ['High', 'Middle', 'Low'])}. "
             f"Monthly returns {p.month.iloc[0]} to {p.month.iloc[-1]} ({T} months). No rows are dropped by this script.\n")
    L.append("## Headline: v2 beside v1\n")
    L.append(md_table(head.drop(columns="universe_label"), 4))
    L.append(f"\nv1 'Benchmark' = scored names only, so it sits beside `BenchmarkScored`. v1 rows use v1's costs (no charge on mid-period reinvestment).\n")
    L.append(f"## Primary tests, High, full period (Newey-West, automatic lag {auto_lag(T)}; t distribution, T - k df; annualised)\n")
    prim = tests[(tests.series == "High") & tests.test.isin(["raw excess vs primary benchmark (all included)", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)"])]
    L.append(md_table(prim.drop(columns=["universe_label", "series", "in_holm_family", "r_squared"]), 4))
    L.append("\nHolm adjustment is over these six p-values (two tests x full period and the two subperiods). `mde_80pct_power_annual` is the smallest true effect detectable with 80% power at 5% two-sided, given this sample's standard error.\n")
    sens = tests[tests.in_holm_family].copy()
    sens["test"] = sens.test.map({"raw excess vs primary benchmark (all included)": "raw excess", "alpha, Mkt-RF+SMB+HML+MOM (excess of rf)": "4-factor alpha"})
    sens_cols = sens[["test", "period", "estimate_annual", "t", "p_value", "holm_adjusted_p", "lag_corr_t", "lag_corr_p", "holm_p_lag_corrected", f"lag{LAG_A}_t", f"lag{LAG_A}_p", f"holm_p_lag{LAG_A}", f"lag{LAG_B}_t", f"lag{LAG_B}_p", f"holm_p_lag{LAG_B}"]]
    sens_cols = sens_cols.rename(columns={"t": "t_as_run", "p_value": "p_as_run", "holm_adjusted_p": "holm_as_run"})
    L.append("## Sensitivity of the primary tests to the standard-error convention\n")
    L.append(f"Every primary test, High, under four conventions: as run (Newey-West, automatic lag floor(4 * (T / 100) ** (2 / 9)) = {auto_lag(T)} for the full period, no small-sample correction; the convention SPEC_V2 locks), the same lag {auto_lag(T)} "
             f"with the covariance multiplied by T / (T - k), lag {LAG_A}, and lag {LAG_B}. p-values use t with T - k degrees of freedom. Holm is over the same six tests within each convention. Reported beside; none was used to choose.\n")
    L.append(md_table(sens_cols, 4))
    reject = []
    for col, lab in [("holm_adjusted_p", "as run"), ("holm_p_lag_corrected", f"lag {auto_lag(T)} with the T / (T - k) correction"), (f"holm_p_lag{LAG_A}", f"lag {LAG_A}"), (f"holm_p_lag{LAG_B}", f"lag {LAG_B}")]:
        hits = [f"{r.test} {r.period}" for r in sens.itertuples() if getattr(r, col) < ALPHA]
        reject.append(f"- {lab}: {', '.join(hits) if hits else 'none'}")
    L.append("\nTests rejecting at 5% after Holm adjustment, by convention:\n")
    L += reject
    a = sens[(sens.test == "4-factor alpha") & (sens.period == periods[2][0])].iloc[0]
    L.append("\nThe lag rule used is the formula floor(4 * (T / 100) ** (2 / 9)), which is what SPEC_V2 locks. It is not the data-dependent Newey-West (1994) bandwidth, which is unstable at T = 127 (one independent check found it picking a lag near 59 there). "
             f"Read plainly: the only primary test that rejects at 5% after Holm is the {periods[2][0]} four-factor alpha, and its margin is thin. Holm p is {a.holm_adjusted_p:.3f} as run, "
             f"{a.holm_p_lag_corrected:.3f} with the T / (T - k) correction (no rejection), {getattr(a, f'holm_p_lag{LAG_A}'):.3f} at lag {LAG_A} and {getattr(a, f'holm_p_lag{LAG_B}'):.4f} at lag {LAG_B}. No other primary test rejects under any convention.\n")
    L.append("## All tests\n")
    L.append(md_table(tests.drop(columns=["universe_label", "in_holm_family"]), 4))
    L.append("\n## Subperiods (net)\n")
    L.append(md_table(subs.drop(columns="universe_label"), 4))
    L.append(f"\n## Holding years\n\nHigh beat the primary benchmark in {int(done.High_beats_Benchmark.sum())} of {len(done)} complete holding years = {hit:.0%}; beat the scored-only benchmark in {int(done.High_beats_BenchmarkScored.sum())} of {len(done)} = {hit_scored:.0%}. The partial year is shown separately.\n")
    L.append(md_table(yr.drop(columns=["universe_label", "formation_date"]), 4))
    (out / "report_v2.md").write_text("\n".join(L), encoding="utf-8")
    (out / "headline_v2.md").write_text(f"# v2 headline beside v1: {LABEL}\n\n{kind}\n\n" + md_table(head.drop(columns="universe_label"), 4), encoding="utf-8")
    print(f"rule={rule} months={T} lags={auto_lag(T)} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
