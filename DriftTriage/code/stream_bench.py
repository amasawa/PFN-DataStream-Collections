"""Streams with typed drift events and context policies for in-context learners (main venv, TabPFN v2).

Streams: segments of `seg` rows; segment 0 is the base concept, every later segment applies ONE event to the current
state (cumulative), drawn without replacement-per-cycle from {tilt, translate, real, novel}:
  tilt       in-support virtual drift (importance resampling along a random direction)      -> benign
  translate  shift of the input range so that part of the support is new (coverage drift)    -> harmful, label-free
  real       change of the labelling function on the same support                            -> harmful, needs labels
  novel      a class absent so far appears                                                   -> reject rows
Families: sine2d (y = 1[x2 < sin(3 x1 + phase)], novel class = band above the sine region) and lin (K linear classes,
y = argmax W x over active classes; novel = a new class vector is activated).
Seeds 0-4 dev, 10-19 test (fixed before running any policy; see logs/EXPERIMENT_LOG.md).

Protocol: batches of B rows, labels arrive one batch late; the context budget is M rows for every policy.
Policies:
  fifo       last M labelled rows
  ltm        dual memory of Lourenco et al. (KDD 2026, Alg. 1), short share 0.75
  ddm        context = labelled rows since the last reset (FIFO beyond M); the DDM rule on the stream error resets it
  pxreset    context = rows since the last reset; reset when a kNN two-sample classifier separates the incoming batch
             from the context with AUROC > 0.75 (an unsupervised P(x) drift detector)
  triage     ours (v2): the DDM rule on a filtered error stream, i.e. only rows covered by the context (NN-distance
             ratio <= tau) and of classes already in the context; uncovered rows enter the context with priority (no
             reset), rows of a new class get a rejection score (no reset). v0/v1 (context-swap tests) were rejected on
             dev, see logs/EXPERIMENT_LOG.md.
Outputs per (stream, policy): per-batch accuracy, rejection scores and novelty flags, resets. Resumable.
"""
import argparse
import os
import time

import numpy as np
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors
from sklearn.model_selection import cross_val_predict

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
EVENTS = ("tilt", "translate", "real", "novel")


# ------------------------------------------------------------------------------------------------------- streams
class Sine2D:
    K = 3  # classes 0/1 known, class 2 = novel band

    def __init__(self, rng):
        self.rng, self.a, self.phase, self.u, self.beta, self.novel = rng, 0.0, 0.0, None, 0.0, False

    def event(self, e):
        if e == "tilt":
            self.u = self.rng.normal(size=2); self.u /= np.linalg.norm(self.u); self.beta = 2.0
        elif e == "translate":
            self.a += 1.5
        elif e == "real":
            self.phase += np.pi / 2
        elif e == "novel":
            self.novel = True

    def draw(self, n):
        top = 1.6 if self.novel else 1.0
        X = np.c_[self.rng.uniform(self.a, self.a + 4, 20 * n), self.rng.uniform(-1, top, 20 * n)]
        if self.novel:  # keep the novel band at 20% of the rows
            band = X[:, 1] > 1.0
            keep = np.r_[np.flatnonzero(~band)[:int(16 * n)], np.flatnonzero(band)[:int(4 * n)]]
            X = X[keep]
        if self.u is not None:
            w = np.exp(self.beta * ((X - X.mean(0)) @ self.u))
            X = X[self.rng.choice(len(X), n, replace=False, p=w / w.sum())]
        else:
            X = X[self.rng.choice(len(X), n, replace=False)]
        y = (X[:, 1] < np.sin(3 * X[:, 0] + self.phase)).astype(int)
        y[X[:, 1] > 1.0] = 2
        return X.astype(np.float32), y


class Lin:
    K = 4  # classes 0-2 active at start, class 3 activated by the novel event

    def __init__(self, rng, d=6):
        self.rng, self.d = rng, d
        self.W = rng.normal(size=(4, d))
        self.active, self.shift, self.u, self.beta = 3, np.zeros(d), None, 0.0

    def event(self, e):
        if e == "tilt":
            self.u = self.rng.normal(size=self.d); self.u /= np.linalg.norm(self.u); self.beta = 2.0
        elif e == "translate":
            j = self.rng.integers(self.d); self.shift[j] += 1.5
        elif e == "real":  # rotate every class vector by 60 degrees in a random plane
            for k in range(4):
                v = self.rng.normal(size=self.d); w = self.W[k]
                v -= (v @ w) / (w @ w) * w; v *= np.linalg.norm(w) / np.linalg.norm(v)
                self.W[k] = np.cos(np.pi / 3) * w + np.sin(np.pi / 3) * v
        elif e == "novel":
            self.active = 4

    def draw(self, n):
        X = self.rng.uniform(-1, 1, size=(20 * n, self.d)) + self.shift
        if self.u is not None:
            w = np.exp(self.beta * ((X - X.mean(0)) @ self.u))
            X = X[self.rng.choice(len(X), n, replace=False, p=w / w.sum())]
        else:
            X = X[:n]
        y = (X @ self.W[:self.active].T).argmax(1)
        return X.astype(np.float32), y


DATA = os.path.join(os.path.dirname(__file__), "..", "data")
PRE, POST = 5000, 2000   # rows kept before / after the event in the withheld-class episodes


def make_stream(family, seed, seg=3000, cycles=2):
    if family.startswith("real:"):  # real stream (copied from the MICE data folder); drift types unknown
        z = np.load(f"{DATA}/{family[5:]}.npz")
        y = z["y"].astype(int)
        return z["X"].astype(np.float32), y, np.array(["unknown"] * len(y)), int(y.max()) + 1
    if family.startswith("nov:"):  # real stream with one class withheld until an event: nov:<stream>:<class>:<pos%>
        _, name, c, pos = family.split(":")
        z = np.load(f"{DATA}/{name}.npz")
        X, y = z["X"].astype(np.float32), z["y"].astype(int)
        K, c, e = int(y.max()) + 1, int(c), int(len(y) * int(pos) / 100)
        pre = np.flatnonzero(y[:e] != c)[-PRE:]                  # the last PRE rows before the event without class c
        idx = np.r_[pre, np.arange(e, min(e + POST, len(y)))]    # from the event on the stream is left as it is
        y = np.where(y == c, K - 1, np.where(y > c, y - 1, y))   # the withheld class becomes label K-1
        return X[idx], y[idx], np.array(["base"] * len(pre) + ["novel"] * (len(idx) - len(pre))), K
    rng = np.random.default_rng(seed)
    g = Sine2D(rng) if family == "sine2d" else Lin(rng)
    Xs, ys, ev = [], [], []
    X, y = g.draw(seg); Xs.append(X); ys.append(y); ev += ["base"] * seg
    order = []
    for _ in range(cycles):
        order += list(rng.permutation(EVENTS))
    for e in order:
        if e == "novel" and getattr(g, "novel", False) or (e == "novel" and getattr(g, "active", 0) == 4):
            e = "tilt"  # a class can only appear once; replace a repeated novel event by a benign one
        g.event(e)
        X, y = g.draw(seg); Xs.append(X); ys.append(y); ev += [e] * seg
    return np.concatenate(Xs), np.concatenate(ys), np.array(ev), g.K


# ------------------------------------------------------------------------------------------------------- learner
class TFM:
    def __init__(self, K, seed=0):
        from tabpfn import TabPFNClassifier
        from tabpfn.constants import ModelVersion
        self.K = K
        self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed,
                                                             n_estimators=4, ignore_pretraining_limits=True)

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K))
        labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0
            return P
        self.m.fit(Xc, yc)
        P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq)
        return P


def loglik(P, y):
    return np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1))


# ------------------------------------------------------------------------------------------------------- policies
class Policy:
    """Context = index set into the stream. Subclasses decide what enters, what leaves and when to reset."""

    def __init__(self, M):
        self.M, self.idx, self.resets = M, np.array([], int), []

    def evict(self):
        if len(self.idx) > self.M:
            self.idx = self.idx[-self.M:]


class Fifo(Policy):
    def observe(self, t, B, **kw):
        self.idx = np.r_[self.idx, np.arange((t - 1) * B, t * B)]
        self.evict()


class LTMp(Policy):
    def __init__(self, M, r=0.75):
        super().__init__(M)
        self.Ms = int(r * M); self.S, self.L, self.C = [], [], {}

    def observe(self, t, B, y, **kw):
        for i in range((t - 1) * B, t * B):
            self.S.append(i)
            if len(self.S) > self.Ms:
                o = self.S.pop(0); self.L.append(o); self.C[y[o]] = self.C.get(y[o], 0) + 1
            if len(self.L) > self.M - self.Ms:
                ym = max(self.C, key=self.C.get)
                j = next(k for k, o in enumerate(self.L) if y[o] == ym)
                self.L.pop(j); self.C[ym] -= 1
        self.idx = np.array(self.S + self.L, int)


class DDMr(Policy):
    """DDM with the same refractory period as triage v4: no reset within `refr` batches after a reset."""

    def __init__(self, M, refr=2):
        super().__init__(M); self.refr = refr; self._reset_stats()

    def _reset_stats(self):
        self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf

    def observe(self, t, B, errors, **kw):
        if not self.resets or t - self.resets[-1] > self.refr:
            for e in errors:
                self.n += 1; self.err += e
                p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
                if self.n >= 30 and p + s < self.pmin + self.smin:
                    self.pmin, self.smin = p, s
                if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
                    self.resets.append(t); self.idx = np.array([], int); self._reset_stats(); break
        self.idx = np.r_[self.idx, np.arange((t - 1) * B, t * B)]
        self.evict()


class DDM(Policy):
    """Gama et al. (2004): reset when p_i + s_i > p_min + 3 s_min, after n >= 30 rows since the last reset."""

    def __init__(self, M):
        super().__init__(M); self._reset_stats()

    def _reset_stats(self):
        self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf

    def observe(self, t, B, errors, **kw):
        for e in errors:
            self.n += 1; self.err += e
            p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
            if self.n >= 30 and p + s < self.pmin + self.smin:
                self.pmin, self.smin = p, s
            if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
                self.resets.append(t); self.idx = np.array([], int); self._reset_stats(); break
        self.idx = np.r_[self.idx, np.arange((t - 1) * B, t * B)]
        self.evict()


class PxReset(Policy):
    def __init__(self, M, thr=0.75):
        super().__init__(M); self.thr = thr

    def observe(self, t, B, X, **kw):
        self.idx = np.r_[self.idx, np.arange((t - 1) * B, t * B)]
        self.evict()
        nxt = np.arange(t * B, (t + 1) * B)
        if len(self.idx) >= 2 * B and nxt[-1] < len(X):
            ref = self.idx[-5 * B:]
            Z = np.r_[X[ref], X[nxt]]; lab = np.r_[np.zeros(len(ref)), np.ones(len(nxt))]
            s = cross_val_predict(KNeighborsClassifier(10), Z, lab, cv=2, method="predict_proba")[:, 1]
            if roc_auc_score(lab, s) > self.thr:
                self.resets.append(t); self.idx = self.idx[-B:]


class Triage4(Policy):
    """Ours (v4) = v2 plus: (a) labelled rows of a class new to the context prune their k nearest context rows that carry
    a different label (a new class that takes over part of the support makes those labels obsolete; local clean-up
    instead of a reset); (b) a class that entered the context in the last `buffer` batches is not yet 'known' (its
    learning errors do not feed the detector); (c) no reset within `refr` batches after a reset."""

    def __init__(self, M, f, tau=3.0, k=5, buffer=3, refr=2):
        super().__init__(M); self.f, self.tau, self.k, self.buffer, self.refr = f, tau, k, buffer, refr
        self.priority = set(); self.kinds = []; self.cov_last = None; self.entry = {}; self._reset_stats()

    def _reset_stats(self):
        self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf

    def coverage(self, X, rows):
        ctx = X[self.idx]
        nn = NearestNeighbors(n_neighbors=2).fit(ctx)
        own = nn.kneighbors(ctx)[0][:, 1].mean() + 1e-12
        return nn.kneighbors(X[rows], n_neighbors=1)[0][:, 0] / own

    def observe(self, t, B, X, y, errors, **kw):
        lab = np.arange((t - 1) * B, t * B)
        kind = "none"
        ctx_classes = set(np.unique(y[self.idx]).tolist()) if len(self.idx) else set()
        for c in set(np.unique(y[lab]).tolist()) - ctx_classes:
            self.entry[c] = t
        fresh = {c for c, t0 in self.entry.items() if t - t0 < self.buffer}
        if len(errors) and self.cov_last is not None:
            known = np.isin(y[lab], list(ctx_classes - fresh)) if ctx_classes else np.ones(len(lab), bool)
            covered = self.cov_last <= self.tau
            self.priority |= set(lab[~covered].tolist())
            if (~covered).mean() > 0.2:
                kind = "coverage"
            if (~np.isin(y[lab], list(ctx_classes))).any():
                kind = "novel"
            if not self.resets or t - self.resets[-1] > self.refr:
                for e in np.asarray(errors)[known & covered]:
                    self.n += 1; self.err += e
                    p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
                    if self.n >= 30 and p + s < self.pmin + self.smin:
                        self.pmin, self.smin = p, s
                    if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
                        self.resets.append(t); kind = "real"
                        self.idx = np.array([], int); self.priority = set(); self._reset_stats()
                        break
        # (a) prune context rows that a fresh class has taken over
        newrows = lab[np.isin(y[lab], list(fresh))]
        if len(newrows) and len(self.idx) > self.k:
            nn = NearestNeighbors(n_neighbors=min(self.k, len(self.idx))).fit(X[self.idx])
            nb = self.idx[nn.kneighbors(X[newrows])[1]]
            bad = set(nb[y[nb] != y[newrows][:, None]].tolist())
            if bad:
                self.idx = np.array([i for i in self.idx if i not in bad], int)
        self.kinds.append(kind)
        self.idx = np.r_[self.idx, lab]
        if len(self.idx) > self.M:
            pri = np.array([i in self.priority for i in self.idx])
            order = np.r_[np.flatnonzero(~pri), np.flatnonzero(pri)]
            drop = set(self.idx[order[:len(self.idx) - self.M]].tolist())
            self.idx = np.array([i for i in self.idx if i not in drop], int)
            self.priority -= drop


class Triage(Policy):
    """Ours (v2). The DDM rule runs on a FILTERED error stream: only rows that the context covers (NN-distance ratio
    <= tau) and whose class is already in the context. Errors on uncovered rows signal coverage drift (their rows are
    kept in the context with priority, no reset); errors on rows of a new class signal novelty (no reset; the rows get
    a rejection score). Only the remaining errors can reveal real drift, which resets the context."""

    def __init__(self, M, f, tau=3.0, min_known=1, keep_uncovered=True, standardise=False, embed=False):
        super().__init__(M); self.f, self.tau, self.min_known = f, tau, min_known
        self.embed = embed  # iteration after pre-registration 3: coverage in the TFM's embedding space
        # ablations added after the real-stream run: FIFO eviction instead of keeping uncovered rows with priority;
        # coverage on features standardised by the context
        self.keep_uncovered, self.standardise = keep_uncovered, standardise
        self.priority = set(); self.kinds = []; self.cov_last = None; self._reset_stats()

    def _reset_stats(self):
        self.n, self.err, self.pmin, self.smin = 0, 0, np.inf, np.inf

    def coverage(self, X, rows):
        """NN distance of `rows` to the context over the context's own leave-one-out NN distance."""
        ctx, Xr = X[self.idx], X[rows]
        if self.embed and len(np.unique(self.f_y[self.idx])) > 1:  # the TFM was just fitted on this context by run()
            ctx = self.f.m.get_embeddings(ctx, data_source="train").mean(0)
            Xr = self.f.m.get_embeddings(Xr, data_source="test").mean(0)
        if self.standardise:
            mu, sd = ctx.mean(0), ctx.std(0) + 1e-12
            ctx, Xr = (ctx - mu) / sd, (Xr - mu) / sd
        nn = NearestNeighbors(n_neighbors=2).fit(ctx)
        own = nn.kneighbors(ctx)[0][:, 1].mean() + 1e-12
        return nn.kneighbors(Xr, n_neighbors=1)[0][:, 0] / own

    def observe(self, t, B, X, y, errors, **kw):
        lab = np.arange((t - 1) * B, t * B)
        kind = "none"
        if len(errors) and self.cov_last is not None:
            if len(self.idx):  # a class counts as known once the context holds at least min_known of its rows
                labs, cnt = np.unique(y[self.idx], return_counts=True)
                known = np.isin(y[lab], labs[cnt >= self.min_known])
            else:
                known = np.ones(len(lab), bool)
            covered = self.cov_last <= self.tau
            if self.keep_uncovered:
                self.priority |= set(lab[~covered].tolist())
            if (~covered).mean() > 0.2:
                kind = "coverage"
            if (~known).any():
                kind = "novel"
            for e in np.asarray(errors)[known & covered]:
                self.n += 1; self.err += e
                p = self.err / self.n; s = np.sqrt(p * (1 - p) / self.n)
                if self.n >= 30 and p + s < self.pmin + self.smin:
                    self.pmin, self.smin = p, s
                if self.n >= 30 and p + s > self.pmin + 3 * self.smin:
                    self.resets.append(t); kind = "real"
                    self.idx = np.array([], int); self.priority = set(); self._reset_stats()
                    break
        self.kinds.append(kind)
        self.idx = np.r_[self.idx, lab]
        if len(self.idx) > self.M:  # evict the oldest covered rows first
            pri = np.array([i in self.priority for i in self.idx])
            order = np.r_[np.flatnonzero(~pri), np.flatnonzero(pri)]
            drop = set(self.idx[order[:len(self.idx) - self.M]].tolist())
            self.idx = np.array([i for i in self.idx if i not in drop], int)
            self.priority -= drop


class LRef(Policy):
    """Locally referenced error (iteration of 2026-10-05). Every context row carries the prequential error it had when
    it was predicted itself. For a newly labelled row the reference is the mean of that error over its k nearest
    context rows (features standardised by the context): the error the learner used to make in this part of the input
    space. The detector runs on the excess d = error - reference instead of the raw error, so a move of P(x) into a
    harder region raises both terms and does not reset, whereas a change of P(y|x) raises the error only. Because the
    reference supplies the null value, no minimum tracking is needed: reset when the mean excess over the last W
    labelled rows exceeds z standard errors (mintrack=True keeps the DDM rule on the excess, as an ablation). The excess is a nearest-neighbour estimate of the loss on the new rows minus the
    density-ratio-weighted loss on the context rows (the form of I-Div)."""

    def __init__(self, M, k=10, W=200, z=3.0, mintrack=False):
        super().__init__(M); self.k, self.W, self.z, self.mintrack = k, W, z, mintrack
        self.perr = None; self._reset_stats()

    def _reset_stats(self):
        self.n, self.s1, self.s2, self.best, self.sebest, self.d = 0, 0.0, 0.0, np.inf, np.inf, []

    def observe(self, t, B, X, errors, **kw):
        lab = np.arange((t - 1) * B, t * B)
        ref_rows = self.idx[~np.isnan(self.perr[self.idx])] if len(self.idx) else self.idx
        if len(errors) and len(ref_rows) >= self.k:
            mu, sd = X[ref_rows].mean(0), X[ref_rows].std(0) + 1e-12
            nb = NearestNeighbors(n_neighbors=self.k).fit((X[ref_rows] - mu) / sd).kneighbors((X[lab] - mu) / sd)[1]
            d = np.asarray(errors) - self.perr[ref_rows][nb].mean(1)
            fire = False
            if self.mintrack:  # ablation: the DDM rule with minimum tracking on the excess
                for v in d:
                    self.n += 1; self.s1 += v; self.s2 += v * v
                    m = self.s1 / self.n
                    se = np.sqrt(max(self.s2 / self.n - m * m, 1e-4) / self.n)
                    if self.n >= 30 and m + se < self.best + self.sebest:
                        self.best, self.sebest = m, se
                    if self.n >= 30 and m + se > self.best + 3 * self.sebest:
                        fire = True; break
            else:  # the reference supplies the null: one-sided test of mean excess > 0 over the last W labelled rows
                self.d = (self.d + d.tolist())[-self.W:]
                if len(self.d) >= self.W:
                    w = np.array(self.d)
                    fire = w.mean() > self.z * max(w.std(), 1e-2) / np.sqrt(len(w))
            if fire:
                self.resets.append(t); self.idx = np.array([], int); self._reset_stats()
        self.idx = np.r_[self.idx, lab]
        self.evict()

def run(family, seed, policy, B, M, out):
    dst = f"{out}/{family.replace('real:', '').replace(':', '-')}_s{seed}__{policy}.npz"
    if os.path.exists(dst):
        return
    X, y, ev, K = make_stream(family, seed)
    f = TFM(K, seed)
    T = len(y) // B
    pol = {"fifo": lambda: Fifo(M), "ltm": lambda: LTMp(M), "ddm": lambda: DDM(M), "pxreset": lambda: PxReset(M),
           "triage": lambda: Triage(M, f), "triage3": lambda: Triage(M, f, min_known=30),
           "triage4": lambda: Triage4(M, f), "ddmr": lambda: DDMr(M),
           "triage_np": lambda: Triage(M, f, keep_uncovered=False),
           "triage_z": lambda: Triage(M, f, standardise=True),
           "triage_znp": lambda: Triage(M, f, keep_uncovered=False, standardise=True),
           "triage_emb": lambda: Triage(M, f, keep_uncovered=False, embed=True), "lref": lambda: LRef(M), "lref_min": lambda: LRef(M, mintrack=True)}[policy]()
    pol.f_y = y
    pol.perr = np.full(len(y), np.nan)   # prequential error of every row at the time it was predicted (LRef)
    cov, unc = np.full(len(y), np.nan), np.full(len(y), np.nan)
    acc, rej, wt = np.full(T, np.nan), np.full(len(y), np.nan), np.zeros(T)
    P_last, err_last = None, None
    for t in range(1, T):
        t0 = time.time()
        pol.observe(t=t, B=B, X=X, y=y, errors=err_last if err_last is not None else [], P_last=P_last)
        q = np.arange(t * B, (t + 1) * B)
        P = f.predict(X[pol.idx], y[pol.idx], X[q]) if len(pol.idx) else np.full((B, K), 1 / K)
        acc[t] = (P.argmax(1) == y[q]).mean()
        rej[q] = 1 - P.max(1)
        unc[q] = rej[q]
        if policy.startswith("triage"):
            pol.cov_last = None
        if policy.startswith("triage") and len(pol.idx) >= B:  # coverage of the incoming (unlabelled) batch
            pol.cov_last = pol.coverage(X, q)
            cov[q] = pol.cov_last
            rej[q] = np.maximum(rej[q], np.clip(pol.cov_last / pol.tau - 1, 0, None))
        err_last = (P.argmax(1) != y[q]).astype(int)
        pol.perr[q] = err_last
        P_last = P
        wt[t] = time.time() - t0
    np.savez_compressed(dst, acc=acc, rej=rej, y=y, ev=ev, resets=np.array(pol.resets), wt=wt, B=B, K=K,
                        kinds=np.array(getattr(pol, "kinds", [])), cov=cov, unc=unc)
    print(family, seed, policy, f"acc={np.nanmean(acc):.4f}", f"resets={len(pol.resets)}", f"time={wt.sum():.0f}s",
          flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="+", default=["sine2d", "lin"])
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--policies", nargs="+", default=["fifo", "ltm", "ddm", "pxreset", "triage"])
    ap.add_argument("--B", type=int, default=100)
    ap.add_argument("--M", type=int, default=1000)
    ap.add_argument("--out", default=os.path.join(OUT, "stream_dev"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for fam in a.families:
        for s in a.seeds:
            for p in a.policies:
                run(fam, s, p, a.B, a.M, a.out)
