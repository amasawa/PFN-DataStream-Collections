"""TKDE review (round 3): uncertainty-aware non-inferiority of MICE against FIFO on the 29 real streams.

Per stream: per-batch accuracy difference d_t = 100 (MICE_t - FIFO_t) on the same batches (MICE: two-level rule
replayed from the cached expert predictions, as in the paper; FIFO: fifo1000 results). One-sided 95% lower bound of
the mean of d_t by a moving-block bootstrap over batches (temporal dependence), block lengths 10, 20 (primary) and 50,
10 000 resamples, fixed seed. Source level: the mean over the source's streams, each stream resampled independently.
Writes ../results_paper/noninferiority.csv and noninferiority_sources.csv. No TFM call.
"""
import glob
import os
import pickle

import numpy as np
import pandas as pd

import reweight

DIRS = {"realD": "../results_test", "realC": "../results_heldout", "realG": "../results_heldout2",
        "realH": "../results_heldout3", "realI": "../results_heldout4"}
REAL_D = {"elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
          "insects_incremental_reoccurring_balanced"}
BLOCKS, PRIMARY, NBOOT = (10, 20, 50), 20, 10_000


def source(stream):
    for name in ("airlines", "covertype", "poker", "insects", "phishing", "rialto", "spam", "weather", "elec2"):
        if name in stream:
            return name
    return stream


def series(d, stream):
    c = pickle.load(open(f"{d}/{stream}__micev1000_500.pkl", "rb"))
    mice = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    fifo = np.load(f"{d}/{stream}__fifo1000.npz")["acc"]
    t = np.array(sorted(mice))
    x = 100 * (np.array([mice[k] for k in t]) - fifo[t])
    assert np.isfinite(x).all(), stream
    return x


def block_means(d, block, rng, nboot=NBOOT):
    n = len(d)
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(nboot, k))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(nboot, -1)[:, :n]
    return d[idx].mean(1)


def main():
    rng = np.random.default_rng(0)
    rows, boots = [], {}
    for g, d in DIRS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if g == "realD" and s not in REAL_D:
                continue
            x = series(d, s)
            r = dict(group=g, stream=s, source=source(s), batches=len(x), mean=x.mean())
            for b in BLOCKS:
                bm = block_means(x, b, rng)
                r[f"lb95_b{b}"] = np.percentile(bm, 5)
                if b == PRIMARY:
                    boots[s] = bm
            rows.append(r)
    r = pd.DataFrame(rows)
    assert len(r) == 29, len(r)
    r.to_csv("../results_paper/noninferiority.csv", index=False)
    src = []
    for name, g in r.groupby("source"):
        bm = np.mean([boots[s] for s in g.stream], axis=0)
        src.append(dict(source=name, streams=len(g), mean=g["mean"].mean(), lb95=np.percentile(bm, 5)))
    s = pd.DataFrame(src)
    s.to_csv("../results_paper/noninferiority_sources.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.round(3).to_string(index=False))
    print(s.round(3).to_string(index=False))
    for b in BLOCKS:
        lb = r[f"lb95_b{b}"]
        print(f"block {b}: streams with LB >= -0.3: {(lb >= -0.3).sum()}/29, >= -0.5: {(lb >= -0.5).sum()}/29, "
              f"worst LB {lb.min():.3f} ({r.stream[lb.idxmin()]})")


if __name__ == "__main__":
    main()
