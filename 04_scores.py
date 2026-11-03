"""
Phase 3: compute Piotroski F-scores and the Checkpoint 2 review files (CLAUDE.md sections 5, 8 and 9).

Reads:  data/clean/fundamentals_clean.parquet, data/clean/universe.parquet, data/raw/comp_co_hgic.parquet,
        data/raw/crsp_ccmxpf_lnkhist.parquet. No return data is read.
Output: data/clean/fscores.parquet (every company-year in the score range; F_SCORE is null when dropped)
Tables: output/tables/handcheck_sample.csv, permco_joins_review.csv, score_distribution.csv, signal_pass_rates.csv,
        signal_pass_rates_by_year.csv, coverage_by_sector_year.csv
Charts: output/charts/fscore_histogram.png
Logs:   output/logs/scores_checks.md, scores_drops.csv
Stops at Checkpoint 2. Exit code is 1 if a check fails.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd

import config as cfg

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "output" / "logs"
TABLES = ROOT / "output" / "tables"
CHARTS = ROOT / "output" / "charts"

SIGNALS = ["F_ROA", "F_CFO", "F_DROA", "F_ACCRUAL", "F_DLEVER", "F_DLIQUID", "F_EQ_OFFER", "F_DMARGIN", "F_DTURN"]
# Whose sign does not depend on the prior year's assets, since assets are positive
SIGN_ONLY_SIGNALS = ["F_ROA", "F_CFO", "F_ACCRUAL"]
# Signals with a prior-year ratio on assets from two years back
LAG2_SIGNALS = ["F_DROA", "F_DLEVER", "F_DTURN"]

# Review files only: these choices do not affect any score.
HANDCHECK_SAMPLE = [("004503", 2023), ("012141", 2023), ("011259", 2023), ("136725", 2018)]
CHART_INK, CHART_MUTED, CHART_BAR, CHART_SURFACE = "#1a1a19", "#6b6a65", "#2a78d6", "#fcfcfb"

# My reading of each join, from the values around it. Report only: the user decides.
JOIN_READINGS = {
    "004060": "Likely invalid. Dow became DowDuPont in FY2017 (assets x2.42), so FY2017 and FY2018 mix two companies. The FY2019 split (assets x0.37, sales x0.25) keeps the same PERMCO, so it is not in this table but has the same problem.",
    "026061": "Likely invalid. IAC's record becomes the separated Match in FY2020 (assets x0.36, sales x0.50), so FY2020 and FY2021 compare different companies.",
    "032280": "Likely invalid. Liberty restructuring: FY2011 sales x4.27, and that score is on the 2012 list. FY2012 (assets x0.28) is not scored.",
    "005073": "Not in use: FY2009-2011 are not scored, so no comparison across the bankruptcy reaches a list. FY2009 includes a $104.8bn gain and FY2010 shares x3.00, so these would need review if they were ever scored.",
    "014489": "Likely invalid on the share test for FY2018: shares x3.61 around the Class V exchange. FY2019's prior-year ratios look like the same business.",
    "005568": "Likely invalid for FY2016's F_DROA and F_DTURN. Prior-year ratios divide merged FY2015 income and sales (assets x3.35, sales x1.68) by pre-merger FY2014 Heinz assets. FY2013-2015 are not scored.",
    "007637": "Looks valid: Mylan continues as acquirer. Assets x1.97 and shares x2.34 in FY2020 reflect a real deal.",
    "164296": "Looks valid: Discovery continues as acquirer. Large deal in FY2022 (assets x3.89, sales x2.77) moves the ratios.",
    "029830": "Looks valid: RockTenn continues as acquirer of MeadWestvaco in FY2015.",
    "029984": "Not in use: not scored in these years. AMB continues as accounting acquirer of ProLogis in FY2011.",
    "010984": "Looks valid: same business with purchase accounting in FY2013 (assets x1.67, sales flat). FY2014 is a flagged year, so the FY2013 score stays in use on the 2015 list.",
    "022260": "Looks valid where used: FY2010-2012 compare years after the 2006 buyout. The FY2006 share change (x0.22) is scored but on no list.",
    "004016": "Looks valid: FY2009-2010 are on lists and compare years after the 2007 buyout. FY2007 purchase accounting (assets x2.85) is on no list.",
    "005643": "Looks valid where used: FY2007-2011 values are null, so nothing is scored until FY2014, which compares years after the buyout.",
    "028320": "Not in use: FY2010-2014 are scored but on no list, since it returns in 2017. Share counts near 1 million before the IPO pass the share-count floor, so FY2013's share test (x169) is an artefact.",
    "063800": "Looks valid where used: FY2010-2011 values are null and FY2012 is not scored. FY2013-2015 compare years after the buyout, with IPO shares x1.20 in FY2014.",
    "028877": "Not in use: FY2016-2017 are null, FY2018 is flagged and FY2019 is not scored. The gvkey moves from Keurig Green Mountain to the Dr Pepper combination, so later years need checking only for that reason.",
    "006310": "Looks valid where used: FY2007-2011 are not scored because shares are null. FY2012 is on a list; assets x2.22 reflect the real El Paso deal.",
    "012485": "Looks valid where used: FY2016-2017 are not scored around the Altice purchase (assets x5.31). FY2018 compares years after it.",
    "025157": "Not in use: FY2016 is scored but on no list, since it returns only in 2019.",
}


def lag_inputs(df):
    """Attach prior-year values, null unless the year-over-year comparison is allowed."""
    d = df.sort_values(["gvkey", "fyear"]).copy()
    g = d.groupby("gvkey")
    consecutive = g.fyear.shift(1).eq(d.fyear - 1)
    prior_stub = g.stub_flag.shift(1).astype("boolean").fillna(False).astype(bool)
    if cfg.STUB_EXCLUSION == "both_sides":
        pair_ok = consecutive & ~d.stub_flag & ~prior_stub
    elif cfg.STUB_EXCLUSION == "gap_only":
        pair_ok = consecutive & ~d.stub_flag
    else:
        raise ValueError(f"Unknown STUB_EXCLUSION {cfg.STUB_EXCLUSION}")
    d["consecutive"] = consecutive
    d["pair_ok"] = pair_ok
    d["pair_ok_lag1"] = d.groupby("gvkey").pair_ok.shift(1).astype("boolean").fillna(False).astype(bool)
    d["lag2_ok"] = d.pair_ok & d.pair_ok_lag1
    for c in ["ni", "at", "dltt", "act", "lct", "sale", "cogs", "csho", "ajex", "adj_shares"]:
        d[f"{c}_lag1"] = g[c].shift(1).where(d.pair_ok)
    d["at_lag2"] = g["at"].shift(2).where(d.lag2_ok)
    return d


def compute_scores(df):
    """Ratios and signals as defined in CLAUDE.md, Phase 3. A signal is null when it cannot be computed."""
    d = lag_inputs(df)
    d["ROA"] = d.ni / d.at_lag1
    d["CFO"] = d.oancf / d.at_lag1
    d["ROA_lag1"] = d.ni_lag1 / d.at_lag2
    d["DROA"] = d.ROA - d.ROA_lag1
    d["ACCRUAL"] = d.CFO - d.ROA
    d["LEVER"] = d.dltt / ((d["at"] + d.at_lag1) / 2)
    d["LEVER_lag1"] = d.dltt_lag1 / ((d.at_lag1 + d.at_lag2) / 2)
    d["DLEVER"] = d.LEVER - d.LEVER_lag1
    d["LIQUID"] = d.act / d.lct
    d["LIQUID_lag1"] = d.act_lag1 / d.lct_lag1
    d["DLIQUID"] = d.LIQUID - d.LIQUID_lag1
    shares_ok = (d.csho >= cfg.MIN_CSHO_FOR_SHARE_TEST) & (d.csho_lag1 >= cfg.MIN_CSHO_FOR_SHARE_TEST)
    d["EQ_GROWTH"] = (d.adj_shares / d.adj_shares_lag1 - 1).where(shares_ok)
    d["MARGIN"] = ((d.sale - d.cogs) / d.sale).where(d.sale > cfg.MIN_SALE_FOR_MARGIN)
    d["MARGIN_lag1"] = ((d.sale_lag1 - d.cogs_lag1) / d.sale_lag1).where(d.sale_lag1 > cfg.MIN_SALE_FOR_MARGIN)
    d["DMARGIN"] = d.MARGIN - d.MARGIN_lag1
    d["TURN"] = d.sale / d.at_lag1
    d["TURN_lag1"] = d.sale_lag1 / d.at_lag2
    d["DTURN"] = d.TURN - d.TURN_lag1
    ratios = ["ROA", "CFO", "ROA_lag1", "DROA", "ACCRUAL", "LEVER", "LEVER_lag1", "DLEVER", "LIQUID", "LIQUID_lag1", "DLIQUID", "EQ_GROWTH",
              "MARGIN", "MARGIN_lag1", "DMARGIN", "TURN", "TURN_lag1", "DTURN"]
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
        d["zero_debt_pass"] = (d.dltt == 0) & (d.dltt_lag1 == 0)
        d.loc[d.zero_debt_pass, "F_DLEVER"] = 1.0
    d["F_DLIQUID"] = signal(d.DLIQUID > 0, d.DLIQUID)
    d["F_EQ_OFFER"] = signal(d.EQ_GROWTH <= cfg.SHARE_ISSUANCE_TOLERANCE, d.EQ_GROWTH)
    d["F_DMARGIN"] = signal(d.DMARGIN > 0, d.DMARGIN)
    d["F_DTURN"] = signal(d.DTURN > 0, d.DTURN)
    d["signals_computable"] = d[SIGNALS].notna().sum(axis=1)
    if cfg.MISSING_SIGNAL_RULE != "drop":
        raise ValueError(f"Unknown MISSING_SIGNAL_RULE {cfg.MISSING_SIGNAL_RULE}")
    d["F_SCORE"] = d[SIGNALS].sum(axis=1).where(d.signals_computable == len(SIGNALS))
    return d[d.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY)].copy()


def drop_reason(s, name):
    """Why one signal is null, one reason per company-year."""
    needs_lag2 = name in LAG2_SIGNALS
    no_prior = ~s.consecutive
    stub = s.consecutive & ~s.pair_ok
    lag2_gap = s.pair_ok & ~s.lag2_ok if needs_lag2 else pd.Series(False, index=s.index)
    out = pd.Series("null input", index=s.index)
    if name == "F_DMARGIN":
        out[(s.sale <= cfg.MIN_SALE_FOR_MARGIN) | (s.sale_lag1 <= cfg.MIN_SALE_FOR_MARGIN)] = "sale at or below minimum"
    if name == "F_EQ_OFFER":
        out[(s.csho < cfg.MIN_CSHO_FOR_SHARE_TEST) | (s.csho_lag1 < cfg.MIN_CSHO_FOR_SHARE_TEST)] = "shares below minimum"
    out[lag2_gap] = "no comparison two years back"
    out[stub] = "flagged fiscal year"
    out[no_prior] = "no prior fiscal year"
    return out


def align_for_counts(scores, universe):
    """Phase 4's logic, for counting only: latest score available by the formation date and not too old."""
    s = scores[scores.F_SCORE.notna()].sort_values(["avail_date", "datadate"])  # same tie-break as 05_align.py
    inc = universe[universe.included].sort_values("formation_date")
    m = pd.merge_asof(inc, s[["gvkey", "avail_date", "datadate", "fyear", "F_SCORE"]], left_on="formation_date", right_on="avail_date", by="gvkey", direction="backward")
    months = (m.formation_date.dt.year - m.datadate.dt.year) * 12 + (m.formation_date.dt.month - m.datadate.dt.month)
    m["age_months"] = months
    m["has_any_score"] = m.datadate.notna()
    m["scored"] = months <= cfg.MAX_SCORE_AGE_MONTHS
    return m


def join_review(scores, universe, links, aligned):
    """One row per fiscal year whose score uses a comparison across a change of PERMCO."""
    span = universe.dropna(subset=["gvkey"]).groupby("gvkey").permco.nunique()
    keys = span[span > 1].index
    rows = []
    for gv in keys:
        on_list = universe[universe.gvkey == gv]
        order = on_list.groupby("permco").formation_date.min().sort_values()
        a = scores[scores.gvkey == gv].set_index("fyear").sort_index()
        all_rows = FUND[FUND.gvkey == gv].set_index("fyear").sort_index()
        for old, new in zip(order.index, order.index[1:]):
            lk = links[links.gvkey == gv]
            old_end = lk[lk.lpermco == old].linkenddt.max()
            new_start = lk[lk.lpermco == new].linkdt.min()
            for fy, r in all_rows.iterrows():
                prior = all_rows.datadate.get(fy - 1)
                prior2 = all_rows.datadate.get(fy - 2)
                if fy not in a.index or pd.isna(prior):
                    continue
                crosses = (r.datadate >= old_end) and (prior < new_start)
                crosses_lag2 = (not crosses) and pd.notna(prior2) and (prior >= old_end) and (prior2 < new_start)
                if not (crosses or crosses_lag2):
                    continue
                x = a.loc[fy]
                used = aligned[(aligned.gvkey == gv) & aligned.scored & (aligned.fyear == fy)].formation_date
                unaffected = SIGN_ONLY_SIGNALS if crosses else [s for s in SIGNALS if s not in LAG2_SIGNALS]
                part = x[unaffected]
                rows.append({
                    "conm": r.conm, "gvkey": gv, "join_year": new_start.year, "old_permco": int(old), "new_permco": int(new),
                    "old_link_end": None if pd.isna(old_end) else old_end.date(), "new_link_start": new_start.date(),
                    "fyear": fy, "datadate": r.datadate.date(), "comparison_type": "t vs t-1 touches the window between listings" if crosses else "only t-1 vs t-2 touches the window",
                    "inputs_affected": "all nine: prior-year assets and every change" if crosses else "ROA, leverage and turnover in the prior year (F_DROA, F_DLEVER, F_DTURN)",
                    "at_yoy_ratio": round(r.at_yoy_ratio, 2) if pd.notna(r.at_yoy_ratio) else None,
                    "sale_yoy_ratio": round(r.sale_yoy_ratio, 2) if pd.notna(r.sale_yoy_ratio) else None,
                    "adj_shares_yoy_ratio": round(r.adj_shares_yoy_ratio, 2) if pd.notna(r.adj_shares_yoy_ratio) else None,
                    "scored": pd.notna(x.F_SCORE), "on_included_list_using_this_score": len(used) > 0,
                    "included_formation_dates": ", ".join(d.date().isoformat() for d in used),
                    "score_with_join_comparison": x.F_SCORE,
                    "score_without_join_comparison": part.sum() if part.notna().all() else None,
                    "signals_counted_without": len(unaffected),
                    "without_note": "No full score exists without the comparison. This counts only signals that do not use it, out of signals_counted_without. "
                                    "The window runs from the old link's end to the new link's start, so some rows compare two years inside it and are not a true break.",
                    "reading": JOIN_READINGS.get(gv, "No reading yet"),
                })
    return pd.DataFrame(rows), list(keys)


def labelled(df):
    return df.assign(universe_label=cfg.UNIVERSE_LABEL)[["universe_label"] + list(df.columns)]


def md_table(df):
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |" for row in df.itertuples(index=False)) + "\n"


def histogram(dist, path):
    """Single series: one hue, recessive axis, the peak labelled."""
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150, facecolor=CHART_SURFACE)
    ax.set_facecolor(CHART_SURFACE)
    ax.bar(dist.F_SCORE, dist.company_years, width=0.82, color=CHART_BAR)
    peak = dist.loc[dist.company_years.idxmax()]
    ax.annotate(f"{int(peak.company_years):,}", (peak.F_SCORE, peak.company_years), ha="center", va="bottom", xytext=(0, 3), textcoords="offset points", color=CHART_INK, fontsize=9)
    ax.set_xticks(range(0, 10))
    ax.set_xlabel("F-score (0 to 9)", color=CHART_MUTED)
    ax.set_ylabel("Company-years", color=CHART_MUTED)
    ax.tick_params(colors=CHART_MUTED, length=0)
    ax.yaxis.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#c9c8c2")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    n = int(dist.company_years.sum())
    fig.text(0.02, 0.97, "F-score distribution", fontsize=13, fontweight="bold", color=CHART_INK, va="top")
    fig.text(0.02, 0.91, f"{n:,} scored company-years, FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}, all companies ever on a list.\n{cfg.UNIVERSE_LABEL}", fontsize=8, color=CHART_MUTED, va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.83))
    fig.savefig(path, facecolor=CHART_SURFACE)
    plt.close(fig)


def handcheck(scores, hgic, failures):
    cols = [("Company", "conm"), ("gvkey", "gvkey"), ("GICS sector on the year-end", "gsector"), ("Fiscal year", "fyear"), ("Fiscal year-end (datadate)", "datadate"),
            ("10-K filing date", "filing_date"), ("Availability date", "avail_date"), ("Availability source", "avail_source")]
    inputs = ["ni", "at", "at_lag1", "at_lag2", "ni_lag1", "oancf", "dltt", "dltt_lag1", "act", "lct", "act_lag1", "lct_lag1", "sale", "cogs", "sale_lag1", "cogs_lag1",
              "csho", "ajex", "adj_shares", "csho_lag1", "ajex_lag1", "adj_shares_lag1"]
    ratios = ["ROA", "ROA_lag1", "DROA", "CFO", "ACCRUAL", "LEVER", "LEVER_lag1", "DLEVER", "LIQUID", "LIQUID_lag1", "DLIQUID", "EQ_GROWTH", "MARGIN", "MARGIN_lag1", "DMARGIN", "TURN", "TURN_lag1", "DTURN"]
    picked, sectors = [], []
    for gv, fy in HANDCHECK_SAMPLE:
        r = scores[(scores.gvkey == gv) & (scores.fyear == fy)]
        if r.empty or pd.isna(r.F_SCORE.iloc[0]):
            failures.append(f"Hand-check row {gv} FY{fy} has no score")
            continue
        r = r.iloc[0].copy()
        if r.avail_source != "filing" or r.stub_flag or r.outlier_flag or r.non_usd:
            failures.append(f"Hand-check row {r.conm} FY{fy} is not clean")
        h = hgic[(hgic.gvkey == gv) & (hgic.indfrom <= r.datadate) & (hgic.indthru.isna() | (r.datadate <= hgic.indthru))]
        r["gsector"] = h.gsector.iloc[-1] if len(h) else None
        picked.append(r)
        sectors.append(r["gsector"])
    if len(set(sectors)) != len(sectors):
        failures.append(f"Hand-check sectors are not all different: {sectors}")
    rows = []
    for label, c in cols:
        rows.append({"item": label, **{p.conm: (p[c].date() if isinstance(p[c], pd.Timestamp) else p[c]) for p in picked}})
    for section, fields, digits in [("Input, USD millions (shares in millions; _lag1 = prior year, _lag2 = two years back)", inputs, 3), ("Ratio", ratios, 6)]:
        rows.append({"item": section})
        for c in fields:
            rows.append({"item": c, **{p.conm: round(float(p[c]), digits) for p in picked}})
    rows.append({"item": "Signal (1 = pass)"})
    for c in SIGNALS:
        rows.append({"item": c, **{p.conm: int(p[c]) for p in picked}})
    rows.append({"item": "Zero-debt rule used for F_DLEVER", **{p.conm: bool(p.zero_debt_pass) for p in picked}})
    rows.append({"item": "F_SCORE", **{p.conm: int(p.F_SCORE) for p in picked}})
    labelled(pd.DataFrame(rows)).to_csv(TABLES / "handcheck_sample.csv", index=False)
    return picked


FUND = None


def main():
    global FUND
    for p in (LOGS, TABLES, CHARTS):
        p.mkdir(parents=True, exist_ok=True)
    failures = []

    FUND = pd.read_parquet(CLEAN / "fundamentals_clean.parquet")
    universe = pd.read_parquet(CLEAN / "universe.parquet")
    hgic = pd.read_parquet(RAW / "comp_co_hgic.parquet")
    links = pd.read_parquet(RAW / "crsp_ccmxpf_lnkhist.parquet")

    s = compute_scores(FUND)
    s.to_parquet(CLEAN / "fscores.parquet", index=False)

    # --- Checks ---
    n, scored = len(s), s.F_SCORE.notna()
    if s.duplicated(["gvkey", "fyear"]).any():
        failures.append("Duplicate gvkey-fyear rows in the scores")
    if not s.F_SCORE.dropna().between(0, len(SIGNALS)).all():
        failures.append("F_SCORE outside 0-9")
    if not (s.loc[scored, SIGNALS].sum(axis=1) == s.loc[scored, "F_SCORE"]).all():
        failures.append("F_SCORE differs from the sum of its signals")
    if not s[s.fyear.between(cfg.FIRST_SCORE_FY, cfg.LAST_SCORE_FY)].fyear.min() >= cfg.FIRST_SCORE_FY:
        failures.append("Scores before FIRST_SCORE_FY")
    stubs_scored = s[s.stub_flag & scored]
    if cfg.STUB_EXCLUSION in ("both_sides", "gap_only") and len(stubs_scored):
        failures.append(f"{len(stubs_scored)} flagged fiscal years were scored")
    placeholder = s[scored & ((s.csho < cfg.MIN_CSHO_FOR_SHARE_TEST) | (s.csho_lag1 < cfg.MIN_CSHO_FOR_SHARE_TEST))]
    if len(placeholder):
        failures.append(f"{len(placeholder)} scores use a share count below the minimum")
    lookahead = s[s.avail_date <= s.datadate]
    if len(lookahead):
        failures.append(f"{len(lookahead)} availability dates fall on or before the year-end")

    # --- Drops by reason and by signal ---
    reasons = []
    for name in SIGNALS:
        miss = s[s[name].isna()]
        if len(miss):
            reasons.append(drop_reason(miss, name).value_counts().rename_axis("reason").reset_index(name="company_years").assign(signal=name))
    drops = pd.concat(reasons)[["signal", "reason", "company_years"]]
    drops.to_csv(LOGS / "scores_drops.csv", index=False)
    by_signal = drops.pivot(index="signal", columns="reason", values="company_years").fillna(0).astype(int).reindex(SIGNALS).reset_index()
    by_signal["total_uncomputable"] = by_signal.drop(columns="signal").sum(axis=1)
    missing_count = (s[SIGNALS].isna()).sum(axis=1)
    only_one = s[missing_count == 1]
    sole = only_one[SIGNALS].isna().sum().rename("dropped_for_this_signal_alone").rename_axis("signal").reset_index()

    # --- Distribution and pass rates ---
    dist = s.loc[scored, "F_SCORE"].value_counts().reindex(range(0, 10), fill_value=0).rename_axis("F_SCORE").reset_index(name="company_years")
    dist["share_pct"] = (100 * dist.company_years / dist.company_years.sum()).round(2)
    a = align_for_counts(s, universe)
    list_dist = a[a.scored].F_SCORE.value_counts().reindex(range(0, 10), fill_value=0).rename("included_list_rows").reset_index(drop=True)
    dist["included_list_rows"] = list_dist
    dist["included_list_share_pct"] = (100 * dist.included_list_rows / dist.included_list_rows.sum()).round(2)
    labelled(dist).to_csv(TABLES / "score_distribution.csv", index=False)
    histogram(dist, CHARTS / "fscore_histogram.png")

    scored_rows = s[scored]
    rates = pd.DataFrame({
        "signal": SIGNALS,
        "pass_pct_scored": [round(100 * scored_rows[c].mean(), 1) for c in SIGNALS],
        "pass_pct_all_computable": [round(100 * s[c].mean(), 1) for c in SIGNALS],
        "computable_company_years": [int(s[c].notna().sum()) for c in SIGNALS],
    })
    labelled(rates).to_csv(TABLES / "signal_pass_rates.csv", index=False)
    by_year = scored_rows.groupby("fyear")[SIGNALS].mean().mul(100).round(1)
    by_year["mean_F_SCORE"] = scored_rows.groupby("fyear").F_SCORE.mean().round(2)
    by_year["scored_company_years"] = scored_rows.groupby("fyear").size()
    by_year = by_year.reset_index()
    labelled(by_year).to_csv(TABLES / "signal_pass_rates_by_year.csv", index=False)

    # --- Coverage, counts only ---
    a["year"] = a.formation_date.dt.year
    cov = a.groupby(["year", "gsector"]).agg(included=("permco", "size"), scored=("scored", "sum")).reset_index()
    labelled(cov).to_csv(TABLES / "coverage_by_sector_year.csv", index=False)
    sector = a.groupby("gsector").agg(included=("permco", "size"), scored=("scored", "sum")).reset_index()
    sector["scored_pct"] = (100 * sector.scored / sector.included).round(1)
    year = a.groupby("year").agg(included=("permco", "size"), scored=("scored", "sum")).reset_index()
    year["scored_pct"] = (100 * year.scored / year.included).round(1)
    stale = int((a.has_any_score & ~a.scored).sum())
    none = int((~a.has_any_score).sum())
    pivot = cov.pivot(index="year", columns="gsector", values="scored").fillna(0).astype(int).reset_index()

    # --- PERMCO joins ---
    joins, span_keys = join_review(s, universe, links, a)
    labelled(joins).to_csv(TABLES / "permco_joins_review.csv", index=False)
    if len(span_keys) != cfg.EXPECTED_SPAN_GVKEYS:
        failures.append(f"Expected {cfg.EXPECTED_SPAN_GVKEYS} gvkeys spanning two PERMCOs, found {len(span_keys)}")
    no_read = [g for g in span_keys if g not in JOIN_READINGS]
    if no_read:
        failures.append(f"No reading written for join gvkeys {no_read}")

    picked = handcheck(s, hgic, failures)
    if not any(p.zero_debt_pass for p in picked):
        failures.append("No hand-check row uses the zero-debt rule")

    # --- Report ---
    L = [f"# Phase 3 checks: {cfg.UNIVERSE_LABEL}\n", "## Result\n", f"**{len(failures)} check failure(s).** Stop here: Checkpoint 2.\n"]
    L += [f"- FAIL: {x}" for x in failures] + [""]
    L.append("## Scores\n")
    L.append(f"{int(scored.sum())} of {n} company-years scored, FY{cfg.FIRST_SCORE_FY}-{cfg.LAST_SCORE_FY}; {n - int(scored.sum())} dropped under `MISSING_SIGNAL_RULE`. Companies scored: {s[scored].gvkey.nunique()} of {s.gvkey.nunique()}. Mean score {s.F_SCORE.mean():.2f}, median {s.F_SCORE.median():.0f}.\n")
    L.append(md_table(dist))
    L.append("\n`included_list_rows` counts one score per included company per formation date, so it weights each list equally.\n")
    L.append("\n## Pass rate per signal (share passing; F_D = year-over-year improvement)\n")
    L.append(md_table(rates))
    L.append("\n## Pass rate per signal by fiscal year (scored company-years, %)\n")
    L.append(md_table(by_year))
    L.append("\n## Drops: why each signal could not be computed\n")
    L.append("A company-year can miss several signals, so these overlap.\n")
    L.append(md_table(by_signal))
    L.append(f"\nCompany-years missing exactly one signal: {len(only_one)}.\n")
    L.append(md_table(sole))
    L.append("\n## Coverage of included formation-date names (counting only; Phase 4 logic)\n")
    L.append(f"{int(a.scored.sum())} of {len(a)} included rows have a score no more than {cfg.MAX_SCORE_AGE_MONTHS} months past its fiscal year-end, counted in calendar months. No score available: {none}. Too old: {stale}. Availability date must be on or before the formation date.\n")
    L.append("### By sector\n")
    L.append(md_table(sector))
    L.append("\n### By formation year\n")
    L.append(md_table(year))
    L.append("\n### Scored names by formation year and sector\n")
    L.append(md_table(pivot))
    L.append(f"\n## PERMCO joins ({len(span_keys)} gvkeys span two PERMCOs). Nothing dropped; the user decides.\n")
    used = joins[joins.on_included_list_using_this_score]
    L.append(f"{len(joins)} fiscal-year rows use a comparison touching the window between two listings; {int(joins.scored.sum())} are scored; {len(used)} are the score on an included list. "
             "This test only sees changes of PERMCO: a split that keeps the PERMCO, such as DuPont FY2019, is not caught. Full table: `output/tables/permco_joins_review.csv`.\n")
    L.append(md_table(used[["conm", "join_year", "fyear", "comparison_type", "included_formation_dates", "score_with_join_comparison", "score_without_join_comparison", "signals_counted_without"]]))
    L.append("\n## Hand-check sample (`output/tables/handcheck_sample.csv`)\n")
    L.append(md_table(pd.DataFrame([{"company": p.conm, "gsector": p.gsector, "fyear": p.fyear, "datadate": p.datadate.date(), "filing_date": p.filing_date.date(), "F_SCORE": int(p.F_SCORE), "zero_debt_rule": bool(p.zero_debt_pass)} for p in picked])))
    (LOGS / "scores_checks.md").write_text("\n".join(L), encoding="utf-8")

    print(f"scored={int(scored.sum())}/{n} included_scored={int(a.scored.sum())}/{len(a)} joins={len(joins)} joins_used={len(used)} failures={len(failures)}")
    print(dist.to_string(index=False))
    for x in failures:
        print("FAIL:", x)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
