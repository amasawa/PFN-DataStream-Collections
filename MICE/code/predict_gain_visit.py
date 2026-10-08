"""Theorem-consistent predicted gain of recall over relearn (TKDE revision, 2026-10-09).

Same learning curves and interpolation as the registered predictions (check_grid_test.py, make_paper_tables.py), but
with the stored context of n_c = min(M, (c-1) L) rows on visit c, as in the theorem, instead of M rows on every
recurrence. Three cycles: visits c = 2, 3 recur, each with weight 1/3. Writes ../results_grid_test/predicted_visit.csv
with the registered and the visit-specific predictions next to the observed gains (fast level, seeds 10-11; full
method, seeds 20-21) and prints the correlations.
"""
import sys

import numpy as np
import pandas as pd

sys.argv = sys.argv[:1]
import make_paper_tables as mpt  # noqa: E402  (collect() reads the stored stream results)

B, M = 100, 1000
REGISTERED = {(5, 500): 0.0009, (5, 2000): 0.0003, (30, 500): 0.0191, (30, 2000): 0.0055, (100, 500): 0.1044,
              (100, 2000): 0.0303}
lc = pd.read_csv("../results_grid_test/learning_curve.csv").groupby(["n_centroids", "n"]).acc.mean()


def predicted(nc, L):
    ns, a = lc[nc].index.values, lc[nc].values
    acc = lambda n: np.interp(np.log(n), np.log(ns), a)
    J = L // B
    return sum(np.mean([max(0.0, acc(min(M, (c - 1) * L)) - acc(min(j * B, M))) for j in range(1, J)]) * (J - 1) / J
               for c in (2, 3)) / 3


g = mpt.collect()
g = g[g.group.isin(["grid10", "grid20"])].copy()
g["c"] = g.stream.str.extract(r"_c(\d+)_")[0].astype(int)
g["b"] = g.stream.str.extract(r"_b(\d+)_")[0].astype(int)
rows = []
for (c, b), p in REGISTERED.items():
    x = g[(g.c == c) & (g.b == b)]
    rows.append(dict(centroids=c, block=b, registered=100 * p, visit_specific=100 * predicted(c, b),
                     observed_fast_s10_11=100 * x[x.group == "grid10"].eval("mice1 - ddm").mean(),
                     observed_mice_s20_21=100 * x[x.group == "grid20"].eval("mice - ddm").mean()))
d = pd.DataFrame(rows)
d.to_csv("../results_grid_test/predicted_visit.csv", index=False)
print(d.round(2).to_string(index=False))
for col in ("registered", "visit_specific"):
    print(col, "Spearman %.3f / %.3f" % (d[col].corr(d.observed_fast_s10_11, method="spearman"),
                                         d[col].corr(d.observed_mice_s20_21, method="spearman")))
