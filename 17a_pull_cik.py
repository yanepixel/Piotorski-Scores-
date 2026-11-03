"""
Stage 17a, SEC vintage check step 1: pull the SEC CIK for each project company from comp.company (read-only), so a sample of firm-years can be matched to SEC filings.
Output: data/raw/comp_company_cik.parquet (gvkey, cik). Write-once: refuses to replace the file unless --overwrite is passed.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import wrds

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "comp_company_cik.parquet"

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--overwrite", action="store_true")
if OUT.exists() and not ap.parse_args().overwrite:
    sys.exit(f"REFUSED: {OUT.name} exists and is write-once. Pass --overwrite to replace it.")
spec = importlib.util.spec_from_file_location("pull_ib", ROOT / "04a_pull_ib.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
gv = sorted(pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey"]).gvkey.unique())
db = wrds.Connection(wrds_username=mod.wrds_username())
keys = ", ".join(f"'{g}'" for g in gv)
q = db.raw_sql(f"select gvkey, cik from comp.company where gvkey in ({keys})")
db.close()
q.to_parquet(OUT, index=False)
print(f"gvkeys {len(gv)}, rows {len(q)}, with cik {int(q.cik.notna().sum())}")
