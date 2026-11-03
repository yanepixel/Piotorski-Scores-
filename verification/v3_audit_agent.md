# v3 audit (read-only agent)

BLOCKER
1. 19_v3_numcheck.py:100-112 (section 3) cannot fail. Replaying its matching logic on 500 random fake 2-decimal numbers against the 34,393 distinct CSV values gave 100% "matched". "0 unmatched" for README (50) and writeup (439) is therefore meaningless; prereg F required exact cell matches. 3.81, 358 and 2.13% are not tied to a cell. Fix: match each printed number to the specific CSV cell (generate the text from keyed cells, or assert key-by-key), and report the check as not done until then.

RISK
2. 12b_spec_v2_scores.py:115 literal rule is `~(sstk.fillna(0) != 0)`, so negative sstk FAILS. prereg D says "sstk not positive" (negative passes). 40 scored firm-years have sstk<0 (all fail now; none currently in High). 19_v3_numcheck.py:63 and tests/test_signals.py copy the same `== 0` convention, so the "400/400 agree" cannot detect it. Fix: `sstk.fillna(0) <= 0`, add a negative-sstk unit test, rerun.
3. 18_v3_inference.py:121-122 trial count: `max(250,0)+n_v3` hard-codes 250. n_prior and count_trials() are computed/defined but never used. My re-count with the script's own regex gives 163 t columns outside archive_v2/spec_v3 (96 of them from the two tests_v2.csv). 250 is the user's figure and cannot be reproduced. n_v3=108 = 6 tests x 2 rules x 3 periods x 3 lags (same test at 3 lags is not 3 independent trials; the 8 robustness t's from script 22 are not included). 3.81 = norm.ppf(1-0.025/358) is correct arithmetic for N=358. Defensible only as "about 360, Bonferroni upper bound"; the writeup/README say "have been computed" as a count. Fix: reword as approximate, or count rows from logged files and state the rule.
4. README.md "Still open" (end of answer section) is stale: says robustness reruns, transaction-cost sensitivities, missing-signal sensitivity are open; scripts 20 and 22 did them. writeup.md (21_v3_writeup.py "Not done" bullet) also lists "missing-signal firm-years kept" as not done while its own robustness table has it. Fix both.
5. README.md answer paragraph: "MDE about 2.1% to 6.2%" and the interval "-1.42% to +1.57%" are the NET (sensitivity) numbers, placed beside the literal primary. Literal MDE is 3.9% to 5.4%; literal 95% interval for (a) is about -1.5% to +3.9% (1.19% +/- 1.97*1.39%), so "contains Piotroski's 1.7" is true but the upper bound is much wider than stated. Fix: quote literal figures for the primary.
6. 22_v3_robustness.py:127-129 avail_datadate_N uses datadate+N even when filing came later (look-ahead for late filers). Measured: only 0.08% of scored firm-years file after 150 days (max lag 275 days), so negligible, but label says "ignore filing date" and prereg wanted a lag rule. Fix: max(filing+3, datadate+N).

NOTE
7. 22 avail_signals: scaled score is non-integer (7/8 -> 7.875 < 8 so not High; 8/9, 9/9, 7/7, 8/8 are). Threshold mixes denominators; label this. Needs n>=7 signals.
8. high_7plus (22:155-157) logic is correct for High/Benchmark (bucket Low retained, unused). High_names_total 2187 vs 620 shows it is a different set. cap_weighted uses formation mktcap, drift handled by run(); cost on weight change vs drifted prior; fine.
9. 19 part 2 draws membership from the same formation parquet and the same flat-month config, so it checks return arithmetic, not membership/availability. Gross only; net and benchmarks not recomputed.
10. Net rule still treats missing prstkc as 0 (prereg D); disclosed in writeup and a failing test (not xfail-marked; pytest is not installed so I could not run the suite).
11. 18 compares total months T for lag formula: floor(4*(247/100)^(2/9)) = 4, correct; t uses T-k df; HAC use_correction False consistently; p from t(df). Holm correct (step-down, monotone, clipped at 1), applied per rule over 3 tests.

CLEAN
- Prereg A.2 family/Holm, literal primary, both benchmarks side by side, post-hoc labels, lag renaming/4-6-12, headline arithmetic + CAGR + Sharpe: all implemented as stated. 6 primary rows recomputed from CSV: all Holm p = 1.0 follows (min p 0.39).
- 20_v3_cost_sensitivity: linear rescale is exact. Net = (1+g)(1-c) with c = first-month two-way turnover x bps + reinvestment x bps; weights and exits do not depend on cost, so gross - net = (1+g)c is linear in bps. 10 bp row equals headline CAGRs exactly (11.7439%, 10.7890%).
- 22 headline reproduces v2 literal portfolio by assertion; identical-row guard present.
- README/writeup table numbers (11.74/10.79/+0.95/+1.19, 0.86, 2.13%, 2.31%, 6.21%) agree with the CSVs.

NOT CHECKED
- Could not run tests (no pytest). Did not rerun 18-22 (would write to repo). No WRDS, so restatement/point-in-time and independent raw pulls untouched. Original list items B/E/F/G/H partially undone as writeup itself states (H2, H4-H7, H9 partly, E beyond FY2014, G only for 8 variants, not 08-11).
