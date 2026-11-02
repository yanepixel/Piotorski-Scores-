"""
Phase 7: rerun Phases 4-6 changing one setting at a time (CLAUDE.md sections 5 and 8c). The headline stays the headline.

Reads:  data/clean/*.parquet, data/raw/*.parquet, output/tables/portfolio_returns.csv. WRDS for the buffer's ranking and the quarterly pull.
Raw:    data/raw/comp_fundq.parquet, comp_co_filedate_quarterly.parquet (new; write-once, pass --overwrite to replace)
Output: output/robustness/<variant>/ (formation, returns, turnover, counts, exits), output/robustness/robustness_report.md,
        output/tables/robustness_comparison.csv, robustness_subperiods.csv
Log:    output/logs/robustness_log.csv
A variant with an empty bucket or an unexpected null return reports no results and sets exit code 1.
"""
import argparse
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
TABLES = ROOT / "output" / "tables"
OUT = ROOT / "output" / "robustness"

MAIN = ["High", "Middle", "Low"]
EIGHT_SIGNALS = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]
HOLD_FLAT_LABEL = "General Growth Properties, May 2009"
BUFFER_HOLD_FLAT_LABEL = "Comverse Technology, February to May 2007"


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


universe_mod = load("01_build_universe.py", "universe_mod")
scores_mod = load("04_scores.py", "scores_mod")
align_mod = load("05_align.py", "align_mod")
eval_mod = load("07_evaluate.py", "eval_mod")
md_table = eval_mod.md_table


def hold_flat_cases(variant, rule):
    """The approved (PERMNO, month) cases, only while the variant's rule is hold_flat. Any other held null stops the run."""
    if rule != "hold_flat":
        return frozenset()
    return frozenset((p, m) for p, months in cfg.NULL_RETURN_HOLD_FLAT_MONTHS[variant].items() for m in months)


class VariantStop(Exception):
    """An empty bucket or unexpected null return: report it, show no results for the variant."""


# ---------- Phase 4 logic ----------
def align(universe, scored):
    s = scored[scored.F_SCORE.notna()].sort_values(["avail_date", "datadate"])
    keep = ["gvkey", "avail_date", "datadate", "fyear", "conm", "F_SCORE", "score_type", "ceq", "txditc", "curcd"]
    inc = universe[universe.included].sort_values("formation_date")
    m = pd.merge_asof(inc, s[keep], left_on="formation_date", right_on="avail_date", by="gvkey", direction="backward")
    m["age_months"] = align_mod.score_age_months(m)
    m["scored"] = m.age_months <= cfg.MAX_SCORE_AGE_MONTHS
    return m


def buckets(d, high=None, low=None):
    high = cfg.HIGH_SCORES if high is None else high
    low = cfg.LOW_SCORES if low is None else low
    out = pd.Series("Middle", index=d.index)
    out[d.F_SCORE.isin(high)] = "High"
    out[d.F_SCORE.isin(low)] = "Low"
    if "score_type" in d:
        eight = d.score_type == "eight"
        out[eight] = "Middle"
        out[eight & d.F_SCORE.isin(cfg.EIGHT_SIGNAL_HIGH_SCORES)] = "High"
        out[eight & d.F_SCORE.isin(cfg.EIGHT_SIGNAL_LOW_SCORES)] = "Low"
    return out


# ---------- Phase 5 logic, with weights as an input ----------
class Returns:
    def __init__(self):
        r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretflg", "mthdelflg", "mthprcdt", "issuernm"])
        r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
        r["month"] = r.mthcaldt.dt.to_period("M")
        r["mthret"] = r.mthret.astype(float)
        self.by_permno = {p: g.set_index("month").sort_index() for p, g in r.groupby("permno")}
        self.by_month = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}


def holding_months(d):
    start = d.to_period("M") + 1
    return pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")


def target_weights(members, cohort, weighting):
    if weighting == "equal_buy_and_hold":
        w = pd.Series(1.0, index=members.permno.values)
    elif weighting == "cap_buy_and_hold":
        if cfg.CAP_WEIGHT_BASIS != "formation_mktcap":
            raise ValueError(cfg.CAP_WEIGHT_BASIS)
        w = pd.Series(members.mktcap.values, index=members.permno.values)
    elif weighting == "equal_sector_neutral":
        if cfg.SECTOR_NEUTRAL_WEIGHTS != "benchmark_sector_weights" or cfg.SECTOR_NEUTRAL_EMPTY_SECTOR != "spread_pro_rata":
            raise ValueError("Sector-neutral settings differ from what this script implements")
        share = cohort.groupby("gsector").size() / len(cohort)
        within = members.groupby("gsector").permno.transform("size")
        # Sectors with no names drop out here, which spreads their weight pro rata when normalised below
        w = pd.Series((members.gsector.map(share) / within).values, index=members.permno.values)
    else:
        raise ValueError(f"Unknown weighting {weighting}")
    return w / w.sum()


def run_portfolios(held, returns, weighting=None, bps=None, hold_flat=frozenset()):
    weighting = cfg.WEIGHTING if weighting is None else weighting
    bps = cfg.TRANSACTION_COST_BPS if bps is None else bps
    exits, flat_used, stops = [], [], []

    flat = {}
    for x in held.itertuples():
        months = holding_months(x.formation_date)
        h = returns.by_permno.get(x.permno)
        if h is None or x.formation_date.to_period("M") not in h.index:
            stops.append(f"No return row on the formation date: {x.permno} {x.formation_date.date()}")
            continue
        w = h[h.index.isin(months)]
        for mth in w.index[w.mthret.isna()]:
            if (x.permno, str(mth)) in hold_flat:
                flat[(x.permno, mth)] = 0.0
                flat_used.append({"formation_date": x.formation_date.date(), "permno": x.permno, "month": str(mth), "treatment": "held flat: no return, not an exit"})
            else:
                stops.append(f"Unexpected null return: {x.permno} {mth} on the {x.formation_date.year} list")
        last = w.index.max() if len(w) else None
        if last is not None:
            for mth in months:
                if mth < last and mth not in w.index:
                    stops.append(f"Missing row: {x.permno} {mth} on the {x.formation_date.year} list")
        if last is None or last < months[-1]:
            row = h.loc[x.formation_date.to_period("M")] if last is None else w.loc[last]
            if last is not None and row.mthdelflg == cfg.ACTIVE_DELISTING_FLAG:
                stops.append(f"Exit with no delisting flag: {x.permno} {last}")
            exits.append({"formation_date": x.formation_date.date(), "permno": x.permno, "bucket": x.bucket, "exit_type": "delisted on the formation date" if last is None else "mid-period exit",
                          "last_month_with_return": None if last is None else str(last), "delisting_flag": row.mthdelflg})
    if stops:
        raise VariantStop("; ".join(sorted(set(stops))[:12]))

    rows, turnover, counts = [], [], []
    drift = {}
    for d in sorted(held.formation_date.unique()):
        d = pd.Timestamp(d)
        cohort = held[held.formation_date == d]
        months = holding_months(d)
        for name, members in [(b, cohort[cohort.bucket == b]) for b in MAIN] + [("Benchmark", cohort)]:
            counts.append({"formation_date": d.date(), "bucket": name, "names": len(members), "under_minimum": len(members) < cfg.MIN_BUCKET_NAMES})
            if members.empty:
                raise VariantStop(f"{name} is empty on {d.date()}")
            target = target_weights(members, cohort, weighting)
            weights = target.copy()
            series = {}
            for mth in months:
                r = returns.by_month.get(mth, pd.Series(dtype=float))
                extra = {p: v for (p, m2), v in flat.items() if m2 == mth and p in weights.index}
                if extra:
                    r = pd.concat([r, pd.Series(extra)])
                active = weights.index.intersection(r.index)
                if len(active) == 0:
                    raise VariantStop(f"{name} has no holdings left in {mth}")
                weights = weights.loc[active] / weights.loc[active].sum()
                rr = r.loc[active]
                gross = float((weights * rr).sum())
                series[mth] = gross
                weights = weights * (1 + rr) / (1 + gross)
            prior = drift.get(name)
            two_way = cfg.FIRST_PORTFOLIO_TURNOVER if prior is None else float(target.sub(prior, fill_value=0).abs().sum())
            cost = two_way * bps / 10000 if (name in MAIN or cfg.CHARGE_PRIMARY_BENCHMARK) else 0.0
            turnover.append({"formation_date": d.date(), "bucket": name, "names": len(members), "turnover_two_way": two_way, "turnover_one_way": two_way / 2 if prior is not None else two_way, "cost": cost})
            drift[name] = weights
            for i, mth in enumerate(months):
                rows.append({"month": mth, "formation_date": d, "bucket": name, "gross": series[mth], "net": (1 + series[mth]) * (1 - cost) - 1 if i == 0 else series[mth]})
    long = pd.DataFrame(rows)
    wide = long.pivot(index="month", columns="bucket", values=["net", "gross"])
    t = pd.DataFrame(index=wide.index)
    t["month"] = wide.index.astype(str)
    t["formation_date"] = long.drop_duplicates("month").set_index("month").formation_date
    for b in MAIN + ["Benchmark"]:
        t[b] = wide["net"][b]
        t[f"{b}_gross"] = wide["gross"][b]
    t["Spread"] = t.High - t.Low
    t["Spread_gross"] = t.High_gross - t.Low_gross
    return t, pd.DataFrame(turnover), pd.DataFrame(counts), pd.DataFrame(exits), flat_used


# ---------- Phase 6 logic ----------
class Evaluator:
    def __init__(self):
        ff = pd.read_parquet(RAW / "ff_factors.parquet")
        ff["period"] = pd.PeriodIndex(ff.month, freq="M")
        self.ff = ff.set_index("period").sort_index()
        self.cols = [eval_mod.FACTOR_COLUMNS[n] for n in cfg.FACTOR_MODEL]

    def __call__(self, t, turnover, counts):
        f = self.ff.reindex(t.index)
        f[self.cols + ["rf"]] = f[self.cols + ["rf"]].astype(float)
        if f[self.cols + ["rf"]].isna().any().any():
            raise VariantStop("Missing factor values")
        rf = f.rf
        high, bench = eval_mod.stats(t.High, rf), eval_mod.stats(t.Benchmark, rf)
        diff = t.High - t.Benchmark
        rh, rs, rb = eval_mod.regress(t.High - rf, f, self.cols), eval_mod.regress(t.Spread, f, self.cols), eval_mod.regress(diff, f, self.cols)
        by_year = t.groupby("formation_date").agg(months=("High", "size"), High=("High", lambda r: (1 + r).prod() - 1), Benchmark=("Benchmark", lambda r: (1 + r).prod() - 1))
        done = by_year[by_year.months == cfg.HOLDING_MONTHS]
        names = counts.pivot(index="formation_date", columns="bucket", values="names")
        later = turnover[turnover.formation_date > turnover.formation_date.min()]
        row = {"High_alpha_annual": rh["alpha_annual"], "High_alpha_t": rh["alpha_t"], "High_minus_Benchmark_annual": diff.mean() * 12, "High_sharpe": high["sharpe"], "Benchmark_sharpe": bench["sharpe"],
               "High_CAGR": high["CAGR"], "Benchmark_CAGR": bench["CAGR"], "High_minus_Benchmark_alpha": rb["alpha_annual"], "High_minus_Benchmark_alpha_t": rb["alpha_t"],
               "information_ratio": diff.mean() * 12 / (diff.std() * 12 ** 0.5), "Spread_annual": t.Spread.mean() * 12, "Spread_alpha_annual": rs["alpha_annual"], "Spread_alpha_t": rs["alpha_t"],
               "High_beats_Benchmark_years": int((done.High > done.Benchmark).sum()), "complete_years": len(done), "High_turnover_two_way": later[later.bucket == "High"].turnover_two_way.mean()}
        for b in MAIN + ["Benchmark"]:
            row[f"{b}_names_median"] = float(names[b].median())
            row[f"{b}_names_min"] = int(names[b].min())
        row["High_dates_under_minimum"] = int((names.High < cfg.MIN_BUCKET_NAMES).sum())
        row["Low_dates_under_minimum"] = int((names.Low < cfg.MIN_BUCKET_NAMES).sum())
        subs = []
        for a, b in cfg.SUBPERIODS:
            w = t.loc[pd.Period(a, "M"):pd.Period(b, "M")]
            fw, rw = f.loc[w.index], rf.loc[w.index]
            d2 = w.High - w.Benchmark
            ra, rc = eval_mod.regress(w.High - rw, fw, self.cols), eval_mod.regress(w.Spread, fw, self.cols)
            subs.append({"period": f"{a} to {b}", "months": len(w), "High_alpha_annual": ra["alpha_annual"], "High_alpha_t": ra["alpha_t"], "High_minus_Benchmark_annual": d2.mean() * 12,
                         "High_sharpe": eval_mod.stats(w.High, rw)["sharpe"], "Benchmark_sharpe": eval_mod.stats(w.Benchmark, rw)["sharpe"], "Spread_alpha_annual": rc["alpha_annual"], "Spread_alpha_t": rc["alpha_t"]})
        return row, subs


# ---------- Variant inputs ----------
def eight_signal_scores(fund):
    d = scores_mod.compute_scores(fund)
    d["score_type"] = "nine"
    no_liquidity = d.F_SCORE.isna() & d.F_DLIQUID.isna() & d[EIGHT_SIGNALS].notna().all(axis=1)
    d.loc[no_liquidity, "F_SCORE"] = d.loc[no_liquidity, EIGHT_SIGNALS].sum(axis=1)
    d.loc[no_liquidity, "score_type"] = "eight"
    return d


def build_buffer_universe(db, buffer_rule):
    """Rebuild with the headline's steps, changing only who is on each list."""
    m = universe_mod.pull_formation_month(db)
    priced = m[universe_mod.eligible_mask(m) & m.seccap.notna() & ~m.stopped_trading]
    company = priced.groupby(["formation_date", "permco"], as_index=False).seccap.sum().rename(columns={"seccap": "mktcap"})
    company = company.sort_values(["formation_date", "mktcap", "permco"], ascending=[True, False, True])
    company["rank"] = company.groupby("formation_date").cumcount() + 1
    held = (priced.sort_values(["formation_date", "permco", "seccap", "permno"], ascending=[True, True, False, True]).drop_duplicates(["formation_date", "permco"]).drop(columns="seccap"))

    def finish(members):
        u = members.merge(held, on=["formation_date", "permco"], how="left", validate="1:1")
        u, _ = universe_mod.attach_gvkey(u, db)
        u, _, _ = universe_mod.apply_sibling_links(u, m, db)
        u, _ = universe_mod.attach_sector(u, db)
        return universe_mod.set_included(u)

    plain = finish(company[company["rank"] <= cfg.UNIVERSE_SIZE])
    current, rows = set(), []
    if cfg.BUFFER_FIRST_LIST != "top_500":
        raise ValueError(cfg.BUFFER_FIRST_LIST)
    for i, (d, g) in enumerate(company.groupby("formation_date")):
        g = g.set_index("permco")
        if i == 0:
            chosen = set(g.index[g["rank"] <= cfg.UNIVERSE_SIZE])
        else:
            chosen = set(g.index[g["rank"] <= buffer_rule["entry_rank"]]) | {p for p in current if p in g.index and g["rank"][p] <= buffer_rule["exit_rank"]}
        rows.append({"formation_date": d.date(), "list_size": len(chosen), "entered": len(chosen - current), "left": len(current - chosen), "rank_above_500_kept": int((g.loc[list(chosen), "rank"] > cfg.UNIVERSE_SIZE).sum())})
        current = chosen
        if i == 0:
            frames = []
        frames.append(g.loc[list(chosen)].reset_index())
    members = pd.concat(frames, ignore_index=True)
    return plain, finish(members), pd.DataFrame(rows)


def pull_quarterly(db, overwrite):
    """New raw files. Write-once, like 02_pull_data.py."""
    fundq, filed = RAW / "comp_fundq.parquet", RAW / "comp_co_filedate_quarterly.parquet"
    if fundq.exists() and filed.exists() and not overwrite:
        return pd.read_parquet(fundq), pd.read_parquet(filed), "read existing raw files"
    gv = sorted(pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey"]).gvkey.unique())
    keys = ", ".join(f"'{g}'" for g in gv)
    have = set(db.describe_table("comp", "fundq").name)
    need = cfg.QTR_PULL_FIELDS + list(cfg.FUNDA_FILTERS)
    if not set(need) <= have:
        raise RuntimeError(f"comp.fundq lacks {set(need) - have}")
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    start = f"{cfg.FIRST_FUNDAMENTAL_FY}-01-01"
    q = db.raw_sql(f"select {', '.join(cfg.QTR_PULL_FIELDS)} from comp.fundq where {filters} and gvkey in ({keys}) and datadate >= '{start}'", date_cols=["datadate"])
    new_types = [t for t in cfg.QTR_FILING_SRCTYPES if t not in cfg.FILING_SRCTYPES]
    types = ", ".join(f"'{t}'" for t in new_types)
    f = db.raw_sql(f"select {', '.join(cfg.QTR_FILING_PULL_FIELDS)} from comp.co_filedate where srctype in ({types}) and gvkey in ({keys}) and datadate >= '{start}'", date_cols=["datadate", "filedate"])
    q.to_parquet(fundq, index=False)
    f.to_parquet(filed, index=False)
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log = pd.DataFrame([{"table": "comp_fundq", "pull_timestamp_utc": now, "rows": len(q), "unique_ids": q.gvkey.nunique(), "date_min": q.datadate.min().date(), "date_max": q.datadate.max().date()},
                        {"table": "comp_co_filedate_quarterly", "pull_timestamp_utc": now, "rows": len(f), "unique_ids": f.gvkey.nunique(), "date_min": f.filedate.min().date(), "date_max": f.filedate.max().date()}])
    log.to_csv(OUT / "pull_log_quarterly.csv", index=False)
    return q, f, f"pulled {len(q)} quarter rows and {len(f)} filing rows"


def profitability_screen(held, q, filings_q):
    if cfg.QTR_SELECTION != "latest_four_consecutive_by_datadate" or cfg.QTR_UNCONFIRMED_RULE != "fail" or cfg.PROFITABILITY_SCREEN_SCOPE != "all_scored":
        raise ValueError("Screen settings differ from what this script implements")
    filings_k = pd.read_parquet(RAW / "comp_co_filedate.parquet", columns=["gvkey", "srctype", "datadate", "filedate"])
    f = pd.concat([filings_q[["gvkey", "srctype", "datadate", "filedate"]], filings_k])
    f = f[f.srctype.isin(cfg.QTR_FILING_SRCTYPES) & (f.filedate > f.datadate)]
    first = f.groupby(["gvkey", "datadate"]).filedate.min().rename("filed").reset_index()
    e = cfg.QTR_EARNINGS_FIELD
    q = q.copy()
    q[e] = q[e].astype(float)
    q["has_e"] = q[e].notna()
    q = q.sort_values(["gvkey", "datadate", "has_e", "fyearq"]).drop_duplicates(["gvkey", "datadate"], keep="last")
    q = q.merge(first, on=["gvkey", "datadate"], how="left")
    q["avail"] = q.filed.fillna(q.datadate + pd.to_timedelta(cfg.FALLBACK_LAG_DAYS, unit="D"))
    q["month_no"] = q.datadate.dt.year * 12 + q.datadate.dt.month
    by = dict(tuple(q.sort_values(["gvkey", "datadate"]).groupby("gvkey")))
    results = []
    for r in held.itertuples():
        k = by.get(r.gvkey)
        a = k[k.avail <= r.formation_date].tail(4) if k is not None else None
        if a is None or len(a) < 4:
            results.append("unconfirmed: fewer than 4 quarters")
        elif not (a.month_no.diff().dropna() == 3).all():
            results.append("unconfirmed: quarters not consecutive")
        elif a[e].isna().any():
            results.append("unconfirmed: null earnings")
        elif (r.formation_date.year * 12 + r.formation_date.month) - a.month_no.iloc[-1] > cfg.MAX_SCORE_AGE_MONTHS:
            results.append("unconfirmed: latest quarter too old")
        elif a[e].sum() > 0 and a[e].iloc[-1] > 0:
            results.append("pass")
        else:
            results.append("failed: earnings not positive")
    return pd.Series(results, index=held.index)


def save(label, formation, t, turnover, counts, exits, extra=None):
    d = OUT / label
    d.mkdir(parents=True, exist_ok=True)
    formation.to_parquet(d / "formation.parquet", index=False)
    x = t.copy()
    x.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    x.insert(1, "variant", label)
    x.to_csv(d / "portfolio_returns.csv", index=False)
    turnover.to_csv(d / "portfolio_turnover.csv", index=False)
    counts.to_csv(d / "bucket_counts.csv", index=False)
    exits.to_csv(d / "portfolio_exits.csv", index=False)
    for name, frame in (extra or {}).items():
        frame.to_csv(d / name, index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Replace the quarterly raw files.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    universe = pd.read_parquet(CLEAN / "universe.parquet")
    fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
    fscores = pd.read_parquet(CLEAN / "fscores.parquet")
    fscores["score_type"] = "nine"
    formation = pd.read_parquet(CLEAN / "formation.parquet")
    returns, evaluate = Returns(), Evaluator()
    db = wrds.Connection(wrds_username=universe_mod.wrds_username())

    # --- Headline through this engine must reproduce the published files exactly ---
    a = align(universe, fscores)
    a_held = a[a.scored].copy()
    pub = formation[formation.scored]
    key = ["formation_date", "permno"]
    same = a_held[key + ["F_SCORE", "fyear"]].sort_values(key).reset_index(drop=True).astype({"F_SCORE": float}).equals(pub[key + ["F_SCORE", "fyear"]].sort_values(key).reset_index(drop=True).astype({"F_SCORE": float}))
    if not same:
        sys.exit("STOP: this script's alignment does not reproduce formation.parquet")
    a_held["bucket"] = buckets(a_held)
    base_t, base_turn, base_counts, base_exits, _ = run_portfolios(a_held, returns)
    published = pd.read_csv(TABLES / "portfolio_returns.csv")
    published.index = pd.PeriodIndex(published.month, freq="M")
    cols = [c for b in MAIN + ["Benchmark", "Spread"] for c in (b, f"{b}_gross")]
    gap = (base_t[cols] - published[cols]).abs().max().max()
    if gap > 1e-12:
        sys.exit(f"STOP: this script's engine differs from portfolio_returns.csv by {gap}")
    print(f"headline reproduced: largest monthly gap {gap:.2e}", flush=True)

    results, stopped, notes, thin, log_rows = [], {}, {}, [], []

    def record(label, change, held, weighting=None, bps=None, hold_flat=frozenset(), extra=None, note="", included_rows=None, drop_reason="no score known by the date, or score too old"):
        print(f"running {label}", flush=True)
        try:
            t, turn, counts, exits, flat = run_portfolios(held, returns, weighting, bps, hold_flat)
            row, subs = evaluate(t, turn, counts)
        except VariantStop as e:
            stopped[label] = str(e)
            print(f"STOP {label}: {e}", flush=True)
            return
        save(label, held, t, turn, counts, exits, extra)
        results.append({"variant": label, "change": change, **row, "subs": subs, "exits": int((exits.exit_type == "mid-period exit").sum()) if len(exits) else 0})
        if flat:
            note += f" Held flat: {flat}."
        notes[label] = note
        included = int(universe.included.sum()) if included_rows is None else included_rows
        log_rows.append({"universe_label": cfg.UNIVERSE_LABEL, "variant": label, "held_rows": len(held), "unique_companies": held.permco.nunique(), "unique_gvkeys": held.gvkey.nunique(), "first_formation": held.formation_date.min().date(), "last_formation": held.formation_date.max().date(),
                         "first_month": t.month.iloc[0], "last_month": t.month.iloc[-1], "months": len(t), "included_rows": included, "rows_dropped": included - len(held), "drop_reason": drop_reason, "mid_period_exits": int((exits.exit_type == "mid-period exit").sum()) if len(exits) else 0})
        small = counts[counts.under_minimum]
        for r in small.itertuples():
            thin.append({"variant": label, "formation_date": r.formation_date, "bucket": r.bucket, "names": r.names})

    record("headline", "None", a_held, note="Same numbers as the published headline; files here are a copy for comparison.")

    settings = cfg.ROBUSTNESS
    v = a_held.copy()
    v["bucket"] = buckets(v, high=settings["high_cutoff_7plus"]["HIGH_SCORES"])
    record("high_cutoff_7plus", f"High = scores {settings['high_cutoff_7plus']['HIGH_SCORES']}; Middle = 5-6", v)

    b = a_held.merge(formation[key + ["in_version_b"]], on=key)
    b = b[b.in_version_b].copy()
    record("value_filter_B", "Only the cheapest third by book-to-market (USD rows)", b, note="The closest variant to Piotroski's sample, which studied cheap stocks.", drop_reason="no valid score, or outside the cheapest third, or not USD")

    record("cap_weighted", "Weights by formation market cap, then drift, in every bucket and the benchmark", a_held, weighting=settings["cap_weighted"]["WEIGHTING"])
    record("sector_neutral", "Each bucket holds the benchmark's sector weights, equal weight within sector", a_held, weighting=settings["sector_neutral"]["WEIGHTING"])

    lag = settings["lag_90_days"]["FALLBACK_LAG_DAYS"]
    s90 = fscores.copy()
    fb = s90.avail_source == "fallback"
    s90.loc[fb, "avail_date"] = s90.loc[fb, "datadate"] + pd.to_timedelta(lag, unit="D")
    v = align(universe, s90)
    v = v[v.scored].copy()
    v["bucket"] = buckets(v)
    changed = v.merge(a_held[key + ["fyear"]], on=key, how="outer", suffixes=("", "_base"), indicator=True)
    lag_diff = int((changed._merge != "both").sum() + (changed.fyear != changed.fyear_base)[changed._merge == "both"].sum())
    record("lag_90_days", f"Fallback availability = year-end + {lag} days, not {cfg.FALLBACK_LAG_DAYS}", v, note=f"Rows that differ from the headline: {lag_diff}.")

    record("cost_25bps", f"{settings['cost_25bps']['TRANSACTION_COST_BPS']} bps a side, not {cfg.TRANSACTION_COST_BPS}", a_held, bps=settings["cost_25bps"]["TRANSACTION_COST_BPS"])

    s8 = eight_signal_scores(fund)
    v = align(universe, s8)
    v = v[v.scored].copy()
    v["bucket"] = buckets(v)
    n8 = int((v.score_type == "eight").sum())
    mix = v[v.score_type == "eight"].bucket.value_counts().to_dict()
    record("eight_signal_no_liquidity", "Firms with no liquidity signal scored out of 8 (High 8, Low 0-3, Middle 4-7); the benchmark gains those firms", v, hold_flat=hold_flat_cases("eight_signal_no_liquidity", cfg.EIGHT_SIGNAL_NULL_RETURN_RULE),
           note=f"{n8} list rows use 8 signals: {mix}. Set after headline returns. Null return rule `{cfg.EIGHT_SIGNAL_NULL_RETURN_RULE}` for {HOLD_FLAT_LABEL}.")

    plain, buffered, size = build_buffer_universe(db, settings["universe_buffer"]["UNIVERSE_BUFFER"])
    u_key = ["formation_date", "permno", "permco", "gvkey", "rank", "gsector", "included"]
    pl = plain[u_key].sort_values(key).reset_index(drop=True)
    ub = universe[u_key].sort_values(key).reset_index(drop=True)
    if not (len(pl) == len(ub) and (pl.astype(object).astype(str) == ub.astype(object).astype(str)).all().all()):
        sys.exit("STOP: the buffer's rebuild path does not reproduce the headline universe")
    print("headline universe reproduced through the buffer path", flush=True)
    cols_u = ["formation_date", "permno", "permco", "gvkey", "mktcap", "rank", "gsector", "included"]
    (OUT / "universe_buffer").mkdir(parents=True, exist_ok=True)
    buffered[cols_u].to_parquet(OUT / "universe_buffer" / "universe.parquet", index=False)
    v = align(buffered, fscores)
    per = v.groupby("formation_date").agg(included=("permno", "size"), scored=("scored", "sum")).reset_index()
    per["formation_date"] = per.formation_date.dt.date
    size = size.merge(per, on="formation_date")
    v = v[v.scored].copy()
    v["bucket"] = buckets(v)
    record("universe_buffer", f"Enter at rank <= {settings['universe_buffer']['UNIVERSE_BUFFER']['entry_rank']}, stay until rank > {settings['universe_buffer']['UNIVERSE_BUFFER']['exit_rank']}; first list is the top 500", v, hold_flat=hold_flat_cases("universe_buffer", cfg.BUFFER_NULL_RETURN_RULE), included_rows=int(buffered.included.sum()),
           extra={"list_sizes.csv": size}, note=f"List size {size.list_size.min()}-{size.list_size.max()} before exclusions; scored names {size.scored.min()}-{size.scored.max()}. "
                                                f"Null return rule `{cfg.BUFFER_NULL_RETURN_RULE}` for {BUFFER_HOLD_FLAT_LABEL}: held flat, not an exit, and sold at its last value at the 2007 rebalance.")

    q, fq, how = pull_quarterly(db, args.overwrite)
    print(how, flush=True)
    v = a_held.copy()
    v["screen"] = profitability_screen(v, q, fq)
    outcome = pd.crosstab(v.bucket, v.screen).reset_index()
    log = v[v.screen != "pass"][["formation_date", "permno", "gvkey", "conm", "F_SCORE", "bucket", "screen"]]
    passed = v[v.screen == "pass"].copy()
    record("profitability_screen", "Require positive trailing-four-quarter and latest-quarter earnings, on every bucket and the benchmark; it overlaps with F_ROA", passed,
           extra={"screen_failures.csv": log, "screen_outcomes.csv": outcome}, note=f"Headline rows {len(v)}: {v.screen.value_counts().to_dict()}. Unconfirmed rows count as failed and are a disclosure.", drop_reason="no valid score, or failed or unconfirmed on the profitability screen")
    db.close()

    # --- Comparison ---
    missing = [k for k in cfg.ROBUSTNESS if k not in [r["variant"] for r in results] and k not in stopped]
    table = pd.DataFrame([{k: x for k, x in r.items() if k != "subs"} for r in results])
    head = table.iloc[0]
    for c in ["High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_annual", "High_sharpe", "Benchmark_CAGR", "Benchmark_sharpe"]:
        table[f"{c}_vs_headline"] = table[c] - head[c]
    table.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    table.to_csv(TABLES / "robustness_comparison.csv", index=False)
    subs = pd.DataFrame([{"universe_label": cfg.UNIVERSE_LABEL, "variant": r["variant"], **s} for r in results for s in r["subs"]])
    subs.to_csv(TABLES / "robustness_subperiods.csv", index=False)
    thin_df = pd.DataFrame(thin, columns=["variant", "formation_date", "bucket", "names"])
    thin_df.to_csv(OUT / "thin_buckets.csv", index=False)
    log_df = pd.DataFrame(log_rows)
    log_df.to_csv(ROOT / "output" / "logs" / "robustness_log.csv", index=False)

    show = table[["variant", "High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_annual", "High_sharpe", "Benchmark_sharpe", "High_CAGR", "Benchmark_CAGR", "Spread_alpha_annual", "Spread_alpha_t"]]
    names = table[["variant", "High_names_median", "High_names_min", "High_dates_under_minimum", "Middle_names_median", "Low_names_median", "Low_names_min", "Low_dates_under_minimum", "Benchmark_names_median", "Benchmark_names_min"]]
    L = [f"# Robustness: {cfg.UNIVERSE_LABEL}\n",
         "One setting changes in each row. All figures are net of costs, June 2005 to December 2025; the 2025 portfolio is partial (7 of 12 months). The headline stays the headline whatever these show. "
         "The variant definitions were set after headline returns existed. Earlier variant runs, whose results by the coordinator's record reached no one but their authors, existed before two later rules were settled: "
         "the Comverse hold-flat rule and the instruction to use the quantile boundary for version B.\n",
         eval_mod.GLOSSARY + "- **Variant:** a rerun with one setting changed.\n",
         f"Results reported: {len(results) - 1} of {len(cfg.ROBUSTNESS)} variants. Stopped: {stopped or 'none'}. Not run: {missing or 'none'}.\n",
         "## Comparison\n", md_table(show, 4), "\n## Names per bucket\n", md_table(names, 1),
         f"\nBuckets under {cfg.MIN_BUCKET_NAMES} names are flagged. Thin buckets make Low and the spread noisy. Every case is in `thin_buckets.csv`: {len(thin_df)} bucket-dates, {thin_df.groupby('variant').size().to_dict()}.\n",
         "\n## Subperiods\n", md_table(subs.drop(columns="universe_label"), 3),
         "\n## Rows and companies\n", md_table(log_df.drop(columns="universe_label")), "\nAlso in `output/logs/robustness_log.csv`.\n",
         "\n## What each variant changed\n"]
    L += [f"- **{r['variant']}**: {r['change']}. {notes[r['variant']]} Mid-period exits: {r['exits']}." for r in results]
    (OUT / "robustness_report.md").write_text("\n".join(L), encoding="utf-8")

    print(show.round(4).to_string(index=False))
    print(names.to_string(index=False))
    print("stopped:", stopped, "missing:", missing)
    sys.exit(1 if stopped or missing else 0)


if __name__ == "__main__":
    main()
