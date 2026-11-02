"""
Labelled variant long_short_100_100: 100% long High, 100% short Low, on NAV (config.LONG_SHORT_100_100; CLAUDE.md section 8d item 4).

Each June: charge trading costs on both legs, then set long = short = NAV. Within the year the legs drift.
Monthly P&L = L x rH - S x rL + cash x rf - S x fee / 12, with cash = NAV - L + S at the start of the month.

Reads:  output/tables/portfolio_returns.csv, portfolio_turnover.csv, bucket_counts.csv, output/extension_2026/returns.csv, data/raw/ff_factors.parquet
Output: output/long_short_100_100/ only
Exit code is 1 if NAV reaches zero, a check fails or an existing file changes.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
TABLES = ROOT / "output" / "tables"
OUT = ROOT / "output" / cfg.LONG_SHORT_100_100["label"]
BPS = cfg.TRANSACTION_COST_BPS / 10000


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ev = load("07_evaluate.py", "ev")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def guarded_files():
    """Everything in the project except this script's own folder."""
    paths = [p for p in ROOT.glob("*") if p.is_file() and p.name != Path(__file__).name]
    for d in [ROOT / "data", ROOT / "output"]:
        paths += [p for p in d.rglob("*") if p.is_file() and OUT not in p.parents]
    return sorted(p for p in paths if "__pycache__" not in str(p))


class NavStop(Exception):
    pass


def run(inp, fee, reset="annual_at_rebalance", costs=True):
    """inp columns: rH, rL, rf, new_cohort (bool), cost_rate (share of NAV charged at that month's start)."""
    nav, L, S = 1.0, 1.0, 1.0
    rows = []
    for m, x in inp.iterrows():
        start = nav
        cost = 0.0
        if x.new_cohort:
            if costs:
                cost = nav * x.cost_rate
                nav -= cost
            L = S = nav
        elif reset == "monthly":
            L = S = nav
        elif reset == "monthly_charged":
            # The trade is the pro rata resize of each leg back to NAV, charged on both sides
            cost = BPS * (abs(L - nav) + abs(S - nav))
            nav -= cost
            L = S = nav
        cash = nav - L + S
        long_pnl, short_pnl, cash_pnl, fee_pnl = L * x.rH, -S * x.rL, cash * x.rf, -S * fee / 12
        nav_new = nav + long_pnl + short_pnl + cash_pnl + fee_pnl
        if nav_new <= 0:
            raise NavStop(f"NAV reached {nav_new:.4f} in {m}")
        rows.append({"month": m, "nav_start": start, "cost": cost, "long": L, "short": S, "cash": cash, "long_pnl": long_pnl, "short_pnl": short_pnl, "cash_pnl": cash_pnl, "fee_pnl": fee_pnl, "nav": nav_new, "ret": nav_new / start - 1})
        L, S, nav = L * (1 + x.rH), S * (1 + x.rL), nav_new
    return pd.DataFrame(rows).set_index("month")


def check_extension_inputs():
    """Stop rather than use an old file: 10's returns must exist and be at least as new as what they are built from."""
    returns = ROOT / "output" / cfg.EXTENSION_2026["label"] / "returns.csv"
    sources = [ROOT / "data" / "raw" / "comp_secm_extension.parquet", TABLES / "portfolio_returns.csv"]
    missing = [p.name for p in [returns] + sources if not p.exists()]
    if missing:
        sys.exit(f"STOP: {missing} not found. Run 06_portfolios.py, 09a_extension_pull.py and 10_extension_2026.py first.")
    older = [p.name for p in sources if returns.stat().st_mtime < p.stat().st_mtime]
    if older:
        sys.exit(f"STOP: output/extension_2026/returns.csv is older than {older}. Rerun 10_extension_2026.py first.")


def main():
    c = cfg.LONG_SHORT_100_100
    if c["long_scores"] != cfg.HIGH_SCORES or c["short_scores"] != cfg.LOW_SCORES or c["reset"] != "annual_at_rebalance" or c["short_side_costs"] != "charged" or c["cash_interest"] != "rf" or c["sensitivity_reset"] != "monthly":
        sys.exit("LONG_SHORT_100_100 differs from what this script implements")
    check_extension_inputs()
    OUT.mkdir(parents=True, exist_ok=True)
    before = {p: sha(p) for p in guarded_files()}

    head = pd.read_csv(TABLES / "portfolio_returns.csv")
    head.index = pd.PeriodIndex(head.month, freq="M")
    turn = pd.read_csv(TABLES / "portfolio_turnover.csv")
    counts = pd.read_csv(TABLES / "bucket_counts.csv")
    ext = pd.read_csv(ROOT / "output" / cfg.EXTENSION_2026["label"] / "returns.csv")
    ext.index = pd.PeriodIndex(ext.month, freq="M")
    ff = pd.read_parquet(ROOT / "data/raw/ff_factors.parquet")
    ff["period"] = pd.PeriodIndex(ff.month, freq="M")
    ff = ff.set_index("period").sort_index()
    fcols = [ev.FACTOR_COLUMNS[n] for n in cfg.FACTOR_MODEL]

    t = turn.pivot(index="formation_date", columns="bucket", values="turnover_two_way")
    # Extension months carry no cost, so their gross return is returns.csv's; earlier months must match the headline
    tail = ext[ext.return_source != "CRSP"]
    earlier = ext[ext.return_source == "CRSP"]
    gap = max((earlier[b] - head[b]).abs().max() for b in ["High", "Low", "Benchmark"])
    if gap > 1e-12 or list(earlier.index) != list(head.index):
        sys.exit(f"STOP: the extension's CRSP months differ from the headline by {gap}")

    def inputs(with_ext):
        d = pd.DataFrame({"rH": head.High_gross, "rL": head.Low_gross, "formation_date": head.formation_date, "High_net": head.High, "Benchmark_net": head.Benchmark, "Spread_net": head.Spread, "Spread_gross": head.Spread_gross})
        if with_ext:
            add = pd.DataFrame({"rH": tail.High, "rL": tail.Low, "formation_date": tail.formation_date, "High_net": tail.High, "Benchmark_net": tail.Benchmark, "Spread_net": tail.High - tail.Low, "Spread_gross": tail.High - tail.Low})
            d = pd.concat([d, add])
        d["rH"], d["rL"] = d.rH.astype(float), d.rL.astype(float)
        f = ff.reindex(d.index)
        if f[fcols + ["rf"]].isna().any().any():
            sys.exit("STOP: missing factor values")
        d[fcols + ["rf"]] = f[fcols + ["rf"]].astype(float)
        d["new_cohort"] = d.formation_date != d.formation_date.shift(1)
        d["cost_rate"] = 0.0
        for date, g in d.groupby("formation_date", sort=False):
            d.loc[g.index[0], "cost_rate"] = BPS * (t.loc[date, "High"] + t.loc[date, "Low"])
        return d

    # Mechanics test: free monthly reset, no fee, no cost. Return above rf must equal the gross spread exactly.
    main_in = inputs(False)
    proof = run(main_in, 0.0, reset="monthly", costs=False)
    proof_gap = float((proof.ret - main_in.rf - main_in.Spread_gross).abs().max())
    if proof_gap > 1e-12:
        sys.exit(f"STOP: mechanics test failed by {proof_gap}")

    def comp(v):
        return (1 + v).prod() - 1

    def stats_for(ret, rf, by_year):
        s = ev.stats(ret, rf)
        y = ret.groupby(by_year).agg(months="size", r=comp)
        done = y[y.months == cfg.HOLDING_MONTHS]
        return {**s, "worst_year": done.r.min(), "worst_year_label": str(done.r.idxmin())[:4], "years_positive": int((done.r > 0).sum()), "complete_years": len(done)}

    def evaluate(d, res, name):
        row = {"series": name, **stats_for(res.ret, d.rf, d.formation_date)}
        rg = ev.regress(res.ret - d.rf, d, fcols)
        row.update({k: rg[k] for k in rg if k != "months"})
        return row

    def long_only(d, col, name):
        row = {"series": name, **stats_for(d[col], d.rf, d.formation_date)}
        rg = ev.regress(d[col] - d.rf, d, fcols)
        row.update({k: rg[k] for k in rg if k != "months"})
        return row

    fee, stress = c["borrow_fee_annual"], c["borrow_fee_stress_annual"]
    tables, sub_rows, sens_rows, year_tables, drags, attribution = [], [], [], {}, [], []
    exposures, charged_subs, spread_rows = [], [], []
    stopped = {}
    for scope, with_ext, title in [("main", False, "June 2005 to December 2025 (CRSP)"), ("extension", True, "June 2005 to May 2026 (CRSP, then Compustat from January 2026)")]:
        d = inputs(with_ext)
        try:
            base, hard, mon, mon_hard = run(d, fee), run(d, stress), run(d, fee, reset="monthly"), run(d, stress, reset="monthly")
            no_cost, no_fee, neither = run(d, fee, costs=False), run(d, 0.0), run(d, 0.0, costs=False)
            charged, charged_hard = run(d, fee, reset="monthly_charged"), run(d, stress, reset="monthly_charged")
        except NavStop as e:
            stopped[scope] = str(e)
            continue
        rows = [evaluate(d, base, f"Long/short, {fee:.2%} borrow"), evaluate(d, hard, f"Long/short, {stress:.2%} borrow stress"), long_only(d, "High_net", "Long-only High"), long_only(d, "Benchmark_net", "Benchmark")]
        tables += [{"scope": title, **r} for r in rows]
        sens_rows += [{"scope": title, **evaluate(d, x, n)} for n, x in [("Annual reset (locked result)", base), ("Monthly reset, free", mon), ("Monthly reset, charged", charged),
                                                                         (f"Annual reset (locked result), {stress:.2%} borrow", hard), (f"Monthly reset, free, {stress:.2%} borrow", mon_hard), (f"Monthly reset, charged, {stress:.2%} borrow", charged_hard)]]
        exposure = base.assign(end_long=base.long * (1 + d.rH), end_short=base.short * (1 + d.rL))
        exposure = pd.DataFrame({"gross": (exposure.end_long + exposure.end_short) / exposure.nav, "net": (exposure.end_long - exposure.end_short) / exposure.nav, "short": exposure.end_short / exposure.nav})
        top = exposure.gross.idxmax()
        charged_cost = (charged.cost / charged.nav_start)
        exposures.append({"scope": title, "peak_gross": exposure.gross.max(), "peak_gross_month": str(top), "net_at_that_month": exposure.net[top], "lowest_net": exposure.net.min(), "lowest_net_month": str(exposure.net.idxmin()), "peak_short_share_of_NAV": exposure.short.max(), "last_month": str(exposure.index[-1]), "last_gross": exposure.gross.iloc[-1], "last_net": exposure.net.iloc[-1], "last_short_share_of_NAV": exposure.short.iloc[-1],
                          "monthly_charged_cost_a_year": charged_cost.mean() * 12, "annual_reset_cost_a_year": (base.cost / base.nav_start).mean() * 12})
        for a2, b2 in ([cfg.SUBPERIODS[0], cfg.SUBPERIODS[1]] if not with_ext else [(cfg.SUBPERIODS[1][0], cfg.EXTENSION_2026["end"][:7])]):
            w = d.loc[pd.Period(a2, "M"):pd.Period(b2, "M")]
            for name, x in [("Monthly reset, charged", charged), (f"Monthly reset, charged, {stress:.2%} borrow", charged_hard)]:
                r = x.ret.loc[w.index]
                s_ = ev.stats(r, w.rf)
                rg = ev.regress(r - w.rf, w, fcols)
                charged_subs.append({"scope": title, "period": f"{a2} to {b2}", "series": name, "months": len(w), "CAGR": s_["CAGR"], "volatility": s_["volatility"], "sharpe": s_["sharpe"], "max_drawdown": s_["max_drawdown"], "alpha_annual": rg["alpha_annual"], "alpha_t": rg["alpha_t"]})
        z = d[["rH", "rL", "rf"]].join(charged[["nav_start", "cost", "long", "short", "cash", "nav", "ret"]]).join(charged_hard[["nav", "ret"]].add_suffix("_stress"))
        z.insert(0, "month", z.index.astype(str))
        z.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
        z.to_csv(OUT / f"nav_monthly_reset_charged_{scope}.csv", index=False)
        windows = [cfg.SUBPERIODS[0], cfg.SUBPERIODS[1]] if not with_ext else [(cfg.SUBPERIODS[1][0], cfg.EXTENSION_2026["end"][:7])]
        for a, b in windows:
            w = d.loc[pd.Period(a, "M"):pd.Period(b, "M")]
            for name, ret in [(f"Long/short, {fee:.2%} borrow", base.ret), (f"Long/short, {stress:.2%} borrow stress", hard.ret), ("Long-only High", d.High_net), ("Benchmark", d.Benchmark_net)]:
                r = ret.loc[w.index]
                s = ev.stats(r, w.rf)
                rg = ev.regress(r - w.rf, w, fcols)
                sub_rows.append({"scope": title, "period": f"{a} to {b}", "series": name, "months": len(w), "CAGR": s["CAGR"], "volatility": s["volatility"], "sharpe": s["sharpe"], "max_drawdown": s["max_drawdown"], "alpha_annual": rg["alpha_annual"], "alpha_t": rg["alpha_t"]})

        # Year by year on NAV, so the pieces add to the year's return
        rows_y = []
        for date, g in base.groupby(d.formation_date, sort=False):
            n0 = g.nav_start.iloc[0]
            mths = len(g)
            label = f"{date[:4]}-{str(int(date[:4]) + 1)[2:]}" if mths == cfg.HOLDING_MONTHS else f"{date[:4]} partial ({mths} of {cfg.HOLDING_MONTHS} months)"
            rows_y.append({"holding_year": label, "months": mths, "return": g.nav.iloc[-1] / n0 - 1, "long_leg": g.long_pnl.sum() / n0, "short_leg": g.short_pnl.sum() / n0, "cash_interest": g.cash_pnl.sum() / n0, "borrow_fee": g.fee_pnl.sum() / n0, "trading_cost": -g.cost.sum() / n0,
                           "stress_return": hard.loc[g.index].nav.iloc[-1] / hard.loc[g.index].nav_start.iloc[0] - 1,
                           "long_only_High": comp(d.High_net.loc[g.index]), "Benchmark": comp(d.Benchmark_net.loc[g.index])})
        y = pd.DataFrame(rows_y)
        y["check"] = (y.long_leg + y.short_leg + y.cash_interest + y.borrow_fee + y.trading_cost - y["return"]).abs()
        if y.check.max() > 1e-10:
            sys.exit(f"STOP: year pieces do not add up: {y.check.max()}")
        year_tables[scope] = y.drop(columns="check")

        cagr = ev.cagr
        drags.append({"scope": title, "CAGR_main": cagr(base.ret), "CAGR_no_costs": cagr(no_cost.ret), "cost_drag_a_year": cagr(no_cost.ret) - cagr(base.ret), "CAGR_no_fee": cagr(no_fee.ret), "borrow_drag_a_year": cagr(no_fee.ret) - cagr(base.ret), "CAGR_neither": cagr(neither.ret),
                      "stress_borrow_drag_a_year": cagr(no_fee.ret) - cagr(hard.ret), "total_cost_share_of_NAV": float((base.cost / base.nav_start).sum()), "total_fee_share_of_NAV": float((-base.fee_pnl / base.nav_start).sum())})

        # Against the Spread column, simple annual means
        n = 12
        cost_h = pd.Series(0.0, index=d.index)
        cost_l = pd.Series(0.0, index=d.index)
        for date, g in d.groupby("formation_date", sort=False):
            cost_h[g.index[0]] = BPS * t.loc[date, "High"]
            cost_l[g.index[0]] = BPS * t.loc[date, "Low"]
        spread_gross, spread_net = d.Spread_gross.mean() * n, d.Spread_net.mean() * n
        both_charged = spread_gross - (cost_h.mean() + cost_l.mean()) * n
        # Excess over rf from the same engine with the same cost timing
        excess = (base.ret - d.rf).mean() * n
        fee_part = (base.fee_pnl / base.nav_start).mean() * n
        g = (base.long + base.short) / (2 * base.nav_start)
        net = (base.long - base.short) / base.nav_start
        size_effect = ((g - 1) * d.Spread_gross).mean() * n
        net_effect = (net * ((d.rH + d.rL) / 2 - d.rf)).mean() * n
        attribution.append({"scope": title, "Spread_column_net": spread_net, "Spread_gross": spread_gross, "low_cost_credit_in_column": spread_net - spread_gross + cost_h.mean() * n,
                            "both_legs_charged": both_charged, "cost_treatment_effect": both_charged - spread_net, "borrow_fee": fee_part, "NAV_return_minus_rf": excess, "size_and_net_exposure_effect": excess - both_charged - fee_part, "size_effect": size_effect, "net_exposure_effect": net_effect, "High_cost_a_year": cost_h.mean() * n, "Low_cost_a_year": cost_l.mean() * n})
        correct = d.Spread_gross - cost_h - cost_l
        rc, rp = ev.regress(correct, d, fcols), ev.regress(d.Spread_net, d, fcols)
        spread_rows += [{"scope": title, "series": "Published net Spread column (credits Low's costs)", "mean_annual": spread_net, "alpha_annual": rp["alpha_annual"], "alpha_t": rp["alpha_t"]},
                        {"scope": title, "series": "Spread with both legs charged", "mean_annual": both_charged, "alpha_annual": rc["alpha_annual"], "alpha_t": rc["alpha_t"]}]
        if scope == "main":
            out = d[["rH", "rL", "rf"]].join(base[["nav_start", "cost", "long", "short", "cash", "nav", "ret"]]).join(hard[["nav", "ret"]].add_suffix("_stress")).join(mon[["nav", "ret"]].add_suffix("_monthly_reset"))
            out.insert(0, "month", out.index.astype(str))
            out.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
            out.to_csv(OUT / "nav_main.csv", index=False)
        else:
            out = d[["rH", "rL", "rf"]].join(base[["nav_start", "cost", "long", "short", "cash", "nav", "ret"]]).join(hard[["nav", "ret"]].add_suffix("_stress"))
            out.insert(0, "month", out.index.astype(str))
            out["return_source"] = ["Compustat trt1m" if m > pd.Period(cfg.RETURNS_END, "M") else "CRSP" for m in out.index]
            out.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
            out.to_csv(OUT / "nav_extension.csv", index=False)

    perf = pd.DataFrame(tables)
    subs = pd.DataFrame(sub_rows)
    sens = pd.DataFrame(sens_rows)
    drag = pd.DataFrame(drags)
    attr = pd.DataFrame(attribution)
    expo = pd.DataFrame(exposures)
    csub = pd.DataFrame(charged_subs)
    spread_fix = pd.DataFrame(spread_rows)
    for name, frame in [("performance", perf), ("subperiods", subs), ("sensitivity_monthly_reset", sens), ("drags", drag), ("spread_comparison", attr), ("exposure", expo), ("subperiods_monthly_reset_charged", csub), ("spread_both_legs_charged", spread_fix)]:
        frame.assign(universe_label=cfg.UNIVERSE_LABEL).to_csv(OUT / f"{name}.csv", index=False)
    for scope, y in year_tables.items():
        y.assign(universe_label=cfg.UNIVERSE_LABEL).to_csv(OUT / f"year_by_year_{scope}.csv", index=False)

    n = counts.pivot(index="formation_date", columns="bucket", values="names")
    thin = n[(n.High < cfg.MIN_BUCKET_NAMES) | (n.Low < cfg.MIN_BUCKET_NAMES)]
    significant = subs[subs.series.str.startswith("Long/short") | subs.series.eq("Long-only High")]
    sig_rows = significant[significant.alpha_t.abs() >= cfg.SIGNIFICANCE_T_STAT]
    full_sig = perf[perf.alpha_t.abs() >= cfg.SIGNIFICANCE_T_STAT]

    after = {p: sha(p) for p in before}
    moved = [str(p.relative_to(ROOT)) for p in before if before[p] != after[p]]

    md = ev.md_table
    show = ["scope", "series", "months", "CAGR", "volatility", "sharpe", "max_drawdown", "worst_year", "worst_year_label", "years_positive", "complete_years", "alpha_annual", "alpha_t"]
    load_cols = ["scope", "series", "r_squared"] + [c2 for n2 in cfg.FACTOR_MODEL for c2 in (f"beta_{n2}", f"t_{n2}")]
    L = [f"# Long/short, 100% long High and 100% short Low: {cfg.UNIVERSE_LABEL}\n",
         "**Labelled variant, not the headline, and not a blind test: the Spread had already been seen.** The borrow fee is a flat assumption, not data. "
         f"From January 2026, returns are Compustat's, and the main result stops at December 2025. Stopped runs: {stopped or 'none'}.\n",
         "**Terms.** **NAV** is net asset value, the capital in the strategy. **Long leg** owns High; **short leg** has sold Low and owes its value. **Borrow fee** is what a short seller pays to borrow the shares. "
         "**Cash** is NAV minus long value plus short value, and earns the risk-free rate. **CAGR** is the constant yearly growth rate. **Sharpe** is return above the risk-free rate per unit of volatility. **Max drawdown** is the largest peak-to-trough fall. "
         f"**Alpha** is return left after six factors, with Newey-West standard errors over {cfg.NEWEY_WEST_LAGS} months. A **t-stat** beyond about {cfg.SIGNIFICANCE_T_STAT:.0f} is treated as significant. **Loading** is sensitivity to a factor. **bp** is 0.01%.\n",
         f"**Mechanics.** Each June, costs of {cfg.TRANSACTION_COST_BPS} bp on each leg's two-way turnover come out of NAV, then long = short = NAV. Costs are measured on NAV before the charge; the first June counts as opening both legs. Resizing the two legs back to equal is not separately charged, because the rule charges each leg's turnover. "
         "Within the year the legs drift. Delisted names use the existing treatment inside each leg. A short position's return here is the opposite of Low's, including delisting returns, and no recall or margin limit is modelled.\n",
         f"**Mechanics test:** with free monthly reset and no fee or cost, return above rf equals the gross Spread to {proof_gap:.1e}. **Existing files:** hashed before and after this run: {'all identical' if not moved else 'CHANGED: ' + str(moved)}.\n",
         "## Performance\n", md(perf[show], 4), "\nWorst year and years positive use complete June-May years. Long/short's figures are after trading costs and borrow fee.\n",
         "\n## Factor loadings\n", md(perf[load_cols], 3),
         "\n## Subperiods\n", md(subs, 4)]
    if len(sig_rows) or len(full_sig):
        L.append(f"\n**Caution on significance.** At |t| of {cfg.SIGNIFICANCE_T_STAT:.0f} or more, in subperiods: {'; '.join(f'{r.series}, {r.period} ({r.months} months), t {r.alpha_t:.2f}' for r in sig_rows.itertuples()) or 'none'}. "
                 f"Over a full window: {'; '.join(f'{r.series}, {r.scope} ({r.months} months), t {r.alpha_t:.2f}' for r in full_sig.itertuples()) or 'none'}. The main-result stress t is {perf[(perf.series.str.contains('stress')) & (perf.months == len(head))].alpha_t.iloc[0]:.2f}, so no full-period alpha in the main result reaches {cfg.SIGNIFICANCE_T_STAT:.0f}.\n")
        L.append("\nThe audit (`verification/data_audit_long_short.md`) ran the random-portfolio tests on this series. The two t's of -2.35 are not evidence about the F-score: for 2015-06 to 2026-05, shuffled scores within sectors average t -2.11, and 56.5% of them pass |t| of 2. By t, the result is ordinary for same-sector portfolios, at 40% or more of draws at or below it in each row tested. "
                 "The test also oversizes: |t| of 2 is more like 2.3-2.5 for a true 5% level, and no row is clearly significant at 5% under all checks. The -2.5 to -3.6 range belongs to long-only High in 2015-25, not to this series.\n")
    L += ["\n## How large the book became\n",
          f"\"100/100\" holds only at each June reset. Gross is (long + short) / NAV and net is (long - short) / NAV, at month-ends.\n",
          md(expo.drop(columns=["monthly_charged_cost_a_year", "annual_reset_cost_a_year"]), 2),
          f"\nThe audit also found Western Digital alone at 46% of NAV and Intel at 26% at the end of May 2026. Few managers or brokers would let such a book run to this size, and no margin limit is modelled. Forced cuts could have helped or hurt, depending on the trigger.\n",
          "\n## Monthly reset with charges: a second view beside the locked result\n",
          f"The annual reset stays the locked result. It tests a position opened 100/100 and left alone for 12 months. This second view holds the book near 100/100: each non-June month, each leg is resized pro rata back to NAV, with {cfg.TRANSACTION_COST_BPS} bp on each dollar of that resize. June keeps the same turnover charge as the locked result, with no extra resize charge. Read the two together.\n",
          md(sens[sens.series.str.contains("Annual|charged")][["scope", "series", "CAGR", "volatility", "sharpe", "max_drawdown", "worst_year", "alpha_annual", "alpha_t"]], 4),
          "\n", md(csub, 4),
          f"\nThe same caution on significance applies to any t here at or beyond {cfg.SIGNIFICANCE_T_STAT:.0f}. In the audit's tests, the free monthly reset is unremarkable against random portfolios; so is the charged series at 0.50% borrow (t -1.06 at 35.9% of random draws, 63.3% within sector), which differs from it by about 0.11 points of CAGR a year.\n",
          f"\nAll charges in this view, averaged a year (share of NAV): {expo.monthly_charged_cost_a_year.round(4).tolist()}, against {expo.annual_reset_cost_a_year.round(4).tolist()} for the locked result, in the two windows above.\n",
          "\n## Cost and borrow drag\n", md(drag, 4),
          "\nDrag a year is the CAGR without that charge minus the CAGR with it, at the main settings. `total_..._share_of_NAV` sums each charge as a share of NAV.\n",
          "\n## Short-leg contribution by year, main result\n", "Each piece is its dollars over NAV at the start of that holding year, so they add to `return`.\n", md(year_tables.get("main", pd.DataFrame()), 4),
          "\n## Year by year with the extension\n", md(year_tables.get("extension", pd.DataFrame()).tail(2), 4),
          "\n## Against the Spread column\n",
          "Annual simple means. `Spread_column_net` is the published column: High's net return minus Low's net return. Low's cost makes Low's return lower, and subtracting it adds to the spread, so that column credits Low's cost instead of charging it. Here both legs pay.\n",
          md(attr, 4),
          "\n`cost_treatment_effect` is `both_legs_charged` minus `Spread_column_net`, which is twice Low's cost. `size_and_net_exposure_effect` is the rest, and it comes from the annual reset: `size_effect` is the legs being larger than NAV, times the spread, and `net_exposure_effect` is the book being net short or long, times the legs' return above rf. They are mostly timing: average exposures are close to neutral, but the book is largest and most net short when Low runs ahead.\n",
          "\n### The Spread, correctly charged\n",
          f"The published net Spread column credits Low's trading costs by about {abs(attr.cost_treatment_effect.iloc[0]) * 100:.2f} points a year. It stays as published. With both legs charged:\n",
          md(spread_fix, 4),
          "\n## Monthly-reset sensitivity (reported only)\n", "All monthly views, free and charged, beside the locked result.\n", md(sens[["scope", "series", "CAGR", "volatility", "sharpe", "max_drawdown", "worst_year", "alpha_annual", "alpha_t"]], 4),
          f"\n## Thin dates (under {cfg.MIN_BUCKET_NAMES} names in a leg): {len(thin)}\n", (md(thin.reset_index()[["formation_date", "High", "Low"]]) if len(thin) else f"None. High's smallest count is {int(n.High.min())} and Low's is {int(n.Low.min())}.\n"),
          "\n## Limits\n",
          "- The borrow fee is one flat rate for every name and date. Low's stocks can be costly or impossible to borrow, especially in stress, and the 2.00% stress does not capture that fully.\n- Dividends on shorted stock are inside Low's total return, so they are paid. No margin, recall or financing spread is modelled, and cash earns the full risk-free rate.\n- Low is scores 0-4, broader than Piotroski's weak group, and traditional REITs are effectively excluded.\n- The 2025 portfolio is partial in the main result. The extension's last five months use Compustat returns.\n"]
    (OUT / "results.md").write_text("\n".join(L), encoding="utf-8")

    print(f"proof gap {proof_gap:.1e}; extension match {gap:.1e}; stopped {stopped}; hashes changed {moved}; thin {len(thin)}")
    print(perf[show].round(4).to_string(index=False))
    print(subs.round(4).to_string(index=False))
    print(drag.round(4).T.to_string())
    print(attr.round(4).T.to_string())
    print(sens[["scope", "series", "CAGR", "sharpe", "max_drawdown", "alpha_annual", "alpha_t"]].round(4).to_string(index=False))
    print(perf[load_cols].round(3).to_string(index=False))
    print(year_tables["main"].round(4).to_string(index=False))
    print(year_tables["extension"].tail(1).round(4).to_string(index=False))
    sys.exit(1 if moved or stopped else 0)


if __name__ == "__main__":
    main()
