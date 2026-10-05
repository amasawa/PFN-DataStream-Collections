"""Fourth set of held-out real streams (pre-registration I, see logs/EXPERIMENT_LOG.md): the next segments of the three
long streams that still have rows no method has loaded:
  airlines, poker: rows [300k, 400k) and [400k, 500k) of the files in ../data/external_cdd
  covertype:       rows [350k, 450k) and [450k, 550k)
(INSECTS abrupt_imbalanced has 355,275 rows, of which 350,000 are used; the seven INSECTS variants of river are all in
use.) Written to ../data/h4_<name>_<d|e>.npz. Each segment is checked with a sliding-window random forest against the
majority-class rate before any method sees it. Run with ~/pfn-venvs/stream/bin/python."""
import os
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def source(name):
    if name in ("airlines", "poker"):
        df = pd.read_csv(f"{D}/external_cdd/{name}{'2' if name == 'airlines' else ''}.csv")
        return df.drop(columns="target").to_numpy(np.float32), df.target.to_numpy(), 300_000
    from sklearn.datasets import fetch_covtype
    d = fetch_covtype(); return d.data.astype(np.float32), d.target.astype(int), 350_000


for name in ("airlines", "poker", "covertype"):
    X, t, start = source(name)
    for tag, lo in (("d", start), ("e", start + 100_000)):
        Xs, ts = X[lo:lo + 100_000], t[lo:lo + 100_000]
        labs = sorted(set(ts.tolist())); y = np.array([labs.index(v) for v in ts.tolist()])
        out = f"{D}/h4_{name}_{tag}.npz"
        np.savez_compressed(out, X=Xs, y=y, concept=np.full(len(y), -1))
        T = len(y) // 100; rf, maj = [], []
        for b in range(10, T, 25):
            a, q = slice(b * 100 - 1000, b * 100), slice(b * 100, (b + 1) * 100)
            rf.append((RandomForestClassifier(100, random_state=0, n_jobs=8).fit(Xs[a], y[a]).predict(Xs[q]) == y[q]).mean())
            maj.append((np.bincount(y[a]).argmax() == y[q]).mean())
        print(os.path.basename(out), "rows", lo, "-", lo + len(y), Xs.shape, "classes", len(labs), "NaN", int(np.isnan(Xs).sum()),
              f"sliding RF {np.mean(rf):.3f} vs majority {np.mean(maj):.3f}", flush=True)
