"""
Labelled extension, Stage 2: hold the 2025 portfolio through May 2026 (config.EXTENSION_2026; CLAUDE.md section 8d).

CRSP returns through RETURNS_END, Compustat comp.secm trt1m after. No new rebalance or cost. Separate from the headline.
secstat is today's status, not dated, so it is never used here.

Reads:  data/clean/formation.parquet, data/raw/crsp_msf_v2.parquet, comp_secm_extension.parquet, ff_factors.parquet,
        output/tables/portfolio_returns.csv, portfolio_turnover.csv, output/extension_2026/security_map.csv (the last and the secm file come from 09a_extension_pull.py)
Output: output/extension_2026/ only: results.md, returns.csv, performance.csv, regressions.csv, subperiods.csv, year_by_year.csv,
        jan_may_2026.csv, sensitivities.csv
Exit code is 1 if the run stops or a headline file changes.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / cfg.EXTENSION_2026["label"]
RAW = ROOT / "data" / "raw"
TABLES = ROOT / "output" / "tables"
MAIN = ["High", "Middle", "Low", "Benchmark"]
LONG = MAIN + ["RSP", "SPY"]
EXIT_GAP_BP = 494  # sensitivity label: 95th percentile of absolute exit gaps in validation.md

DISCLOSURE = ("The January-May 2026 extension uses Compustat monthly returns because CRSP data on this account ends in December 2025. It is reported separately and does not change any headline figure. "
              "On 15,752 earlier held months, Compustat agrees with CRSP within 1% on 99.96%, but it differs at spin-offs (up to 8.4 points on a single stock) and at delistings. "
              "Two spin-offs (Becton Dickinson, Comcast) and two acquisitions (Hologic, Coterra) fall in the window. No bankruptcies do.")


class Stop(Exception):
    """Any null, missing row or exit the rules do not name."""


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


port = load("06_portfolios.py", "port")
ev = load("07_evaluate.py", "ev")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def headline_files():
    named = [ROOT / "config.py", ROOT / "CLAUDE.md", ROOT / "output" / "writeup.md", ROOT / "output" / "checkpoint3_results.md"]
    named += [ROOT / f for f in ["01_build_universe.py", "02_pull_data.py", "03_clean.py", "04_scores.py", "05_align.py", "06_portfolios.py", "07_evaluate.py", "08_robustness.py"]]
    groups = list(RAW.glob("*")) + list((ROOT / "data" / "clean").glob("*")) + list(TABLES.glob("*")) + list((ROOT / "output" / "charts").glob("*")) + list((ROOT / "output" / "logs").glob("*")) + list((ROOT / "output" / "robustness").rglob("*"))
    return sorted({p for p in named + groups if p.is_file()})


def find_permno(map_df, name):
    hit = map_df[map_df.name.str.upper().str.contains(name.upper(), regex=False)]
    if len(hit) != 1:
        raise Stop(f"{name} matches {len(hit)} held names")
    return int(hit.permno.iloc[0])


def extend(end_weights, secm_by_month, exit_after, departed, overrides=None):
    """Five Compustat months from December 2025 weights. A name stops by rule, never because a row is or is not there."""
    overrides = overrides or {}
    series = {}
    weights = end_weights.copy()
    for mth in pd.period_range(pd.Period(cfg.RETURNS_END, "M") + 1, pd.Period(cfg.EXTENSION_2026["end"], "M"), freq="M"):
        # Names that left in the prior month, by rule, drop out here; their value goes pro rata, as DELISTING_RULE says
        live = [p for p in weights.index if p not in departed and not (p in exit_after and mth > exit_after[p])]
        weights = weights.loc[live]
        rets = secm_by_month[mth]
        missing = [p for p in live if p not in rets.index]
        nulls = [p for p in live if p in rets.index and pd.isna(rets[p])]
        if missing or nulls:
            raise Stop(f"{mth}: missing rows {missing}; null returns {nulls}")
        r = rets.loc[live].astype(float).copy()
        for (p, m2), v in overrides.items():
            if m2 == mth and p in r.index:
                r[p] = v
        weights = weights / weights.sum()
        gross = float((weights * r).sum())
        series[mth] = gross
        weights = weights * (1 + r) / (1 + gross)
    return pd.Series(series), weights


def main():
    x = cfg.EXTENSION_2026
    if x["return_field"] != "trt1m" or cfg.DELISTING_RULE != "reinvest_pro_rata":
        sys.exit("EXTENSION_2026 differs from what this script implements")
    before = {p: sha(p) for p in headline_files()}

    fm = pd.read_parquet(ROOT / "data/clean/formation.parquet")
    last = fm.formation_date.max()
    held = fm[(fm.formation_date == last) & fm.scored].copy()
    held["F_SCORE"] = held.F_SCORE.astype(int)
    held["bucket"] = held.F_SCORE.map(port.bucket_of)
    map_df = pd.read_csv(OUT / "security_map.csv", dtype={"gvkey": str, "iid": str, "list_gvkey": str})
    if set(map_df.permno) != set(held.permno) or map_df.iid.isna().any() or map_df.duplicated(["gvkey", "iid"]).any():
        sys.exit("STOP: security_map.csv does not map each held name once")

    r = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthdelflg"])
    r = r[r.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    r["month"] = r.mthcaldt.dt.to_period("M")
    r["mthret"] = r.mthret.astype(float)
    crsp = {m: g.dropna(subset=["mthret"]).set_index("permno").mthret for m, g in r.groupby("month")}

    s = pd.read_parquet(RAW / "comp_secm_extension.parquet", columns=["gvkey", "iid", "datadate", "trt1m", "prccm", "ajexm", "conm"])
    s["month"] = s.datadate.dt.to_period("M")
    for c in ["trt1m", "prccm", "ajexm"]:
        s[c] = s[c].astype(float)
    s = s.sort_values(["gvkey", "iid", "month"])
    s["adj"] = s.prccm / s.ajexm
    s["price_only"] = s.groupby(["gvkey", "iid"]).adj.pct_change(fill_method=None)
    s["ret"] = s.trt1m / 100
    joined = map_df[["permno", "gvkey", "iid"]].merge(s, on=["gvkey", "iid"])
    window = pd.period_range(pd.Period(cfg.RETURNS_END, "M") + 1, pd.Period(x["end"], "M"), freq="M")
    secm_by_month = {m: joined[joined.month == m].set_index("permno").ret for m in window}

    # Names that had already left in CRSP: their final return is CRSP's
    months_2025 = port.holding_months(last)
    last_row = r[r.permno.isin(held.permno)].sort_values("mthcaldt").groupby("permno").agg(last_month=("month", "last"), flag=("mthdelflg", "last"))
    departed = set(last_row[(last_row.last_month < months_2025[-1]) | (last_row.flag != cfg.ACTIVE_DELISTING_FLAG)].index)
    exit_after = {find_permno(map_df, n): pd.Period(m, "M") for n, m in x["exits"].items()}
    spin = {find_permno(map_df, n): pd.Period(m, "M") for n, m in x["report_spinoff_months"].items()}

    # CRSP-to-December weights; the published June-December series must come back exactly
    published = pd.read_csv(TABLES / "portfolio_returns.csv")
    published.index = pd.PeriodIndex(published.month, freq="M")
    ends = {}
    worst = 0.0
    for b in MAIN:
        members = held if b == "Benchmark" else held[held.bucket == b]
        series, w = port.buy_and_hold(members.permno.tolist(), months_2025, crsp)
        worst = max(worst, float((series - published.loc[months_2025, f"{b}_gross"]).abs().max()))
        ends[b] = w
    if worst > 1e-12:
        sys.exit(f"STOP: June-December 2025 differs from the published gross series by {worst}")
    print(f"published Jun-Dec 2025 reproduced: largest gap {worst:.1e}", flush=True)

    funds = {}
    for t, (gv, iid) in x["benchmark_lines"].items():
        f = s[(s.gvkey == gv) & (s.iid == iid)].set_index("month").ret
        if not set(window) <= set(f.dropna().index):
            sys.exit(f"STOP: {t} is missing a month")
        funds[t] = f.loc[window]

    def build(overrides=None):
        rows = {}
        for b in MAIN:
            rows[b], _ = extend(ends[b], secm_by_month, exit_after, departed, overrides)
        return pd.DataFrame(rows)

    try:
        ext = build()
    except Stop as e:
        (OUT / "STOPPED.md").write_text(f"# Stopped\n\n{cfg.UNIVERSE_LABEL}\n\n{e}\n", encoding="utf-8")
        print("STOP:", e)
        sys.exit(1)

    def full_series(ext_table):
        p = published[MAIN + ["RSP", "SPY", "formation_date"]].copy()
        add = ext_table.copy()
        for t in funds:
            add[t] = funds[t]
        add["formation_date"] = str(last.date())
        p = pd.concat([p, add])
        p["Spread"] = p.High - p.Low
        return p

    ff = pd.read_parquet(RAW / "ff_factors.parquet")
    ff["period"] = pd.PeriodIndex(ff.month, freq="M")
    ff = ff.set_index("period").sort_index()
    fcols = [ev.FACTOR_COLUMNS[n] for n in cfg.FACTOR_MODEL]

    def factors_for(idx):
        f = ff.reindex(idx)[fcols + ["rf"]].astype(float)
        if f.isna().any().any():
            sys.exit("STOP: missing factor values")
        return f

    def perf_table(p, label):
        f = factors_for(p.index)
        out = []
        for n in LONG:
            st = ev.stats(p[n], f.rf)
            out.append({"period": label, "portfolio": n, "months": st["months"], "CAGR": st["CAGR"], "volatility": st["volatility"], "sharpe": st["sharpe"], "max_drawdown": st["max_drawdown"]})
        return out

    def regress_table(p, label):
        f = factors_for(p.index)
        rows = [("High minus risk-free", p.High - f.rf), ("Spread", p.Spread), ("High minus Benchmark", p.High - p.Benchmark), ("Low minus risk-free", p.Low - f.rf), ("Benchmark minus risk-free", p.Benchmark - f.rf)]
        return [{"period": label, "series": n, **ev.regress(y, f, fcols)} for n, y in rows]

    def versus(p, label):
        d = p.High - p.Benchmark
        te = d.std() * 12 ** 0.5
        return {"period": label, "months": len(p), "High_minus_Benchmark_annual": d.mean() * 12, "CAGR_difference": ev.cagr(p.High) - ev.cagr(p.Benchmark), "tracking_error": te, "information_ratio": d.mean() * 12 / te}

    head = published[MAIN + ["RSP", "SPY", "formation_date"]].copy()
    head["Spread"] = head.High - head.Low
    full = full_series(ext)
    expected = pd.period_range(f"{cfg.FIRST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", pd.Period(x["end"], "M"), freq="M")
    if list(full.index) != list(expected):
        sys.exit(f"STOP: expected {len(expected)} months, {expected[0]} to {expected[-1]}; got {len(full)}")
    H_LABEL, E_LABEL = "Headline: June 2005 to December 2025 (CRSP)", "Extension: June 2005 to May 2026 (CRSP, then Compustat from January 2026)"

    perf = pd.DataFrame(perf_table(head, H_LABEL) + perf_table(full, E_LABEL))
    vs = pd.DataFrame([versus(head, H_LABEL), versus(full, E_LABEL)])
    regs = pd.DataFrame(regress_table(head, H_LABEL) + regress_table(full, E_LABEL))
    subs = []
    for label, a, b, src in [("Headline", cfg.SUBPERIODS[0][0], cfg.SUBPERIODS[0][1], head), ("Headline", cfg.SUBPERIODS[1][0], cfg.SUBPERIODS[1][1], head), ("Extension", cfg.SUBPERIODS[1][0], x["end"][:7], full)]:
        w = src.loc[pd.Period(a, "M"):pd.Period(b, "M")]
        f = factors_for(w.index)
        rh, rs = ev.regress(w.High - f.rf, f, fcols), ev.regress(w.Spread, f, fcols)
        rd = ev.regress(w.High - w.Benchmark, f, fcols)
        subs.append({"run": label, "period": f"{a} to {b}", "months": len(w), "High_CAGR": ev.cagr(w.High), "Low_CAGR": ev.cagr(w.Low), "Benchmark_CAGR": ev.cagr(w.Benchmark), "High_sharpe": ev.stats(w.High, f.rf)["sharpe"], "Benchmark_sharpe": ev.stats(w.Benchmark, f.rf)["sharpe"],
                     "High_excess_annual": (w.High - w.Benchmark).mean() * 12, "Spread_annual": w.Spread.mean() * 12, "High_alpha_annual": rh["alpha_annual"], "High_alpha_t": rh["alpha_t"], "High_minus_Benchmark_alpha": rd["alpha_annual"], "High_minus_Benchmark_alpha_t": rd["alpha_t"], "Spread_alpha_annual": rs["alpha_annual"], "Spread_alpha_t": rs["alpha_t"]})
    subs = pd.DataFrame(subs)

    def comp(v):
        return (1 + v).prod() - 1
    yr = full.groupby("formation_date").agg(months=("High", "size"), High=("High", comp), Low=("Low", comp), Middle=("Middle", comp), Benchmark=("Benchmark", comp)).reset_index()
    yr["Spread"] = yr.High - yr.Low
    yr["High_minus_Benchmark"] = yr.High - yr.Benchmark
    yr["High_beats_Benchmark"] = yr.High > yr.Benchmark
    yr["holding_year"] = [f"{d[:4]}-{str(int(d[:4]) + 1)[2:]}" for d in yr.formation_date.astype(str)]
    yr.loc[yr.holding_year == "2025-26", "holding_year"] = "2025-26 (CRSP to Dec 2025, Compustat Jan-May 2026)"
    if (yr.months != cfg.HOLDING_MONTHS).any():
        sys.exit("STOP: a holding year is not complete")
    hit = int(yr.High_beats_Benchmark.sum())
    y_out = yr[["holding_year", "months", "High", "Middle", "Low", "Spread", "Benchmark", "High_minus_Benchmark", "High_beats_Benchmark"]]

    jm = full.loc[window, LONG + ["Spread"]]
    jm_total = pd.DataFrame([{"portfolio": n, "jan_may_2026": comp(jm[n]), **{str(m): jm.loc[m, n] for m in window}} for n in LONG + ["Spread"]])
    jm_total.loc[jm_total.portfolio == "Spread", "jan_may_2026"] = comp(jm.High) - comp(jm.Low)

    # Sensitivities, reported only
    bucket_of = held.set_index("permno").bucket
    price_only = joined.set_index(["permno", "month"]).price_only
    spin_override = {(p, m): float(price_only[(p, m)]) for p, m in spin.items()}
    exit_ret = {(p, m): float(secm_by_month[m][p]) for p, m in exit_after.items()}
    runs = [("Base", None), ("Spin-off months at price-only return", spin_override),
            (f"Hologic and Coterra final returns +{EXIT_GAP_BP} bp", {k: v + EXIT_GAP_BP / 10000 for k, v in exit_ret.items()}),
            (f"Hologic and Coterra final returns -{EXIT_GAP_BP} bp", {k: v - EXIT_GAP_BP / 10000 for k, v in exit_ret.items()})]
    sens = []
    for label, o in runs:
        p = full_series(build(o))
        f = factors_for(p.index)
        rh, rs = ev.regress(p.High - f.rf, f, fcols), ev.regress(p.Spread, f, fcols)
        w = p.loc[pd.Period(cfg.SUBPERIODS[1][0], "M"):]
        fw = f.loc[w.index]
        r2 = ev.regress(w.High - fw.rf, fw, fcols)
        y = p.groupby("formation_date").agg(H=("High", comp), B=("Benchmark", comp))
        sens.append({"run": label, "High_jan_may": comp(p.High.loc[window]), "Low_jan_may": comp(p.Low.loc[window]), "Benchmark_jan_may": comp(p.Benchmark.loc[window]), "High_CAGR": ev.cagr(p.High), "Benchmark_CAGR": ev.cagr(p.Benchmark), "High_minus_Benchmark_annual": (p.High - p.Benchmark).mean() * 12,
                     "High_alpha_annual": rh["alpha_annual"], "High_alpha_t": rh["alpha_t"], "Spread_alpha_annual": rs["alpha_annual"], "Spread_alpha_t": rs["alpha_t"], "alpha_2015_on": r2["alpha_annual"], "alpha_2015_on_t": r2["alpha_t"], "hit_years": int((y.H > y.B).sum())})
    sens = pd.DataFrame(sens)

    named = []
    names = map_df.set_index("permno").name
    for p, m in {**spin, **exit_after}.items():
        row = joined[(joined.permno == p) & (joined.month == m)].iloc[0]
        named.append({"name": names[p], "month": str(m), "event": "spin-off (used as given)" if p in spin else "acquisition: final return, then pro rata", "bucket": bucket_of[p], "trt1m_pct": row.trt1m, "price_only_pct": 100 * row.price_only, "rows_after_in_raw": int(((joined.permno == p) & (joined.month > m)).sum()) if p in exit_after else None})
    named = pd.DataFrame(named)

    # Save
    add_label = lambda d: d.assign(universe_label=cfg.UNIVERSE_LABEL)
    z = full[MAIN + ["Spread", "RSP", "SPY", "formation_date"]].copy()
    z.insert(0, "month", z.index.astype(str))
    z["return_source"] = ["Compustat trt1m" if m in window else "CRSP" for m in z.index]
    add_label(z).to_csv(OUT / "returns.csv", index=False)
    add_label(perf).to_csv(OUT / "performance.csv", index=False)
    add_label(regs).to_csv(OUT / "regressions.csv", index=False)
    add_label(subs).to_csv(OUT / "subperiods.csv", index=False)
    add_label(y_out).to_csv(OUT / "year_by_year.csv", index=False)
    add_label(jm_total).to_csv(OUT / "jan_may_2026.csv", index=False)
    add_label(sens).to_csv(OUT / "sensitivities.csv", index=False)

    after = {p: sha(p) for p in before}
    moved = [str(p.relative_to(ROOT)) for p in before if before[p] != after[p]]

    md = ev.md_table
    show_r = ["period", "series", "months", "alpha_annual", "alpha_t", "r_squared"] + [f"beta_{n}" for n in cfg.FACTOR_MODEL]
    L = [f"# Extension to May 2026 (Compustat returns from January 2026): {cfg.UNIVERSE_LABEL}\n",
         f"**Labelled extension, not the headline.** {DISCLOSURE}\n",
         "**Terms.** **CAGR** is the constant yearly growth rate. **Sharpe** is return above the risk-free rate per unit of volatility. **Alpha** is return left after six factors (market, size, value, profitability, investment, momentum), with Newey-West standard errors over "
         f"{cfg.NEWEY_WEST_LAGS} months. A **t-stat** beyond about 2 is treated as significant. A **spin-off** is a company distributing shares of a subsidiary. **bp** is 0.01%.\n",
         "**Mechanics.** The 2025 portfolio keeps its CRSP December 2025 weights and drifts for five more months, with no new rebalance and no new cost. Returns are net of costs through the existing rebalance charges. "
         "Hologic stops after April 2026 and Coterra after May 2026 by rule, with their value going pro rata afterwards. `secstat` is not used. Any other null, missing row or exit stops the run; none occurred. No portfolio is rebalanced in June 2026.\n",
         f"**Headline unchanged:** files hashed before and after this run: {'all identical' if not moved else 'CHANGED: ' + str(moved)}. The June-December 2025 series reproduces the published file to {worst:.1e}.\n",
         "## Performance\n", md(perf, 4), "\n## High against the Benchmark\n", md(vs, 4),
         f"\nHigh beat the Benchmark in **{hit} of {len(yr)} complete holding years**. The headline counted 10 of 20 complete years, with 2025 shown separately as partial.\n",
         "\n## Six-factor regressions, net\n", md(regs[show_r], 3),
         "\n## Subperiods\n", md(subs, 4),
         "\nFor the 2015-06 onward row, the audit's caution about the t-stat applies: Newey-West with 12 lags on this few months overstates significance somewhat, and random portfolios from this universe also averaged a negative alpha in the shorter window. The audit reran that testing on this window: a fair t is about -2.7 to -3.25, and the alpha sits at 1.7% of random portfolios but 12.5% of those keeping High's sector mix (verification/data_audit_post_writeup.md).\n",
         "\n## Year by year\n", md(y_out, 4),
         "\n## January-May 2026 alone\n",
         "**Five months say little.** They are one short window, in a later part of a single holding year, from a different data source, and with no test of significance.\n",
         md(jm_total, 4),
         "\n## Named events\n", md(named, 3),
         "\nBecton Dickinson's and Comcast's spin-off months are used as given. Compustat and CRSP differ at such months, and CRSP cannot check these two. Whether each is a spin-off is from the audit's reading.\n",
         "\n## Sensitivities (reported only; no rule changes)\n", md(sens, 4),
         f"\nPrice-only ignores the distribution altogether, so it is a deliberately harsh lower case for the two spin-off months, not an estimate. The {EXIT_GAP_BP} bp is the 95th percentile of absolute gaps at past exits, from `validation.md`, applied to both final returns at once.\n",
         "\n## Limits\n",
         "- Compustat 2026 rows can be revised, and they cannot be compared with CRSP until CRSP covers 2026.\n- The extended full-period figures mix two sources. Use the headline as the result of record.\n- Adding a few months to a 20-year test can't change much by itself; the new information is only these five months.\n"]
    (OUT / "results.md").write_text("\n".join(L), encoding="utf-8")

    print(perf.drop(columns=[]).round(4).to_string(index=False))
    print(vs.round(4).to_string(index=False))
    print(regs[["period", "series", "alpha_annual", "alpha_t"]].round(4).to_string(index=False))
    print(subs[["run", "period", "months", "High_excess_annual", "High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_alpha", "High_minus_Benchmark_alpha_t", "Spread_alpha_annual", "Spread_alpha_t"]].round(4).to_string(index=False))
    print(jm_total[["portfolio", "jan_may_2026"]].round(4).to_string(index=False))
    print(y_out.tail(2).round(4).to_string(index=False))
    print(named.to_string(index=False))
    print(sens.round(4).T.to_string())
    print(f"hit {hit}/{len(yr)}; departed before 2026 {sorted(departed)}; hashes changed {moved}")
    sys.exit(1 if moved else 0)


if __name__ == "__main__":
    main()
