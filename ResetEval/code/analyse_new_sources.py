"""Stage 1 on the added independent real sources (round 1: gas, occupancy, room, bank, kdd, logs 2026-10-06 23:09;
round 2: eeg, news, home, wall, chest, logs 2026-10-06 23:25) and the source-clustered tests together with the 9 earlier
real sources. Same quantities as analyse_stage1.py (accuracy difference to `none`, per-reset effect) and cluster_tests.py
(Wilcoxon over source means, 95% source bootstrap, Holm over the 8 detectors).
Input ../results/tabpfn_M1000/, ../results/stage1_summary.csv. Output ../results/new_sources<rounds>_summary.csv,
../results/new_sources<rounds>_cluster_tests.csv, printed tables.
Usage: python analyse_new_sources.py [round ...]   (e.g. 1, 2, or 1 2)"""
import os

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, POLS, RES, load
from cluster_tests import holm, source, tests

ROUNDS = {1: ["gas", "occupancy", "room", "bank", "kdd"], 2: ["eeg", "news", "home", "wall", "chest"]}


def main(rounds):
    NEW = [s for r in rounds for s in ROUNDS[r]]
    tag = "_".join(map(str, rounds))
    rows, rr = [], []
    for s in NEW:
        a0, _, _ = load(s, "none")
        for p in POLS:
            a, l, r = load(s, p)
            rows.append(dict(group="new", stream=s, pol=p, acc=100 * np.nanmean(a), ll=np.nanmean(l), resets=len(r),
                             d_acc=100 * (np.nanmean(a) - np.nanmean(a0))))
            if p in DETS:
                for i, t in enumerate(r):
                    end = min(t + 10, r[i + 1] if i + 1 < len(r) else len(a), len(a))
                    rr.append(dict(stream=s, det=p, gain=100 * np.nansum(a[t:end] - a0[t:end])))
    N = pd.DataFrame(rows); N.to_csv(f"{RES}/new_sources{tag}_summary.csv", index=False)
    R = pd.DataFrame(rr)
    pd.set_option("display.width", 200, "display.max_rows", 200)

    print("== new sources: accuracy of none (%), difference to none (points) per stream")
    print("none acc:", N[N.pol == "none"].set_index("stream").acc.round(2).to_dict())
    print(N[N.pol != "none"].pivot(index="pol", columns="stream", values="d_acc").reindex(POLS[1:])[NEW].round(2).to_string())
    print("\nresets per stream (full reset):")
    print(N[N.pol.isin(DETS)].pivot(index="pol", columns="stream", values="resets").reindex(DETS)[NEW].to_string())
    print(f"\nper-reset effect on new sources: {len(R)} resets, loss {100 * (R.gain < 0).mean():.1f}%, "
          f"win {100 * (R.gain > 0).mean():.1f}%, mean {R.gain.mean():.2f} point-batches")
    print((R.assign(loss=R.gain < 0).groupby("stream").loss.mean() * 100).round(1).reindex(NEW).to_string())

    S = pd.read_csv(f"{RES}/stage1_summary.csv")
    A = pd.concat([S[S.group == "real"], N.assign(group="real")], ignore_index=True)
    A["src"] = A.stream.map(source)
    N["src"] = N.stream.map(source)
    out = []
    for label, df in ((f"new{len(NEW)}", N.assign(group="new")), (f"real{9 + len(NEW)}", A)):
        g = df.group.iloc[0]
        for v in ("", "+half", "+hedge"):
            t = tests(df, g, [d + v for d in DETS])
            t["p_holm"] = holm(t.p); t["set"] = label
            out.append(t)
    T = pd.concat(out, ignore_index=True)
    T.to_csv(f"{RES}/new_sources{tag}_cluster_tests.csv", index=False)
    for label, t in T.groupby("set", sort=False):
        print(f"\n== {label}: source-weighted mean of d (points), 95% source bootstrap, Wilcoxon over sources, Holm over 8")
        print(t.drop(columns=["group", "drop", "set"]).set_index("pol").round(
            {"mean": 2, "median": 2, "ci_lo": 2, "ci_hi": 2, "p": 4, "p_holm": 4}).to_string())


if __name__ == "__main__":
    import sys
    main([int(a) for a in sys.argv[1:]] or [1])
