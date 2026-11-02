"""
Extension to May 2026, pull and validation: can Compustat comp.secm stand in for CRSP after December 2025?

Name-level validation only. Computes no portfolio returns, and no bucket is read or reported.
Raw:    data/raw/comp_secm_extension.parquet (new; write-once, pass --overwrite to replace)
Output: output/extension_2026/validation.md, security_map.csv, overlap_gaps_over_100bp.csv, compound_jun_dec_2025.csv,
        coverage_2026.csv, past_exits_evidence.csv
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
HERE = ROOT / "output" / cfg.EXTENSION_2026["label"]
RAW_FILE = ROOT / "data" / "raw" / "comp_secm_extension.parquet"
FIELDS = cfg.EXTENSION_PULL["fields"]
PULL_START, PULL_END = cfg.EXTENSION_PULL["start"], cfg.EXTENSION_PULL["end"]
CRSP_END = pd.Period(cfg.RETURNS_END, "M")
EXT_MONTHS = pd.period_range(CRSP_END + 1, pd.Period(cfg.EXTENSION_2026["end"], "M"), freq="M")
OVERLAP = pd.period_range(f"{CRSP_END.year}-01", CRSP_END, freq="M")
HOLD_2025 = pd.period_range(f"{cfg.LAST_FORMATION_YEAR}-{cfg.FORMATION_MONTH + 1:02d}", CRSP_END, freq="M")
BENCHMARK_CUSIPS = cfg.EXTENSION_PULL["benchmark_cusips"]
LARGE_PRICE_GAP = 0.005  # report label: closing prices differ by over 0.5%


def wrds_username():
    """Username field of the saved pgpass entry. The file is read in memory, only the username is kept, and nothing is printed or stored."""
    if os.environ.get("PGUSER"):
        return os.environ["PGUSER"]
    for path in (Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf", Path.home() / ".pgpass"):
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("wrds-pgdata"):
                    return line.split(":")[3]
    raise RuntimeError("No WRDS username: set PGUSER or create pgpass.conf")


def md(df, digits=2):
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].round(digits)
    head = "| " + " | ".join(map(str, d.columns)) + " |\n|" + "---|" * len(d.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in d.itertuples(index=False)) + "\n"


def describe_gaps(g):
    a = g.dropna()
    n = len(a)
    return {"pairs": n, "within_1bp_pct": 100 * (a.abs() <= 1).mean(), "within_10bp_pct": 100 * (a.abs() <= 10).mean(), "within_100bp_pct": 100 * (a.abs() <= 100).mean(),
            "mean_gap_bp": a.mean(), "median_gap_bp": a.median(), "mean_abs_gap_bp": a.abs().mean(), "largest_abs_gap_bp": a.abs().max()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--overwrite", action="store_true", help="Replace the extension raw file.")
    args = ap.parse_args()
    HERE.mkdir(parents=True, exist_ok=True)

    u = pd.read_parquet(ROOT / "data/clean/universe.parquet")
    fm = pd.read_parquet(ROOT / "data/clean/formation.parquet", columns=["formation_date", "permno", "gvkey", "conm", "scored"])
    last = u.formation_date.max()
    held = fm[(fm.formation_date == last) & fm.scored].copy()
    list_rows = u[u.formation_date == last]
    r = pd.read_parquet(ROOT / "data/raw/crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretx", "mthretflg", "mthdelflg", "mthprc", "cusip", "ticker", "issuernm"])
    r["month"] = r.mthcaldt.dt.to_period("M")
    r["mthret"], r["mthprc"] = r.mthret.astype(float), r.mthprc.astype(float)
    b = pd.read_parquet(ROOT / "data/raw/crsp_benchmarks.parquet", columns=["permno", "ticker", "mthcaldt", "mthret", "mthprc", "cusip"])
    b["month"] = b.mthcaldt.dt.to_period("M")
    b["mthret"], b["mthprc"] = b.mthret.astype(float), b.mthprc.astype(float)

    db = wrds.Connection(wrds_username=wrds_username())
    have = set(db.describe_table("comp", "secm").name)
    missing = [f for f in FIELDS if f not in have]
    if missing:
        sys.exit(f"comp.secm lacks {missing}")
    gv = sorted(list_rows.gvkey.dropna().unique())
    keys = ", ".join(f"'{g}'" for g in gv)
    cus = " or ".join(f"cusip like '{c}%%'" for c, _ in BENCHMARK_CUSIPS.values())
    fields = ", ".join(FIELDS)
    if RAW_FILE.exists() and not args.overwrite:
        s = pd.read_parquet(RAW_FILE)  # write-once: reuse what was pulled
    else:
        s = db.raw_sql(f"select {fields} from comp.secm where (gvkey in ({keys}) or {cus}) and datadate between '{PULL_START}' and '{PULL_END}'", date_cols=["datadate"])
        s = s.sort_values(["gvkey", "iid", "datadate"]).reset_index(drop=True)
        s.to_parquet(RAW_FILE, index=False)
    for c in ["trt1m", "prccm", "ajexm", "trfm", "cshtrm"]:
        s[c] = s[c].astype(float)
    s["month"] = s.datadate.dt.to_period("M")
    s["cusip8"] = s.cusip.str[:8]

    L = [f"# Extension to May 2026, validation: {cfg.UNIVERSE_LABEL}\n",
         "Name-level checks only. No portfolio return was computed and no bucket was read. Terms: **bp** is a basis point, 0.01%. **trt1m** is Compustat's monthly total return. **mthret** is CRSP's, which includes delisting returns. **Gap** is trt1m minus mthret.\n",
         f"Raw file `{RAW_FILE.name}`: {len(s)} rows, {s.gvkey.nunique()} gvkeys, {s.datadate.min().date()} to {s.datadate.max().date()}. Held names on the {last.date()} list: {len(held)}; included {int(list_rows.included.sum())}; on the list {len(list_rows)}.\n"]

    # --- Units ---
    units = s.trt1m.abs().describe(percentiles=[.5, .99])
    L.append("## Units and calendar\n")
    L.append(f"- `datadate` is the calendar month-end ({sorted(set(s.datadate.dt.day))}). `trt1m` median absolute value {units['50%']:.2f}, 99th percentile {units['99%']:.2f}, against a CRSP decimal scale: see the unit test in section 3.")
    L.append(f"- `curcdm`: {s.curcdm.value_counts(dropna=False).to_dict()}. `secstat`: {s.secstat.value_counts(dropna=False).to_dict()}.\n")

    # --- Step 2: map ---
    may = r[r.mthcaldt == last][["permno", "cusip", "ticker", "issuernm"]].rename(columns={"cusip": "crsp_cusip", "ticker": "crsp_ticker"})
    held = held.merge(may, on="permno", how="left")
    ref = s[s.month == last.to_period("M")]
    rows = []
    for x in held.itertuples():
        same_gv = ref[ref.gvkey == x.gvkey]
        by_cusip = same_gv[same_gv.cusip8 == x.crsp_cusip]
        by_tic = same_gv[same_gv.tic == x.crsp_ticker]
        issue, method = "", ""
        if len(by_cusip) == 1:
            pick, method = by_cusip.iloc[0], "gvkey + CUSIP"
            if pick.tic != x.crsp_ticker:
                issue = f"ticker differs: secm {pick.tic}, CRSP {x.crsp_ticker}"
        elif len(by_cusip) > 1:
            usd = by_cusip[by_cusip.curcdm == "USD"]
            others = ", ".join(f"{a.iid} {a.tic} {a.curcdm} exchg {a.exchg}" for a in by_cusip.itertuples())
            if len(usd) == 1:
                pick, method = usd.iloc[0], "gvkey + CUSIP, USD line"
                issue = f"Two lines share the CUSIP ({others}); USD line chosen"
            else:
                pick, method, issue = None, "", f"AMBIGUOUS: {others}"
        elif len(by_tic) == 1:
            pick, method = by_tic.iloc[0], "gvkey + ticker"
            issue = f"CUSIP differs: secm {pick.cusip8}, CRSP {x.crsp_cusip}"
        elif len(same_gv) == 1:
            pick, method = same_gv.iloc[0], "gvkey, only line"
            issue = f"CUSIP and ticker differ: secm {pick.tic} {pick.cusip8}, CRSP {x.crsp_ticker} {x.crsp_cusip}; only one line on the gvkey"
        else:
            other = ref[ref.cusip8 == x.crsp_cusip]
            if len(other) == 1:
                pick, method = other.iloc[0], "CUSIP, other gvkey"
                issue = f"gvkey differs: secm {pick.gvkey}, list {x.gvkey}"
            else:
                pick, method = None, ""
                issue = f"FAILED: no row by CUSIP or ticker; iids on this gvkey {same_gv.iid.tolist()}"
        rows.append({"permno": x.permno, "name": x.conm, "list_gvkey": x.gvkey, "crsp_cusip": x.crsp_cusip, "crsp_ticker": x.crsp_ticker, "gvkey": None if pick is None else pick.gvkey, "iid": None if pick is None else pick.iid,
                     "secm_tic": None if pick is None else pick.tic, "secm_cusip8": None if pick is None else pick.cusip8, "primiss": None if pick is None else pick.primiss, "curcdm": None if pick is None else pick.curcdm, "method": method, "issue": issue,
                     "iids_on_gvkey": len(same_gv)})
    map_df = pd.DataFrame(rows)
    map_df.to_csv(HERE / "security_map.csv", index=False)
    mapped = map_df[map_df.iid.notna()]
    dup = mapped[mapped.duplicated(["gvkey", "iid"], keep=False)]
    L.append("## 2. Mapping held PERMNOs to one gvkey-iid\n")
    L.append(f"{len(mapped)} of {len(map_df)} mapped: {mapped.method.value_counts().to_dict()}. Failed or ambiguous: {int(map_df.iid.isna().sum())}. Two PERMNOs on one gvkey-iid: {len(dup)}. "
             f"Held class is not secm's primary issue (primiss not P): {int((mapped.primiss != 'P').sum())}. Non-USD: {int((mapped.curcdm != 'USD').sum())}. Full map in `security_map.csv`.\n")
    issues = map_df[map_df.issue != ""]
    L.append("### Every failure, ambiguity or mismatch\n")
    L.append(md(issues[["name", "permno", "crsp_ticker", "secm_tic", "crsp_cusip", "secm_cusip8", "method", "issue"]]) if len(issues) else "None.\n")
    test = r[r.permno.isin(issues.permno) & r.month.isin(OVERLAP)].merge(mapped[["permno", "gvkey", "iid"]], on="permno").merge(s[["gvkey", "iid", "month", "trt1m"]], on=["gvkey", "iid", "month"], how="left")
    test["gap_bp"] = (test.trt1m / 100 - test.mthret) * 10000
    proof = test.groupby("permno").agg(months=("gap_bp", "count"), median_abs_gap_bp=("gap_bp", lambda v: v.abs().median()), largest_abs_gap_bp=("gap_bp", lambda v: v.abs().max())).reset_index().merge(map_df[["permno", "name"]], on="permno")
    L.append("\n### Do those mappings hold? 2025 returns of each against CRSP\n")
    L.append("A wrong security would show large gaps every month.\n")
    L.append(md(proof[["name", "months", "median_abs_gap_bp", "largest_abs_gap_bp"]]))
    L.append("\n### Held class not secm's primary issue\n")
    np_df = mapped[mapped.primiss != "P"]
    L.append(md(np_df[["name", "crsp_ticker", "secm_tic", "iid", "primiss"]]) if len(np_df) else "None.\n")

    # --- Step 3: overlap ---
    crsp = r[r.permno.isin(mapped.permno) & r.month.isin(OVERLAP)]
    j = crsp.merge(mapped[["permno", "name", "gvkey", "iid"]], on="permno").merge(s[["gvkey", "iid", "month", "trt1m", "prccm", "trfm", "ajexm", "secstat", "tic"]], on=["gvkey", "iid", "month"], how="left")
    j["gap_bp"] = (j.trt1m / 100 - j.mthret) * 10000
    j["alt_decimal_gap_bp"] = (j.trt1m - j.mthret) * 10000
    j["price_gap"] = (j.prccm / j.mthprc.abs() - 1)
    no_secm = j[j.trt1m.isna()]
    no_crsp = j[j.mthret.isna()]
    summary = pd.DataFrame([{"set": "All held, all of 2025", **describe_gaps(j.gap_bp)}, {"set": "Holding months, Jun-Dec 2025", **describe_gaps(j[j.month.isin(HOLD_2025)].gap_bp)},
                            {"set": "Excluding CRSP delisting months", **describe_gaps(j[j.mthretflg != "DE"].gap_bp)}])
    L.append("\n## 3. Overlap: trt1m against mthret, by security-month, all of 2025\n")
    L.append(f"**Units:** read as percent, the mean absolute gap is {j.gap_bp.abs().mean():.1f} bp; read as decimal, {j.alt_decimal_gap_bp.abs().mean():.0f} bp. So `trt1m` is in percent. Correlation with mthret: {j.trt1m.corr(j.mthret):.5f}.\n")
    L.append(md(summary))
    L.append(f"\nCRSP rows with no secm return: {len(no_secm)}. CRSP null returns: {len(no_crsp)}.\n")
    if len(no_secm):
        L.append(md(no_secm[["name", "permno", "month", "mthret", "mthretflg", "mthdelflg", "secstat"]].astype({"month": str}), 4))
    big = j[j.gap_bp.abs() > 100].copy()

    def cause(x):
        if x.mthretflg == "DE":
            return "CRSP delisting month: CRSP adds a delisting return"
        if pd.notna(x.price_gap) and abs(x.price_gap) > LARGE_PRICE_GAP:
            ratio = x.prccm / abs(x.mthprc)
            return f"closing prices differ (secm/CRSP {ratio:.3f}): a split or spin-off adjustment, or another close"
        spread = x.mthret - x.mthretx
        if abs(x.gap_bp) / 10000 > max(abs(spread) * 0.5, 0.001) and abs(spread) > 0.001:
            return "same close, distribution treated differently (CRSP dividend effect is large)"
        return "same close, prior-month base or adjustment differs (spin-off or special distribution likely)"
    big["likely_cause"] = big.apply(cause, axis=1) if len(big) else []
    big = big.sort_values("gap_bp", key=np.abs, ascending=False)
    bout = big[["name", "permno", "month", "trt1m", "mthret", "gap_bp", "prccm", "mthprc", "mthretflg", "likely_cause"]].astype({"month": str})
    bout.to_csv(HERE / "overlap_gaps_over_100bp.csv", index=False)
    L.append(f"\n### Every gap over 100 bp ({len(big)})\n")
    L.append(md(bout) if len(big) else "None.\n")

    # Compounded Jun-Dec 2025, name by name
    w = j[j.month.isin(HOLD_2025)]
    comp = w.groupby(["permno", "name"]).apply(lambda g: pd.Series({"months_crsp": int(g.mthret.notna().sum()), "months_both": int((g.mthret.notna() & g.trt1m.notna()).sum()),
                                                                   "crsp": (1 + g.mthret).prod() - 1 if g.mthret.notna().all() else np.nan,
                                                                   "secm": (1 + g.trt1m / 100).prod() - 1 if g.trt1m.notna().all() else np.nan,
                                                                   "had_delisting": (g.mthretflg == "DE").any()}), include_groups=False).reset_index()
    comp["gap_bp"] = (comp.secm - comp.crsp) * 10000
    comp.sort_values("gap_bp", key=np.abs, ascending=False).to_csv(HERE / "compound_jun_dec_2025.csv", index=False)
    full = comp[comp.months_crsp == len(HOLD_2025)]
    L.append("\n### Compounded June-December 2025, name by name\n")
    L.append(md(pd.DataFrame([{"set": "Names with all 7 months", **describe_gaps(full.gap_bp)}, {"set": "All names with a value", **describe_gaps(comp.gap_bp)}])))
    L.append(f"\nCompounded gaps over 100 bp ({int((comp.gap_bp.abs() > 100).sum())}); the file has every name:\n")
    L.append(md(comp[comp.gap_bp.abs() > 100].sort_values("gap_bp", key=np.abs, ascending=False)[["name", "months_crsp", "gap_bp", "had_delisting"]]))

    # Funds
    L.append("\n### RSP and SPY\n")
    fund_rows, fund_map = [], {}
    for t, (c8, permno) in BENCHMARK_CUSIPS.items():
        sf = s[s.cusip8 == c8]
        ids = sf[["gvkey", "iid", "tic", "conm"]].drop_duplicates()
        fund_map[t] = sf
        cf = b[(b.permno == permno) & b.month.isin(OVERLAP)]
        jf = cf.merge(sf[["month", "trt1m", "prccm"]], on="month", how="left")
        gap = (jf.trt1m / 100 - jf.mthret) * 10000
        hold = jf[jf.month.isin(HOLD_2025)]
        fund_rows.append({"fund": t, "secm_ids": "; ".join(f"{a.gvkey}-{a.iid} {a.tic}" for a in ids.itertuples()), **describe_gaps(gap),
                          "jun_dec_compound_gap_bp": ((1 + hold.trt1m / 100).prod() - (1 + hold.mthret).prod()) * 10000,
                          "months_2026_with_return": int(sf[sf.month.isin(EXT_MONTHS)].trt1m.notna().sum())})
    L.append(md(pd.DataFrame(fund_rows)))

    # --- Step 4: coverage ---
    ext = mapped.merge(s[s.month.isin(EXT_MONTHS)][["gvkey", "iid", "month", "trt1m", "prccm", "secstat", "tic", "cusip8", "cshtrm"]], on=["gvkey", "iid"], how="left")
    counts = pd.DataFrame([{"month": str(m), "row": int((ext.month == m).sum()), "non_null_trt1m": int(((ext.month == m) & ext.trt1m.notna()).sum()), "active_status": int(((ext.month == m) & (ext.secstat == "A")).sum())} for m in EXT_MONTHS])
    crsp_last = r[r.permno.isin(mapped.permno)].groupby("permno").agg(crsp_last_month=("month", "max")).reset_index()
    flags = r[r.permno.isin(mapped.permno)].sort_values("mthcaldt").groupby("permno").agg(crsp_last_del=("mthdelflg", "last"), crsp_last_flag=("mthretflg", "last"), crsp_last_ret=("mthret", "last")).reset_index()
    sec = db.raw_sql(f"select gvkey, iid, secstat as sec_secstat, dlrsni, dldtei, tic as sec_tic from comp.security where gvkey in ({', '.join(repr(g) for g in mapped.gvkey.unique())})", date_cols=["dldtei"])
    co = db.raw_sql(f"select gvkey, costat, dlrsn, dldte from comp.company where gvkey in ({', '.join(repr(g) for g in mapped.gvkey.unique())})", date_cols=["dldte"])
    cov = []
    allrows = s.set_index(["gvkey", "iid"]).sort_index()
    for x in mapped.itertuples():
        g = allrows.loc[(x.gvkey, x.iid)].reset_index().sort_values("month")
        e = g[g.month.isin(EXT_MONTHS)]
        after = g[g.month >= pd.Period("2025-06", "M")]
        problems = []
        if len(e) < len(EXT_MONTHS):
            problems.append(f"rows in {len(e)} of 5 months")
        n_null = int(e.trt1m.isna().sum())
        if n_null:
            problems.append(f"null trt1m in {n_null}: {[str(m) for m in e[e.trt1m.isna()].month]}")
        if (after.secstat != "A").any():
            problems.append("status not active: " + ", ".join(f"{a.month} {a.secstat}" for a in after[after.secstat != "A"].itertuples()))
        if after.tic.nunique() > 1:
            problems.append("ticker changes: " + " to ".join(after.tic.drop_duplicates().astype(str)))
        if after.cusip8.nunique() > 1:
            problems.append("CUSIP changes")
        unchanged = e[(e.prccm.diff() == 0)]
        if len(unchanged):
            problems.append(f"price unchanged in {[str(m) for m in unchanged.month]}")
        zero = e[e.cshtrm.fillna(0) == 0]
        if len(zero):
            problems.append(f"no trading volume in {[str(m) for m in zero.month]}")
        cov.append({"permno": x.permno, "name": x.name, "gvkey": x.gvkey, "iid": x.iid, "tic": x.secm_tic, "rows_2026": len(e), "null_2026": n_null, "last_row": str(g.month.max()), "last_trt1m_month": str(g[g.trt1m.notna()].month.max()) if g.trt1m.notna().any() else "",
                    "last_trt1m": g[g.trt1m.notna()].trt1m.iloc[-1] if g.trt1m.notna().any() else np.nan, "problems": "; ".join(problems)})
    # Distributions and splits: secm has no CRSP cross-check in 2026, so size what trt1m carries beyond the price move
    dist = s.merge(mapped[["gvkey", "iid", "name"]], on=["gvkey", "iid"]).sort_values(["gvkey", "iid", "month"])
    grp = dist.groupby(["gvkey", "iid"])
    dist["adj_price"] = dist.prccm / dist.ajexm
    dist["price_only_pct"] = (dist.adj_price / grp.adj_price.shift(1) - 1) * 100
    dist["beyond_price_pct"] = dist.trt1m - dist.price_only_pct
    dist["trfm_ratio"] = dist.trfm / grp.trfm.shift(1)
    dist["ajexm_ratio"] = dist.ajexm / grp.ajexm.shift(1)
    known = dist[dist.month.isin(OVERLAP)].merge(j[["permno", "month", "gap_bp", "name"]].rename(columns={"name": "n2"}), left_on=["name", "month"], right_on=["n2", "month"])
    cal = known.assign(abs_gap=known.gap_bp.abs()).sort_values("abs_gap", ascending=False).head(6)
    in_2026 = dist[dist.month.isin(EXT_MONTHS)]
    unusual = in_2026.assign(abs_b=in_2026.beyond_price_pct.abs()).sort_values("abs_b", ascending=False).head(15)
    splits = in_2026[(in_2026.ajexm_ratio - 1).abs() > 1e-9]
    cov = pd.DataFrame(cov).merge(crsp_last, on="permno").merge(flags, on="permno").merge(sec[["gvkey", "iid", "sec_secstat", "dlrsni", "dldtei"]], on=["gvkey", "iid"], how="left").merge(co, on="gvkey", how="left")
    cov["crsp_last_month"] = cov.crsp_last_month.astype(str)
    cov.to_csv(HERE / "coverage_2026.csv", index=False)
    L.append("\n## 4. Coverage, January-May 2026\n")
    L.append(f"Held names mapped: {len(mapped)}.\n")
    L.append(md(counts))
    dec = j[(j.month == pd.Period("2025-12", "M")) & j.mthprc.notna() & j.prccm.notna()]
    dec_off = dec[dec.price_gap.abs() > LARGE_PRICE_GAP]
    L.append(f"\n**The December 2025 join:** January's trt1m starts from secm's December close, and the CRSP series ends on CRSP's. Closes agree exactly (within 0.01%) on {int((dec.price_gap.abs() <= 0.0001).sum())} of {len(dec)} names; over 0.5% apart on {len(dec_off)}" + (f": {dec_off.name.tolist()}.\n" if len(dec_off) else ".\n"))
    L.append("**secstat and tic are current header values, not dated ones:** Hologic reads `I` back through 2025 although it traded until April 2026. So status can't date an exit; the deletion date and last row do.\n")
    exited_crsp = cov[cov.crsp_last_month < "2025-12"]
    ended_flag = cov[(cov.crsp_last_month == "2025-12") & (cov.crsp_last_del != cfg.ACTIVE_DELISTING_FLAG)]
    L.append(f"\nAlready exited in CRSP before December 2025: {len(exited_crsp)}. Delisting flag in December 2025: {len(ended_flag)}. These have their final CRSP return, so they need no secm month for 2026.\n")
    L.append(md(pd.concat([exited_crsp, ended_flag])[["name", "tic", "crsp_last_month", "crsp_last_del", "crsp_last_flag", "rows_2026", "last_row"]]) if len(exited_crsp) + len(ended_flag) else "None.\n")
    live = cov[~cov.permno.isin(pd.concat([exited_crsp, ended_flag]).permno)]
    trouble = live[live.problems != ""].sort_values(["rows_2026", "name"])
    L.append(f"\n### Names still live in CRSP at December 2025 with any flag in 2026 ({len(trouble)} of {len(live)})\n")
    L.append("Codes `dlrsn` / `dlrsni` are Compustat's deletion reason: 01 acquisition or merger, 02 bankruptcy, 03 liquidation, 04 reverse acquisition, 05 no longer files or fits, 06 leveraged buyout, 07 other, 09 now a private company, 10 other. The text and any reason are as Compustat records them today.\n")
    L.append(md(trouble[["name", "tic", "rows_2026", "null_2026", "last_row", "last_trt1m_month", "last_trt1m", "sec_secstat", "dlrsni", "dldtei", "costat", "dlrsn", "dldte", "problems"]]) if len(trouble) else "None.\n")

    L.append("\n### Spin-offs and large distributions\n")
    L.append("The largest gaps in 2025 look like spin-offs, and CRSP cannot check 2026. `beyond_price_pct` is trt1m minus the split-adjusted price change, so it shows what trt1m adds for dividends and distributions. `trfm_ratio` is the month's change in Compustat's total return factor.\n")
    L.append("Calibration: the 2025 months with the largest gaps to CRSP.\n")
    L.append(md(cal[["name", "month", "trt1m", "price_only_pct", "beyond_price_pct", "trfm_ratio", "ajexm_ratio", "gap_bp"]].astype({"month": str}), 3))
    L.append("\nThe 15 largest values in January-May 2026:\n")
    L.append(md(unusual[["name", "month", "trt1m", "price_only_pct", "beyond_price_pct", "trfm_ratio", "ajexm_ratio"]].astype({"month": str}), 3))
    L.append(f"\nSplits in 2026 (ajexm changes): {len(splits)}.\n")
    if len(splits):
        L.append(md(splits[["name", "month", "trt1m", "price_only_pct", "ajexm_ratio"]].astype({"month": str}), 3))

    # --- Evidence: what secm shows at CRSP's recorded exits. Name level; no bucket is read. ---
    ex = pd.read_csv(ROOT / "output/logs/portfolio_exits.csv", usecols=["formation_date", "permno", "conm", "exit_type", "last_month_with_return", "last_return_in_holding", "delisting_flag", "last_return_flag"])
    ex = ex[ex.exit_type == "mid-period exit"].merge(fm[["formation_date", "permno", "gvkey"]].assign(formation_date=fm.formation_date.dt.strftime("%Y-%m-%d")), on=["formation_date", "permno"], how="left")
    ex["last_month"] = pd.PeriodIndex(ex.last_month_with_return, freq="M")
    c_map = r[["permno", "month", "cusip"]].drop_duplicates(["permno", "month"])
    ex = ex.merge(c_map, left_on=["permno", "last_month"], right_on=["permno", "month"], how="left")
    evid = []
    gkeys = ", ".join(f"'{g}'" for g in ex.gvkey.dropna().unique())
    hist = db.raw_sql(f"select gvkey, iid, datadate, cusip, tic, primiss, curcdm, trt1m, prccm, secstat from comp.secm where gvkey in ({gkeys}) and datadate >= '{cfg.RETURNS_START}'", date_cols=["datadate"])
    db.close()
    hist["trt1m"], hist["prccm"] = hist.trt1m.astype(float), hist.prccm.astype(float)
    hist["month"] = hist.datadate.dt.to_period("M")
    hist["cusip8"] = hist.cusip.str[:8]
    for x in ex.itertuples():
        g = hist[(hist.gvkey == x.gvkey) & (hist.cusip8 == x.cusip) & (hist.curcdm == "USD")].sort_values("month")
        match = "CUSIP"
        if g.empty:
            # secm carries a company's current CUSIP, so a reorganised company needs its primary USD line
            g = hist[(hist.gvkey == x.gvkey) & (hist.primiss == "P") & (hist.curcdm == "USD")].sort_values("month")
            match = "primary line, CUSIP differs"
        if g.empty:
            evid.append({"name": x.conm, "exit_month": str(x.last_month), "crsp_final_return": x.last_return_in_holding, "match": "none", "status": "no secm row found"})
            continue
        at = g[g.month == x.last_month]
        before = g[g.month == x.last_month - 1]
        later = g[g.month > x.last_month]
        has_row, val = len(at) > 0, at.trt1m.iloc[0] if len(at) else np.nan
        status = "no row in the exit month" if not has_row else ("row, null trt1m" if pd.isna(val) else "row with return")
        if len(at) == 0 and len(before) and pd.notna(before.trt1m.iloc[0]):
            status = "rows stop the month before"
        evid.append({"name": x.conm, "exit_month": str(x.last_month), "match": match, "crsp_final_return": x.last_return_in_holding, "crsp_flag": x.delisting_flag, "secm_return": None if pd.isna(val) else val / 100,
                     "gap_bp": None if pd.isna(val) else (val / 100 - x.last_return_in_holding) * 10000, "status": status, "rows_after_exit": len(later), "non_null_after_exit": int(later.trt1m.notna().sum())})
    evid = pd.DataFrame(evid)
    evid.to_csv(HERE / "past_exits_evidence.csv", index=False)
    L.append("\n### Evidence on the risk: what secm shows at past CRSP exits\n")
    L.append(f"The {len(evid)} mid-period exits already logged in the headline (2005-2025), compared name by name. This tests whether secm carries a final return when a stock leaves. Details in `past_exits_evidence.csv`.\n")
    L.append(md(evid.status.value_counts().rename_axis("what secm shows").reset_index(name="exits")))
    w2 = evid[evid.status == "row with return"]
    L.append(f"\nWhere secm has a return in the exit month, against CRSP's final return:\n")
    w2 = w2.assign(gap=w2.gap_bp.astype(float))
    ended = w2[(w2.rows_after_exit.fillna(0) == 0) | (w2.non_null_after_exit.fillna(0) == 0)]
    went_on = w2[w2.non_null_after_exit.fillna(0) > 0]
    recent = w2[w2.exit_month >= "2015-06"]
    L.append(md(pd.DataFrame([{"set": "All exit months", **describe_gaps(w2.gap)}, {"set": "secm returns stop after the exit", **describe_gaps(ended.gap)}, {"set": "secm returns continue after the exit (same gvkey and line)", **describe_gaps(went_on.gap)},
                              {"set": "Matched by CUSIP", **describe_gaps(w2[w2.match == "CUSIP"].gap)}, {"set": "Exits from June 2015", **describe_gaps(recent.gap)}, {"set": "For comparison: all held names in 2025, non-exit months", **describe_gaps(j[j.mthretflg != "DE"].gap_bp)}])))
    L.append(f"\nSigned exit-month gap, percentiles in bp: {w2.gap.quantile([.05, .25, .5, .75, .95]).round(1).to_dict()}. Share with secm above CRSP: {(w2.gap > 0).mean():.0%}.\n")
    L.append(f"\nExits with rows or returns after the exit month: rows {int((evid.rows_after_exit.fillna(0) > 0).sum())}, non-null returns {int((evid.non_null_after_exit.fillna(0) > 0).sum())}.\n")
    wide = w2[w2.gap_bp.astype(float).abs() > 100].sort_values("gap_bp", key=lambda v: v.astype(float).abs(), ascending=False)
    L.append(f"\nExit-month gaps over 100 bp ({len(wide)}):\n")
    L.append(md(wide[["name", "exit_month", "crsp_final_return", "secm_return", "gap_bp", "crsp_flag"]], 4) if len(wide) else "None.\n")
    nor = evid[evid.status != "row with return"]
    L.append(f"\nExits with no secm return in the exit month ({len(nor)}):\n")
    L.append(md(nor[["name", "exit_month", "crsp_final_return", "crsp_flag", "status"]], 4) if len(nor) else "None.\n")

    # --- Step 5: factors ---
    ff = pd.read_parquet(ROOT / "data/raw/ff_factors.parquet")
    need = [str(m) for m in EXT_MONTHS]
    fx = ff[ff.month.isin(need)]
    cols = ["mktrf", "smb", "hml", "rmw", "cma", "rf", "umd"]
    L.append("\n## 5. Factors\n")
    L.append(f"`ff_factors.parquet` runs to {ff.month.max()}. January-May 2026: {len(fx)} of {len(need)} months present; null values {int(fx[cols].isna().sum().sum())}.\n")
    q = w2.gap.abs().quantile(.95)
    counts_2025 = pd.read_csv(ROOT / "output/tables/bucket_counts.csv")
    counts_2025 = counts_2025[counts_2025.formation_date == str(last.date())].set_index("bucket").names
    L.append("\n## Treatment proposed at this stage (set without using any performance; since approved and applied in `10_extension_2026.py`)\n")
    L.append("1. **Months:** use `trt1m / 100` for January-May 2026 on the mapped line, unadjusted, with the CRSP series unchanged through December 2025. Label the result an extension: a different source, not part of the headline.")
    L.append("2. **Exits inside the window:** only Hologic (deleted 2026-04-09, last row April) and Coterra (deleted 2026-05-07, last row May, the final month anyway). Both have a final secm return and Compustat records an acquisition. Take that as the final return, then apply `DELISTING_RULE` as elsewhere, so Hologic's value goes pro rata from May. Disclose that it may omit part of what CRSP would count: secm has no delisting return.")
    L.append(f"3. **Size of that risk:** at past exits, 95% of absolute gaps to CRSP are within {q:.0f} bp. At equal weight, one such gap is about {q / counts_2025['Benchmark']:.1f} bp on the Benchmark ({counts_2025['Benchmark']} names), {q / counts_2025['High']:.1f} bp on High ({counts_2025['High']}) and {q / counts_2025['Low']:.1f} bp on Low ({counts_2025['Low']}) if the name is in that bucket, ignoring drift. Bucket counts are used here, not bucket returns, and which bucket each name is in was not read. The largest past gap, Premcor, was {w2.gap.abs().max():.0f} bp.")
    L.append("4. **Spin-offs:** use trt1m as given, and disclose it. It handled the 2025 spin-offs imperfectly (DuPont -843 bp, Liberty Broadband +205 bp, Western Digital +179 bp, in different directions), and January-May 2026 has two months of the same type by the size of the distribution: Becton Dickinson February and Comcast January. Whether these are spin-offs is my reading of the size, not checked against a filing, and neither can be tested against CRSP.")
    L.append("5. **No other rule:** the portfolio script should stop on any null trt1m, missing row or new exit in the window rather than choose. None exists today among held names.")
    L.append("6. **RSP and SPY:** `trt1m` from the lines above, which match CRSP closely in 2025.")
    L.append("7. **Factors:** cut at 2026-05 for extension regressions, and join on month.")
    L.append("\n## Limits\n")
    L.append("- The overlap test covers 2025 only, and only this list's names. Exit evidence is from all logged exits and includes old data.\n- The Compustat deletion reasons are as recorded now, and no filing was opened. The reading of a likely cause for each gap is mine.\n- Passing on 2025 does not prove 2026 rows are final: Compustat can revise them.")
    (HERE / "validation.md").write_text("\n".join(L), encoding="utf-8")

    print(summary.round(2).to_string(index=False))
    print(counts.to_string(index=False))
    print(evid.status.value_counts().to_dict())
    print(f"mapped {len(mapped)}/{len(map_df)}; issues {len(issues)}; gaps over 100bp {len(big)}; 2026 flags {len(trouble)} of {len(live)}; factors {len(fx)}/{len(need)}")


if __name__ == "__main__":
    main()
