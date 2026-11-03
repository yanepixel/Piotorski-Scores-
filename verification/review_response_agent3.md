# Review response, Agent 3 (audit)

Scripts: `audit_38_delisting.py`, `audit_39_capweight.py`, `audit_40_spec_v2.py` (run again this session), and new `audit_41_net_rule_power.py`. Read-only on WRDS; no raw files written; Agent 2 files and `spec_v2_compare.md` not read.

## Correction to my own earlier work (High)

`audit_40_spec_v2.py` section C divided the annual standard error by 12 a second time (`hac()` already returns annualised estimates). Its "SE 0.07%", "MDE 0.19%" and "power 1.00" lines are wrong. Corrected in `audit_41` (raw High minus scored-only benchmark, lag 4, t with T-1 df):

| Period | T | SE a year | MDE at 80% power | MDE at first Holm-6 step | Power, true +1.7% | Power, true +3.0% |
|---|---|---|---|---|---|---|
| Full | 247 | 0.80% | 2.26% | 2.61% | 0.56 | 0.96 |
| 2005-15 | 120 | 1.00% | 2.82% | 3.27% | 0.39 | 0.85 |
| 2015-25 | 127 | 1.19% | 3.35% | 3.89% | 0.30 | 0.71 |

The other numbers in audit_40 (sizes, p-values, Holm table, availability) do not use that SE and stand.

## Item 1. Restated data (Medium; cannot be extended)

- Source of the 2005-2015 test: `compsamp_snapshot.wrds_csa_pit` (sample library), 1,480 companies, 55 project companies, 446 project company-dates (`data_audit_phase2_3.md` section 2).
- Re-checked today: `comp_snapshot` (full point-in-time) is still "no permission". `compsamp_snapshot` is readable, but `wrds_csa_pit` ends at FY2014. So FY2015-2024 and formation years 2016-2025 cannot be tested, and I did not try to get around the permission.
- What exists: 98.5% of scores unchanged (97.3% for project companies), 0.2% bucket change (0.45%), 98.9% of today's High were High then, for 2005-2015 only. Share of High-to-High and bucket change for 2016-2025 is unknown.
- What is missing: full `comp_snapshot` access (or another as-first-reported source) for FY2015-2024. A partial substitute within the account would be Audit Analytics restatement flags for 2015-2024 to count exposed company-years; that gives exposure, not score changes, and is not done.

## Item 2. Delisting returns (Low; premise does not apply)

Method: for every included row, the held return series ends before its window ends; matched to `crsp.msedelist` (permnos in the project, dlstdt through 2024-12-31).

- 193 exits inside holding windows across all included rows; 179 are held (scored).
- Held exits by code: 173 merger (2xx), 2 exchange (3xx), 3 with no delisting record (the three non-trading cases), **1 performance-coded (5xx)**: one company in the Low bucket, formation 2015, last month 2016-04, with its return and delisting return already recorded.
- Held 5xx exits with mthret exactly 0 or dlret missing: **0**. Held exits with mthret = 0 under any code: 0. Among all included (including unscored) 5xx exits: 1, zero return 0.
- Of 27 5xx rows for project permnos in total, 26 fall outside any holding window.
- Shumway -30% scenarios (replace where missing/zero; floor every 5xx at -30%; extra -30% on every 5xx): the first two replace 0 rows; the third touches that one company only. High 10.91% CAGR, alpha -0.78% (t -0.71), Benchmark 11.35%, Low 10.93%: no change at two decimals in every scenario.
- The premise (optimistic hold-flat) is about the three non-trading cases, not delistings; it does not apply to delistings, which carry real delisting returns here.
- Limit: `msedelist` ends 2024-12-31 in this extract, so 2025 exits rest on `msf_v2` alone and are not cross-checked.

## Item 3. Cap-weighted High (Low-Medium; not unusual, not mega-cap driven)

Actual cap-weighted: High CAGR 11.23% vs benchmark 12.64% (gap -1.41), excess -0.99% a year (t -0.85), Sharpe 0.63 vs 0.78, alpha -0.78% (t -0.54). My rebuild matches the published file to 1e-16.

1,000 draws, cap-weighted, same number of High names each date:

| Placebo | Mean excess | Share of draws at or below actual: excess | Sharpe gap | alpha t | Share with abs(excess t) >= 2 |
|---|---|---|---|---|---|
| Random High | -0.29% | 28.6% | 10.0% | 12.6% | 7.0% |
| Within-sector High | -0.32% | 26.8% | 13.5% | 16.4% | 4.3% |

A random cap-weighted subset already lags the cap-weighted benchmark (mean -0.3%) and the actual sits at the 27th-29th percentile on excess return and the 10th-14th on Sharpe gap. Mild, not unusual at 5%.

Mega-caps: High holds a similar weight in the top 10 (29.2% vs 27.7% benchmark), and holds none of the top 5 on 24% of dates. Dropping the top 5 or 10 by market cap each date widens the gap (-2.0%) rather than closing it; dropping the top 20 gives -1.2%. Active return by name: High names +9.5 points a year, non-High (underweights) -10.4, total -0.84. No single name accounts for the gap: the largest individual active contributions, positive or negative, are about one point a year or less. The ten worst and ten best names offset roughly (-1.73 vs +2.04), so the result is about the few large winners High did or did not own, spread over several names, not one.

## Item 4. v2 spec gaps before results

**Net issuance rule (sstk - prstkc, null as zero).** Read-only `comp.funda` pull, 13,993 scored company-years, v1 other signals unchanged:
- Not degenerate. Pass rate: v1 share test 80.7%, literal sstk 20.1%, net 67.8%. High 1,380 rows vs 1,553 (1,323 stay High); High median per date 61 (min 42, max 112); Low median 34; mean score 6.19 vs 6.28.
- Nulls: sstk null 3.2%, prstkc null 4.1%, both null 0.1%. sstk negative in 84 rows (a negative sstk lowers net, helping pass; the spec does not say to floor it); prstkc never negative.
- Pass rate drifts with time: 43% (2004), 52% (2005), 44% (2009), 74% (2015), 83% (2022-23). I did not test why (option proceeds versus buybacks is a guess); this shifts High composition toward later years.
- Agreement with v1: net passes and v1 fails 4.5%; net fails but v1 passes 17.4%. Net failers: 46% had share growth over 2%, 1.8% had growth at or below 0. Net passers: 71% had growth at or below 0, but 6.6% still had share growth over 2% (stock compensation, stock-funded deals, which sstk and prstkc miss).
- Bias: a net buyback passes the test even when it is a buyback of shares funded by debt and the firm issued stock; this favours large cash-rich buyback firms. Null-as-zero is asymmetric: null prstkc with real issuance counts as a fail (conservative), null sstk with a buyback counts as a pass. Both are small (about 4%).
- Do not pick between literal and net by returns; the spec already fixed net before returns and the sensitivity is reported beside.

**No-fallback and 3-day buffer (survivorship from dropping late filers).** Small and not clearly biased:
- 50 of 7,571 held rows lost (0.66%): 6 fallback-dated, 47 filed 0-3 days before formation (15 on the formation date). By year 1-7 rows. Their scores: 5 to 9, with 9 High.
- Equal-weight benchmark CAGR (gross, labelled check) 11.39% all vs 11.40% without them. The dropped rows' own simple mean return 11.28% vs 12.15% for all scored (211 months): slightly lower, not a dropped-winners pattern.
- Spec gap, now closed by CLAUDE.md 8f Clarifications (4): the most recent earlier scored year is used if it passes the filing date + 3 test, with the 18-month age rule. Applied to the 50 lost rows (`audit_42_older_year.py`): **43 are scored from an older year**, **4 go stale** (23, 53, 23 and 22 months old, against the 18-month limit) and **3 have no earlier scored year** (two in 2005 and one new listing in 2021), The 6 fallback-dated rows are all among the 7 that are stale or have no earlier year (none uses an older year), so the 43 older-year cases are all rows filed 0-2 days before formation.
- Effect of the older year: mean absolute score change 1.21 points; 14 of the 43 change bucket (newest-year bucket to older-year bucket: 6 High to Middle, 3 Middle to High, 4 Middle to Low, 1 Low to Middle). Of the 9 lost High rows, 7 get an older score (1 stays High, 6 become Middle) and 2 drop out (one stale, one with no earlier scored year). So the rule replaces a newest-year score with a one-year-old score for about 0.6% of held rows and it is not systematically upward. Fallback company-years overall are 528 of 18,159 (2.9%), almost all outside the held lists.

**Newey-West automatic lag.** `floor(4*(T/100)^(2/9))` gives 4 for T = 120, 127 and 247, versus 12 in v1. Simulated size of the lag-4 test with t(T-k) critical values: 0.049-0.070 under iid and 0.028-0.069 under block-12 residuals (nominal 0.05). Slight over-rejection for raw excess (0.069) and some under-rejection for 2015-25 alpha with block residuals (0.028). Keep the lag-12 sensitivity beside, as specified. t(T-k) does not fix the lag-4 over-rejection.

**Holm family.** Six tests (raw excess and four-factor alpha, across full and the two subperiods). Holm is valid under dependence but the full period and subperiods overlap, so it is conservative. The split date 2015-05 and the 2015-25 weakness were seen in v1 (six-factor t -4.10; four-factor lag-4 p 0.0065), so the subperiod tests are not blind. On v1 data Holm would reject only 2015-25 alpha (0.0065 vs threshold 0.0083). The family should be stated as two-sided and the v1 knowledge disclosed.

**Power.** See the corrected table above: the subperiod tests can detect only 2.8%-3.4% a year excess at 80% power.

**One more gap.** The primary benchmark includes unscored included names (REITs, most homebuilders, finance arms, per section 8b), so High-minus-benchmark mixes the score effect with the effect of being scorable. The scored-only benchmark is reported beside; interpret the primary one with that in mind.

## Item 5. Paper check (Medium; wording, redone with the Table 4 figures supplied)

Table 4 as transcribed by the master (not checked by me against the PDF): one-year market-adjusted returns, high book-to-market firms 1976-1996. Large firms: All 0.003 (n 1,835), Low -0.132 (n 34), High 0.020 (n 161); High minus All 0.017 (t 0.872, p 0.203); High minus Low 0.152 (t 1.884). Small firms: High minus All 0.088 (t 2.456), High minus Low 0.270 (t 4.709). Medium: High minus All 0.071 (t 2.870), High minus Low 0.173. The paper says differentiation is weak among the largest firms.

What can be said:
- **Direction and significance fit.** The paper's large-firm High minus All is +1.7 points with t 0.87 (not significant); ours is -0.29% a year with t -0.37 (lag 4), also not significant. The paper's own large-firm High minus Low (t 1.88) is not significant at 5% either.
- **Our universe is more extreme than the paper's "large" group.** The paper finds the gain isolated to the bottom two-thirds of market cap; the top 500 US companies sit well above that, so a null is what the paper's own result predicts.
- **Power is a fair caveat, but the sentence needs care.** In our units, an effect of +1.7% a year would be detected only 56% of the time over the full period (0.30 and 0.39 in the subperiods). But the full-period 95% interval for our excess is about -1.9% to +1.3% (-0.29% +/- 1.97 x 0.80%), which just excludes +1.7% (t of about -2.5 against +1.7%, -2.3 with lag 12). So "too little power to confirm or reject" understates the full-period result and overstates it for the subperiods. The two numbers are not strictly comparable: the paper's is a pooled cross-section of one-year market-adjusted returns on 161 High firms, ours a monthly time series of portfolio returns against an equal-weight benchmark, and the paper's sample is high book-to-market only, 1976-1996.
- **High minus Low is not comparable.** The paper's Low is 0-1 (n 34 large firms, mean -13.2%, which carries its 0.152); ours is 0-4, and our High and Low CAGRs are about equal (10.91% vs 10.93%; spread alpha -2.04%, t -0.72). I did not rerun a Low 0-1 portfolio, which is empty in some years.

Suggested wording: "Our top-500 null is consistent with the paper's own finding that the effect is weak in its largest firms (High minus All +1.7 points, t 0.87). The tests are not directly comparable (different return measure, sample and Low definition), and over the full period our estimate is below +1.7% a year by about 2.3 to 2.5 standard errors, while the subperiod tests could detect only an effect of about 3% a year or more." "Consistent with" is fair; "too little power to confirm or reject" is fair only for the subperiods and for the High-minus-Low comparison.

## Earlier questions still unanswered

- Restatement exposure for FY2015-2024 (needs comp_snapshot access).
- (Closed) the 43 of 50 rows: older year used under 8f Clarifications (4); 4 stale, 3 no earlier year.
- Table 4 figures are the master's transcription; I have not seen the PDF.
- 2025 delistings, not cross-checked with `msedelist`.
- The net-rule scores themselves: my numbers use v1 other signals; Agent 1's `scores_checks_v2` tables should be compared with the figures above (not read).

---

# Audit of the v2 build (2026-11-02)

Scripts: `audit_43_v2_audit.py`, `audit_44_nw94.py`. Read: scripts 12b, 13, 14, `output/spec_v2/*` and `data/clean/spec_v2/*`. Not read: Agent 2 files, `spec_v2_compare.md`. No raw data written.

## Flag (High, wording): the one Holm rejection is fragile to the HAC convention

2015-25 High four-factor alpha, -3.38% a year, from `portfolio_returns_v2.csv` (Newey-West, Bartlett weights, T-k degrees of freedom; Holm over the six pre-specified p-values):

| Convention | t | Holm-adjusted p | Rejects at 5% |
|---|---|---|---|
| As run: statsmodels HAC, lag 4, no small-sample correction | -2.70 | 0.047 | yes |
| Lag 4 with T/(T-k) correction | -2.65 | 0.055 | no |
| Lag 6, no correction | -2.94 | 0.024 | yes |
| Lag 12, no correction (v1's lag) | -3.72 | 0.002 | yes |
| Lag 12 with correction | -3.65 | 0.002 | yes |

- What was used matches the spec: `14_spec_v2_evaluate.py` calls statsmodels HAC with `maxlags = floor(4*(T/100)^(2/9))` = 4 and takes p from t with T-k df. statsmodels' HAC has no small-sample correction by default; my own `hac()` is the same formula, and the as-run numbers reproduce exactly. The spec names no correction, so this is compliant.
- "Newey-West 1994 automatic" in the spec is the rule-of-thumb lag only. The full data-dependent plug-in bandwidth is unstable at these sample sizes: 59 lags for T = 127, 10 for 2005-15, 24 for the full period (t -6.06 at 59 lags, not credible). Do not use it.
- Wording: say "rejects at Holm 0.047 under the pre-specified convention; it does not clear 5% (0.055) if the variance gets a degrees-of-freedom correction, and it clears under lag 6 and lag 12". Do not describe it as robust or as failing. No other test in the family comes near.
- Holm is implemented correctly (step-down, checked against the textbook form).

## 1. Look-ahead and alignment (no error found)

- Filing dates in `formation_v2` equal the earliest 10-K `filedate` in `comp_co_filedate.parquet` on all 7,614 scored rows (0 differences, 0 null).
- Minimum gap, formation date minus filing date: 3 days; rows under 3: 0. Rows with year-end on or after the formation date: 0. Rows older than 18 months: 0.
- The score is attached by `merge_asof` on the buffered date, then the 18-month rule: matches 8f Clarification (4). Valid rows where a higher fiscal year was also known: 0 (no inversions among scored years).
- v1 scored rows (7,571) in v2: 7,564 valid, 4 stale, 3 missing. Of the valid, 7,521 use the same fiscal year as v1, 43 an older year, none a later one. This matches my own count exactly (43 older, 4 stale, 3 no earlier year).
- prstkc: 20,796 rows merged 1:1, 0 unmatched, 0 duplicates, null 5.6%. It is the same gvkey-datadate-fyear row as sstk, so the same period and the same current-vintage limit as every other input; no extra look-ahead. Both fields include preferred stock, so the net is like for like.
- F_EQ_OFFER equals `(sstk - prstkc <= 0)` with nulls as 0 on all 14,111 scored company-years.
- Reporting error (Low): `scores_checks_v2.md` section 5 says 13 list rows use an older year "because the newest year is unscorable or not yet available". That count uses the buffered availability date, so it only counts newest years that are known but unscorable; the 43 rows pushed back by the buffer or fallback rule are not in it. Rows scored from an older year than v1: 43.

## 2. Pipeline against my independent net-rule check

| Item | Pipeline | Mine |
|---|---|---|
| Net pass rate, scored company-years | 67.9% | 67.8% (v1 other signals) |
| By year | 43.0% (FY2004), 83.0% (FY2022) | 43% and 83% |
| sstk negative, scored | 84 | 84 |
| High list rows | 1,408 | 1,380 (v1 other signals); the 28 difference is ib, the zero-debt override and 50 newly scored rows |
| High staying High | 1,302 of 1,553 | 1,323 (v1 other signals) |
| 43 older / 4 stale / 3 none | 43 / 4 / 3 | 43 / 4 / 3 |

All agree within the expected difference. Bucket changes versus v1: 681 of 8,414 list rows (High -145, Low +130, Middle +58); High to Middle is 249 and Middle to Low 198, consistent with the net rule scoring more firms as issuers.

## 3. HAC, t(T-k), Holm, power

See the flag above. The pipeline numbers reproduce from the returns file. Power: minimum detectable raw excess 2.1% (full), 2.8% (2005-15), 3.1% (2015-25); four-factor alpha 3.2% to 4.1%.

## 4. Reinvestment charge and benchmark mechanics (no error found)

- My own gross rebuild of High, Middle, Low and the all-included Benchmark from `formation_v2` and `crsp_msf_v2` (equal weight, drift, pro-rata reinvestment, Maxim and General Growth held flat) matches the published `_gross` columns to 1e-16.
- The reinvestment charge is the exiting position's drifted weight times 10 bps, taken in the exit month, one side, none in the final month, none for hold-flat months. This matches 8f (7). Timing nit: the purchase happens at the next month's start but the cost falls in the exit month; immaterial.
- The only hold-flat cases are Maxim (seven months) and General Growth, both only in the all-included benchmark. Assuming 0% for Maxim for those months is an unmeasured error of a few hundredths of a point in one year's benchmark at most.

## 5. Middle in 2015-25 (+0.99%, t 2.30): plausible, not a bug

- From my rebuild, gross annualised excess versus the all-included benchmark in 2015-25: High -0.78%, Middle +1.03%, Low +0.66%, **Unscored -5.29%** (Unscored CAGR 4.88% against 10.83% for all included). Full period: Unscored -3.81%.
- Unscored names are 9.5% of list rows, mostly real estate and REITs (sector 60: 210 of the unscored rows from 2015), which the nine-signal rule cannot score (no liquidity ratio). Their poor 2015-25 return pulls the benchmark below every scored bucket, and Middle, the largest bucket (63.6% of rows), gets most of the mirror image. So the +0.99% is about the unscored group, not about the score.
- Consequence: the all-included benchmark flatters every scored bucket by about 0.5% a year over the full period relative to the scored-only benchmark. High's full-period excess is +0.08% (t 0.10) against the primary benchmark and -0.42% (t -0.56) against scored-only. The change of sign comes from benchmark composition, not from the v2 scores. Always show the two together, and describe the Middle result as a benchmark-composition effect.
- Nothing looks too good or too bad: all point estimates are within the range of v1. High alpha -0.15% (t -0.13) full period, -3.38% (t -2.70) in 2015-25, +2.28% (t 1.56) in 2005-15.

## 6. Do the write-up's v1 claims need changing?

Not in direction, and nothing here suggests a rule change from performance:
- v1 headline: High 10.91% against 11.35% for the scored-only benchmark, six-factor alpha -0.78% (t -0.71). v2: High 10.75%; against scored-only 11.36%, against all-included 10.79%; six-factor alpha -0.86% (t -0.75). The "no benefit in the top 500" answer stands.
- Disclose that the benchmark choice moves the sign of High minus benchmark (+0.08% against all-included, -0.42% against scored-only), and that v1 used scored-only.
- 2015-25 weakness: v2 four-factor alpha -3.38% (t -2.70), six-factor -3.79% (t -3.01 at lag 4, -4.08 at lag 12). Keep the existing wording (t -2.5 to -3.6 defensible) and add the lag and Holm note above.
- 2005-15: High alpha +2.28% (t 1.56, lag 12 t 1.94, p 0.054), similar to v1 and still not significant.
- Low is broader and a little weaker in v2 (10.19% CAGR, 858 rows); this is not a reason for any change.
- State that v2 is a re-specification fixed before returns, that the net issuance rule replaced the literal rule before returns because the literal rule flagged 77% as issuers (pass rate 20%), and that the literal sensitivity is reported beside.

---

# Audit of the new write-up and README (2026-11-02)

Read in full: `output/writeup.md`, `README.md`; read the relevant parts of `17_spec_v2_writeup.py`, `writeup_figures_v2.csv`, and the v2 tables. Script: `audit_45_writeup_trace.py`. Report only; no files outside `verification/` changed. No High item found.

## Summary

Every figure I could recompute reproduces. The claims are not stronger than the evidence. Four wording and traceability fixes (Medium) and four smaller ones (Low) are listed. I did not run git, so I could not check the four commit hashes or their order against the first v2 return.

## 1. Figure trace

Reproduced exactly from `portfolio_returns_v2.csv`, the factor file and the other v2 tables:
- 95% range -1.42% to +1.57% (estimate +0.08%, SE 0.76%, t critical value 1.970 on 246 df) and minimum detectable effect 2.13%.
- Excess table: High +0.08% (t +0.10), Middle +0.50% (t +1.52), Low -0.09% (t -0.05); against scored-only -0.42% (-0.56), +0.01% (+0.02), -0.59% (-0.31); tracking errors 4.13%, 1.47%, 7.68%; information ratios +0.02, +0.34, -0.01.
- All four factor-regression rows (alphas and every loading), including the Spread six-factor -1.53% (t -0.68).
- Complete years: High beat the all-included benchmark in 9 of 20 and the scored-only one in 10 of 20; literal rule 10 of 20; partial 2025 year High 11.17%, all-included 9.75%, scored-only 10.41%.
- Subperiod table (CAGRs, excess, Spread); Middle 2015-25 +0.99% (t +2.30) against all-included and +0.39% (t +0.92) against scored-only.
- Literal-rule table (High 11.74%, +1.19% t +0.86; Middle 11.16%, +0.27%; Low 10.86%, +0.19%; High four-factor alpha +0.77% t +0.53).
- Costs: High's rebalance cost 0.166% a year plus 0.002% reinvestment; 191 mid-period exits (Middle 125, Low 28, High 27, Unscored 11) and 4 formation-date delisters.
- SE-convention table (lag 4 as run, lag 4 with T/(T-k), lag 6, lag 12) matches my own recomputation row for row, including Holm 0.047 / 0.055 / 0.024 / 0.002 for the 2015-25 four-factor alpha.

Hand-copied figures checked against my reports: the restatement test (1,480 companies, 98.5%, 0.2%, 55 companies, 97.3%, 0.45%) and the `comp_snapshot` limit match `data_audit_phase2_3.md` and my item 1. The Table 4 numbers (+0.017, t 0.872, +0.088, t 2.456) match the master's transcription; I have not seen the PDF.

Problems found:
- **Medium: the -5.3% is not traceable and is attributed to an internal agent.** Line 123 says "(Agent 3's recomputation, not reproduced here)". A reader cannot follow that. The figure is reproducible: `verification/audit_43_v2_audit.py` gives -5.29% a year gross for the unscored group against the all-included benchmark in 2015-25 (unscored CAGR 4.88% against 10.83%). Replace the parenthesis by that file name, say it is a gross figure, and keep the script. Line 248 says the write-up "does not restate" the audit conclusions, which this sentence and the standard-error table contradict.
- **Medium: line 197 gets the buffer and fallback split wrong.** It says the buffer moves 43 rows to an earlier year, "1 buffer case went stale and 1 had no earlier score". My cross-tabulation of v1 scored rows against v2: buffer cases (filed less than 3 days before) 44 = 43 older year + 1 stale; fallback-dated cases 6 = 3 stale + 3 with no earlier score. Totals 43 / 4 stale / 3 none, as in my first report. The "1 had no earlier score" is wrong; the 3 none cases are all fallback-dated rows, which the sentence does not mention.
- **Low: "because buybacks grew" (line 140)** is a causal guess I did not test. Say "probably because".
- **Low: two ways of saying the same 0.5 (line 123)**: "0.50% a year (CAGR 0.57%)". One is the difference in mean excess, the other the CAGR gap. Say which is which, or give one.

## 2. Strength of claims

- **Answer paragraph:** fair. It says neither number is distinguishable from zero, gives the minimum detectable effect and the 95% range, and states that a true edge up to about +1.6% a year cannot be ruled out. It calls the Holm result "narrowly" significant, "not under every way of computing the standard error", and "weak evidence". Nothing there is stronger than the table.
- **Holm sentence (line 111):** accurate. "Below 0.05 after Holm as run, at lag 6 and at lag 12, and not with the T/(T-k) correction at lag 4 (0.055). No other test below 0.05 under any of the four": true in my recomputation.
- **Paper comparison (lines 166-167):** uses "consistent with", not "confirms", and notes the non-comparability. Suggestion (Low): add one clause that +1.7 points sits just outside our 95% range (+1.57% a year) and that the subperiod tests could detect only about 2.8% to 3.1% or more a year, so the sentence matches the power wording in the answer. The Low definition difference (0-1 against 0-4) is already stated above in that section.
- **Both benchmarks shown together:** yes, in the results tables, the answer, the two-benchmark section and the v1 comparison. The Middle 2015-25 note is labelled as a benchmark effect, outside the Holm family.
- **Literal-rule paragraph:** "the sign here says little" is fair but should give the literal High row count (620 at first draft; check the final) so the reader sees how thin it is.

## 3. Timing claims

- The issuance revision is stated (lines 129, 149, 234): revised once, after a pass rate was seen, before any return, with the reason (`sstk` includes option-exercise proceeds; pass rate 20.1% against 80.7% in v1; High 1,553 to 620 rows). The numbers match `signal_pass_rates_v2_literal.csv` and my own check.
- Medium (verification): the claim "committed before any v2 return was read (four commits on 2026-11-01 and 2026-11-02)" is not something I can check, because I do not run git. File times cannot show the order: `config.py` was last saved at 17:42 on 2026-11-02, after `portfolio_returns_v2.csv` (17:25) and `scores_checks_v2.md` (17:32), so it was saved after the returns existed (the visible edits are `HEADLINE_SPEC` and the "now the headline" comments, but I cannot see a diff), and the pre-return report was regenerated after the returns. Ask the builder to show that `SPEC_V2` and the `spec_v2` hold-flat entry in `config.py` are identical to the committed version except those labelled additions, and the commit timestamps against the first v2 return. Commit dates are set by the committer, so say they are the author's record.
- The Maxim and General Growth hold-flat rule was added to `config.py` after the pre-return report (that report still shows Maxim as "not approved") and before the portfolio script ran. The write-up says "fixed before any v2 return", which is consistent, but it should be listed with the issuance revision as a change made between the pre-return report and the first return.
- Low: the clarification that an older year is used when the newest fails the date test was settled after I compared dropped rows' v1 returns (my `audit_40`). No v2 return was read, so "before any v2 return" is true, but the write-up could say that some v1 returns were seen by auditors before the spec was final.
- Fair statement kept: v2 was specified after v1's results were known; a re-specification, not a blind test.

## 4. Wording in carried blocks

- "As recalled": absent from the new write-up and README (searched).
- The universe and who-is-in/out blocks are labelled "carried unchanged from the v1 write-up"; the restatement limit and the exclusion paragraph are updated for v2. No contradiction with v2 found (378-417 names, 83.6% overlap, 727 removals all match).
- Medium: the "Runs after the v1 write-up" section is labelled as v1-specification runs, but its tables use a column headed "Headline" holding 10.91% and 11.35%, while the headline is now 10.75%. The intro line says "Headline means the v1 headline", but the tables and bullets ("the headline result holds", "t of -4.10") are easy to misread. Rename the columns "v1 headline" and the bullets "v1 headline".
- Line 235 says "the coordinator's record". That is an internal role name; say "the project lead's record" or describe it.

## 5. README

- Run order matches the scripts: `12a`, `12c`, `12b` (literal first so the net report can quote the literal pass rate; I confirmed `12b` reads `fscores_v2_literal.parquet` only if it exists), then `13`, `14`, `16`, `15`, `17`. `17` reads the literal outputs and `archive_v1/writeup_v1.md`, so it must come last. `12a` and `12c` do refuse to replace their raw files. `07_evaluate.py` writes `output/checkpoint3_results.md`, as README says.
- Low: "Run from this folder, in numeric order" is followed by a table with `12a`, `12c`, `12b` and then a paragraph that overrides it; say "in the order below".
- Low: the "Where outputs go" table has two rows for `output/tables/`: one says "v1 tables, unchanged; use `output/spec_v2/` for the headline" and the next still says "Headline tables, robustness comparison and charts". Remove the second claim.
- Low: the closing "A rerun ... reproduced the same data files, tables and charts" was tested for the v1 pipeline only. It has not been shown for scripts 12 to 17, so say so.
- Answer paragraph in the README matches the write-up's numbers.

## Too good or too bad?

Nothing. The result is a null with one borderline later-period shortfall, both described as such.
