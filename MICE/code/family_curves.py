"""Learning curves of the frozen TFM on the concepts of the synthetic family streams (dev seeds 0-2), and the
recall-versus-relearn gain they predict (same formula as predict_gain.py; block L = 2000, 3 cycles).
For each concept: context = n rows of its first visit, test = 1000 rows of its second visit.
Output: ../results_dev/family_curves.csv"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from run import TFM

SEEDS = [int(a) for a in sys.argv[1:]] or [0, 1, 2]
rows = []
for fam in ("sea", "stagger", "agrawal", "sine", "rbf", "hyperplane"):
    for s in SEEDS:
        z = np.load(f"../data/{fam}_s{s}.npz"); X, y, c = z["X"], z["y"].astype(int), z["concept"]
        f = TFM(int(y.max()) + 1, s)
        for k in np.unique(c):
            idx = np.flatnonzero(c == k)
            first, second = idx[:2000], idx[2000:3000]
            for n in (50, 100, 200, 500, 1000, 2000):
                tr = first[-n:]
                rows.append(dict(family=fam, seed=s, concept=k, n=n,
                                 acc=(f.predict(X[tr], y[tr], X[second]).argmax(1) == y[second]).mean()))
d = pd.DataFrame(rows); d.to_csv(f"../results_{'dev' if SEEDS == [0, 1, 2] else 'test'}/family_curves.csv", index=False)
lc = d.groupby(["family", "n"]).acc.mean()
B, M, L = 100, 1000, 2000
for fam in lc.index.levels[0]:
    ns, accs = lc[fam].index.values, lc[fam].values
    acc = lambda n: np.interp(np.log(n), np.log(ns), accs)
    J = L // B
    g = (2 / 3) * np.mean([acc(M) - acc(min(j * B, M)) for j in range(1, J)]) * (J - 1) / J
    print(fam, " ".join(f"{a:.3f}" for a in accs), "predicted gain", round(g, 4))
