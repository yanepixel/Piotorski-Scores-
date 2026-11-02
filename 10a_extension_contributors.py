"""Reporting only: separately written dollar-value rebuild of January-May 2026, and which names drive each bucket. Writes contributors_jan_may_2026.csv."""
import sys
from pathlib import Path

import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
HERE = ROOT / "output" / cfg.EXTENSION_2026["label"]

pd.set_option("display.width", 200, "display.max_columns", 30, "display.max_rows", 60, "display.max_colwidth", 34)
fm = pd.read_parquet(ROOT / "data/clean/formation.parquet")
h = fm[(fm.formation_date == fm.formation_date.max()) & fm.scored].copy()
h["bucket"] = "Middle"
h.loc[h.F_SCORE.isin(cfg.HIGH_SCORES), "bucket"] = "High"
h.loc[h.F_SCORE.isin(cfg.LOW_SCORES), "bucket"] = "Low"
r = pd.read_parquet(ROOT / "data/raw/crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret"])
r["ym"] = r.mthcaldt.dt.strftime("%Y-%m")
m = pd.read_csv(HERE / "security_map.csv", dtype={"gvkey": str, "iid": str})
s = pd.read_parquet(ROOT / "data/raw/comp_secm_extension.parquet", columns=["gvkey", "iid", "datadate", "trt1m"])
s["ym"] = s.datadate.dt.strftime("%Y-%m")
s = s.merge(m[["permno", "gvkey", "iid", "name"]], on=["gvkey", "iid"])
published = pd.read_csv(HERE / "returns.csv").set_index("month")
crsp_end = pd.Period(cfg.RETURNS_END, "M")
hold = [str(m) for m in pd.period_range(f"{cfg.LAST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", crsp_end, freq="M")]
ext = [str(m) for m in pd.period_range(crsp_end + 1, pd.Period(cfg.EXTENSION_2026["end"], "M"), freq="M")]
STOP = {name.upper(): month for name, month in cfg.EXTENSION_2026["exits"].items()}
names = m.set_index("permno").name
rows, check = [], {}
for b in ["High", "Middle", "Low", "Benchmark"]:
    g = h if b == "Benchmark" else h[h.bucket == b]
    dollars = {int(p): 1.0 for p in g.permno}
    last_crsp = r[r.permno.isin(dollars)].groupby("permno").ym.max()
    for y in hold:
        ret = r[(r.ym == y)].set_index("permno").mthret.astype(float)
        live = {p: v for p, v in dollars.items() if p in ret.index}
        pot = sum(dollars.values()) / sum(live.values())
        dollars = {p: v * pot * (1 + ret[p]) for p, v in live.items()}
    start = dollars.copy()
    begin_total = sum(start.values())
    contrib = {p: 0.0 for p in start}
    for y in ext:
        ret = s[s.ym == y].set_index("permno").trt1m.astype(float) / 100
        total = sum(dollars.values())
        keep = {}
        for p, v in dollars.items():
            nm = names[p].upper()
            over = any(k in nm and y > e for k, e in STOP.items())
            if p in ret.index and not over:
                keep[p] = v
        pot = total / sum(keep.values())
        new = {}
        for p, v in keep.items():
            nv = v * pot * (1 + ret[p])
            contrib[p] += (nv - v * pot) / begin_total
            new[p] = nv
        check[(b, y)] = sum(new.values()) / total - 1
        dollars = new
    if b != "Benchmark":
        for p, c in contrib.items():
            rows.append({"bucket": b, "name": names[p], "weight_at_dec_2025": start[p] / begin_total, "jan_may_return": (s[(s.permno == p) & s.ym.isin(ext)].trt1m.astype(float).div(100).add(1).prod() - 1), "contribution_points": 100 * c})
gaps = [abs(check[(b, y)] - published.loc[y, b]) for b in ["High", "Middle", "Low", "Benchmark"] for y in ext]
print("largest gap to returns.csv:", max(gaps))
t = pd.DataFrame(rows).sort_values(["bucket", "contribution_points"], ascending=[True, False])
t.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
t.to_csv(HERE / "contributors_jan_may_2026.csv", index=False)
for b in ["High", "Low"]:
    x = t[t.bucket == b]
    print(f"\n{b}: {len(x)} names; top 5 contributions sum {x.contribution_points.head(5).sum():.1f} of {x.contribution_points.sum():.1f} points; median name return {x.jan_may_return.median():.1%}; share of names up {(x.jan_may_return > 0).mean():.0%}")
    print(x.head(6)[["name", "weight_at_dec_2025", "jan_may_return", "contribution_points"]].round(3).to_string(index=False))
