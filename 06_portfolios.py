"""
Phase 5: monthly returns for the score portfolios (CLAUDE.md sections 5, 8b and 9).

Reads:  data/clean/formation.parquet, data/clean/universe.parquet, data/raw/crsp_msf_v2.parquet, data/raw/crsp_benchmarks.parquet
Output: output/tables/portfolio_returns.csv (net and gross), score_portfolio_returns.csv, portfolio_turnover.csv, bucket_counts.csv
Logs:   output/logs/portfolio_checks.md, portfolio_exits.csv
Exit code is 1 if a check fails. A null return or a missing row inside a held position's window is always a failure.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"
TABLES = ROOT / "output" / "tables"

MAIN_BUCKETS = ["High", "Middle", "Low"]
CHARGED = MAIN_BUCKETS + (["Benchmark"] if cfg.CHARGE_PRIMARY_BENCHMARK else [])
RETURN_FIELDS = ["permno", "mthcaldt", "mthret", "mthretflg", "mthdelflg", "mthprcdt", "ticker", "issuernm"]


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def bucket_of(score):
    if score in cfg.HIGH_SCORES:
        return "High"
    if score in cfg.LOW_SCORES:
        return "Low"
    return "Middle"


def holding_months(formation_date):
    start = formation_date.to_period("M") + 1
    end = min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M"))
    return pd.period_range(start, end, freq="M")


def buy_and_hold(permnos, months, returns):
    """Equal weights at formation, drifting with returns. A stock with no row has exited; its value goes pro rata to the rest."""
    weights = pd.Series(1.0 / len(permnos), index=list(permnos))
    out = {}
    for mth in months:
        rets = returns.get(mth, pd.Series(dtype=float))
        active = weights.index.intersection(rets.index)
        weights = weights.loc[active]
        total = weights.sum()
        if total == 0 or len(active) == 0:
            out[mth] = np.nan
            continue
        weights = weights / total
        r = rets.loc[active]
        gross = float((weights * r).sum())
        out[mth] = gross
        weights = weights * (1 + r) / (1 + gross)
    return pd.Series(out), weights


def main():
    if cfg.WEIGHTING != "equal_buy_and_hold":
        raise ValueError(f"This script builds equal_buy_and_hold only, not {cfg.WEIGHTING}")
    if cfg.DELISTING_RULE != "reinvest_pro_rata":
        raise ValueError(f"Unknown DELISTING_RULE {cfg.DELISTING_RULE}")
    if cfg.TURNOVER_BASIS != "two_way" or cfg.COST_TIMING != "first_holding_month" or cfg.CHARGE_MIDPERIOD_REINVESTMENT:
        raise ValueError("Cost settings differ from what this script implements")
    TABLES.mkdir(parents=True, exist_ok=True)
    failures = []

    fm = pd.read_parquet(CLEAN / "formation.parquet")
    held = fm[fm.scored].copy()
    held["F_SCORE"] = held.F_SCORE.astype(int)
    held["bucket"] = held.F_SCORE.map(bucket_of)
    u = pd.read_parquet(CLEAN / "universe.parquet")
    r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=RETURN_FIELDS)
    r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    r["month"] = r.mthcaldt.dt.to_period("M")
    r["mthret"] = r.mthret.astype(float)
    if r.duplicated(["permno", "month"]).any():
        failures.append("Duplicate permno-month rows in returns")

    # Check every held position's window before any return is compounded
    by_permno = {p: g.set_index("month") for p, g in r.groupby("permno")}
    exits, nulls, gaps, no_formation_row = [], [], [], []
    for x in held.itertuples():
        months = holding_months(x.formation_date)
        h = by_permno.get(x.permno)
        if h is None or x.formation_date.to_period("M") not in h.index:
            no_formation_row.append((x.formation_date, x.permno))
            continue
        w = h[h.index.isin(months)].sort_index()
        for mth in w.index[w.mthret.isna()]:
            nulls.append({"formation_date": x.formation_date.date(), "permno": x.permno, "conm": x.conm, "month": str(mth), "flag": w.mthretflg[mth]})
        last = w.index.max() if len(w) else None
        if last is not None:
            for mth in months:
                if mth < last and mth not in w.index:
                    gaps.append({"formation_date": x.formation_date.date(), "permno": x.permno, "conm": x.conm, "month": str(mth)})
        if last is None or last < months[-1]:
            row = h.loc[x.formation_date.to_period("M")] if last is None else w.loc[last]
            exits.append({"formation_date": x.formation_date.date(), "permno": x.permno, "conm": x.conm, "F_SCORE": x.F_SCORE, "bucket": x.bucket,
                          "exit_type": "delisted on the formation date" if last is None else "mid-period exit",
                          "last_month_with_return": None if last is None else str(last), "months_held": 0 if last is None else len(w),
                          "last_return_flag": row.mthretflg, "delisting_flag": row.mthdelflg, "last_price_date": row.mthprcdt.date(),
                          "last_return_in_holding": None if last is None else row.mthret,
                          "treatment": "No later return. Target weight spread pro rata over the rest in the first holding month; uncharged." if last is None
                                       else "Final return includes the delisting return. Value spread pro rata over the rest from the next month; uncharged."})
    exits = pd.DataFrame(exits)
    exits.to_csv(LOGS / "portfolio_exits.csv", index=False)
    if nulls:
        failures.append(f"{len(nulls)} null returns inside a held position's window: {nulls[:10]}")
    if gaps:
        failures.append(f"{len(gaps)} missing rows inside a held position's window: {gaps[:10]}")
    if no_formation_row:
        failures.append(f"{len(no_formation_row)} held positions have no row on the formation date")
    bad_exit = exits[exits.exit_type.eq("mid-period exit") & (exits.delisting_flag == cfg.ACTIVE_DELISTING_FLAG)]
    if len(bad_exit):
        failures.append(f"{len(bad_exit)} exits have no delisting flag")

    # Null returns on included names that are not held: confirm each one explicitly
    fullrows = []
    null_rows = r[r.mthret.isna()][["permno", "month", "mthretflg", "issuernm"]]
    inc = fm[["formation_date", "permno", "conm", "scored", "score_status", "age_months"]]
    for x in inc.itertuples():
        hit = null_rows[(null_rows.permno == x.permno) & null_rows.month.isin(holding_months(x.formation_date))]
        if len(hit):
            fullrows.append({"formation_date": x.formation_date.date(), "permno": x.permno, "name": hit.issuernm.iloc[0], "null_months": f"{hit.month.min()} to {hit.month.max()}", "count": len(hit),
                             "flag": hit.mthretflg.iloc[0], "held": bool(x.scored), "score_status": x.score_status, "score_age_months": x.age_months})
    included_nulls = pd.DataFrame(fullrows)
    if len(included_nulls) and included_nulls.held.any():
        failures.append("A held position has null returns")

    # Monthly returns by cohort
    returns = {mth: g.dropna(subset=["mthret"]).set_index("permno").mthret for mth, g in r.groupby("month")}
    rows, score_rows, turnover_rows, count_rows = [], [], [], []
    drift = {}
    first_cost_month = {}
    for d in sorted(held.formation_date.unique()):
        d = pd.Timestamp(d)
        cohort = held[held.formation_date == d]
        months = holding_months(d)
        partial = len(months) < cfg.HOLDING_MONTHS
        for name, members in [(b, cohort[cohort.bucket == b]) for b in MAIN_BUCKETS] + [("Benchmark", cohort)]:
            count_rows.append({"formation_date": d.date(), "bucket": name, "names": len(members), "under_minimum": len(members) < cfg.MIN_BUCKET_NAMES})
            if members.empty:
                failures.append(f"{name} is empty on {d.date()}")
                continue
            series, end_weights = buy_and_hold(members.permno.tolist(), months, returns)
            if series.isna().any():
                failures.append(f"{name} has no holdings left during the {d.year} holding period")
            target = pd.Series(1.0 / len(members), index=members.permno.tolist())
            prior = drift.get(name)
            if prior is None:
                two_way = cfg.FIRST_PORTFOLIO_TURNOVER
            else:
                two_way = float(target.sub(prior, fill_value=0).abs().sum())
            cost = two_way * cfg.TRANSACTION_COST_BPS / 10000 if name in CHARGED else 0.0
            turnover_rows.append({"formation_date": d.date(), "bucket": name, "names": len(members), "turnover_two_way": two_way, "turnover_one_way": two_way / 2 if prior is not None else two_way, "cost": cost})
            drift[name] = end_weights
            for i, mth in enumerate(months):
                gross = series[mth]
                net = (1 + gross) * (1 - cost) - 1 if i == 0 else gross
                rows.append({"month": mth, "formation_date": d.date(), "partial_period": partial, "bucket": name, "gross": gross, "net": net})
        for score in range(0, 10):
            members = cohort[cohort.F_SCORE == score]
            if members.empty:
                continue
            series, _ = buy_and_hold(members.permno.tolist(), months, returns)
            for mth in months:
                score_rows.append({"month": str(mth), "formation_date": d.date(), "partial_period": partial, "F_SCORE": score, "names_at_formation": len(members), "gross": series[mth]})
    long = pd.DataFrame(rows)
    wide = long.pivot(index="month", columns="bucket", values=["net", "gross"])
    table = pd.DataFrame({"month": wide.index.astype(str)}, index=wide.index)
    cohort_of = long.drop_duplicates("month").set_index("month")
    table["formation_date"] = cohort_of.formation_date
    table["partial_period"] = cohort_of.partial_period
    for b in MAIN_BUCKETS + ["Benchmark"]:
        table[b] = wide["net"][b]
        table[f"{b}_gross"] = wide["gross"][b]
    table["Spread"] = table.High - table.Low
    table["Spread_gross"] = table.High_gross - table.Low_gross

    # Secondary benchmarks. RSP has two rows in April 2018, chained into one month.
    b = pd.read_parquet(RAW / "crsp_benchmarks.parquet", columns=["permno", "ticker", "mthcaldt", "mthret"])
    b = b[b.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    b["month"] = b.mthcaldt.dt.to_period("M")
    b["mthret"] = b.mthret.astype(float)
    if b.mthret.isna().any():
        failures.append("Null benchmark return")
    doubled = b[b.duplicated(["ticker", "month"], keep=False)]
    chained = b.groupby(["ticker", "month"]).mthret.apply(lambda s: (1 + s).prod() - 1).unstack("ticker")
    for t in cfg.SECONDARY_BENCHMARKS:
        table[t] = chained[t].reindex(table.index)
        if table[t].isna().any():
            failures.append(f"{t} is missing months in the test period")
    table.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    table.to_csv(TABLES / "portfolio_returns.csv", index=False)

    score_table = pd.DataFrame(score_rows)
    score_table.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    score_table.to_csv(TABLES / "score_portfolio_returns.csv", index=False)
    turnover = pd.DataFrame(turnover_rows)
    turnover.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    turnover.to_csv(TABLES / "portfolio_turnover.csv", index=False)
    counts = pd.DataFrame(count_rows)
    counts.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    counts.to_csv(TABLES / "bucket_counts.csv", index=False)

    # --- Checks on the built series ---
    start, end = pd.Period(f"{cfg.FIRST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", "M"), pd.Period(cfg.RETURNS_END, "M")
    expected = pd.period_range(start, end, freq="M")
    if list(table.index) != list(expected):
        failures.append(f"Months run {table.index.min()} to {table.index.max()}, expected {start} to {end}")
    if table[MAIN_BUCKETS + ["Benchmark", "Spread"]].isna().any().any():
        failures.append("Null in the monthly portfolio returns")
    # Benchmark's first month must equal the name-weighted buckets when no name exits at the start
    gap_rows = []
    gross_first = long.groupby(["formation_date", "bucket"]).first().reset_index()
    late = set(exits[exits.exit_type == "delisted on the formation date"].formation_date) if len(exits) else set()
    for d, g in gross_first.groupby("formation_date"):
        if d in late:
            continue
        n = counts[counts.formation_date == d].set_index("bucket").names
        g = g.set_index("bucket")
        calc = sum(g.gross[x] * n[x] for x in MAIN_BUCKETS) / n["Benchmark"]
        gap_rows.append(abs(calc - g.gross["Benchmark"]))
    if max(gap_rows) > 1e-10:
        failures.append(f"Buckets do not add up to the benchmark in the first month: largest gap {max(gap_rows)}")
    total = counts[counts.bucket == "Benchmark"].names.sum()
    if total != len(held):
        failures.append(f"Benchmark holds {total} names against {len(held)} valid scores")
    sum_buckets = counts[counts.bucket.isin(MAIN_BUCKETS)].groupby("formation_date").names.sum()
    if not (sum_buckets.values == counts[counts.bucket == "Benchmark"].names.values).all():
        failures.append("Buckets do not partition the benchmark")
    if (turnover.turnover_two_way > 2 + 1e-9).any():
        failures.append("Two-way turnover above 200%")

    small = counts[counts.under_minimum]
    delisters = exits[exits.exit_type == "delisted on the formation date"]
    mid = exits[exits.exit_type == "mid-period exit"]

    L = [f"# Phase 5 checks: {cfg.UNIVERSE_LABEL}\n", "## Result\n", f"**{len(failures)} check failure(s).** {len(small)} bucket-dates under {cfg.MIN_BUCKET_NAMES} names (flag only).\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Series\n")
    L.append(f"`portfolio_returns.csv`: {len(table)} months, {table.month.iloc[0]} to {table.month.iloc[-1]}. Named columns are **net of costs**; `_gross` columns are before costs. "
             f"RSP and SPY carry no extra charge. Spread is High minus Low, with no shorting costs, and is diagnostic only. "
             f"The {cfg.LAST_FORMATION_YEAR} portfolio stops at {cfg.RETURNS_END} and is partial: {int(table.partial_period.sum())} of {cfg.HOLDING_MONTHS} months.\n")
    unique = held.groupby("bucket").permco.nunique().reindex(MAIN_BUCKETS).to_dict()
    L.append(f"Held: {len(held)} company-dates, {held.permco.nunique()} unique companies, on {held.formation_date.nunique()} formation dates, {held.formation_date.min().date()} to {held.formation_date.max().date()}. Unique companies by bucket: {unique}.\n")
    L.append("## Bucket counts\n")
    L.append(md_table(counts.pivot(index="formation_date", columns="bucket", values="names")[MAIN_BUCKETS + ["Benchmark"]].reset_index()))
    L.append(f"\nBelow {cfg.MIN_BUCKET_NAMES} names:\n")
    L.append(md_table(small[["formation_date", "bucket", "names"]]) if len(small) else "None.\n")
    L.append("\n## Exits and missing returns\n")
    L.append(f"- Null returns inside held windows: {len(nulls)}. Missing rows inside held windows: {len(gaps)}.")
    L.append(f"- Mid-period exits: {len(mid)}, all with a delisting flag, by flag {mid.delisting_flag.value_counts().to_dict()}. Every one is in `portfolio_exits.csv` with its treatment.")
    L.append(f"- Delisted on the formation date: {len(delisters)}. No later return; the weight is spread pro rata in the first holding month, uncharged:\n")
    L.append(md_table(delisters[["formation_date", "conm", "F_SCORE", "bucket", "last_price_date", "delisting_flag"]]))
    L.append("\n## Null returns on included names not held (confirmed for Agent 3's cases)\n")
    L.append("Maxim's 2007 list row has a score 23 months old, so it is too old; General Growth has no score. Neither is in any portfolio or benchmark in those months.\n")
    L.append(md_table(included_nulls) if len(included_nulls) else "None.\n")
    L.append("\n## Costs\n")
    t2 = turnover[turnover.formation_date > turnover.formation_date.min()]
    avg = t2.groupby("bucket").agg(avg_two_way=("turnover_two_way", "mean"), avg_one_way=("turnover_one_way", "mean"), avg_cost=("cost", "mean")).reindex(MAIN_BUCKETS + ["Benchmark"]).reset_index()
    avg[["avg_two_way", "avg_one_way"]] = avg[["avg_two_way", "avg_one_way"]].round(4)
    avg["avg_cost"] = avg.avg_cost.round(6)
    L.append(f"{cfg.TRANSACTION_COST_BPS} bps on each side of `turnover_two_way`, taken in the first holding month. The first portfolio is charged at {cfg.FIRST_PORTFOLIO_TURNOVER:.0%} turnover. Averages exclude that first year. Every rebalance is in `portfolio_turnover.csv`.\n")
    L.append(md_table(avg))
    L.append("\n## Secondary benchmarks\n")
    L.append(f"Months with two rows for one fund, chained into one return: {sorted(set(str(m) for m in doubled.month))}, on {sorted(int(p) for p in doubled.permno.unique())}.\n")
    (LOGS / "portfolio_checks.md").write_text("\n".join(L), encoding="utf-8")

    print(f"months={len(table)} held={len(held)} exits={len(mid)} formation_delisters={len(delisters)} nulls={len(nulls)} gaps={len(gaps)} small_buckets={len(small)} failures={len(failures)}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
