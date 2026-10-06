"""Feasibility check: a tabular foundation model on a stream whose feature space evolves (design and decision rule:
logs/EXPERIMENT_LOG.md, 2026-10-06). Self-contained (TFM wrapper copied from MICE/code/run.py).

A stream = the first NROWS rows of a source stream in their original order. Its non-constant features are split into
three groups: A (observed before the switch only), B (always observed) and C (observed after the switch only). The
switch is at row S = min(10000, n/2). Batches of B rows, labels one batch late, context budget M, TabPFN v2.
Splits per source: three random splits into thirds (seeds 0-2) and "strong": A = the third of the features with the
largest mutual information with the label on the rows before the switch, B and C random from the rest.
Policies after the switch (batch ts is the first batch with a row at or after S; before it every policy is FIFO on A+B):
  union    last M labelled rows, all features A+B+C, unobserved entries NaN (TabPFN handles missing values)
  shared   last M labelled rows, features B only
  new      labelled rows from the switch on, features B+C (the first post-switch batch, which has none, uses shared)
  settled  last M labelled rows, features B+C fully observed, i.e. as if the new feature space had always been there
           (uses the hidden values of C before the switch: the reference for what the transition costs)
  oracle   last M labelled rows, all features fully observed (no evolution; includes the lost features A)
Only batches ts-10 ... ts+59 are predicted (all policies are identical before the switch).
Output: ../results/featevo/<source>__<split>.npz with y and the full probabilities of every policy per predicted batch.
Usage: python check_featevo.py <source> [...]"""
import os
import sys
import time
import warnings

import numpy as np

warnings.filterwarnings("ignore")
DATA, OUT = "../../MICE/data", "../results/featevo"
B, M, NROWS, PRE, POST = 100, 1000, 20_000, 10, 60
POLS = ("union", "shared", "new", "settled", "oracle")
SPLITS = ("r0", "r1", "r2", "strong")


class TFM:
    def __init__(self, K, seed=0):
        from tabpfn import TabPFNClassifier
        from tabpfn.constants import ModelVersion
        self.K = K
        self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed, n_estimators=4,
                                                             ignore_pretraining_limits=True)

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K)); labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0; return P
        self.m.fit(Xc, yc); P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq); return P


def split(X, y, S, kind):
    d = X.shape[1]; idx = np.arange(d)
    if kind == "strong":
        from sklearn.feature_selection import mutual_info_classif
        n = min(S, 5000)
        mi = mutual_info_classif(X[S - n:S], y[S - n:S], random_state=0)
        order = np.argsort(-mi); A = np.sort(order[:d // 3]); rest = np.random.default_rng(99).permutation(order[d // 3:])
        Bf, C = np.sort(rest[:len(rest) // 2]), np.sort(rest[len(rest) // 2:])
    else:
        p = np.random.default_rng(int(kind[1:])).permutation(idx)
        A, Bf, C = np.sort(p[:d // 3]), np.sort(p[d // 3:2 * d // 3]), np.sort(p[2 * d // 3:])
    return A, Bf, C


def run(src, kind, X, y, K):
    dst = f"{OUT}/{src}__{kind}.npz"
    if os.path.exists(dst):
        return
    S = min(10_000, len(y) // 2); T = len(y) // B; ts = -(-S // B)
    A, Bf, C = split(X, y, S, kind)
    Xo = X.copy(); Xo[S:, A] = np.nan; Xo[:S, C] = np.nan      # what is observed
    f = TFM(K); t0 = time.time()
    ts_range = list(range(ts - PRE, min(ts + POST, T)))
    P = {p: np.zeros((len(ts_range), B, K), np.float16) for p in POLS}
    for i, t in enumerate(ts_range):
        lo, hi = max(0, t * B - M), t * B; q = slice(t * B, (t + 1) * B)
        P["oracle"][i] = f.predict(X[lo:hi], y[lo:hi], X[q])
        if t < ts:
            P["settled"][i] = f.predict(X[lo:hi][:, np.r_[Bf, C]], y[lo:hi], X[q][:, np.r_[Bf, C]])
            P["union"][i] = P["shared"][i] = P["new"][i] = f.predict(Xo[lo:hi][:, np.r_[A, Bf]], y[lo:hi], Xo[q][:, np.r_[A, Bf]])
            continue
        P["union"][i] = f.predict(Xo[lo:hi], y[lo:hi], Xo[q])
        P["settled"][i] = f.predict(X[lo:hi][:, np.r_[Bf, C]], y[lo:hi], X[q][:, np.r_[Bf, C]])
        P["shared"][i] = f.predict(X[lo:hi][:, Bf], y[lo:hi], X[q][:, Bf])
        lo_new = max(S, hi - M)
        P["new"][i] = (f.predict(X[lo_new:hi][:, np.r_[Bf, C]], y[lo_new:hi], X[q][:, np.r_[Bf, C]]) if hi - lo_new >= B
                       else P["shared"][i])
    os.makedirs(OUT, exist_ok=True)
    yy = np.stack([y[t * B:(t + 1) * B] for t in ts_range])
    np.savez_compressed(dst, y=yy, t=np.array(ts_range), ts=ts, S=S, A=A, Bf=Bf, C=C, B=B, M=M, **{f"P_{p}": v for p, v in P.items()})
    w = (np.array(ts_range) >= ts) & (np.array(ts_range) < ts + 10)
    acc = {p: 100 * (P[p][w].argmax(2) == yy[w]).mean() for p in POLS}
    print(src, kind, f"|A|={len(A)} |B|={len(Bf)} |C|={len(C)} first 10 after switch:", " ".join(f"{p}={a:.2f}" for p, a in acc.items()),
          f"time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    for src in sys.argv[1:]:
        z = np.load(f"{DATA}/{src}.npz")
        X, y = np.nan_to_num(z["X"][:NROWS].astype(np.float32)), z["y"][:NROWS].astype(int)
        X = X[:, X.std(0) > 0]
        for kind in SPLITS:
            run(src, kind, X, y, int(y.max()) + 1)
