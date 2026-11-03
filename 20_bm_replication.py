"""
Stage 20: book-to-market replication-LITE inside the top-500 universe (prereg_bm.md). NOT a replication of Piotroski (2000): no small value firms.
Top book-to-market quintile (ceq / (prcc_f*csho), fiscal year of the score) of scored included names per formation date; High vs whole quintile, High vs Low.
Mechanics copied from 13_robustness.py (literal issuance rule). Usage: python -W ignore 20_bm_replication.py   Writes output/results/bm_replication.csv
"""
import importlib.util
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
OUT = ROOT / "output" / "results"
BPS = cfg.TRANSACTION_COST_BPS / 10000


def load(fn, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / fn)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SC = load("05_scores.py", "scores")
FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["pipeline"].items() for m in ms}
r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret"])
r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
r["month"] = r.mthcaldt.dt.to_period("M")
r["mthret"] = r.mthret.astype(float)
RET = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}
HAS = r.dropna(subset=["mthret"]).groupby("permno").month.apply(set).to_dict()
ff = pd.read_parquet(RAW / "ff_factors.parquet")
ff.index = pd.PeriodIndex(ff.month, freq="M")


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def last_month(permno, months):
    ok = [m for m in months if m in HAS.get(permno, ()) or (permno, m) in FLAT]
    return max(ok) if ok else None


def run(weights, months, last):
    w = weights.copy()
    gross, reinv = {}, {}
    for m in months:
        rets = RET.get(m, pd.Series(dtype=float)).copy()
        for p in [p for p in w.index if (p, m) in FLAT]:
            rets.loc[p] = 0.0
        w = w.loc[w.index.intersection(rets.index)]
        w = w / w.sum()
        rr = rets.loc[w.index]
        g = float((w * rr).sum())
        gross[m] = g
        w = w * (1 + rr) / (1 + g)
        leaving = [p for p in w.index if last.get(p) == m and m < months[-1]]
        reinv[m] = float(w.loc[leaving].sum()) * BPS
    return pd.Series(gross), pd.Series(reinv), w


# ---- scores (literal rule) and book-to-market ----
SC.RULE = "literal"
fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
ib = pd.read_parquet(RAW / "comp_funda_ib.parquet")
pk = pd.read_parquet(RAW / "comp_funda_prstkc.parquet")
fund = fund.merge(ib[["gvkey", "datadate", "fyear", "ib"]].assign(fyear=lambda x: x.fyear.astype(int), ib=lambda x: x.ib.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
fund = fund.merge(pk[["gvkey", "datadate", "fyear", "prstkc"]].assign(fyear=lambda x: x.fyear.astype(int), prstkc=lambda x: x.prstkc.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
scores = SC.compute_scores(fund)
universe = pd.read_parquet(CLEAN / "universe.parquet")
m = SC.align(scores, universe)
raw = pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey", "datadate", "ceq", "csho", "prcc_f", "curcd"])
assert not raw.duplicated(["gvkey", "datadate"]).any()
m = m.merge(raw, on=["gvkey", "datadate"], how="left", validate="m:1")
for c in ["ceq", "csho", "prcc_f"]:
    m[c] = m[c].astype(float)
m["bm"] = m.ceq / (m.prcc_f * m.csho).where((m.prcc_f > 0) & (m.csho > 0))
m["rankable"] = m.scored & (m.curcd == cfg.VERSION_B_CURRENCY) & np.isfinite(m.bm)
q = Fraction(4, 5)
m["in_q"] = False
for d, g in m[m.rankable].groupby("formation_date"):
    cut = SC.exact_quantile(g.bm, q)
    m.loc[g.index[g.bm >= cut], "in_q"] = True
quint = m[m.in_q].copy()
dates = sorted(m.formation_date.unique())
counts = pd.DataFrame({
    "rankable": m[m.rankable].groupby("formation_date").size(),
    "quintile": quint.groupby("formation_date").size(),
    "High": quint[quint.bucket == "High"].groupby("formation_date").size(),
    "Low": quint[quint.bucket == "Low"].groupby("formation_date").size()}).reindex(dates).fillna(0).astype(int)

# ---- portfolios ----
res = {"High": {}, "Low": {}, "Quintile": {}}
drift = {}
for d in dates:
    d = pd.Timestamp(d)
    coh = quint[quint.formation_date == d]
    months = holding_months(d)
    last = {p: last_month(p, months) for p in coh.permno}
    groups = {"High": coh[coh.bucket == "High"], "Low": coh[coh.bucket == "Low"], "Quintile": coh}
    for nm, mem in groups.items():
        if len(mem) == 0:
            drift[nm] = None
            continue
        wt = pd.Series(1.0 / len(mem), index=mem.permno.values)
        g, rv, end = run(wt, months, last)
        prior = drift.get(nm)
        two = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(wt.sub(prior, fill_value=0).abs().sum())
        cost = two * BPS
        drift[nm] = end
        for i, mo in enumerate(months):
            res[nm][mo] = (1 + g[mo]) * (1 - ((cost if i == 0 else 0.0) + rv[mo])) - 1
S = pd.DataFrame({k: pd.Series(v) for k, v in res.items()})
S.index = pd.PeriodIndex(S.index, freq="M")
S = S.sort_index()
fac = ff.loc[S.index.intersection(ff.index), ["mktrf", "smb", "hml", "umd"]].astype(float)
assert fac.mktrf.abs().max() < 1, "factor units are not decimals"


def cagr(x):
    return (1 + x).prod() ** (12 / len(x)) - 1


def hac(y, X):
    L = int(np.floor(4 * (len(y) / 100) ** (2 / 9)))
    f = sm.OLS(y.values, X.values).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": False})
    df = len(y) - X.shape[1]
    t = f.tvalues[0]
    mde = (st.t.ppf(0.975, df) + st.t.ppf(0.8, df)) * f.bse[0]
    return dict(months=len(y), hac_lags=L, df=df, est_annual=f.params[0] * 12, se_annual=f.bse[0] * 12, t=t, p=2 * st.t.sf(abs(t), df), mde_80_annual=mde * 12)


def test(a, b, kind):
    d = (S[a] - S[b]).dropna()
    one = pd.DataFrame({"c": np.ones(len(d))}, index=d.index)
    X = one if kind == "mean" else one.join(fac.reindex(d.index))
    row = hac(d, X)
    row.update(comparison=f"{a} - {b}", test=kind, **{f"{a}_CAGR_overlap": cagr(S.loc[d.index, a]), f"{b}_CAGR_overlap": cagr(S.loc[d.index, b])})
    return row


t = pd.DataFrame([test("High", "Quintile", "mean"), test("High", "Quintile", "alpha4"), test("High", "Low", "mean"), test("High", "Low", "alpha4")])
fam = t.iloc[:2].p.values
adj = np.empty(2)
cur = 0.0
for k, i in enumerate(np.argsort(fam)):
    cur = max(cur, min(1.0, (2 - k) * fam[i]))
    adj[i] = cur
t["holm_p_family"] = list(adj) + [np.nan, np.nan]
t["family"] = ["primary (Holm over 2)", "primary (Holm over 2)", "descriptive", "descriptive"]
for nm in ["High", "Low", "Quintile"]:
    t[f"{nm}_months_total"] = int(S[nm].notna().sum())
t["dates"] = len(counts)
t["dates_High_lt10"] = int((counts.High < 10).sum())
t["dates_Low_lt10"] = int((counts.Low < 10).sum())
t["dates_quintile_lt10"] = int((counts.quintile < 10).sum())
t["dates_High_zero"] = int((counts.High == 0).sum())
t["dates_Low_zero"] = int((counts.Low == 0).sum())
t["median_High_names"] = counts.High.median()
t["median_Low_names"] = counts.Low.median()
t["median_quintile_names"] = counts.quintile.median()
OUT.mkdir(parents=True, exist_ok=True)
t.to_csv(OUT / "bm_replication.csv", index=False)
pd.set_option("display.width", 250)
print(t[["comparison", "test", "family", "months", "hac_lags", "df", "est_annual", "se_annual", "t", "p", "holm_p_family", "mde_80_annual"]].round(4).to_string())
print("CAGRs (own months):", {k: round(cagr(S[k].dropna()), 4) for k in S}, "months", S.notna().sum().to_dict())
print("ranked rows", int(m.rankable.sum()), "of scored", int(m.scored.sum()), "of included", len(m))
print(counts.describe().round(1).to_string())
print("thin dates (<10): High", int((counts.High < 10).sum()), "Low", int((counts.Low < 10).sum()), "quintile", int((counts.quintile < 10).sum()), "of", len(counts))
print("zero High", int((counts.High == 0).sum()), "zero Low", int((counts.Low == 0).sum()))
print(counts.to_string())
