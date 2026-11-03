"""
Stage 04a: pull income before extraordinary items (ib) from comp.funda, same filters, companies and years as data/raw/comp_funda.parquet.

Output: data/raw/comp_funda_ib.parquet (gvkey, datadate, fyear, ib). Write-once: refuses to replace the file unless --overwrite is passed.
Log:    output/logs/pull_ib_log.md. No earlier raw file is changed.
Exit code is 1 if a check fails.
"""
import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output" / "logs"
RAW_FILE = RAW / "comp_funda_ib.parquet"


def wrds_username():
    """Username field of the saved pgpass entry. The file is read in memory, only the username is kept, and nothing is printed or stored."""
    if os.environ.get("PGUSER"):
        return os.environ["PGUSER"]
    for path in (Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf", Path.home() / ".pgpass"):
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("wrds-pgdata"):
                    return line.split(":")[3]
    raise RuntimeError("No WRDS username: set PGUSER or create pgpass.conf")


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
        coverage_log("ib", "pull_ib_log.md")
        return
    if RAW_FILE.exists() and not args.overwrite:
        sys.exit(f"REFUSED: {RAW_FILE.name} exists and is write-once. Pass --overwrite to replace it.")
    OUT.mkdir(parents=True, exist_ok=True)
    field = cfg.PIPELINE["profit_field"]
    base = pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey", "datadate", "fyear", "ni"])
    gv = sorted(base.gvkey.unique())

    db = wrds.Connection(wrds_username=wrds_username())
    have = set(db.describe_table("comp", "funda").name)
    need = ["gvkey", "datadate", "fyear", field] + list(cfg.FUNDA_FILTERS)
    if not set(need) <= have:
        sys.exit(f"comp.funda lacks {set(need) - have}")
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    keys = ", ".join(f"'{g}'" for g in gv)
    q = db.raw_sql(f'select gvkey, datadate, fyear, "{field}" from comp.funda where {filters} and gvkey in ({keys}) '
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
    ni, ib = both.ni.astype(float), both[field].astype(float)
    sha = hashlib.sha256(RAW_FILE.read_bytes()).hexdigest().upper()
    L = ["# Pull: income before extraordinary items (ib)\n", f"Run started {started} (UTC). File `data/raw/comp_funda_ib.parquet`, SHA-256 `{sha}`.\n",
         f"- Rows pulled {len(q)}; rows in comp_funda {len(base)}; keys only in old {only_old}; only in new {only_new}.",
         f"- Null ib {int(ib.isna().sum())}; null ni {int(ni.isna().sum())}; null in one but not the other {int((ib.isna() != ni.isna()).sum())}.",
         f"- ib equals ni (within 0.0005) on {int(((ib - ni).abs() <= 0.0005).sum())} rows; differs on {int(((ib - ni).abs() > 0.0005).sum())} rows.",
         f"- Check failures: {len(failures)}."] + [f"- FAIL: {x}" for x in failures]
    (OUT / "pull_ib_log.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"rows={len(q)} null_ib={int(ib.isna().sum())} differs_from_ni={int(((ib - ni).abs() > 0.0005).sum())} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
