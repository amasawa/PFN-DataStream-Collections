"""Batch-prequential evaluation of in-context stream learners on ../data/<stream>.npz (main venv: ~/pfn-venvs/venv).

Protocol: the stream is cut into batches of B rows. Batch t is predicted from the labelled rows of batches < t (labels
arrive one batch late); batch 0 is the warm-up and is not scored. Every method uses the same frozen backbone (TabPFN v2,
4 estimators, as in Lourenco et al. KDD 2026) and the same context budget M.

Methods (name -> spec):
  fifo<M>            last M labelled rows
  ltm<M>_<r>         dual memory of Lourenco et al. (KDD 2026, Alg. 1): short FIFO of r*M rows, long class-balanced
                     memory of (1-r)*M rows fed by rows leaving the short memory
  oracle<M>          last M rows of the concept of the first row of the batch (needs concept labels; upper bound)
  mice<M>            mixture of in-context experts (see class Mice)
Output: <out>/<stream>__<method>.npz with per-batch accuracy, log-loss and wall time. Resumable per (stream, method).
Usage: python run.py --streams sea_s0 rbf_s0 --methods fifo1000 ltm1000_75 oracle1000 mice1000 --out ../results_dev
"""
import argparse
import os
import pickle
import re
import time
from collections import deque

import numpy as np

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


class TFM:
    """Frozen TabPFN v2; fit on a context, predict probabilities over the global label set."""

    def __init__(self, n_classes, seed=0):
        self.K = n_classes
        if os.environ.get("MICE_BACKBONE", "tabpfn") == "tabicl":   # second backbone, same number of estimators
            from tabicl import TabICLClassifier
            self.m = TabICLClassifier(device="cuda", random_state=seed, n_estimators=4)
        else:
            from tabpfn import TabPFNClassifier
            from tabpfn.constants import ModelVersion
            self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed,
                                                                 n_estimators=4, ignore_pretraining_limits=True)
        self.calls = 0

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K))
        labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0
            return P
        self.m.fit(Xc, yc)
        if self.m.__class__.__name__ == "TabICLClassifier":   # fit() reloads the checkpoint on every call (~1.3 s);
            self.m._load_model = lambda: None                 # keep the loaded model (predictions are identical)
        P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq)
        self.calls += 1
        return P


# ------------------------------------------------------------------------------------------------ context policies
def fifo(X, y, t, B, M):
    lo = max(0, t * B - M)
    return X[lo:t * B], y[lo:t * B]


class LTM:
    """Lourenco et al. (KDD 2026), Algorithm 1, applied row by row; contexts are read once per batch."""

    def __init__(self, M, r):
        self.Ms, self.Ml = int(round(r * M)), M - int(round(r * M))
        self.S, self.L, self.C = deque(), [], {}

    def add(self, X, y):
        for xi, yi in zip(X, y):
            self.S.append((xi, yi))
            if len(self.S) > self.Ms:
                xo, yo = self.S.popleft()
                self.L.append((xo, yo))
                self.C[yo] = self.C.get(yo, 0) + 1
            if len(self.L) > self.Ml:
                ymax = max(self.C, key=self.C.get)
                j = next(i for i, (_, yy) in enumerate(self.L) if yy == ymax)  # oldest of the largest class
                self.L.pop(j)
                self.C[ymax] -= 1

    def context(self):
        rows = list(self.S) + self.L
        return np.array([r[0] for r in rows]), np.array([r[1] for r in rows])


class DDMReset:
    """Context = labelled rows since the last DDM detection (Gama et al. 2004), FIFO beyond M."""

    def __init__(self, M):
        self.M, self.start, self.n, self.err, self.pmin, self.smin, self.resets = M, 0, 0, 0, np.inf, np.inf, []

    def update(self, errors, t, B):
        for e in errors:
            self.n += 1; self.err += e
            p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
            if self.n >= 30 and p + s < self.pmin + self.smin:
                self.pmin, self.smin = p, s
            if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
                self.start, self.resets = (t - 1) * B, self.resets + [t]
                self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf
                break

    def context(self, X, y, t, B):
        lo = max(self.start, t * B - self.M)
        return X[lo:t * B], y[lo:t * B]


def oracle(X, y, concept, t, B, M):
    idx = np.flatnonzero(concept[:t * B] == concept[t * B])[-M:]
    return (X[idx], y[idx]) if len(idx) >= 20 else fifo(X, y, t, B, M)


class Mice:
    """Mixture of in-context experts.
    Pool: every `seg` labelled rows close a segment; it is merged into the expert whose context predicts it as well as
    the segment predicts itself (2-fold, model-oriented discrepancy in the sense of R-divergence), else it becomes a new
    expert. Each expert keeps its last M rows. The online expert is the FIFO context.
    Weights: exponentially weighted forecaster on the log-loss of each expert on the latest labelled batch, with
    discount gamma (so that a recurring concept can regain weight quickly); prediction = weighted mixture."""

    def __init__(self, tfm, M, seg=1000, eta=2.0, gamma=0.5, delta=0.02, kmax=12, cache_px=False):
        self.cache_px = cache_px
        self.f, self.M, self.seg, self.eta, self.gamma, self.delta, self.kmax = tfm, M, seg, eta, gamma, delta, kmax
        self.experts = []          # list of dicts: X, y, loss, last_used
        self.pending = None        # predictions of every expert on the batch whose labels arrive next
        self.closed = 0
        self.online = dict(loss=0.0)
        self.uid = 0
        self.cache = []            # per batch: {uid or -1 (online): probabilities}, and the label-free discrepancy

    def _merge_or_add(self, Xs, ys, now):
        h = len(ys) // 2
        own = 0.5 * ((self.f.predict(Xs[:h], ys[:h], Xs[h:]).argmax(1) == ys[h:]).mean()
                     + (self.f.predict(Xs[h:], ys[h:], Xs[:h]).argmax(1) == ys[:h]).mean())
        best, bacc = None, -1
        for e in self.experts:
            acc = (self.f.predict(e["X"], e["y"], Xs).argmax(1) == ys).mean()
            if acc > bacc:
                best, bacc = e, acc
        if best is not None and bacc >= own - self.delta:
            best["X"], best["y"] = np.r_[best["X"], Xs][-self.M:], np.r_[best["y"], ys][-self.M:]
            best["last"] = now
        else:
            self.uid += 1
            self.experts.append(dict(X=Xs[-self.M:], y=ys[-self.M:], loss=self.online["loss"], last=now, uid=self.uid))
            if len(self.experts) > self.kmax:
                self.experts.pop(int(np.argmin([e["last"] for e in self.experts])))

    def step(self, X, y, t, B):
        n = t * B
        # 1) labels of batch t-1 arrived: update losses with the predictions made for it
        if self.pending is not None:
            yb = y[n - B:n]
            for key, P in self.pending.items():
                l = -np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean()
                tgt = self.online if key == "online" else self.experts[key] if key < len(self.experts) else None
                if tgt is not None:
                    tgt["loss"] = self.gamma * tgt["loss"] + l
        # 2) close segments
        while n - self.closed >= self.seg:
            self._merge_or_add(X[self.closed:self.closed + self.seg], y[self.closed:self.closed + self.seg], t)
            self.closed += self.seg
        # 3) predict batch t
        Xq = X[n:n + B]
        Xo, yo = fifo(X, y, t, B, self.M)
        preds = {"online": self.f.predict(Xo, yo, Xq)}
        for k, e in enumerate(self.experts):
            preds[k] = self.f.predict(e["X"], e["y"], Xq)
        disc = {}
        if self.cache_px:
            for k, e in enumerate(self.experts):
                disc[e["uid"]] = two_sample_auc(e["X"], Xq)
            disc[-1] = two_sample_auc(Xo, Xq)
        self.cache.append(dict(t=t, P={(-1 if k == "online" else self.experts[k]["uid"]): preds[k] for k in preds},
                               disc=disc))
        keys = list(preds)
        losses = np.array([self.online["loss"] if k == "online" else self.experts[k]["loss"] for k in keys])
        w = np.exp(-self.eta * (losses - losses.min()))
        w /= w.sum()
        self.pending = preds
        return sum(wi * preds[k] for wi, k in zip(w, keys)), dict(zip(map(str, keys), w))


class MiceV1(Mice):
    """Mice with several online experts: FIFO windows of `windows` rows (fast in-context re-learning) next to the pool of
    past-segment experts (memory). Every expert's prediction on every batch is cached (keys: -w for the window of w rows,
    uid > 0 for pool experts), so that weighting rules and expert subsets can be compared offline (reweight.py)."""

    def __init__(self, tfm, M, windows=(100, 300), **kw):
        super().__init__(tfm, M, cache_px=False, **kw)
        self.windows = tuple(windows) + (M,)
        self.wloss = {w: 0.0 for w in self.windows}

    def step(self, X, y, t, B):
        n = t * B
        if self.pending is not None:
            yb = y[n - B:n]
            for key, P in self.pending.items():
                l = -np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean()
                if key < 0:
                    self.wloss[-key] = self.gamma * self.wloss[-key] + l
                else:
                    e = next((e for e in self.experts if e["uid"] == key), None)
                    if e is not None:
                        e["loss"] = self.gamma * e["loss"] + l
        self.online = dict(loss=float(np.median(list(self.wloss.values()))))
        while n - self.closed >= self.seg:
            self._merge_or_add(X[self.closed:self.closed + self.seg], y[self.closed:self.closed + self.seg], t)
            self.closed += self.seg
        Xq = X[n:n + B]
        preds = {-w: self.f.predict(*fifo(X, y, t, B, w), Xq) for w in self.windows}
        for e in self.experts:
            preds[e["uid"]] = self.f.predict(e["X"], e["y"], Xq)
        losses = np.array([self.wloss[-k] if k < 0 else next(e["loss"] for e in self.experts if e["uid"] == k)
                           for k in preds])
        w = np.exp(-self.eta * (losses - losses.min()))
        w /= w.sum()
        self.pending = preds
        self.cache.append(dict(t=t, P=dict(preds), disc={}))
        return sum(wi * P for wi, P in zip(w, preds.values())), None


def two_sample_auc(Xa, Xb):
    """Label-free discrepancy: AUROC of a 2-fold kNN classifier separating context rows from the query batch."""
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_predict
    from sklearn.neighbors import KNeighborsClassifier
    Xa = Xa[-len(Xb) * 3:]
    Z, lab = np.r_[Xa, Xb], np.r_[np.zeros(len(Xa)), np.ones(len(Xb))]
    s = cross_val_predict(KNeighborsClassifier(10), Z, lab, cv=2, method="predict_proba")[:, 1]
    return roc_auc_score(lab, s)


def run(stream, method, B, out):
    dst = f"{out}/{stream}__{method}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{DATA}/{stream}.npz")
    X, y, concept = z["X"], z["y"].astype(int), z["concept"]
    K, T = int(y.max()) + 1, len(y) // B
    f = TFM(K)
    acc, ll, wt = np.full(T, np.nan), np.full(T, np.nan), np.zeros(T)
    m = re.fullmatch(r"([a-z]+)(\d+)(?:_(\d+))?", method)
    kind, M = m.group(1), int(m.group(2))
    pol = (LTM(M, int(m.group(3)) / 100) if kind == "ltm" else Mice(f, M) if kind == "mice"
           else Mice(f, M, cache_px=True) if kind == "micecache" else DDMReset(M) if kind == "ddm"
           else MiceV1(f, M, seg=int(m.group(3)) if m.group(3) else 1000) if kind == "micev" else None)
    Lw = {}  # winens: discounted losses of the window experts
    errs, Pw_last = None, None
    # micev runs take hours and the machine restarts: its state is saved every CK batches and picked up on restart
    ck, CK, t0_ = dst[:-4] + ".ckpt", int(os.environ.get("MICE_CKPT_EVERY", 100)), 1
    if kind == "micev" and os.path.exists(ck):
        st = pickle.load(open(ck, "rb"))
        pol.__dict__.update(st["pol"])
        acc, ll, wt, f.calls, t0_ = st["acc"], st["ll"], st["wt"], st["calls"], st["t"] + 1
        print(stream, method, f"resumed at batch {t0_}", flush=True)
    for t in range(t0_, T):
        t0 = time.time()
        Xq, yq = X[t * B:(t + 1) * B], y[t * B:(t + 1) * B]
        if kind == "fifo":
            P = f.predict(*fifo(X, y, t, B, M), Xq)
        elif kind == "ltm":
            pol.add(X[(t - 1) * B:t * B], y[(t - 1) * B:t * B])
            P = f.predict(*pol.context(), Xq)
        elif kind == "oracle":
            if concept[0] < 0:
                return
            P = f.predict(*oracle(X, y, concept, t, B, M), Xq)
        elif kind in ("mice", "micecache", "micev"):
            P, _ = pol.step(X, y, t, B)
        elif kind == "ddm":
            if errs is not None:
                pol.update(errs, t, B)
            P = f.predict(*pol.context(X, y, t, B), Xq)
            errs = (P.argmax(1) != yq).astype(int)
        elif kind == "winens":  # hedge over FIFO windows of 100/300/M rows (eta=2, gamma=0.5, as mice1000)
            if Pw_last is not None:
                yb = y[(t - 1) * B:t * B]
                for wsz, Pp in Pw_last.items():
                    Lw[wsz] = 0.5 * Lw.get(wsz, 0.0) - np.log(np.clip(Pp[np.arange(len(yb)), yb], 1e-6, 1)).mean()
            Pw_last = {wsz: f.predict(*fifo(X, y, t, B, wsz), Xq) for wsz in (100, 300, M)}
            Lk = np.array([Lw.get(wsz, 0.0) for wsz in Pw_last])
            w = np.exp(-2.0 * (Lk - Lk.min())); w /= w.sum()
            P = sum(wi * Pp for wi, Pp in zip(w, Pw_last.values()))
        acc[t] = (P.argmax(1) == yq).mean()
        ll[t] = -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)).mean()
        wt[t] = time.time() - t0
        if kind == "micev" and t % CK == 0:
            pickle.dump(dict(pol={k: v for k, v in pol.__dict__.items() if k != "f"}, acc=acc, ll=ll, wt=wt,
                             calls=f.calls, t=t), open(ck + ".tmp", "wb"))
            os.replace(ck + ".tmp", ck)
    np.savez_compressed(dst, acc=acc, ll=ll, wt=wt, B=B, concept=concept, calls=f.calls,
                        n_experts=len(pol.experts) if kind in ("mice", "micecache", "micev") else 0)
    if kind in ("micecache", "micev"):
        pickle.dump(dict(cache=pol.cache, y=y, B=B, concept=concept, K=K), open(dst[:-4] + ".pkl", "wb"))
        if os.path.exists(ck):
            os.remove(ck)
    print(stream, method, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+")
    ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--out", default="../results_dev")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for meth in a.methods:
            run(s, meth, a.B, a.out)
