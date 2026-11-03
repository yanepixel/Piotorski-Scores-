"""
Stage 14: robustness, five more variants under the final specification (prereg_main; same engine as 13_robustness.py, copied not imported).
Mechanics: literal issuance rule primary, equal weight, buy and hold, pro rata redistribution on exit, one-sided charge on reinvestment, TRANSACTION_COST_BPS on turnover,
approved hold-flat months, High vs an all-included benchmark. Headline row must reproduce output/core/portfolio_returns.csv or the script stops.

Variants (definitions locked in config.py before their results were seen; nothing tuned, nothing chosen from returns; every variant is compared with the headline and must differ):
  sector_neutral            High and benchmark both hold the benchmark's (all included names that date) sector weights, equal weight within sector, empty sector spread pro rata.
  value_filter_B            only names in the cheapest third by book-to-market ((ceq + txditc)/formation mktcap, USD rows, scored rows only, boundary by exact quantile 1/3);
                            High = High within them; benchmark = that same cheapest-third set (the variant's own all-included set; unscored names cannot be ranked so are not in it).
  profitability_screen      require trailing-four-quarter niq > 0 and latest quarter niq > 0 (unconfirmed counts as failed), on EVERY included name (scored or not), so the benchmark is
                            the screened all-included set and High = scored High that pass.
  universe_buffer           universe enters at rank <= 450, stays until rank > 550 (first list top 500); read from data/clean/universe_buffer.parquet
                            (built by 01b_build_universe_buffer.py, which checks that its plain path reproduces the headline universe). Benchmark = all included names of the buffered universe. Comverse (PERMNO 10942) Feb-May 2007 held flat.
  eight_signal_no_liquidity firm-years whose only uncomputable signal is F_DLIQUID (and that have a real 10-K filing date) are scored out of 8: High = 8, Low = 0-3, Middle = 4-7;
                            nine-signal firm-years keep High 8-9, Low 0-4, Middle 5-7 (config HIGH_SCORES/LOW_SCORES); benchmark = all included names (unchanged set).
Usage: python -W ignore 14_robustness_extra.py     Writes output/results/robustness_extra.csv
"""
import importlib.util
from fractions import Fraction
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
EIGHT_SIGNALS = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]   # the nine signals without F_DLIQUID
EIGHT_HIGH, EIGHT_LOW = cfg.EIGHT_SIGNAL_HIGH_SCORES, cfg.EIGHT_SIGNAL_LOW_SCORES
VALUE_Q = Fraction(cfg.VALUE_FILTER_QUANTILE).limit_denominator(1000)                                        # 1/3
BUFFER_FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["universe_buffer"].items() for m in ms}   # Comverse


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
_n = r[r.mthret.isna()]
NULLS = set(zip(_n.permno.astype(int), _n.month))
ff = pd.read_parquet(RAW / "ff_factors.parquet")
ff.index = pd.PeriodIndex(ff.month, freq="M")
rf = ff.rf.astype(float)


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def last_month(permno, months, flat):
    ok = [m for m in months if m in HAS.get(permno, ()) or (permno, m) in flat]
    return max(ok) if ok else None


def run(weights, months, last, flat):
    w = weights.copy()
    gross, reinv = {}, {}
    for m in months:
        rets = RET.get(m, pd.Series(dtype=float)).copy()
        for p in [p for p in w.index if (p, m) in flat]:
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


def target_weights(mem, coh, sector):
    if sector:   # sector-neutral weights: benchmark sector shares, equal within sector, empty sectors drop out (pro rata via normalisation)
        share = coh.groupby("gsector").size() / len(coh)
        within = mem.groupby("gsector").permno.transform("size")
        w = pd.Series((mem.gsector.map(share) / within).values, index=mem.permno.values)
    else:
        w = pd.Series(1.0, index=mem.permno.values)
    return w / w.sum()


def series(inc, sector=False, flat=FLAT):
    """Monthly net High and all-included Benchmark. inc = the variant's own included rows with a bucket column."""
    out = {"High": [], "Benchmark": []}
    drift, idx, unapproved, min_high = {}, [], [], 10 ** 9
    for d in sorted(inc.formation_date.unique()):
        d = pd.Timestamp(d)
        coh = inc[inc.formation_date == d].copy()
        coh["gsector"] = coh.gsector.astype(object).where(coh.gsector.notna(), "NA")
        months = holding_months(d)
        last = {p: last_month(p, months, flat) for p in coh.permno}
        unapproved += [(int(p), str(m)) for p in coh.permno for m in months if (int(p), m) in NULLS and (p, m) not in flat]
        groups = {"High": coh[coh.bucket == "High"], "Benchmark": coh}
        if groups["High"].empty:
            raise RuntimeError(f"High is empty on {d.date()}")
        min_high = min(min_high, len(groups["High"]))
        for nm, mem in groups.items():
            wt = target_weights(mem, coh, sector)
            g, rv, end = run(wt, months, last, flat)
            prior = drift.get(nm)
            two = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(wt.sub(prior, fill_value=0).abs().sum())
            cost = two * BPS
            drift[nm] = end
            out[nm] += [(1 + g[m]) * (1 - ((cost if i == 0 else 0.0) + rv[m])) - 1 for i, m in enumerate(months)]
            if nm == "High":
                idx += list(months)
    return pd.DataFrame(out, index=pd.PeriodIndex(idx, freq="M")), sorted(set(unapproved)), min_high


def stats(s):
    cg = lambda x: (1 + x).prod() ** (12 / len(x)) - 1
    d = s.High - s.Benchmark
    L = int(np.floor(4 * (len(d) / 100) ** (2 / 9)))
    f = sm.OLS(d.values, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": False})
    ex = s.High - rf.reindex(s.index)
    return {"months": len(s), "High_CAGR": cg(s.High), "Benchmark_CAGR": cg(s.Benchmark), "cagr_gap": cg(s.High) - cg(s.Benchmark), "mean_gap_x12": d.mean() * 12, "t": float(f.tvalues[0]),
            "High_sharpe": (ex.mean() * 12) / (ex.std() * 12 ** 0.5)}


def profitability_screen(held, q, filings_q):   # applied to every included row
    filings_k = pd.read_parquet(RAW / "comp_co_filedate.parquet", columns=["gvkey", "srctype", "datadate", "filedate"])
    f = pd.concat([filings_q[["gvkey", "srctype", "datadate", "filedate"]], filings_k])
    f = f[f.srctype.isin(cfg.QTR_FILING_SRCTYPES) & (f.filedate > f.datadate)]
    first = f.groupby(["gvkey", "datadate"]).filedate.min().rename("filed").reset_index()
    e = cfg.QTR_EARNINGS_FIELD
    q = q.copy()
    q[e] = q[e].astype(float)
    q["has_e"] = q[e].notna()
    q = q.sort_values(["gvkey", "datadate", "has_e", "fyearq"]).drop_duplicates(["gvkey", "datadate"], keep="last")
    q = q.merge(first, on=["gvkey", "datadate"], how="left")
    q["avail"] = q.filed.fillna(q.datadate + pd.to_timedelta(cfg.FALLBACK_LAG_DAYS, unit="D"))
    q["month_no"] = q.datadate.dt.year * 12 + q.datadate.dt.month
    by = dict(tuple(q.sort_values(["gvkey", "datadate"]).groupby("gvkey")))
    results = []
    for x in held.itertuples():
        k = by.get(x.gvkey)
        a = k[k.avail <= x.formation_date].tail(4) if k is not None else None
        if a is None or len(a) < 4:
            results.append("unconfirmed: fewer than 4 quarters")
        elif not (a.month_no.diff().dropna() == 3).all():
            results.append("unconfirmed: quarters not consecutive")
        elif a[e].isna().any():
            results.append("unconfirmed: null earnings")
        elif (x.formation_date.year * 12 + x.formation_date.month) - a.month_no.iloc[-1] > cfg.MAX_SCORE_AGE_MONTHS:
            results.append("unconfirmed: latest quarter too old")
        elif a[e].sum() > 0 and a[e].iloc[-1] > 0:
            results.append("pass")
        else:
            results.append("failed: earnings not positive")
    return pd.Series(results, index=held.index)


SC.RULE = "literal"
fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
ib = pd.read_parquet(RAW / "comp_funda_ib.parquet")
pk = pd.read_parquet(RAW / "comp_funda_prstkc.parquet")
fund = fund.merge(ib[["gvkey", "datadate", "fyear", "ib"]].assign(fyear=lambda x: x.fyear.astype(int), ib=lambda x: x.ib.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
fund = fund.merge(pk[["gvkey", "datadate", "fyear", "prstkc"]].assign(fyear=lambda x: x.fyear.astype(int), prstkc=lambda x: x.prstkc.astype(float)), on=["gvkey", "datadate", "fyear"], how="left")
scores = SC.compute_scores(fund)
assert not scores.duplicated(["gvkey", "fyear"]).any()
universe = pd.read_parquet(CLEAN / "universe.parquet")
buffered = pd.read_parquet(CLEAN / "universe_buffer.parquet")
for df_ in (buffered, universe):
    for col in ["permno", "permco"]:
        df_[col] = df_[col].astype("int64")

head = SC.align(scores, universe)
variants = {"headline": dict(inc=head), "sector_neutral": dict(inc=head, sector=True)}

# value_filter_B
b = head.merge(scores[["gvkey", "fyear", "datadate", "ceq", "txditc", "curcd"]], on=["gvkey", "fyear", "datadate"], how="left", validate="m:1")
b["book_equity"] = (b.ceq + b.txditc.fillna(0)).where(b.scored)
b["btm"] = b.book_equity / b.mktcap
ranked = b.scored & (b.curcd == cfg.VERSION_B_CURRENCY) & b.btm.notna()
b["in_b"] = False
for d, g in b[ranked].groupby("formation_date"):
    hi = SC.exact_quantile(g.btm, 1 - VALUE_Q)
    b.loc[g.index[g.btm >= hi], "in_b"] = True
variants["value_filter_B"] = dict(inc=b[b.in_b].copy())

# profitability_screen: every included name
fq = pd.read_parquet(RAW / "comp_fundq.parquet")
fqf = pd.read_parquet(RAW / "comp_co_filedate_quarterly.parquet")
p = head.copy()
p["screen"] = profitability_screen(p, fq, fqf)
variants["profitability_screen"] = dict(inc=p[p.screen == "pass"].copy())
screen_counts = p.groupby(["bucket", "screen"]).size().unstack(fill_value=0)

variants["universe_buffer"] = dict(inc=SC.align(scores, buffered), flat=FLAT | BUFFER_FLAT)

# eight_signal_no_liquidity
s8 = scores.copy()
s8["score_type"] = "nine"
no_liq = s8.F_SCORE.isna() & s8.F_DLIQUID.isna() & s8[EIGHT_SIGNALS].notna().all(axis=1) & s8.filing_date.notna() & ~s8.stub_flag.astype(bool)
s8.loc[no_liq, "F_SCORE"] = s8.loc[no_liq, EIGHT_SIGNALS].sum(axis=1)
s8.loc[no_liq, "score_type"] = "eight"
e8 = SC.align(s8, universe).merge(s8[["gvkey", "fyear", "datadate", "score_type"]], on=["gvkey", "fyear", "datadate"], how="left", validate="m:1")
eight = e8.score_type == "eight"
e8["bucket"] = np.where(~e8.scored, "Unscored", np.where(eight, np.where(e8.F_SCORE.isin(EIGHT_HIGH), "High", np.where(e8.F_SCORE.isin(EIGHT_LOW), "Low", "Middle")), e8.bucket))
variants["eight_signal_no_liquidity"] = dict(inc=e8)

rows, base = [], None
for name, v in variants.items():
    inc = v["inc"]
    s, unapproved, min_high = series(inc, v.get("sector", False), v.get("flat", FLAT))
    assert not unapproved, f"{name}: unapproved null returns in holding windows {unapproved[:10]}"
    st_ = stats(s)
    st_.update({"variant": name, "universe_rows": len(inc), "scored_rows": int(inc.scored.sum()), "High_names_total": int((inc.bucket == "High").sum()), "High_min_names_per_date": min_high})
    if name == "headline":
        base = s
        ref = pd.read_csv(ROOT / "output/core/portfolio_returns.csv")
        assert np.allclose(ref.High.values, s.High.values, atol=1e-10) and np.allclose(ref.Benchmark.values, s.Benchmark.values, atol=1e-10), "headline does not reproduce the literal portfolio"
    else:
        assert not (len(s) == len(base) and np.allclose(s.High.values, base.High.values, atol=1e-12)), f"{name} High is identical to the headline"
    rows.append(st_)
    if name == "eight_signal_no_liquidity":
        print("eight-signal list rows:", int(eight.sum()), e8[eight].bucket.value_counts().to_dict())
res = pd.DataFrame(rows)[["variant", "months", "universe_rows", "scored_rows", "High_names_total", "High_min_names_per_date", "High_CAGR", "Benchmark_CAGR", "cagr_gap", "mean_gap_x12", "t", "High_sharpe"]]
res.to_csv(OUT / "robustness_extra.csv", index=False)
print(res.round(4).to_string())
print(screen_counts)
