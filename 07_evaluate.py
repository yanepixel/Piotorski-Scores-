"""
Phase 6: evaluate the portfolios (CLAUDE.md sections 5, 8b and 9). Stops at Checkpoint 3.

Reads:  output/tables/portfolio_returns.csv, score_portfolio_returns.csv, portfolio_turnover.csv, data/raw/ff_factors.parquet
Tables: output/tables/performance.csv, versus_benchmark.csv, factor_regressions.csv, returns_by_score.csv, year_by_year.csv, subperiods.csv
Charts: output/charts/cumulative_returns.png, drawdowns.png, returns_by_score.png
Report: output/checkpoint3_results.md
Log:    output/logs/evaluate_log.md
Exit code is 1 if a check fails.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import statsmodels.api as sm

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "output"
TABLES = OUTPUT / "tables"
CHARTS = OUTPUT / "charts"

FACTOR_COLUMNS = {"Mkt-RF": "mktrf", "SMB": "smb", "HML": "hml", "RMW": "rmw", "CMA": "cma", "MOM": "umd"}
LONG_ONLY = ["High", "Middle", "Low", "Benchmark", "RSP", "SPY"]
BUCKETS = ["High", "Middle", "Low", "Benchmark"]
INK, MUTED, GRID, AXIS, SURFACE = "#1a1a19", "#6b6a65", "#e6e5e0", "#c9c8c2", "#fcfcfb"
SERIES_COLORS = {"High": "#2a78d6", "Low": "#eb6834", "Benchmark": "#1baf7a"}
SERIES_NAMES = {"High": f"High (scores {cfg.HIGH_SCORES[0]}-{cfg.HIGH_SCORES[-1]})", "Low": f"Low (scores {cfg.LOW_SCORES[0]}-{cfg.LOW_SCORES[-1]})", "Benchmark": "Benchmark (all scored names)"}

# Wording from verification/data_audit_phase4_6.md (M1), required by CLAUDE.md section 8c.
SUBPERIOD_CONTEXT = ("High's alpha for June 2015 to December 2025 was -3.8% a year, t -4.10 with the pre-set 12 lags (-2.47 without adjustment; -3.06 with 4 lags). "
                     "In simulations, 12 lags on 127 months overstate significance somewhat, implying a t nearer -3.4 to -4.0. Randomly chosen portfolios from the same universe also averaged -1.3%, "
                     "and 19% of them reached |t| of 2 or more. The alpha falls in the lowest 1.5% of random selections, but the lowest 11% if the random selections keep High's sector mix. "
                     "The full-period alpha is -0.8%, t -0.71, and 2005-15 has the opposite sign.")

GLOSSARY = f"""## Terms

- **F-score:** a 0-9 count of financial-health tests a company passes, from its latest annual report.
- **Net / gross:** after / before trading costs ({cfg.TRANSACTION_COST_BPS} bps, or {cfg.TRANSACTION_COST_BPS / 100:.2f}%, on each dollar traded at each rebalance).
- **Benchmark:** every scored company in the universe, equally weighted, run the same way and charged the same costs.
- **CAGR:** the constant yearly growth rate that gives the same end value.
- **Volatility:** how much monthly returns swing, stated per year.
- **Sharpe ratio:** return above the risk-free rate per unit of volatility. Higher is better.
- **Max drawdown:** the largest peak-to-trough fall.
- **Turnover:** the share of the portfolio traded at a rebalance. Two-way counts buys and sells; one-way is half that.
- **Excess return:** return above the benchmark, here the average monthly gap times 12.
- **Tracking error:** how much the return gap to the benchmark swings, per year.
- **Information ratio:** excess return divided by tracking error.
- **Factor:** a broad return pattern. Mkt-RF is the market above cash, SMB small vs large companies, HML cheap vs expensive, RMW profitable vs unprofitable, CMA low vs high asset growth, MOM recent winners vs losers.
- **Alpha:** return left after accounting for those factors, stated per year.
- **t-stat:** how many standard errors a number is from zero. Beyond {cfg.SIGNIFICANCE_T_STAT:.0f} in either direction is treated as significant here.
- **Newey-West:** standard errors adjusted for returns that are correlated over time, here over {cfg.NEWEY_WEST_LAGS} months.
- **Spread:** High minus Low. A diagnostic only, with no shorting costs.
"""


def md_table(df, digits=None):
    d = df.copy()
    if digits is not None:
        for c in d.columns:
            if pd.api.types.is_float_dtype(d[c]):
                d[c] = d[c].round(digits)
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in d.itertuples(index=False)) + "\n"


def cagr(r):
    return (1 + r).prod() ** (12 / len(r)) - 1


def max_drawdown(r):
    return drawdown_series(r).min()


def drawdown_series(r):
    wealth = (1 + r).cumprod()
    peak = pd.concat([pd.Series([1.0]), wealth]).cummax().iloc[1:]
    return pd.Series(wealth.values / peak.values - 1, index=r.index)


def stats(r, rf):
    excess = r - rf
    return {"months": len(r), "CAGR": cagr(r), "volatility": r.std() * 12 ** 0.5, "sharpe": excess.mean() * 12 / (excess.std() * 12 ** 0.5), "max_drawdown": max_drawdown(r)}


def regress(y, factors, cols):
    x = sm.add_constant(factors[cols].astype(float))
    fit = sm.OLS(y.astype(float), x).fit(cov_type="HAC", cov_kwds={"maxlags": cfg.NEWEY_WEST_LAGS})
    row = {"months": int(fit.nobs), "alpha_annual": fit.params["const"] * 12, "alpha_t": fit.tvalues["const"], "r_squared": fit.rsquared}
    for name in cfg.FACTOR_MODEL:
        row[f"beta_{name}"] = fit.params[FACTOR_COLUMNS[name]]
        row[f"t_{name}"] = fit.tvalues[FACTOR_COLUMNS[name]]
    return row


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)


def titles(fig, title, note):
    fig.text(0.02, 0.97, title, fontsize=13, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.91, f"{note}\n{cfg.UNIVERSE_LABEL}", fontsize=8, color=MUTED, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.82))


def line_chart(series, path, title, note, ylabel, log=False, fmt=None):
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150, facecolor=SURFACE)
    style(ax)
    dates = series.index.to_timestamp("M")
    for name in ["High", "Benchmark", "Low"]:
        ax.plot(dates, series[name], color=SERIES_COLORS[name], linewidth=2, label=SERIES_NAMES[name], solid_capstyle="round")
    if log:
        ax.set_yscale("log", base=2)
        ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    if fmt:
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(fmt))
    ax.set_ylabel(ylabel, color=MUTED)
    ax.legend(frameon=False, loc="upper left" if log else "lower right", fontsize=8, labelcolor=INK)
    titles(fig, title, note)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main():
    CHARTS.mkdir(parents=True, exist_ok=True)
    failures = []

    p = pd.read_csv(TABLES / "portfolio_returns.csv", parse_dates=["formation_date"])
    p.index = pd.PeriodIndex(p.month, freq="M")
    s = pd.read_csv(TABLES / "score_portfolio_returns.csv", parse_dates=["formation_date"])
    t = pd.read_csv(TABLES / "portfolio_turnover.csv", parse_dates=["formation_date"])

    # Factors join on month: portfolio dates are last trading day, factor dates first of month. Cut at the last return.
    ff = pd.read_parquet(RAW / "ff_factors.parquet")
    ff["period"] = pd.PeriodIndex(ff.month, freq="M")
    ff = ff.set_index("period").sort_index()
    ff_full_end = ff.index.max()
    factors = ff.reindex(p.index)
    cols = [FACTOR_COLUMNS[n] for n in cfg.FACTOR_MODEL]
    factors[cols + ["rf"]] = factors[cols + ["rf"]].astype(float)
    if factors[cols + ["rf"]].isna().any().any():
        failures.append("Missing factor values in the test period")
    if p.index.max() != pd.Period(cfg.RETURNS_END, "M"):
        failures.append(f"Returns end {p.index.max()}, not {cfg.RETURNS_END}")
    rf = factors.rf

    # --- Performance ---
    perf = []
    for name in LONG_ONLY:
        row = {"portfolio": name, "basis": "net" if name in BUCKETS else "fund return", **stats(p[name], rf)}
        if name in BUCKETS:
            rows = t[(t.bucket == name) & (t.formation_date > t.formation_date.min())]
            row["avg_turnover_two_way"] = rows.turnover_two_way.mean()
            row["avg_turnover_one_way"] = rows.turnover_one_way.mean()
            row["avg_annual_cost"] = rows.cost.mean()
        perf.append(row)
    for name in BUCKETS:
        perf.append({"portfolio": name, "basis": "gross", **stats(p[f"{name}_gross"], rf)})
    perf = pd.DataFrame(perf)
    perf.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    perf.to_csv(TABLES / "performance.csv", index=False)
    spread_row = {"portfolio": "Spread", "months": len(p)}
    for basis, col in [("net", "Spread"), ("gross", "Spread_gross")]:
        spread_row[f"mean_annual_{basis}"] = p[col].mean() * 12
        spread_row[f"volatility_{basis}"] = p[col].std() * 12 ** 0.5
        spread_row[f"max_drawdown_{basis}"] = max_drawdown(p[col])

    # --- Holding years ---
    def compound(r):
        return (1 + r).prod() - 1
    yr = p.groupby("formation_date").agg(months=("High", "size"), High=("High", compound), Low=("Low", compound), Middle=("Middle", compound), Benchmark=("Benchmark", compound),
                                         High_gross=("High_gross", compound), Low_gross=("Low_gross", compound), Benchmark_gross=("Benchmark_gross", compound)).reset_index()
    yr["Spread"] = yr.High - yr.Low
    yr["High_minus_Benchmark"] = yr.High - yr.Benchmark
    yr["High_beats_Benchmark"] = yr.High > yr.Benchmark
    yr["holding_year"] = [f"{d.year}-{str(d.year + 1)[2:]}" if m == cfg.HOLDING_MONTHS else f"{d.year} partial ({m} of {cfg.HOLDING_MONTHS} months)" for d, m in zip(yr.formation_date, yr.months)]
    counts = t.pivot(index="formation_date", columns="bucket", values="names").reset_index()
    yr = yr.merge(counts[["formation_date", "High", "Low"]].rename(columns={"High": "High_names", "Low": "Low_names"}), on="formation_date")
    complete = yr[yr.months == cfg.HOLDING_MONTHS]
    partial = yr[yr.months < cfg.HOLDING_MONTHS]
    hit_set = complete if cfg.HIT_RATE_COMPLETE_YEARS_ONLY else yr
    hit = hit_set.High_beats_Benchmark.mean()
    out = yr[["holding_year", "months", "High_names", "Low_names", "High", "Low", "Spread", "Benchmark", "High_minus_Benchmark", "High_beats_Benchmark"]].copy()
    out.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    out.to_csv(TABLES / "year_by_year.csv", index=False)

    # --- Versus the primary benchmark ---
    vs = []
    for name, col, base in [("High", "High", "Benchmark"), ("Middle", "Middle", "Benchmark"), ("Low", "Low", "Benchmark"), ("High, gross", "High_gross", "Benchmark_gross"), ("RSP", "RSP", "Benchmark"), ("SPY", "SPY", "Benchmark")]:
        diff = p[col] - p[base]
        te = diff.std() * 12 ** 0.5
        vs.append({"portfolio": name, "versus": base, "excess_return_annual": diff.mean() * 12, "cagr_difference": cagr(p[col]) - cagr(p[base]), "tracking_error": te, "information_ratio": diff.mean() * 12 / te,
                   "excess_t_newey_west": sm.OLS(diff.astype(float), np.ones(len(diff))).fit(cov_type="HAC", cov_kwds={"maxlags": cfg.NEWEY_WEST_LAGS}).tvalues.iloc[0]})
    vs = pd.DataFrame(vs)
    vs.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    vs.to_csv(TABLES / "versus_benchmark.csv", index=False)

    # --- Factor regressions ---
    specs = [("High excess of risk-free", "net", p.High - rf), ("High excess of risk-free", "gross", p.High_gross - rf),
             ("Spread (High minus Low)", "net", p.Spread), ("Spread (High minus Low)", "gross", p.Spread_gross),
             ("High minus Benchmark (added)", "net", p.High - p.Benchmark), ("Low excess of risk-free (added)", "net", p.Low - rf), ("Benchmark excess of risk-free (added)", "net", p.Benchmark - rf)]
    regs = [{"series": n, "basis": b, **regress(y, factors, cols)} for n, b, y in specs]
    regs = pd.DataFrame(regs)
    regs.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    regs.to_csv(TABLES / "factor_regressions.csv", index=False)
    if (regs.months != len(p)).any():
        failures.append("A regression does not use every month")

    # --- Subperiods ---
    subs = []
    for a, b in cfg.SUBPERIODS:
        w = p.loc[pd.Period(a, "M"):pd.Period(b, "M")]
        fw, rw = factors.loc[w.index], rf.loc[w.index]
        high, bench, low = stats(w.High, rw), stats(w.Benchmark, rw), stats(w.Low, rw)
        diff = w.High - w.Benchmark
        rh, rs = regress(w.High - rw, fw, cols), regress(w.Spread, fw, cols)
        subs.append({"period": f"{a} to {b}", "months": len(w), "High_CAGR": high["CAGR"], "Low_CAGR": low["CAGR"], "Benchmark_CAGR": bench["CAGR"], "High_sharpe": high["sharpe"], "Benchmark_sharpe": bench["sharpe"],
                     "High_excess_annual": diff.mean() * 12, "information_ratio": diff.mean() * 12 / (diff.std() * 12 ** 0.5), "Spread_annual": w.Spread.mean() * 12,
                     "High_alpha_annual": rh["alpha_annual"], "High_alpha_t": rh["alpha_t"], "Spread_alpha_annual": rs["alpha_annual"], "Spread_alpha_t": rs["alpha_t"]})
    subs = pd.DataFrame(subs)
    if subs.months.sum() != len(p):
        failures.append("Subperiods do not cover every month once")
    subs.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    subs.to_csv(TABLES / "subperiods.csv", index=False)

    # --- Monotonicity, gross, complete holding years ---
    sy = s.groupby(["formation_date", "F_SCORE", "partial_period"]).agg(ret=("gross", lambda r: (1 + r.dropna()).prod() - 1), names=("names_at_formation", "first")).reset_index()
    done = sy[~sy.partial_period]
    mono = done.groupby("F_SCORE").agg(avg_annual_return=("ret", "mean"), complete_years=("ret", "size"), avg_names=("names", "mean")).reindex(range(0, 10)).reset_index()
    pr = sy[sy.partial_period].set_index("F_SCORE").ret.rename("partial_2025_return")
    mono = mono.merge(pr, on="F_SCORE", how="left")
    mono["under_minimum_names"] = mono.avg_names < cfg.MIN_BUCKET_NAMES
    ordered = mono.dropna(subset=["avg_annual_return"])
    rank_corr = ordered.avg_annual_return.rank().corr(ordered.F_SCORE.rank())
    mono.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    mono.to_csv(TABLES / "returns_by_score.csv", index=False)

    # --- Charts ---
    pct = lambda v, _: f"{v:.0%}"
    usd = lambda v, _: f"${v:g}"
    wealth = pd.DataFrame({n: (1 + p[n]).cumprod() for n in SERIES_COLORS})
    period_note = f"Net of costs, {p.month.iloc[0]} to {p.month.iloc[-1]}. The last portfolio is partial (7 of 12 months)."
    line_chart(wealth, CHARTS / "cumulative_returns.png", "Growth of $1, log scale", period_note, "Value of $1 (log scale)", log=True, fmt=usd)
    dd = pd.DataFrame({n: drawdown_series(p[n]) for n in SERIES_COLORS})
    line_chart(dd, CHARTS / "drawdowns.png", "Drawdowns", period_note, "Fall from prior peak", fmt=pct)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150, facecolor=SURFACE)
    style(ax)
    shown = mono.dropna(subset=["avg_annual_return"])
    ax.bar(shown.F_SCORE, shown.avg_annual_return, width=0.82, color=SERIES_COLORS["High"])
    ax.axhline(0, color=AXIS, linewidth=1)
    for r in shown.itertuples():
        ax.annotate(f"{int(r.complete_years)} yrs\n{r.avg_names:.0f} names", (r.F_SCORE, max(r.avg_annual_return, 0)), ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", color=MUTED, fontsize=7)
    ax.set_xticks(range(0, 10))
    ax.set_xlabel("F-score (0 to 9)", color=MUTED)
    ax.set_ylabel("Average annual return", color=MUTED)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(pct))
    ax.margins(y=0.15)
    titles(fig, "Average annual return by F-score", "Gross of costs, complete June-May holding years. Scores with few names or years are unreliable; see labels.")
    fig.savefig(CHARTS / "returns_by_score.png", facecolor=SURFACE)
    plt.close(fig)

    # --- Report ---
    h = regs[(regs.series.str.startswith("High excess")) & (regs.basis == "net")].iloc[0]
    sp = regs[(regs.series.str.startswith("Spread")) & (regs.basis == "net")].iloc[0]
    hb = regs[regs.series.str.startswith("High minus")].iloc[0]
    significant = [n for n, v in [("High", h.alpha_t), ("Spread", sp.alpha_t), ("High minus Benchmark", hb.alpha_t)] if abs(v) >= cfg.SIGNIFICANCE_T_STAT]
    sub_sig = subs[(subs.High_alpha_t.abs() >= cfg.SIGNIFICANCE_T_STAT) | (subs.Spread_alpha_t.abs() >= cfg.SIGNIFICANCE_T_STAT)]
    L = [f"# Checkpoint 3 results: {cfg.UNIVERSE_LABEL}\n", "## Checks\n", f"**{len(failures)} check failure(s).** {len(p)} months, {p.month.iloc[0]} to {p.month.iloc[-1]}. Factors available to {ff_full_end}, cut to the last return month and joined on month.\n",
         f"**Significance at |t| = {cfg.SIGNIFICANCE_T_STAT:.0f}.** Full period: {significant or 'none'}. Subperiods: {', '.join(sub_sig.period) or 'none'}, one High alpha. Read it with the context below.\n",
         f"> {SUBPERIOD_CONTEXT}\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append(GLOSSARY)
    L.append("\n## Performance (returns are net of costs unless marked gross; RSP and SPY are fund returns)\n")
    L.append(md_table(perf.drop(columns="universe_label"), 4))
    L.append(f"\nSpread: {spread_row['mean_annual_net']:.2%} a year net, {spread_row['mean_annual_gross']:.2%} gross, volatility {spread_row['volatility_net']:.2%}, largest drawdown {spread_row['max_drawdown_net']:.2%}.\n")
    L.append(f"\nHigh beat the Benchmark in {int(hit_set.High_beats_Benchmark.sum())} of {len(hit_set)} complete holding years = {hit:.0%}. {partial.holding_year.iloc[0]}: {'beat' if partial.High_beats_Benchmark.iloc[0] else 'trailed'}, shown separately.\n")
    L.append("\n## Versus the Benchmark\n")
    L.append(md_table(vs.drop(columns="universe_label"), 4))
    L.append(f"\n## Factor regressions ({', '.join(cfg.FACTOR_MODEL)}; Newey-West, {cfg.NEWEY_WEST_LAGS} lags)\n")
    L.append(md_table(regs.drop(columns="universe_label"), 3))
    L.append("\nThe rows marked (added) go beyond the brief, for context.\n")
    L.append("\n## Returns by individual score (gross, complete years)\n")
    L.append(md_table(mono.drop(columns="universe_label"), 4))
    thin = mono[mono.under_minimum_names].F_SCORE.tolist()
    well = ordered[~ordered.under_minimum_names]
    L.append(f"\nRank correlation of score with average return: {rank_corr:+.2f}, across {len(ordered)} scores. **Treat this with caution:** it includes scores {thin}, which average under {cfg.MIN_BUCKET_NAMES} names, and score 0 has a single name in a single year. "
             f"It is {well.avg_annual_return.rank().corr(well.F_SCORE.rank()):+.2f} across the {len(well)} scores with enough names, and neither figure is a test of significance.\n")
    L.append("\n## Year by year (net)\n")
    L.append(md_table(out.drop(columns="universe_label"), 4))
    L.append("\n## Subperiods (net)\n")
    L.append(md_table(subs.drop(columns="universe_label"), 3))
    L.append(f"\nSubperiods with an alpha at or beyond |t| = {cfg.SIGNIFICANCE_T_STAT:.0f}: {', '.join(sub_sig.period) or 'none'}. {SUBPERIOD_CONTEXT}\n")
    (OUTPUT / "checkpoint3_results.md").write_text("\n".join(L), encoding="utf-8")

    fm = pd.read_parquet(ROOT / "data" / "clean" / "formation.parquet", columns=["formation_date", "permco", "scored"])
    held = fm[fm.scored]
    log = [f"# Phase 6 log: {cfg.UNIVERSE_LABEL}\n", f"{len(failures)} check failure(s).\n",
           f"- Months evaluated: {len(p)}, {p.month.iloc[0]} to {p.month.iloc[-1]}. Regression months: {int(regs.months.min())} to {int(regs.months.max())}.",
           f"- Portfolios cover {len(held)} held company-dates, {held.permco.nunique()} unique companies, on {held.formation_date.nunique()} formation dates.",
           f"- Rows dropped by this script: 0. It reads the finished monthly series; drops are in `formation_checks.md` and `portfolio_checks.md`.",
           f"- Factor months available to {ff_full_end}, used to {p.month.iloc[-1]}.\n"]
    (OUTPUT / "logs" / "evaluate_log.md").write_text("\n".join(log), encoding="utf-8")

    print(f"months={len(p)} failures={len(failures)} significant={significant}")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
