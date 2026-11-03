"""
v3 H4: hash and timestamp every raw pull. Records SHA-256, size, row count and file modification time for each data/raw file in output/logs/raw_hashes_v3.csv, and compares
with another folder's raw files when given one (used to show two independent pulls are identical).
Usage:  python 24_hash_raw.py                    record this folder's raw hashes
        python 24_hash_raw.py --compare OTHER    also compare against OTHER/data/raw (a second pull)
Exit code 1 if any compared file differs. Read-only on data/raw.
"""
import argparse
import hashlib
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table(raw):
    rows = []
    for p in sorted(raw.glob("*.parquet")):
        rows.append({"file": p.name, "sha256": sha(p), "bytes": p.stat().st_size, "rows": len(pd.read_parquet(p)),
                     "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")})
    return pd.DataFrame(rows)


ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--compare")
a = ap.parse_args()
mine = table(ROOT / "data" / "raw")
mine["recorded_at"] = datetime.now().isoformat(timespec="seconds")
out = ROOT / "output" / "logs"
out.mkdir(parents=True, exist_ok=True)
mine.to_csv(out / "raw_hashes_v3.csv", index=False)
print(mine[["file", "rows", "sha256"]].assign(sha256=lambda d: d.sha256.str[:12]).to_string(index=False))
if a.compare:
    other = table(Path(a.compare) / "data" / "raw")
    m = mine.merge(other, on="file", how="outer", suffixes=("", "_other"), indicator=True)
    m["identical"] = (m.sha256 == m.sha256_other)
    m[["file", "rows", "rows_other", "identical"]].to_csv(out / "raw_hash_compare_v3.csv", index=False)
    print(m[["file", "rows", "rows_other", "identical"]].to_string(index=False))
    sys.exit(0 if m.identical.all() else 1)
