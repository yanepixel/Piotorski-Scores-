"""
spec_v2, step 2: v2 F-scores and the score-to-list alignment (CLAUDE.md section 8f, SPEC_V2 in config.py). No return value is read.

Reads:  data/clean/fundamentals_clean.parquet, universe.parquet, fscores.parquet, formation.parquet (v1, read only), data/raw/comp_funda_ib.parquet,
        data/raw/crsp_msf_v2.parquet (only to count missing-return rows in holding windows, never a return)
Output: data/clean/spec_v2/fscores_v2.parquet, formation_v2.parquet
Usage:  python 12b_spec_v2_scores.py [--rule net|literal]   (default net = SPEC_V2 issuance_field; literal = SPEC_V2 issuance_sensitivity, files get a _literal suffix)
Tables: output/spec_v2/score_distribution_v2.csv, signal_pass_rates_v2.csv, eq_offer_pass_by_year.csv, list_rows_by_bucket_v1_v2.csv, list_rows_bucket_transition.csv,
        list_rows_by_date_v1_v2.csv, unscorable_no_filing_date.csv
Report: output/spec_v2/scores_checks_v2.md (the report to read before any return)
Exit code is 1 if a check fails.

Differences from v1, all from SPEC_V2: ib replaces ni; F_EQ_OFFER = 1 if sstk - prstkc <= 0, null counting 0 (net rule; the literal rule, 1 only if sstk is 0 or null, is the sensitivity); the zero-debt override needs the prior-year change to be computable;
a firm-year with no real 10-K filing date is unscorable; a filing counts only if filing date + availability_buffer_days is on or before the formation date.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
V2CLEAN = CLEAN / "spec_v2"
OUT = ROOT / cfg.SPEC_V2["output_dir"]
V2 = cfg.SPEC_V2
LIT_PASS = "n/a"  # literal pass rate over scored company-years, read from the literal run
RULE = "net"      # set in main(); "net" or "literal"
SUF = ""          # "" for the net rule, "_literal" for the sensitivity


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SC = load("04_scores.py", "v1_scores")
SIGNALS = SC.SIGNALS
HIGH, LOW = cfg.HIGH_SCORES, cfg.LOW_SCORES


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def bucket_of(score):
    if pd.isna(score):
        return "Unscored"
    return "High" if score in HIGH else "Low" if score in LOW else "Middle"


def lag_inputs(df):
    """04_scores.lag_inputs with ib added to the lagged fields; same pair and stub rules."""
    d = SC.lag_inputs(df)
    g = d.sort_values(["gvkey", "fyear"]).groupby("gvkey")
    d["ib_lag1"] = g["ib"].shift(1).where(d.pair_ok)
    return d


def compute_scores_v2(df):
    d = lag_inputs(df)
    d["ROA"] = d.ib / d.at_lag1
    d["CFO"] = d.oancf / d.at_lag1
    d["ROA_lag1"] = d.ib_lag1 / d.at_lag2
    d["DROA"] = d.ROA - d.ROA_lag1
    d["ACCRUAL"] = d.CFO - d.ROA
    d["LEVER"] = d.dltt / ((d["at"] + d.at_lag1) / 2)
    d["LEVER_lag1"] = d.dltt_lag1 / ((d.at_lag1 + d.at_lag2) / 2)
    d["DLEVER"] = d.LEVER - d.LEVER_lag1
    d["LIQUID"] = d.act / d.lct
    d["LIQUID_lag1"] = d.act_lag1 / d.lct_lag1
    d["DLIQUID"] = d.LIQUID - d.LIQUID_lag1
    d["MARGIN"] = ((d.sale - d.cogs) / d.sale).where(d.sale > cfg.MIN_SALE_FOR_MARGIN)
    d["MARGIN_lag1"] = ((d.sale_lag1 - d.cogs_lag1) / d.sale_lag1).where(d.sale_lag1 > cfg.MIN_SALE_FOR_MARGIN)
    d["DMARGIN"] = d.MARGIN - d.MARGIN_lag1
    d["TURN"] = d.sale / d.at_lag1
    d["TURN_lag1"] = d.sale_lag1 / d.at_lag2
    d["DTURN"] = d.TURN - d.TURN_lag1
    ratios = ["ROA", "CFO", "ROA_lag1", "DROA", "ACCRUAL", "LEVER", "LEVER_lag1", "DLEVER", "LIQUID", "LIQUID_lag1", "DLIQUID", "MARGIN", "MARGIN_lag1", "DMARGIN", "TURN", "TURN_lag1", "DTURN"]
    d[ratios] = d[ratios].replace([np.inf, -np.inf], np.nan)

    def signal(test, value):
        return test.astype(float).where(value.notna())

    d["F_ROA"] = signal(d.ROA > 0, d.ROA)
    d["F_CFO"] = signal(d.CFO > 0, d.CFO)
    d["F_DROA"] = signal(d.DROA > 0, d.DROA)
    d["F_ACCRUAL"] = signal(d.CFO > d.ROA, d.ACCRUAL)
    d["F_DLEVER"] = signal(d.DLEVER < 0, d.DLEVER)
    d["zero_debt_pass"] = False
    if cfg.ZERO_DEBT_COUNTS_AS_PASS:
        if V2["zero_debt_requires_lag2"]:
            can_change = d.LEVER.notna() & d.LEVER_lag1.notna()   # needs assets one and two years back, so the prior-year inputs exist
        else:
            can_change = pd.Series(True, index=d.index)
        d["zero_debt_pass"] = (d.dltt == 0) & (d.dltt_lag1 == 0) & can_change
        d.loc[d.zero_debt_pass, "F_DLEVER"] = 1.0
    d["F_DLIQUID"] = signal(d.DLIQUID > 0, d.DLIQUID)
    if V2["issuance_field"] != "sstk_net_of_prstkc" or V2["issuance_sensitivity"] != "sstk_literal":
        raise ValueError("spec_v2 issuance rules are not the ones this script implements")
    d["sstk_positive"] = d.sstk > 0
    d["sstk_negative"] = d.sstk < 0
    d["net_issue"] = d.sstk.fillna(0) - d.prstkc.fillna(0)
    if RULE == "net":
        d["F_EQ_OFFER"] = (d.net_issue <= 0).astype(float)           # 1 if sstk - prstkc <= 0, nulls count 0
    else:
        d["F_EQ_OFFER"] = (~(d.sstk.fillna(0) != 0)).astype(float)   # 1 if sstk is 0 or null; negative or positive fails
    d["F_DMARGIN"] = signal(d.DMARGIN > 0, d.DMARGIN)
    d["F_DTURN"] = signal(d.DTURN > 0, d.DTURN)
    d["signals_computable"] = d[SIGNALS].notna().sum(axis=1)
    if cfg.MISSING_SIGNAL_RULE != "drop":
        raise ValueError(f"Unknown MISSING_SIGNAL_RULE {cfg.MISSING_SIGNAL_RULE}")
    d["F_SCORE_computed"] = d[SIGNALS].sum(axis=1).where(d.signals_computable == len(SIGNALS))
    d["no_filing_date"] = d.filing_date.isna()
    d["F_SCORE"] = d.F_SCORE_computed.where(~d.no_filing_date)   # no real 10-K date: unscorable, no fallback
    d["avail_date_v2"] = d.filing_date + pd.Timedelta(days=V2["availability_buffer_days"])
    return d[d.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY)].copy()


def align(s, u):
    """05_align.py rule with the buffered availability date: latest scorable year known by the formation date, not too old."""
    keep = ["gvkey", "avail_date_v2", "filing_date", "datadate", "fyear", "F_SCORE"] + SIGNALS
    scored = s[s.F_SCORE.notna()][keep].sort_values(["avail_date_v2", "datadate"])
    inc = u[u.included].sort_values("formation_date")
    m = pd.merge_asof(inc, scored, left_on="formation_date", right_on="avail_date_v2", by="gvkey", direction="backward")
    m["age_months"] = (m.formation_date.dt.year - m.datadate.dt.year) * 12 + (m.formation_date.dt.month - m.datadate.dt.month)
    m["score_status"] = "missing"
    m.loc[m.datadate.notna(), "score_status"] = "stale"
    m.loc[m.age_months <= cfg.MAX_SCORE_AGE_MONTHS, "score_status"] = "valid"
    m.loc[m.score_status != "valid", ["F_SCORE"] + SIGNALS] = np.nan
    m["scored"] = m.score_status == "valid"
    m["bucket"] = m.F_SCORE.map(bucket_of)
    return m


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    V2CLEAN.mkdir(parents=True, exist_ok=True)
    failures = []

    fund = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
    global RULE, SUF
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rule", choices=["net", "literal"], default="net")
    RULE = ap.parse_args().rule
    SUF = "" if RULE == "net" else "_literal"
    global LIT_PASS
    lit = V2CLEAN / "fscores_v2_literal.parquet"
    if RULE == "net" and lit.exists():
        ls = pd.read_parquet(lit, columns=["F_SCORE", "F_EQ_OFFER"])
        LIT_PASS = f"{100 * ls.loc[ls.F_SCORE.notna()].F_EQ_OFFER.mean():.1f}%"
    ib = pd.read_parquet(RAW / "comp_funda_ib.parquet")
    pk = pd.read_parquet(RAW / "comp_funda_prstkc.parquet")
    pk["prstkc"] = pk.prstkc.astype(float)
    ib["ib"] = ib.ib.astype(float)
    fund = fund.merge(ib[["gvkey", "datadate", "fyear", "ib"]].assign(fyear=lambda x: x.fyear.astype(int)), on=["gvkey", "datadate", "fyear"], how="left", validate="1:1")
    fund = fund.merge(pk[["gvkey", "datadate", "fyear", "prstkc"]].assign(fyear=lambda x: x.fyear.astype(int)), on=["gvkey", "datadate", "fyear"], how="left", validate="1:1")
    if fund.prstkc.isna().sum() != pk.prstkc.isna().sum():
        failures.append("prstkc merge changed the null count")
    if fund.ib.isna().sum() != fund.ni.isna().sum():
        failures.append("ib and ni differ in how many rows are null")
    universe = pd.read_parquet(CLEAN / "universe.parquet")
    v1s = pd.read_parquet(CLEAN / "fscores.parquet")
    v1f = pd.read_parquet(CLEAN / "formation.parquet")

    s = compute_scores_v2(fund)
    s.to_parquet(V2CLEAN / f"fscores_v2{SUF}.parquet", index=False)
    m = align(s, universe)
    out_cols = ["formation_date", "permno", "permco", "gvkey", "mktcap", "rank", "gsector", "score_status", "scored", "bucket", "fyear", "datadate", "filing_date", "avail_date_v2", "age_months", "F_SCORE"] + SIGNALS
    m[out_cols].sort_values(["formation_date", "rank"]).reset_index(drop=True).to_parquet(V2CLEAN / f"formation_v2{SUF}.parquet", index=False)

    # --- Checks ---
    scored = s.F_SCORE.notna()
    if s.duplicated(["gvkey", "fyear"]).any():
        failures.append("Duplicate gvkey-fyear rows")
    if not s.F_SCORE.dropna().between(0, 9).all():
        failures.append("F_SCORE outside 0-9")
    if not (s.loc[scored, SIGNALS].sum(axis=1) == s.loc[scored, "F_SCORE"]).all():
        failures.append("F_SCORE differs from the sum of its signals")
    if (s[scored].stub_flag).any():
        failures.append("A flagged fiscal year was scored")
    if s[scored].filing_date.isna().any():
        failures.append("A score exists with no filing date")
    valid = m[m.scored]
    if (valid.avail_date_v2 > valid.formation_date).any():
        failures.append("A score is attached before its buffered availability date")
    if ((valid.formation_date - valid.filing_date).dt.days < V2["availability_buffer_days"]).any():
        failures.append("A filing less than the buffer before the formation date is used")
    if (valid.datadate >= valid.formation_date).any() or (valid.age_months > cfg.MAX_SCORE_AGE_MONTHS).any():
        failures.append("A valid score is too late or too old")
    if len(m) != int(universe.included.sum()) or m.duplicated(["formation_date", "permco"]).any():
        failures.append("Included rows do not match the universe")
    # Negative sstk / prstkc handling. Counted and sized below; not a check failure.
    def bucket_moves(rows, alt_pass):
        """List rows whose bucket would change if F_EQ_OFFER took the alternative value alt_pass (bool Series aligned to rows)."""
        alt = rows.F_SCORE - rows.F_EQ_OFFER + alt_pass.astype(float)
        return int((rows.F_SCORE.map(bucket_of) != alt.map(bucket_of)).sum())
    neg = s[s.sstk_negative]
    neg_list = valid.merge(neg[["gvkey", "fyear"]], on=["gvkey", "fyear"], how="inner")
    vs = valid.merge(s[["gvkey", "fyear", "sstk", "prstkc", "net_issue"]], on=["gvkey", "fyear"], how="left")
    if RULE == "net":
        neg_alt_changes = int((neg_list.F_EQ_OFFER == 1).sum())   # rows with negative sstk that pass under the net rule
        floor_alt = (vs.sstk.clip(lower=0).fillna(0) - vs.prstkc.fillna(0) <= 0)   # negative sstk floored at 0 before netting
        floor_moves = bucket_moves(vs, floor_alt)
        floor_changes = int((floor_alt.astype(float) != vs.F_EQ_OFFER).sum())
        null_pr_issuer = vs[vs.prstkc.isna() & (vs.sstk > 0)]   # fails only because a missing buyback counts 0
        null_pr_moves = bucket_moves(null_pr_issuer, pd.Series(True, index=null_pr_issuer.index))
    else:
        alt = neg_list.F_SCORE + 1   # the same row if a negative value passed instead
        neg_bucket_moves = int((neg_list.F_SCORE.map(bucket_of) != alt.map(bucket_of)).sum())

    # --- Pre-return report ---
    v1_scored = v1s.F_SCORE.notna()
    dist = pd.DataFrame({"F_SCORE": range(10)})
    dist["v1_company_years"] = v1s.loc[v1_scored].F_SCORE.value_counts().reindex(range(10), fill_value=0).values
    dist["v2_company_years"] = s.loc[scored].F_SCORE.value_counts().reindex(range(10), fill_value=0).values
    dist["v1_list_rows"] = v1f[v1f.scored].F_SCORE.value_counts().reindex(range(10), fill_value=0).values
    dist["v2_list_rows"] = valid.F_SCORE.value_counts().reindex(range(10), fill_value=0).values
    for c in ["v1_company_years", "v2_company_years", "v1_list_rows", "v2_list_rows"]:
        dist[c.replace("company_years", "company_years_pct").replace("list_rows", "list_rows_pct")] = (100 * dist[c] / dist[c].sum()).round(2)
    dist.to_csv(OUT / f"score_distribution_v2{SUF}.csv", index=False)
    mean_v1, mean_v2 = v1s.F_SCORE.mean(), s.F_SCORE.mean()

    rates = pd.DataFrame({"signal": SIGNALS})
    rates["v1_pass_pct_scored"] = [round(100 * v1s.loc[v1_scored, c].mean(), 1) for c in SIGNALS]
    rates["v2_pass_pct_scored"] = [round(100 * s.loc[scored, c].mean(), 1) for c in SIGNALS]
    rates["v1_computable"] = [int(v1s[c].notna().sum()) for c in SIGNALS]
    rates["v2_computable"] = [int(s[c].notna().sum()) for c in SIGNALS]
    rates.to_csv(OUT / f"signal_pass_rates_v2{SUF}.csv", index=False)

    ok = s.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY)
    byy = s[ok].groupby("fyear").agg(company_years=("gvkey", "size"), sstk_null_pct=("sstk", lambda x: round(100 * x.isna().mean(), 1)),
                                      sstk_positive_pct=("sstk_positive", lambda x: round(100 * x.mean(), 1)), v2_eq_offer_pass_pct=("F_EQ_OFFER", lambda x: round(100 * x.mean(), 1)))
    byy["v2_eq_offer_pass_pct_scored"] = s[scored].groupby("fyear").F_EQ_OFFER.mean().mul(100).round(1)
    byy["v1_eq_offer_pass_pct_scored"] = v1s[v1_scored].groupby("fyear").F_EQ_OFFER.mean().mul(100).round(1)
    byy["v1_eq_offer_pass_pct_computable"] = v1s.groupby("fyear").F_EQ_OFFER.mean().mul(100).round(1)
    byy = byy.reset_index()
    byy.to_csv(OUT / f"eq_offer_pass_by_year{SUF}.csv", index=False)
    lst = valid.assign(formation_year=valid.formation_date.dt.year).groupby("formation_year").F_EQ_OFFER.mean().mul(100).round(1).rename("v2_eq_offer_pass_pct_list_rows")
    lst1 = v1f[v1f.scored].assign(formation_year=lambda x: x.formation_date.dt.year).groupby("formation_year").F_EQ_OFFER.mean().mul(100).round(1).rename("v1_eq_offer_pass_pct_list_rows")
    by_list = pd.concat([lst1, lst], axis=1).reset_index()

    # Unscorable: no real 10-K filing date
    nofile = s[s.no_filing_date]
    v1_fallback_listed = v1f[v1f.scored & (v1f.avail_source == "fallback")]
    nf = nofile.assign(v1_scored=nofile.F_SCORE_computed.notna() & True)
    unscor = nofile[["gvkey", "conm", "fyear", "datadate", "at", "F_SCORE_computed"]].rename(columns={"F_SCORE_computed": "would_be_score"}).sort_values(["gvkey", "fyear"])
    unscor["v1_list_dates_using_it"] = [", ".join(str(x.date()) for x in v1f[(v1f.gvkey == r.gvkey) & (v1f.fyear == r.fyear) & v1f.scored & (v1f.avail_source == "fallback")].formation_date) for r in unscor.itertuples()]
    unscor.to_csv(OUT / f"unscorable_no_filing_date{SUF}.csv", index=False)
    in_range_rows = int(ok.sum())
    n_nofile, n_nofile_comp = len(nofile), int(nofile.F_SCORE_computed.notna().sum())

    # Alignment changes versus v1
    key = ["formation_date", "permco"]
    cmp = v1f[key + ["scored", "F_SCORE", "fyear"]].rename(columns={"scored": "scored_v1", "F_SCORE": "F_v1", "fyear": "fy_v1"}).merge(
        m[key + ["scored", "F_SCORE", "fyear", "bucket", "score_status"]].rename(columns={"scored": "scored_v2", "F_SCORE": "F_v2", "fyear": "fy_v2", "bucket": "bucket_v2", "score_status": "status_v2"}), on=key, validate="1:1")
    cmp["bucket_v1"] = cmp.F_v1.map(bucket_of)
    if len(cmp) != len(m):
        failures.append("v1 and v2 included rows do not line up")
    order = ["High", "Middle", "Low", "Unscored"]
    byb = pd.DataFrame({"bucket": order})
    byb["v1_rows"] = [int((cmp.bucket_v1 == b).sum()) for b in order]
    byb["v2_rows"] = [int((cmp.bucket_v2 == b).sum()) for b in order]
    byb["change"] = byb.v2_rows - byb.v1_rows
    byb["in_from_other_bucket"] = [int(((cmp.bucket_v2 == b) & (cmp.bucket_v1 != b)).sum()) for b in order]
    byb["out_to_other_bucket"] = [int(((cmp.bucket_v1 == b) & (cmp.bucket_v2 != b)).sum()) for b in order]
    byb.to_csv(OUT / f"list_rows_by_bucket_v1_v2{SUF}.csv", index=False)
    trans = pd.crosstab(cmp.bucket_v1, cmp.bucket_v2).reindex(index=order, columns=order, fill_value=0)
    trans.index.name = "v1_bucket_to_v2_bucket"
    trans.reset_index().to_csv(OUT / f"list_rows_bucket_transition{SUF}.csv", index=False)
    bydate = cmp.groupby("formation_date").apply(lambda g: pd.Series({f"{b}_{v}": int((g[f"bucket_{v}"] == b).sum()) for b in order for v in ["v1", "v2"]}), include_groups=False).reset_index()
    bydate.to_csv(OUT / f"list_rows_by_date_v1_v2{SUF}.csv", index=False)
    status = pd.crosstab(cmp.scored_v1.map({True: "v1 scored", False: "v1 not scored"}), cmp.status_v2).reset_index()

    # Timing items
    gap = (valid.formation_date - valid.filing_date).dt.days
    v1_on_date = int((v1f.scored & (v1f.avail_date == v1f.formation_date)).sum())
    v1_within_buffer = v1f[v1f.scored & (v1f.avail_source == "filing") & ((v1f.formation_date - v1f.filing_date if "filing_date" in v1f else (v1f.formation_date - v1f.avail_date)).dt.days < V2["availability_buffer_days"])]
    older_v2 = 0
    f_known = s[["gvkey", "fyear", "avail_date_v2"]].dropna(subset=["avail_date_v2"])
    for r in valid.itertuples():
        k = f_known[(f_known.gvkey == r.gvkey) & (f_known.avail_date_v2 <= r.formation_date)]
        if len(k) and k.fyear.max() > r.fyear:
            older_v2 += 1
    # Rows whose newest scorable filing fell inside the buffer (filed on or before the formation date, but less than the buffer before it)
    buf = pd.Timedelta(days=V2["availability_buffer_days"])
    inbuf = s[s.F_SCORE.notna() & s.filing_date.notna()][["gvkey", "fyear", "filing_date"]]
    buffer_rows = m.merge(inbuf, on="gvkey", how="inner", suffixes=("", "_b"))
    buffer_rows = buffer_rows[(buffer_rows.filing_date_b <= buffer_rows.formation_date) & (buffer_rows.filing_date_b + buf > buffer_rows.formation_date)]
    buffer_rows = buffer_rows.sort_values("fyear_b").groupby(["formation_date", "permco"]).tail(1)
    buf_earlier = int(((buffer_rows.score_status == "valid") & (buffer_rows.fyear < buffer_rows.fyear_b)).sum())
    buf_stale = int((buffer_rows.score_status == "stale").sum())
    buf_none = int((buffer_rows.score_status == "missing").sum())

    # Missing-return rows in the all-included windows (counts only; no return value is read)
    msf = pd.read_parquet(RAW / "crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretflg", "issuernm"])
    msf = msf[msf.mthcaldt <= pd.Timestamp(cfg.RETURNS_END)].copy()
    msf["month"] = msf.mthcaldt.dt.to_period("M")
    nullrows = msf[msf.mthret.isna()][["permno", "month", "mthretflg", "issuernm"]]
    null_cases = []
    for x in m.itertuples():
        start = x.formation_date.to_period("M") + 1
        months = pd.period_range(start, min(start + cfg.HOLDING_MONTHS - 1, pd.Period(cfg.RETURNS_END, "M")), freq="M")
        hit = nullrows[(nullrows.permno == x.permno) & nullrows.month.isin(months)]
        if len(hit):
            null_cases.append({"formation_date": x.formation_date.date(), "permno": x.permno, "name": hit.issuernm.iloc[0], "null_months": ", ".join(map(str, hit.month)), "flag": hit.mthretflg.iloc[0],
                               "v2_status": x.score_status, "v2_bucket": x.bucket, "approved_hold_flat": x.permno in {p for v in cfg.NULL_RETURN_HOLD_FLAT_MONTHS.values() for p in v if v} and str(hit.month.iloc[0]) in {mm for v in cfg.NULL_RETURN_HOLD_FLAT_MONTHS.values() for ms in v.values() for mm in ms}})
    null_cases = pd.DataFrame(null_cases)

    per = m.groupby("formation_date").agg(included=("permco", "size"), scored=("scored", "sum")).reset_index()
    L = [f"# spec_v2 scores: report before any return is read\n", f"Label `{V2['label']}`, rules in `SPEC_V2` (config.py) and CLAUDE.md section 8f. No return value was read to produce this file. **{len(failures)} check failure(s).**\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## 1. F-score distribution, v1 beside v2\n")
    L.append(f"Company-years scored FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}: v1 {int(v1_scored.sum())}, v2 {int(scored.sum())} (of {in_range_rows}). Mean score v1 {mean_v1:.2f}, v2 {mean_v2:.2f}. Median v1 {v1s.F_SCORE.median():.0f}, v2 {s.F_SCORE.median():.0f}. List rows scored: v1 {int(v1f.scored.sum())}, v2 {len(valid)} (of {len(m)}).\n")
    L.append(md_table(dist))
    L.append("\n## 2. Signal pass rates (share passing, scored company-years)\n")
    L.append(md_table(rates))
    ok_s = s[ok]
    if RULE == "net":
        L.append("\n## 3. F_EQ_OFFER, v1 (shares up no more than 2%) against v2 net rule (1 if sstk - prstkc <= 0, null counts 0), by fiscal year\n")
        L.append(f"Company-years FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}: sstk null {100 * ok_s.sstk.isna().mean():.1f}%, sstk positive {100 * ok_s.sstk_positive.mean():.1f}%, sstk negative {int(ok_s.sstk_negative.sum())}; "
                 f"prstkc null {100 * ok_s.prstkc.isna().mean():.1f}%, positive {100 * (ok_s.prstkc > 0).mean():.1f}%, negative {int((ok_s.prstkc < 0).sum())}. Net issue (sstk - prstkc, nulls as 0): positive {100 * (ok_s.net_issue > 0).mean():.1f}%, zero {100 * (ok_s.net_issue == 0).mean():.1f}%, negative {100 * (ok_s.net_issue < 0).mean():.1f}%. "
                 f"Nulls count 0, so the signal is always computable (v1 dropped {int(v1s.F_EQ_OFFER.isna().sum())} company-years on this signal).\n")
        yr = s[scored].groupby("fyear").F_EQ_OFFER.mean() * 100
        L.append(f"**Degenerate?** Pass rate over scored company-years {s[scored].F_EQ_OFFER.mean() * 100:.1f}% (v1 {100 * v1s.loc[v1_scored].F_EQ_OFFER.mean():.1f}%, literal sensitivity {LIT_PASS}). By fiscal year it ranges from {yr.min():.1f}% (FY{int(yr.idxmin())}) to {yr.max():.1f}% (FY{int(yr.idxmax())}). "
                 f"The signal would be degenerate if it passed almost everyone or almost no one, or drifted across years so it mostly dated the filing; the table below shows which.\n")
        L.append(f"**Negative sstk and prstkc.** Negative prstkc: {int((s.prstkc < 0).sum())}. Negative sstk: {len(neg)} company-years in range, {int(neg.F_SCORE.notna().sum())} scored, {len(neg_list)} included list rows use one; "
                 f"used as reported, a negative sstk lowers the net, and {neg_alt_changes} of those list rows pass because of it. If negative sstk were floored at 0 before netting, F_EQ_OFFER would change on {floor_changes} list rows and the bucket on {floor_moves}. "
                 f"**Null prstkc with positive sstk** (buyback counted 0, so the row fails): {len(null_pr_issuer)} list rows; if those passed instead, {null_pr_moves} would change bucket. Applied as locked in CLAUDE.md section 8f.\n")
    else:
        L.append("\n## 3. F_EQ_OFFER, v1 (shares up no more than 2%) against v2 literal sensitivity (sstk is 0 or null), by fiscal year\n")
        L.append(f"sstk is null on {100 * s[ok].sstk.isna().mean():.1f}% of company-years and positive on {100 * s[ok].sstk_positive.mean():.1f}%. Negative sstk: {int(s.sstk_negative.sum())}. A null passes by the spec, so the signal is always computable in v2 (v1 dropped {int(v1s.F_EQ_OFFER.isna().sum())} company-years on this signal).\n")
        L.append(f"**Negative sstk (not covered by the spec).** {len(neg)} company-years in the score range, {int(neg.F_SCORE.notna().sum())} of them scored, {len(neg_list)} included list rows use one. Read literally (only 0 or null passes) they fail. "
                 f"If a negative value passed instead, {neg_bucket_moves} of those list rows would change bucket.\n")
    L.append(md_table(byy))
    L.append("\nOn included list rows, by formation year:\n")
    L.append(md_table(by_list))
    L.append("\n## 4. Firm-years with no real 10-K filing date: unscorable in v2\n")
    L.append(f"FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}: {n_nofile} company-years have no filing date ({100 * n_nofile / in_range_rows:.2f}% of {in_range_rows}); {n_nofile_comp} of them would otherwise have a score. "
             f"v1 used a fallback date (year-end + {cfg.FALLBACK_LAG_DAYS} days) on {len(v1_fallback_listed)} included list rows with a score. Full list, with the v1 list dates that used each one: `output/spec_v2/unscorable_no_filing_date{SUF}.csv`.\n")
    L.append("## 5. Availability rule (filing date + buffer on or before the formation date)\n")
    L.append(f"Buffer {V2['availability_buffer_days']} days. v1 list rows scored from a filing made on the formation date itself: {v1_on_date}. v1 scored rows whose filing came less than {V2['availability_buffer_days']} days before the formation date: {len(v1_within_buffer)}. "
             f"**Older-year rows.** Rows scored from an older year than the newest filed year, by cause: (i) {older_v2} because the newest filed year is unscorable (missing signal, stub or t-2 chain); "
             f"(ii) {buf_earlier} because the newest filing fell inside the {V2['availability_buffer_days']}-day buffer (filed on or before the formation date, less than {V2['availability_buffer_days']} days earlier) and the next earlier scored year was used. "
             f"Buffer cases that did not reach a score: {buf_stale} stale (the earlier score is over {cfg.MAX_SCORE_AGE_MONTHS} months old) and {buf_none} with no earlier scored year. Total buffer cases {len(buffer_rows)}.\n")
    L.append("## 6. Change in list rows versus v1, by bucket\n")
    L.append(f"Included list rows: {len(m)}. v1 buckets use High {HIGH}, Low {LOW}, Middle the rest, as in the headline.\n")
    L.append(md_table(byb))
    L.append("\nWhere each v1 row goes in v2 (rows are v1 buckets, columns v2):\n")
    L.append(md_table(trans.reset_index()))
    L.append(f"\nRows whose bucket differs from v1: {int((cmp.bucket_v1 != cmp.bucket_v2).sum())} of {len(cmp)}. By v1 and v2 score status:\n")
    L.append(md_table(status))
    L.append(f"\nBy formation date: `output/spec_v2/list_rows_by_date_v1_v2{SUF}.csv`.\n")
    L.append("## 7. Missing-return rows in holding windows of included names (flags only, no value read)\n")
    L.append("The all-included benchmark holds unscored names, so any missing return in their windows must be handled by an approved rule or stop the run.\n")
    L.append(md_table(null_cases) if len(null_cases) else "None.\n")
    L.append("\n## 8. Included rows and scored rows per formation date\n")
    L.append(md_table(per))
    (OUT / f"scores_checks_v2{SUF}.md").write_text("\n".join(L), encoding="utf-8")

    print(f"v2 scored={int(scored.sum())}/{in_range_rows} list_scored={len(valid)}/{len(m)} nofile={n_nofile} (would-score {n_nofile_comp}) older_v2={older_v2} bucket_changes={int((cmp.bucket_v1 != cmp.bucket_v2).sum())} failures={len(failures)}")
    print(dist.to_string(index=False))
    print(byb.to_string(index=False))
    print(null_cases.to_string(index=False) if len(null_cases) else "no null-return cases")
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
