"""Stage 3: TabPFN backbone seeds 1 and 2 against seed 0 (logs/EXPERIMENT_LOG.md, 2026-10-07 00:55).
For every stream with all 26 policies in both runs: d = acc(policy) - acc(none) per stream, compared across seeds.
  S1 Pearson r of per-stream d (full resets, 8 detectors pooled) between seed s and seed 0 >= 0.9 (real streams)
  S2 on the same real streams, the source-weighted mean of d for full reset and for +hedge keeps its sign for >= 7/8
     detectors, and the tail statistics T1 (+hedge - full on the worst source >= 10) and T2 hold as for seed 0
Usage: python seed_compare.py 1 [2] -> ../results/stage3_seeds.csv, printed table"""
import os
import sys

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, POLS, REAL, RES, SYN
from cluster_tests import source

NEW = ["gas", "occupancy", "room", "bank", "kdd", "eeg", "news", "home", "wall", "chest"]


def table(tag, streams):
    d = f"{RES}/{tag}_M1000"; rows = []
    for s in streams:
        if not all(os.path.exists(f"{d}/{s}__{p}.npz") for p in POLS):
            continue
        a0 = np.nanmean(np.load(f"{d}/{s}__none.npz")["acc"])
        for p in POLS[1:]:
            rows.append(dict(stream=s, pol=p, d=100 * (np.nanmean(np.load(f"{d}/{s}__{p}.npz")["acc"]) - a0)))
    return pd.DataFrame(rows)


def tail(df):
    df = df.assign(src=df.stream.map(source))
    m = df.groupby(["pol", "src"]).d.mean().unstack()
    return {v or "full": (m.loc[[x + v for x in DETS]].min(1).mean(), m.loc[[x + v for x in DETS]].max(1).mean())
            for v in ("", "+hedge")}, m.mean(1)


def main(seeds):
    out = []
    for grp, streams in (("real", REAL + NEW), ("syn", SYN)):
        base = table("tabpfn", streams)
        for sd in seeds:
            other = table(f"tabpfn_s{sd}", streams)
            if other.empty:
                print(f"seed {sd}, {grp}: no complete stream"); continue
            j = base.merge(other, on=["stream", "pol"], suffixes=("_0", "_s"))
            n = j.stream.nunique()
            full = j[j.pol.isin(DETS)]
            r = np.corrcoef(full.d_0, full.d_s)[0, 1] if len(full) > 2 else np.nan
            print(f"\n== seed {sd} vs seed 0, {grp}: {n}/{len(streams)} streams complete in both; "
                  f"Pearson r of per-stream d (full resets) {r:.3f}; mean |diff| {np.abs(full.d_0 - full.d_s).mean():.2f} points")
            if grp == "real":
                (t0, m0), (ts, ms) = tail(j.rename(columns={"d_0": "d"})), tail(j.rename(columns={"d_s": "d"}))
                same = {v: sum(np.sign(m0[x + v]) == np.sign(ms[x + v]) for x in DETS) for v in ("", "+hedge")}
                t1 = {k: t["+hedge"][0] - t["full"][0] for k, t in (("seed0", t0), (f"seed{sd}", ts))}
                t2 = {k: t["+hedge"][1] >= 0.5 * t["full"][1] for k, t in (("seed0", t0), (f"seed{sd}", ts))}
                print("source-weighted mean d, seed 0 vs seed", sd, ":")
                print(pd.DataFrame({"seed0": m0, f"seed{sd}": ms}).reindex([x + v for v in ("", "+half", "+hedge") for x in DETS]).round(2).to_string())
                print(f"S1 r >= 0.9 -> {'holds' if r >= 0.9 else 'fails'}; S2 sign kept: full {same['']}/8, +hedge {same['+hedge']}/8; "
                      f"T1 (+hedge - full, worst source) {({k: round(v, 2) for k, v in t1.items()})}; T2 {t2} -> "
                      f"{'holds' if min(same.values()) >= 7 and all(v >= 10 for v in t1.values()) and all(t2.values()) else 'fails'}")
            out.append(j.assign(group=grp, seed=sd))
    if out:
        pd.concat(out).to_csv(f"{RES}/stage3_seeds.csv", index=False)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [1])
