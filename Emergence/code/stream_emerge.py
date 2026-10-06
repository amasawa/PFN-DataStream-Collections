"""Emergence on real streams (design: logs/EXPERIMENT_LOG.md, 2026-10-06, "流上的 Observation").
A stream = the first NROWS rows of a source stream in their original order, with every row of class c before row T0
removed, so that c emerges at T0 and then arrives at its natural rate. Batches of B rows, labels one batch late,
context budget M. TabPFN v2, 4 estimators, seed 0.
Policies (all but ltm share the FIFO prediction; corrections act on it):
  fifo     last M labelled rows
  ltm      dual memory of Lourenco et al. (KDD 2026), copied from MICE/code/run.py (class-balanced long memory)
  em       Saerens et al. EM prior correction on the unlabelled batch, from the context prior
  rp       recent prior: reweight to the class frequencies of the latest labelled batch, (count + 1) / (B + K)
  rp5      the same with the latest five labelled batches
  oracle   reweight to the true class frequencies of the batch being predicted (upper bound, uses its labels)
Output: ../results/stream_emerge/<source>__c<c>.npz with y, the row index of emergence, n_c (rows of c in the context
per batch) and the full probabilities of every policy per batch (float16), so that any metric can be computed later.
Usage: python stream_emerge.py <source> [...]"""
import os
import sys
import time
import warnings
from collections import deque

import numpy as np

warnings.filterwarnings("ignore")
DATA, OUT = "../../MICE/data", "../results/stream_emerge"
B, M, NROWS, T0, MIN_AFTER = 100, 1000, 20_000, 8_000, 300
SEED = int(os.environ.get("EMERGE_SEED", 0))   # TabPFN initialisation; seeds > 0 write to stream_emerge_s<seed>/
if SEED:
    OUT = f"{OUT}_s{SEED}"
# delay/rarity check (2026-10-06): labels of batch t arrive after batch t+DELAY-1 (DELAY = 1 is the default protocol);
# THIN > 0 keeps each row of c after T0 with a probability that brings its share down to THIN; MIN_AFTER may be lowered
# to take naturally rare classes; NOLTM skips the LTM baseline. Non-default settings write to their own folder.
DELAY, THIN = int(os.environ.get("EMERGE_DELAY", 1)), float(os.environ.get("EMERGE_THIN", 0))
MIN_AFTER = int(os.environ.get("EMERGE_MIN_AFTER", MIN_AFTER)); MAX_AFTER = int(os.environ.get("EMERGE_MAX_AFTER", 10**9))
NOLTM = os.environ.get("EMERGE_NOLTM") == "1"
if DELAY != 1 or THIN or MAX_AFTER < 10**9:
    OUT = f"{OUT}_d{DELAY}" + (f"_thin{THIN:g}" if THIN else "") + ("_rare" if MAX_AFTER < 10**9 else "")
POLS = ("fifo", "ltm", "em", "rp", "rp5", "oracle")


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


class LTM:
    """Lourenco et al. (KDD 2026), Algorithm 1 (copied from MICE/code/run.py)."""

    def __init__(self, M, r=0.75):
        self.Ms, self.Ml = int(round(r * M)), M - int(round(r * M))
        self.S, self.L, self.C = deque(), [], {}

    def add(self, X, y):
        for xi, yi in zip(X, y):
            self.S.append((xi, yi))
            if len(self.S) > self.Ms:
                xo, yo = self.S.popleft(); self.L.append((xo, yo)); self.C[yo] = self.C.get(yo, 0) + 1
            if len(self.L) > self.Ml:
                ymax = max(self.C, key=self.C.get)
                j = next(i for i, (_, yy) in enumerate(self.L) if yy == ymax)
                self.L.pop(j); self.C[ymax] -= 1

    def context(self):
        rows = list(self.S) + self.L
        return np.array([r[0] for r in rows]), np.array([r[1] for r in rows])


def reweight(P, target, prior):
    W = P * (target / np.clip(prior, 1e-9, None)); s = W.sum(1, keepdims=True)
    return np.where(s > 0, W / np.where(s > 0, s, 1), P)


def em_prior(P, prior, it=50):
    q = prior.copy()
    for _ in range(it):
        W = reweight(P, q, prior); q = W.mean(0)
    return W


def run(src, c, X0, y0, K):
    dst = f"{OUT}/{src}__c{c}.npz"
    if os.path.exists(dst):
        return
    keep = ~((np.arange(len(y0)) < T0) & (y0 == c))
    if THIN:
        share = (y0[T0:] == c).mean(); rng = np.random.default_rng(100 + c)
        keep &= ~((np.arange(len(y0)) >= T0) & (y0 == c) & (rng.random(len(y0)) > THIN / share))
    X, y = X0[keep], y0[keep]
    first = int(np.flatnonzero(y == c)[0])
    T = len(y) // B
    f = TFM(K, SEED); ltm = LTM(M)
    P = {p: np.zeros((T, B, K), np.float16) for p in POLS}; n_c = np.zeros(T, int); t0 = time.time()
    for t in range(1, T):
        Xq, yq = X[t * B:(t + 1) * B], y[t * B:(t + 1) * B]
        hi = (t - DELAY + 1) * B                      # labelled rows available: [0, hi)
        if hi <= 0:
            continue
        lo = max(0, hi - M); yc = y[lo:hi]
        Pf = f.predict(X[lo:hi], yc, Xq)
        if not NOLTM:
            ltm.add(X[hi - B:hi], y[hi - B:hi])
        Pl = Pf if NOLTM else f.predict(*ltm.context(), Xq)
        prior = np.bincount(yc, minlength=K) / len(yc)
        last1 = y[hi - B:hi]; last5 = y[max(0, hi - 5 * B):hi]
        P["fifo"][t], P["ltm"][t], P["em"][t] = Pf, Pl, em_prior(Pf, prior)
        P["rp"][t] = reweight(Pf, (np.bincount(last1, minlength=K) + 1) / (len(last1) + K), prior)
        P["rp5"][t] = reweight(Pf, (np.bincount(last5, minlength=K) + 1) / (len(last5) + K), prior)
        P["oracle"][t] = reweight(Pf, (np.bincount(yq, minlength=K) + 1e-3) / (len(yq) + 1e-3 * K), prior)
        n_c[t] = (yc == c).sum()
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(dst, y=y[:T * B].reshape(T, B), c=c, first=first, n_c=n_c, B=B, M=M, delay=DELAY, thin=THIN, **{f"P_{p}": v for p, v in P.items()})
    acc = {p: float((P[p][DELAY:].argmax(2) == y[DELAY * B:T * B].reshape(T - DELAY, B)).mean()) for p in POLS}
    print(src, c, "first", first, " ".join(f"{p}={100 * a:.2f}" for p, a in acc.items()), f"time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    for src in sys.argv[1:]:
        z = np.load(f"{DATA}/{src}.npz")
        X0, y0 = np.nan_to_num(z["X"][:NROWS].astype(np.float32)), z["y"][:NROWS].astype(int)
        K = int(y0.max()) + 1
        for c in range(K):
            if MIN_AFTER <= (y0[T0:] == c).sum() < MAX_AFTER:
                run(src, c, X0, y0, K)
