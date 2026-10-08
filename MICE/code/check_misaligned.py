"""TKDE review, round 4: misaligned-boundary robustness test, decided as pre-registered in
experiments/mice_tkde_control/PLAN.md (written before the run).

Streams mis_{b700,b1300,bvar}_c{30,100}_s{30,31} (make_misaligned.py). MICE and the arch control are replayed from
the cached expert predictions with the two-level rule of the paper (half Brier, step 1/2, tempered); the baselines
use their per-batch accuracies, averaged over the same batches 1..T. Criterion: MICE - DDM > 0 on at least 10 of 12
streams and mean >= +1.0 point. Also reported: MICE - FIFO, MICE - window ensemble, MICE - arch per condition and
centroid count; accuracy in the first five batches after each recurring switch (blocks 4-9, whose concept was seen
before); the aligned grid (seeds 20 and 21, ../results_grid_test3) for comparison.
Usage: python check_misaligned.py <run root>   (writes ../results_paper/misaligned*.csv)"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight

BASE = ("ddm1000", "fifo1000", "winens1000")


def replay(f):
    c = pickle.load(open(f, "rb"))
    a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    t = np.array(sorted(a))
    return t, 100 * np.array([a[k] for k in t]), c


def recurring_batches(concept, B, K=3, first=5):
    starts = np.flatnonzero(np.r_[True, concept[1:] != concept[:-1]])
    out = []
    for r in starts[K:]:                         # blocks after the first cycle: their concept was seen before
        b0 = r // B
        out += list(range(b0, b0 + first))
    return np.array(sorted(set(out)))


def stream_row(d, s):
    t, mice, c = replay(f"{d}/{s}__micev1000_500.pkl")
    row = dict(stream=s, batches=len(t), mice=mice.mean())
    acc = {"mice": mice}
    f = f"{d}/{s}__arch1000_500.pkl"
    if os.path.exists(f):
        ta, arch, _ = replay(f)
        assert (ta == t).all()
        acc["arch"] = arch
        row["arch"] = arch.mean()
    for b in BASE:
        x = 100 * np.load(f"{d}/{s}__{b}.npz")["acc"][t]
        assert np.isfinite(x).all(), (s, b)
        acc[b[:-4]] = x
        row[b[:-4]] = x.mean()
    rb = recurring_batches(c["concept"], c["B"])
    keep = np.isin(t, rb)
    for k, x in acc.items():
        row[f"{k}_rec5"] = x[keep].mean()
    return row


def main(root):
    rows = []
    for f in sorted(glob.glob(f"{root}/mis/mis_*__micev1000_500.pkl")):
        s = os.path.basename(f).split("__")[0]
        r = stream_row(f"{root}/mis", s)
        r["cond"], r["nc"] = s.split("_")[1], int(s.split("_")[2][1:])
        rows.append(r)
    m = pd.DataFrame(rows)
    assert len(m) == 12, len(m)
    for b in ("ddm", "fifo", "winens", "arch"):
        m[f"d_{b}"] = m.mice - m[b]
        m[f"d_{b}_rec5"] = m.mice_rec5 - m[f"{b}_rec5"]
    al = []
    for f in sorted(glob.glob("../results_grid_test3/grid_c*_b*_s2[01]__micev1000_500.pkl")):
        s = os.path.basename(f).split("__")[0]
        nc = int(s.split("_")[1][1:])
        if nc < 30:
            continue
        r = stream_row("../results_grid_test3", s)
        r["cond"], r["nc"] = s.split("_")[2], nc
        al.append(r)
    a = pd.DataFrame(al)
    for b in ("ddm", "fifo", "winens"):
        a[f"d_{b}"] = a.mice - a[b]
        a[f"d_{b}_rec5"] = a.mice_rec5 - a[f"{b}_rec5"]
    os.makedirs("../results_paper", exist_ok=True)
    m.to_csv("../results_paper/misaligned.csv", index=False)
    a.to_csv("../results_paper/misaligned_aligned_reference.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["stream", "batches", "mice", "ddm", "fifo", "winens", "arch", "d_ddm", "d_fifo", "d_winens", "d_arch",
            "d_ddm_rec5"]
    print(m[cols].round(2).to_string(index=False))
    g = m.groupby(["cond", "nc"])[["d_ddm", "d_fifo", "d_winens", "d_arch", "d_ddm_rec5", "d_arch_rec5"]].mean()
    print(g.round(2))
    print("aligned grid (seeds 20, 21; c30/c100):")
    print(a.groupby(["cond", "nc"])[["d_ddm", "d_fifo", "d_winens", "d_ddm_rec5"]].mean().round(2))
    pos, mean = int((m.d_ddm > 0).sum()), m.d_ddm.mean()
    ok = pos >= 10 and mean >= 1.0
    print(f"CRITERION MICE - DDM: positive on {pos}/12 (need >= 10), mean {mean:+.3f} (need >= +1.0) -> "
          f"{'PASS' if ok else 'FAIL'}")
    print(f"MICE - arch: mean {m.d_arch.mean():+.3f}, positive {int((m.d_arch > 0).sum())}/12; "
          f"MICE - FIFO mean {m.d_fifo.mean():+.3f}; MICE - winens mean {m.d_winens.mean():+.3f}")




def snap_exploratory(root):
    """Exploratory (added after the round-4 results; not registered): storage-matched snapshot control on the
    12 misaligned streams, following MiMo's round-4 finding F2. Writes ../results_paper/misaligned_snap.csv."""
    m = pd.read_csv("../results_paper/misaligned.csv")
    rows = []
    for s in m.stream:
        t, mice, _ = replay(f"{root}/mis/{s}__micev1000_500.pkl")
        ts, snap, _ = replay(f"{root}/mis/{s}__snap1000_500.pkl")
        assert (ts == t).all(), s
        rows.append(dict(stream=s, snap=snap.mean(), d_snap=(mice - snap).mean()))
    r = m[["stream", "cond", "nc", "mice", "arch", "d_arch"]].merge(pd.DataFrame(rows), on="stream")
    r.to_csv("../results_paper/misaligned_snap.csv", index=False)
    print(r.round(2).to_string(index=False))
    print(f"EXPLORATORY MICE - snap: mean {r.d_snap.mean():+.3f}, positive {int((r.d_snap > 0).sum())}/12, "
          f"range {r.d_snap.min():+.2f}..{r.d_snap.max():+.2f}")


if __name__ == "__main__":
    snap_exploratory(sys.argv[1]) if sys.argv[2:] == ["snap"] else main(sys.argv[1])
