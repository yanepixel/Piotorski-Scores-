"""
Stage 04c: pull EVERY Compustat annual input of a score in ONE query with ONE timestamp, so numerator and denominator come from the same vintage (the earlier ib and prstkc pulls ran separately).
Output: data/raw/comp_funda_single.parquet (all inputs below plus a pull stamp column). Write-once: refuses to replace the file unless --overwrite is passed.
Log:    output/logs/single_pull_log.md, comparing the single pull with the separate earlier pulls column by column (read only).
Usage:  python 04c_pull_single_vintage.py
"""
import argparse
import hashlib
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "comp_funda_single.parquet"
COLS = ["gvkey", "datadate", "fyear", "fyr", "ni", "ib", "at", "oancf", "dltt", "act", "lct", "sale", "cogs", "csho", "ajex", "sstk", "prstkc", "ceq", "txditc", "pstk", "prcc_f", "curcd", "che", "lt"]

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--overwrite", action="store_true")
a = ap.parse_args()
if OUT.exists() and not a.overwrite:
    sys.exit(f"REFUSED: {OUT.name} exists and is write-once. Pass --overwrite to replace it.")
spec = importlib.util.spec_from_file_location("pull_ib", ROOT / "04a_pull_ib.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
base = pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey", "datadate", "fyear"])
gv = sorted(base.gvkey.unique())
db = wrds.Connection(wrds_username=mod.wrds_username())
have = set(db.describe_table("comp", "funda").name)
missing = set(COLS) - have
if missing:
    sys.exit(f"comp.funda lacks {missing}")
filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
keys = ", ".join(f"'{g}'" for g in gv)
stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
q = db.raw_sql(f'select {", ".join(chr(34) + c + chr(34) for c in COLS)} from comp.funda where {filters} and gvkey in ({keys}) '
               f"and fyear between {cfg.FIRST_FUNDAMENTAL_FY} and {cfg.LAST_FUNDAMENTAL_FY}", date_cols=["datadate"])
db.close()
q["pull_stamp_utc"] = stamp
q.to_parquet(OUT, index=False)
sha = hashlib.sha256(OUT.read_bytes()).hexdigest().upper()

L = ["# Single-vintage pull of Compustat annual inputs\n", f"One query, one stamp {stamp} (UTC). `data/raw/comp_funda_single.parquet`, {len(q)} rows, SHA-256 `{sha}`.\n"]
sources = {"comp_funda.parquet": [c for c in COLS if c not in ("ib", "prstkc", "che", "lt")], "comp_funda_ib.parquet": ["ib"], "comp_funda_prstkc.parquet": ["prstkc"]}
fails = 0
for fn, cols in sources.items():
    old = pd.read_parquet(RAW / fn)
    keycols = ["gvkey", "datadate", "fyear"]
    m = q.merge(old, on=keycols, how="outer", suffixes=("", "_old"), indicator=True)
    only = int((m._merge != "both").sum())
    L.append(f"- vs `{fn}`: rows {len(old)}; key mismatches {only}.")
    for c in cols:
        if c not in old.columns:
            continue
        both = m[m._merge == "both"]
        x, y = both[c], both[c + "_old"] if c + "_old" in both.columns else None
        if y is None:
            continue
        try:
            xf, yf = pd.to_numeric(x), pd.to_numeric(y)
            diff = ~((xf == yf) | (xf.isna() & yf.isna()))
        except Exception:
            diff = ~((x == y) | (x.isna() & y.isna()))
        L.append(f"  - {c}: {int(diff.sum())} rows differ")
        fails += int(diff.sum())
L.append(f"\nTotal differing cells against the separate pulls: {fails}. A non-zero count would mean the earlier separate pulls came from different vintages.")
(ROOT / "output" / "logs").mkdir(parents=True, exist_ok=True)
(ROOT / "output" / "logs" / "single_pull_log.md").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
