"""Held-out real streams (run with ~/pfn-venvs/stream/bin/python): the INSECTS variants never used so far and the
Forest Covertype stream, written to ../data/<name>.npz in the format of streams.py. Streams longer than CAP rows are
cut to their first CAP rows (fixed before any model is run; see logs/EXPERIMENT_LOG.md, pre-registration C). After
writing, each stream is checked with a sliding-window random forest against the majority-class rate, so that a broken
feature parse (as in the hashed INSECTS files) is caught before any method sees the data."""
import itertools
import os

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from streams import OUT, to_row

CAP = 150_000


def insects(v):
    from river import datasets
    rows = list(itertools.islice(datasets.Insects(variant=v), CAP))
    labs = sorted({t for _, t in rows})
    return np.asarray([to_row(x) for x, _ in rows], np.float32), np.asarray([labs.index(t) for _, t in rows])


def covertype():
    from sklearn.datasets import fetch_covtype
    d = fetch_covtype()  # rows in the original file order, the order used as a stream in the drift literature
    return d.data[:CAP].astype(np.float32), d.target[:CAP].astype(int) - 1


def check(X, y, B=100, M=1000, step=20):
    acc, maj = [], []
    for t in range(M // B, len(y) // B, step):
        Xc, yc = X[t * B - M:t * B], y[t * B - M:t * B]
        q = slice(t * B, (t + 1) * B)
        acc.append((RandomForestClassifier(50, random_state=0).fit(Xc, yc).predict(X[q]) == y[q]).mean())
        maj.append((y[q] == np.bincount(yc).argmax()).mean())
    return np.mean(acc), np.mean(maj)


if __name__ == "__main__":
    jobs = {"insects_incremental_abrupt_balanced": lambda: insects("incremental_abrupt_balanced"),
            "insects_gradual_imbalanced": lambda: insects("gradual_imbalanced"),
            "insects_abrupt_imbalanced": lambda: insects("abrupt_imbalanced"),
            "covertype": covertype}
    for name, fn in jobs.items():
        f = f"{OUT}/{name}.npz"
        try:
            if not os.path.exists(f):
                X, y = fn()
                np.savez_compressed(f, X=X, y=y, concept=-np.ones(len(y), int))
            z = np.load(f)
            X, y = z["X"], z["y"]
            a, m = check(X, y)
            print(name, X.shape, "classes", np.bincount(y).tolist(), "nan", int(np.isnan(X).sum()),
                  f"sliding RF acc={a:.3f} majority={m:.3f}", flush=True)
        except Exception as e:  # download problems are reported, not hidden
            print(name, "failed:", repr(e), flush=True)
