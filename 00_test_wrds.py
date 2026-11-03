"""
Step 0 check: confirm WRDS login works and that your account can read every table the backtest needs.
Run once. Each table prints OK or NO ACCESS. crsp.msp500list is expected to print NO ACCESS (S&P 500 history is not available to this account; the project uses a market-cap proxy instead).
"""
import os
from pathlib import Path

import wrds

TABLES = {
    "Compustat annual fundamentals":   "comp.funda",
    "Compustat 10-K filing dates":     "comp.co_filedate",
    "Compustat historical GICS":       "comp.co_hgic",
    "CRSP S&P 500 membership":         "crsp.msp500list",
    "CRSP monthly returns (new CIZ)":  "crsp.msf_v2",
    "CRSP monthly returns (legacy)":   "crsp.msf",
    "CRSP delisting returns (legacy)": "crsp.msedelist",
    "CRSP-Compustat link":             "crsp.ccmxpf_lnkhist",
    "Fama-French 5 factors":           "ff.fivefactors_monthly",
    "Fama-French 3 + momentum":        "ff.factors_monthly",
    # Tables used by later scripts (added so step 0 covers the whole pipeline)
    "CRSP stock names":                "crsp.msenames",             # 01
    "Compustat S&P index members":     "comp.idxcst_his",           # 01 (current members only)
    "Compustat company names":         "comp.company",              # 03
    "Compustat quarterly":             "comp.fundq",                # 08
    "Compustat monthly security":      "comp.secm",                 # 02c
    "Compustat security":              "comp.security",             # 02c
}


def wrds_username():
    """PGUSER if set, else the username field of the saved pgpass entry. Nothing is printed or stored."""
    if os.environ.get("PGUSER"):
        return os.environ["PGUSER"]
    for path in (Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf", Path.home() / ".pgpass"):
        if path.exists():
            for line in path.read_text().splitlines():
                if line.startswith("wrds-pgdata"):
                    return line.split(":")[3]
    raise RuntimeError("No WRDS username: set PGUSER or create pgpass.conf (see README.md)")


db = wrds.Connection(wrds_username=wrds_username())

for label, table in TABLES.items():
    try:
        db.raw_sql(f"select * from {table} limit 1")
        print(f"OK         {label:35s} {table}")
    except Exception as e:
        print(f"NO ACCESS  {label:35s} {table}  ->  {str(e).splitlines()[0][:80]}")

db.close()
