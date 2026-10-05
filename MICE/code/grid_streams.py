"""Controlled recall-versus-relearn grid (numpy only; runs in any venv). RBF mixture with n_centroids centroids in d=10
dimensions and 4 classes; the K=3 concepts share the centroids (so P(x) is identical) and differ only in the class
assigned to each centroid (a random permutation per concept): a pure real drift whose learning cost grows with the
number of centroids. Concepts recur in blocks of `block` rows, cycling 3 times.
Grid: n_centroids in {5, 30, 100} x block in {500, 2000}; dev seeds 0, 1 (test seeds 10, 11 reserved).
Output: ../data/grid_c<n>_b<block>_s<seed>.npz"""
import os
import sys

import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "..", "data")


def stream(nc, block, seed, d=10, n_classes=4, K=3, cycles=3, width=0.15):
    rng = np.random.default_rng(seed)
    C = rng.uniform(0, 1, size=(nc, d))
    w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(n_classes, size=nc) for _ in range(K)]  # class of each centroid, per concept
    X, y, c = [], [], []
    for _ in range(cycles):
        for k in range(K):
            j = rng.choice(nc, block, p=w)
            X.append(C[j] + rng.normal(scale=width, size=(block, d)))
            y.append(lab[k][j]); c.append(np.full(block, k))
    return np.concatenate(X).astype(np.float32), np.concatenate(y), np.concatenate(c)


if __name__ == "__main__":
    seeds = [int(s) for s in sys.argv[1:]] or [0, 1]
    for s in seeds:
        for nc in (5, 30, 100):
            for b in (500, 2000):
                f = f"{OUT}/grid_c{nc}_b{b}_s{s}.npz"
                if not os.path.exists(f):
                    X, y, c = stream(nc, b, s)
                    np.savez_compressed(f, X=X, y=y, concept=c)
                    print(f, X.shape, np.bincount(y))
