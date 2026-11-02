"""
Phase 1b: pull raw data for every company in the 21 universe lists (CLAUDE.md sections 5, 8 and 9).

Output: data/raw/*.parquet, one file per table. Raw files are write-once.
Logs:   output/logs/pull_log.csv (one row per table per run), pull_checks.md, pull_raw_hashes.csv, pull_runs.csv
The logs reflect config.py at pull time.
Refuses to overwrite an existing raw file unless --overwrite is passed.
Exit code is 1 if any check fails.
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
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"

OUTPUTS = ["comp_funda", "comp_co_filedate", "comp_co_hgic", "crsp_ccmxpf_lnkhist", "crsp_msf_v2", "crsp_benchmarks", "ff_factors"]


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


def sql_list(values):
    return ", ".join(f"'{v}'" for v in values)


def sql_ints(values):
    return ", ".join(str(int(v)) for v in values)


def check_columns(db, lib, table, fields):
    """Stop before querying if a requested column is not in the table."""
    have = set(db.describe_table(lib, table).name)
    missing = [f for f in fields if f not in have]
    if missing:
        raise RuntimeError(f"{lib}.{table} has no column(s) {missing}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Replace existing files in data/raw. Raw files are write-once without this.")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    existing = [n for n in OUTPUTS if (RAW / f"{n}.parquet").exists()]
    if existing and not args.overwrite:
        with open(LOGS / "pull_runs.csv", "a", encoding="utf-8") as f:
            f.write(f"{started},refused,existing raw files: {' '.join(existing)}\n")
        sys.exit(f"REFUSED: raw files already exist and are write-once: {existing}. Pass --overwrite to replace them.")

    # --- Master ID list: all rows of all 21 lists ---
    u = pd.read_parquet(CLEAN / "universe.parquet")
    gvkeys = sorted(u.gvkey.dropna().unique())
    null_gvkey = u[u.gvkey.isna()]
    included_gvkeys = u[u.included].gvkey.nunique()
    held = set(int(p) for p in u.permno)

    db = wrds.Connection(wrds_username=wrds_username())
    pull_time = {}
    tables = {}
    failures = []
    L = [f"# Phase 1b pull checks: {cfg.UNIVERSE_LABEL}\n", f"Run started {started} (UTC).\n"]

    def pull(name, sql, date_cols):
        tables[name] = db.raw_sql(sql, date_cols=date_cols)
        pull_time[name] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return tables[name]

    gv = sql_list(gvkeys)

    # --- Compustat ---
    check_columns(db, "comp", "funda", cfg.FUNDA_FIELDS + list(cfg.FUNDA_FILTERS))
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    # "at" is a reserved word in Postgres
    fields = ", ".join(f'"{f}"' for f in cfg.FUNDA_FIELDS)
    funda = pull("comp_funda", f"""
        select {fields} from comp.funda
        where {filters} and gvkey in ({gv}) and fyear between {cfg.FIRST_FUNDAMENTAL_FY} and {cfg.LAST_FUNDAMENTAL_FY}
    """, ["datadate"])

    check_columns(db, "comp", "co_filedate", ["gvkey", "consol", "popsrc", "srctype", "filedatetime", "datadate", "filedate"])
    filings = pull("comp_co_filedate", f"""
        select gvkey, consol, popsrc, srctype, filedatetime, datadate, filedate from comp.co_filedate
        where srctype in ({sql_list(cfg.FILING_SRCTYPES)}) and gvkey in ({gv})
    """, ["datadate", "filedate"])

    check_columns(db, "comp", "co_hgic", ["gvkey", "indtype", "ggroup", "gind", "gsector", "gsubind", "indfrom", "indthru"])
    hgic = pull("comp_co_hgic", f"""
        select gvkey, indtype, gsector, ggroup, gind, gsubind, indfrom, indthru from comp.co_hgic where gvkey in ({gv})
    """, ["indfrom", "indthru"])

    # --- Every PERMNO linked to these gvkeys, on any link type, plus every held PERMNO ---
    check_columns(db, "crsp", "ccmxpf_lnkhist", ["gvkey", "linkprim", "liid", "linktype", "lpermno", "lpermco", "linkdt", "linkenddt"])
    links = pull("crsp_ccmxpf_lnkhist", f"""
        select gvkey, linkprim, liid, linktype, lpermno, lpermco, linkdt, linkenddt from crsp.ccmxpf_lnkhist
        where gvkey in ({gv}) and lpermno is not null
    """, ["linkdt", "linkenddt"])
    linked = set(int(p) for p in links.lpermno)
    permnos = sorted(linked | held)

    # --- CRSP monthly, through the latest date in the table ---
    check_columns(db, "crsp", "msf_v2", cfg.MSF_FIELDS)
    msf_fields = ", ".join(cfg.MSF_FIELDS)
    msf = pull("crsp_msf_v2", f"""
        select {msf_fields} from crsp.msf_v2
        where permno in ({sql_ints(permnos)}) and mthcaldt >= '{cfg.RETURNS_START}'
    """, ["mthcaldt", "mthprcdt"])

    # --- Benchmarks, by fixed identifier, then proved to be the right fund on every row ---
    bench_permnos = {p: t for t, ps in cfg.BENCHMARK_PERMNOS.items() for p in ps}
    bench = pull("crsp_benchmarks", f"""
        select {msf_fields} from crsp.msf_v2
        where permno in ({sql_ints(bench_permnos)}) and mthcaldt >= '{cfg.RETURNS_START}'
    """, ["mthcaldt", "mthprcdt"])
    bench_bad = bench[(bench.ticker != bench.permno.map(bench_permnos))
                      | (bench.securitytype != cfg.BENCHMARK_SECURITY_TYPE)
                      | (bench.securitysubtype != cfg.BENCHMARK_SECURITY_SUBTYPE)]
    if len(bench_bad):
        failures.append(f"{len(bench_bad)} benchmark rows are not the expected fund")
    if set(cfg.BENCHMARK_PERMNOS) != set(cfg.BENCHMARK_TICKERS):
        failures.append("BENCHMARK_PERMNOS and BENCHMARK_TICKERS name different funds")

    # --- Factors: everything from the five-factor table except UMD; merged on month ---
    check_columns(db, "ff", "fivefactors_monthly", cfg.FF5_FIELDS)
    check_columns(db, "ff", "factors_monthly", cfg.UMD_FIELDS)
    ff5 = db.raw_sql(f"select {', '.join(cfg.FF5_FIELDS)} from ff.fivefactors_monthly", date_cols=["date", "dateff"])
    umd = db.raw_sql(f"select {', '.join(cfg.UMD_FIELDS)} from ff.factors_monthly", date_cols=["date"])
    ff5["month"] = ff5.date.dt.to_period("M").astype(str)
    umd["month"] = umd.date.dt.to_period("M").astype(str)
    ff = ff5.merge(umd.drop(columns="date"), on="month", how="left", validate="1:1")
    tables["ff_factors"] = ff
    pull_time["ff_factors"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # Latest source dates, read from the tables themselves
    msf_table_latest = pd.Timestamp(db.raw_sql("select max(mthcaldt) mx from crsp.msf_v2").mx.iloc[0])
    db.close()

    # --- Write, write-once unless --overwrite ---
    ids = {"comp_funda": ("gvkey", "datadate"), "comp_co_filedate": ("gvkey", "filedate"), "comp_co_hgic": ("gvkey", "indfrom"),
           "crsp_ccmxpf_lnkhist": ("lpermno", "linkdt"), "crsp_msf_v2": ("permno", "mthcaldt"), "crsp_benchmarks": ("permno", "mthcaldt"), "ff_factors": ("month", "date")}
    rows, hashes = [], []
    for name in OUTPUTS:
        df = tables[name]
        path = RAW / f"{name}.parquet"
        df.to_parquet(path, index=False)
        id_col, date_col = ids[name]
        rows.append({"table": name, "pull_timestamp_utc": pull_time[name], "rows": len(df), "unique_ids": df[id_col].nunique(), "id_column": id_col,
                     "date_column": date_col, "date_min": df[date_col].min().date(), "date_max": df[date_col].max().date()})
        hashes.append({"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    log = pd.DataFrame(rows)
    log_path = LOGS / "pull_log.csv"
    log.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
    hash_df = pd.DataFrame(hashes)
    hash_df.to_csv(LOGS / "pull_raw_hashes.csv", index=False)

    # --- Checks ---
    # Master list coverage
    no_funda = sorted(set(gvkeys) - set(funda.gvkey))
    no_hgic = sorted(set(gvkeys) - set(hgic.gvkey))
    no_filing = sorted(set(gvkeys) - set(filings.gvkey))
    no_msf = sorted(set(permnos) - set(int(p) for p in msf.permno))
    held_no_msf = sorted(held - set(int(p) for p in msf.permno))
    if no_funda:
        failures.append(f"{len(no_funda)} gvkeys have no comp.funda rows")
    if no_hgic:
        failures.append(f"{len(no_hgic)} gvkeys have no comp.co_hgic rows")
    if held_no_msf:
        failures.append(f"{len(held_no_msf)} held PERMNOs have no crsp.msf_v2 rows")
    dup_funda = int(funda.duplicated(["gvkey", "datadate"]).sum())
    if dup_funda:
        failures.append(f"{dup_funda} duplicate gvkey-datadate rows in comp.funda")
    bad_src = sorted(set(filings.srctype) - set(cfg.FILING_SRCTYPES))
    if bad_src:
        failures.append(f"Unexpected filing types: {bad_src}")
    dup_msf = int(msf.duplicated(["permno", "mthcaldt"]).sum())
    if dup_msf:
        failures.append(f"{dup_msf} duplicate permno-month rows in crsp.msf_v2")
    if msf.mthcaldt.max() != msf_table_latest:
        failures.append(f"Pulled returns end {msf.mthcaldt.max().date()}, table ends {msf_table_latest.date()}")

    # Every held security has a row on its formation date, and carries through to delisting or the table end
    keyed = u[["formation_date", "permno"]].merge(msf[["permno", "mthcaldt"]], left_on=["formation_date", "permno"], right_on=["mthcaldt", "permno"], how="left")
    held_no_row = int(keyed.mthcaldt.isna().sum())
    if held_no_row:
        failures.append(f"{held_no_row} held company-dates have no return row on the formation date")
    span = msf.groupby("permno").mthcaldt.max().rename("last_row").reset_index()
    last_flag = msf.sort_values("mthcaldt").groupby("permno").mthdelflg.last().rename("last_flag").reset_index()
    span = span[span.permno.isin(held)].merge(last_flag, on="permno")
    ended_no_flag = span[(span.last_row < msf_table_latest) & (span.last_flag == cfg.ACTIVE_DELISTING_FLAG)]
    if len(ended_no_flag):
        failures.append(f"{len(ended_no_flag)} held PERMNOs stop before the table end with no delisting flag")

    # Factors: same coverage, no gaps
    start = pd.Timestamp(cfg.RETURNS_START)
    ff5_w, umd_w = ff5[ff5.date >= start], umd[umd.date >= start]
    months_expected = pd.period_range(start, max(ff5.date.max(), umd.date.max()), freq="M").astype(str)
    gap5 = sorted(set(months_expected) - set(ff5_w.month))
    gapu = sorted(set(months_expected) - set(umd_w.month))
    if set(ff5_w.month) != set(umd_w.month):
        failures.append("Factor tables cover different months since RETURNS_START")
    if gap5 or gapu:
        failures.append(f"Missing factor months: five-factor {gap5}, UMD {gapu}")
    ff_w = ff[ff.date >= start]
    ff_nulls = ff_w.isna().sum()
    ff_nulls = ff_nulls[ff_nulls > 0]
    if len(ff_nulls):
        failures.append(f"Null factor values since RETURNS_START: {ff_nulls.to_dict()}")

    # --- Report ---
    required_end = (pd.Timestamp(cfg.SUBPERIODS[-1][1] + "-01") + pd.offsets.MonthEnd(0))
    L.append("## Result\n")
    L.append(f"**{len(failures)} check failure(s).**\n")
    L += [f"- FAIL: {f}" for f in failures]
    L.append("")
    L.append("## Pull log\n")
    L.append(md_table(log))
    L.append("\n## Raw file hashes (SHA-256)\n")
    L.append(md_table(hash_df))
    L.append("\n## Master ID list (all rows of all 21 lists)\n")
    L.append(f"- GVKEYs, all rows: {len(gvkeys)}. Included rows only: {included_gvkeys}.")
    L.append(f"- Rows with no GVKEY, so not in Compustat pulls: {len(null_gvkey)} company-dates, PERMNOs {sorted(int(p) for p in null_gvkey.permno.unique())}. They are in the returns pull.")
    L.append(f"- PERMNOs: {len(linked)} linked on any link type, {len(held)} held, {len(permnos)} in the union; {len(held - linked)} held with no link row: {sorted(held - linked)}.")
    L.append(f"- GVKEYs with no funda rows: {no_funda or 'none'}. No co_hgic rows: {no_hgic or 'none'}.")
    L.append(f"- GVKEYs with no {cfg.FILING_SRCTYPES} filing at any date: {len(no_filing)}: {no_filing or 'none'}.")
    L.append(f"- Linked PERMNOs with no msf_v2 row since {cfg.RETURNS_START} (linked outside the period, not held): {len(no_msf)}. Held with no row: {len(held_no_msf)}.\n")
    L.append("\n## Returns coverage\n")
    L.append(f"- `crsp.msf_v2` latest month in the table: **{msf_table_latest.date()}**. Pulled through: {msf.mthcaldt.max().date()}.")
    L.append(f"- Last subperiod in config at pull time ends {required_end.date()}: **{'covered' if msf_table_latest >= required_end else 'NOT covered'}**. Reported, not trimmed; this does not fail the pull.")
    L.append(f"- Held company-dates with no row on the formation date: {held_no_row}. Held PERMNOs ending before the table end with no delisting flag: {len(ended_no_flag)}.\n")
    if len(ended_no_flag):
        L.append(md_table(ended_no_flag))
    L.append("\n## Benchmarks\n")
    b = bench.groupby(["permno", "ticker", "issuernm", "cusip", "securitytype", "securitysubtype"]).mthcaldt.agg(["min", "max", "size"]).reset_index()
    b["min"], b["max"] = b["min"].dt.date, b["max"].dt.date
    L.append(md_table(b))
    L.append(f"\nRows that are not the expected fund: {len(bench_bad)}.")
    dbl = bench.assign(t=bench.permno.map(bench_permnos))
    dbl = dbl[dbl.duplicated(["t", "mthcaldt"], keep=False)]
    L.append(f"Months where one fund has two rows (kept raw; Phase 5 must chain them): {sorted(set(d.date().isoformat() for d in dbl.mthcaldt))}.\n")
    L.append("\n## Factors\n")
    L.append(f"- Five-factor table: {ff5.date.min().date()} to {ff5.date.max().date()}. `factors_monthly`: {umd.date.min().date()} to {umd.date.max().date()}.")
    L.append(f"- Months since {cfg.RETURNS_START}: five-factor {len(ff5_w)}, UMD {len(umd_w)}, merged {len(ff_w)}. Same months: {set(ff5_w.month) == set(umd_w.month)}. Gaps: {len(gap5) + len(gapu)}. Nulls: {int(ff_nulls.sum())}.")
    L.append(f"- Latest month reaches {required_end.date()}: five-factor {ff5.date.max() >= required_end.replace(day=1)}, UMD {umd.date.max() >= required_end.replace(day=1)}.\n")
    L.append("\n## Compustat notes\n")
    cur = funda.curcd.value_counts(dropna=False).rename_axis("curcd").reset_index(name="rows")
    L.append(md_table(cur))
    nonusd = funda[funda.curcd != "USD"].groupby(["gvkey", "curcd"]).agg(rows=("fyear", "size"), first_fy=("fyear", "min"), last_fy=("fyear", "max")).reset_index()
    L.append("\nNon-USD reporters, for Phase 2:\n")
    L.append(md_table(nonusd))
    L.append(f"\nFiling rows by `srctype`: {filings.srctype.value_counts().to_dict()}. Filing `consol`/`popsrc`: {filings.groupby(['consol', 'popsrc']).size().to_dict()}.\n")
    (LOGS / "pull_checks.md").write_text("\n".join(L), encoding="utf-8")

    status = "failed_checks" if failures else "ok"
    with open(LOGS / "pull_runs.csv", "a", encoding="utf-8") as f:
        f.write(f"{started},{status},overwrite={args.overwrite} tables={len(OUTPUTS)} failures={len(failures)}\n")

    print(log.to_string(index=False))
    print(hash_df.to_string(index=False))
    print(f"failures={len(failures)} msf_latest={msf_table_latest.date()}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
