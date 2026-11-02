"""
Phase 4: attach to each included company the score it could have known on the formation date (CLAUDE.md sections 5, 8b and 9).

Reads:  data/clean/universe.parquet, data/clean/fscores.parquet, data/clean/fundamentals_clean.parquet. No return data is read.
Output: data/clean/formation.parquet (one row per included company per date; F_SCORE is null if missing or too old)
Logs:   output/logs/formation_log.csv, formation_checks.md, formation_older_year.csv, formation_filed_on_date.csv, formation_non_usd.csv
Exit code is 1 if a check fails.
"""
import sys
from fractions import Fraction
from pathlib import Path

import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"

SIGNALS = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_DLIQUID", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]
LARGE_MOVE_RATIOS = (2, 10)  # report label for the disclosure in CLAUDE.md section 9; affects nothing


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def book_equity(d):
    if cfg.BOOK_EQUITY_RULE != "ceq_plus_txditc":
        raise ValueError(f"Unknown BOOK_EQUITY_RULE {cfg.BOOK_EQUITY_RULE}")
    return d.ceq + d.txditc.fillna(0)


def score_age_months(d):
    if cfg.SCORE_AGE_BASIS != "fiscal_year_end":
        raise ValueError(f"Unknown SCORE_AGE_BASIS {cfg.SCORE_AGE_BASIS}")
    return (d.formation_date.dt.year - d.datadate.dt.year) * 12 + (d.formation_date.dt.month - d.datadate.dt.month)


def exact_quantile(values, q):
    """Linear-interpolation quantile at an exact fraction, landing on a stock when the position is whole."""
    v = values.sort_values().to_numpy(dtype=float)
    pos = q * (len(v) - 1)
    below = int(pos)
    if pos == below:
        return v[below]
    return v[below] + (v[below + 1] - v[below]) * float(pos - below)


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    failures = []

    u = pd.read_parquet(CLEAN / "universe.parquet")
    s = pd.read_parquet(CLEAN / "fscores.parquet")
    f = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")

    # Latest score known by the formation date; on the same availability date, the later year-end wins
    keep = ["gvkey", "avail_date", "avail_source", "filing_date", "datadate", "fyear", "conm", "curcd", "F_SCORE", "ceq", "txditc", "at_yoy_ratio", "sale_yoy_ratio"] + SIGNALS
    scored = s[s.F_SCORE.notna()][keep].sort_values(["avail_date", "datadate"])
    inc = u[u.included].sort_values("formation_date")
    m = pd.merge_asof(inc, scored, left_on="formation_date", right_on="avail_date", by="gvkey", direction="backward")

    m["age_months"] = score_age_months(m)
    m["score_status"] = "missing"
    m.loc[m.datadate.notna(), "score_status"] = "stale"
    m.loc[m.age_months <= cfg.MAX_SCORE_AGE_MONTHS, "score_status"] = "valid"
    stale = m.score_status == "stale"
    m["stale_fyear"] = m.fyear.where(stale)
    m.loc[m.score_status != "valid", ["F_SCORE"] + SIGNALS] = float("nan")
    m["scored"] = m.score_status == "valid"

    # Version B inputs: book-to-market and its tercile, 1 = cheapest
    m["book_equity"] = book_equity(m).where(m.scored)
    m["book_to_market"] = m.book_equity / m.mktcap
    m["version_b_currency_ok"] = m.curcd == cfg.VERSION_B_CURRENCY
    m["value_tercile"] = pd.NA
    ranked = m.scored & m.version_b_currency_ok & m.book_to_market.notna()
    # Exact fractions: float 1 - 1/3 sits just above two-thirds and would miss a stock exactly on that point
    low_q = Fraction(cfg.VALUE_FILTER_QUANTILE).limit_denominator(1000)
    high_q = 1 - low_q
    for d, g in m[ranked].groupby("formation_date"):
        lo, hi = exact_quantile(g.book_to_market, low_q), exact_quantile(g.book_to_market, high_q)
        m.loc[g.index[g.book_to_market >= hi], "value_tercile"] = 1
        m.loc[g.index[(g.book_to_market < hi) & (g.book_to_market >= lo)], "value_tercile"] = 2
        m.loc[g.index[g.book_to_market < lo], "value_tercile"] = 3
    m["value_tercile"] = m.value_tercile.astype("Int64")
    m["in_version_b"] = m.value_tercile == 1

    cols = ["formation_date", "permno", "permco", "gvkey", "conm", "mktcap", "rank", "gsector", "score_status", "scored", "fyear", "datadate", "avail_date", "avail_source",
            "age_months", "F_SCORE"] + SIGNALS + ["curcd", "version_b_currency_ok", "ceq", "txditc", "book_equity", "book_to_market", "value_tercile", "in_version_b"]
    out = m[cols].sort_values(["formation_date", "rank"]).reset_index(drop=True)
    out.to_parquet(CLEAN / "formation.parquet", index=False)

    # --- Checks ---
    valid = m[m.scored]
    if len(m) != int(u.included.sum()):
        failures.append(f"Row count {len(m)} differs from included universe rows {int(u.included.sum())}")
    if m.duplicated(["formation_date", "permco"]).any():
        failures.append("Duplicate company on a formation date")
    if (valid.avail_date > valid.formation_date).any():
        failures.append("A score is attached before its availability date")
    if (valid.datadate >= valid.formation_date).any():
        failures.append("A score's fiscal year ends on or after the formation date")
    if (valid.age_months > cfg.MAX_SCORE_AGE_MONTHS).any():
        failures.append("A valid score is older than MAX_SCORE_AGE_MONTHS")
    if not valid.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY).all():
        failures.append("A score falls outside the score range")
    if (m[m.in_version_b].book_equity <= 0).any():
        failures.append("A non-positive book equity row is in the cheapest third")
    if (m.in_version_b & ~m.version_b_currency_ok).any():
        failures.append("A non-USD row is in version B")

    # Availability order inverts when an older year is filed after a newer one
    highest = []
    for r in valid.itertuples():
        known = scored[(scored.gvkey == r.gvkey) & (scored.avail_date <= r.formation_date)]
        highest.append(known.fyear.max())
    inverted = valid[pd.Series(highest, index=valid.index) != valid.fyear]
    if len(inverted):
        failures.append(f"{len(inverted)} rows use a lower fiscal year than a score already available: availability order inverted")

    # --- Section 9 reports ---
    per = m.groupby("formation_date").agg(universe_size=("permco", "size"), valid_score=("scored", "sum"), dropped_stale=("score_status", lambda x: (x == "stale").sum()),
                                          dropped_missing=("score_status", lambda x: (x == "missing").sum()), version_b_names=("in_version_b", "sum")).reset_index()
    per.to_csv(LOGS / "formation_log.csv", index=False)

    older = []
    for r in valid.itertuples():
        known = f[(f.gvkey == r.gvkey) & (f.avail_date <= r.formation_date)]
        if len(known) and known.fyear.max() > r.fyear:
            older.append({"formation_date": r.formation_date.date(), "conm": r.conm, "fyear_used": int(r.fyear), "newest_fyear_available": int(known.fyear.max()), "age_months": int(r.age_months)})
    older = pd.DataFrame(older)
    older.to_csv(LOGS / "formation_older_year.csv", index=False)

    on_date = valid[valid.avail_date == valid.formation_date][["formation_date", "conm", "fyear", "avail_date", "F_SCORE"]]
    on_date.to_csv(LOGS / "formation_filed_on_date.csv", index=False)
    non_usd = valid[~valid.version_b_currency_ok][["formation_date", "conm", "gvkey", "curcd", "fyear", "F_SCORE"]]
    non_usd.to_csv(LOGS / "formation_non_usd.csv", index=False)
    ties = scored[scored.duplicated(["gvkey", "avail_date"], keep=False)][["conm", "gvkey", "fyear", "datadate", "avail_date"]]
    tie_rows = valid.merge(ties[["gvkey", "avail_date"]].drop_duplicates(), on=["gvkey", "avail_date"])
    lo2, hi2 = LARGE_MOVE_RATIOS
    moved = valid[[((a := r.at_yoy_ratio) > lo2 and a <= hi2) or (a < 1 / lo2 and a >= 1 / hi2) or ((b := r.sale_yoy_ratio) > lo2 and b <= hi2) or (b < 1 / lo2 and b >= 1 / hi2)
                   for r in valid.itertuples()]]

    L = [f"# Phase 4 checks: {cfg.UNIVERSE_LABEL}\n", "## Result\n", f"**{len(failures)} check failure(s).**\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Coverage\n")
    L.append(f"{len(m)} included company-dates: {len(valid)} with a valid score, {int(stale.sum())} dropped as too old (over {cfg.MAX_SCORE_AGE_MONTHS} months from fiscal year-end to formation date), "
             f"{int((m.score_status == 'missing').sum())} with no score known by the date.\n")
    L.append(f"Unique companies: {m.permco.nunique()} included, {valid.permco.nunique()} with a valid score. Formation dates: {m.formation_date.nunique()}, {m.formation_date.min().date()} to {m.formation_date.max().date()}. Fiscal years used: {int(valid.fyear.min())}-{int(valid.fyear.max())}.\n")
    L.append(md_table(per))
    L.append("\n## Alignment items (CLAUDE.md section 9)\n")
    L.append(f"- Same availability date for several years: {len(ties)} fiscal years. The later year-end wins. List rows using such a date: {len(tie_rows)}.")
    L.append(f"- Rows using a lower fiscal year than a score already available (order inversion): {len(inverted)}.")
    L.append(f"- Rows using an older year because the newest available year has no score: {len(older)}. Listed below and in `formation_older_year.csv`.")
    L.append(f"- Rows whose 10-K was filed on the formation date itself: {len(on_date)}, kept under the on-or-before rule. Listed in `formation_filed_on_date.csv`.")
    L.append(f"- Rows with a {lo2}x-{hi2}x move in assets or sales in the scored year, for disclosure: {len(moved)}.")
    L.append(f"- Non-{cfg.VERSION_B_CURRENCY} rows, excluded from version B only: {len(non_usd)}: {sorted(non_usd.conm.unique())}.\n")
    if len(older):
        L.append(md_table(older))
    L.append("\n## Version B inputs (robustness only)\n")
    rb = m[ranked]
    L.append(f"Book equity rule `{cfg.BOOK_EQUITY_RULE}`. Ranked rows {len(rb)}; cheapest-third rows {int(m.in_version_b.sum())}; non-positive book equity {int((rb.book_equity <= 0).sum())}; "
             f"null book equity among valid scores {int(valid.book_equity.isna().sum())}.\n")
    (LOGS / "formation_checks.md").write_text("\n".join(L), encoding="utf-8")

    print(f"included={len(m)} valid={len(valid)} stale={int(stale.sum())} missing={int((m.score_status == 'missing').sum())} older_year={len(older)} filed_on_date={len(on_date)} "
          f"large_moves={len(moved)} ties={len(tie_rows)} inverted={len(inverted)} non_usd={len(non_usd)} version_b={int(m.in_version_b.sum())} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
