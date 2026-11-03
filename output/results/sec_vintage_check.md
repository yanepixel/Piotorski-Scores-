# SEC vintage check, FY2015-2024 (aggregates only)

Sample: 250 random scored firm-years (seed 20261103). No CIK on file: 1; no SEC facts or no original 10-K found: 1; not scoreable from the mapped SEC tags (a needed input missing in either version): 129. **Usable: 119.** Scores use the paper's literal issuance rule and the same signal definitions as the backtest, but SEC XBRL tags, so levels differ from Compustat; the comparison PIT vs LATEST uses the same tags both ways and so isolates restatement.

## Restatement effect: PIT (as filed by the original 10-K date) vs LATEST (current vintage)

- Score identical: 109 of 119 (91.6%).
- Mean absolute score change: 0.109; max 3.
- At least one signal flips: 11 of 119 (9.2%).
- Bucket (High/Middle/Low) changes: 6 of 119 (5.0%).
- PIT High that stay High in LATEST: 26 of 26 (100.0%).
- LATEST High that were not High in PIT: 0 of 26. Of the 6 bucket changes, 6 involve Middle and 0 jump between High and Low.
- Share of firm-years where the input was revised (any of the three years): ib 15.1%, oancf 17.6%, at 10.1%, act 10.1%, lct 7.6%, dltt 4.2%, sale 14.3%, cogs 22.7%, sstk 2.5%.

## Mapping check (informational): SEC-LATEST score vs the Compustat score in the backtest

- Identical: 43 of 119 (36.1%); within one point: 90.8%. Differences here come from tag choices and definitions (for example income before extraordinary items, current-portion debt), not restatement.

## Limits

A sample, not the full table; firms whose inputs the simple tag map cannot find are excluded, which tilts the sample toward standard filers. A 10-K filed in the SEC feed only from 2009. Sample uses the project's current-vintage scorable firm-years, so firms excluded for missing data are not represented. A restated value that appears only in a later 10-K comparative column is treated as filed on that later date, which is the point-in-time-correct reading.
