"""Metrics beyond accuracy for every finished (backbone, stream, policy), replayed from the prediction caches.

reset_eval.py stored only per-batch accuracy and log-loss. The policies are deterministic given the cached TFM
predictions, so each policy is replayed here with the same code path and its per-row probabilities are recovered;
a key missing from the cache is recomputed with the TFM (counted). The replay is checked against the stored per-batch accuracy.
Metrics over all scored rows (batches 1..T-1): accuracy, macro-F1, macro one-vs-rest ROC AUC (classes present in the
stream), ECE (15 equal-width bins, top label), log-loss, Brier score, mean predictive entropy.
Probabilities (float16, per row) are saved for the main configuration (TabPFN, seed 0, M 1000) only.
Usage: RESET_BACKBONE=.. RESET_SEED=.. RESET_M=.. RESET_DATA=.. python metrics_replay.py <stream> [...]
  -> ../results/metrics/<tag>_M<M>/<stream>.csv (and ../results/probs_tabpfn_M1000/<stream>__<pol>.npz)"""
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

import reset_eval as r


class NoMiss(r.Cache):
    """A miss (a key lost when two processes saved the same cache before saves merged, 2026-10-07 06:22) is recomputed:
    the TFM is deterministic given the context, and the replay check below confirms the result."""
    def get(self, lo, t):
        if (int(lo), int(t)) not in self.d:
            self.miss = getattr(self, "miss", 0) + 1
        return super().get(lo, t)


def replay(pol, cache, X, y):
    """reset_eval.run without writing; returns the (T, B, K) probabilities (row 0 unused) and the reset batches."""
    B, M = r.B, r.M
    det_name, _, var = pol.partition("+")
    hedge = var.startswith("hedge")
    eta, gam = (float(v) for v in var[7:].split("g")) if "@" in var else (2.0, 0.5)
    T = len(y) // B
    det = r.DDMCopy() if pol == "ddmM" else None if pol == "none" else r.DETS[det_name]()
    start, resets, errs, L, Pq = 0, [], None, {"fifo": 0.0, "reset": 0.0}, None
    out = np.zeros((T, B, cache.K))
    for t in range(1, T):
        yq = y[t * B:(t + 1) * B]
        if errs is not None and det is not None:
            if Pq is not None and hedge:
                yb = y[(t - 1) * B:t * B]
                for k, P in Pq.items():
                    L[k] = gam * L[k] - np.log(np.clip(P[np.arange(B), yb], 1e-6, 1)).mean()
            for e in errs:
                if isinstance(det, r.DDMCopy):
                    hit = det.feed(int(e))
                else:
                    det.update(bool(e) if det_name in ("ddm", "eddm", "fhddm", "hddma", "hddmw") else float(e))
                    hit = det.drift_detected
                if hit:
                    start = t * B - M // 2 if var == "half" else (t - 1) * B
                    resets.append(t)
                    if hedge:
                        L["reset"] = L["fifo"]
                    break
        lo_f = max(0, t * B - M)
        lo = max(start, lo_f)
        if hedge:
            Pq = {"fifo": cache.get(lo_f, t), "reset": cache.get(lo, t)}
            w = np.exp(-eta * (np.array([L["fifo"], L["reset"]]) - min(L.values()))); w /= w.sum()
            P = w[0] * Pq["fifo"] + w[1] * Pq["reset"]
        else:
            P = cache.get(lo, t)
        P = P / P.sum(1, keepdims=True)
        out[t] = P
        errs = (P.argmax(1) != yq).astype(int)
    return out, resets


def metrics(P, y):
    pred = P.argmax(1); conf = P.max(1); n = len(y)
    bins = np.minimum((conf * 15).astype(int), 14)
    ece = sum(abs((pred[bins == b] == y[bins == b]).mean() - conf[bins == b].mean()) * (bins == b).sum() / n
              for b in range(15) if (bins == b).any())
    present = [k for k in np.unique(y) if 0 < (y == k).sum() < n]
    aucs = [roc_auc_score(y == k, P[:, k]) for k in present]
    onehot = np.eye(P.shape[1])[y]
    return dict(acc=100 * (pred == y).mean(), f1=100 * f1_score(y, pred, average="macro", labels=np.unique(y)),
                auc=100 * np.mean(aucs) if aucs else np.nan, ece=100 * ece,
                logloss=-np.log(np.clip(P[np.arange(n), y], 1e-6, 1)).mean(),
                brier=((P - onehot) ** 2).sum(1).mean(), entropy=-(P * np.log(np.clip(P, 1e-12, 1))).sum(1).mean())


if __name__ == "__main__":
    pols = r.POLSETS[os.environ.get("RESET_POLSET", "std")]
    tag = f"{r.TAG}_M{r.M}"; main = tag == "tabpfn_M1000"
    os.makedirs(f"{r.RES}/metrics/{tag}", exist_ok=True)
    for s in sys.argv[1:]:
        dst = f"{r.RES}/metrics/{tag}/{s}.csv"
        if os.path.exists(dst):
            continue
        z = np.load(f"{r.DATA}/{s}.npz"); X, y = z["X"], z["y"].astype(int)
        cache = NoMiss(s, X, y, int(y.max()) + 1); T = len(y) // r.B; yy = y[r.B:T * r.B]
        rows = []
        for p in pols:
            P, res = replay(p, cache, X, y)
            stored = np.load(f"{r.RES}/{tag}/{s}__{p}.npz")
            acc_b = (P[1:].argmax(2) == y[r.B:T * r.B].reshape(T - 1, r.B)).mean(1)
            assert np.allclose(acc_b, stored["acc"][1:]) and list(stored["resets"]) == res, f"replay mismatch {s} {p}"
            Pf = P[1:].reshape(-1, cache.K)
            rows.append(dict(stream=s, pol=p, resets=len(res), **metrics(Pf, yy)))
            if main:
                os.makedirs(f"{r.RES}/probs_tabpfn_M1000", exist_ok=True)
                np.savez_compressed(f"{r.RES}/probs_tabpfn_M1000/{s}__{p}.npz", P=Pf.astype(np.float16), y=yy)
        pd.DataFrame(rows).to_csv(dst, index=False)
        if cache.new:
            cache.save()
        print(tag, s, "ok", f"recomputed={getattr(cache, 'miss', 0)}", flush=True)
