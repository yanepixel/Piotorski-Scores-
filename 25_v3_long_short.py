"""
v3 long-short 100/100 ILLUSTRATION (prereg_v3 H7), on the v3 primary series (literal rule). Not a strategy test: borrow fees are flat assumptions, short availability and recall are not modelled.
Gross High and Gross Low returns, each formation date: pay TRANSACTION_COST_BPS x two-way turnover on each leg (long on NAV, short on NAV), set long = short = NAV.
Monthly P&L = L rH - S rL + cash rf - S fee/12, cash = NAV - L + S. Variants: annual reset at 0.50% and 2.00% borrow (uncapped, as in v1) and a monthly-reset variant that caps gross exposure
at 2x NAV by construction, charged BPS on the monthly rebalancing trade. Reports peak gross exposure and peak short/NAV so the leverage the illustration reaches is visible.
Usage: python 25_v3_long_short.py   Writes output/spec_v3/long_short_v3.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "output/spec_v2/literal_sensitivity"
BPS = cfg.TRANSACTION_COST_BPS / 10000
p = pd.read_csv(SRC / "portfolio_returns_v2.csv")
p.index = pd.PeriodIndex(p.month, freq="M")
p["formation_date"] = pd.to_datetime(p.formation_date)
t = pd.read_csv(SRC / "portfolio_turnover_v2.csv", parse_dates=["formation_date"])
tw = {(r.formation_date, r.portfolio): r.turnover_two_way for r in t.itertuples()}
ff = pd.read_parquet(ROOT / "data/raw/ff_factors.parquet")
ff.index = pd.PeriodIndex(ff.month, freq="M")
rf = ff.rf.astype(float).reindex(p.index)
LS = cfg.LONG_SHORT_100_100


def run(fee, monthly_reset):
    nav, rows = 1.0, []
    for fd, g in p.groupby("formation_date"):
        cost = nav * BPS * (tw[(fd, "High")] + tw[(fd, "Low")])
        nav -= cost
        L = S = nav
        for m in g.index:
            cash = nav - L + S
            pnl = L * g.loc[m, "High_gross"] - S * g.loc[m, "Low_gross"] + cash * rf[m] - S * fee / 12
            L, S = L * (1 + g.loc[m, "High_gross"]), S * (1 + g.loc[m, "Low_gross"])
            nav += pnl
            if nav <= 0:
                raise SystemExit("NAV reached zero")
            gross_exp, short_nav = (L + S) / nav, S / nav
            if monthly_reset:
                nav -= BPS * (abs(L - nav) + abs(S - nav))
                L = S = nav
            rows.append({"month": m, "ret": pnl / (nav - pnl) if not monthly_reset else np.nan, "nav": nav, "gross_exposure": gross_exp, "short_over_nav": short_nav})
    d = pd.DataFrame(rows).set_index("month")
    d["ret"] = d.nav.pct_change()
    d.iloc[0, d.columns.get_loc("ret")] = d.nav.iloc[0] - 1
    return d


out = []
for name, fee, mr in [("annual reset, 0.50% borrow (uncapped)", LS["borrow_fee_annual"], False),
                      ("annual reset, 2.00% borrow (uncapped)", LS["borrow_fee_stress_annual"], False),
                      ("monthly reset, 0.50% borrow (gross exposure reset to 2x each month start)",LS["borrow_fee_annual"], True)]:
    d = run(fee, mr)
    ex = d.ret - rf
    out.append({"variant": name, "CAGR": d.nav.iloc[-1] ** (12 / len(d)) - 1, "volatility": d.ret.std() * 12 ** 0.5, "sharpe": ex.mean() * 12 / (ex.std() * 12 ** 0.5),
                "max_drawdown": float((d.nav / d.nav.cummax() - 1).min()), "peak_gross_exposure": d.gross_exposure.max(), "peak_short_over_nav": d.short_over_nav.max(), "months": len(d)})
res = pd.DataFrame(out)
res.to_csv(ROOT / "output/spec_v3/long_short_v3.csv", index=False)
print(res.round(4).to_string())
