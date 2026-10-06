"""Error-driven context resets for a frozen tabular foundation model (TFM) on a data stream (design: logs/EXPERIMENT_LOG.md).

Protocol (as MICE/code/run.py, from which the TFM wrapper and the DDM copy are taken): the stream is cut into batches of
B rows; batch t is predicted from labelled rows of batches < t (labels arrive one batch late); batch 0 is not scored.
The context is always a contiguous window [lo, t*B) of at most M rows, so every prediction is identified by (lo, t).
Predictions are cached per (backbone, stream) under that key and shared by all policies: the TFM is deterministic given
the context, so a cached prediction is the prediction the policy would have obtained.

Policies (name):
  none              FIFO, last M rows, never reset
  <det>             full reset: on detection the context restarts at the latest labelled batch
  <det>+half        partial reset: on detection the context keeps only the latest M/2 labelled rows
  <det>+hedge       the reset context and the FIFO context are both kept; prediction = exponentially weighted mixture
                    (eta 2, discounted log-loss with gamma 0.5, as MICE's window ensemble); a detection restarts the reset
                    context and sets its loss to that of FIFO
  ddmM              the DDM copy of MICE/code/run.py (consistency check against MICE's ddm1000 results)
Detectors <det> (river 0.26.1, default parameters; input = per-row 0/1 error of the policy's own prediction):
  ddm eddm fhddm hddma hddmw adwin ph kswin
At most one detection per labelled batch (the rest of the batch is not fed after a detection), as in MICE.
Environment: RESET_BACKBONE=tabpfn|tabicl, RESET_M (default 1000), RESET_DATA (stream directory, default MICE/data),
RESET_SEED (backbone random_state, default 0; seed s > 0 writes to <backbone>_s<s>_M<M> and cache_<backbone>_s<s>).
Usage: python reset_eval.py <stream> [...] [--pols none ddm ...] -> ../results/<backbone>_M<M>/<stream>__<pol>.npz"""
import argparse
import os
import pickle
import sys
import time

import numpy as np

sys.path.append(os.path.expanduser("~/pfn-venvs/stream/lib/python3.12/site-packages"))  # river only; appended last
from river.drift import ADWIN, KSWIN, PageHinkley
from river.drift.binary import DDM, EDDM, FHDDM, HDDMA, HDDMW

DATA = os.environ.get("RESET_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "data"))
RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
B, M = 100, int(os.environ.get("RESET_M", 1000))
BB = os.environ.get("RESET_BACKBONE", "tabpfn")
SEED = int(os.environ.get("RESET_SEED", 0))                       # backbone random_state; 0 keeps the original paths
TAG = BB if SEED == 0 else f"{BB}_s{SEED}"
DETS = {"ddm": DDM, "eddm": EDDM, "fhddm": FHDDM, "hddma": HDDMA, "hddmw": HDDMW, "adwin": ADWIN, "ph": PageHinkley,
        "kswin": lambda: KSWIN(seed=0)}
POLS = ["none", "ddmM"] + [d + v for d in DETS for v in ("", "+half", "+hedge")]


class TFM:
    """Frozen backbone (copied from MICE/code/run.py)."""

    def __init__(self, n_classes, seed=0):
        self.K = n_classes
        if BB == "tabicl":
            from tabicl import TabICLClassifier
            self.m = TabICLClassifier(device="cuda", random_state=seed, n_estimators=4)
        else:
            from tabpfn import TabPFNClassifier
            from tabpfn.constants import ModelVersion
            self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed,
                                                                 n_estimators=4, ignore_pretraining_limits=True)

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K))
        labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0
            return P
        self.m.fit(Xc, yc)
        if self.m.__class__.__name__ == "TabICLClassifier":
            self.m._load_model = lambda: None
        P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq)
        return P


class Cache:
    def __init__(self, stream, X, y, K):
        self.path = f"{RES}/cache_{TAG}/{stream}.pkl"
        self.X, self.y, self.K, self.f, self.new = X, y, K, None, 0
        self.d = pickle.load(open(self.path, "rb")) if os.path.exists(self.path) else {}

    def get(self, lo, t):
        key = (int(lo), int(t))
        if key not in self.d:
            if self.f is None:
                self.f = TFM(self.K, seed=SEED)
            self.d[key] = self.f.predict(self.X[lo:t * B], self.y[lo:t * B], self.X[t * B:(t + 1) * B]).astype(np.float16)
            self.new += 1
            if self.new % 200 == 0:
                self.save()
        return self.d[key].astype(np.float64)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        pickle.dump(self.d, open(self.path + ".tmp", "wb"))
        os.replace(self.path + ".tmp", self.path)


class DDMCopy:
    """MICE/code/run.py DDMReset, detector part only."""

    def __init__(self):
        self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf

    def feed(self, e):
        self.n += 1; self.err += e
        p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
        if self.n >= 30 and p + s < self.pmin + self.smin:
            self.pmin, self.smin = p, s
        if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
            self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf
            return True
        return False


def run(stream, pol, cache, X, y):
    out = f"{RES}/{TAG}_M{M}"
    dst = f"{out}/{stream}__{pol}.npz"
    if os.path.exists(dst):
        return
    det_name, _, var = pol.partition("+")
    T = len(y) // B
    acc, ll, lo_used = np.full(T, np.nan), np.full(T, np.nan), np.zeros(T, int)
    det = DDMCopy() if pol == "ddmM" else None if pol == "none" else DETS[det_name]()
    start, resets, errs, L, Pq = 0, [], None, {"fifo": 0.0, "reset": 0.0}, None
    t0 = time.time()
    for t in range(1, T):
        yq = y[t * B:(t + 1) * B]
        if errs is not None and det is not None:
            if Pq is not None and var == "hedge":
                yb = y[(t - 1) * B:t * B]
                for k, P in Pq.items():
                    L[k] = 0.5 * L[k] - np.log(np.clip(P[np.arange(B), yb], 1e-6, 1)).mean()
            for e in errs:
                if isinstance(det, DDMCopy):
                    hit = det.feed(int(e))
                else:
                    det.update(bool(e) if det_name in ("ddm", "eddm", "fhddm", "hddma", "hddmw") else float(e))
                    hit = det.drift_detected
                if hit:
                    start = t * B - M // 2 if var == "half" else (t - 1) * B
                    resets.append(t)
                    if var == "hedge":
                        L["reset"] = L["fifo"]
                    break
        lo_f = max(0, t * B - M)
        lo = max(start, lo_f)
        if var == "hedge":
            Pq = {"fifo": cache.get(lo_f, t), "reset": cache.get(lo, t)}
            w = np.exp(-2.0 * (np.array([L["fifo"], L["reset"]]) - min(L.values()))); w /= w.sum()
            P = w[0] * Pq["fifo"] + w[1] * Pq["reset"]
        else:
            P = cache.get(lo, t)
        P = P / P.sum(1, keepdims=True)
        lo_used[t] = lo
        errs = (P.argmax(1) != yq).astype(int)
        acc[t] = 1 - errs.mean()
        ll[t] = -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)).mean()
    os.makedirs(out, exist_ok=True)
    np.savez_compressed(dst, acc=acc, ll=ll, lo=lo_used, resets=np.array(resets, int), B=B, M=M)
    print(stream, pol, f"acc={np.nanmean(acc):.4f} resets={len(resets)} new_calls={cache.new} time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("streams", nargs="+")
    ap.add_argument("--pols", nargs="+", default=POLS)
    a = ap.parse_args()
    for s in a.streams:
        z = np.load(f"{DATA}/{s}.npz")
        X, y = z["X"], z["y"].astype(int)
        cache = Cache(s, X, y, int(y.max()) + 1)
        for p in a.pols:
            run(s, p, cache, X, y)
        if cache.new:
            cache.save()
