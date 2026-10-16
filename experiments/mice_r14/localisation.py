"""Round 14.b, part 1 (descriptive; PLAN_14B.md): location of the declared changes, separately from detection. For
every true change c (row) matched by a cut at batch b (as in analyse_test.segments: -B < bB - c < 4B), the lag
b - floor(c/B) in batches and the distance |bB - c| in rows, on the 72 test streams (seeds 40-43) and the 72
confirmation streams (seeds 50-53). Usage: python localisation.py   (writes ../../MICE/results_paper/r14b_location.csv)"""
import glob
import os

import numpy as np
import pandas as pd

from analyse_test import OUT, RUNS

B = 100
rows = []
for name, root in (("test", f"{RUNS}/mice-r14-test"), ("confirm", f"{RUNS}/mice-r14-confirm")):
    names = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{root}/data/*.npz"))
    assert len(names) == 72, (name, len(names))
    for s in names:
        concept = np.load(f"{root}/data/{s}.npz")["concept"]
        cuts = np.load(f"{root}/P/{s}__micecp1000_500.npz")["cuts"]
        ch = np.flatnonzero(concept[1:] != concept[:-1]) + 1
        det = np.array([b * B for _, b in cuts])
        for c in ch:
            m = det[(det - c > -B) & (det - c < 4 * B)]
            if len(m):
                d = m[np.argmin(np.abs(m - c))]
                rows.append(dict(set=name, stream=s, change=int(c), lag=int(d // B - c // B), dist=int(abs(d - c))))
            else:
                rows.append(dict(set=name, stream=s, change=int(c), lag=-1, dist=-1))
d = pd.DataFrame(rows)
d.to_csv(f"{OUT}/r14b_location.csv", index=False)
for name, x in d.groupby("set"):
    f = x[x.lag >= 0]
    print(f"{name}: changes {len(x)}, found {len(f)}; lag 0: {(f.lag == 0).mean():.3f}, lag 1: {(f.lag == 1).mean():.3f}, "
          f"lag 2: {(f.lag == 2).mean():.3f}, lag 3: {(f.lag == 3).mean():.3f}; within one batch (dist < {B}): "
          f"{(f.dist < B).mean():.3f}; median dist {f.dist.median():.0f}, max {f.dist.max()}")
