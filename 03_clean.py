"""
Phase 2: clean annual fundamentals (CLAUDE.md sections 5, 8 and 9).

Reads:  data/raw/comp_funda.parquet, data/raw/comp_co_filedate.parquet. No return data is read.
Output: data/clean/fundamentals_clean.parquet (USD millions as reported; CAD rows are reported, not converted)
Logs:   output/logs/clean_checks.md, clean_stub_years.csv, clean_outliers.csv, clean_late_filings.csv, clean_non_usd.csv
Nothing is dropped except a failure on duplicate rows. Exit code is 1 if a check fails.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"

NUMERIC = ["ni", "at", "oancf", "dltt", "act", "lct", "sale", "cogs", "csho", "ajex", "sstk", "ceq", "txditc", "pstk", "prcc_f"]
OUTLIER_FIELDS = ["at", "sale", "adj_shares"]


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


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    failures = []

    f = pd.read_parquet(RAW / "comp_funda.parquet")
    filings = pd.read_parquet(RAW / "comp_co_filedate.parquet")
    f[NUMERIC] = f[NUMERIC].astype(float)
    f["fyear"] = f.fyear.astype(int)
    f["fyr"] = f.fyr.astype(int)
    raw_rows = len(f)

    # Compustat names, for logs only
    db = wrds.Connection(wrds_username=wrds_username())
    keys = ", ".join(f"'{g}'" for g in f.gvkey.unique())
    names = db.raw_sql(f"select gvkey, conm from comp.company where gvkey in ({keys})").set_index("gvkey").conm
    db.close()
    f["conm"] = f.gvkey.map(names)

    # --- One row per gvkey-fiscal year. The filtered table has no amendment marker, so a duplicate is a failure, and a duplicate year-end also halts the merge below. ---
    dup_fy = int(f.duplicated(["gvkey", "fyear"]).sum())
    dup_date = int(f.duplicated(["gvkey", "datadate"]).sum())
    if dup_fy or dup_date:
        failures.append(f"Duplicate rows: {dup_fy} gvkey-fyear, {dup_date} gvkey-datadate")
    f = f.sort_values(["gvkey", "fyear"]).reset_index(drop=True)

    # --- Fiscal-year changes and stub years ---
    g = f.groupby("gvkey")
    f["days_since_prior"] = (f.datadate - g.datadate.shift(1)).dt.days
    f["fy_gap"] = f.fyear - g.fyear.shift(1)
    f["fyr_changed"] = g.fyr.shift(1).notna() & (f.fyr != g.fyr.shift(1))
    f["stub_flag"] = f.days_since_prior.notna() & ~f.days_since_prior.between(cfg.STUB_MIN_DAYS, cfg.STUB_MAX_DAYS)

    # --- Availability date: earliest valid 10-K date, else year-end plus the fallback lag ---
    filings = filings[filings.srctype.isin(cfg.FILING_SRCTYPES)]
    on_or_before = filings[filings.filedate <= filings.datadate]
    valid = filings[filings.filedate > filings.datadate]
    first = valid.groupby(["gvkey", "datadate"]).filedate.min().rename("filing_date").reset_index()
    f = f.merge(first, on=["gvkey", "datadate"], how="left", validate="1:1")
    use_filed = f.filing_date.notna() & cfg.USE_ACTUAL_FILING_DATE
    f["avail_date"] = (f.datadate + pd.to_timedelta(cfg.FALLBACK_LAG_DAYS, unit="D")).where(~use_filed, f.filing_date)
    f["avail_source"] = "fallback"
    f.loc[use_filed, "avail_source"] = "filing"
    f["filing_lag_days"] = (f.filing_date - f.datadate).dt.days

    # --- Sanity flags, never drops ---
    f["adj_shares"] = f.csho * f.ajex
    f["neg_assets"] = f["at"] < 0
    f["neg_sale"] = f.sale < 0
    f["non_usd"] = f.curcd != "USD"
    prior = f.groupby("gvkey")
    for c in OUTLIER_FIELDS:
        p = prior[c].shift(1)
        both_positive = (f[c] > 0) & (p > 0) & (f.fy_gap == 1)
        ratio = (f[c] / p).where(both_positive)
        f[f"{c}_yoy_ratio"] = ratio
        f[f"outlier_{c}"] = (ratio > cfg.OUTLIER_YOY_RATIO) | (ratio < 1 / cfg.OUTLIER_YOY_RATIO)
    f["outlier_flag"] = f[[f"outlier_{c}" for c in OUTLIER_FIELDS]].any(axis=1)

    f.to_parquet(CLEAN / "fundamentals_clean.parquet", index=False)

    # --- Logs ---
    in_range = f.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY)
    has_assets = f["at"].notna()
    short_lag, long_lag = cfg.FILING_LATE_LOG_DAYS
    late = f[f.filing_lag_days > short_lag].sort_values("filing_lag_days", ascending=False)
    late[["gvkey", "conm", "fyear", "datadate", "filing_date", "filing_lag_days"]].to_csv(LOGS / "clean_late_filings.csv", index=False)
    stubs = f[f.stub_flag]
    stubs[["gvkey", "conm", "fyear", "datadate", "fyr", "days_since_prior", "fyr_changed"]].to_csv(LOGS / "clean_stub_years.csv", index=False)
    outliers = f[f.outlier_flag]
    outliers[["gvkey", "conm", "fyear", "datadate", "at", "sale", "csho", "ajex", "at_yoy_ratio", "sale_yoy_ratio", "adj_shares_yoy_ratio",
              "outlier_at", "outlier_sale", "outlier_adj_shares"]].to_csv(LOGS / "clean_outliers.csv", index=False)
    non_usd = f[f.non_usd]
    non_usd[["gvkey", "conm", "fyear", "datadate", "curcd", "at", "sale"]].to_csv(LOGS / "clean_non_usd.csv", index=False)
    if not (f.stub_flag & ~f.fyr_changed).sum() == 0:
        failures.append("A flagged year has no fiscal-year-end change: review clean_stub_years.csv")

    L = [f"# Phase 2 checks: {cfg.UNIVERSE_LABEL}\n", "## Result\n", f"**{len(failures)} check failure(s).**\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Rows\n")
    L.append(f"- Raw {raw_rows}, clean {len(f)}, dropped {raw_rows - len(f)}. Companies {f.gvkey.nunique()}. Fiscal years {f.fyear.min()}-{f.fyear.max()}. Year-ends {f.datadate.min().date()} to {f.datadate.max().date()}.")
    L.append(f"- Duplicates: {dup_fy} gvkey-fyear, {dup_date} gvkey-datadate. Rows with no assets value: {int((~has_assets).sum())}.\n")
    L.append("## Availability dates (when a number could first be used)\n")
    for label, mask in [("All rows", pd.Series(True, index=f.index)), ("Rows with assets", has_assets), (f"FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY} with assets", in_range & has_assets)]:
        s = f[mask]
        L.append(f"- {label}: {len(s)} rows, fallback lag used on {int((s.avail_source == 'fallback').sum())} = {(s.avail_source == 'fallback').mean():.2%}.")
    L.append(f"- 10-K dates on or before the year-end, treated as invalid: {len(on_or_before)}.")
    L.append(f"- 10-K filed over {short_lag} days after year-end: {int((f.filing_lag_days > short_lag).sum())}. Over {long_lag} days: {int((f.filing_lag_days > long_lag).sum())}. These are real dates and are used; see `clean_late_filings.csv`.\n")
    L.append(md_table(f[f.filing_lag_days > long_lag].sort_values("filing_lag_days", ascending=False)[["conm", "fyear", "datadate", "filing_date", "filing_lag_days"]]))
    L.append(f"\n## Fiscal-year changes and stub years (gap outside {cfg.STUB_MIN_DAYS}-{cfg.STUB_MAX_DAYS} days)\n")
    L.append(f"{len(stubs)} flagged, {int((stubs.days_since_prior < cfg.STUB_MIN_DAYS).sum())} short and {int((stubs.days_since_prior > cfg.STUB_MAX_DAYS).sum())} long. "
             f"{int(stubs.fyr_changed.sum())} changed fiscal-year end. Treatment in `04_scores.py`: {cfg.STUB_EXCLUSION}. Listed in `clean_stub_years.csv`.\n")
    L.append("## Sanity flags (never dropped)\n")
    L.append(f"- Negative assets: {int(f.neg_assets.sum())}. Negative sales: {int(f.neg_sale.sum())}, listed below.")
    L.append(f"- Year-over-year moves above {cfg.OUTLIER_YOY_RATIO}x, both years positive: at {int(f.outlier_at.sum())}, sale {int(f.outlier_sale.sum())}, adjusted shares {int(f.outlier_adj_shares.sum())}. Listed in `clean_outliers.csv`.\n")
    L.append(md_table(f[f.neg_sale][["conm", "fyear", "at", "sale"]]))
    L.append("\n## Non-USD reporters (not converted; decision pending)\n")
    L.append(md_table(non_usd.groupby(["gvkey", "conm", "curcd"]).agg(rows=("fyear", "size"), first_fy=("fyear", "min"), last_fy=("fyear", "max")).reset_index()))
    (LOGS / "clean_checks.md").write_text("\n".join(L), encoding="utf-8")

    print(f"rows={len(f)} companies={f.gvkey.nunique()} stubs={len(stubs)} fallback_all={(f.avail_source == 'fallback').mean():.2%} "
          f"outliers at/sale/adj={int(f.outlier_at.sum())}/{int(f.outlier_sale.sum())}/{int(f.outlier_adj_shares.sum())} late={int((f.filing_lag_days > short_lag).sum())}/{int((f.filing_lag_days > long_lag).sum())} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
