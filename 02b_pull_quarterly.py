"""
Stage 02b: pull the quarterly Compustat inputs of the profitability-screen variant: comp.fundq and the 10-Q/10-K filing dates from comp.co_filedate.
Raw:    data/raw/comp_fundq.parquet, comp_co_filedate_quarterly.parquet. Write-once: refuses to replace them unless --overwrite is passed.
Log:    output/logs/pull_log_quarterly.csv
Usage:  python 02b_pull_quarterly.py
"""
import argparse
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output" / "logs"
spec = importlib.util.spec_from_file_location("pull_ib", ROOT / "04a_pull_ib.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true", help="Replace the quarterly raw files. Raw files are write-once without this.")
    overwrite = ap.parse_args().overwrite
    fundq, filed = RAW / "comp_fundq.parquet", RAW / "comp_co_filedate_quarterly.parquet"
    if (fundq.exists() or filed.exists()) and not overwrite:
        sys.exit("REFUSED: the quarterly raw files exist and are write-once. Pass --overwrite to replace them.")
    db = wrds.Connection(wrds_username=mod.wrds_username())
    gv = sorted(pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey"]).gvkey.unique())
    keys = ", ".join(f"'{g}'" for g in gv)
    have = set(db.describe_table("comp", "fundq").name)
    need = cfg.QTR_PULL_FIELDS + list(cfg.FUNDA_FILTERS)
    if not set(need) <= have:
        raise RuntimeError(f"comp.fundq lacks {set(need) - have}")
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    start = f"{cfg.FIRST_FUNDAMENTAL_FY}-01-01"
    q = db.raw_sql(f"select {', '.join(cfg.QTR_PULL_FIELDS)} from comp.fundq where {filters} and gvkey in ({keys}) and datadate >= '{start}'", date_cols=["datadate"])
    new_types = [t for t in cfg.QTR_FILING_SRCTYPES if t not in cfg.FILING_SRCTYPES]
    types = ", ".join(f"'{t}'" for t in new_types)
    f = db.raw_sql(f"select {', '.join(cfg.QTR_FILING_PULL_FIELDS)} from comp.co_filedate where srctype in ({types}) and gvkey in ({keys}) and datadate >= '{start}'", date_cols=["datadate", "filedate"])
    q.to_parquet(fundq, index=False)
    f.to_parquet(filed, index=False)
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log = pd.DataFrame([{"table": "comp_fundq", "pull_timestamp_utc": now, "rows": len(q), "unique_ids": q.gvkey.nunique(), "date_min": q.datadate.min().date(), "date_max": q.datadate.max().date()},
                        {"table": "comp_co_filedate_quarterly", "pull_timestamp_utc": now, "rows": len(f), "unique_ids": f.gvkey.nunique(), "date_min": f.filedate.min().date(), "date_max": f.filedate.max().date()}])
    log.to_csv(OUT / "pull_log_quarterly.csv", index=False)
    db.close()
    print(f"pulled {len(q)} quarter rows and {len(f)} filing rows")


if __name__ == "__main__":
    main()
