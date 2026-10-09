"""TKDE round 8 sensitivity (registered in experiments/mice_tkde_control/PLAN.md, "Round 8 addition"): learning
curves of the frozen TFM measured on rows drawn independently of every evaluated grid stream.

Concept definitions (centroids, weights, labels) come from default_rng(seed) exactly as in grid_streams.stream; the
rows come from default_rng([20_000 + seed, m, k]), one generator per seed, centroid count m and concept k. Protocol otherwise as learning_curve.py. Writes
../results_grid_test/learning_curve_indep.csv and ../results_grid_test/predicted_indep.csv."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from grid_streams import stream

D, NCLS, K, WIDTH, B, M = 10, 4, 3, 0.15, 100, 1000


def concept_rows(nc, seed, k, n):
    rng = np.random.default_rng(seed)
    C = rng.uniform(0, 1, size=(nc, D))
    w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(NCLS, size=nc) for _ in range(K)]
    aux = np.random.default_rng([20_000 + seed, nc, k])
    j = aux.choice(nc, n, p=w)
    return (C[j] + aux.normal(scale=WIDTH, size=(n, D))).astype(np.float32), lab[k][j]


def no_overlap():
    for seed in (10, 11):
        for nc in (5, 30, 100):
            new = {bytes(r) for k in range(K) for r in concept_rows(nc, seed, k, 4000)[0]}
            for s in (10, 11, 20, 21):
                for b in (500, 2000):
                    X, _, _ = stream(nc, b, s)
                    assert not any(bytes(r) in new for r in X), (seed, nc, s, b)
    print("no row of the new curve data appears in any evaluated grid stream (seeds 10, 11, 20, 21)")


def curves():
    from run import TFM
    rows = []
    for seed in (10, 11):
        for nc in (5, 30, 100):
            for k in range(K):
                Xk, yk = concept_rows(nc, seed, k, 4000)
                f = TFM(NCLS, seed)
                for n in (50, 100, 200, 500, 1000, 2000):
                    for rep in range(3):
                        idx = np.random.default_rng(rep).choice(3000, n, replace=False)
                        acc = (f.predict(Xk[idx], yk[idx], Xk[3000:]).argmax(1) == yk[3000:]).mean()
                        rows.append(dict(seed=seed, n_centroids=nc, concept=k, n=n, rep=rep, acc=acc))
    d = pd.DataFrame(rows)
    d.to_csv("../results_grid_test/learning_curve_indep.csv", index=False)
    return d


def predictions(lc):
    lc = lc.groupby(["n_centroids", "n"]).acc.mean()
    out = {}
    for nc in (5, 30, 100):
        ns, a = lc[nc].index.values, lc[nc].values
        acc = lambda n: np.interp(np.log(n), np.log(ns), a)
        for L in (500, 2000):
            J = L // B
            reg = np.mean([max(0.0, acc(M) - acc(min(j * B, M))) for j in range(1, J)]) * (J - 1) / J * 2 / 3
            vis = sum(np.mean([max(0.0, acc(min(M, (c - 1) * L)) - acc(min(j * B, M))) for j in range(1, J)])
                      * (J - 1) / J for c in (2, 3)) / 3
            out[(nc, L)] = (100 * reg, 100 * vis)
    return out


if __name__ == "__main__":
    no_overlap()
    d = curves() if "--reuse" not in sys.argv else pd.read_csv("../results_grid_test/learning_curve_indep.csv")
    old = pd.read_csv("../results_grid_test/learning_curve.csv")
    pv = pd.read_csv("../results_grid_test/predicted_visit.csv")
    pn, po = predictions(d), predictions(old)
    pv["registered_recomputed"] = [po[(r.centroids, r.block)][0] for r in pv.itertuples()]
    pv["indep_registered"] = [pn[(r.centroids, r.block)][0] for r in pv.itertuples()]
    pv["indep_visit_specific"] = [pn[(r.centroids, r.block)][1] for r in pv.itertuples()]
    pv.to_csv("../results_grid_test/predicted_indep.csv", index=False)
    pd.set_option("display.width", 200)
    print(pv.round(2).to_string(index=False))
    for col in ("registered", "registered_recomputed", "visit_specific", "indep_registered", "indep_visit_specific"):
        print(f"{col:22s} Spearman seeds 10-11 (fast) {pv[col].corr(pv.observed_fast_s10_11, method='spearman'):.3f} "
              f"| seeds 20-21 (MICE) {pv[col].corr(pv.observed_mice_s20_21, method='spearman'):.3f}")
    print(d.groupby(["n_centroids", "n"]).acc.mean().unstack().round(3).to_string())
    print(old.groupby(["n_centroids", "n"]).acc.mean().unstack().round(3).to_string())
