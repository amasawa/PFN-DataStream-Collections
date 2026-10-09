"""TKDE round 4, attempt 4.b (registered in experiments/mice_tkde_control/PLAN.md before the run): boundary
alignment at fixed block length. Offset streams off_c<nc>_b<block>_s<seed> (make_offset.py) hold 200 extra rows of
the first concept before the unchanged aligned stream, so offset batch t+2 = aligned batch t.

Matched batches t = 1..T_aligned-1. MICE and the archive replayed with the paper's two-level rule; baselines from
their per-batch accuracies. Recurrence windows: first five batches of blocks 4-9 (aligned indexing, +2 in offset).
Primary contrast: Delta_i = (MICE - DDM)_offset - (MICE - DDM)_aligned on matched batches (descriptive).
Descriptive criterion: MICE - DDM on the offset streams positive on >= 7 of 8 and mean >= +1.0.
Usage: python check_offset.py <run root>   (writes ../results_paper/offset.csv)"""
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight

SHIFT, ALIGNED = 2, "../results_grid_test3"


def replay(f):
    c = pickle.load(open(f, "rb"))
    a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    return a, c


def series(a, t):
    return 100 * np.array([a[k] for k in t])


def recurring(concept, B, K=3, first=5):
    starts = np.flatnonzero(np.r_[True, concept[1:] != concept[:-1]])
    return np.array(sorted({b for r in starts[K:] for b in range(r // B, r // B + first)}))


def policies(d_mice, d_arch, d_base, stream, t):
    out = {}
    a, c = replay(f"{d_mice}/{stream}__micev1000_500.pkl")
    out["mice"] = series(a, t)
    a, _ = replay(f"{d_arch}/{stream}__arch1000_500.pkl")
    out["arch"] = series(a, t)
    for b in ("ddm1000", "fifo1000", "winens1000"):
        x = 100 * np.load(f"{d_base}/{stream}__{b}.npz")["acc"][t]
        assert np.isfinite(x).all(), (stream, b)
        out[b[:-4]] = x
    return out, c


def main(root):
    rows = []
    for nc in (30, 100):
        for blk in (500, 2000):
            for s in (20, 21):
                al, of = f"grid_c{nc}_b{blk}_s{s}", f"off_c{nc}_b{blk}_s{s}"
                a0, c0 = replay(f"{ALIGNED}/{al}__micev1000_500.pkl")
                t = np.array(sorted(a0))                     # aligned batches 1..T-1
                A, _ = policies(ALIGNED, f"{root}/arch", ALIGNED, al, t)
                O, c1 = policies(f"{root}/off", f"{root}/off", f"{root}/off", of, t + SHIFT)
                assert c0["B"] == c1["B"] == 100 and blk % 100 == 0, of          # B=100 frozen for 4.b
                assert np.array_equal(c1["y"][SHIFT * c1["B"]:], c0["y"]), of
                rec = np.isin(t, recurring(c0["concept"], c0["B"]))
                r = dict(nc=nc, block=blk, seed=s, batches=len(t))
                for tag, P in (("al", A), ("off", O)):
                    for k, x in P.items():
                        r[f"{tag}_{k}"], r[f"{tag}_{k}_rec5"] = x.mean(), x[rec].mean()
                    for b in ("ddm", "fifo", "winens", "arch"):
                        r[f"{tag}_d_{b}"] = (P["mice"] - P[b]).mean()
                        r[f"{tag}_d_{b}_rec5"] = (P["mice"] - P[b])[rec].mean()
                r["delta"] = r["off_d_ddm"] - r["al_d_ddm"]
                r["delta_rec5"] = r["off_d_ddm_rec5"] - r["al_d_ddm_rec5"]
                full = replay(f"{root}/off/{of}__micev1000_500.pkl")[0]
                r["off_mice_full"] = 100 * np.mean(list(full.values()))
                rows.append(r)
    m = pd.DataFrame(rows)
    m.to_csv("../results_paper/offset.csv", index=False)
    pd.set_option("display.width", 250)
    print(m[["nc", "block", "seed", "al_d_ddm", "off_d_ddm", "delta", "al_d_ddm_rec5", "off_d_ddm_rec5", "delta_rec5",
             "al_d_arch", "off_d_arch", "off_d_fifo", "off_d_winens"]].round(2).to_string(index=False))
    print(m.groupby(["block", "nc"])[["al_d_ddm", "off_d_ddm", "delta", "delta_rec5", "off_d_arch"]].mean().round(2))
    pos, mean = int((m.off_d_ddm > 0).sum()), m.off_d_ddm.mean()
    print(f"PRIMARY CONTRAST Delta (offset - aligned of MICE - DDM): mean {m.delta.mean():+.3f}, "
          f"range {m.delta.min():+.2f}..{m.delta.max():+.2f}; recurrence windows mean {m.delta_rec5.mean():+.3f}")
    print(f"DESCRIPTIVE CRITERION offset MICE - DDM: positive {pos}/8 (>= 7), mean {mean:+.3f} (>= +1.0) -> "
          f"{'MET' if pos >= 7 and mean >= 1.0 else 'NOT MET'}")
    print(f"MICE - archive: aligned mean {m.al_d_arch.mean():+.3f}, offset mean {m.off_d_arch.mean():+.3f}, "
          f"offset positive {int((m.off_d_arch > 0).sum())}/8")


if __name__ == "__main__":
    main(sys.argv[1])
