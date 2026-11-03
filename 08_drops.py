"""
Stage 08: what the pipeline loses, per formation date. No new rules; the universe log and the stage 05 results only.

Usage:  python 08_drops.py [--rule literal|net]   (default literal, the primary rule)
Reads:  output/logs/universe_log.csv, data/clean/universe.parquet, data/clean/core[/net_sensitivity]/formation.parquet, fscores.parquet
Output: <out>/drops_by_date.csv (one row per formation date), drops_reasons.csv (unscored included names, one row per name and date), drops_summary.md
        <out> is output/core for the literal rule and output/core/net_sensitivity for the net rule. Scorability differs slightly between the rules: the net rule makes a missing prstkc unscorable.

Columns, per date: (a) universe names with no GVKEY link, (b) no sector, (c) securities removed as stopped trading; (d) included names unscored, split by reason
(missing signal by signal is counted separately and is not exclusive); (e) share of included market cap held by the unscored names; share of unscored names in GICS sectors 40 and 60.
Reason for an unscored name: the newest fiscal year within the 18-month age rule whose 10-K was filed (date + buffer on or before the formation date), or with no filing date; if none
exists, 'stale score' (a scored year exists but is older than the rule allows) or 'no usable fiscal year' (none at all).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
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
    buf = pd.Timedelta(days=cfg.PIPELINE["availability_buffer_days"])
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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rule", choices=["literal", "net"], default="literal")
    sub = "" if ap.parse_args().rule == "literal" else "net_sensitivity"
    OUT = ROOT / cfg.PIPELINE["output_dir"] / sub
    OUT.mkdir(parents=True, exist_ok=True)
    failures = []
    ulog = pd.read_csv(ROOT / "output" / "logs" / "universe_log.csv", parse_dates=["formation_date"])
    u = pd.read_parquet(CLEAN / "universe.parquet")
    fm = pd.read_parquet(CLEAN / "core" / sub / "formation.parquet")
    s = pd.read_parquet(CLEAN / "core" / sub / "fscores.parquet")
    s_by_gv = {g: d for g, d in s.groupby("gvkey")}

    reasons = []
    for r in fm[~fm.scored].itertuples():
        reason, miss = reason_for(r, s_by_gv)
        reasons.append({"formation_date": r.formation_date, "permno": r.permno, "gvkey": r.gvkey, "gsector": r.gsector, "mktcap": r.mktcap, "score_status": r.score_status, "reason": reason, "missing_signals": miss})
    reasons = pd.DataFrame(reasons)
    reasons.insert(0, "universe_label", LABEL)
    reasons.to_csv(OUT / "drops_reasons.csv", index=False)
    if (reasons.reason == "other").any():
        failures.append(f"{int((reasons.reason == 'other').sum())} unscored rows with no identified reason")

    rows = []
    for d, ug in ulog.set_index("formation_date").iterrows():
        inc = fm[fm.formation_date == d]
        un = inc[~inc.scored]
        rs = reasons[reasons.formation_date == d]
        cap = inc.mktcap.sum()
        row = {"universe_label": LABEL, "formation_date": d.date(), "universe_companies": int(ug.companies), "a_no_gvkey_link": int(ug.companies - ug.linked), "b_no_sector": int(ug.linked - ug.has_sector),
               "c_removed_stopped_trading": int(ug.drop_stopped_trading), "included": len(inc), "d_unscored": len(un),
               "d_missing": int((un.score_status == "missing").sum()), "d_stale": int((un.score_status == "stale").sum()),
               "e_unscored_mktcap_share": un.mktcap.sum() / cap,
               "unscored_in_sectors_40_60": int(un.gsector.isin(REIT_SECTORS).sum())}
        for k, v in rs.reason.value_counts().items():
            row[f"reason: {k}"] = int(v)
        for sig in SIGNALS:
            row[f"missing_signal: {sig}"] = int(rs.missing_signals.str.split(",").map(lambda xs: sig in xs).sum())
        rows.append(row)
    by_date = pd.DataFrame(rows).fillna(0)
    for c in by_date.columns:
        if c.startswith("reason") or c.startswith("missing_signal"):
            by_date[c] = by_date[c].astype(int)
    by_date.to_csv(OUT / "drops_by_date.csv", index=False)
    if not (by_date.d_unscored == by_date.filter(like="reason: ").sum(axis=1)).all():
        failures.append("Reasons do not add to the unscored count on every date")

    tot_inc, tot = by_date.included.sum(), by_date.d_unscored.sum()
    reason_totals = reasons.reason.value_counts().rename_axis("reason").reset_index(name="list_rows")
    reason_totals["share_of_unscored_pct"] = (100 * reason_totals.list_rows / tot).round(1)
    sig_totals = pd.DataFrame({"signal": SIGNALS, "unscored_rows_missing_it": [int(by_date[f"missing_signal: {x}"].sum()) for x in SIGNALS]})
    cap = np.average(by_date.e_unscored_mktcap_share)
    L = [f"# Drops: {LABEL}\n",
         f"**{len(failures)} check failure(s).** One row per formation date: `drops_by_date.csv`; one row per unscored name: `drops_reasons.csv` (same folder). No return value was used.\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Totals over the 21 lists\n")
    L.append(f"- (a) Universe names with no GVKEY link: {int(by_date.a_no_gvkey_link.sum())}; (b) no sector: {int(by_date.b_no_sector.sum())}; (c) securities removed as stopped trading before ranking: {int(by_date.c_removed_stopped_trading.sum())}.")
    L.append(f"- (d) Included list rows: {tot_inc}. Unscored: {tot} ({100 * tot / tot_inc:.1f}%). Split: missing {int(by_date.d_missing.sum())}, stale {int(by_date.d_stale.sum())}.")
    L.append(f"- (e) Average share of included market cap held by unscored names per date: {100 * cap:.1f}%.")
    un_reit = int(by_date.unscored_in_sectors_40_60.sum())
    L.append(f"- Unscored names in GICS sectors 40 and 60 (REITs sit in 40 until the 2016 change, then 60; sector 40 also holds any remaining financials): {un_reit} of {tot} ({100 * un_reit / tot:.1f}%).\n")
    L.append("## Unscored names by reason\n")
    L.append(md_table(reason_totals))
    L.append("\nMissing-signal reasons, counted per signal (a name missing two signals counts in both):\n")
    L.append(md_table(sig_totals))
    L.append("\n## By formation date\n")
    show = by_date[["formation_date", "universe_companies", "a_no_gvkey_link", "b_no_sector", "c_removed_stopped_trading", "included", "d_unscored", "e_unscored_mktcap_share", "unscored_in_sectors_40_60"]]
    L.append(md_table(show, 4))
    L.append("\nPer-reason counts by date are in the CSV (`reason: ...` and `missing_signal: ...` columns).\n")
    (OUT / "drops_summary.md").write_text("\n".join(L), encoding="utf-8")
    print(f"unscored={tot} failures={len(failures)}")
    print(reason_totals.to_string(index=False))
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
