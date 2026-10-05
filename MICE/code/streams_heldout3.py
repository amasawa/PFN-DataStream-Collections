"""Third set of held-out real streams (pre-registration H, see logs/EXPERIMENT_LOG.md): the LATER segments of the four
streams that were cut to their first rows in pre-registrations C and G, i.e. rows never loaded by any method:
  airlines, poker: rows [100k, 200k) and [200k, 300k) of the files in ../data/external_cdd
  covertype, insects_abrupt_imbalanced: rows [150k, 250k) and [250k, 350k)
Written to ../data/h3_<name>_<b|c>.npz. Each segment is checked with a sliding-window random forest against the
majority-class rate before any method sees it."""
import itertools, os
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from streams import to_row

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def source(name):
    if name in ("airlines", "poker"):
        df = pd.read_csv(f"{D}/external_cdd/{name}{'2' if name == 'airlines' else ''}.csv")
        return df.drop(columns="target").to_numpy(np.float32), df.target.to_numpy(), 100_000
    if name == "covertype":
        from sklearn.datasets import fetch_covtype
        d = fetch_covtype(); return d.data.astype(np.float32), d.target.astype(int), 150_000
    from river import datasets
    rows = list(itertools.islice(datasets.Insects(variant="abrupt_imbalanced"), 350_000))
    return np.asarray([to_row(x) for x, _ in rows], np.float32), np.asarray([t for _, t in rows]), 150_000


for name in ("airlines", "poker", "covertype", "insects"):
    X, t, start = source(name)
    for tag, lo in (("b", start), ("c", start + 100_000)):
        Xs, ts = X[lo:lo + 100_000], t[lo:lo + 100_000]
        labs = sorted(set(ts.tolist())); y = np.array([labs.index(v) for v in ts.tolist()])
        out = f"{D}/h3_{name}_{tag}.npz"
        np.savez_compressed(out, X=Xs, y=y, concept=np.full(len(y), -1))
        T = len(y) // 100; rf, maj = [], []
        for b in range(10, T, 25):
            a, q = slice(b * 100 - 1000, b * 100), slice(b * 100, (b + 1) * 100)
            rf.append((RandomForestClassifier(100, random_state=0, n_jobs=8).fit(Xs[a], y[a]).predict(Xs[q]) == y[q]).mean())
            maj.append((np.bincount(y[a]).argmax() == y[q]).mean())
        print(os.path.basename(out), "rows", lo, "-", lo + len(y), Xs.shape, "classes", len(labs), "NaN", int(np.isnan(Xs).sum()),
              f"sliding RF {np.mean(rf):.3f} vs majority {np.mean(maj):.3f}", flush=True)
