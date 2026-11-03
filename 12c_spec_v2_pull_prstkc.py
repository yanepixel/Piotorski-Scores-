"""
spec_v2, step 1b: pull purchase of common and preferred stock (prstkc) from comp.funda, same filters, companies and years as data/raw/comp_funda.parquet.
Needed for the revised issuance rule (SPEC_V2 issuance_field: sstk net of prstkc).

Output: data/raw/comp_funda_prstkc.parquet (gvkey, datadate, fyear, prstkc). Write-once: refuses to replace the file unless --overwrite is passed.
Log:    output/spec_v2/pull_prstkc_log.md. Nothing in v1 or in the earlier raw files is read for writing or changed.
Exit code is 1 if a check fails.
"""
import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / cfg.SPEC_V2["output_dir"]
RAW_FILE = RAW / "comp_funda_prstkc.parquet"
FIELD = "prstkc"


def load_username():
    """Same username handling as 12a_spec_v2_pull.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pull_ib", ROOT / "12a_spec_v2_pull.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.wrds_username()


def coverage_log(field, log_name):
    """--log-only: add unique-company counts and date ranges to the existing log from the stored raw file. No WRDS connection; the raw file is only read."""
    q = pd.read_parquet(RAW_FILE)
    base = pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey", "datadate", "fyear"])
    path = OUT / log_name
    text = path.read_text(encoding="utf-8")
    marker = "## Coverage (added from the stored file)"
    if marker in text:
        text = text[:text.index(marker)].rstrip("\n") + "\n"
    sha = hashlib.sha256(RAW_FILE.read_bytes()).hexdigest().upper()
    add = [marker, "",
           f"- Stored file `{RAW_FILE.name}` read again; SHA-256 `{sha}`. This section was added later from the stored file, not at pull time.",
           f"- Rows {len(q)}; unique companies (GVKEY) {q.gvkey.nunique()} (comp_funda: {base.gvkey.nunique()}); fiscal years {int(q.fyear.min())} to {int(q.fyear.max())}; year-ends {pd.to_datetime(q.datadate).min().date()} to {pd.to_datetime(q.datadate).max().date()}.",
           f"- Non-null {field} on {int(q[field].notna().sum())} rows ({q.loc[q[field].notna(), 'gvkey'].nunique()} companies); null on {int(q[field].isna().sum())} rows. No rows were dropped by the pull."]
    path.write_text(text + "\n" + "\n".join(add) + "\n", encoding="utf-8")
    print("coverage section written to", path.name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true", help="Replace the raw file. Raw files are write-once without this.")
    ap.add_argument("--log-only", action="store_true", help="Do not pull: append unique-company counts and date ranges to the log from the stored raw file.")
    args = ap.parse_args()
    if args.log_only:
        coverage_log("prstkc", "pull_prstkc_log.md")
        return
    if RAW_FILE.exists() and not args.overwrite:
        sys.exit(f"REFUSED: {RAW_FILE.name} exists and is write-once. Pass --overwrite to replace it.")
    OUT.mkdir(parents=True, exist_ok=True)
    base = pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey", "datadate", "fyear", "sstk"])
    gv = sorted(base.gvkey.unique())

    db = wrds.Connection(wrds_username=load_username())
    have = set(db.describe_table("comp", "funda").name)
    need = ["gvkey", "datadate", "fyear", FIELD] + list(cfg.FUNDA_FILTERS)
    if not set(need) <= have:
        sys.exit(f"comp.funda lacks {set(need) - have}")
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    keys = ", ".join(f"'{g}'" for g in gv)
    q = db.raw_sql(f'select gvkey, datadate, fyear, "{FIELD}" from comp.funda where {filters} and gvkey in ({keys}) '
                   f"and fyear between {cfg.FIRST_FUNDAMENTAL_FY} and {cfg.LAST_FUNDAMENTAL_FY}", date_cols=["datadate"])
    db.close()
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    failures = []
    if q.duplicated(["gvkey", "datadate"]).any() or q.duplicated(["gvkey", "fyear"]).any():
        failures.append("Duplicate rows in the new pull")
    k0 = base[["gvkey", "datadate", "fyear"]].assign(a=1)
    k1 = q[["gvkey", "datadate", "fyear"]].assign(b=1)
    m = k0.merge(k1, on=["gvkey", "datadate", "fyear"], how="outer")
    only_old, only_new = int(m.b.isna().sum()), int(m.a.isna().sum())
    if only_old or only_new:
        failures.append(f"Keys differ from comp_funda: {only_old} only in the old pull, {only_new} only in the new")
    q.to_parquet(RAW_FILE, index=False)

    both = base.merge(q, on=["gvkey", "datadate", "fyear"], how="inner")
    sstk, pr = both.sstk.astype(float), both[FIELD].astype(float)
    net = sstk.fillna(0) - pr.fillna(0)
    sha = hashlib.sha256(RAW_FILE.read_bytes()).hexdigest().upper()
    L = ["# spec_v2 pull: purchase of common and preferred stock (prstkc)\n", f"Run started {started} (UTC). File `data/raw/comp_funda_prstkc.parquet`, SHA-256 `{sha}`.\n",
         f"- Rows pulled {len(q)}; rows in comp_funda {len(base)}; keys only in old {only_old}; only in new {only_new}.",
         f"- Null prstkc {int(pr.isna().sum())} ({100 * pr.isna().mean():.1f}%); null sstk {int(sstk.isna().sum())}; negative prstkc {int((pr < 0).sum())}; negative sstk {int((sstk < 0).sum())}.",
         f"- prstkc positive {int((pr > 0).sum())}; zero {int((pr == 0).sum())}.",
         f"- sstk - prstkc (nulls as 0) is positive on {int((net > 0).sum())} rows ({100 * (net > 0).mean():.1f}%), zero on {int((net == 0).sum())}, negative on {int((net < 0).sum())}.",
         f"- Check failures: {len(failures)}."] + [f"- FAIL: {x}" for x in failures]
    (OUT / "pull_prstkc_log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"rows={len(q)} null_prstkc={int(pr.isna().sum())} net_positive={int((net > 0).sum())} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
