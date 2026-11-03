"""
v3 rerun of the labelled extension_2026 (config.EXTENSION_2026, V2_RERUNS; CLAUDE.md 8d and 8g). Descriptive only; not part of any test family.

Inputs are the v3 ones: literal issuance rule (primary), ib, v2 mechanics (equal weight, buy and hold, pro rata redistribution, one-sided charge on reinvestment,
approved hold-flat months), availability = filing date + 3 days with no fallback, all-included benchmark (scored-only beside). The 2025 list is held January-May 2026
with comp.secm trt1m under the four EXTENSION_2026 conditions (return field, two named exits then DELISTING_RULE, two spin-off months used as given, any other null or
missing row stops). Anything the locked rules do not cover STOPS the run (STOPPED file, exit 1); nothing is decided here.

Reads:  data/clean/*.parquet, data/raw/{crsp_msf_v2,crsp_benchmarks,comp_secm_extension,comp_funda_ib,comp_funda_prstkc,ff_factors}.parquet,
        output/spec_v2/literal_sensitivity/portfolio_returns_v2.csv (reproduction check only), output/extension_2026/{returns.csv,security_map.csv,sensitivities.csv} (v1, read only)
Writes: output/spec_v3/extension_2026_v3.csv (aggregates only), data/external/extension_2026_v3_names.csv (company-level)
Also importable: 29_v3_reit_liquidity.py reuses the engine below.
Usage:  python -W ignore 28_v3_extension_2026.py
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
OUT = ROOT / "output" / "spec_v3"
EXT = ROOT / "data" / "external"
BPS = cfg.TRANSACTION_COST_BPS / 10000
MAIN = ["High", "Middle", "Low"]
PORTS = MAIN + ["Benchmark", "BenchmarkScored"]
FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2_reruns"].items() for m in ms}
FC = {"Mkt-RF": "mktrf", "SMB": "smb", "HML": "hml", "MOM": "umd"}   # prereg_v3 A.2 four-factor model
EXIT_GAP_BP = 494   # constant carried from 10_extension_2026.py (v1 sensitivity label: 95th percentile of absolute exit gaps in the v1 validation); not re-derived, not chosen from
SENS_EXTRA_LAGS = [12]   # fixed lag beside the automatic one (CLAUDE.md 8g clarification 4)


class Stop(Exception):
    """A case no locked rule covers."""


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- v3 inputs
def v3_scores(rule="literal"):
    """v3 F-scores by company-year under the 12b mechanics (ib, chosen issuance rule, no fallback availability)."""
    s12 = load("12b_spec_v2_scores.py", "s12")
    s12.RULE = rule
    fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
    ib = pd.read_parquet(RAW / "comp_funda_ib.parquet")
    pk = pd.read_parquet(RAW / "comp_funda_prstkc.parquet")
    fund = fund.merge(ib[["gvkey", "datadate", "fyear", "ib"]].assign(fyear=lambda x: x.fyear.astype(int), ib=lambda x: x.ib.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
    fund = fund.merge(pk[["gvkey", "datadate", "fyear", "prstkc"]].assign(fyear=lambda x: x.fyear.astype(int), prstkc=lambda x: x.prstkc.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
    return s12, fund, s12.compute_scores_v2(fund)


# ---------------------------------------------------------------- returns and portfolio engine (13_spec_v2_portfolios.py mechanics)
def load_crsp():
    r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretflg", "mthdelflg", "mthprcdt", "issuernm", "cusip", "ticker", "issuertype"])
    r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    r["month"] = r.mthcaldt.dt.to_period("M")
    r["mthret"] = r.mthret.astype(float)
    if r.duplicated(["permno", "month"]).any():
        raise Stop("duplicate permno-month rows in CRSP returns")
    by_permno = {p: g.set_index("month") for p, g in r.groupby("permno")}
    ret_by_month = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}
    return r, by_permno, ret_by_month


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def window_checks(inc, by_permno):
    """13's checks for every included name, with the approved hold-flat months allowed in any bucket (V2_RERUNS clarification 5). Returns last month with a return per (date, permno)."""
    last_month_of, nulls, gaps, no_row, flat_used = {}, [], [], [], []
    for x in inc.itertuples():
        months = holding_months(x.formation_date)
        h = by_permno.get(x.permno)
        if h is None or x.formation_date.to_period("M") not in h.index:
            no_row.append((x.formation_date.date(), x.permno))
            continue
        w = h[h.index.isin(months)].sort_index()
        for mth in w.index[w.mthret.isna()]:
            (flat_used if (x.permno, mth) in FLAT else nulls).append((x.formation_date.date(), x.permno, str(mth)))
        ok = [m for m in w.index if pd.notna(w.mthret[m]) or (x.permno, m) in FLAT]
        last = max(ok) if ok else None
        last_month_of[(x.formation_date, x.permno)] = last
        if last is not None:
            gaps += [(x.formation_date.date(), x.permno, str(m)) for m in months if m < last and m not in w.index]
    if nulls or gaps or no_row:
        raise Stop(f"held-window problems with no approved rule: {len(nulls)} null returns {nulls[:5]}, {len(gaps)} gaps {gaps[:5]}, {len(no_row)} names without a formation-date row {no_row[:5]}")
    return last_month_of, flat_used


def run_portfolio(members, months, ret_by_month, last_month):
    w = pd.Series(1.0 / len(members), index=list(members))
    gross, reinv = {}, {}
    for m in months:
        rets = ret_by_month.get(m, pd.Series(dtype=float))
        flat = [p for p in w.index if (p, m) in FLAT]
        if flat:
            rets = rets.copy()
            for p in flat:
                rets.loc[p] = 0.0
        active = w.index.intersection(rets.index)
        w = w.loc[active]
        if len(active) == 0:
            raise Stop(f"no holdings left in {m}")
        w = w / w.sum()
        r = rets.loc[active]
        g = float((w * r).sum())
        gross[m] = g
        w = w * (1 + r) / (1 + g)
        leaving = [p for p in w.index if last_month.get(p) == m and m < months[-1]]
        reinv[m] = float(w.loc[leaving].sum()) * BPS
    return pd.Series(gross), pd.Series(reinv), w


def build_series(inc, ret_by_month, last_month_of):
    """Monthly net and gross series for the five portfolios, formation-date column, end weights of the last cohort."""
    rows, drift, ends, turn = [], {}, {}, []
    for d in sorted(inc.formation_date.unique()):
        d = pd.Timestamp(d)
        cohort = inc[inc.formation_date == d]
        months = holding_months(d)
        last_month = {p: last_month_of[(d, p)] for p in cohort.permno}
        groups = {b: cohort[cohort.bucket == b] for b in MAIN}
        groups["Benchmark"] = cohort
        groups["BenchmarkScored"] = cohort[cohort.scored]
        for name in PORTS:
            mem = groups[name]
            if mem.empty:
                raise Stop(f"{name} is empty on {d.date()}")
            gross, reinv, end_w = run_portfolio(mem.permno.tolist(), months, ret_by_month, last_month)
            target = pd.Series(1.0 / len(mem), index=mem.permno.tolist())
            prior = drift.get(name)
            two_way = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(target.sub(prior, fill_value=0).abs().sum())
            cost = two_way * BPS
            drift[name] = end_w
            ends[(d, name)] = end_w
            turn.append({"formation_date": d, "portfolio": name, "names": len(mem), "turnover_two_way": two_way})
            for i, m in enumerate(months):
                c = (cost if i == 0 else 0.0) + reinv[m]
                rows.append({"month": m, "formation_date": d, "portfolio": name, "n": len(mem), "gross": gross[m], "net": (1 + gross[m]) * (1 - c) - 1})
    long = pd.DataFrame(rows)
    wide = long.pivot(index="month", columns="portfolio", values=["net", "gross"])
    t = pd.DataFrame(index=wide.index)
    t["formation_date"] = long.drop_duplicates("month").set_index("month").formation_date
    for b in PORTS:
        t[b], t[f"{b}_gross"] = wide["net"][b], wide["gross"][b]
    t["Spread"] = t.High - t.Low
    return t, long, ends, pd.DataFrame(turn)


def fund_chain():
    b = pd.read_parquet(RAW / "crsp_benchmarks.parquet", columns=["permno", "ticker", "mthcaldt", "mthret"])
    b = b[b.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    b["month"] = b.mthcaldt.dt.to_period("M")
    b["mthret"] = b.mthret.astype(float)
    return b.groupby(["ticker", "month"]).mthret.apply(lambda s: (1 + s).prod() - 1).unstack("ticker")


def check_reproduces(tab, label="literal_sensitivity"):
    ref = pd.read_csv(ROOT / "output" / "spec_v2" / "literal_sensitivity" / "portfolio_returns_v2.csv")
    for c in PORTS + ["Spread"] + [f"{b}_gross" for b in PORTS]:
        if not np.allclose(ref[c].values, tab[c].values, atol=1e-10):
            raise Stop(f"baseline series {c} does not reproduce output/spec_v2/{label}/portfolio_returns_v2.csv")


# ---------------------------------------------------------------- statistics
def lag_formula(T):
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def fit(y, x, lags):
    X = sm.add_constant(x.astype(float)) if x is not None else pd.DataFrame({"const": np.ones(len(y))}, index=y.index)
    f = sm.OLS(y.astype(float), X).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False})
    df = int(f.nobs) - X.shape[1]
    t = f.params["const"] / f.bse["const"]
    return f.params["const"] * 12, t, 2 * st.t.sf(abs(t), df)


def cagr(r):
    return (1 + r).prod() ** (12 / len(r)) - 1


def maxdd(r):
    w = (1 + r).cumprod()
    return float((w / np.maximum.accumulate(np.r_[1.0, w.values])[1:] - 1).min())


def load_factors():
    ff = pd.read_parquet(RAW / "ff_factors.parquet")
    ff.index = pd.PeriodIndex(ff.month, freq="M")
    return ff.astype({c: float for c in ["mktrf", "smb", "hml", "rf", "umd"]})


def metrics(P, ff, windows=None, ext_block=True):
    """Dict {(block, item, series, window): value}. P columns: High, Middle, Low, Benchmark, BenchmarkScored, RSP, SPY (any may be NaN-only), index monthly Period, formation_date."""
    out = {}
    windows = windows or {"Jun2005-Dec2025": P.loc[:pd.Period(cfg.RETURNS_END, "M")], f"Jun2005-{cfg.EXTENSION_2026['end'][:7]}": P}
    for wn, w in windows.items():
        f = ff.reindex(w.index)
        if f[list(FC.values()) + ["rf"]].isna().any().any():
            raise Stop("missing factor values")
        for s in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored", "RSP", "SPY"]:
            if w[s].isna().all():
                continue
            x = w[s]
            ex = x - f.rf
            out[("performance", "months", s, wn)] = len(x)
            out[("performance", "CAGR", s, wn)] = cagr(x)
            out[("performance", "volatility", s, wn)] = x.std() * 12 ** 0.5
            out[("performance", "sharpe", s, wn)] = ex.mean() * 12 / (ex.std() * 12 ** 0.5)
            out[("performance", "max_drawdown", s, wn)] = maxdd(x)
        gaps = {"High_minus_Benchmark": w.High - w.Benchmark, "High_minus_BenchmarkScored": w.High - w.BenchmarkScored, "High_minus_Low": w.High - w.Low}
        for gname, d in gaps.items():
            if d.isna().all():
                continue
            out[("gap", "mean_monthly_x12", gname, wn)] = d.mean() * 12
            if gname != "High_minus_Low":
                bm = gname.split("_minus_")[1]
                out[("gap", "cagr_gap", gname, wn)] = cagr(w.High) - cagr(w[bm])
            lags = [lag_formula(len(d))] + SENS_EXTRA_LAGS
            out[("gap", "hac_lag_automatic", gname, wn)] = lags[0]
            for tag, L in zip(["auto"] + [f"lag{k}" for k in SENS_EXTRA_LAGS], lags):
                a, t, p = fit(d, None, L)
                out[("gap_test_raw", f"t_{tag}", gname, wn)] = t
                out[("gap_test_raw", f"p_{tag}", gname, wn)] = p
                a4, t4, p4 = fit(d, f[list(FC.values())], L)
                out[("gap_test_4factor", f"alpha_x12_{tag}", gname, wn)] = a4
                out[("gap_test_4factor", f"t_{tag}", gname, wn)] = t4
                out[("gap_test_4factor", f"p_{tag}", gname, wn)] = p4
        if True:
            y = w.groupby("formation_date").agg(n=("High", "size"), H=("High", lambda v: (1 + v).prod() - 1), B=("Benchmark", lambda v: (1 + v).prod() - 1), S=("BenchmarkScored", lambda v: (1 + v).prod() - 1))
            y = y[y.n == cfg.HOLDING_MONTHS]
            out[("hit_years", "complete_years", "High", wn)] = len(y)
            if not w.Benchmark.isna().all():
                out[("hit_years", "High_beats_Benchmark", "High", wn)] = int((y.H > y.B).sum())
            if not w.BenchmarkScored.isna().all():
                out[("hit_years", "High_beats_BenchmarkScored", "High", wn)] = int((y.H > y.S).sum())
    if not ext_block:
        return out
    ext = P.loc[pd.Period(cfg.RETURNS_END, "M") + 1:]
    comp = lambda v: (1 + v).prod() - 1
    for s in ["High", "Middle", "Low", "Benchmark", "BenchmarkScored", "RSP", "SPY"]:
        if ext[s].isna().all():
            continue
        out[("jan_may_2026", "compounded", s, "Jan-May2026")] = comp(ext[s])
        for m in ext.index:
            out[("jan_may_2026", f"month_{m}", s, "Jan-May2026")] = ext.loc[m, s]
    out[("jan_may_2026", "compounded", "High_minus_Low", "Jan-May2026")] = comp(ext.High) - comp(ext.Low)
    yr = P[P.formation_date == P.formation_date.max()]
    for s in ["High", "Low", "Benchmark", "BenchmarkScored"]:
        if not yr[s].isna().all():
            out[("holding_year_2025_26", "compounded_jun2025_may2026", s, "Jun2025-May2026")] = comp(yr[s])
    return out


# ---------------------------------------------------------------- security map (09a_extension_pull.py mapping procedure, applied to every name on the 2025 list)
def map_names(list_rows, crsp_all, secm, last):
    ref = secm[secm.month == last.to_period("M")]
    may = crsp_all[crsp_all.mthcaldt == last][["permno", "cusip", "ticker", "issuernm"]].rename(columns={"cusip": "crsp_cusip", "ticker": "crsp_ticker"})
    held = list_rows.merge(may, on="permno", how="left")
    rows = []
    for x in held.itertuples():
        same_gv = ref[ref.gvkey == x.gvkey]
        by_cusip = same_gv[same_gv.cusip8 == x.crsp_cusip]
        by_tic = same_gv[same_gv.tic == x.crsp_ticker]
        pick, method = None, ""
        if len(by_cusip) == 1:
            pick, method = by_cusip.iloc[0], "gvkey + CUSIP"
        elif len(by_cusip) > 1:
            usd = by_cusip[by_cusip.curcdm == "USD"]
            if len(usd) == 1:
                pick, method = usd.iloc[0], "gvkey + CUSIP, USD line"
        elif len(by_tic) == 1:
            pick, method = by_tic.iloc[0], "gvkey + ticker"
        elif len(same_gv) == 1:
            pick, method = same_gv.iloc[0], "gvkey, only line"
        else:
            other = ref[ref.cusip8 == x.crsp_cusip]
            if len(other) == 1:
                pick, method = other.iloc[0], "CUSIP, other gvkey"
        rows.append({"permno": x.permno, "bucket": x.bucket, "list_gvkey": x.gvkey, "gvkey": None if pick is None else pick.gvkey, "iid": None if pick is None else pick.iid,
                     "name": (pick.conm if pick is not None else ""), "method": method})
    return pd.DataFrame(rows)


def find_permno(map_df, name):
    hit = map_df[map_df.name.str.upper().str.contains(name.upper(), regex=False)]
    if len(hit) != 1:
        raise Stop(f"{name} matches {len(hit)} held names")
    return int(hit.permno.iloc[0])


def extend(end_weights, secm_by_month, exit_after, departed, window, overrides=None):
    """Five Compustat months from the December 2025 weights under the EXTENSION_2026 conditions; returns gross and net (one-sided charge on the value reinvested after a mid-window exit)."""
    overrides = overrides or {}
    gross, net = {}, {}
    w = end_weights.copy()
    for mth in window:
        live = [p for p in w.index if p not in departed and not (p in exit_after and mth > exit_after[p])]
        w = w.loc[live]
        rets = secm_by_month[mth]
        missing = [p for p in live if p not in rets.index]
        nulls = [p for p in live if p in rets.index and pd.isna(rets[p])]
        if missing or nulls:
            raise Stop(f"{mth}: {len(missing)} missing rows (permnos {missing[:8]}); {len(nulls)} null returns (permnos {nulls[:8]})")
        r = rets.loc[live].astype(float).copy()
        for (p, m2), v in overrides.items():
            if m2 == mth and p in r.index:
                r[p] = v
        w = w / w.sum()
        g = float((w * r).sum())
        w = w * (1 + r) / (1 + g)
        leaving = [p for p in w.index if p in exit_after and exit_after[p] == mth and mth < window[-1]]
        c = float(w.loc[leaving].sum()) * BPS
        gross[mth], net[mth] = g, (1 + g) * (1 - c) - 1
    return pd.Series(gross), pd.Series(net)


def v1_frame():
    """The v1-specification extension series (read only), renamed to v3 column names. v1 Benchmark held scored names only, so it maps to BenchmarkScored."""
    v1 = pd.read_csv(ROOT / "output" / "extension_2026" / "returns.csv")
    v1.index = pd.PeriodIndex(v1.month, freq="M")
    p = pd.DataFrame({"High": v1.High, "Middle": v1.Middle, "Low": v1.Low, "Benchmark": np.nan, "BenchmarkScored": v1.Benchmark, "RSP": v1.RSP, "SPY": v1.SPY}, index=v1.index)
    p["formation_date"] = pd.to_datetime(v1.formation_date)
    return p


def main():
    x = cfg.EXTENSION_2026
    if x["return_field"] != "trt1m" or cfg.DELISTING_RULE != "reinvest_pro_rata" or cfg.SPEC_V2["primary_benchmark"] != "equal_weight_all_included":
        sys.exit("STOP: locked rules differ from what this script implements")
    OUT.mkdir(parents=True, exist_ok=True)
    EXT.mkdir(parents=True, exist_ok=True)
    try:
        s12, fund, scores = v3_scores("literal")
        universe = pd.read_parquet(CLEAN / "universe.parquet")
        inc = s12.align(scores, universe)
        # the v3 list must be the one the existing literal run saved
        saved = pd.read_parquet(CLEAN / "spec_v2" / "formation_v2_literal.parquet")
        if not inc[["formation_date", "permno", "F_SCORE", "bucket"]].reset_index(drop=True).fillna(-1).equals(saved[["formation_date", "permno", "F_SCORE", "bucket"]].reset_index(drop=True).fillna(-1)):
            inc_s = inc.sort_values(["formation_date", "permno"]).reset_index(drop=True)
            sv = saved.sort_values(["formation_date", "permno"]).reset_index(drop=True)
            if not inc_s[["formation_date", "permno", "F_SCORE", "bucket"]].fillna(-1).equals(sv[["formation_date", "permno", "F_SCORE", "bucket"]].fillna(-1)):
                raise Stop("recomputed v3 list differs from data/clean/spec_v2/formation_v2_literal.parquet")
        crsp_all, by_permno, ret_by_month = load_crsp()
        last_month_of, flat_used = window_checks(inc, by_permno)
        tab, long, ends, turn = build_series(inc, ret_by_month, last_month_of)
        check_reproduces(tab)
        print("v3 literal baseline June 2005-December 2025 reproduced from the v2 literal file", flush=True)

        last = inc.formation_date.max()
        held = inc[inc.formation_date == last].copy()
        months_2025 = holding_months(last)
        window = pd.period_range(pd.Period(cfg.RETURNS_END, "M") + 1, pd.Period(x["end"], "M"), freq="M")
        s = pd.read_parquet(RAW / "comp_secm_extension.parquet", columns=["gvkey", "iid", "datadate", "trt1m", "prccm", "ajexm", "conm", "cusip", "tic", "curcdm"])
        s["month"] = s.datadate.dt.to_period("M")
        s["cusip8"] = s.cusip.str[:8]
        for c in ["trt1m", "prccm", "ajexm"]:
            s[c] = s[c].astype(float)
        s = s.sort_values(["gvkey", "iid", "month"])
        s["price_only"] = (s.prccm / s.ajexm).groupby([s.gvkey, s.iid]).pct_change(fill_method=None)
        s["ret"] = s.trt1m / 100

        map_df = map_names(held, crsp_all, s, last)
        bad = map_df[map_df.iid.isna()]
        if len(bad):
            raise Stop(f"{len(bad)} held names have no unique secm line by the 09a procedure (permnos {bad.permno.tolist()[:10]})")
        if map_df.duplicated(["gvkey", "iid"]).any():
            raise Stop("two held PERMNOs map to one gvkey-iid")
        v1map = pd.read_csv(ROOT / "output" / "extension_2026" / "security_map.csv", dtype={"gvkey": str, "iid": str})
        both = v1map.merge(map_df, on="permno", suffixes=("_v1", "_v3"))
        if ((both.gvkey_v1 != both.gvkey_v3) | (both.iid_v1 != both.iid_v3)).any():
            raise Stop("the 09a mapping procedure disagrees with the saved v1 security_map.csv for a name held in both")
        map_df["name"] = map_df.permno.map(v1map.set_index("permno").name).fillna(map_df.name)

        joined = map_df[["permno", "gvkey", "iid"]].merge(s, on=["gvkey", "iid"])
        secm_by_month = {m: joined[joined.month == m].set_index("permno").ret for m in window}

        # names that already left in CRSP: their final return is CRSP's (v1 rule); a name that left in the last CRSP month would be a case the locked rules do not price
        last_row = crsp_all[crsp_all.permno.isin(held.permno)].sort_values("mthcaldt").groupby("permno").agg(last_month=("month", "last"), flag=("mthdelflg", "last"))
        departed = set(last_row[(last_row.last_month < months_2025[-1]) | (last_row.flag != cfg.ACTIVE_DELISTING_FLAG)].index)
        left_in_dec = last_row[(last_row.last_month == months_2025[-1]) & (last_row.flag != cfg.ACTIVE_DELISTING_FLAG)]
        # Names whose CRSP series ends in the last CRSP month (acquired, final return in December) are treated by the v1 rule above (departed) and CLAUDE.md 8g clarification 3
        # (the extension starts from end-December weights and holds no such name). The v2 run does not charge an exit in its final month, so no charge is applied; the weight is reported below.
        exit_after = {find_permno(map_df, n): pd.Period(m, "M") for n, m in x["exits"].items()}
        spin = {find_permno(map_df, n): pd.Period(m, "M") for n, m in x["report_spinoff_months"].items()}

        funds = {}
        for t, (gv, iid) in x["benchmark_lines"].items():
            f = s[(s.gvkey == gv) & (s.iid == iid)].set_index("month").ret
            if not set(window) <= set(f.dropna().index):
                raise Stop(f"{t} is missing a month")
            funds[t] = f.loc[window]

        def build(overrides=None):
            gr, nt = {}, {}
            for b in PORTS:
                mem = held if b == "Benchmark" else held[held.scored] if b == "BenchmarkScored" else held[held.bucket == b]
                ends_b = ends[(last, b)].loc[lambda w: w.index.isin(mem.permno)]
                gr[b], nt[b] = extend(ends_b, secm_by_month, exit_after, departed, window, overrides)
            return pd.DataFrame(gr), pd.DataFrame(nt)

        ext_gross, ext_net = build()
    except Stop as e:
        (OUT / "STOPPED_28.md").write_text(f"# 28_v3_extension_2026 stopped\n\n{e}\n", encoding="utf-8")
        print("STOP:", e)
        sys.exit(1)

    def full_series(net):
        p = tab[PORTS].copy()
        ch = fund_chain()
        for t in cfg.SECONDARY_BENCHMARKS:
            p[t] = ch[t].reindex(p.index)
        p["formation_date"] = tab.formation_date
        add = net.copy()
        for t in funds:
            add[t] = funds[t]
        add["formation_date"] = last
        add.index = pd.PeriodIndex(add.index, freq="M")
        return pd.concat([p, add])

    ff = load_factors()
    full = full_series(ext_net)
    expected = pd.period_range(f"{cfg.FIRST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", pd.Period(x["end"], "M"), freq="M")
    if list(full.index) != list(expected):
        sys.exit("STOP: month index is not June 2005 to May 2026")
    full["Spread"] = full.High - full.Low
    m3 = metrics(full, ff)
    v1p = v1_frame()
    v1p["Spread"] = v1p.High - v1p.Low
    m1 = metrics(v1p, ff)

    # sensitivities (reported only): spin-off months at price-only; Hologic and Coterra final returns +/- EXIT_GAP_BP
    price_only = joined.set_index(["permno", "month"]).price_only
    spin_override = {(p, m): float(price_only[(p, m)]) for p, m in spin.items()}
    exit_ret = {(p, m): float(secm_by_month[m][p]) for p, m in exit_after.items()}
    runs = [("Base", None), ("Spin-off months at price-only return", spin_override), (f"Hologic and Coterra final returns +{EXIT_GAP_BP} bp", {k: v + EXIT_GAP_BP / 1e4 for k, v in exit_ret.items()}),
            (f"Hologic and Coterra final returns -{EXIT_GAP_BP} bp", {k: v - EXIT_GAP_BP / 1e4 for k, v in exit_ret.items()})]
    v1s = pd.read_csv(ROOT / "output" / "extension_2026" / "sensitivities.csv").set_index("run")
    sens = []
    for label, o in runs:
        _, net = build(o)
        comp = lambda v: float((1 + v).prod() - 1)
        for key, col in [("High", "High"), ("Low", "Low"), ("Benchmark", "Benchmark"), ("BenchmarkScored", "BenchmarkScored")]:
            sens.append({"block": "sensitivity", "item": "jan_may_2026_compounded", "series": key, "window": label, "v1_spec": (float(v1s.loc[label, f"{ 'Benchmark' if key == 'BenchmarkScored' else key}_jan_may"]) if key != "Benchmark" else np.nan), "v3_spec": comp(net[col])})

    rows = []
    for k in list(m3) + [k for k in m1 if k not in m3]:
        rows.append({"block": k[0], "item": k[1], "series": k[2], "window": k[3], "v1_spec": m1.get(k, np.nan), "v3_spec": m3.get(k, np.nan)})
    names = pd.DataFrame(rows + sens)
    names["difference_v3_minus_v1"] = names.v3_spec - names.v1_spec
    cnt = held.groupby("bucket").size().to_dict()
    v1c = pd.read_csv(ROOT / "output" / "extension_2026" / "security_map.csv")
    extra = []
    for b in PORTS:
        mem = held if b == "Benchmark" else held[held.scored] if b == "BenchmarkScored" else held[held.bucket == b]
        e = ends[(last, b)].loc[lambda w: w.index.isin(mem.permno)]
        wgt = float(e.loc[e.index.isin(left_in_dec.index)].sum() / e.sum())
        extra.append({"block": "list_2025", "item": "weight_of_names_leaving_in_last_crsp_month_at_dec2025", "series": b, "window": "2025 list; a 10 bp charge on it would be weight x 0.0010", "v1_spec": np.nan, "v3_spec": wgt})
    extra += [{"block": "list_2025", "item": "names_held", "series": b, "window": "2025 list", "v1_spec": np.nan, "v3_spec": float(cnt.get(b, 0))} for b in ["High", "Middle", "Low", "Unscored"]]
    extra += [{"block": "list_2025", "item": "names_held", "series": "Benchmark (all included)", "window": "2025 list", "v1_spec": np.nan, "v3_spec": float(len(held))},
              {"block": "list_2025", "item": "names_held", "series": "BenchmarkScored", "window": "2025 list", "v1_spec": float(len(v1c)), "v3_spec": float(held.scored.sum())}]
    out = pd.concat([pd.DataFrame(extra), names], ignore_index=True)
    out["note"] = ""
    out.loc[out.series == "BenchmarkScored", "note"] = "v1 Benchmark = scored names only, so it is compared here"
    out.loc[(out.series == "Benchmark") & (out.block != "list_2025"), "note"] = "v3 primary benchmark = all included names; no v1 counterpart"
    out.to_csv(OUT / "extension_2026_v3.csv", index=False)

    # company-level detail goes outside the shareable folder
    nm = map_df.merge(held[["permno", "F_SCORE", "scored"]], on="permno")
    nm["departed_by_dec2025"] = nm.permno.isin(departed)
    nm["exit_2026"] = nm.permno.map(lambda p: str(exit_after.get(p, "")))
    nm["spinoff_month_used"] = nm.permno.map(lambda p: str(spin.get(p, "")))
    nm.to_csv(EXT / "extension_2026_v3_names.csv", index=False)

    show = out[(out.block.isin(["jan_may_2026"])) & (out.item == "compounded")]
    print(show[["series", "v1_spec", "v3_spec"]].round(4).to_string(index=False))
    sel = out[(out.block.isin(["gap", "gap_test_raw", "gap_test_4factor", "hit_years"])) & out.item.isin(["mean_monthly_x12", "t_auto", "alpha_x12_auto", "High_beats_Benchmark", "High_beats_BenchmarkScored", "complete_years"])]
    print(sel[["block", "item", "series", "window", "v1_spec", "v3_spec"]].round(4).to_string(index=False))
    print(f"held {len(held)} names {cnt}; hold-flat months used {len(flat_used)}; departed {len(departed)}; exits {sorted(exit_after.values())}")


if __name__ == "__main__":
    main()
