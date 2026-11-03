"""
spec_v2, step 3: monthly portfolio returns from the v2 lists (CLAUDE.md section 8f and its Clarifications, SPEC_V2 in config.py). First script that reads returns.

Usage:  python 13_spec_v2_portfolios.py [--rule net|literal]
Reads:  data/clean/spec_v2/formation_v2[_literal].parquet, data/raw/crsp_msf_v2.parquet, data/raw/crsp_benchmarks.parquet
Output: <out>/portfolio_returns_v2.csv, portfolio_turnover_v2.csv, bucket_counts_v2.csv, portfolio_exits_v2.csv, portfolio_checks_v2.md
        <out> is output/spec_v2 for the net rule and output/spec_v2/literal_sensitivity for the literal rule.
Exit code is 1 if a check fails.

Portfolios: High, Middle, Low from valid scores; Benchmark = every included name (scored and unscored), the primary benchmark; BenchmarkScored = scored names only
(v1's benchmark), reported beside. All five are charged TRANSACTION_COST_BPS on two-way turnover in the first holding month, as in v1.
v2 differences: a mid-period exit's proceeds, reinvested pro rata, are charged TRANSACTION_COST_BPS on the value reinvested (one side), in the exit month, unless the exit is in the
final holding month; a formation-date delister counts at 1/N in the turnover target (charged as a buy), earns nothing and is respread free; null-return months listed in
NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2"] are held flat at 0% with no charge; any other null return in a held window stops the run.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
V2CLEAN = ROOT / "data" / "clean" / "spec_v2"
V2 = cfg.SPEC_V2
MAIN = ["High", "Middle", "Low"]
PORTS = MAIN + ["Benchmark", "BenchmarkScored"]
FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2"].items() for m in ms}
BPS = cfg.TRANSACTION_COST_BPS / 10000


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def run_portfolio(members, months, ret_by_month, last_month):
    """Equal weights at formation, buy and hold. Returns (gross by month, reinvestment cost fraction by month, end weights).
    A stock with no row in a month has exited; its value goes pro rata to the rest. Reinvestment of a mid-period exit is charged in the exit month."""
    w = pd.Series(1.0 / len(members), index=list(members))
    gross, reinv = {}, {}
    for m in months:
        rets = ret_by_month.get(m, pd.Series(dtype=float))
        flat = [p for p in w.index if (p, m) in FLAT]
        if flat:
            rets = rets.copy()
            for p in flat:
                rets.loc[p] = 0.0
        active = w.index.intersection(rets.index)
        w = w.loc[active]
        if len(active) == 0:
            gross[m], reinv[m] = np.nan, 0.0
            continue
        w = w / w.sum()
        r = rets.loc[active]
        g = float((w * r).sum())
        gross[m] = g
        w = w * (1 + r) / (1 + g)
        leaving = [p for p in w.index if last_month.get(p) == m and m < months[-1]]
        reinv[m] = float(w.loc[leaving].sum()) * BPS if V2["charge_every_trade"] else 0.0
    return pd.Series(gross), pd.Series(reinv), w


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rule", choices=["net", "literal"], default="net")
    rule = ap.parse_args().rule
    suf = "" if rule == "net" else "_literal"
    out = ROOT / V2["output_dir"] / ("" if rule == "net" else "literal_sensitivity")
    out.mkdir(parents=True, exist_ok=True)
    failures = []
    label = cfg.UNIVERSE_LABEL

    inc = pd.read_parquet(V2CLEAN / f"formation_v2{suf}.parquet")
    r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretflg", "mthdelflg", "mthprcdt", "issuernm"])
    r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    r["month"] = r.mthcaldt.dt.to_period("M")
    r["mthret"] = r.mthret.astype(float)
    if r.duplicated(["permno", "month"]).any():
        failures.append("Duplicate permno-month rows in returns")
    by_permno = {p: g.set_index("month") for p, g in r.groupby("permno")}
    ret_by_month = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}

    # --- Window checks for every included name (all are held in the primary benchmark) ---
    exits, nulls, flat_used, gaps, no_row = [], [], [], [], []
    last_month_of = {}   # (formation_date, permno) -> last month with a return (or hold-flat month) in the window
    for x in inc.itertuples():
        months = holding_months(x.formation_date)
        h = by_permno.get(x.permno)
        if h is None or x.formation_date.to_period("M") not in h.index:
            no_row.append((x.formation_date.date(), x.permno))
            continue
        w = h[h.index.isin(months)].sort_index()
        for mth in w.index[w.mthret.isna()]:
            rec = {"formation_date": x.formation_date.date(), "permno": x.permno, "month": str(mth), "bucket": x.bucket, "flag": w.mthretflg[mth]}
            if (x.permno, mth) in FLAT and x.bucket == "Unscored":
                flat_used.append(rec)
            else:
                nulls.append(rec)
        ok_months = [m for m in w.index if pd.notna(w.mthret[m]) or (x.permno, m) in FLAT]
        last = max(ok_months) if ok_months else None
        last_month_of[(x.formation_date, x.permno)] = last
        if last is not None:
            for mth in months:
                if mth < last and mth not in w.index:
                    gaps.append((x.formation_date.date(), x.permno, str(mth)))
        if last is None or last < months[-1]:
            row = h.loc[x.formation_date.to_period("M")] if last is None else w.loc[last]
            exits.append({"formation_date": x.formation_date.date(), "permno": x.permno, "name": row.issuernm, "bucket": x.bucket, "F_SCORE": x.F_SCORE,
                          "exit_type": "delisted on the formation date" if last is None else "mid-period exit",
                          "last_month_with_return": None if last is None else str(last), "delisting_flag": row.mthdelflg, "last_price_date": row.mthprcdt.date()})
    exits = pd.DataFrame(exits)
    exits.to_csv(out / "portfolio_exits_v2.csv", index=False)
    if nulls:
        failures.append(f"{len(nulls)} null returns in held windows with no approved rule: {nulls[:10]}")
    if gaps:
        failures.append(f"{len(gaps)} missing rows inside held windows: {gaps[:10]}")
    if no_row:
        failures.append(f"{len(no_row)} included names have no row on the formation date: {no_row[:10]}")
    approved = {(p, str(m)) for p, m in FLAT}
    if {(x["permno"], x["month"]) for x in flat_used} - approved:
        failures.append("A hold-flat month outside the approved list was used")
    if len(exits) and (exits.exit_type.eq("mid-period exit") & (exits.delisting_flag == cfg.ACTIVE_DELISTING_FLAG)).any():
        failures.append("A mid-period exit has no delisting flag")
    if failures:
        (out / "portfolio_checks_v2.md").write_text("# spec_v2 portfolios: STOPPED before compounding\n" + "\n".join(f"- FAIL: {x}" for x in failures) + "\n", encoding="utf-8")
        for x in failures:
            print("FAIL:", x)
        sys.exit(1)

    rows, turn_rows, count_rows = [], [], []
    drift = {}
    for d in sorted(inc.formation_date.unique()):
        d = pd.Timestamp(d)
        cohort = inc[inc.formation_date == d]
        months = holding_months(d)
        partial = len(months) < cfg.HOLDING_MONTHS
        last_month = {p: last_month_of[(d, p)] for p in cohort.permno}
        groups = {b: cohort[cohort.bucket == b] for b in MAIN}
        groups["Benchmark"] = cohort
        groups["BenchmarkScored"] = cohort[cohort.scored]
        for name in PORTS:
            mem = groups[name]
            count_rows.append({"formation_date": d.date(), "portfolio": name, "names": len(mem), "under_minimum": len(mem) < cfg.MIN_BUCKET_NAMES})
            if mem.empty:
                failures.append(f"{name} is empty on {d.date()}")
                continue
            gross, reinv, end_w = run_portfolio(mem.permno.tolist(), months, ret_by_month, last_month)
            if gross.isna().any():
                failures.append(f"{name} has no holdings left in the {d.year} holding period")
            target = pd.Series(1.0 / len(mem), index=mem.permno.tolist())
            prior = drift.get(name)
            two_way = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(target.sub(prior, fill_value=0).abs().sum())
            cost = two_way * BPS
            turn_rows.append({"formation_date": d.date(), "portfolio": name, "names": len(mem), "turnover_two_way": two_way, "turnover_one_way": two_way / 2 if prior is not None else two_way,
                              "cost_rebalance": cost, "reinvestment_cost_total": float(reinv.sum())})
            drift[name] = end_w
            for i, m in enumerate(months):
                c = (cost if i == 0 else 0.0) + reinv[m]
                rows.append({"month": m, "formation_date": d.date(), "partial_period": partial, "portfolio": name, "gross": gross[m], "net": (1 + gross[m]) * (1 - c) - 1})
    long = pd.DataFrame(rows)
    wide = long.pivot(index="month", columns="portfolio", values=["net", "gross"])
    table = pd.DataFrame({"month": wide.index.astype(str)}, index=wide.index)
    co = long.drop_duplicates("month").set_index("month")
    table["formation_date"] = co.formation_date
    table["partial_period"] = co.partial_period
    for b in PORTS:
        table[b] = wide["net"][b]
        table[f"{b}_gross"] = wide["gross"][b]
    table["Spread"] = table.High - table.Low
    table["Spread_gross"] = table.High_gross - table.Low_gross
    bm_raw = pd.read_parquet(RAW / "crsp_benchmarks.parquet", columns=["permno", "ticker", "mthcaldt", "mthret"])
    bm_raw = bm_raw[bm_raw.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    bm_raw["month"] = bm_raw.mthcaldt.dt.to_period("M")
    bm_raw["mthret"] = bm_raw.mthret.astype(float)
    if bm_raw.mthret.isna().any():
        failures.append("Null benchmark return")
    chained = bm_raw.groupby(["ticker", "month"]).mthret.apply(lambda s: (1 + s).prod() - 1).unstack("ticker")
    for t in cfg.SECONDARY_BENCHMARKS:
        table[t] = chained[t].reindex(table.index)
        if table[t].isna().any():
            failures.append(f"{t} is missing months")
    table.insert(0, "universe_label", label)
    table.to_csv(out / "portfolio_returns_v2.csv", index=False)
    counts = pd.DataFrame(count_rows)
    counts.insert(0, "universe_label", label)
    counts.to_csv(out / "bucket_counts_v2.csv", index=False)
    turnover = pd.DataFrame(turn_rows)
    turnover.insert(0, "universe_label", label)
    turnover.to_csv(out / "portfolio_turnover_v2.csv", index=False)

    # --- Checks ---
    expected = pd.period_range(pd.Period(f"{cfg.FIRST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", "M"), pd.Period(cfg.RETURNS_END, "M"), freq="M")
    if list(table.index) != list(expected):
        failures.append("Months do not run June 2005 to December 2025")
    if table[PORTS + ["Spread"]].isna().any().any():
        failures.append("Null in the monthly portfolio series")
    sum_b = counts[counts.portfolio.isin(MAIN)].groupby("formation_date").names.sum()
    sc = counts[counts.portfolio == "BenchmarkScored"].set_index("formation_date").names
    if not (sum_b.values == sc.loc[sum_b.index].values).all():
        failures.append("Buckets do not partition the scored-only benchmark")
    bm = counts[counts.portfolio == "Benchmark"].set_index("formation_date").names
    if not (bm.values == inc.groupby("formation_date").size().values).all():
        failures.append("Primary benchmark does not hold every included name")
    if (turnover.turnover_two_way > 2 + 1e-9).any():
        failures.append("Two-way turnover above 200%")
    gap_rows = []
    late = set(exits[exits.exit_type == "delisted on the formation date"].formation_date) if len(exits) else set()
    first = long.groupby(["formation_date", "portfolio"]).first().reset_index()
    for d, g in first.groupby("formation_date"):
        if d in late:
            continue
        n = counts[counts.formation_date == d].set_index("portfolio").names
        g = g.set_index("portfolio")
        gap_rows.append(abs(sum(g.gross[x] * n[x] for x in MAIN) / n["BenchmarkScored"] - g.gross["BenchmarkScored"]))
    if gap_rows and max(gap_rows) > 1e-10:
        failures.append(f"Buckets do not add to the scored-only benchmark in the first month: {max(gap_rows)}")

    small = counts[counts.under_minimum]
    delisters = exits[exits.exit_type == "delisted on the formation date"] if len(exits) else exits
    mid = exits[exits.exit_type == "mid-period exit"] if len(exits) else exits
    L = [f"# spec_v2 portfolios ({'net issuance rule, primary' if rule == 'net' else 'literal issuance rule, sensitivity'}): {label}\n",
         f"**{len(failures)} check failure(s).** {len(small)} portfolio-dates under {cfg.MIN_BUCKET_NAMES} names (flag only).\n"] + [f"- FAIL: {x}" for x in failures] + [""]
    L.append(f"`portfolio_returns_v2.csv`: {len(table)} months, {table.month.iloc[0]} to {table.month.iloc[-1]}, net of costs unless `_gross`. Benchmark = all included names ({int(bm.sum())} company-dates); BenchmarkScored = scored names ({int(sc.sum())}). The {cfg.LAST_FORMATION_YEAR} portfolio is partial ({int(table.partial_period.sum())} of {cfg.HOLDING_MONTHS} months).\n")
    uniq = inc.groupby("bucket").permco.nunique().to_dict()
    L.append(f"Coverage: {len(inc)} included company-dates from {inc.permco.nunique()} unique companies on {inc.formation_date.nunique()} formation dates, {inc.formation_date.min().date()} to {inc.formation_date.max().date()}; "
             f"unique companies by bucket (Unscored = included but not scored): {uniq}. Holding months {table.month.iloc[0]} to {table.month.iloc[-1]}.\n")
    L.append("## Bucket counts\n")
    L.append(md_table(counts.pivot(index="formation_date", columns="portfolio", values="names")[PORTS].reset_index()))
    L.append(f"\nUnder {cfg.MIN_BUCKET_NAMES} names:\n")
    L.append(md_table(small[["formation_date", "portfolio", "names"]]) if len(small) else "None.\n")
    L.append("\n## Exits and missing returns\n")
    L.append(f"- Unapproved null returns in held windows: {len(nulls)}. Missing rows: {len(gaps)}.")
    L.append(f"- Hold-flat months used (0% return, no charge, benchmark only): {len(flat_used)}. " + "; ".join(f"permno {x['permno']} {x['month']} (formation {x['formation_date']})" for x in flat_used))
    L.append(f"- Mid-period exits: {len(mid)} (bucket mix {mid.bucket.value_counts().to_dict() if len(mid) else {}}). Formation-date delisters: {len(delisters)}.")
    if len(delisters):
        L.append(md_table(delisters[["formation_date", "name", "bucket", "last_price_date", "delisting_flag"]]))
    L.append("\n## Costs\n")
    t2 = turnover[turnover.formation_date > turnover.formation_date.min()]
    avg = t2.groupby("portfolio").agg(avg_two_way=("turnover_two_way", "mean"), avg_one_way=("turnover_one_way", "mean"), avg_rebalance_cost=("cost_rebalance", "mean"), avg_reinvestment_cost=("reinvestment_cost_total", "mean")).reindex(PORTS).round(6).reset_index()
    L.append(f"{cfg.TRANSACTION_COST_BPS} bps per side of two-way turnover, taken in the first holding month, plus {cfg.TRANSACTION_COST_BPS} bps on the value reinvested after a mid-period exit, taken in the exit month. First portfolio charged at {cfg.FIRST_PORTFOLIO_TURNOVER:.0%}; averages exclude it.\n")
    L.append(md_table(avg))
    (out / "portfolio_checks_v2.md").write_text("\n".join(L), encoding="utf-8")
    print(f"rule={rule} months={len(table)} exits={len(mid)} formation_delisters={len(delisters)} hold_flat={len(flat_used)} small={len(small)} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
