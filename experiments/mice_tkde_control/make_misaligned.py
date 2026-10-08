"""Round-4 robustness streams (TKDE review): concept boundaries not aligned with MICE's 500-row segments.

Same construction as MICE/code/grid_streams.py (RBF mixture, d=10, 4 classes, K=3 concepts sharing centroids and
differing only in centroid labels, three cycles), but with block lengths that are not multiples of 500: fixed 700,
fixed 1300, or variable (each block drawn uniformly from {500, 600, ..., 2500} rows). Fresh data seeds 30 and 31,
30 or 100 centroids: 12 streams. Writes <root>/data/mis_<cond>_c<nc>_s<seed>.npz with X, y, concept.
"""
from pathlib import Path
import sys

import numpy as np


def stream(nc, blocks, seed, d=10, n_classes=4, K=3, width=0.15):
    rng = np.random.default_rng(seed)
    C = rng.uniform(0, 1, size=(nc, d))
    w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(n_classes, size=nc) for _ in range(K)]
    X, y, c = [], [], []
    for i, block in enumerate(blocks):
        k = i % K
        j = rng.choice(nc, block, p=w)
        X.append(C[j] + rng.normal(scale=width, size=(block, d)))
        y.append(lab[k][j]); c.append(np.full(block, k))
    return np.concatenate(X).astype(np.float32), np.concatenate(y), np.concatenate(c)


def names():
    return [f"mis_{cond}_c{nc}_s{s}" for cond in ("b700", "b1300", "bvar") for nc in (30, 100) for s in (30, 31)]


def main(root):
    out = Path(root) / "data"
    for name in names():
        cond, c, s = name.split("_")[1:]
        nc, seed = int(c[1:]), int(s[1:])
        if cond == "bvar":
            blocks = list(np.random.default_rng(1000 + seed).choice(np.arange(500, 2501, 100), size=9))
        else:
            blocks = [int(cond[1:])] * 9
        X, y, concept = stream(nc, blocks, seed)
        np.savez_compressed(out / f"{name}.npz", X=X, y=y, concept=concept)
        print(name, X.shape, "blocks", blocks if cond == "bvar" else blocks[0])


if __name__ == "__main__":
    main(sys.argv[1])
