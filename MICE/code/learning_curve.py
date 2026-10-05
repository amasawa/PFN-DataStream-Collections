"""Learning curves of the frozen TFM on the grid concepts: accuracy with a context of n rows of one concept, tested on
1000 fresh rows of the same concept. eps(n) = acc(2000) - acc(n) is the excess error of re-learning from n rows,
which the recall-versus-relearn analysis uses. Dev seeds 0, 1. Output: ../results_grid_dev/learning_curve.csv"""
import os, sys
SEEDS = [int(a) for a in sys.argv[1:]] or [0, 1]
OUTF = "../results_grid_dev/learning_curve.csv" if SEEDS == [0, 1] else "../results_grid_test/learning_curve.csv"
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from run import TFM
from grid_streams import stream

rows = []
for seed in SEEDS:
    for nc in (5, 30, 100):
        X, y, c = stream(nc, 4000, seed, cycles=1)          # one long block per concept
        for k in range(3):
            Xk, yk = X[c == k], y[c == k]
            f = TFM(4, seed)
            for n in (50, 100, 200, 500, 1000, 2000):
                for rep in range(3):
                    idx = np.random.default_rng(rep).choice(3000, n, replace=False)
                    acc = (f.predict(Xk[idx], yk[idx], Xk[3000:]).argmax(1) == yk[3000:]).mean()
                    rows.append(dict(seed=seed, n_centroids=nc, concept=k, n=n, rep=rep, acc=acc))
    os.makedirs(os.path.dirname(OUTF), exist_ok=True); pd.DataFrame(rows).to_csv(OUTF, index=False)
d = pd.DataFrame(rows)
print(d.groupby(["n_centroids", "n"]).acc.mean().unstack().round(3).to_string())
