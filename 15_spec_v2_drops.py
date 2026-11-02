"""
spec_v2, step 5: what the pipeline loses, per formation date, v1 beside v2 (master's drops table). No new rules; existing v1 logs and the v2 results only.

Reads:  output/logs/universe_log.csv (v1, read only), data/clean/universe.parquet, formation.parquet (v1), data/clean/spec_v2/formation_v2.parquet, fscores_v2.parquet
Output: output/spec_v2/drops_by_date_v2.csv (one row per formation date), drops_reasons_v2.csv (unscored included names, one row per name and date), drops_summary_v2.md
The reasons depend only on scorability, which the issuance rule does not change (F_EQ_OFFER is always computable), so the net and literal runs share this table.

Columns, per date: (a) universe names with no GVKEY link, (b) no sector, (c) securities removed as stopped trading; (d) included names unscored in v1 and in v2, v2 split by reason
(missing signal by signal is counted separately and is not exclusive); (e) share of included market cap held by the unscored names; share of unscored names in GICS sectors 40 and 60.
Reason for an unscored name: the newest fiscal year within the 18-month age rule whose 10-K was filed (date + buffer on or before the formation date), or with no filing date; if none
exists, 'stale score' (a scored year exists but is older than the rule allows) or 'no usable fiscal year' (none at all).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / cfg.SPEC_V2["output_dir"]
LABEL = cfg.UNIVERSE_LABEL
SIGNALS = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_DLIQUID", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]
REIT_SECTORS = {"40", "60"}


def md_table(df, digits=None):
    d = df.copy()
    if digits is not None:
        for c in d.columns:
            if pd.api.types.is_float_dtype(d[c]):
                d[c] = d[c].round(digits)
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in d.itertuples(index=False)) + "\n"


def reason_for(row, s_by_gv):
    g = s_by_gv.get(row.gvkey)
    if g is None or g.empty:
        return "no usable fiscal year", ""
    buf = pd.Timedelta(days=cfg.SPEC_V2["availability_buffer_days"])
    fd = row.formation_date
    age = (fd.year - g.datadate.dt.year) * 12 + (fd.month - g.datadate.dt.month)
    cand = g[(g.datadate < fd) & (age <= cfg.MAX_SCORE_AGE_MONTHS) & (g.filing_date.isna() | (g.filing_date + buf <= fd))].sort_values("datadate")
    if cand.empty:
        return ("stale score" if (g.F_SCORE.notna() & (g.datadate < fd)).any() else "no usable fiscal year"), ""
    c = cand.iloc[-1]
    if bool(c.stub_flag):
        return "stub or fiscal-year change", ""
    if bool(c.no_filing_date):
        return "no 10-K filing date", ""
    if not bool(c.lag2_ok):
        return "unscorable t-2 (no consecutive prior years)", ""
    missing = [x for x in SIGNALS if pd.isna(c[x])]
    if missing:
        return "missing signal", ",".join(missing)
    return "other", ""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    ulog = pd.read_csv(ROOT / "output" / "logs" / "universe_log.csv", parse_dates=["formation_date"])
    u = pd.read_parquet(CLEAN / "universe.parquet")
    v1 = pd.read_parquet(CLEAN / "formation.parquet")
    v2 = pd.read_parquet(CLEAN / "spec_v2" / "formation_v2.parquet")
    s = pd.read_parquet(CLEAN / "spec_v2" / "fscores_v2.parquet")
    s_by_gv = {g: d for g, d in s.groupby("gvkey")}
    if len(v1) != len(v2):
        failures.append("v1 and v2 included rows differ")

    reasons = []
    for r in v2[~v2.scored].itertuples():
        reason, miss = reason_for(r, s_by_gv)
        reasons.append({"formation_date": r.formation_date, "permno": r.permno, "gvkey": r.gvkey, "gsector": r.gsector, "mktcap": r.mktcap, "v2_score_status": r.score_status, "reason": reason, "missing_signals": miss})
    reasons = pd.DataFrame(reasons)
    reasons.insert(0, "universe_label", LABEL)
    reasons.to_csv(OUT / "drops_reasons_v2.csv", index=False)
    if (reasons.reason == "other").any():
        failures.append(f"{int((reasons.reason == 'other').sum())} unscored rows with no identified reason")

    v1u = v1[~v1.scored]
    rows = []
    for d, ug in ulog.set_index("formation_date").iterrows():
        inc2 = v2[v2.formation_date == d]
        un2 = inc2[~inc2.scored]
        inc1 = v1[v1.formation_date == d]
        un1 = inc1[~inc1.scored]
        rs = reasons[reasons.formation_date == d]
        cap = inc2.mktcap.sum()
        row = {"universe_label": LABEL, "formation_date": d.date(), "universe_companies": int(ug.companies), "a_no_gvkey_link": int(ug.companies - ug.linked), "b_no_sector": int(ug.linked - ug.has_sector),
               "c_removed_stopped_trading": int(ug.drop_stopped_trading), "included": len(inc2), "d_unscored_v1": len(un1), "d_unscored_v2": len(un2),
               "d_v1_missing": int((inc1.score_status == "missing").sum()), "d_v1_stale": int((inc1.score_status == "stale").sum()),
               "d_v2_missing": int((un2.score_status == "missing").sum()), "d_v2_stale": int((un2.score_status == "stale").sum()),
               "e_unscored_mktcap_share_v1": un1.mktcap.sum() / inc1.mktcap.sum(), "e_unscored_mktcap_share_v2": un2.mktcap.sum() / cap,
               "unscored_in_sectors_40_60_v1": int(un1.gsector.isin(REIT_SECTORS).sum()), "unscored_in_sectors_40_60_v2": int(un2.gsector.isin(REIT_SECTORS).sum())}
        for k, v in rs.reason.value_counts().items():
            row[f"v2_reason: {k}"] = int(v)
        for sig in SIGNALS:
            row[f"v2_missing_signal: {sig}"] = int(rs.missing_signals.str.split(",").map(lambda xs: sig in xs).sum())
        rows.append(row)
    by_date = pd.DataFrame(rows).fillna(0)
    for c in by_date.columns:
        if c.startswith("v2_reason") or c.startswith("v2_missing_signal"):
            by_date[c] = by_date[c].astype(int)
    by_date.to_csv(OUT / "drops_by_date_v2.csv", index=False)
    if not (by_date.d_unscored_v2 == by_date.filter(like="v2_reason").sum(axis=1)).all():
        failures.append("Reasons do not add to the unscored count on every date")

    tot_inc, tot2, tot1 = by_date.included.sum(), by_date.d_unscored_v2.sum(), by_date.d_unscored_v1.sum()
    reason_totals = reasons.reason.value_counts().rename_axis("reason").reset_index(name="list_rows")
    reason_totals["share_of_unscored_pct"] = (100 * reason_totals.list_rows / tot2).round(1)
    sig_totals = pd.DataFrame({"signal": SIGNALS, "unscored_rows_missing_it": [int(by_date[f"v2_missing_signal: {x}"].sum()) for x in SIGNALS]})
    cap1 = np.average(by_date.e_unscored_mktcap_share_v1)
    cap2 = np.average(by_date.e_unscored_mktcap_share_v2)
    L = [f"# spec_v2 drops: {LABEL}\n",
         f"**{len(failures)} check failure(s).** One row per formation date: `output/spec_v2/drops_by_date_v2.csv`; one row per unscored name: `drops_reasons_v2.csv`. No return value was used. v1 columns come from the existing v1 files; the issuance rule does not change which names are scorable, so this table is the same for the net and literal runs.\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Totals over the 21 lists\n")
    L.append(f"- (a) Universe names with no GVKEY link: {int(by_date.a_no_gvkey_link.sum())}; (b) no sector: {int(by_date.b_no_sector.sum())}; (c) securities removed as stopped trading before ranking: {int(by_date.c_removed_stopped_trading.sum())}.")
    L.append(f"- (d) Included list rows: {tot_inc}. Unscored in v1: {tot1} ({100 * tot1 / tot_inc:.1f}%); unscored in v2: {tot2} ({100 * tot2 / tot_inc:.1f}%). v2 split: missing {int(by_date.d_v2_missing.sum())}, stale {int(by_date.d_v2_stale.sum())}. v1 split: missing {int(by_date.d_v1_missing.sum())}, stale {int(by_date.d_v1_stale.sum())}.")
    L.append(f"- (e) Average share of included market cap held by unscored names per date: v1 {100 * cap1:.1f}%, v2 {100 * cap2:.1f}%.")
    un_reit1, un_reit2 = int(by_date.unscored_in_sectors_40_60_v1.sum()), int(by_date.unscored_in_sectors_40_60_v2.sum())
    L.append(f"- Unscored names in GICS sectors 40 and 60 (REITs sit in 40 until the 2016 change, then 60; sector 40 also holds any remaining financials): v1 {un_reit1} of {tot1} ({100 * un_reit1 / tot1:.1f}%); v2 {un_reit2} of {tot2} ({100 * un_reit2 / tot2:.1f}%).\n")
    L.append("## v2 unscored names by reason\n")
    L.append(md_table(reason_totals))
    L.append("\nMissing-signal reasons, counted per signal (a name missing two signals counts in both):\n")
    L.append(md_table(sig_totals))
    L.append("\n## By formation date\n")
    show = by_date[["formation_date", "universe_companies", "a_no_gvkey_link", "b_no_sector", "c_removed_stopped_trading", "included", "d_unscored_v1", "d_unscored_v2", "e_unscored_mktcap_share_v1", "e_unscored_mktcap_share_v2",
                    "unscored_in_sectors_40_60_v1", "unscored_in_sectors_40_60_v2"]]
    L.append(md_table(show, 4))
    L.append("\nPer-reason counts by date are in the CSV (`v2_reason: ...` and `v2_missing_signal: ...` columns).\n")
    (OUT / "drops_summary_v2.md").write_text("\n".join(L), encoding="utf-8")
    print(f"unscored v1={tot1} v2={tot2} failures={len(failures)}")
    print(reason_totals.to_string(index=False))
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
