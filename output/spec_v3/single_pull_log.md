# Single-vintage pull of Compustat annual inputs

One query, one stamp 2026-11-03T04:50:08+00:00 (UTC). `data/raw/comp_funda_single.parquet`, 20796 rows, SHA-256 `4DA9E8A72D102C24FF01631ED72AC0D2A7396765A4B01921235C9B9EF58D6EE2`.

- vs `comp_funda.parquet`: rows 20796; key mismatches 0.
  - fyr: 0 rows differ
  - ni: 0 rows differ
  - at: 0 rows differ
  - oancf: 0 rows differ
  - dltt: 0 rows differ
  - act: 0 rows differ
  - lct: 0 rows differ
  - sale: 0 rows differ
  - cogs: 0 rows differ
  - csho: 0 rows differ
  - ajex: 0 rows differ
  - sstk: 0 rows differ
  - ceq: 0 rows differ
  - txditc: 0 rows differ
  - pstk: 0 rows differ
  - prcc_f: 0 rows differ
  - curcd: 0 rows differ
- vs `comp_funda_ib.parquet`: rows 20796; key mismatches 0.
  - ib: 0 rows differ
- vs `comp_funda_prstkc.parquet`: rows 20796; key mismatches 0.
  - prstkc: 0 rows differ
- vs `comp_funda_reit_fields.parquet`: rows 20796; key mismatches 0.
  - che: 0 rows differ
  - lt: 0 rows differ

Total differing cells against the separate pulls: 0. A non-zero count would mean the earlier separate pulls came from different vintages.