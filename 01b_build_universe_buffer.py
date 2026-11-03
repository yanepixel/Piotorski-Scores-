"""
Stage 01b: the buffered universe (entry at rank <= 450, stay until rank > 550, first list the top 500) used by the universe_buffer robustness variant in 14_robustness_extra.py.
Rebuilds with the headline's steps from 01_build_universe.py, changing only who is on each list, and stops unless its plain path reproduces data/clean/universe.parquet exactly.
Output: data/clean/universe_buffer.parquet. Write-once: refuses to replace the file unless --overwrite is passed. Reads WRDS (read-only queries).
Usage:  python 01b_build_universe_buffer.py
"""
import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import wrds

import config as cfg

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT / "data" / "clean"
OUT_FILE = CLEAN / "universe_buffer.parquet"


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


universe_mod = load("01_build_universe.py", "universe_mod")


def build_buffer_universe(db, buffer_rule):
    """Rebuild with the headline's steps, changing only who is on each list."""
    m = universe_mod.pull_formation_month(db)
    priced = m[universe_mod.eligible_mask(m) & m.seccap.notna() & ~m.stopped_trading]
    company = priced.groupby(["formation_date", "permco"], as_index=False).seccap.sum().rename(columns={"seccap": "mktcap"})
    company = company.sort_values(["formation_date", "mktcap", "permco"], ascending=[True, False, True])
    company["rank"] = company.groupby("formation_date").cumcount() + 1
    held = (priced.sort_values(["formation_date", "permco", "seccap", "permno"], ascending=[True, True, False, True]).drop_duplicates(["formation_date", "permco"]).drop(columns="seccap"))

    def finish(members):
        u = members.merge(held, on=["formation_date", "permco"], how="left", validate="1:1")
        u, _ = universe_mod.attach_gvkey(u, db)
        u, _, _ = universe_mod.apply_sibling_links(u, m, db)
        u, _ = universe_mod.attach_sector(u, db)
        return universe_mod.set_included(u)

    plain = finish(company[company["rank"] <= cfg.UNIVERSE_SIZE])
    current, rows = set(), []
    if cfg.BUFFER_FIRST_LIST != "top_500":
        raise ValueError(cfg.BUFFER_FIRST_LIST)
    for i, (d, g) in enumerate(company.groupby("formation_date")):
        g = g.set_index("permco")
        if i == 0:
            chosen = set(g.index[g["rank"] <= cfg.UNIVERSE_SIZE])
        else:
            chosen = set(g.index[g["rank"] <= buffer_rule["entry_rank"]]) | {p for p in current if p in g.index and g["rank"][p] <= buffer_rule["exit_rank"]}
        rows.append({"formation_date": d.date(), "list_size": len(chosen), "entered": len(chosen - current), "left": len(current - chosen), "rank_above_500_kept": int((g.loc[list(chosen), "rank"] > cfg.UNIVERSE_SIZE).sum())})
        current = chosen
        if i == 0:
            frames = []
        frames.append(g.loc[list(chosen)].reset_index())
    members = pd.concat(frames, ignore_index=True)
    return plain, finish(members), pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true")
    if OUT_FILE.exists() and not ap.parse_args().overwrite:
        sys.exit(f"REFUSED: {OUT_FILE.name} exists and is write-once. Pass --overwrite to replace it.")
    universe = pd.read_parquet(CLEAN / "universe.parquet")
    db = wrds.Connection(wrds_username=universe_mod.wrds_username())
    plain, buffered, size = build_buffer_universe(db, cfg.ROBUSTNESS["universe_buffer"]["UNIVERSE_BUFFER"])
    db.close()
    key = ["formation_date", "permno"]
    u_key = ["formation_date", "permno", "permco", "gvkey", "rank", "gsector", "included"]
    pl = plain[u_key].sort_values(key).reset_index(drop=True)
    ub = universe[u_key].sort_values(key).reset_index(drop=True)
    if not (len(pl) == len(ub) and (pl.astype(object).astype(str) == ub.astype(object).astype(str)).all().all()):
        sys.exit("STOP: the buffer's rebuild path does not reproduce the headline universe")
    print("headline universe reproduced through the buffer path", flush=True)
    cols_u = ["formation_date", "permno", "permco", "gvkey", "mktcap", "rank", "gsector", "included"]
    buffered[cols_u].to_parquet(OUT_FILE, index=False)
    print(f"buffered universe: {len(buffered)} rows, list size {size.list_size.min()}-{size.list_size.max()} before exclusions")


if __name__ == "__main__":
    main()
