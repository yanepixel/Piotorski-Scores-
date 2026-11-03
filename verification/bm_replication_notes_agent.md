# Book-to-market replication-lite: agent notes

**This is NOT a full replication of Piotroski (2000).** The universe is the 500 largest US non-financial non-utility firms, so it cannot include small value firms, which is where Piotroski found the effect. A real replication needs a broad-universe WRDS pull that the project owner has not authorised. This is the closest test available without new data.

Pre-registration: `output/prereg_v3_bm.md` (written before any return was computed). Script: `30_v3_bm_replication.py`. Output: `output/spec_v3/bm_replication_v3.csv`.

## Definitions
- Sample: included names per formation date, v2 scores under the literal issuance rule, availability = filing date + 3 days (same alignment code as v3).
- Book-to-market = `ceq / (prcc_f * csho)` from `comp_funda.parquet`, same fiscal year as the score (fiscal-year-end price and shares, as in the paper). USD rows only. Non-positive ceq stays ranked (never top quintile). Not-rankable rows are dropped (7,600 of 7,614 scored list rows were rankable).
- Top quintile: >= exact 0.8 quantile among scored rankable names on that date; ties included. High = scores 8-9, Low = 0-4 (config).
- Portfolios: v3 mechanics copied from `22_v3_robustness.py`; benchmark = equal weight of the whole quintile.
- Tests: mean gap x12 and four-factor (Mkt-RF, SMB, HML, MOM) alpha x12, HAC lag floor(4*(T/100)^(2/9)) = 4, t(T-k) p-values, Holm over the two, MDE at 80% power.

## Results (247 months, 21 formation dates, 2005-2025)
| Comparison | Test | Estimate/yr | SE | t | p | Holm p | MDE/yr |
|---|---|---|---|---|---|---|---|
| High - quintile | mean | +2.33% | 3.23% | 0.72 | 0.471 | 0.942 | 9.1% |
| High - quintile | 4-factor alpha | +1.37% | 3.28% | 0.42 | 0.676 | 0.942 | 9.2% |
| High - Low (descriptive) | mean | +0.57% | 4.14% | 0.14 | 0.891 | n/a | 11.7% |
| High - Low (descriptive) | 4-factor alpha | -0.32% | 4.32% | -0.07 | 0.941 | n/a | 12.2% |

CAGRs: High 11.18%, Low 11.63%, quintile 10.38%.

## Thin buckets (rule unchanged)
Names per date: quintile 64-77 (median 74; 0 thin dates). High median 5, range 2-19; **17 of 21 dates have fewer than 10 High names**. Low median 17, range 3-41; 5 of 21 dates below 10. No date had zero High or zero Low names, so no months were dropped. Per-date counts are in the script's printed output.

## Honest limits
- Nothing is significant, and the MDE (about 9% a year for High vs quintile) is several times Piotroski's roughly 1.7 point effect, so the test cannot rule that effect in or out. The result is uninformative, not a refutation.
- High is about 5 names on a typical date: the High portfolio is highly concentrated, driven by a few stocks; estimates are noisy.
- `prcc_f*csho` is one share class only, so multi-class firms get an inflated book-to-market and may enter the quintile spuriously.
- Large caps in the top book-to-market quintile of a 500-name universe are not the paper's small, distressed value firms.
- Four factors used (Carhart) from `ff_factors.parquet`; the definition of "four-factor" was fixed in the prereg, not read from an earlier script.
- No other design was run; nothing was selected from returns.
