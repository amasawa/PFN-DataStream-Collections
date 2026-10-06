"""Feasibility check for MICE-DUO (design and decision rules: logs/EXPERIMENT_LOG.md, 2026-10-06). Self-contained
(TFM wrapper copied from MICE/code/run.py). Protocol as MICE: batches of B rows, labels one batch late, context budget M,
TabPFN v2 with 4 estimators and seed 0; the first NB batches of each stream.

Two contexts per step t (the latest labelled batch is r = t-1):
  fifo   the last M labelled rows (recency)
  sel    relevance: the candidates are the labelled batches t-H ... t-1; a TFM fitted on batch r alone predicts every
         candidate, and the candidates are ranked by that log-loss (a model-oriented discrepancy to the newest batch, in
         the spirit of R-divergence / WNB: a batch from the same distribution as r is predicted well by r's hypothesis).
         Batch r is always kept; the M/B - 1 best-ranked other batches complete the context.
Predictions:
  fifo, sel, and duo = exponentially weighted mixture of the two (eta 2, discounted log-loss with gamma 0.5 on the
  latest labelled batch, as MICE's window ensemble).
Output: ../results/duo/<stream>.npz with y, the full probabilities of fifo, sel and duo per batch, the mixture weight of
sel, and the selected batch indices. Usage: python check_duo.py <stream> [...]"""
import os
import pickle
import sys
import time
import warnings

import numpy as np

warnings.filterwarnings("ignore")
DATA, OUT = "../../MICE/data", "../results/duo"
B, M, H, NB = 100, 1000, 100, 300


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
        self.m.fit(Xc, yc); cls = self.m.classes_.astype(int)
        for i in range(0, len(Xq), 1000):                             # query in chunks: test rows are independent, and
            P[i:i + 1000, cls] = self.m.predict_proba(Xq[i:i + 1000])  # ~10^4 rows at once filled the 32 GB GPU
        return P


def nll(P, y):
    return float(-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean())


def run(stream):
    dst = f"{OUT}/{stream}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{DATA}/{stream}.npz")
    X, y = z["X"].astype(np.float32), z["y"].astype(int)
    K, T = int(y.max()) + 1, min(NB, len(y) // B)
    f = TFM(K); t0 = time.time()
    P = {k: np.zeros((T, B, K), np.float16) for k in ("fifo", "sel", "duo")}
    wsel, chosen = np.full(T, np.nan), np.full((T, M // B), -1)
    L = {"fifo": 0.0, "sel": 0.0}; prev = None; t_start = 1
    part = f"{OUT}/{stream}.part.pkl"                                 # checkpoint every 20 batches; the TFM is
    if os.path.exists(part):                                          # deterministic given the context, so a resumed
        P, wsel, chosen, L, prev, t_start = pickle.load(open(part, "rb"))  # run equals an uninterrupted one
    for t in range(t_start, T):
        if t % 20 == 0 and t > t_start:
            os.makedirs(OUT, exist_ok=True)
            pickle.dump((P, wsel, chosen, L, prev, t), open(part + ".tmp", "wb")); os.replace(part + ".tmp", part)
        q = slice(t * B, (t + 1) * B)
        if prev is not None:
            yb = y[(t - 1) * B:t * B]
            for k in L:
                L[k] = 0.5 * L[k] + nll(prev[k], yb)
        lo = max(0, t * B - M)
        Pf = f.predict(X[lo:t * B], y[lo:t * B], X[q])
        cands = list(range(max(0, t - H), t - 1))                     # labelled batches other than r = t-1
        if len(cands) <= M // B - 1:
            sel = cands + [t - 1]
        else:
            r = slice((t - 1) * B, t * B)
            idx = np.concatenate([np.arange(b * B, (b + 1) * B) for b in cands])
            Pc = f.predict(X[r], y[r], X[idx])
            loss = -np.log(np.clip(Pc[np.arange(len(idx)), y[idx]], 1e-6, 1)).reshape(len(cands), B).mean(1)
            sel = sorted([cands[i] for i in np.argsort(loss)[:M // B - 1]] + [t - 1])
        rows = np.concatenate([np.arange(b * B, (b + 1) * B) for b in sel])
        Ps = f.predict(X[rows], y[rows], X[q])
        w = np.exp(-2.0 * (np.array([L["fifo"], L["sel"]]) - min(L.values()))); w /= w.sum()
        P["fifo"][t], P["sel"][t], P["duo"][t] = Pf, Ps, w[0] * Pf + w[1] * Ps
        wsel[t] = w[1]; chosen[t, :len(sel)] = sel
        prev = {"fifo": Pf, "sel": Ps}
    os.makedirs(OUT, exist_ok=True)
    yy = y[:T * B].reshape(T, B)
    np.savez_compressed(dst + ".tmp.npz", y=yy, wsel=wsel, chosen=chosen, B=B, M=M, H=H, **{f"P_{k}": v for k, v in P.items()})
    os.replace(dst + ".tmp.npz", dst)
    if os.path.exists(part):
        os.remove(part)
    acc = {k: 100 * (P[k][1:].argmax(2) == yy[1:]).mean() for k in P}
    print(stream, " ".join(f"{k}={a:.2f}" for k, a in acc.items()), f"mean w_sel={np.nanmean(wsel):.2f} time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
