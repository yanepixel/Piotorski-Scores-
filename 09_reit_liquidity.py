"""
Labelled variant reit_liquidity_substitute (config.REIT_LIQUIDITY_SUBSTITUTE; CLAUDE.md section 8d). The headline is unchanged.

On each formation date, a row-level REIT with no F_DLIQUID may use: change in che / lt > 0, on the same one-year and stub rules.
It then scores 0-9 on the standard buckets. Other firms with no liquidity signal stay dropped.

Reads:  data/clean/*.parquet, data/raw/*.parquet, output/tables/portfolio_returns.csv
Raw:    data/raw/comp_funda_reit_fields.parquet (new; write-once, pass --overwrite to replace)
Output: output/reit_liquidity_substitute/ only
Exit code is 1 if the run stops or a headline file changes.
"""
import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
TABLES = ROOT / "output" / "tables"
OUT = ROOT / "output" / cfg.REIT_LIQUIDITY_SUBSTITUTE["label"]
RAW_FILE = RAW / "comp_funda_reit_fields.parquet"

EIGHT = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def headline_files():
    """Every file this variant must leave alone."""
    named = [ROOT / "config.py", ROOT / "CLAUDE.md", ROOT / "output" / "writeup.md", ROOT / "output" / "checkpoint3_results.md"]
    named += [ROOT / f for f in ["01_build_universe.py", "02_pull_data.py", "03_clean.py", "04_scores.py", "05_align.py", "06_portfolios.py", "07_evaluate.py", "08_robustness.py"]]
    groups = list(RAW.glob("*")) + list(CLEAN.glob("*")) + list(TABLES.glob("*")) + list((ROOT / "output" / "charts").glob("*")) + list((ROOT / "output" / "logs").glob("*")) + list((ROOT / "output" / "robustness").rglob("*"))
    return sorted({p for p in named + groups if p.is_file() and p != RAW_FILE})


def pull_fields(overwrite):
    if RAW_FILE.exists() and not overwrite:
        return pd.read_parquet(RAW_FILE), "read existing raw file"
    gv = sorted(pd.read_parquet(RAW / "comp_funda.parquet", columns=["gvkey"]).gvkey.unique())
    db = wrds.Connection(wrds_username=rob.universe_mod.wrds_username())
    have = set(db.describe_table("comp", "funda").name)
    need = cfg.REIT_PULL_FIELDS
    if not set(need) <= have:
        sys.exit(f"comp.funda lacks {set(need) - have}")
    filters = " and ".join(f"{k} = '{v}'" for k, v in cfg.FUNDA_FILTERS.items())
    keys = ", ".join(f"'{g}'" for g in gv)
    columns = ", ".join(f'"{c}"' for c in need)  # "lt" is a reserved word in Postgres
    q = db.raw_sql(f'select {columns} from comp.funda where {filters} and gvkey in ({keys}) and fyear between {cfg.FIRST_FUNDAMENTAL_FY} and {cfg.LAST_FUNDAMENTAL_FY}', date_cols=["datadate"])
    db.close()
    q.to_parquet(RAW_FILE, index=False)
    return q, f"pulled {len(q)} rows"


def add_substitute(scores, fund, fields):
    """Scores carry every ratio already; only the new ratio needs its lag, under the same pair rule."""
    f = fund[["gvkey", "fyear", "datadate"]].merge(fields, on=["gvkey", "datadate", "fyear"], how="left", validate="1:1")
    f["che"], f["lt"] = f.che.astype(float), f["lt"].astype(float)
    f["CASH_TO_LIAB"] = (f.che / f["lt"]).where(f["lt"] > 0)
    f = f.sort_values(["gvkey", "fyear"])
    f["CASH_TO_LIAB_prior"] = f.groupby("gvkey").CASH_TO_LIAB.shift(1)
    f["che_prior"], f["lt_prior"] = f.groupby("gvkey").che.shift(1), f.groupby("gvkey")["lt"].shift(1)
    d = scores.merge(f[["gvkey", "fyear", "che", "lt", "CASH_TO_LIAB", "CASH_TO_LIAB_prior", "che_prior", "lt_prior"]], on=["gvkey", "fyear"], how="left", validate="1:1")
    d["CASH_TO_LIAB_prior"] = d.CASH_TO_LIAB_prior.where(d.pair_ok)
    d["DCASH_TO_LIAB"] = d.CASH_TO_LIAB - d.CASH_TO_LIAB_prior
    d["F_DLIQUID_SUB"] = (d.DCASH_TO_LIAB > 0).astype(float).where(d.DCASH_TO_LIAB.notna())
    needs = d.F_DLIQUID.isna() & d[EIGHT].notna().all(axis=1)
    usable = needs & d.F_DLIQUID_SUB.notna()
    d["substitute_needed"] = needs
    d["substitute_usable"] = usable
    d["F_SCORE_SUB"] = d.F_SCORE
    d.loc[usable, "F_SCORE_SUB"] = d.loc[usable, EIGHT].sum(axis=1) + d.loc[usable, "F_DLIQUID_SUB"]
    reason = pd.Series("", index=d.index)
    reason[needs & ~d.pair_ok] = "flagged or missing prior year"
    reason[needs & d.pair_ok & (d["lt_prior"].isna() | (d["lt_prior"] <= 0))] = "prior-year lt null or not positive"
    reason[needs & d.pair_ok & d.che_prior.isna()] = "prior-year che null"
    reason[needs & (d["lt"].isna() | (d["lt"] <= 0))] = "lt null or not positive"
    reason[needs & d.che.isna()] = "che null"
    d["substitute_failure"] = reason.where(needs & ~usable, "")
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true", help="Replace the new raw file.")
    args = ap.parse_args()
    v = cfg.REIT_LIQUIDITY_SUBSTITUTE
    if v["ratio"] != "che / lt" or v["buckets"] != "standard":
        sys.exit("REIT_LIQUIDITY_SUBSTITUTE differs from what this script implements")
    OUT.mkdir(parents=True, exist_ok=True)
    before = {p: sha(p) for p in headline_files()}

    fields, how = pull_fields(args.overwrite)
    print(how, flush=True)
    universe = pd.read_parquet(CLEAN / "universe.parquet")
    fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
    fscores = pd.read_parquet(CLEAN / "fscores.parquet")
    fscores["score_type"] = "nine"
    formation = pd.read_parquet(CLEAN / "formation.parquet")
    msf = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "issuertype", "issuernm"])

    returns, evaluate = rob.Returns(), rob.Evaluator()

    # Headline through the same engine must reproduce the published files
    a = rob.align(universe, fscores)
    base = a[a.scored].copy()
    key = ["formation_date", "permno"]
    pub = formation[formation.scored]
    if not base[key + ["F_SCORE", "fyear"]].sort_values(key).reset_index(drop=True).astype({"F_SCORE": float}).equals(pub[key + ["F_SCORE", "fyear"]].sort_values(key).reset_index(drop=True).astype({"F_SCORE": float})):
        sys.exit("STOP: alignment does not reproduce formation.parquet")
    base["bucket"] = rob.buckets(base)
    t0, turn0, cnt0, exits0, _ = rob.run_portfolios(base, returns)
    published = pd.read_csv(TABLES / "portfolio_returns.csv")
    published.index = pd.PeriodIndex(published.month, freq="M")
    cols = [c for b in rob.MAIN + ["Benchmark", "Spread"] for c in (b, f"{b}_gross")]
    gap = (t0[cols] - published[cols]).abs().max().max()
    if gap > 1e-12:
        sys.exit(f"STOP: engine differs from portfolio_returns.csv by {gap}")
    print(f"headline reproduced: largest monthly gap {gap:.2e}", flush=True)
    row0, subs0 = evaluate(t0, turn0, cnt0)

    # Row-level REIT flag on each formation date
    uni = universe.merge(msf[["permno", "mthcaldt", "issuertype", "issuernm"]], left_on=["permno", "formation_date"], right_on=["permno", "mthcaldt"], how="left", validate="1:1")
    uni["is_reit"] = uni.issuertype == cfg.REIT_ISSUER_TYPE
    if uni.issuertype.isna().any():
        sys.exit("STOP: a list row has no issuer type on its formation date")

    d = add_substitute(scores_full(), fund, fields)
    sub = d.copy()
    sub["F_SCORE"] = sub.F_SCORE_SUB
    sub["score_type"] = np.where(sub.F_SCORE_SUB.notna() & d.F_SCORE.isna(), "reit_substitute", "nine")
    normal = d.copy()
    normal["score_type"] = "nine"

    reit_rows = rob.align(uni[uni.is_reit], sub)
    other_rows = rob.align(uni[~uni.is_reit], normal)
    keep_cols = sorted(set(reit_rows.columns) & set(other_rows.columns))
    m = pd.concat([reit_rows[keep_cols], other_rows[keep_cols]]).sort_values(["formation_date", "rank"]).reset_index(drop=True)
    if len(m) != int(universe.included.sum()):
        sys.exit("STOP: row count differs from the included universe")
    held = m[m.scored].copy()
    held["bucket"] = rob.buckets(held.assign(score_type="nine"))
    if (held[held.avail_date > held.formation_date].shape[0]) or (held.age_months > cfg.MAX_SCORE_AGE_MONTHS).any():
        sys.exit("STOP: timing check failed")
    if held.is_reit.eq(False).pipe(lambda s: (held[s].score_type != "nine").any()):
        sys.exit("STOP: a non-REIT row uses the substitute")

    stopped = None
    try:
        t1, turn1, cnt1, exits1, flat = rob.run_portfolios(held, returns, hold_flat=rob.hold_flat_cases(v["label"], v["null_return_rule"]))
        row1, subs1 = evaluate(t1, turn1, cnt1)
    except rob.VariantStop as e:
        stopped = str(e)
    if stopped:
        (OUT / "STOPPED.md").write_text(f"# Stopped\n\n{cfg.UNIVERSE_LABEL}\n\n{stopped}\n", encoding="utf-8")
        print("STOP:", stopped)
        sys.exit(1)

    # --- Reports ---
    held_key = held.merge(base[key + ["fyear", "F_SCORE", "bucket"]], on=key, how="left", suffixes=("", "_headline"), indicator=True)
    added = held_key[held_key._merge == "left_only"]
    changed = held_key[(held_key._merge == "both") & ((held_key.fyear != held_key.fyear_headline) | (held_key.bucket != held_key.bucket_headline) | (held_key.F_SCORE != held_key.F_SCORE_headline))]
    gone = base.merge(held[key], on=key, how="left", indicator=True).query("_merge == 'left_only'")
    if len(gone):
        print(f"WARNING: {len(gone)} headline rows left the variant")
    subs_used = held[held.score_type == "reit_substitute"].merge(d[["gvkey", "fyear", "F_DLIQUID_SUB", "CASH_TO_LIAB", "CASH_TO_LIAB_prior", "che", "lt"]], on=["gvkey", "fyear"], how="left", suffixes=("", "_d"))
    add_out = added[["formation_date", "permno", "gvkey", "conm", "gsector", "fyear", "age_months", "F_SCORE", "bucket"]].sort_values(["formation_date", "conm"])
    add_out.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    add_out.to_csv(OUT / "rows_added.csv", index=False)
    chg_out = changed[["formation_date", "conm", "fyear_headline", "fyear", "F_SCORE_headline", "F_SCORE", "bucket_headline", "bucket", "score_type"]].sort_values("formation_date")
    chg_out.to_csv(OUT / "rows_changed.csv", index=False)
    by_bucket = added.groupby("bucket").size().reindex(rob.MAIN, fill_value=0).rename("rows_added").rename_axis("bucket").reset_index()
    by_year = added.assign(year=added.formation_date.dt.year).groupby(["year", "bucket"]).size().unstack(fill_value=0).reindex(columns=rob.MAIN, fill_value=0)
    by_year["all"] = by_year.sum(axis=1)
    by_year = by_year.reset_index()
    by_name = added.groupby("conm").agg(rows=("permno", "size"), first=("formation_date", lambda s: s.min().year), last=("formation_date", lambda s: s.max().year), High=("bucket", lambda s: (s == "High").sum()), Middle=("bucket", lambda s: (s == "Middle").sum()), Low=("bucket", lambda s: (s == "Low").sum())).reset_index().sort_values("rows", ascending=False)

    # REIT coverage
    ur = m[m.is_reit].merge(base[key].assign(headline_scored=True), on=key, how="left")
    ur["headline_scored"] = ur.headline_scored.fillna(False).astype(bool)
    cov_year = ur.assign(year=ur.formation_date.dt.year).groupby("year").agg(reit_rows=("permno", "size"), scored_before=("headline_scored", "sum"), scored_after=("scored", "sum")).reset_index()
    cov_sector = ur.groupby("gsector").agg(reit_rows=("permno", "size"), scored_before=("headline_scored", "sum"), scored_after=("scored", "sum")).reset_index()
    cov_all = {"reit_rows": len(ur), "before": int(ur.headline_scored.sum()), "after": int(ur.scored.sum())}
    # Why REIT rows stay unscored: the latest fiscal year available on the date
    latest = d.sort_values(["avail_date", "datadate"])
    un = ur[~ur.scored].sort_values("formation_date").drop(columns=[c for c in ["avail_date", "datadate", "fyear", "conm", "F_SCORE", "score_type", "age_months"] if c in ur])
    un = pd.merge_asof(un, latest[["gvkey", "avail_date", "fyear", "conm", "datadate", "substitute_needed", "substitute_failure", "F_SCORE_SUB"] + EIGHT], left_on="formation_date", right_on="avail_date", by="gvkey", direction="backward")
    def why(x):
        if pd.isna(x.avail_date):
            return "no fiscal year available"
        if pd.notna(x.F_SCORE_SUB):
            return "latest available score too old"
        if x.substitute_needed:
            return f"substitute uncomputable: {x.substitute_failure}"
        return "another signal uncomputable"
    un["reason"] = un.apply(why, axis=1) if len(un) else []
    why_table = un.reason.value_counts().rename_axis("reason").reset_index(name="reit_rows")
    un[["formation_date", "permno", "gvkey", "conm", "fyear", "reason"]].to_csv(OUT / "reit_rows_still_unscored.csv", index=False)

    # Pass rate of the new signal
    reit_gv = set(uni[uni.is_reit & uni.included].gvkey.dropna())
    pass_list = subs_used.F_DLIQUID_SUB.mean() if len(subs_used) else np.nan
    pool = d[d.gvkey.isin(reit_gv) & d.substitute_usable]
    pass_table = pd.DataFrame([{"set": "List rows that use the signal", "rows": len(subs_used), "pass_pct": 100 * pass_list},
                               {"set": "Company-years of REIT names where it is computable", "rows": len(pool), "pass_pct": 100 * pool.F_DLIQUID_SUB.mean()}])
    py = subs_used.assign(year=subs_used.formation_date.dt.year).groupby("year").F_DLIQUID_SUB.agg(["size", "mean"]).reset_index()
    py["pass_pct"] = 100 * py["mean"]
    py = py[["year", "size", "pass_pct"]].rename(columns={"size": "rows"})

    # Uncomputable substitute, company-years of REIT names
    fail = d[d.gvkey.isin(reit_gv) & d.substitute_needed & ~d.substitute_usable]
    fail_table = fail.substitute_failure.value_counts().rename_axis("reason").reset_index(name="company_years")
    fail[["gvkey", "conm", "fyear", "che", "lt", "substitute_failure"]].sort_values(["conm", "fyear"]).to_csv(OUT / "substitute_uncomputable.csv", index=False)
    lt_nonpos = d[d.gvkey.isin(reit_gv) & d.substitute_needed & (d["lt"] <= 0)]

    # F_DLIQUID-alone drops that remain
    sig_cols = EIGHT + ["F_DLIQUID"]
    alone = d[d[sig_cols].isna().sum(axis=1).eq(1) & d.F_DLIQUID.isna()]
    used_keys = set(zip(subs_used.gvkey, subs_used.fyear))
    alone_used = alone[[k in used_keys for k in zip(alone.gvkey, alone.fyear)]]
    # List rows whose latest available year misses only liquidity
    def list_alone(frame, label):
        z = frame[~frame.scored].sort_values("formation_date").drop(columns=[c for c in ["avail_date", "datadate", "fyear", "conm", "F_SCORE", "score_type", "age_months"] if c in frame])
        z = pd.merge_asof(z, latest[["gvkey", "avail_date", "substitute_needed", "F_SCORE_SUB"]], left_on="formation_date", right_on="avail_date", by="gvkey", direction="backward")
        return {"set": label, "included_rows_unscored": len(z), "of_which_only_liquidity_missing": int(z.substitute_needed.fillna(False).astype(bool).sum())}
    base_all = a.merge(uni[key + ["is_reit"]], on=key)
    list_left = pd.DataFrame([list_alone(base_all, "Headline"), list_alone(m, "This variant, all rows"), list_alone(m[m.is_reit], "This variant, REIT rows"), list_alone(m[~m.is_reit], "This variant, non-REIT rows")])

    # Comparison
    show = ["High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_annual", "High_minus_Benchmark_alpha", "High_minus_Benchmark_alpha_t", "High_sharpe", "Benchmark_sharpe", "High_CAGR", "Benchmark_CAGR", "information_ratio", "Spread_annual", "Spread_alpha_annual", "Spread_alpha_t", "High_beats_Benchmark_years", "complete_years", "High_turnover_two_way",
            "High_names_median", "High_names_min", "High_dates_under_minimum", "Middle_names_median", "Low_names_median", "Low_names_min", "Low_dates_under_minimum", "Benchmark_names_median", "Benchmark_names_min"]
    comp = pd.DataFrame([{"metric": k, "headline": row0[k], "variant": row1[k], "change": row1[k] - row0[k]} for k in show])
    comp.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    comp.to_csv(OUT / "comparison.csv", index=False)
    sub_table = pd.concat([pd.DataFrame(subs0).assign(run="headline"), pd.DataFrame(subs1).assign(run=v["label"])])
    sub_table.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    sub_table.to_csv(OUT / "subperiods.csv", index=False)

    x = t1.copy()
    x.insert(0, "universe_label", cfg.UNIVERSE_LABEL)
    x.insert(1, "variant", v["label"])
    x.to_csv(OUT / "portfolio_returns.csv", index=False)
    turn1.to_csv(OUT / "portfolio_turnover.csv", index=False)
    cnt1.to_csv(OUT / "bucket_counts.csv", index=False)
    exits1.to_csv(OUT / "portfolio_exits.csv", index=False)
    out_cols = ["formation_date", "permno", "permco", "gvkey", "conm", "mktcap", "rank", "gsector", "is_reit", "score_type", "fyear", "datadate", "avail_date", "age_months", "F_SCORE", "bucket"]
    held[out_cols].to_parquet(OUT / "formation.parquet", index=False)
    thin = cnt1[cnt1.under_minimum][["formation_date", "bucket", "names"]]
    thin.to_csv(OUT / "thin_buckets.csv", index=False)

    after = {p: sha(p) for p in before}
    moved = [str(p.relative_to(ROOT)) for p in before if before[p] != after[p]]

    md = rob.md_table
    L = [f"# Labelled variant `{v['label']}`: {cfg.UNIVERSE_LABEL}\n",
         "**Not the headline, and not a blind test.** The user chose this rule after similar variants had been seen. Terms: a **REIT** is a real estate investment trust; **F_DLIQUID** is the test that the current ratio rose, which REITs usually cannot compute; **che** is cash and short-term investments and **lt** is total liabilities; **alpha** is return left after the six factors; a **t-stat** beyond about 2 is treated as significant.\n",
         f"**Rule.** For an included row whose CRSP issuer type on the formation date is `{cfg.REIT_ISSUER_TYPE}` and whose F_DLIQUID cannot be computed: the signal passes if che / lt rose, on the same one-year and stub rules. Null che, or null or non-positive lt, leaves it uncomputable and the company-year drops. Standard buckets, 0-9. Mortgage REITs stay excluded, and availability and age rules are unchanged. Other firms with no liquidity signal stay dropped.\n",
         f"June 2005 to December 2025 on CRSP, net of costs; the 2025 portfolio is partial (7 of 12 months). Separate from the 2026 extension.\n",
         f"**Headline unchanged:** files hashed before and after this run: {'all identical' if not moved else 'CHANGED: ' + str(moved)}. The engine reproduces `portfolio_returns.csv` to {gap:.1e}.\n",
         f"Null return rule: {flat if flat else 'not used; General Growth May 2009 is not held in this variant'}.\n",
         "## Comparison with the headline\n", md(comp.drop(columns="universe_label"), 4),
         "\n## Subperiods\n", md(sub_table.drop(columns="universe_label")[["run", "period", "months", "High_alpha_annual", "High_alpha_t", "High_minus_Benchmark_annual", "High_sharpe", "Benchmark_sharpe", "Spread_alpha_annual", "Spread_alpha_t"]], 4),
         f"\n## Rows added: {len(added)}\n", md(by_bucket), "\n### By formation year\n", md(by_year), f"\n### By name ({by_name.shape[0]} companies)\n", md(by_name),
         f"\nEvery row is in `rows_added.csv`. Headline rows that changed fiscal year, score or bucket because a newer substitute score now applies: {len(changed)}. Headline rows lost: {len(gone)}.\n"]
    if len(changed):
        L.append(md(chg_out))
    L += [f"\n## REIT coverage\n", f"Included REIT rows: {cov_all['reit_rows']}. Scored before {cov_all['before']} ({100 * cov_all['before'] / cov_all['reit_rows']:.1f}%), after {cov_all['after']} ({100 * cov_all['after'] / cov_all['reit_rows']:.1f}%).\n",
          md(cov_sector), "\n", md(cov_year), "\n### Why the remaining REIT rows are unscored\n", md(why_table) if len(why_table) else "None.\n",
          f"\n## Pass rate of the new signal\n", md(pass_table, 1), "\n", md(py, 1),
          f"\n## Substitute uncomputable, company-years of REIT names: {len(fail)}\n", md(fail_table) if len(fail_table) else "None.\n",
          f"\nNon-positive lt among those needing the signal: {len(lt_nonpos)}. Each case is in `substitute_uncomputable.csv`.\n",
          "\n## F_DLIQUID-alone drops that remain\n",
          f"Company-years, FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}, with only F_DLIQUID missing: {len(alone)}. Of these, {len(alone_used)} now supply a score on an included list. The rest, {len(alone) - len(alone_used)}, stay dropped from every list: non-REITs, or REIT company-years never chosen on a date or with no computable substitute.\n",
          md(list_left),
          f"\n## Thin buckets (under {cfg.MIN_BUCKET_NAMES} names): {len(thin)}\n", md(thin) if len(thin) else "None.\n"]
    (OUT / "results.md").write_text("\n".join(L), encoding="utf-8")

    print(comp[["metric", "headline", "variant", "change"]].round(4).to_string(index=False))
    print(by_bucket.to_string(index=False))
    print(f"added={len(added)} changed={len(changed)} gone={len(gone)} coverage={cov_all} alone={len(alone)} alone_used={len(alone_used)} thin={len(thin)} hashes_changed={moved}")
    sys.exit(1 if moved else 0)


def scores_full():
    return rob.scores_mod.compute_scores(pd.read_parquet(CLEAN / "fundamentals_clean.parquet"))


rob = load("08_robustness.py", "rob")

if __name__ == "__main__":
    main()
