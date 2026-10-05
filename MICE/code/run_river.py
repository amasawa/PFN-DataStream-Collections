"""Incremental stream learners from river as baselines, under the same protocol as run.py: batches of B rows, the
labels of a batch arrive after the batch is predicted (predict batch t with a model that has learned batches < t),
batch 0 is warm-up and not scored. Usage (stream venv): python run_river.py --streams s1 s2 --methods arf srp --out dir"""
import argparse, os, time
import numpy as np
from river import forest, ensemble, tree

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
MODELS = {"arf": lambda: forest.ARFClassifier(n_models=10, seed=0),
          "srp": lambda: ensemble.SRPClassifier(n_models=10, seed=0),
          "hat": lambda: tree.HoeffdingAdaptiveTreeClassifier(seed=0),
          "levbag": lambda: ensemble.LeveragingBaggingClassifier(tree.HoeffdingTreeClassifier(), n_models=10, seed=0),
          "adwinbag": lambda: ensemble.ADWINBaggingClassifier(tree.HoeffdingTreeClassifier(), n_models=10, seed=0)}


def run(stream, method, B, out):
    dst = f"{out}/{stream}__{method}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{DATA}/{stream}.npz"); X, y, concept = z["X"], z["y"].astype(int), z["concept"]
    T = len(y) // B; m = MODELS[method](); acc, wt = np.full(T, np.nan), np.zeros(T)
    rows = [dict(enumerate(map(float, x))) for x in X[:T * B]]
    for t in range(T):
        t0 = time.time(); q = range(t * B, (t + 1) * B)
        if t > 0:
            acc[t] = np.mean([m.predict_one(rows[i]) == y[i] for i in q])
        for i in q:
            m.learn_one(rows[i], int(y[i]))
        wt[t] = time.time() - t0
    np.savez_compressed(dst, acc=acc, ll=np.full(T, np.nan), wt=wt, B=B, concept=concept, calls=0, n_experts=0)
    print(stream, method, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+", default=["arf", "srp"])
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_test")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for me in a.methods:
            run(s, me, a.B, a.out)
