"""TKDE round 9, part B (registered in experiments/mice_tkde_control/PLAN.md, "Round 9 addition"): MICE versus FIFO
with M* = 3000 rows (fixed from timings only; not cost-matched: about 2.5 times cheaper than MICE) on the 29 real
streams. Per stream: mean of per-batch differences (points), two-sided 95% and one-sided 95% moving-block bootstrap
bounds (blocks of 20 batches, or floor(T/2) for short streams; 10 000 resamples; seed 0; paired batch indices).
Aggregate: unweighted mean over streams, each resampled independently. Writes ../results_paper/fifo3000_real.csv."""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight
from noninferiority import DIRS, REAL_D, source

B, NB = 20, 10_000


def main(root):
    rng = np.random.default_rng(0)
    rows, boots = [], []
    for g, d in DIRS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if g == "realD" and s not in REAL_D:
                continue
            a = reweight.simulate2(pickle.load(open(f, "rb")), outer="brier", scale=0.5, temper=True)
            t = np.array(sorted(a)); m = 100 * np.array([a[k] for k in t])
            x = 100 * np.load(f"{root}/fifoM/{s}__fifo3000.npz")["acc"][t]
            f1 = 100 * np.load(f"{d}/{s}__fifo1000.npz")["acc"][t]
            assert np.isfinite(x).all() and np.isfinite(f1).all(), s
            diff, n = m - x, len(t)
            b = B if n >= 2 * B else n // 2
            idx = (rng.integers(0, n - b + 1, size=(NB, int(np.ceil(n / b))))[:, :, None] + np.arange(b)).reshape(NB, -1)[:, :n]
            bm = diff[idx].mean(1); boots.append(bm)
            rows.append(dict(stream=s, source=source(s), batches=n, mice=m.mean(), fifo3000=x.mean(), fifo1000=f1.mean(),
                             d=diff.mean(), lo=np.percentile(bm, 2.5), hi=np.percentile(bm, 97.5), lb=np.percentile(bm, 5)))
    r = pd.DataFrame(rows); assert len(r) == 29
    agg = np.mean(boots, axis=0)
    r.to_csv("../results_paper/fifo3000_real.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.round(2).to_string(index=False))
    print(f"MICE - FIFO3000: mean {r.d.mean():+.3f}, 95% [{np.percentile(agg,2.5):+.3f}, {np.percentile(agg,97.5):+.3f}], "
          f"one-sided LB {np.percentile(agg,5):+.3f}; positive {int((r.d>0).sum())}/29; "
          f"two-sided CI excludes 0 below: {int((r.hi<0).sum())}, above: {int((r.lo>0).sum())}")
    print(r.groupby("source")[["d"]].mean().round(2).T)
    print(f"FIFO3000 - FIFO1000 mean {(r.fifo3000-r.fifo1000).mean():+.3f}; MICE - FIFO1000 mean {(r.mice-r.fifo1000).mean():+.3f}")
    pd.DataFrame([dict(mean=r.d.mean(), lo=np.percentile(agg, 2.5), hi=np.percentile(agg, 97.5), lb=np.percentile(agg, 5))]
                 ).to_csv("../results_paper/fifo3000_real_aggregate.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1])
