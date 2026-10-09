"""TKDE round 2 (rebuttal item 2, retrospective, not registered): uncertainty for the pool controls on the aligned
grid. Per stream, moving-block bootstrap of the batch sequence with the same indices for MICE - archive and
MICE - snapshot (blocks of 10 batches, 10 000 resamples, seed 0; streams have 44 or 179 batches); two-sided 95%
percentile intervals and one-sided 95% lower bounds. Aggregate over the 8 streams with 30 or 100 centroids (the
criterion set): mean of independently resampled streams. Pointwise, conditional on the streams and backbone seed 0.
Writes ../results_paper/pool_control_grid_ci.csv."""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight

B, NB = 10, 10_000


def series(f):
    a = reweight.simulate2(pickle.load(open(f, "rb")), outer="brier", scale=0.5, temper=True)
    t = np.array(sorted(a))
    return t, 100 * np.array([a[k] for k in t])


def main(root):
    rng = np.random.default_rng(0)
    rows, boots = [], {}
    for f in sorted(glob.glob("../results_grid_test3/grid_c*_s2[01]__micev1000_500.pkl")):
        s = os.path.basename(f).split("__")[0]
        t, m = series(f)
        ta, a = series(f"{root}/arch/{s}__arch1000_500.pkl")
        ts, sn = series(f"{root}/snap/{s}__snap1000_500.pkl")
        assert (t == ta).all() and (t == ts).all()
        da, ds, n = m - a, m - sn, len(t)
        k = int(np.ceil(n / B))
        idx = (rng.integers(0, n - B + 1, size=(NB, k))[:, :, None] + np.arange(B)).reshape(NB, -1)[:, :n]
        ba, bs = da[idx].mean(1), ds[idx].mean(1)
        boots[s] = (ba, bs)
        rows.append(dict(stream=s, nc=int(s.split("_")[1][1:]), block=int(s.split("_")[2][1:]), batches=n,
                         d_arch=da.mean(), arch_lo=np.percentile(ba, 2.5), arch_hi=np.percentile(ba, 97.5),
                         arch_lb=np.percentile(ba, 5), d_snap=ds.mean(), snap_lo=np.percentile(bs, 2.5),
                         snap_hi=np.percentile(bs, 97.5), snap_lb=np.percentile(bs, 5)))
    r = pd.DataFrame(rows)
    h = r[r.nc >= 30]
    agg_a = np.mean([boots[s][0] for s in h.stream], axis=0)
    agg_s = np.mean([boots[s][1] for s in h.stream], axis=0)
    r.to_csv("../results_paper/pool_control_grid_ci.csv", index=False)
    pd.DataFrame([dict(comparison="arch", mean=h.d_arch.mean(), lo=np.percentile(agg_a, 2.5), hi=np.percentile(agg_a, 97.5)),
                  dict(comparison="snap", mean=h.d_snap.mean(), lo=np.percentile(agg_s, 2.5), hi=np.percentile(agg_s, 97.5))]
                 ).to_csv("../results_paper/pool_control_grid_ci_aggregate.csv", index=False)
    pd.set_option("display.width", 220)
    print(r.round(2).to_string(index=False))
    print(f"aggregate c30/c100 MICE-arch {h.d_arch.mean():+.3f} 95% [{np.percentile(agg_a,2.5):+.3f}, {np.percentile(agg_a,97.5):+.3f}]"
          f" | MICE-snap {h.d_snap.mean():+.3f} 95% [{np.percentile(agg_s,2.5):+.3f}, {np.percentile(agg_s,97.5):+.3f}]")
    print("streams whose 95% interval for MICE-arch excludes 0:", int(((h.arch_lo > 0) | (h.arch_hi < 0)).sum()), "/ 8")


if __name__ == "__main__":
    main(sys.argv[1])
