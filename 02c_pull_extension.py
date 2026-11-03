"""
Stage 02c: pull comp.secm monthly security rows for the 2025 list's gvkeys and the two index funds, Jan 2025 to Jun 2026 (config.EXTENSION_PULL), the return source for the
extension after CRSP ends (18_extension.py). secstat is pulled for reporting only, never used as a filter.
Raw:    data/raw/comp_secm_extension.parquet. Write-once: refuses to replace the file unless --overwrite is passed.
Usage:  python 02c_pull_extension.py
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW_FILE = ROOT / "data" / "raw" / "comp_secm_extension.parquet"
FIELDS = cfg.EXTENSION_PULL["fields"]
PULL_START, PULL_END = cfg.EXTENSION_PULL["start"], cfg.EXTENSION_PULL["end"]
BENCHMARK_CUSIPS = cfg.EXTENSION_PULL["benchmark_cusips"]
spec = importlib.util.spec_from_file_location("pull_ib", ROOT / "04a_pull_ib.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true", help="Replace the extension raw file. Raw files are write-once without this.")
    args = ap.parse_args()
    if RAW_FILE.exists() and not args.overwrite:
        sys.exit(f"REFUSED: {RAW_FILE.name} exists and is write-once. Pass --overwrite to replace it.")
    u = pd.read_parquet(ROOT / "data/clean/universe.parquet")
    last = u.formation_date.max()
    list_rows = u[u.formation_date == last]
    db = wrds.Connection(wrds_username=mod.wrds_username())
    have = set(db.describe_table("comp", "secm").name)
    missing = [f for f in FIELDS if f not in have]
    if missing:
        sys.exit(f"comp.secm lacks {missing}")
    gv = sorted(list_rows.gvkey.dropna().unique())
    keys = ", ".join(f"'{g}'" for g in gv)
    cus = " or ".join(f"cusip like '{c}%%'" for c, _ in BENCHMARK_CUSIPS.values())
    fields = ", ".join(FIELDS)
    s = db.raw_sql(f"select {fields} from comp.secm where (gvkey in ({keys}) or {cus}) and datadate between '{PULL_START}' and '{PULL_END}'", date_cols=["datadate"])
    db.close()
    s = s.sort_values(["gvkey", "iid", "datadate"]).reset_index(drop=True)
    s.to_parquet(RAW_FILE, index=False)
    print(f"{len(s)} rows, {s.gvkey.nunique()} gvkeys, {s.datadate.min().date()} to {s.datadate.max().date()}")


if __name__ == "__main__":
    main()
