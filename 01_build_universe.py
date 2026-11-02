"""
Phase 1a: build the Top-500 universe for each formation date (CLAUDE.md sections 4, 5 and 8).

Output: data/clean/universe.parquet
Logs:   output/logs/universe_log.csv, universe_link_failures.csv, universe_sibling_links.csv,
        universe_removed_stopped_trading.csv, universe_mortgage_reits_excluded.csv, universe_checks.md
Exit code is 1 if any check fails; outputs are still written so the failure can be inspected.
"""
import os
import sys
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"

# Labels for checks and reports only. None of these affects which companies are in the universe.
GICS_REAL_ESTATE_GROUP = "4040"  # co_hgic ggroup used to validate the row-level REIT flag
CRASH_WINDOW = ("2019-12-01", "2020-05-31")
CONTEXT_RANKS = [100, 250, 500, 1000]
CONTEXT_YEARS = (2019, 2022)


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


def sql_list(values):
    return ", ".join(f"'{v}'" for v in values)


def sql_ints(values):
    return ", ".join(str(int(v)) for v in values)


def valid_on(df, date_col, start, end):
    return (df[start] <= df[date_col]) & (df[end].isna() | (df[date_col] <= df[end]))


def pull_formation_month(db):
    m = db.raw_sql(f"""
        select permno, permco, mthcaldt, mthprc, shrout, mthprcdt, mthprcflg, mthdelflg, ticker, issuernm, usincflg,
               issuertype, securitytype, securitysubtype, sharetype, primaryexch, tradingstatusflg
        from crsp.msf_v2
        where extract(month from mthcaldt) = {cfg.FORMATION_MONTH}
          and extract(year from mthcaldt) between {cfg.FIRST_FORMATION_YEAR} and {cfg.LAST_FORMATION_YEAR}
    """, date_cols=["mthcaldt", "mthprcdt"])
    last = m.groupby(m.mthcaldt.dt.year).mthcaldt.transform("max")
    m = m[m.mthcaldt == last].rename(columns={"mthcaldt": "formation_date"}).copy()
    m["mthprc"] = m.mthprc.astype(float)
    m["shrout"] = m.shrout.astype(float)
    # price (USD) x shares (thousands) / 1000 = USD millions
    m["seccap"] = m.mthprc.abs() * m.shrout / 1000
    m["stopped_trading"] = ((m.mthdelflg != cfg.ACTIVE_DELISTING_FLAG) & (m.mthprcdt < m.formation_date)).fillna(False).astype(bool)
    return m


def eligible_mask(m):
    return (
        (m.usincflg == cfg.US_INCORPORATED_FLAG)
        & (m.securitytype == cfg.SECURITY_TYPE)
        & (m.securitysubtype == cfg.SECURITY_SUBTYPE)
        & m.primaryexch.isin(cfg.LISTING_EXCHANGES)
        & ((m.sharetype == cfg.ORDINARY_SHARE_TYPE)
           | ((m.sharetype == cfg.REIT_SHARE_TYPE) & (m.issuertype == cfg.REIT_ISSUER_TYPE)))
    )


def drop_counts(m):
    """Waterfall of securities removed at each filter, one row per date."""
    rows = []
    for d, g in m.groupby("formation_date"):
        r = {"formation_date": d, "crsp_securities": len(g), "drop_stopped_trading": int(g.stopped_trading.sum())}
        keep = ~g.stopped_trading
        step = keep & (g.usincflg == cfg.US_INCORPORATED_FLAG)
        r["drop_not_us_incorporated"] = int((keep & ~step).sum())
        keep = step
        step = keep & (g.securitytype == cfg.SECURITY_TYPE) & (g.securitysubtype == cfg.SECURITY_SUBTYPE)
        r["drop_fund_etf_cef"] = int((keep & ~step).sum())
        keep = step
        step = keep & g.primaryexch.isin(cfg.LISTING_EXCHANGES)
        r["drop_other_exchange"] = int((keep & ~step).sum())
        keep = step
        step = keep & eligible_mask(g)
        r["drop_share_type"] = int((keep & ~step).sum())
        keep = step
        r["drop_missing_price"] = int((keep & g.seccap.isna()).sum())
        r["eligible_securities"] = int((keep & g.seccap.notna()).sum())
        r["eligible_companies"] = g[keep & g.seccap.notna()].permco.nunique()
        rows.append(r)
    return pd.DataFrame(rows)


def rank_companies(elig):
    """Sum classes by PERMCO, keep the top N, hold the largest class of each."""
    company = elig.groupby(["formation_date", "permco"], as_index=False).seccap.sum().rename(columns={"seccap": "mktcap"})
    company = company.sort_values(["formation_date", "mktcap", "permco"], ascending=[True, False, True])
    company["rank"] = company.groupby("formation_date").cumcount() + 1
    top = company[company["rank"] <= cfg.UNIVERSE_SIZE]
    held = (elig.sort_values(["formation_date", "permco", "seccap", "permno"], ascending=[True, True, False, True])
            .drop_duplicates(["formation_date", "permco"]))
    return top.merge(held.drop(columns=["seccap"]), on=["formation_date", "permco"], how="left", validate="1:1"), company


def attach_gvkey(u, db):
    link = db.raw_sql(f"""
        select gvkey, lpermno as permno, linktype, linkprim, linkdt, linkenddt
        from crsp.ccmxpf_lnkhist
        where linktype in ({sql_list(cfg.LINK_TYPES)}) and linkprim in ({sql_list(cfg.LINK_PRIMARY)})
          and lpermno in ({sql_ints(u.permno.unique())})
    """, date_cols=["linkdt", "linkenddt"])
    link["permno"] = link.permno.astype(int)
    hit = u[["formation_date", "permno"]].merge(link, on="permno")
    hit = hit[valid_on(hit, "formation_date", "linkdt", "linkenddt")]
    multi = hit[hit.duplicated(["formation_date", "permno"], keep=False)]
    # A primary link sorts ahead of a secondary one if a security ever has two; any such case is reported.
    hit = hit.sort_values(["formation_date", "permno", "linkprim", "gvkey"], ascending=[True, True, False, True])
    hit = hit.drop_duplicates(["formation_date", "permno"])
    return u.merge(hit[["formation_date", "permno", "gvkey"]], on=["formation_date", "permno"], how="left", validate="1:1"), multi


def apply_sibling_links(u, m, db):
    """Held class has no valid link: use the PERMCO's gvkey when exactly one valid gvkey exists."""
    fails = u[u.gvkey.isna()]
    if fails.empty:
        return u, pd.DataFrame(), pd.DataFrame()
    classes = m[m.permco.isin(fails.permco)][["formation_date", "permco", "permno"]]
    raw = db.raw_sql(f"""
        select gvkey, lpermno, lpermco, linktype, linkprim, linkdt, linkenddt from crsp.ccmxpf_lnkhist
        where lpermno in ({sql_ints(classes.permno.unique())}) or lpermco in ({sql_ints(fails.permco.unique())})
    """, date_cols=["linkdt", "linkenddt"])
    raw = raw[raw.lpermno.notna()].copy()
    raw["lpermno"] = raw.lpermno.astype(int)

    used, remaining = [], []
    u = u.copy()
    for f in fails.itertuples():
        same_date = classes[(classes.formation_date == f.formation_date) & (classes.permco == f.permco)]
        r = raw[(raw.lpermco == f.permco) | raw.lpermno.isin(same_date.permno)]
        r = r[(r.linkdt <= f.formation_date) & (r.linkenddt.isna() | (f.formation_date <= r.linkenddt))]
        usable = r[r.linktype.isin(cfg.LINK_TYPES) & r.linkprim.isin(cfg.LINK_PRIMARY)]
        own = r[r.lpermno == f.permno]
        own_links = ", ".join(sorted(set(own.linktype + "/" + own.linkprim)))
        base = {"formation_date": f.formation_date, "rank": f.rank, "permno": f.permno, "permco": f.permco,
                "ticker": f.ticker, "issuernm": f.issuernm, "mktcap": f.mktcap}
        gvkeys = sorted(usable.gvkey.unique())
        if cfg.SIBLING_CLASS_LINK and len(gvkeys) == 1:
            u.loc[f.Index, "gvkey"] = gvkeys[0]
            used.append({**base, "gvkey": gvkeys[0], "held_class_link": own_links,
                         "sibling_permnos": ", ".join(map(str, sorted(usable.lpermno.unique()))),
                         "sibling_lpermcos": ", ".join(str(p) for p in sorted(usable.lpermco.unique())),
                         "lpermco_matches": bool((usable.lpermco == f.permco).all())})
        else:
            if len(gvkeys) > 1:
                cause = "several gvkeys across the company's classes"
            elif len(own):
                cause = "held class linked, but type or primary flag not allowed"
            else:
                cause = "no link for any class on the date"
            remaining.append({**base, "cause": cause, "held_class_link": own_links, "candidate_gvkeys": ", ".join(gvkeys)})
    used_cols = ["formation_date", "rank", "permno", "permco", "ticker", "issuernm", "mktcap", "gvkey", "held_class_link", "sibling_permnos", "sibling_lpermcos", "lpermco_matches"]
    rem_cols = ["formation_date", "rank", "permno", "permco", "ticker", "issuernm", "mktcap", "cause", "held_class_link", "candidate_gvkeys"]
    return u, pd.DataFrame(used, columns=used_cols), pd.DataFrame(remaining, columns=rem_cols)


def attach_sector(u, db):
    gvkeys = u.gvkey.dropna().unique()
    sec = db.raw_sql(f"""
        select gvkey, gsector, ggroup, gsubind, indfrom, indthru from comp.co_hgic
        where indtype = 'GICS' and gvkey in ({sql_list(gvkeys)})
    """, date_cols=["indfrom", "indthru"])
    hit = u[["formation_date", "gvkey"]].dropna().drop_duplicates().merge(sec, on="gvkey")
    hit = hit[valid_on(hit, "formation_date", "indfrom", "indthru")]
    multi = hit[hit.duplicated(["formation_date", "gvkey"], keep=False)]
    hit = hit.sort_values(["formation_date", "gvkey", "indfrom"]).drop_duplicates(["formation_date", "gvkey"], keep="last")
    return u.merge(hit[["formation_date", "gvkey", "gsector", "ggroup", "gsubind"]], on=["formation_date", "gvkey"], how="left", validate="m:1"), multi


def mortgage_reit_mask(u):
    """REIT on the row, with a mortgage sub-industry on the date or a named (issuernm, formation year) exception."""
    named = pd.Series([(n, d.year) in cfg.MORTGAGE_REIT_NAMED_EXCEPTIONS for n, d in zip(u.issuernm, u.formation_date)], index=u.index)
    return (u.issuertype == cfg.REIT_ISSUER_TYPE) & (u.gsubind.isin(cfg.MORTGAGE_REIT_GICS_SUBINDUSTRIES) | named)


def set_included(u):
    """Exclusions come after ranking, so only the included flag changes."""
    u = u.copy()
    u["is_reit"] = u.issuertype == cfg.REIT_ISSUER_TYPE
    u["is_excluded_sector"] = u.gsector.isin(cfg.EXCLUDED_GICS_SECTORS)
    u["mortgage_reit_excluded"] = mortgage_reit_mask(u) & cfg.EXCLUDE_MORTGAGE_REITS
    u["kept_reit"] = u.is_excluded_sector & u.is_reit & cfg.KEEP_REITS_ON_ALL_DATES & ~u.mortgage_reit_excluded
    u["included"] = (u.gvkey.notna() & u.gsector.notna() & (~u.is_excluded_sector | u.kept_reit) & ~u.mortgage_reit_excluded).astype(bool)
    return u


def md_table(df, floatfmt="{:,.1f}"):
    def fmt(v):
        if pd.isna(v):
            return ""
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        if isinstance(v, float):
            return floatfmt.format(v)
        return str(v)
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    db = wrds.Connection(wrds_username=wrds_username())
    m = pull_formation_month(db)
    drops = drop_counts(m)
    priced = m[eligible_mask(m) & m.seccap.notna()]

    # Checkpoint 1 rules, rebuilt only for the before-and-after table
    u0, companies0 = rank_companies(priced)
    u0, _ = attach_gvkey(u0, db)
    u0, _ = attach_sector(u0, db)
    u0["included"] = u0.gvkey.notna() & u0.gsector.notna() & ~u0.gsector.isin(cfg.EXCLUDED_GICS_SECTORS)

    # Approved rules
    u, all_companies = rank_companies(priced[~priced.stopped_trading])
    u, multi_link = attach_gvkey(u, db)
    u, siblings, fails = apply_sibling_links(u, m, db)
    u, multi_sector = attach_sector(u, db)

    u = set_included(u)
    u["year"] = u.formation_date.dt.year

    out = u[["formation_date", "permno", "permco", "gvkey", "mktcap", "rank", "gsector", "included"]]
    out.to_parquet(CLEAN / "universe.parquet", index=False)

    # Each removal, with the rank its company held before the removal
    removed = m[m.stopped_trading].copy()
    removed["eligible_otherwise"] = eligible_mask(removed) & removed.seccap.notna()
    removed = removed.merge(companies0[["formation_date", "permco", "rank"]].rename(columns={"rank": "rank_before_removal"}),
                            on=["formation_date", "permco"], how="left")
    removed = removed.sort_values(["formation_date", "rank_before_removal"])
    removed[["formation_date", "permno", "permco", "ticker", "issuernm", "mthprcdt", "mthdelflg", "seccap", "eligible_otherwise", "rank_before_removal"]] \
        .rename(columns={"seccap": "cap_musd"}).to_csv(LOGS / "universe_removed_stopped_trading.csv", index=False)
    fails.to_csv(LOGS / "universe_link_failures.csv", index=False)
    siblings.to_csv(LOGS / "universe_sibling_links.csv", index=False)
    mortgage = u[mortgage_reit_mask(u)].sort_values(["formation_date", "rank"])[
        ["formation_date", "rank", "permno", "permco", "gvkey", "ticker", "issuernm", "gsector", "gsubind", "mktcap", "included"]]
    mortgage.to_csv(LOGS / "universe_mortgage_reits_excluded.csv", index=False)

    failures, flags = [], []
    L = [f"# Phase 1a checks: {cfg.UNIVERSE_LABEL}\n"]

    # --- Per-date summary ---
    u["linked_cap"] = u.mktcap.where(u.gvkey.notna(), 0.0)
    per = u.groupby("formation_date").agg(
        companies=("permco", "nunique"), linked=("gvkey", lambda s: s.notna().sum()), has_sector=("gsector", lambda s: s.notna().sum()),
        excluded_sector=("is_excluded_sector", "sum"), reits_kept=("kept_reit", "sum"), mortgage_reits_excluded=("mortgage_reit_excluded", "sum"), included=("included", "sum"),
        cutoff_mktcap_musd=("mktcap", "min"), total_cap=("mktcap", "sum"), linked_cap=("linked_cap", "sum"),
    ).reset_index()
    per["link_rate"] = per.linked / per.companies
    per["link_rate_cap"] = per.linked_cap / per.total_cap
    per["cutoff_yoy"] = per.cutoff_mktcap_musd.pct_change()
    drops.merge(per.drop(columns=["total_cap", "linked_cap"]), on="formation_date").to_csv(LOGS / "universe_log.csv", index=False)

    # --- Check: counts ---
    bad = per[per.companies != cfg.UNIVERSE_SIZE]
    if len(bad):
        failures.append(f"Company count differs from {cfg.UNIVERSE_SIZE} on {len(bad)} dates")
    lo, hi = cfg.INCLUDED_COUNT_RANGE
    bad_inc = per[(per.included < lo) | (per.included > hi)]
    if len(bad_inc):
        failures.append(f"Included count outside {lo}-{hi} on {len(bad_inc)} of {len(per)} dates: "
                        + ", ".join(f"{r.formation_date.year}={r.included}" for r in bad_inc.itertuples()))
    L.append("## 1. Company counts (before and after exclusions)\n")
    L.append(f"Exactly {cfg.UNIVERSE_SIZE} before exclusions: **{'PASS' if not len(bad) else 'FAIL'}**. "
             f"Included within {lo}-{hi}: **{'PASS' if not len(bad_inc) else 'FAIL'}** "
             f"(range {per.included.min()}-{per.included.max()}).\n")
    L.append(md_table(per[["formation_date", "companies", "linked", "has_sector", "excluded_sector", "reits_kept", "mortgage_reits_excluded", "included"]]))

    # --- Before and after ---
    per0 = u0.groupby("formation_date").agg(
        included_before=("included", "sum"), failed_links_before=("gvkey", lambda s: s.isna().sum()),
        no_sector_before=("gsector", lambda s: s.isna().sum()), cutoff_before=("mktcap", "min"),
    ).reset_index()
    rows = []
    for d in per.formation_date:
        s0 = set(u0[(u0.formation_date == d) & u0.included].permco)
        s1 = set(u[(u.formation_date == d) & u.included].permco)
        g = u[u.formation_date == d]
        rows.append({"formation_date": d, "included_after": len(s1), "included_entered": len(s1 - s0), "included_left": len(s0 - s1),
                     "stopped_trading_removed_from_top500": int(((removed.formation_date == d) & removed.eligible_otherwise & (removed.rank_before_removal <= cfg.UNIVERSE_SIZE)).sum()),
                     "sibling_links": int((siblings.formation_date == d).sum()) if len(siblings) else 0,
                     "failed_links_after": int(g.gvkey.isna().sum()), "no_sector_after": int((g.gvkey.notna() & g.gsector.isna()).sum()),
                     "cutoff_after": float(g.mktcap.min())})
    ba = per0.merge(pd.DataFrame(rows), on="formation_date")
    ba["no_sector_before"] = ba.no_sector_before - ba.failed_links_before  # linked names only, to match the after column
    L.append("\n## 2. Before and after, per date (Checkpoint 1 rules vs approved rules)\n")
    L.append("Before = the rules used at Checkpoint 1, recomputed in this run. Market caps are USD millions.\n")
    L.append(md_table(ba[["formation_date", "included_before", "included_after", "included_entered", "included_left", "stopped_trading_removed_from_top500",
                          "sibling_links", "failed_links_before", "failed_links_after", "no_sector_before", "no_sector_after", "cutoff_before", "cutoff_after"]]))

    # --- Check: cutoff ---
    flagged = per[per.cutoff_yoy.abs() > cfg.MAX_CUTOFF_MKTCAP_CHANGE]
    for r in flagged.itertuples():
        flags.append(f"Cutoff market cap moved {r.cutoff_yoy:+.1%} in {r.formation_date.year}, above the {cfg.MAX_CUTOFF_MKTCAP_CHANGE:.0%} flag level")
    series = per.set_index(per.formation_date.dt.year)
    required_dip = series.cutoff_yoy.get(cfg.CUTOFF_DIP_YEAR_REQUIRED, 0) < 0
    reported_dip = series.cutoff_yoy.get(cfg.CUTOFF_DIP_YEAR_REPORTED, 0)
    if not required_dip:
        failures.append(f"Expected cutoff dip absent in {cfg.CUTOFF_DIP_YEAR_REQUIRED}")
    up_ends = series.cutoff_mktcap_musd.iloc[-1] > series.cutoff_mktcap_musd.iloc[0]
    if not up_ends:
        failures.append("Cutoff market cap does not rise from first to last year")
    # Rank correlation with year: uses every year, and needs no threshold beyond "positive"
    trend_corr = series.cutoff_mktcap_musd.rank().corr(pd.Series(series.index, index=series.index, dtype=float).rank())
    if not trend_corr > 0:
        failures.append(f"Cutoff market cap has no upward trend: rank correlation with year is {trend_corr:.3f}")
    up = up_ends and trend_corr > 0
    L.append("\n## 3. Market cap of the 500th company (USD millions)\n")
    L.append(f"Upward trend (last year above first, and rank correlation with year {trend_corr:+.3f} is positive): **{'PASS' if up else 'FAIL'}**. Dip in {cfg.CUTOFF_DIP_YEAR_REQUIRED}: **{'PASS' if required_dip else 'FAIL'}**. "
             f"{cfg.CUTOFF_DIP_YEAR_REPORTED} change, reported only: **{reported_dip:+.1%}**. "
             f"Moves above {cfg.MAX_CUTOFF_MKTCAP_CHANGE:.0%}, flagged only: **{', '.join(str(d.year) for d in flagged.formation_date) or 'none'}**.\n")
    t = per[["formation_date", "cutoff_mktcap_musd"]].copy()
    t["yoy_pct"] = per.cutoff_yoy * 100
    L.append(md_table(t))
    c20 = db.raw_sql(f"""
        select permco, mthcaldt, mthprc, shrout, usincflg, issuertype, securitytype, securitysubtype, sharetype, primaryexch
        from crsp.msf_v2 where mthcaldt between '{CRASH_WINDOW[0]}' and '{CRASH_WINDOW[1]}'
    """, date_cols=["mthcaldt"])
    c20["seccap"] = c20.mthprc.astype(float).abs() * c20.shrout.astype(float) / 1000
    c20 = c20[eligible_mask(c20) & c20.seccap.notna()].groupby(["mthcaldt", "permco"]).seccap.sum().reset_index()
    c20 = c20.groupby("mthcaldt").seccap.apply(lambda s: s.nlargest(cfg.UNIVERSE_SIZE).min()).rename("cutoff_mktcap_musd").reset_index()
    L.append("\n### Same cutoff by month around the 2020 crash\n")
    L.append(md_table(c20))
    at = all_companies[all_companies["rank"].isin(CONTEXT_RANKS)].pivot(index="formation_date", columns="rank", values="mktcap")
    at = at.pct_change().mul(100).reset_index()
    at.columns = ["formation_date"] + [f"rank_{c}_yoy_pct" for c in at.columns[1:]]
    L.append("\n### Year-over-year change in market cap at other ranks\n")
    L.append(md_table(at[at.formation_date.dt.year.between(*CONTEXT_YEARS)]))

    # --- Check: links ---
    name_rate = u.gvkey.notna().mean()
    cap_rate = u.linked_cap.sum() / u.mktcap.sum()
    low_name = per[per.link_rate < cfg.MIN_LINK_RATE]
    low_cap = per[per.link_rate_cap < cfg.MIN_LINK_RATE]
    name_ok = name_rate >= cfg.MIN_LINK_RATE and not len(low_name)
    cap_ok = cap_rate >= cfg.MIN_LINK_RATE and not len(low_cap)
    if not name_ok:
        failures.append(f"Link rate by name below {cfg.MIN_LINK_RATE:.0%}: overall {name_rate:.2%}, {len(low_name)} dates below")
    if not cap_ok:
        failures.append(f"Link rate by market cap below {cfg.MIN_LINK_RATE:.0%}: overall {cap_rate:.2%}, {len(low_cap)} dates below")
    bad_sibling = siblings[~siblings.lpermco_matches] if len(siblings) else siblings
    if len(bad_sibling):
        failures.append(f"{len(bad_sibling)} sibling links have an lpermco different from the company's PERMCO: "
                        + ", ".join(f"{r.ticker} {r.formation_date.year}" for r in bad_sibling.itertuples()))
    if len(multi_link):
        failures.append(f"{len(multi_link)} link rows where one security has several GVKEYs on a date")
    if len(multi_sector):
        failures.append(f"{len(multi_sector)} sector rows where one GVKEY has several sectors on a date")
    dup_gvkey = u[u.gvkey.notna() & u.duplicated(["formation_date", "gvkey"], keep=False)]
    if len(dup_gvkey):
        failures.append(f"{len(dup_gvkey)} company-dates share a GVKEY with another company on the same date")
    no_sector = u[u.gvkey.notna() & u.gsector.isna()][["formation_date", "rank", "permno", "gvkey", "ticker", "issuernm", "mktcap"]]
    L.append("\n## 4. GVKEY links (the ID that connects CRSP prices to Compustat financials)\n")
    L.append(f"By name: **{name_rate:.2%}** overall, lowest date {per.link_rate.min():.2%}: **{'PASS' if name_ok else 'FAIL'}**. "
             f"By market cap: **{cap_rate:.2%}** overall, lowest date {per.link_rate_cap.min():.2%}: **{'PASS' if cap_ok else 'FAIL'}**. Minimum {cfg.MIN_LINK_RATE:.0%}. "
             f"Sibling links with a different lpermco: {len(bad_sibling)}. Securities with several GVKEYs on a date: {len(multi_link)}. GVKEYs with several sectors on a date: {len(multi_sector)}. "
             f"GVKEYs shared by two companies on a date: {len(dup_gvkey)}.\n")
    L.append(f"### Links that still fail ({len(fails)} company-dates, {fails.permco.nunique() if len(fails) else 0} companies; included=False)\n")
    L.append(md_table(fails) if len(fails) else "None.\n")
    L.append(f"\n### Sibling links used ({len(siblings)} company-dates, {siblings.permco.nunique() if len(siblings) else 0} companies). The held PERMNO stays the largest class.\n")
    L.append(md_table(siblings) if len(siblings) else "None.\n")
    if len(dup_gvkey):
        L.append("\n### Companies sharing a GVKEY on a date\n")
        L.append(md_table(dup_gvkey.sort_values(["formation_date", "gvkey"])[["formation_date", "gvkey", "permno", "permco", "rank", "ticker", "issuernm", "included"]]))
    L.append(f"\n### Linked but no GICS sector on the date ({len(no_sector)} company-dates; included=False)\n")
    L.append(md_table(no_sector) if len(no_sector) else "None.\n")

    # --- REIT validation ---
    has_sector = u[u.gsector.notna()]
    rows = []
    for d, g in has_sector.groupby("formation_date"):
        group = g.ggroup == GICS_REAL_ESTATE_GROUP
        rows.append({"formation_date": d, "reits_row_level": int(g.is_reit.sum()), "group_4040": int(group.sum()), "both": int((g.is_reit & group).sum()),
                     "reit_in_excluded_sector_not_4040": int((g.is_reit & g.is_excluded_sector & ~group).sum()),
                     "group_4040_not_reit": int((group & ~g.is_reit).sum()), "kept": int(g.kept_reit.sum())})
    val = pd.DataFrame(rows)
    cols = ["formation_date", "rank", "ticker", "issuernm", "gvkey", "issuertype", "gsector", "ggroup", "mktcap", "included"]
    a = has_sector[has_sector.is_reit & has_sector.is_excluded_sector & (has_sector.ggroup != GICS_REAL_ESTATE_GROUP)][cols]
    b = has_sector[(has_sector.ggroup == GICS_REAL_ESTATE_GROUP) & ~has_sector.is_reit][cols]
    c = u[u.is_reit & u.gsector.isna()][cols]
    L.append(f"\n## 5. REIT validation: row-level `issuertype` = '{cfg.REIT_ISSUER_TYPE}' vs `co_hgic` industry group {GICS_REAL_ESTATE_GROUP}\n")
    tagged = int((has_sector.is_reit | (has_sector.ggroup == GICS_REAL_ESTATE_GROUP)).sum())
    L.append(f"REIT or group {GICS_REAL_ESTATE_GROUP}: {tagged} company-dates. Agree on {int(val.both.sum())}. "
             f"REITs in an excluded sector but not in the group: {len(a)}. Group members not coded REIT (stay excluded): {len(b)}. REITs with no sector (excluded): {len(c)}.\n")
    L.append(md_table(val))
    mortgage_included = mortgage[mortgage.included] if cfg.EXCLUDE_MORTGAGE_REITS else mortgage.iloc[0:0]
    if len(mortgage_included):
        failures.append(f"{len(mortgage_included)} included rows meet the mortgage REIT rule: "
                        + ", ".join(f"{r.ticker} {r.formation_date.year}" for r in mortgage_included.itertuples()))
    L.append(f"\n### Mortgage REITs (lenders) excluded after ranking ({len(mortgage)} company-dates, {mortgage.permco.nunique()} companies)\n")
    L.append(f"Rule: row-level REIT, with `gsubind` on the date in {cfg.MORTGAGE_REIT_GICS_SUBINDUSTRIES} or a named exception {sorted(cfg.MORTGAGE_REIT_NAMED_EXCEPTIONS)}. "
             f"Included rows meeting the rule (must be 0): **{'PASS' if not len(mortgage_included) else 'FAIL'}**, {len(mortgage_included)}. "
             "The named exception is a judgment call, to be disclosed in the write-up.\n")
    L.append(md_table(mortgage) if len(mortgage) else "None.\n")
    L.append(f"\n### REIT in an excluded sector but not group {GICS_REAL_ESTATE_GROUP} ({len(a)} company-dates)\n")
    L.append(md_table(a) if len(a) else "None.\n")
    L.append(f"\n### Excluded: group {GICS_REAL_ESTATE_GROUP} but not coded REIT ({len(b)} company-dates)\n")
    L.append(md_table(b) if len(b) else "None.\n")
    L.append(f"\n### Excluded: REIT with no sector ({len(c)} company-dates)\n")
    L.append(md_table(c) if len(c) else "None.\n")
    group_dates = val[val.group_4040 > 0].formation_date
    d = has_sector[has_sector.is_reit & ~has_sector.is_excluded_sector & (has_sector.ggroup != GICS_REAL_ESTATE_GROUP) & has_sector.formation_date.isin(group_dates)][cols]
    L.append(f"\n### Included anyway: REIT outside group {GICS_REAL_ESTATE_GROUP} and outside excluded sectors, on dates the group exists ({len(d)} company-dates)\n")
    L.append(md_table(d) if len(d) else "None.\n")
    L.append(f"\nGroup {GICS_REAL_ESTATE_GROUP} has members through {group_dates.max().date()} only, so the two sources can be compared only on those dates.\n")
    moved = u[u.formation_date > group_dates.max()]
    moved = moved[moved.gvkey.isin(b.gvkey)][["formation_date", "ticker", "issuernm", "gsector", "included"]]
    L.append(f"\n### Later dates for the non-REIT group {GICS_REAL_ESTATE_GROUP} names above ({len(moved)} company-dates)\n")
    L.append(md_table(moved) if len(moved) else "None.\n")

    # --- Check: S&P 500 overlap ---
    sp = db.raw_sql(f"""select gvkey, "from" as from_date, thru from comp.idxcst_his where gvkeyx = '{cfg.SP500_GVKEYX}'""", date_cols=["from_date", "thru"])
    last_date = u.formation_date.max()
    current = sp[sp.thru.isna()]
    sp_keys = set(current.gvkey)
    sp_then = set(current[current.from_date <= last_date].gvkey)
    last = u[u.formation_date == last_date]
    ranked = set(last.gvkey.dropna())
    included = set(last[last.included].gvkey)
    sec = db.raw_sql(f"""
        select gvkey, gsector, indfrom, indthru from comp.co_hgic
        where indtype = 'GICS' and gvkey in ({sql_list(sp_keys)})
    """, date_cols=["indfrom", "indthru"])
    sec = sec[(sec.indfrom <= last_date) & (sec.indthru.isna() | (last_date <= sec.indthru))]
    sp_ex = sp_keys - set(sec[sec.gsector.isin(cfg.EXCLUDED_GICS_SECTORS)].gvkey)
    overlap = len(ranked & sp_keys)
    overlap_pct = overlap / len(sp_keys)
    L.append(f"\n## 6. Overlap of the {last_date.date()} list with current S&P 500 members (`comp.idxcst_his`)\n")
    L.append(f"Member GVKEYs: {len(sp_keys)} (latest addition {current.from_date.max().date()}; membership is today's, not May 2025's).\n")
    L.append(f"- **Headline: {overlap} of {len(sp_keys)} current members are in the 500-company list = {overlap_pct:.1%}**")
    L.append(f"- Share of the {len(ranked)} linked list names that are current members: {overlap / len(ranked):.1%}")
    L.append(f"- Members already in the index by the formation date: {len(ranked & sp_then)} of {len(sp_then)} = {len(ranked & sp_then) / len(sp_then):.1%}")
    L.append(f"- After exclusions: {len(included & sp_ex)} of {len(sp_ex)} members outside financials and utilities = {len(included & sp_ex) / len(sp_ex):.1%}\n")

    # Why current members are missing from the list
    missing = sp_keys - ranked
    lk = db.raw_sql(f"""
        select gvkey, lpermno as permno, linkdt, linkenddt from crsp.ccmxpf_lnkhist
        where linktype in ({sql_list(cfg.LINK_TYPES)}) and linkprim in ({sql_list(cfg.LINK_PRIMARY)}) and gvkey in ({sql_list(missing)})
    """, date_cols=["linkdt", "linkenddt"])
    lk = lk[(lk.linkdt <= last_date) & (lk.linkenddt.isna() | (last_date <= lk.linkenddt))]
    lk["permno"] = lk.permno.astype(int)
    last_all = m[m.formation_date == last_date].copy()
    ranks = all_companies[all_companies.formation_date == last_date][["permco", "mktcap", "rank"]]
    miss = lk.merge(last_all, on="permno", how="left").merge(ranks, on="permco", how="left")
    miss = miss.sort_values("seccap", ascending=False).drop_duplicates("gvkey")

    def reason(r):
        if pd.isna(r.formation_date):
            return "no CRSP row on date"
        if r.stopped_trading:
            return "stopped trading before the date"
        if r.usincflg != cfg.US_INCORPORATED_FLAG:
            return "not US-incorporated"
        if not eligible_mask(pd.DataFrame([r])).iloc[0]:
            return "fails share type or exchange filter"
        if r["rank"] <= cfg.UNIVERSE_SIZE:
            return "company in list, but no valid link"
        return "eligible, ranked below 500"
    miss["reason"] = miss.apply(reason, axis=1) if len(miss) else []
    unmatched = missing - set(miss.gvkey)
    summary = miss.reason.value_counts().rename_axis("reason").reset_index(name="members")
    if unmatched:
        summary.loc[len(summary)] = ["no valid link on date", len(unmatched)]
    L.append(f"### Why {len(missing)} current members are not on the list\n")
    L.append(md_table(summary))
    L.append("\n### Those members, largest first\n")
    L.append(md_table(miss[["gvkey", "ticker", "issuernm", "seccap", "rank", "reason"]].rename(columns={"seccap": "cap_musd", "rank": "rank_if_eligible"})))

    # --- Check: turnover ---
    rows = []
    dates = sorted(u.formation_date.unique())
    for a_d, b_d in zip(dates, dates[1:]):
        s0, s1 = set(u[u.formation_date == a_d].permco), set(u[u.formation_date == b_d].permco)
        i0, i1 = set(u[(u.formation_date == a_d) & u.included].permco), set(u[(u.formation_date == b_d) & u.included].permco)
        rows.append({"formation_date": pd.Timestamp(b_d), "entered": len(s1 - s0), "left": len(s0 - s1), "turnover_pct": 100.0 * len(s0 - s1) / len(s0),
                     "included_entered": len(i1 - i0), "included_left": len(i0 - i1), "included_turnover_pct": 100.0 * len(i0 - i1) / len(i0)})
    L.append("\n## 7. Year-over-year name turnover (companies leaving as % of the prior list)\n")
    L.append(md_table(pd.DataFrame(rows)))

    # --- Check: required early names ---
    rows = []
    for name in cfg.REQUIRED_EARLY_NAMES:
        h = u[u.issuernm.str.upper().str.contains(name.upper(), na=False, regex=False)]
        in_first = cfg.FIRST_FORMATION_YEAR in set(h.year)
        rows.append({"name": name, f"in_{cfg.FIRST_FORMATION_YEAR}_list": in_first, "years_in_list": ", ".join(map(str, sorted(h.year.unique()))) or "none",
                     "best_rank": int(h["rank"].min()) if len(h) else None, "gsector": ",".join(sorted(h.gsector.dropna().unique())), "ever_included": bool(h.included.any())})
        if not in_first:
            failures.append(f"{name} not in the {cfg.FIRST_FORMATION_YEAR} list")
    L.append(f"\n## 8. Required early names (all must be in the {cfg.FIRST_FORMATION_YEAR} list)\n")
    L.append(md_table(pd.DataFrame(rows)))

    # --- Definition ---
    L.append("\n## 9. Definition of US-incorporated ordinary common stock (columns in `crsp.msf_v2`; values from `config.py`)\n")
    L.append(f"- `usincflg` = '{cfg.US_INCORPORATED_FLAG}'\n- `securitytype` = '{cfg.SECURITY_TYPE}' and `securitysubtype` = '{cfg.SECURITY_SUBTYPE}'\n"
             f"- `primaryexch` in {cfg.LISTING_EXCHANGES}\n"
             f"- `sharetype` = '{cfg.ORDINARY_SHARE_TYPE}', or `sharetype` = '{cfg.REIT_SHARE_TYPE}' with `issuertype` = '{cfg.REIT_ISSUER_TYPE}'\n"
             f"- Non-null `mthprc`. Market cap = |`mthprc`| x `shrout`, summed over eligible classes by `permco`.\n"
             f"- Removed before ranking: `mthdelflg` <> '{cfg.ACTIVE_DELISTING_FLAG}' and `mthprcdt` < `mthcaldt`.\n")
    cutoffs = per.set_index("formation_date").cutoff_mktcap_musd
    other = m[~eligible_mask(m) & m.seccap.notna() & (m.usincflg == cfg.US_INCORPORATED_FLAG) & (m.securitytype == cfg.SECURITY_TYPE) & m.primaryexch.isin(cfg.LISTING_EXCHANGES)].copy()
    big = other[other.seccap >= other.formation_date.map(cutoffs)]
    L.append("### Excluded US-incorporated securities large enough to have made the list, by share and issuer type\n")
    L.append(md_table(big.groupby(["sharetype", "issuertype"]).agg(security_dates=("permno", "size"), securities=("permno", "nunique"), example=("issuernm", "first")).reset_index()))
    L.append("\nHeld securities by `sharetype`/`issuertype`:\n")
    L.append(md_table(u.groupby(["sharetype", "issuertype"]).size().rename("company_dates").reset_index()))

    # Independent check against legacy CRSP share codes
    names = db.raw_sql(f"""
        select permno, namedt, nameendt, shrcd, exchcd from crsp.msenames where permno in ({sql_ints(u.permno.unique())})
    """, date_cols=["namedt", "nameendt"])
    chk = u[["formation_date", "permno"]].merge(names, on="permno", how="left")
    chk = chk[(chk.namedt <= chk.formation_date) & (chk.formation_date <= chk.nameendt)]
    unmatched_codes = u.merge(chk[["formation_date", "permno"]].drop_duplicates().assign(ok=True), how="left", on=["formation_date", "permno"])
    unmatched_codes = unmatched_codes[unmatched_codes.ok.isna()].groupby("year").size().rename("company_dates").reset_index()
    L.append("\n### Cross-check: legacy CRSP share code of held securities (`crsp.msenames`)\n")
    L.append(f"Matched {len(chk)} of {len(u)} company-dates.\n")
    L.append(md_table(chk.groupby(["shrcd", "exchcd"]).size().rename("company_dates").reset_index()))
    L.append("\nHeld securities with no legacy code on the date:\n")
    L.append(md_table(unmatched_codes))

    # --- Removals and remaining data flags ---
    top_removed = removed[removed.eligible_otherwise & (removed.rank_before_removal <= cfg.UNIVERSE_SIZE)]
    stale_left = u[u.mthprcdt < u.formation_date]
    delist_left = u[u.mthdelflg != cfg.ACTIVE_DELISTING_FLAG]
    stopped_left = stale_left[stale_left.mthdelflg != cfg.ACTIVE_DELISTING_FLAG]
    if len(stopped_left):
        failures.append(f"{len(stopped_left)} held securities stopped trading before the formation date: "
                        + ", ".join(f"{r.ticker} {r.formation_date.year}" for r in stopped_left.itertuples()))
    if len(stale_left) > len(stopped_left):
        flags.append(f"{len(stale_left) - len(stopped_left)} held securities with no delisting flag have a price dated before the formation date")
    L.append("\n## 10. Securities removed because they stopped trading before the formation date\n")
    L.append(f"{len(removed)} security-dates removed, {int(removed.eligible_otherwise.sum())} of them otherwise eligible. "
             f"{len(top_removed)} would have ranked in the top {cfg.UNIVERSE_SIZE}, listed below. Every removal is in `universe_removed_stopped_trading.csv`.\n")
    L.append(md_table(top_removed[["formation_date", "rank_before_removal", "ticker", "issuernm", "mthprcdt", "mthdelflg", "seccap"]].rename(columns={"seccap": "cap_musd"})))
    L.append(f"\nHeld securities that stopped trading before the formation date (must be 0): **{'PASS' if not len(stopped_left) else 'FAIL'}**, {len(stopped_left)}. "
             f"Held securities left with a price dated before the formation date: {len(stale_left)}. "
             f"Held securities with a delisting flag that still priced on the date, so they stay in: {len(delist_left)}.\n")
    if len(delist_left) or len(stale_left):
        L.append(md_table(pd.concat([stale_left, delist_left]).drop_duplicates(["formation_date", "permno"])[["formation_date", "rank", "ticker", "issuernm", "mthprcdt", "mthdelflg", "included"]]))

    L.append("\n## 11. Filter waterfall (securities dropped per date, by reason)\n")
    L.append(md_table(drops))
    L.append(f"\n## 12. Output\n\n`data/clean/universe.parquet`: {len(out)} rows, {out.permco.nunique()} companies, {out.gvkey.nunique()} GVKEYs, "
             f"{out.formation_date.min().date()} to {out.formation_date.max().date()}, {int(out.included.sum())} included. mktcap is in USD millions.\n")

    verdict = ["## Result\n", f"**{len(failures)} check failure(s), {len(flags)} flag(s).**\n"] + [f"- FAIL: {f}" for f in failures] + [f"- FLAG: {f}" for f in flags] + [""]
    (LOGS / "universe_checks.md").write_text("\n".join(L[:1] + verdict + L[1:]), encoding="utf-8")

    db.close()
    print(f"rows={len(out)} included={int(out.included.sum())} overlap={overlap_pct:.1%} link_name={name_rate:.2%} link_cap={cap_rate:.2%} failures={len(failures)} flags={len(flags)}")
    for f in failures:
        print("FAIL:", f)
    for f in flags:
        print("FLAG:", f)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
