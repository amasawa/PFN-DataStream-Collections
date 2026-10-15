"""TKDE round 14 (method change approved by the user 2026-10-15): grid streams with concept boundaries at arbitrary
phase relative to MICE's 500-row segments. Same generator as MICE/code/grid_streams.py and
experiments/mice_tkde_control/make_misaligned.py (RBF mixture, d=10, 4 classes, K=3 concepts sharing centroids,
concepts recur in order), with `offset` rows of the first concept prepended (auxiliary generator 10_000 + seed, as
make_offset.py) and arbitrary block lengths.
Development set (seeds 0 and 1, the generator's development seeds): see DEV. Test sets are defined in PLAN.md.
Usage: python make_streams.py dev <root>    -> <root>/data/<name>.npz with X, y, concept."""
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mice_tkde_control"))
from make_misaligned import stream  # noqa: E402


def make(nc, blocks, seed, offset, d=10, n_classes=4, K=3, width=0.15):
    X, y, c = stream(nc, blocks, seed)
    if offset == 0:
        return X, y, c
    rng = np.random.default_rng(seed)                         # same draws as stream(): centroids, weights, labels
    C = rng.uniform(0, 1, size=(nc, d))
    w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(n_classes, size=nc) for _ in range(K)]
    aux = np.random.default_rng(10_000 + seed)
    j = aux.choice(nc, offset, p=w)
    Xp = (C[j] + aux.normal(scale=width, size=(offset, d))).astype(np.float32)
    return np.r_[Xp, X], np.r_[lab[0][j], y], np.r_[np.zeros(offset, dtype=c.dtype), c]


def dev():
    """name -> (nc, blocks, seed, offset). Aligned and shifted fixed blocks, and variable blocks with an offset."""
    out = {}
    for s in (0, 1):
        for nc in (30, 100):
            out[f"d_b500_o0_c{nc}_s{s}"] = (nc, [500] * 9, s, 0)
            out[f"d_b500_o200_c{nc}_s{s}"] = (nc, [500] * 9, s, 200)
            out[f"d_b2000_o0_c{nc}_s{s}"] = (nc, [2000] * 9, s, 0)
            out[f"d_b2000_o300_c{nc}_s{s}"] = (nc, [2000] * 9, s, 300)
            r = np.random.default_rng(2000 + 10 * s + nc)
            out[f"d_bvar_o100_c{nc}_s{s}"] = (nc, [int(b) for b in r.choice(np.arange(500, 2501, 100), size=9)], s, 100)
    return out


def dev2():
    """Development streams with boundaries inside batches (row-granularity offsets and block lengths)."""
    out = {}
    for s in (0, 1):
        for nc in (30, 100):
            out[f"d_b500_o250_c{nc}_s{s}"] = (nc, [500] * 9, s, 250)
            out[f"d_b2000_o1170_c{nc}_s{s}"] = (nc, [2000] * 9, s, 1170)
            r = np.random.default_rng(3000 + 10 * s + nc)
            out[f"d_bvarr_o37_c{nc}_s{s}"] = (nc, [int(b) for b in r.integers(500, 2501, size=9)], s, 37)
    return out


if __name__ == "__main__":
    which, root = sys.argv[1], Path(sys.argv[2])
    spec = dev() if which == "dev" else dev2() if which == "dev2" else None
    (root / "data").mkdir(parents=True, exist_ok=True)
    for name, (nc, blocks, s, off) in spec.items():
        f = root / "data" / f"{name}.npz"
        if f.exists():
            continue
        X, y, concept = make(nc, blocks, s, off)
        np.savez_compressed(f, X=X, y=y, concept=concept)
        with open(root / "data" / "manifest.txt", "a") as fh:
            fh.write(f"{name} blocks={blocks} offset={off} sha256={hashlib.sha256(f.read_bytes()).hexdigest()}\n")
        print(name, X.shape, blocks, off)
