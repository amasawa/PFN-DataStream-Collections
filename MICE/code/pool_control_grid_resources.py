"""TKDE round 2 (rebuttal): per-stream resources of the three pools on the aligned grid, as in pool_control_real.py:
active experts per batch (from the cached predictions), TFM calls per batch (counter, MICE including its discrepancy
calls), stored pool rows per batch (archive and snapshot exact from their storage rules; MICE bounded by 500 and
1000 rows per stored expert). Writes ../results_paper/pool_control_grid_resources.csv."""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

from pool_control_real import SEG, pool_sizes, snap_rows


def main(root):
    rows = []
    for f in sorted(glob.glob("../results_grid_test3/grid_c*_s2[01]__micev1000_500.pkl")):
        s = os.path.basename(f).split("__")[0]
        r = dict(stream=s)
        c = pickle.load(open(f, "rb")); t = np.array([st["t"] for st in c["cache"]])
        n_all, n_pool = pool_sizes(c, t)
        r.update(mice_experts=n_all.mean(), mice_calls=float(np.load(f[:-4] + ".npz")["calls"]) / len(t),
                 mice_rows_min=(SEG * n_pool).mean(), mice_rows_max=(1000 * n_pool).mean())
        for name in ("arch", "snap"):
            g = f"{root}/{name}/{s}__{name}1000_500.pkl"
            cc = pickle.load(open(g, "rb"))
            na, npool = pool_sizes(cc, t)
            r[f"{name}_experts"] = na.mean()
            r[f"{name}_calls"] = float(np.load(g[:-4] + ".npz")["calls"]) / len(t)
            r[f"{name}_rows"] = (SEG * npool if name == "arch" else snap_rows(t, c["B"])).mean()
        rows.append(r)
    d = pd.DataFrame(rows)
    d.to_csv("../results_paper/pool_control_grid_resources.csv", index=False)
    print(d.round(1).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
