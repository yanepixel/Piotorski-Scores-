"""
Unit tests for the nine signals on one synthetic firm with hand-worked numbers (prereg_main section I).
Run from the project folder:  python -m pytest tests -q   (or: python tests/test_signals.py)

Firm A, scored year FY2003 (hand-worked):
  FY2001 at 100 ib 5 dltt 20 act 40 lct 20 sale 100 cogs 70
  FY2002 at 110 ib 8 dltt 20 act 44 lct 20 sale 120 cogs 80
  FY2003 at 120 ib 12 oancf 15 dltt 18 act 60 lct 24 sale 150 cogs 90 sstk 0 prstkc 0
  ROA 12/110 > 0; CFO 15/110 > 0; DROA 12/110 - 8/100 = +0.029; ACCRUAL CFO .136 > ROA .109;
  LEVER 18/115 = .157 < 20/105 = .190; LIQUID 60/24 = 2.5 > 44/20 = 2.2; EQ_OFFER sstk 0;
  MARGIN 60/150 = .400 > 40/120 = .333; TURN 150/110 = 1.364 > 120/100 = 1.2.  Every signal passes: score 9.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(src_path, name, mutate=None):
    text = Path(src_path).read_text(encoding="utf-8")
    if mutate:
        old, new = mutate
        assert old in text, f"planted-bug target not found: {old}"
        text = text.replace(old, new)
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(src_path)
    exec(compile(text, str(src_path), "exec"), mod.__dict__)
    return mod


def firm(**over):
    rows = [
        dict(fyear=2011, at=100.0, ib=5.0, ni=5.0, oancf=6.0, dltt=20.0, act=40.0, lct=20.0, sale=100.0, cogs=70.0, sstk=0.0, prstkc=0.0),
        dict(fyear=2012, at=110.0, ib=8.0, ni=8.0, oancf=9.0, dltt=20.0, act=44.0, lct=20.0, sale=120.0, cogs=80.0, sstk=0.0, prstkc=0.0),
        dict(fyear=2013, at=120.0, ib=12.0, ni=12.0, oancf=15.0, dltt=18.0, act=60.0, lct=24.0, sale=150.0, cogs=90.0, sstk=0.0, prstkc=0.0),
    ]
    for k, v in over.items():
        rows[-1][k] = v
    d = pd.DataFrame(rows)
    d["gvkey"] = "A"
    d["stub_flag"] = False
    d["csho"] = 10.0
    d["ajex"] = 1.0
    d["adj_shares"] = 10.0
    d["filing_date"] = pd.to_datetime(d.fyear.astype(str) + "-03-15") + pd.DateOffset(years=1)
    return d


def scores(mod, df, rule="literal"):
    mod.RULE = rule
    out = mod.compute_scores(df)
    return out[out.fyear == 2013].iloc[0]


def Scores():
    return load(ROOT / "05_scores.py", "scores")


def test_all_pass_scores_nine():
    r = scores(Scores(), firm())
    assert r.F_SCORE == 9
    assert abs(r.ROA - 12 / 110) < 1e-12 and abs(r.DROA - (12 / 110 - 0.08)) < 1e-12
    assert abs(r.LEVER - 18 / 115) < 1e-12 and abs(r.LEVER_lag1 - 20 / 105) < 1e-12


def test_each_signal_flips_alone():
    m = Scores()
    cases = {"F_ROA": dict(ib=-1.0, oancf=-2.0), "F_CFO": dict(oancf=-1.0), "F_DLEVER": dict(dltt=25.0), "F_DLIQUID": dict(act=40.0),
             "F_DMARGIN": dict(cogs=110.0), "F_DTURN": dict(sale=100.0, cogs=60.0), "F_EQ_OFFER": dict(sstk=5.0)}
    for sig, over in cases.items():
        r = scores(m, firm(**over))
        assert r[sig] == 0, f"{sig} should fail for {over}"
    # ACCRUAL fails when CFO <= ROA: oancf 10 gives CFO .091 < ROA .109
    assert scores(m, firm(oancf=10.0)).F_ACCRUAL == 0
    # DROA fails when ROA does not rise: ib 8 gives ROA .073 < .08
    assert scores(m, firm(ib=8.0)).F_DROA == 0


def test_issuance_rules():
    m = Scores()
    assert scores(m, firm(sstk=5.0, prstkc=10.0), "literal").F_EQ_OFFER == 0   # paper: any issuance fails
    assert scores(m, firm(sstk=5.0, prstkc=10.0), "net").F_EQ_OFFER == 1       # net sensitivity: buyback exceeds issue
    assert scores(m, firm(sstk=np.nan), "literal").F_EQ_OFFER == 1             # missing sstk read as none
    assert scores(m, firm(sstk=-3.0), "literal").F_EQ_OFFER == 1              # paper: nothing issued, so a negative sstk passes


def test_missing_prstkc_is_unknown_under_net_rule():
    # prereg_main D: a missing prstkc must be UNKNOWN under the net rule, not zero.
    r = scores(Scores(), firm(prstkc=np.nan), "net")
    assert pd.isna(r.F_EQ_OFFER), "net rule still treats missing prstkc as 0 (prereg_main D)"


def test_null_input_gives_null_signal_and_no_score():
    r = scores(Scores(), firm(oancf=np.nan))
    assert pd.isna(r.F_CFO) and pd.isna(r.F_ACCRUAL) and pd.isna(r.F_SCORE)


def test_fiscal_year_gap_blocks_comparisons():
    d = firm()
    d = d[d.fyear != 2012]                      # FY2002 missing: no prior-year pair
    r = scores(Scores(), d)
    assert pd.isna(r.F_DROA) and pd.isna(r.F_DLEVER) and pd.isna(r.F_SCORE)


def test_no_filing_date_means_unscorable():
    d = firm()
    d.loc[d.fyear == 2013, "filing_date"] = pd.NaT
    assert pd.isna(scores(Scores(), d).F_SCORE)


def test_availability_buffer():
    r = scores(Scores(), firm())
    assert r.avail_date_buffered == r.filing_date + pd.Timedelta(days=3)


# ---- planted bugs: the same hand-worked checks must FAIL on a deliberately broken copy ----
def _detects(mutate, check):
    mod = load(ROOT / "05_scores.py", "scores_bug", mutate)
    try:
        check(mod)
    except AssertionError:
        return True
    return False


def test_planted_bugs_are_caught():
    assert _detects(("d.DLEVER < 0", "d.DLEVER > 0"), lambda m: [scores(m, firm()).F_DLEVER == 1 or (_ for _ in ()).throw(AssertionError())])
    assert _detects(("d.ROA = d.ib / d.at_lag1".replace("d.ROA", 'd["ROA"]'), 'd["ROA"] = d.ib / d["at"]'), lambda m: _eq(scores(m, firm()).ROA, 12 / 110))
    assert _detects(("d.CFO > d.ROA", "d.CFO < d.ROA"), lambda m: _eq(scores(m, firm()).F_ACCRUAL, 1))
    assert _detects(('d["F_DLIQUID"] = signal(d.DLIQUID > 0, d.DLIQUID)', 'd["F_DLIQUID"] = signal(d.DLIQUID < 0, d.DLIQUID)'), lambda m: _eq(scores(m, firm()).F_DLIQUID, 1))
    assert _detects(("(d.net_issue <= 0)", "(d.net_issue < 0)"), lambda m: _eq(scores(m, firm(), "net").F_EQ_OFFER, 1))


def _eq(a, b):
    assert abs(float(a) - float(b)) < 1e-12


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, "-", e)
    sys.exit(1 if fails else 0)

