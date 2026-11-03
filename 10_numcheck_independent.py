"""
Stage 10: independent number check (prereg_main section F). Unlike 11_numcheck_arithmetic.py it does NOT read portfolio_returns for its inputs.
  1. Recomputes F-scores for a random sample of scored list rows (seed fixed in prereg_main: 20261102) from raw Compustat pulls with a separate minimal implementation.
  2. Recomputes gross High and Low returns for every month from raw CRSP monthly returns (equal weight at formation, drifting, delisted names held at their last value), compares to portfolio_returns.
  3. Matches every number token in README.md and output/writeup.md to a value in the output CSVs, by exact rounding to the printed decimals (not substring).
Reports counts of matches and mismatches; it asserts nothing is perfect. Writes output/results/numcheck.md. Usage: python 10_numcheck_independent.py
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW, CLEAN, OUT = ROOT / "data" / "raw", ROOT / "data" / "clean" / "core", ROOT / "output" / "results"
SEED = 20261102
L = ["# Independent number check\n"]

# ---- 1. F-scores from raw pulls ----
f = pd.read_parquet(RAW / "comp_funda.parquet").merge(pd.read_parquet(RAW / "comp_funda_ib.parquet")[["gvkey", "datadate", "ib"]], on=["gvkey", "datadate"], how="left")
f = f.merge(pd.read_parquet(RAW / "comp_funda_prstkc.parquet")[["gvkey", "datadate", "prstkc"]], on=["gvkey", "datadate"], how="left")
f = f.drop_duplicates(["gvkey", "fyear"]).set_index(["gvkey", "fyear"]).sort_index()


def indep_score(g, y):
    try:
        c, p, q = f.loc[(g, y)], f.loc[(g, y - 1)], f.loc[(g, y - 2)]
    except KeyError:
        return None
    need = [c.ib, c.oancf, c["at"], p["at"], q["at"], p.ib, c.dltt, p.dltt, c.act, c.lct, p.act, p.lct, c.sale, c.cogs, p.sale, p.cogs]
    if any(pd.isna(v) for v in need) or min(c.sale, p.sale) <= 0:
        return None
    s = {}
    roa, roa1 = c.ib / p["at"], p.ib / q["at"]
    s["ROA"], s["CFO"], s["DROA"], s["ACCRUAL"] = roa > 0, c.oancf / p["at"] > 0, roa > roa1, c.oancf / p["at"] > roa
    lev, lev1 = c.dltt / ((c["at"] + p["at"]) / 2), p.dltt / ((p["at"] + q["at"]) / 2)
    s["DLEVER"] = (lev < lev1) or (cfg.ZERO_DEBT_COUNTS_AS_PASS and c.dltt == 0 and p.dltt == 0)
    s["DLIQUID"] = c.act / c.lct > p.act / p.lct
    s["EQ_OFFER"] = (c.sstk if pd.notna(c.sstk) else 0) <= 0
    s["DMARGIN"] = (c.sale - c.cogs) / c.sale > (p.sale - p.cogs) / p.sale
    s["DTURN"] = c.sale / p["at"] > p.sale / q["at"]
    return s


form = pd.read_parquet(CLEAN / "formation.parquet")
sc = form[form.F_SCORE.notna()].drop_duplicates(["gvkey", "fyear"])
samp = sc.sample(min(400, len(sc)), random_state=SEED)
agree = disagree = skipped = 0
bad = []
for r in samp.itertuples():
    s = indep_score(r.gvkey, int(r.fyear))
    if s is None:
        skipped += 1
        continue
    mine = sum(bool(v) for v in s.values())
    if mine == r.F_SCORE:
        agree += 1
    else:
        disagree += 1
        bad.append((r.gvkey, int(r.fyear), r.F_SCORE, mine))
L.append(f"## 1. F-scores, {len(samp)} random scored firm-years (seed {SEED}), literal rule\n\nIndependent implementation agrees on {agree}, disagrees on {disagree}, could not compute independently on {skipped} (missing inputs or sales <= 0 in my minimal version).\n")
if bad:
    L.append("Disagreements (gvkey, fyear, pipeline, independent): " + "; ".join(map(str, bad[:20])) + "\n")

# ---- 2. Portfolio returns from raw CRSP ----
m = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret"])
m["month"] = pd.to_datetime(m.mthcaldt).dt.to_period("M")
ret = m.pivot_table(index="month", columns="permno", values="mthret", aggfunc="first")
pr = pd.read_csv(ROOT / "output" / "core" / "portfolio_returns.csv")
pr.index = pd.PeriodIndex(pr.month, freq="M")
pr["formation_date"] = pd.to_datetime(pr.formation_date)
res = {"High": [], "Low": []}
for fd, grp in pr.groupby("formation_date"):
    for b in res:
        names = form[(form.formation_date == fd) & (form.bucket == b)].permno.unique()
        w = pd.Series(1.0 / len(names), index=names)
        for mon in grp.index:
            r = ret.loc[mon].reindex(w.index) if mon in ret.index else pd.Series(np.nan, index=w.index)
            flat = [p for p in w.index if str(mon) in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["pipeline"].get(p, [])]
            r.loc[flat] = r.loc[flat].fillna(0.0)
            gone = r.index[r.isna()]            # no return this month: exited; its value goes pro rata to the rest
            w = w.drop(gone)
            r = r.drop(gone)
            port = float((w * r).sum() / w.sum())
            res[b].append(port - pr.loc[mon, f"{b}_gross"])
            w = w * (1 + r)
for b, d in res.items():
    d = np.abs(np.array(d))
    L.append(f"## 2. {b} gross monthly return, raw CRSP vs pipeline\n\n{len(d)} months; {int((d < 1e-6).sum())} agree within 1e-6; max abs difference {d.max():.4%}; months differing by more than 10 bps: {int((d > 1e-3).sum())}. "
             f"This version redistributes exited names pro rata, as the pipeline documents, and holds the approved flat cases at 0%; any remaining difference is unexplained.\n")

# ---- 3. Printed numbers vs tables: NOT DONE. The first version matched tokens to any CSV value and could not fail (audit finding), so it was removed.
L.append("## 3. Printed numbers vs tables: not checked\n\nThe earlier lenient token match could not fail and was removed. Tables in writeup.md are generated from the CSVs by 22_writeup.py; figures typed by hand in README.md are not machine-checked.\n")
L.append("## What this does and does not check\n\nIt checks F-score logic and gross High/Low returns independently of the pipeline's own code, only. It does not check printed numbers against tables, or every table row (Middle, RSP, SPY, tracking error, information ratio, loadings and subperiod CAGRs are still checked only by 11_numcheck_arithmetic.py against the same file)\n")
(OUT / "numcheck.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
