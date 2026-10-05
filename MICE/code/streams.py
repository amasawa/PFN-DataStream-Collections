"""Streams for MICE (run with ~/pfn-venvs/stream/bin/python): synthetic streams with recurring concepts and real
streams, written to ../data/<name>.npz with X (float32), y (int), concept (int, -1 if unknown).

Synthetic recurring streams: a generator family with K concepts; the schedule visits the concepts in blocks of
`block` rows, cycling `cycles` times (0,1,...,K-1,0,1,...). Each concept is a fixed river generator; drawing from a
concept continues its own random stream, so a recurring concept has the same distribution, not the same rows.
Seeds: dev streams use seeds 0-2, test streams 10-14 (fixed before any model is run; see logs/EXPERIMENT_LOG.md).
Usage: python streams.py [--seeds 0 1 2] [--real]
"""
import argparse
import os

import numpy as np
from river.datasets import synth

OUT = os.path.join(os.path.dirname(__file__), "..", "data")


def families(seed):
    """name -> list of K concept generators (each an infinite river iterator)."""
    return {
        # P(x) identical across concepts, only the labelling function changes (real drift only)
        "sea": [synth.SEA(variant=v, seed=seed * 10 + v) for v in (0, 1, 2)],
        "stagger": [synth.STAGGER(classification_function=f, seed=seed * 10 + f) for f in (0, 1, 2)],
        "agrawal": [synth.Agrawal(classification_function=f, seed=seed * 10 + f) for f in (0, 2, 4, 6)],
        "sine": [synth.Sine(classification_function=f, seed=seed * 10 + f) for f in (0, 1, 2, 3)],
        # P(x) and P(y|x) change: each concept has its own centroids
        "rbf": [synth.RandomRBF(seed_model=seed * 10 + k, seed_sample=seed * 10 + k, n_classes=4, n_features=10,
                                n_centroids=20) for k in range(3)],
        "hyperplane": [synth.Hyperplane(seed=seed * 10 + k, n_features=10, n_drift_features=0, noise_percentage=0.05)
                       for k in range(3)],
    }


def to_row(x):
    # river yields the INSECTS features as numeric strings; they must be parsed, not hashed
    return [float(v) for _, v in sorted(x.items())]


def recurring(gens, block, cycles):
    its = [iter(g) for g in gens]
    X, y, c = [], [], []
    for _ in range(cycles):
        for k, it in enumerate(its):
            for _ in range(block):
                xi, yi = next(it)
                X.append(to_row(xi)), y.append(int(yi)), c.append(k)
    return np.asarray(X, np.float32), np.asarray(y), np.asarray(c)


def real():
    from river import datasets
    out = {}
    try:
        X, y = zip(*[(to_row(x), int(t)) for x, t in datasets.Elec2()])
        out["elec2"] = (np.asarray(X, np.float32), np.asarray(y))
    except Exception as e:  # download problems are reported, not hidden
        print("elec2 failed:", e)
    for v in ("abrupt_balanced", "gradual_balanced", "incremental_reoccurring_balanced", "incremental_balanced"):
        try:
            rows = list(datasets.Insects(variant=v))
            labs = sorted({t for _, t in rows})
            X = np.asarray([to_row(x) for x, _ in rows], np.float32)
            y = np.asarray([labs.index(t) for _, t in rows])
            out["insects_" + v.replace("-", "_")] = (X, y)
        except Exception as e:
            print("insects", v, "failed:", e)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--block", type=int, default=2000)
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--real", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    for s in a.seeds:
        for name, gens in families(s).items():
            f = f"{OUT}/{name}_s{s}.npz"
            if os.path.exists(f):
                continue
            X, y, c = recurring(gens, a.block, a.cycles)
            np.savez_compressed(f, X=X, y=y, concept=c)
            print(name, s, X.shape, np.bincount(y))
    if a.real:
        for name, (X, y) in real().items():
            np.savez_compressed(f"{OUT}/{name}.npz", X=X, y=y, concept=-np.ones(len(y), int))
            print(name, X.shape, np.bincount(y))
