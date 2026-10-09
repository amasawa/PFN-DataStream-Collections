"""TKDE round 2, registered addition (experiments/mice_tkde_control/PLAN.md, "Round 2 addition"): MICE versus the
storage-matched snapshot control and the archive on the 29 real streams, per stream, with uncertainty and resources.

Accuracy: mean of per-batch accuracies over batches 1..T-1 (two-level rule replayed from the caches).
Descriptive criterion (registered): unweighted mean over the 29 streams of MICE - snap >= -0.1 points.
Uncertainty: moving-block bootstrap of the batch sequence, the same resampled indices for all methods jointly; blocks
of 20 (10, 50 sensitivity; floor(T/2) if T < 2 x block), 10 000 resamples, seed 0; one-sided 95% percentile lower
bounds of the mean differences. Pointwise, conditional on the streams and backbone seed 0. MICE - arch bounds are a
retrospective analysis (labelled so).
Resources: active experts per batch (experts in the cached predictions; mean, max), TFM calls per batch (all fits and
predicts, including MICE's discrepancy calls), stored pool rows per batch: archive 500 per stored expert, snapshot
min(1000, 500 k) for the expert stored at the k-th segment close (exact, at most 12, oldest evicted), MICE between
500 and 1000 per stored expert (per-expert counts were not recorded): reported as a range.
Usage: python pool_control_real.py <run root>   (writes ../results_paper/pool_control_real_full.csv)"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight
from noninferiority import DIRS as REAL, REAL_D, source

BLOCKS, NBOOT, SEG, KMAX = (10, 20, 50), 10_000, 500, 12


def replay(f):
    c = pickle.load(open(f, "rb"))
    a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    t = np.array(sorted(a))
    return t, 100 * np.array([a[k] for k in t]), c


def pool_sizes(c, t):
    by_t = {s["t"]: s for s in c["cache"]}
    n_all = np.array([len(by_t[k]["P"]) for k in t])
    n_pool = np.array([sum(1 for u in by_t[k]["P"] if u > 0) for k in t])
    return n_all, n_pool


def snap_rows(t, B):
    out = []
    for k_t in (t * B) // SEG:
        ks = range(max(1, k_t - KMAX + 1), k_t + 1)
        out.append(sum(min(1000, SEG * k) for k in ks))
    return np.array(out)


def lower_bounds(d, rng):
    n, out = len(d), {}
    for b in BLOCKS:
        b_ = b if n >= 2 * b else n // 2
        k = int(np.ceil(n / b_))
        starts = rng.integers(0, n - b_ + 1, size=(NBOOT, k))
        idx = (starts[:, :, None] + np.arange(b_)[None, None, :]).reshape(NBOOT, -1)[:, :n]
        out[b] = {name: np.percentile(x[idx].mean(1), 5) for name, x in d.items()}
    return out


def main(root):
    rng = np.random.default_rng(0)
    rows = []
    for grp, d in REAL.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if grp == "realD" and s not in REAL_D:
                continue
            t, mice, cm = replay(f)
            r = dict(group=grp, stream=s, source=source(s), batches=len(t), mice=mice.mean())
            acc = {"mice": mice}
            for name in ("arch", "snap"):
                ft = f"{root}/{name}/{s}__{name}1000_500.pkl"
                tc, x, cc = replay(ft)
                assert (tc == t).all(), (s, name)
                acc[name] = x
                r[name] = x.mean()
                n_all, n_pool = pool_sizes(cc, t)
                r[f"{name}_experts_mean"], r[f"{name}_experts_max"] = n_all.mean(), n_all.max()
                r[f"{name}_calls_per_batch"] = float(np.load(f"{root}/{name}/{s}__{name}1000_500.npz")["calls"]) / len(t)
                rows_ = SEG * n_pool if name == "arch" else snap_rows(t, cm["B"])
                r[f"{name}_rows_mean"], r[f"{name}_rows_max"] = rows_.mean(), rows_.max()
            n_all, n_pool = pool_sizes(cm, t)
            r["mice_experts_mean"], r["mice_experts_max"] = n_all.mean(), n_all.max()
            r["mice_calls_per_batch"] = float(np.load(f"{d}/{s}__micev1000_500.npz")["calls"]) / len(t)
            r["mice_rows_min_mean"], r["mice_rows_max_mean"] = (SEG * n_pool).mean(), (1000 * n_pool).mean()
            r["mice_rows_max_bound"] = (1000 * n_pool).max()
            diffs = {"d_arch": acc["mice"] - acc["arch"], "d_snap": acc["mice"] - acc["snap"]}
            r["d_arch"], r["d_snap"] = diffs["d_arch"].mean(), diffs["d_snap"].mean()
            for b, lb in lower_bounds(diffs, rng).items():
                r[f"lb_snap_b{b}"], r[f"lb_arch_b{b}_retro"] = lb["d_snap"], lb["d_arch"]
            rows.append(r)
    r = pd.DataFrame(rows)
    assert len(r) == 29, len(r)
    r.to_csv("../results_paper/pool_control_real_full.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["stream", "batches", "mice", "arch", "snap", "d_arch", "d_snap", "lb_snap_b20", "lb_arch_b20_retro",
            "mice_calls_per_batch", "arch_calls_per_batch", "snap_calls_per_batch"]
    print(r[cols].round(3).to_string(index=False))
    m = r.d_snap.mean()
    print(f"REGISTERED DESCRIPTIVE CRITERION MICE - snap: mean {m:+.3f} (>= -0.1?) -> {'MET' if m >= -0.1 else 'NOT MET'}; "
          f"positive {int((r.d_snap > 0).sum())}/29; min {r.d_snap.min():+.3f}; max {r.d_snap.max():+.3f}")
    for b in BLOCKS:
        print(f"block {b}: LB(MICE-snap) >= -0.3 on {(r[f'lb_snap_b{b}'] >= -0.3).sum()}/29; "
              f"LB(MICE-arch, retrospective) >= -0.3 on {(r[f'lb_arch_b{b}_retro'] >= -0.3).sum()}/29")
    print(r.groupby("source")[["d_arch", "d_snap"]].mean().round(3))
    print("experts per batch (mean over streams):", r[["mice_experts_mean", "arch_experts_mean", "snap_experts_mean"]].mean().round(2).to_dict())
    print("calls per batch (mean):", r[["mice_calls_per_batch", "arch_calls_per_batch", "snap_calls_per_batch"]].mean().round(2).to_dict())
    print("pool rows (mean over streams of per-batch mean): MICE in [", round(r.mice_rows_min_mean.mean()), ",",
          round(r.mice_rows_max_mean.mean()), "], arch", round(r.arch_rows_mean.mean()), ", snap", round(r.snap_rows_mean.mean()))


if __name__ == "__main__":
    main(sys.argv[1])
