"""
Stage 13: robustness under the final specification (prereg_main G and H9). Rebuilds High and the all-included benchmark for each variant using the stage 06 portfolio mechanics
(equal weight, buy and hold, pro rata redistribution on exit, one-sided charge on reinvestment, approved hold-flat months, TRANSACTION_COST_BPS on turnover).
Primary issuance rule = literal. The headline row must reproduce output/core/portfolio_returns.csv; the script stops if not.

Variants (all labelled; none chosen from):
  headline; high_7plus (High = 7-9); cap_weighted (weights = market cap at formation, High and benchmark); avail_filing_plus_30 / _60 (filing date + N days, N replaces the 3-day buffer);
  avail_datadate_plus_150 / _180 (ignore the filing date: a fiscal year is known 150 or 180 days after year-end; no-filing-date firm-years stay unscorable);
  score_on_available_signals (H9: firm-years missing some signals kept; score = sum of available signals / number available x 9, needs 7 or more available; High >= 8, Low <= 4).
Every variant row is compared with the headline; a row identical to it stops the run.
Usage: python 13_robustness.py        Writes output/results/robustness.csv
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
OUT = ROOT / "output" / "results"
OUT.mkdir(parents=True, exist_ok=True)
BPS = cfg.TRANSACTION_COST_BPS / 10000


def load(fn, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / fn)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SC = load("05_scores.py", "scores")
SIG = SC.SIGNALS
FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["pipeline"].items() for m in ms}

r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret"])
r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
r["month"] = r.mthcaldt.dt.to_period("M")
r["mthret"] = r.mthret.astype(float)
RET = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}
HAS = r.dropna(subset=["mthret"]).groupby("permno").month.apply(set).to_dict()
ff = pd.read_parquet(RAW / "ff_factors.parquet")
ff.index = pd.PeriodIndex(ff.month, freq="M")
rf = ff.rf.astype(float)


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def last_month(permno, months):
    ok = [m for m in months if m in HAS.get(permno, ()) or (permno, m) in FLAT]
    return max(ok) if ok else None


def run(members, weights, months, last):
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


def series(inc, high, cap):
    """Monthly net High and all-included Benchmark for a formation table."""
    out = {"High": [], "Benchmark": []}
    drift = {}
    idx = []
    for d in sorted(inc.formation_date.unique()):
        d = pd.Timestamp(d)
        coh = inc[inc.formation_date == d]
        months = holding_months(d)
        last = {p: last_month(p, months) for p in coh.permno}
        groups = {"High": coh[coh.bucket == "High"], "Benchmark": coh}
        for nm, mem in groups.items():
            wt = (mem.set_index("permno").mktcap if cap else pd.Series(1.0, index=mem.permno.values))
            wt = pd.Series(wt.values / wt.sum(), index=mem.permno.values)
            g, rv, end = run(mem.permno.tolist(), wt, months, last)
            prior = drift.get(nm)
            two = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(wt.sub(prior, fill_value=0).abs().sum())
            cost = two * BPS
            drift[nm] = end
            out[nm] += [(1 + g[m]) * (1 - ((cost if i == 0 else 0.0) + rv[m])) - 1 for i, m in enumerate(months)]
            if nm == "High":
                idx += list(months)
    return pd.DataFrame(out, index=pd.PeriodIndex(idx, freq="M"))


def stats(s):
    cg = lambda x: (1 + x).prod() ** (12 / len(x)) - 1
    d = s.High - s.Benchmark
    L = int(np.floor(4 * (len(d) / 100) ** (2 / 9)))
    f = sm.OLS(d.values, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": False})
    return {"months": len(s), "High_CAGR": cg(s.High), "Benchmark_CAGR": cg(s.Benchmark), "cagr_gap": cg(s.High) - cg(s.Benchmark), "mean_gap_x12": d.mean() * 12, "t": float(f.tvalues[0]),
            "High_sharpe": ((s.High - rf.reindex(s.index)).mean() * 12) / ((s.High - rf.reindex(s.index)).std() * 12 ** 0.5)}


SC.RULE = "literal"
fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
ib = pd.read_parquet(RAW / "comp_funda_ib.parquet")
pk = pd.read_parquet(RAW / "comp_funda_prstkc.parquet")
fund = fund.merge(ib[["gvkey", "datadate", "fyear", "ib"]].assign(fyear=lambda x: x.fyear.astype(int), ib=lambda x: x.ib.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
fund = fund.merge(pk[["gvkey", "datadate", "fyear", "prstkc"]].assign(fyear=lambda x: x.fyear.astype(int), prstkc=lambda x: x.prstkc.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
scores = SC.compute_scores(fund)
universe = pd.read_parquet(CLEAN / "universe.parquet")


def aligned(buffer_days=None, datadate_days=None, avail_signals=False):
    s = scores.copy()
    if buffer_days is not None:
        s["avail_date_buffered"] = s.filing_date + pd.Timedelta(days=buffer_days)
    if datadate_days is not None:
        s["avail_date_buffered"] = np.where(s.filing_date.notna(), np.maximum((s.datadate + pd.Timedelta(days=datadate_days)).values, (s.filing_date + pd.Timedelta(days=SC.PIPE["availability_buffer_days"])).values), np.datetime64("NaT"))
        s["avail_date_buffered"] = pd.to_datetime(s.avail_date_buffered)
    if avail_signals:
        n = s[SIG].notna().sum(axis=1)
        raw = s[SIG].sum(axis=1) / n.where(n > 0) * 9
        s["F_SCORE"] = raw.where((n >= 7) & s.filing_date.notna())
    m = SC.align(s, universe)
    if avail_signals:
        m["bucket"] = m.F_SCORE.map(lambda v: "Unscored" if pd.isna(v) else "High" if v >= 8 else "Low" if v <= 4 else "Middle")
    return m


variants = {
    "headline": dict(m=aligned(), cap=False),
    "high_7plus": dict(m=aligned(), cap=False, hi=7),
    "cap_weighted": dict(m=aligned(), cap=True),
    "avail_filing_plus_30": dict(m=aligned(buffer_days=30), cap=False),
    "avail_filing_plus_60": dict(m=aligned(buffer_days=60), cap=False),
    "avail_datadate_plus_150": dict(m=aligned(datadate_days=150), cap=False),
    "avail_datadate_plus_180": dict(m=aligned(datadate_days=180), cap=False),
    "score_on_available_signals": dict(m=aligned(avail_signals=True), cap=False),
}
rows, base = [], None
for name, v in variants.items():
    m = v["m"].copy()
    if "hi" in v:
        m["bucket"] = np.where(m.scored & (m.F_SCORE >= v["hi"]), "High", np.where(m.scored, np.where(m.bucket == "Low", "Low", "Middle"), "Unscored"))
    s = series(m, True, v["cap"])
    st_ = stats(s)
    st_.update({"variant": name, "High_names_total": int((m.bucket == "High").sum()), "scored_rows": int(m.scored.sum())})
    if name == "headline":
        base = s
        ref = pd.read_csv(ROOT / "output/core/portfolio_returns.csv")
        assert np.allclose(ref.High.values, s.High.values, atol=1e-10) and np.allclose(ref.Benchmark.values, s.Benchmark.values, atol=1e-10), "headline does not reproduce the literal portfolio"
    else:
        assert not (len(s) == len(base) and np.allclose(s.High.values, base.High.values, atol=1e-12)), f"{name} is identical to the headline"
    rows.append(st_)
res = pd.DataFrame(rows)[["variant", "months", "scored_rows", "High_names_total", "High_CAGR", "Benchmark_CAGR", "cagr_gap", "mean_gap_x12", "t", "High_sharpe"]]
res.to_csv(OUT / "robustness.csv", index=False)
print(res.round(4).to_string())
