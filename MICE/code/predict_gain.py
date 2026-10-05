"""Predicted gain of recall over relearn from the learning curve alone (no stream result is used).
Model: after a switch, both lose the first batch (labels one batch late). Relearning (reset) then predicts batch j with
a context of min(j*B, L) rows of the concept: accuracy acc(min(jB, M)). Recall predicts with the stored context of
min(M, rows seen so far) rows: accuracy acc(M) from the second visit on (the first visit has no memory). With 3 cycles
over the concepts, 2 of 3 visits are recurrences. Predicted gain in overall accuracy:
  (2/3) * mean_{j=1..L/B-1} [acc(M) - acc(min(jB, M))] * (L/B - 1)/(L/B).
acc(n) is interpolated on log n from learning_curve.csv. Compared with the observed gain of micev (eta=10, gamma=0)
over ddm on the dev grid."""
import numpy as np, pandas as pd
lc = pd.read_csv("../results_grid_dev/learning_curve.csv").groupby(["n_centroids", "n"]).acc.mean()
B, M = 100, 1000
obs = {(5, 500): 0.0019, (5, 2000): 0.0015, (30, 500): 0.0172, (30, 2000): 0.0062, (100, 500): 0.0867, (100, 2000): 0.0296}
rows = []
for (nc, L), g_obs in obs.items():
    ns, accs = lc[nc].index.values, lc[nc].values
    acc = lambda n: np.interp(np.log(n), np.log(ns), accs)
    J = L // B
    rel = np.array([acc(min(j * B, M)) for j in range(1, J)])
    g = (2 / 3) * np.mean(acc(M) - rel) * (J - 1) / J
    rows.append(dict(n_centroids=nc, block=L, predicted=round(g, 4), observed=g_obs))
d = pd.DataFrame(rows); print(d.to_string(index=False))
print("Spearman", d[["predicted", "observed"]].corr(method="spearman").iloc[0, 1].round(3),
      "Pearson", d[["predicted", "observed"]].corr().iloc[0, 1].round(3))
