"""
Stage 12: transaction-cost sensitivity (prereg_main H8). The pipeline charges cost as bps x traded value, so the monthly cost is linear in bps:
cost_x = (gross - net) * x / TRANSACTION_COST_BPS. This rescales that charge to 5, 10, 20, 50 bps for High and both benchmarks (all charged alike).
Usage: python 12_costs.py   Writes output/results/cost_sensitivity.csv
"""
from pathlib import Path

import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
rows = []
for rule, d in [("literal (primary)", ROOT / "output/core"), ("net (sensitivity)", ROOT / "output/core/net_sensitivity")]:
    p = pd.read_csv(d / "portfolio_returns.csv")
    base = cfg.TRANSACTION_COST_BPS
    for bps in [0, 5, 10, 20, 50]:
        s = {n: p[n + "_gross"] - (p[n + "_gross"] - p[n]) * bps / base for n in ["High", "Benchmark", "BenchmarkScored"]}
        cg = lambda r: (1 + r).prod() ** (12 / len(r)) - 1
        rows.append({"rule": rule, "bps": bps, "High_CAGR": cg(s["High"]), "Benchmark_CAGR": cg(s["Benchmark"]), "BenchmarkScored_CAGR": cg(s["BenchmarkScored"]),
                     "gap_vs_all_included": cg(s["High"]) - cg(s["Benchmark"]), "gap_vs_scored_only": cg(s["High"]) - cg(s["BenchmarkScored"]),
                     "mean_monthly_gap_x12_vs_all_included": (s["High"] - s["Benchmark"]).mean() * 12})
out = pd.DataFrame(rows)
out.to_csv(ROOT / "output/results/cost_sensitivity.csv", index=False)
print(out.round(4).to_string())
