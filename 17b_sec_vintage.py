"""
Stage 17b: SEC vintage check for FY2015-2024 (answers the restatement gap that Compustat comp_snapshot, denied on this account, would have covered).
For a random sample of scored firm-years, recompute the F-score (paper's literal issuance rule) two ways from SEC XBRL company facts (data.sec.gov, as filed):
  PIT    = every input is the latest value that had been filed on or before the original 10-K's filing date for year t (what an investor could see);
  LATEST = every input is the latest value filed ever (what a current-vintage database holds).
Comparing PIT with LATEST measures how much restatement can move the score, independent of tag mapping, because both use the same tags.
SEC-LATEST is also compared with the Compustat score used in the backtest (mapping check, informational only).
Sample: 250 scored list rows, FY2015-2024, seed fixed here (20261103). Downloads cached in data/external/sec (not committed). Downloaded files are untrusted: parsed as JSON only.
Output: output/results/sec_vintage_check.md (aggregates only) and data/external/sec_vintage_rows.csv (company-level, private).
Usage: python 17b_sec_vintage.py   (run 17a_pull_cik.py first)
"""
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "data" / "external" / "sec"
CACHE.mkdir(parents=True, exist_ok=True)
SEED, N = 20261103, 250
UA = "PiotroskiBacktest academic-research"
TAGS = {
    "ib": ["IncomeLossFromContinuingOperations", "ProfitLoss", "NetIncomeLoss"],
    "oancf": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "at": ["Assets"], "act": ["AssetsCurrent"], "lct": ["LiabilitiesCurrent"],
    "dltt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "sale": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"],
    "cogs": ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"],
    "sstk": ["StockIssuedDuringPeriodValueNewIssues", "ProceedsFromIssuanceOfCommonStock", "ProceedsFromIssuanceOrSaleOfEquity"],
}
FLOW = {"ib", "oancf", "sale", "cogs", "sstk"}


def fetch(cik):
    p = CACHE / f"CIK{int(cik):010d}.json"
    if not p.exists():
        req = urllib.request.Request(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json", headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        try:
            p.write_bytes(urllib.request.urlopen(req, timeout=90).read())
        except Exception:
            return None
        time.sleep(0.2)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def entries(facts, item):
    """Annual 10-K entries per tag, in tag priority order: list of (end, filed, val)."""
    out = []
    for tag in TAGS[item]:
        e = []
        for unit in facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", []):
            if not str(unit.get("form", "")).startswith("10-K"):
                continue
            if item in FLOW:
                try:
                    days = (pd.Timestamp(unit["end"]) - pd.Timestamp(unit["start"])).days
                except Exception:
                    continue
                if not 340 <= days <= 380:
                    continue
            e.append((pd.Timestamp(unit["end"]), pd.Timestamp(unit["filed"]), float(unit["val"])))
        if e:
            out.append(e)
    return out


def value(ent, target, asof, tol):
    """Latest value filed on or before asof (None = ever) for the period ending nearest target within tol days; first tag that has it."""
    for e in ent:
        cand = [x for x in e if abs((x[0] - target).days) <= tol and (asof is None or x[1] <= asof)]
        if cand:
            near = min(abs((x[0] - target).days) for x in cand)
            cand = [x for x in cand if abs((x[0] - target).days) == near]
            return max(cand, key=lambda x: x[1])[2]
    return np.nan


def score(vals):
    c, p, q = vals["t"], vals["t1"], vals["t2"]
    need = [c["ib"], c["oancf"], c["at"], p["at"], q["at"], p["ib"], c["dltt"], p["dltt"], c["act"], c["lct"], p["act"], p["lct"], c["sale"], c["cogs"], p["sale"], p["cogs"]]
    if any(pd.isna(v) for v in need) or min(c["sale"], p["sale"]) <= 0:
        return None
    s = {}
    roa, roa1 = c["ib"] / p["at"], p["ib"] / q["at"]
    s["ROA"], s["CFO"], s["DROA"], s["ACCRUAL"] = roa > 0, c["oancf"] / p["at"] > 0, roa > roa1, c["oancf"] / p["at"] > roa
    lev, lev1 = c["dltt"] / ((c["at"] + p["at"]) / 2), p["dltt"] / ((p["at"] + q["at"]) / 2)
    s["DLEVER"] = (lev < lev1) or (cfg.ZERO_DEBT_COUNTS_AS_PASS and c["dltt"] == 0 and p["dltt"] == 0)
    s["DLIQUID"] = c["act"] / c["lct"] > p["act"] / p["lct"]
    sstk = 0 if pd.isna(c["sstk"]) else c["sstk"]
    s["EQ_OFFER"] = sstk <= 0
    s["DMARGIN"] = (c["sale"] - c["cogs"]) / c["sale"] > (p["sale"] - p["cogs"]) / p["sale"]
    s["DTURN"] = c["sale"] / p["at"] > p["sale"] / q["at"]
    return s


def bucket(v):
    return "High" if v in cfg.HIGH_SCORES else "Low" if v in cfg.LOW_SCORES else "Middle"


form = pd.read_parquet(ROOT / "data/clean/core/formation.parquet")
sc = form[form.F_SCORE.notna() & form.fyear.between(2015, 2024)].drop_duplicates(["gvkey", "fyear"])
cik = pd.read_parquet(ROOT / "data/raw/comp_company_cik.parquet").dropna(subset=["cik"])
sc = sc.merge(cik, on="gvkey", how="left")
samp = sc.sample(min(N, len(sc)), random_state=SEED)
rows, nocik, nofacts, noscore = [], 0, 0, 0
for r in samp.itertuples():
    if pd.isna(r.cik):
        nocik += 1
        continue
    facts = fetch(r.cik)
    if facts is None:
        nofacts += 1
        continue
    ent = {k: entries(facts, k) for k in TAGS}
    dd = pd.Timestamp(r.datadate)
    # original 10-K filing date for year t: earliest filing that reports total assets for this period
    orig = min((x[1] for e in ent["at"] for x in e if abs((x[0] - dd).days) <= 7), default=None)
    if orig is None:
        nofacts += 1
        continue
    ends = {"t": (dd, 7), "t1": (dd - pd.DateOffset(years=1), 20), "t2": (dd - pd.DateOffset(years=2), 20)}
    ver = {}
    for name, asof in (("PIT", orig), ("LATEST", None)):
        ver[name] = {k: {it: value(ent[it], ends[k][0], asof, ends[k][1]) for it in TAGS} for k in ends}
    sp, sl = score(ver["PIT"]), score(ver["LATEST"])
    if sp is None or sl is None:
        noscore += 1
        continue
    pit, lat = sum(map(bool, sp.values())), sum(map(bool, sl.values()))
    diff_inputs = {it: (not np.isclose(ver["PIT"]["t"][it], ver["LATEST"]["t"][it], equal_nan=True)) or (not np.isclose(ver["PIT"]["t1"][it], ver["LATEST"]["t1"][it], equal_nan=True)) for it in TAGS}
    rows.append({"gvkey": r.gvkey, "fyear": int(r.fyear), "compustat_score": r.F_SCORE, "sec_pit_score": pit, "sec_latest_score": lat,
                 "signals_changed": sum(bool(sp[k]) != bool(sl[k]) for k in sp), **{f"revised_{k}": v for k, v in diff_inputs.items()}})
d = pd.DataFrame(rows)
(ROOT / "data" / "external").mkdir(exist_ok=True)
(ROOT / "output" / "results").mkdir(parents=True, exist_ok=True)
d.to_csv(ROOT / "data" / "external" / "sec_vintage_rows.csv", index=False)
n = len(d)
pb, lb = d.sec_pit_score.map(bucket), d.sec_latest_score.map(bucket)
hi = pb == "High"
L = ["# SEC vintage check, FY2015-2024 (aggregates only)\n",
     f"Sample: {len(samp)} random scored firm-years (seed {SEED}). No CIK on file: {nocik}; no SEC facts or no original 10-K found: {nofacts}; not scoreable from the mapped SEC tags (a needed input missing in either version): {noscore}. **Usable: {n}.** "
     "Scores use the paper's literal issuance rule and the same signal definitions as the backtest, but SEC XBRL tags, so levels differ from Compustat; the comparison PIT vs LATEST uses the same tags both ways and so isolates restatement.\n",
     "## Restatement effect: PIT (as filed by the original 10-K date) vs LATEST (current vintage)\n",
     f"- Score identical: {int((d.sec_pit_score == d.sec_latest_score).sum())} of {n} ({100 * (d.sec_pit_score == d.sec_latest_score).mean():.1f}%).",
     f"- Mean absolute score change: {(d.sec_pit_score - d.sec_latest_score).abs().mean():.3f}; max {int((d.sec_pit_score - d.sec_latest_score).abs().max())}.",
     f"- At least one signal flips: {int((d.signals_changed > 0).sum())} of {n} ({100 * (d.signals_changed > 0).mean():.1f}%).",
     f"- Bucket (High/Middle/Low) changes: {int((pb != lb).sum())} of {n} ({100 * (pb != lb).mean():.1f}%).",
     f"- PIT High that stay High in LATEST: {int(((pb == 'High') & (lb == 'High')).sum())} of {int(hi.sum())}" + (f" ({100 * ((pb == 'High') & (lb == 'High')).sum() / hi.sum():.1f}%)." if hi.sum() else "."),
     f"- LATEST High that were not High in PIT: {int(((lb == 'High') & (pb != 'High')).sum())} of {int((lb == 'High').sum())}. Of the {int((pb != lb).sum())} bucket changes, {int(((pb == 'Middle') & (lb != 'Middle')).sum() + ((pb != 'Middle') & (lb == 'Middle')).sum())} involve Middle and {int(((pb == 'High') & (lb == 'Low')).sum() + ((pb == 'Low') & (lb == 'High')).sum())} jump between High and Low.",
     "- Share of firm-years where the input was revised (any of the three years): " + ", ".join(f"{k} {100 * d[f'revised_{k}'].mean():.1f}%" for k in TAGS) + ".\n",
     "## Mapping check (informational): SEC-LATEST score vs the Compustat score in the backtest\n",
     f"- Identical: {int((d.sec_latest_score == d.compustat_score).sum())} of {n} ({100 * (d.sec_latest_score == d.compustat_score).mean():.1f}%); within one point: {100 * ((d.sec_latest_score - d.compustat_score).abs() <= 1).mean():.1f}%. "
     "Differences here come from tag choices and definitions (for example income before extraordinary items, current-portion debt), not restatement.\n",
     "## Limits\n",
     "A sample, not the full table; firms whose inputs the simple tag map cannot find are excluded, which tilts the sample toward standard filers. A 10-K filed in the SEC feed only from 2009. Sample uses the project's current-vintage scorable firm-years, so firms excluded for missing data are not represented. "
     "A restated value that appears only in a later 10-K comparative column is treated as filed on that later date, which is the point-in-time-correct reading.\n"]
(ROOT / "output" / "results" / "sec_vintage_check.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
