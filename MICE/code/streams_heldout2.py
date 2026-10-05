"""Second set of held-out real streams (pre-registration G, see logs/EXPERIMENT_LOG.md): every real-world stream of
github.com/ogozuacik/concept-drift-datasets-scikit-multiflow with at least 5000 rows and at most 10 classes that has
not been used before (covtype and elec are excluded), in file order, cut to the first CAP rows. Written to
../data/h2_<name>.npz in the format of streams.py. Each stream is then checked with a sliding-window random forest
against the majority-class rate, before any method sees the data."""
import os
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
CAP = 100_000
for name in ("airlines2", "phishing", "poker", "rialto", "spam", "weather"):
    df = pd.read_csv(f"{D}/external_cdd/{name}.csv").iloc[:CAP]
    X = df.drop(columns="target").to_numpy(np.float32)
    labs = sorted(df.target.unique()); y = df.target.map({l: i for i, l in enumerate(labs)}).to_numpy()
    out = f"{D}/h2_{name.replace('2', '')}.npz"
    np.savez_compressed(out, X=X, y=y, concept=np.full(len(y), -1))
    T = len(y) // 100; rf, maj = [], []
    for t in range(10, T, max(1, T // 40)):   # about 40 batches: forest on the previous 1000 rows against the majority
        a, b = slice(max(0, t * 100 - 1000), t * 100), slice(t * 100, (t + 1) * 100)
        rf.append((RandomForestClassifier(100, random_state=0, n_jobs=8).fit(X[a], y[a]).predict(X[b]) == y[b]).mean())
        maj.append((np.bincount(y[a]).argmax() == y[b]).mean())
    print(os.path.basename(out), X.shape, "classes", len(labs), "NaN", int(np.isnan(X).sum()),
          f"sliding RF {np.mean(rf):.3f} vs majority {np.mean(maj):.3f}", flush=True)
