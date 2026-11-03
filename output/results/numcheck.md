# Independent number check

## 1. F-scores, 400 random scored firm-years (seed 20261102), literal rule

Independent implementation agrees on 400, disagrees on 0, could not compute independently on 0 (missing inputs or sales <= 0 in my minimal version).

## 2. High gross monthly return, raw CRSP vs pipeline

247 months; 247 agree within 1e-6; max abs difference 0.0000%; months differing by more than 10 bps: 0. This version redistributes exited names pro rata, as the pipeline documents, and holds the approved flat cases at 0%; any remaining difference is unexplained.

## 2. Low gross monthly return, raw CRSP vs pipeline

247 months; 247 agree within 1e-6; max abs difference 0.0000%; months differing by more than 10 bps: 0. This version redistributes exited names pro rata, as the pipeline documents, and holds the approved flat cases at 0%; any remaining difference is unexplained.

## 3. Printed numbers vs tables: not checked

The earlier lenient token match could not fail and was removed. Tables in writeup.md are generated from the CSVs by 22_writeup.py; figures typed by hand in README.md are not machine-checked.

## What this does and does not check

It checks F-score logic and gross High/Low returns independently of the pipeline's own code, only. It does not check printed numbers against tables, or every table row (Middle, RSP, SPY, tracking error, information ratio, loadings and subperiod CAGRs are still checked only by 11_numcheck_arithmetic.py against the same file)
