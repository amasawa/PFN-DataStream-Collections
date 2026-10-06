"""Contrast for RQ2: the same error-driven resets on trained incremental learners (design: logs/EXPERIMENT_LOG.md).

Same protocol as reset_eval.py: batches of B = 100 rows, batch t is predicted by a model that has learned batches < t
(labels one batch late), batch 0 is not scored; the detector is fed the per-row 0/1 errors of the policy's own previous
batch and fires at most once per batch.
Models (river 0.26.1, default parameters): ht = HoeffdingTreeClassifier, nb = GaussianNB.
Policies (name):
  none          one model, never reset
  <det>         full reset: on detection the model is replaced by a fresh one, which then learns from the latest
                labelled batch on (the analogue of restarting the TFM context at the latest labelled batch)
  <det>+hedge   the never-reset model and the reset model are both kept; prediction = exponentially weighted mixture
                with the rule of reset_eval.py (eta 2, discounted log-loss with gamma 0.5); a detection replaces the reset
                model and sets its loss to that of the never-reset one
Usage: python trained_eval.py <model> <stream> [...] -> ../results/trained_<model>/<stream>__<pol>.npz
Environment: RESET_DATA (stream directory, default MICE/data)."""
import os
import sys
import time

import numpy as np
from river.naive_bayes import GaussianNB
from river.tree import HoeffdingTreeClassifier

from reset_eval import B, DATA, DETS, RES

MODELS = {"ht": HoeffdingTreeClassifier, "nb": GaussianNB}
POLS = ["none"] + [d + v for d in DETS for v in ("", "+hedge")]


def proba(m, Xb, K):
    P = np.zeros((len(Xb), K))
    for i, x in enumerate(Xb):
        for k, p in m.predict_proba_one(x).items():
            if 0 <= int(k) < K:
                P[i, int(k)] = p
    s = P.sum(1, keepdims=True)
    return np.where(s > 0, P / np.where(s > 0, s, 1), 1.0 / K)


def run(model, stream, pol, X, y, K):
    out = f"{RES}/trained_{model}"
    dst = f"{out}/{stream}__{pol}.npz"
    if os.path.exists(dst):
        return
    det_name, _, var = pol.partition("+")
    hedge = var == "hedge"
    T = len(y) // B
    acc, ll = np.full(T, np.nan), np.full(T, np.nan)
    det = None if pol == "none" else DETS[det_name]()
    ms = {"fifo": MODELS[model]()} | ({"reset": MODELS[model]()} if hedge else {})
    L, resets, t0 = {k: 0.0 for k in ms}, [], time.time()
    rows = [[dict(enumerate(r)) for r in X[t * B:(t + 1) * B]] for t in range(T)]
    for t in range(T):
        yq = y[t * B:(t + 1) * B]
        if t > 0:
            Pq = {k: proba(m, rows[t], K) for k, m in ms.items()}
            if hedge:
                w = np.exp(-2.0 * (np.array([L["fifo"], L["reset"]]) - min(L.values()))); w /= w.sum()
                P = w[0] * Pq["fifo"] + w[1] * Pq["reset"]
                for k in ms:
                    L[k] = 0.5 * L[k] - np.log(np.clip(Pq[k][np.arange(len(yq)), yq], 1e-6, 1)).mean()
            else:
                P = Pq["fifo"]
            errs = (P.argmax(1) != yq).astype(int)
            acc[t] = 1 - errs.mean()
            ll[t] = -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)).mean()
            if det is not None:
                for e in errs:
                    det.update(bool(e) if det_name in ("ddm", "eddm", "fhddm", "hddma", "hddmw") else float(e))
                    if det.drift_detected:
                        resets.append(t + 1)          # same convention as reset_eval.py: the batch first served after it
                        k = "reset" if hedge else "fifo"
                        ms[k] = MODELS[model]()
                        if hedge:
                            L["reset"] = L["fifo"]
                        break
        for x, yi in zip(rows[t], yq):                # labels of batch t arrive before batch t + 1 is predicted
            for m in ms.values():
                m.learn_one(x, int(yi))
    os.makedirs(out, exist_ok=True)
    np.savez_compressed(dst, acc=acc, ll=ll, resets=np.array(resets, int), B=B)
    print(model, stream, pol, f"acc={np.nanmean(acc):.4f} resets={len(resets)} time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    model = sys.argv[1]
    for s in sys.argv[2:]:
        z = np.load(f"{DATA}/{s}.npz")
        X, y = z["X"], z["y"].astype(int)
        for p in POLS:
            run(model, s, p, X, y, int(y.max()) + 1)
