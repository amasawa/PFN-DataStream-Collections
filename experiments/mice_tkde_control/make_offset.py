"""Round-4 attempt 4.b (TKDE review): boundary alignment at fixed block length, paired with the aligned grid.

For each aligned confirmatory grid stream (data seeds 20 and 21; 30 and 100 centroids; blocks of 500 and 2000 rows;
K=3; three cycles) the aligned observations are kept unchanged (generator of make_misaligned.stream with the same
seed, which reproduces MICE/code/grid_streams.py bit for bit) and OFFSET=200 rows of the first concept are
prepended, drawn with an auxiliary generator default_rng(10_000 + seed) from the same centroids, weights and labels.
Every later boundary then falls 200 rows into a 500-row segment, while batch boundaries (100 rows) stay aligned and
all recurring blocks keep their length. Offset batch t+2 holds exactly the rows of aligned batch t.
Writes <root>/data/off_c<nc>_b<block>_s<seed>.npz with X, y, concept.
"""
import hashlib
from pathlib import Path
import sys

import numpy as np

from make_misaligned import stream

OFFSET = 200


def offset_stream(nc, block, seed, offset=OFFSET, d=10, n_classes=4, K=3, width=0.15):
    X, y, c = stream(nc, [block] * 3 * K, seed)              # aligned observations, unchanged
    rng = np.random.default_rng(seed)                         # same draws as stream(): centroids, weights, labels
    C = rng.uniform(0, 1, size=(nc, d))
    w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(n_classes, size=nc) for _ in range(K)]
    aux = np.random.default_rng(10_000 + seed)
    j = aux.choice(nc, offset, p=w)
    Xp = (C[j] + aux.normal(scale=width, size=(offset, d))).astype(np.float32)
    return np.r_[Xp, X], np.r_[lab[0][j], y], np.r_[np.zeros(offset, dtype=c.dtype), c]


def names():
    return [f"off_c{nc}_b{b}_s{s}" for nc in (30, 100) for b in (500, 2000) for s in (20, 21)]


def main(root):
    out = Path(root) / "data"
    for name in names():
        _, c, b, s = name.split("_")
        X, y, concept = offset_stream(int(c[1:]), int(b[1:]), int(s[1:]))
        z = np.load(out / f"grid_{c}_{b}_{s}.npz")            # the aligned file the existing results were computed on
        assert all(np.array_equal(a, z[k]) for a, k in ((X[OFFSET:], "X"), (y[OFFSET:], "y"), (concept[OFFSET:], "concept"))), name
        assert OFFSET % 100 == 0 and int(b[1:]) % 100 == 0                     # batch size B=100 frozen for 4.b
        np.savez_compressed(out / f"{name}.npz", X=X, y=y, concept=concept)
        digest = hashlib.sha256((out / f"{name}.npz").read_bytes()).hexdigest()
        with open(out / "offset_manifest.txt", "a") as fh:
            fh.write(f"{name} sha256={digest} numpy={np.__version__} aligned=grid_{c}_{b}_{s}.npz rows_200+_identical=True\n")
        print(name, X.shape, digest[:12])


if __name__ == "__main__":
    main(sys.argv[1])
