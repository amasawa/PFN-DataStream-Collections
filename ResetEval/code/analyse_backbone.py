"""Stage 2 verdicts for one backbone (logs/EXPERIMENT_LOG.md, 2026-10-06 23:35 and 23:38): H1'-H4' and the tail tests
T1, T2 over all 39 real streams (19 sources) and 42 synthetic streams (7 generator families).
Source-weighted means as in cluster_tests.py. Per-reset effect as in analyse_stage1.py.
  H1' >= 6/8 detectors: full reset below none (real, source-weighted)
  H2' >= 6/8 detectors: full reset above none (synthetic, family-weighted)
  H3' real: > 50% of non-zero single resets are net losses; synthetic: > 50% of single resets are net wins
  H4' +hedge on real >= -0.2 and on synthetic >= half of the full-reset gain (per detector and on the detector average)
  T1  detector-averaged worst real source: +hedge at least 10 points better than full reset
  T2  detector-averaged best real source: +hedge at least half of full reset's
Usage: python analyse_backbone.py tabicl|tabpfn|tabpfn_s<s>|tabpfn_M<M> -> ../results/stage2_<backbone>_summary.csv, _tests.csv, printed verdicts"""
import os
import sys

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, POLS, REAL, RES, SYN
from cluster_tests import holm, source, tests
from reset_effects import effects

NEW = ["gas", "occupancy", "room", "bank", "kdd", "eeg", "news", "home", "wall", "chest"]


def main(bb):
    d = f"{RES}/{bb}" if "_M" in bb else f"{RES}/{bb}_M1000"     # e.g. tabpfn, tabpfn_s1, tabpfn_M500
    rows, rr = [], []
    for grp, streams in (("real", REAL + NEW), ("syn", SYN)):
        done = [s for s in streams if all(os.path.exists(f"{d}/{s}__{p}.npz") for p in POLS)]
        if len(done) < len(streams):                                  # partial run (e.g. stopped by the 05:00 restart)
            print(f"PARTIAL {grp}: {len(done)}/{len(streams)} streams complete; missing: {sorted(set(streams) - set(done))}")
        for s in done:
            a0 = np.load(f"{d}/{s}__none.npz")["acc"]
            for p in POLS:
                z = np.load(f"{d}/{s}__{p}.npz"); a, r = z["acc"], z["resets"]
                rows.append(dict(group=grp, stream=s, pol=p, acc=100 * np.nanmean(a), resets=len(r),
                                 d_acc=100 * (np.nanmean(a) - np.nanmean(a0))))
                if p in DETS:
                    for gain in effects(a, a0, r, int(z['B']), int(z['M']) if 'M' in z else None):
                        rr.append(dict(group=grp, stream=s, det=p, gain=gain))
    S = pd.DataFrame(rows); S["src"] = S.stream.map(source); R = pd.DataFrame(rr)
    S.to_csv(f"{RES}/stage2_{bb}_summary.csv", index=False)
    out = []
    groups = [g for g in ("real", "syn") if (S.group == g).any()]
    for g in groups:
        for v in ("", "+half", "+hedge"):
            t = tests(S, g, [x + v for x in DETS]); t["p_holm"] = holm(t.p); out.append(t)
    T = pd.concat(out, ignore_index=True); T.to_csv(f"{RES}/stage2_{bb}_tests.csv", index=False)
    pd.set_option("display.width", 200, "display.max_rows", 200)
    for g, t in T.groupby("group", sort=False):
        print(f"\n== {bb}, {g}: source-weighted mean of d (points), 95% source bootstrap, Wilcoxon over sources, Holm over 8")
        print(t.drop(columns=["group", "drop"]).set_index("pol").round(
            {"mean": 2, "median": 2, "ci_lo": 2, "ci_hi": 2, "p": 4, "p_holm": 4}).to_string())
    m = T.set_index(["group", "pol"])["mean"]
    if "syn" not in groups:                                           # no complete synthetic stream yet
        m = pd.concat([m, pd.Series(np.nan, index=pd.MultiIndex.from_product([["syn"], POLS[1:]]))])
        print("no complete synthetic stream: H2', H3' (synthetic part) and H4' (synthetic part) cannot be judged")
    h1 = sum(m[("real", x)] < 0 for x in DETS); h2 = sum(m[("syn", x)] > 0 for x in DETS)
    rz = R[(R.group == "real") & (R.gain != 0)]; sy = R[R.group == "syn"]
    h3r, h3s = (rz.gain < 0).mean(), (sy.gain > 0).mean()
    h4 = [(m[("real", x + "+hedge")] >= -0.2) and (m[("syn", x)] <= 0 or m[("syn", x + "+hedge")] >= 0.5 * m[("syn", x)]) for x in DETS]
    avg = lambda v, g: np.mean([m[(g, x + v)] for x in DETS])
    h4avg = avg("+hedge", "real") >= -0.2 and avg("+hedge", "syn") >= 0.5 * avg("", "syn")
    src = S[(S.group == "real") & (S.pol != "none")].groupby(["pol", "src"]).d_acc.mean().unstack()
    tail = {v or "full": (src.loc[[x + v for x in DETS]].min(1).mean(), src.loc[[x + v for x in DETS]].max(1).mean())
            for v in ("", "+half", "+hedge")}
    print(f"\nH1' full below none on real: {h1}/8 (need >= 6) -> {'holds' if h1 >= 6 else 'fails'}")
    print(f"H2' full above none on synthetic: {h2}/8 (need >= 6) -> {'holds' if h2 >= 6 else 'fails'}")
    print(f"H3' real: {100 * h3r:.1f}% of {len(rz)} non-zero resets are losses; synthetic: {100 * h3s:.1f}% of {len(sy)} resets "
          f"are wins (need > 50% each) -> {'holds' if h3r > 0.5 and h3s > 0.5 else 'fails'}")
    print(f"H4' per detector {sum(h4)}/8; detector average: real +hedge {avg('+hedge', 'real'):.2f} (need >= -0.2), synthetic "
          f"+hedge {avg('+hedge', 'syn'):.2f} vs half of full {0.5 * avg('', 'syn'):.2f} -> {'holds' if h4avg else 'fails'}")
    print(f"tail over {src.shape[1]} real sources, detector-averaged (worst, best):", {k: (round(a, 2), round(b, 2)) for k, (a, b) in tail.items()})
    t1 = tail["+hedge"][0] - tail["full"][0]; t2 = tail["+hedge"][1] >= 0.5 * tail["full"][1]
    print(f"T1 worst source: +hedge - full = {t1:.2f} (need >= 10) -> {'holds' if t1 >= 10 else 'fails'}")
    print(f"T2 best source: +hedge {tail['+hedge'][1]:.2f} vs half of full {0.5 * tail['full'][1]:.2f} -> {'holds' if t2 else 'fails'}")


if __name__ == "__main__":
    main(sys.argv[1])
