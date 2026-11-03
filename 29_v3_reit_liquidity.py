"""
v3 rerun of the labelled variant reit_liquidity_substitute (config.REIT_LIQUIDITY_SUBSTITUTE, V2_RERUNS; CLAUDE.md 8d and 8g). Descriptive only; not part of any test family.

Rule (locked): an included row whose CRSP issuertype on the formation date is REIT, and whose only uncomputable signal in its latest scorable year is F_DLIQUID, may use
che / lt: passes if the ratio rose on the same one-year and stub rules (che and lt present in t and t-1, lt > 0; pair_ok from 04_scores). Standard 0-9 buckets (High 8-9, Low 0-4).
All other signals follow the v3 inputs: literal issuance rule (primary), ib, filing date + 3 days with no fallback (a year with no real filing date stays unscorable).
The latest year is chosen among nine-signal years and, for REITs, substitute years, with the 18-month age rule. The all-included Benchmark is unchanged; the scored-only Benchmark
gains the substitute REITs. General Growth 2009-05 (and Maxim) are held flat if held (NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2_reruns"]); any other held null stops the run.
Mechanics are those of 13_spec_v2_portfolios.py through the engine in 28_v3_extension_2026.py (reproduces output/spec_v2/literal_sensitivity before anything is added).

Reads:  data/clean/*.parquet, data/raw/{comp_funda_reit_fields,crsp_msf_v2,crsp_benchmarks,comp_funda_ib,comp_funda_prstkc,ff_factors}.parquet,
        output/reit_liquidity_substitute/{comparison.csv,rows_added.csv,reit_rows_still_unscored.csv,substitute_uncomputable.csv,bucket_counts.csv} (v1, read only)
Writes: output/spec_v3/reit_liquidity_v3.csv (aggregates only), data/external/reit_liquidity_v3_rows.csv (company-level)
Usage:  python -W ignore 29_v3_reit_liquidity.py          (no network, no WRDS)
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e28", ROOT / "28_v3_extension_2026.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
RAW, CLEAN, OUT, EXT = E.RAW, E.CLEAN, E.OUT, E.EXT
V1 = ROOT / "output" / "reit_liquidity_substitute"
V = cfg.REIT_LIQUIDITY_SUBSTITUTE
EIGHT = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]
WIN = "Jun2005-Dec2025"


def add_substitute(scores, fund, fields):
    """che / lt with its prior-year value under the same pair rule; substitute score where F_DLIQUID is the only signal missing."""
    f = fund[["gvkey", "fyear", "datadate"]].merge(fields, on=["gvkey", "datadate", "fyear"], how="left", validate="1:1")
    f["che"], f["lt"] = f.che.astype(float), f["lt"].astype(float)
    f["CASH_TO_LIAB"] = (f.che / f["lt"]).where(f["lt"] > 0)
    f = f.sort_values(["gvkey", "fyear"])
    f["CASH_TO_LIAB_prior"] = f.groupby("gvkey").CASH_TO_LIAB.shift(1)
    d = scores.merge(f[["gvkey", "fyear", "che", "lt", "CASH_TO_LIAB", "CASH_TO_LIAB_prior"]], on=["gvkey", "fyear"], how="left", validate="1:1")
    d["CASH_TO_LIAB_prior"] = d.CASH_TO_LIAB_prior.where(d.pair_ok)
    d["F_DLIQUID_SUB"] = ((d.CASH_TO_LIAB - d.CASH_TO_LIAB_prior) > 0).astype(float).where((d.CASH_TO_LIAB - d.CASH_TO_LIAB_prior).notna())
    d["needs"] = d.F_DLIQUID.isna() & d[EIGHT].notna().all(axis=1) & d.filing_date.notna()   # only F_DLIQUID uncomputable, and a real filing date exists
    d["usable"] = d.needs & d.F_DLIQUID_SUB.notna()
    d["F_SCORE_SUB"] = d.F_SCORE
    d.loc[d.usable, "F_SCORE_SUB"] = d.loc[d.usable, EIGHT].sum(axis=1) + d.loc[d.usable, "F_DLIQUID_SUB"]
    return d


def summarise(P, long, turn, ff):
    """Metrics for one run on June 2005 to December 2025, plus the v1-style comparison metrics."""
    m = E.metrics(P, ff, windows={WIN: P}, ext_block=False)
    o = {}
    d_s = P.High - P.BenchmarkScored
    d_a = P.High - P.Benchmark
    o["High_minus_Benchmark_annual"] = d_s.mean() * 12     # v1 Benchmark = scored names only
    o["High_minus_BenchmarkAll_annual"] = d_a.mean() * 12
    o["information_ratio"] = d_s.mean() * 12 / (d_s.std() * 12 ** 0.5)
    o["information_ratio_vs_all_included"] = d_a.mean() * 12 / (d_a.std() * 12 ** 0.5)
    o["High_sharpe"] = m[("performance", "sharpe", "High", WIN)]
    o["Benchmark_sharpe"] = m[("performance", "sharpe", "BenchmarkScored", WIN)]
    o["BenchmarkAll_sharpe"] = m[("performance", "sharpe", "Benchmark", WIN)]
    o["High_CAGR"] = m[("performance", "CAGR", "High", WIN)]
    o["Benchmark_CAGR"] = m[("performance", "CAGR", "BenchmarkScored", WIN)]
    o["BenchmarkAll_CAGR"] = m[("performance", "CAGR", "Benchmark", WIN)]
    o["Spread_annual"] = (P.High - P.Low).mean() * 12
    o["High_beats_Benchmark_years"] = m[("hit_years", "High_beats_BenchmarkScored", "High", WIN)]
    o["High_beats_BenchmarkAll_years"] = m[("hit_years", "High_beats_Benchmark", "High", WIN)]
    o["complete_years"] = m[("hit_years", "complete_years", "High", WIN)]
    t2 = turn[turn.formation_date > turn.formation_date.min()]
    o["High_turnover_two_way"] = t2[t2.portfolio == "High"].turnover_two_way.mean()
    cnt = long.drop_duplicates(["formation_date", "portfolio"])
    for b, key in [("High", "High"), ("Middle", "Middle"), ("Low", "Low"), ("Benchmark", "Benchmark"), ("BenchmarkScored", "BenchmarkScored")]:
        c = cnt[cnt.portfolio == b].n
        o[f"{key}_names_median"] = float(c.median())
        o[f"{key}_names_min"] = float(c.min())
    return m, o


def main():
    if V["ratio"] != "che / lt" or V["buckets"] != "standard" or V["null_return_rule"] != "hold_flat":
        sys.exit("STOP: REIT_LIQUIDITY_SUBSTITUTE differs from what this script implements")
    OUT.mkdir(parents=True, exist_ok=True)
    EXT.mkdir(parents=True, exist_ok=True)
    try:
        s12, fund, scores = E.v3_scores("literal")
        universe = pd.read_parquet(CLEAN / "universe.parquet")
        fields = pd.read_parquet(RAW / "comp_funda_reit_fields.parquet")
        crsp_all, by_permno, ret_by_month = E.load_crsp()
        ff = E.load_factors()

        base = s12.align(scores, universe)
        # REIT status = CRSP issuertype on the formation date (v1 rule)
        it = crsp_all[["permno", "mthcaldt", "issuertype"]].rename(columns={"mthcaldt": "formation_date"})
        uni = universe.merge(it, on=["permno", "formation_date"], how="left", validate="1:1")
        if uni[uni.included].issuertype.isna().any():
            raise E.Stop("an included list row has no CRSP issuer type on its formation date")
        uni["is_reit"] = uni.issuertype == cfg.REIT_ISSUER_TYPE

        d = add_substitute(scores, fund, fields)
        sub = d.copy()
        sub["F_SCORE"] = sub.F_SCORE_SUB
        sub.loc[sub.usable, "F_DLIQUID"] = sub.loc[sub.usable, "F_DLIQUID_SUB"]
        reit_rows = s12.align(sub, uni[uni.is_reit])
        other_rows = s12.align(d, uni[~uni.is_reit])
        m = pd.concat([reit_rows, other_rows]).sort_values(["formation_date", "rank"]).reset_index(drop=True)
        if len(m) != int(universe.included.sum()) or m.duplicated(["formation_date", "permco"]).any():
            raise E.Stop("variant list does not match the included universe")
        used = m[m.scored].merge(d[["gvkey", "fyear", "usable"]], on=["gvkey", "fyear"], how="left")
        m = m.merge(used[["formation_date", "permno", "usable"]].rename(columns={"usable": "uses_substitute"}), on=["formation_date", "permno"], how="left")
        m["uses_substitute"] = m.uses_substitute.fillna(False).astype(bool)
        if (m.uses_substitute & ~m.is_reit).any():
            raise E.Stop("a non-REIT row uses the substitute")
        v = m[m.scored]
        if (v.avail_date_v2 > v.formation_date).any() or (v.age_months > cfg.MAX_SCORE_AGE_MONTHS).any():
            raise E.Stop("timing check failed")

        # baseline engine run must reproduce the saved v3 (literal) series before anything is compared
        lm0, flat0 = E.window_checks(base, by_permno)
        t0, long0, _, turn0 = E.build_series(base, ret_by_month, lm0)
        E.check_reproduces(t0)
        lm1, flat1 = E.window_checks(m, by_permno)
        t1, long1, _, turn1 = E.build_series(m, ret_by_month, lm1)
        print("baseline reproduced from the v2 literal file; variant run complete", flush=True)
    except E.Stop as e:
        (OUT / "STOPPED_29.md").write_text(f"# 29_v3_reit_liquidity stopped\n\n{e}\n", encoding="utf-8")
        print("STOP:", e)
        sys.exit(1)

    ch = E.fund_chain()
    for t in (t0, t1):
        for k in cfg.SECONDARY_BENCHMARKS:
            t[k] = ch[k].reindex(t.index)
    m0, o0 = summarise(t0, long0, turn0, ff)
    m1, o1 = summarise(t1, long1, turn1, ff)

    v1c = pd.read_csv(V1 / "comparison.csv").set_index("metric")
    rows = []

    def add(block, item, series, window, v1h, v1v, v3b, v3v, note=""):
        rows.append({"block": block, "item": item, "series": series, "window": window, "v1_headline": v1h, "v1_variant": v1v, "v3_baseline": v3b, "v3_variant": v3v, "note": note})

    v1_note = {"High_minus_Benchmark_annual": "v1 and v3 on the scored-only benchmark (the v1 benchmark); all-included beside",
               "information_ratio": "scored-only benchmark", "Benchmark_sharpe": "scored-only benchmark", "Benchmark_CAGR": "scored-only benchmark", "High_beats_Benchmark_years": "scored-only benchmark; complete years only"}
    for k in ["High_minus_Benchmark_annual", "High_minus_BenchmarkAll_annual", "information_ratio", "information_ratio_vs_all_included", "High_sharpe", "Benchmark_sharpe", "BenchmarkAll_sharpe", "High_CAGR", "Benchmark_CAGR", "BenchmarkAll_CAGR",
              "Spread_annual", "High_beats_Benchmark_years", "High_beats_BenchmarkAll_years", "complete_years", "High_turnover_two_way",
              "High_names_median", "High_names_min", "Middle_names_median", "Low_names_median", "Low_names_min", "Benchmark_names_median", "Benchmark_names_min", "BenchmarkScored_names_median", "BenchmarkScored_names_min"]:
        kv1 = k if k in v1c.index else None
        add("comparison", k, "", WIN, v1c.headline[kv1] if kv1 else np.nan, v1c.variant[kv1] if kv1 else np.nan, o0[k], o1[k], v1_note.get(k, "v1 Benchmark_names are scored-only counts" if k.startswith("Benchmark_names") else ""))
    for k in ["High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_alpha", "High_minus_Benchmark_alpha_t", "Spread_alpha_annual", "Spread_alpha_t"]:
        add("v1_only", k, "", WIN, v1c.headline[k], v1c.variant[k], np.nan, np.nan, "v1: six-factor, Newey-West 12 lags; not comparable with the v3 four-factor tests below")
    for key in sorted(set(m0) | set(m1)):
        if key[0] in ("gap", "gap_test_raw", "gap_test_4factor", "performance"):
            add("v3_" + key[0], key[1], key[2], key[3], np.nan, np.nan, m0.get(key, np.nan), m1.get(key, np.nan), "v3 convention: automatic HAC lag, t(T-k); lag 12 beside")

    # list rows and REIT coverage
    key = ["formation_date", "permno"]
    bm = base[key + ["fyear", "F_SCORE", "bucket", "scored"]].rename(columns={"fyear": "fy0", "F_SCORE": "F0", "bucket": "b0", "scored": "s0"})
    j = m.merge(bm, on=key, how="left")
    added = j[j.scored & ~j.s0]
    changed = j[j.scored & j.s0 & ((j.fyear != j.fy0) | (j.F_SCORE != j.F0) | (j.bucket != j.b0))]
    lost = j[~j.scored & j.s0]
    v1add = pd.read_csv(V1 / "rows_added.csv")
    for b in ["High", "Middle", "Low"]:
        add("rows", "rows_added", b, "all formation dates", float((v1add.bucket == b).sum()), np.nan, np.nan, float((added.bucket == b).sum()), "v1 added rows were counted against the v1 headline; v3 against the v3 literal baseline")
    add("rows", "rows_added", "all", "all formation dates", float(len(v1add)), np.nan, np.nan, float(len(added)))
    add("rows", "headline_rows_that_changed_year_score_or_bucket", "all", "all formation dates", np.nan, np.nan, np.nan, float(len(changed)))
    add("rows", "baseline_rows_lost", "all", "all formation dates", np.nan, np.nan, np.nan, float(len(lost)))
    reit = j[j.is_reit]
    add("reit_coverage", "included_reit_rows", "REIT", "all formation dates", np.nan, np.nan, float(len(reit)), float(len(reit)))
    add("reit_coverage", "reit_rows_scored", "REIT", "all formation dates", np.nan, np.nan, float(reit.s0.sum()), float(reit.scored.sum()))
    add("reit_coverage", "reit_rows_using_substitute", "REIT", "all formation dates", np.nan, np.nan, 0.0, float(m.uses_substitute.sum()))
    v1un = pd.read_csv(V1 / "reit_rows_still_unscored.csv")
    add("reit_coverage", "reit_rows_still_unscored", "REIT", "all formation dates", np.nan, float(len(v1un)), float((~reit.s0.astype(bool)).sum()), float((~reit.scored).sum()))
    gv_reit = set(uni[uni.is_reit & uni.included].gvkey.dropna())
    pool = d[d.gvkey.isin(gv_reit) & d.usable]
    fail = d[d.gvkey.isin(gv_reit) & d.needs & ~d.usable]
    v1fail = pd.read_csv(V1 / "substitute_uncomputable.csv")
    add("reit_coverage", "substitute_uncomputable_company_years_of_reit_names", "REIT", "FY range", np.nan, float(len(v1fail)), np.nan, float(len(fail)))
    sub_rows = m[m.uses_substitute][["gvkey", "fyear"]].merge(d[["gvkey", "fyear", "F_DLIQUID_SUB"]], on=["gvkey", "fyear"], how="left")
    add("signal", "pass_pct_list_rows_using_it", "F_DLIQUID_SUB", "all formation dates", np.nan, np.nan, np.nan, float(100 * sub_rows.F_DLIQUID_SUB.mean()) if len(sub_rows) else np.nan)
    add("signal", "pass_pct_company_years_where_computable", "F_DLIQUID_SUB", "FY range", np.nan, np.nan, np.nan, float(100 * pool.F_DLIQUID_SUB.mean()))
    add("null_return", "hold_flat_months_used_in_any_series", "", "all", np.nan, np.nan, float(len(flat0)), float(len(flat1)), "approved cases only: General Growth 2009-05, Maxim 2007-11 to 2008-05")
    out = pd.DataFrame(rows)
    out["change_v1"] = out.v1_variant - out.v1_headline
    out["change_v3"] = out.v3_variant - out.v3_baseline
    out.to_csv(OUT / "reit_liquidity_v3.csv", index=False)

    comp_cols = ["formation_date", "permno", "gvkey", "fyear", "age_months", "F_SCORE", "bucket"]
    detail = pd.concat([added[comp_cols].assign(kind="added"), changed[comp_cols].assign(kind="changed")])
    names = fund.sort_values("fyear").drop_duplicates("gvkey", keep="last").set_index("gvkey").conm
    detail["conm"] = detail.gvkey.map(names)
    detail.sort_values(["formation_date", "conm"]).to_csv(EXT / "reit_liquidity_v3_rows.csv", index=False)

    show = out[out.block == "comparison"][["item", "v1_headline", "v1_variant", "v3_baseline", "v3_variant", "change_v3"]]
    print(show.round(4).to_string(index=False))
    sel = out[(out.block.isin(["v3_gap_test_raw", "v3_gap_test_4factor"])) & out.item.isin(["t_auto", "alpha_x12_auto"]) & (out.series == "High_minus_Benchmark")]
    print(sel[["block", "item", "series", "v3_baseline", "v3_variant"]].round(4).to_string(index=False))
    print(out[out.block.isin(["rows", "reit_coverage", "signal", "null_return"])][["block", "item", "series", "v1_headline", "v1_variant", "v3_baseline", "v3_variant"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
