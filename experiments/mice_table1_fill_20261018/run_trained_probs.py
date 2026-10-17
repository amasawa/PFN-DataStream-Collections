"""Table 1 fill (PLAN.md, item 1): the eight trained learners rerun with the same code paths as MICE/code/run_river.py
and MICE/code/run_trained.py, recording per row what each learner can give besides its label. CPU only (stream venv).
- river learners (arf, srp, hat, levbag, adwinbag): p = predict_proba_one(x) and the label max(p, key=p.get), which is
  river's Classifier.predict_one (none of the five overrides it), so the accuracy equals the original runs; when p is
  empty (no prediction) predict_one returns None and pred = -1 here (both count as wrong) and the P row stays 0 (the
  read-out sets such rows uniform). P[i, k] = p.get(k, 0) for the classes 0..C-1 of the stream.
- nse: the weighted votes of Learn++.NSE (NSE._votes with its weights); P = votes / sum (uniform when the sum is 0);
  label = NSE.predict (arg max of the same votes).
- mooe_*: no probability (squared loss on linear outputs). S = the linear outputs Z @ W_mix (the scores whose arg max is
  the label); only rank-based metrics (AUC) may use them.
Output <out>/<stream>__<method>.npz: acc (per batch, NaN at batch 0, as the original), pred (int, rows of batches
1..T-1), P (float32, same rows; river, nse) or S (float32; mooe), C, B. Skipped if present.
Usage: python run_trained_probs.py --data <dir> --out <dir> --streams s1 s2 --methods arf nse ..."""
import argparse, os, sys, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import run_river, run_trained  # noqa: E402
from run_trained import MOOE, NSE, features  # noqa: E402

RIVER = list(run_river.MODELS)


def run(data, stream, method, B, out):
    dst = f"{out}/{stream}__{method}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{data}/{stream}.npz")
    X, y = (z["X"] if method in RIVER else z["X"].astype(float)), z["y"].astype(int)
    C, T = int(y.max()) + 1, len(y) // B
    acc, wt = np.full(T, np.nan), np.zeros(T)
    pred = np.zeros((T - 1) * B, int); P = np.zeros(((T - 1) * B, C), np.float32)
    if method in RIVER:                                   # as run_river.run
        m = run_river.MODELS[method](); rows = [dict(enumerate(map(float, x))) for x in X[:T * B]]
        for t in range(T):
            t0 = time.time(); q = range(t * B, (t + 1) * B)
            if t > 0:
                for i in q:
                    p = m.predict_proba_one(rows[i]); j = i - B
                    pred[j] = max(p, key=p.get) if p else -1
                    for k, v in p.items():
                        P[j, int(k)] = v
                acc[t] = np.mean(pred[(t - 1) * B:t * B] == y[q])
            for i in q:
                m.learn_one(rows[i], int(y[i]))
            wt[t] = time.time() - t0
        extra = dict(P=P)
    else:                                                 # as run_trained.run
        if method.startswith("mooe"):
            _, feat, I, c, g = method.split("_")
            mu, sd = X[:B].mean(0), X[:B].std(0) + 1e-6
            Z = features(feat, X.shape[1])(np.clip((X[:T * B] - mu) / sd, -10, 10))
            m = MOOE(Z.shape[1], C, int(I), float(c), float(g))
        else:
            m, Z = NSE(C), X
        for t in range(T):
            t0 = time.time(); q = slice(t * B, (t + 1) * B); r = slice((t - 1) * B, t * B)
            if t > 0:
                if method.startswith("mooe"):
                    s = Z[q] @ m._mix(); P[r] = s; pred[r] = s.argmax(1)
                    assert (pred[r] == m.predict(Z[q])).all()
                else:
                    V = m._votes(Z[q], m.w) if m.h else np.zeros((B, C)); sv = V.sum(1, keepdims=True)
                    pred[r] = V.argmax(1)                         # = NSE.predict (the same votes, also when empty)
                    P[r] = np.where(sv > 0, V / np.where(sv > 0, sv, 1), 1.0 / C)
                acc[t] = (pred[r] == y[q]).mean()
            m.learn(Z[q], y[q])
            wt[t] = time.time() - t0
        extra = dict(S=P) if method.startswith("mooe") else dict(P=P)
    tmp = dst[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, acc=acc, pred=pred, C=C, B=B, wt=wt, **extra); os.replace(tmp, dst)
    print(stream, method, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+"); ap.add_argument("--B", type=int, default=100)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for me in a.methods:
            run(a.data, s, me, a.B, a.out)
