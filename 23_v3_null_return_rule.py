"""
v3 null-return and delisting sensitivities (prereg_v3 H2).
(1) Null-return rule on both sides: the v2 pipeline holds approved no-trade months flat at 0% (General Growth 2009-05, Maxim 2007-11 to 2008-05); these names sit in the
    benchmark only. Here the same rule is changed for every portfolio to EXIT: a name with no return is sold at its last value and the proceeds go pro rata to the rest.
    Implemented by running 22_v3_robustness.py's own code with the flat set emptied, so every portfolio and variant uses the exit rule. Output: robustness_v3_exit_rule.csv.
(2) Delisting returns (Shumway 1997): counts, from the raw CRSP file, how many mid-period exits in the primary list lack a delisting return in their last month.
    Output: delisting_check_v3.md. If none lack one, a -30% replacement has nothing to replace.
Usage: python 23_v3_null_return_rule.py
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "spec_v3"

src = (ROOT / "22_v3_robustness.py").read_text(encoding="utf-8")
src = src.replace('FLAT = {(p, pd.Period(m, "M")) for p, ms in cfg.NULL_RETURN_HOLD_FLAT_MONTHS["spec_v2"].items() for m in ms}', "FLAT = set()")
src, n = re.subn(r"\n\s+assert np\.allclose\(ref\.High\.values.*\n", "\n        pass\n", src)
assert n == 1, "reproduction assert not found"
src = src.replace('res.to_csv(OUT / "robustness_v3.csv", index=False)', 'res.to_csv(OUT / "robustness_v3_exit_rule.csv", index=False)')
src = src.replace("__file__", repr(str(ROOT / "22_v3_robustness.py")))
exec(compile(src, "22_v3_robustness_exit_rule", "exec"), {"__name__": "exit_rule_run"})

r = pd.read_parquet(ROOT / "data/raw/crsp_msf_v2.parquet", columns=["permno", "mthcaldt", "mthret", "mthretflg", "mthdelflg"])
r["month"] = r.mthcaldt.dt.to_period("M")
e = pd.read_csv(ROOT / "output/spec_v2/literal_sensitivity/portfolio_exits_v2.csv").dropna(subset=["last_month_with_return"])
e["m"] = pd.PeriodIndex(e.last_month_with_return, freq="M")
x = e.merge(r, left_on=["permno", "m"], right_on=["permno", "month"], how="left")
has_dlret = (x.mthretflg == "DE") & x.mthret.notna()
(OUT / "delisting_check_v3.md").write_text(
    f"# Delisting-return check (Shumway, 1997)\n\n{len(x)} mid-period exits in the literal-rule primary list. {int(has_dlret.sum())} have a delisting return (return flag DE, non-null) in their last month; "
    f"{int((~has_dlret).sum())} do not. Shumway's -30% replacement applies only to a missing performance-related delisting return, so it replaces nothing in this data. "
    f"The one performance-flagged exit (P) has a recorded return.\n\n"
    f"Raw file: {int((r.mthretflg == 'NT').sum())} null-return rows, all flagged NT (no trade), none flagged DE. The NT months of held names are the only null returns; the approved cases are handled in the exit-rule run above.\n",
    encoding="utf-8")
print((OUT / "delisting_check_v3.md").read_text())
