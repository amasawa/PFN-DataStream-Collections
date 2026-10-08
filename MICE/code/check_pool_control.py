"""TKDE review, round 2: does merging by discrepancy add value over a plain pool of past contexts?
Decided as pre-registered in experiments/mice_tkde_control/PLAN.md (written before the run).

MICE (existing micev1000_500 caches of the paper) and the controls arch1000_500 (every closed segment its own
expert, no merging) and snap1000_500 (snapshot of the latest 1000 rows at every segment close) are replayed with the
same two-level rule (half Brier, step 1/2, tempered), over the same batches. Criteria:
  merging adds value on recurring concepts: on the 8 grid streams with 30 or 100 centroids (seeds 20, 21),
      MICE - arch mean >= +0.5 points and positive on >= 6 of 8;
  no cost on real streams: MICE - arch mean >= -0.1 points over the 29 real streams.
Also reported: snap, expert calls and wall time per batch.
Usage: python check_pool_control.py <run root> [grid|all]   (writes ../results_paper/pool_control_*.csv)"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

import reweight
from noninferiority import DIRS as REAL, REAL_D, source


def replay(f):
    a = reweight.simulate2(pickle.load(open(f, "rb")), outer="brier", scale=0.5, temper=True)
    t = np.array(sorted(a))
    return t, 100 * np.array([a[k] for k in t])


def cost(f, t):
    z = np.load(f)
    return float(z["calls"]) / len(t) if z["calls"].ndim == 0 else float(np.mean(z["calls"])), float(np.mean(z["wt"][t]))


def row(stream, mice_dir, ctl_dirs):
    t, mice = replay(f"{mice_dir}/{stream}__micev1000_500.pkl")
    r = dict(stream=stream, batches=len(t), mice=mice.mean())
    r["mice_calls"], r["mice_wt"] = cost(f"{mice_dir}/{stream}__micev1000_500.npz", t)
    for name, d in ctl_dirs.items():
        f = f"{d}/{stream}__{name}1000_500.pkl"
        if not os.path.exists(f):
            continue
        tc, x = replay(f)
        assert (tc == t).all(), (stream, name)
        r[name] = x.mean()
        r[f"d_{name}"] = (mice - x).mean()
        r[f"{name}_calls"], r[f"{name}_wt"] = cost(f"{d}/{stream}__{name}1000_500.npz", t)
    return r


def main(root, part):
    ctl = {"arch": f"{root}/arch", "snap": f"{root}/snap"}
    g = []
    for f in sorted(glob.glob("../results_grid_test3/grid_c*_s2[01]__micev1000_500.pkl")):
        s = os.path.basename(f).split("__")[0]
        r = row(s, "../results_grid_test3", ctl)
        r["nc"], r["block"] = int(s.split("_")[1][1:]), int(s.split("_")[2][1:])
        g.append(r)
    g = pd.DataFrame(g)
    assert len(g) == 12 and g.d_arch.notna().all() and g.d_snap.notna().all(), len(g)
    g.to_csv("../results_paper/pool_control_grid.csv", index=False)
    pd.set_option("display.width", 250)
    print(g.round(3).to_string(index=False))
    h = g[g.nc >= 30]
    pos, mean = int((h.d_arch > 0).sum()), h.d_arch.mean()
    ok1 = mean >= 0.5 and pos >= 6
    print(f"CRITERION 1 (grid c30/c100, MICE - arch): mean {mean:+.3f} (need >= +0.5), positive {pos}/8 (need >= 6) "
          f"-> {'PASS' if ok1 else 'FAIL'}")
    print(f"  snap: MICE - snap on c30/c100 mean {h.d_snap.mean():+.3f}, positive {int((h.d_snap > 0).sum())}/8; "
          f"all 12: MICE - arch {g.d_arch.mean():+.3f}, MICE - snap {g.d_snap.mean():+.3f}")
    if part == "grid":
        return
    rr = []
    for grp, d in REAL.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if grp == "realD" and s not in REAL_D:
                continue
            r = row(s, d, {"arch": ctl["arch"]})
            r["group"], r["source"] = grp, source(s)
            rr.append(r)
    rr = pd.DataFrame(rr)
    assert len(rr) == 29 and rr.d_arch.notna().all(), (len(rr), rr.d_arch.isna().sum())
    rr.to_csv("../results_paper/pool_control_real.csv", index=False)
    print(rr.round(3).to_string(index=False))
    m = rr.d_arch.mean()
    print(f"CRITERION 2 (29 real streams, MICE - arch): mean {m:+.3f} (need >= -0.1) -> {'PASS' if m >= -0.1 else 'FAIL'}; "
          f"positive {int((rr.d_arch > 0).sum())}/29, min {rr.d_arch.min():+.3f} ({rr.stream[rr.d_arch.idxmin()]}), "
          f"max {rr.d_arch.max():+.3f} ({rr.stream[rr.d_arch.idxmax()]})")
    print(rr.groupby("source").d_arch.mean().round(3))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "all")
