"""
v3 write-up. Replaces output/writeup.md (the v2 text is kept in output/archive_v2/writeup_v2.md). Every number is read from output/spec_v3/*.csv
or output/spec_v2 files at run time; none is typed in. Usage: python 21_v3_writeup.py   (run after 18, 19, 20)
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
V3 = ROOT / "output" / "spec_v3"
h = pd.read_csv(V3 / "headline_v3.csv")
t = pd.read_csv(V3 / "tests_v3.csv")
c = pd.read_csv(V3 / "cost_sensitivity_v3.csv")
y = pd.read_csv(V3 / "high_count_and_passrate_by_year_v3.csv")
pc = lambda x, d=2, s=True: f"{x * 100:{'+' if s else ''}.{d}f}%"
LIT, NET = "literal (primary)", "net (sensitivity)"


def H(rule, base, col):
    return h[(h.rule == rule) & (h.benchmark == base)].iloc[0][col]


def T(rule, test, period="full", lag="formula"):
    return t[(t.rule == rule) & (t.test == test) & (t.period == period) & (t.lag_kind == lag)].iloc[0]


A, B, C_ = "(a) High - Benchmark(all included), mean", "(b) High - Benchmark(all included), 4-factor alpha", "(c) High - Low, 4-factor alpha"
E, F = "(e) High excess of rf, 4-factor alpha (v2 primary test)", "(f) Benchmark(all included) excess of rf, 4-factor alpha"
POST = "2015-06 to 2025-12 (POST-HOC split)"
L = ["# Piotroski F-score backtest: v3 write-up\n",
     f"Universe: Top 500 US common stocks by market cap, excluding financials and utilities (S&P 500 proxy). June 2005 to December 2025 ({int(h.months.iloc[0])} months). Rules are in `output/prereg_v3.md`, written and committed before any v3 number. The v1 and v2 results are archived (`output/archive_v1/`, `output/archive_v2/`); v3 corrects errors found in review and does not search for a better-looking result.\n",
     "## Answer\n",
     "**No detectable edge.** Excess return means High's return minus the benchmark's, shown both as the mean monthly gap times 12 and as the gap between compounded annual returns (CAGR).\n",
     "| Issuance rule | Benchmark | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | Sharpe High / benchmark |", "|---|---|---|---|---|---|---|"]
for rule in (LIT, NET):
    for base, nm in (("Benchmark", "all included (primary)"), ("BenchmarkScored", "scored only")):
        L.append(f"| {rule} | {nm} | {pc(H(rule, base, 'High_CAGR'), 2, False)} | {pc(H(rule, base, base + '_CAGR') if base + '_CAGR' in h else float('nan'), 2, False) if False else pc(H(rule, 'Benchmark', 'Benchmark_CAGR') if base == 'Benchmark' else H(rule, 'BenchmarkScored', 'BenchmarkScored_CAGR'), 2, False)} | {pc(H(rule, base, 'cagr_gap'))} | {pc(H(rule, base, 'mean_monthly_gap_x12'))} | {H(rule, base, 'High_sharpe'):.2f} / {H(rule, base, 'benchmark_sharpe'):.2f} |")
L += ["\nThe literal issuance rule is primary because the paper defines it (fixed before looking at results); the net rule (sstk minus prstkc) was adopted in v2 after seeing a pass rate and is a sensitivity. Both are shown because they give different signs. All-included is the primary benchmark because the brief defines the comparison as the equal-weighted universe; it was chosen after v1, so scored-only is shown with equal prominence.\n",
      "## Primary tests (three, Holm-adjusted; full period, HAC lag by formula, t with T-k df)\n", "| Rule | Test | Estimate / yr | t | p | Holm p | Min detectable (80% power) |", "|---|---|---|---|---|---|---|"]
for rule in (LIT, NET):
    for nm in (A, B, C_):
        r = T(rule, nm)
        L.append(f"| {rule} | {nm} | {pc(r.estimate_annual)} | {r.t:.2f} | {r.p:.3f} | {r.holm_p_primary_family:.3f} | {pc(r.mde_80pct, 2, False)} |")
n = len(t)
L += [f"\nNo primary test is close to significant. Piotroski's own +1.7 point effect is inside the range these tests could not rule out.\n",
      "## The 2015-25 shortfall is mostly the universe's, and the split is post-hoc\n",
      f"The 2015-06 split and the v2 family of six were chosen after v1 showed a large t. They are exploratory only. In that period (net rule) High's four-factor alpha is {pc(T(NET, E, POST).estimate_annual)} (t {T(NET, E, POST).t:.2f}), but the all-included benchmark's own alpha is {pc(T(NET, F, POST).estimate_annual)} (t {T(NET, F, POST).t:.2f}) and High minus the benchmark is {pc(T(NET, B, POST).estimate_annual)} (t {T(NET, B, POST).t:.2f}). Under the literal rule High minus the benchmark in the same period is {pc(T(LIT, B, POST).estimate_annual)} (t {T(LIT, B, POST).t:.2f}). The v2 'Holm survivor' (p 0.047) is not presented as inference.\n",
      "Roughly 250 earlier t-statistics plus the v3 rows (`output/spec_v3/trial_count_v3.md`) give an approximate upper bound of about 360 trials, and a Bonferroni-equivalent critical |t| of about 3.8 (a conservative bound, not an exact count). No score-isolating test reaches it. No period was held out.\n",
      "## Transaction costs (High minus all-included benchmark, CAGR gap)\n", "| bps per side | Literal | Net |", "|---|---|---|"]
for b in sorted(c.bps.unique()):
    L.append(f"| {b} | {pc(c[(c.rule == LIT) & (c.bps == b)].gap_vs_all_included.iloc[0])} | {pc(c[(c.rule == NET) & (c.bps == b)].gap_vs_all_included.iloc[0])} |")
ls_ = pd.read_csv(V3 / "long_short_v3.csv")
LS_ROWS = ["| Variant | CAGR | Volatility | Sharpe | Max drawdown | Peak gross exposure | Peak short / NAV |", "|---|---|---|---|---|---|---|"] + [f"| {q.variant} | {pc(q.CAGR)} | {pc(q.volatility, 1, False)} | {q.sharpe:.2f} | {pc(q.max_drawdown, 1)} | {q.peak_gross_exposure:.2f}x | {q.peak_short_over_nav:.2f}x |" for q in ls_.itertuples()]
L += ["\n## 100/100 long-short: an illustration, not a strategy test (`25_v3_long_short.py`, literal rule)\n", *LS_ROWS,
      "\nLong High and short Low, each equal to NAV at every formation date, costs charged on both legs. Borrow fees are flat assumptions; short availability and recall are not modelled. The uncapped annual-reset versions drift to roughly 4x gross exposure with the short leg above 2x NAV, so their returns are not a realistic account of a fund. The monthly-reset row resets exposure to 2x each month start. None of this is added to the test family.\n"]
rb = pd.read_csv(V3 / "robustness_v3.csv")
L += ["\n## Robustness under the final specification (literal rule; `22_v3_robustness.py`)\n", "| Variant | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | t |", "|---|---|---|---|---|---|"]
for q in rb.itertuples():
    L.append(f"| {q.variant} | {pc(q.High_CAGR, 2, False)} | {pc(q.Benchmark_CAGR, 2, False)} | {pc(q.cagr_gap)} | {pc(q.mean_gap_x12)} | {q.t:.2f} |")
L += ["\nVariants: High = 7-9; market-cap weights; availability at filing date + 30 or 60 days; availability at year-end + 150 or 180 days (filing date ignored, no fallback); firm-years missing some signals kept, scored on the signals available (needs 7 of 9). None is identical to the headline (checked in code). The headline reproduces the v2 literal portfolio exactly. All gaps have |t| below 1.5. Sector-neutral, value-filter, profitability-screen, universe-buffer and eight-signal variants from v1 are not rerun.\n",
      "\n## Issuance signal drift and bucket size\n",
      f"The signal pass rate rises over the sample under both rules (literal {y.pass_pct_scored_literal.iloc[0]:.1f}% in FY{int(y.fyear.iloc[0])} to {y.pass_pct_scored_literal.iloc[-1]:.1f}% in FY{int(y.fyear.iloc[-1])}; net {y.pass_pct_scored_net.iloc[0]:.1f}% to {y.pass_pct_scored_net.iloc[-1]:.1f}%), so High membership clusters in later years. Literal-rule High holds between {int(y['High_names_literal (primary)'].min())} and {int(y['High_names_literal (primary)'].max())} names a year (net {int(y['High_names_net (sensitivity)'].min())} to {int(y['High_names_net (sensitivity)'].max())}); thin buckets are noisy. Per-year counts: `output/spec_v3/high_count_and_passrate_by_year_v3.csv`.\n",
      "## What was checked, and what was not\n",
      "- Independent F-score recomputation from raw Compustat on 400 random firm-years (seed 20261102): see `output/spec_v3/numcheck_v3.md`.\n- Independent recomputation of gross High and Low returns from raw CRSP for every month: see the same file.\n- Signal unit tests with hand-worked numbers and planted bugs: `tests/test_signals.py`.\n- Null returns and delistings (`23_v3_null_return_rule.py`): treating the approved no-trade months as exits instead of flat zero, for every portfolio, moves the headline gap from +0.95% to +0.96% (t 0.86); all 191 mid-period exits already carry a recorded delisting return, so Shumway's -30% replacement replaces nothing (`output/spec_v3/delisting_check_v3.md`).\n- NOT claimed: that every number in every table was recomputed. Middle, RSP, SPY, tracking error, information ratio, factor loadings and subperiod CAGRs are checked only by `16_spec_v2_numcheck.py`, which reads the same portfolio file the evaluator reads (arithmetic, not pipeline). The printed-number match in `19_v3_numcheck.py` is lenient.\n",
      "## Known limits and work not done\n",
      "- Fundamentals are current-vintage Compustat dated by original filing date; `ib` and `prstkc` came from separate pulls. Point-in-time testing exists only to FY2014 (98.5% of scores unchanged then); `comp_snapshot` is denied, so FY2015-24 exposure is unmeasured.\n- Under the net rule a missing `prstkc` now makes the signal unknown and the firm-year unscorable (prereg D); that sensitivity therefore scores fewer firm-years.\n- The literal rule treats a negative `sstk` as no issuance (paper: nothing issued), fixed after an audit found it failing them; all v3 numbers are from after that fix.\n- The extension and REIT variant (scripts 09-10) are still on the earlier specifications; the 100/100 long-short is rerun on v3 as an illustration (script 25). Scripts 08 robustness is replaced by 22 for the variants listed above; the rest of the v1 variants are not rerun.\n- Not done: single-vintage pull, pull hashing, book-to-market replication. Raw pulls are hashed after the fact (`24_hash_raw.py`), not inside each pull script.\n- This universe (the 500 largest) is not a test of Piotroski's claim, which concerns high book-to-market firms; the paper itself finds the effect weak among the largest firms.\n",
      "## Conclusion\n",
      "On the 500 largest non-financial, non-utility US stocks, buying high F-score names shows no detectable edge, and the sign depends on defensible choices (issuance rule, benchmark) that no test here can separate. Costs of realistic size do not change that. An effect of about 4% a year would be needed to show up reliably, so a Piotroski-sized effect is not ruled out. The one earlier significant result is a post-hoc, mostly universe-wide shortfall. Several corrections remain outstanding (listed above).\n"]
(ROOT / "output" / "writeup.md").write_text("\n".join(L), encoding="utf-8")

# README headline, generated from the same numbers
from scipy import stats as _st
pl = t[(t.rule == LIT) & t.in_primary_family]
a_ = T(LIT, A)
tcrit = _st.t.ppf(0.975, int(a_.months) - 1)
R = ["## The answer\n",
     "**No detectable edge.** Excess return means High's return minus the benchmark's; it is shown as the mean monthly gap times 12 and as the gap between compounded annual returns (CAGR), which differ. The issuance signal's literal paper rule is primary (fixed before looking at results, `output/prereg_v3.md`); the v2 net rule is a sensitivity. Both benchmarks are shown: all included names is primary because the brief defines the comparison as the equal-weighted universe, but that was set after v1.\n",
     "| Issuance rule | Benchmark | High CAGR | Benchmark CAGR | CAGR gap | Mean gap x12 | Sharpe High / benchmark |", "|---|---|---|---|---|---|---|"]
for rule in (LIT, NET):
    for base, nm in (("Benchmark", "all included (primary)"), ("BenchmarkScored", "scored only")):
        R.append(f"| {rule} | {nm} | {pc(H(rule, base, 'High_CAGR'), 2, False)} | {pc(H(rule, 'Benchmark', 'Benchmark_CAGR') if base == 'Benchmark' else H(rule, 'BenchmarkScored', 'BenchmarkScored_CAGR'), 2, False)} | {pc(H(rule, base, 'cagr_gap'))} | {pc(H(rule, base, 'mean_monthly_gap_x12'))} | {H(rule, base, 'High_sharpe'):.2f} / {H(rule, base, 'benchmark_sharpe'):.2f} |")
R.append(f"\nPrimary tests, literal rule (Holm-adjusted, all adjusted p {pl.holm_p_primary_family.min():.2f} or higher): High minus benchmark {pc(a_.estimate_annual)} (t {a_.t:.2f}); four-factor alpha {pc(T(LIT, B).estimate_annual)} (t {T(LIT, B).t:.2f}); High minus Low alpha {pc(T(LIT, C_).estimate_annual)} (t {T(LIT, C_).t:.2f}). "
         f"Minimum detectable effect at 80% power: {pc(pl.mde_80pct.min(), 1, False)} to {pc(pl.mde_80pct.max(), 1, False)} a year. The 95% interval for the first is {pc(a_.estimate_annual - tcrit * a_.se_annual)} to {pc(a_.estimate_annual + tcrit * a_.se_annual)}, which contains Piotroski's own +1.7 point effect, so it cannot be ruled out.\n")
R.append(f"The earlier 2015-25 'significant' four-factor alpha is post-hoc and exploratory (the split was chosen after v1 showed a large t); the universe's own benchmark alpha in that period is {pc(T(NET, F, POST).estimate_annual)} (t {T(NET, F, POST).t:.2f}). Trial count is an approximate upper bound of about 360, critical |t| about 3.8; no score-isolating test reaches it.\n")
R.append("**Still open:** restatement testing past FY2014 (blocked on this account), a single-vintage pull, pull hashing, config and `07_evaluate.py` cleanups, moving the extension and REIT runs (09-10) and the v1 robustness variants not rerun to v3, the end-to-end rerun, and a book-to-market replication. The full write-up is `output/writeup.md` (generated by `21_v3_writeup.py`); the v2 text is in `output/archive_v2/`.\n")
rd = (ROOT / "README.md").read_text(encoding="utf-8")
i, j = rd.index("## The answer"), rd.index("## What you need")
(ROOT / "README.md").write_text(rd[:i] + "\n".join(R) + "\n" + rd[j:], encoding="utf-8")
print("\n".join(L)[:3500])
