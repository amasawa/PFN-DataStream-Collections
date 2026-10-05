"""Observations 1-2 of DriftTriage: what each drift type does to an in-context learner (main venv, TabPFN v2).

For a base concept we draw a context window (pre-drift) and post-drift windows of three types at several magnitudes:
  virtual  same labelling function, P(x) tilted along a random direction u by importance resampling, p(x) ~ exp(beta u.x)
  real     same P(x), labelling function changed (hyperplane rotated by angle theta; SEA threshold moved)
  novel    same labelling of the known classes, plus rows of a class absent from the context (fraction 20%)
For every post window we record, with the frozen TFM:
  acc_stale   accuracy on the post window with the pre-drift context (what the deployed learner does)
  acc_fresh   accuracy with a context of the same size drawn from the post-drift distribution (what refreshing gives)
  conf_*      mean max-probability on the post window (stale context), for known-class rows and for novel rows
  shift       P(x) shift: AUROC of a TFM domain classifier separating pre from post rows (0.5 = no shift)
  disagree    fraction of post rows whose label under the old function differs from the new one (real drift)
Generators (own numpy implementations, standard definitions): hyperplane (Hulten et al. 2001), SEA (Street & Kim 2001),
Gaussian blobs (multi-class, for novel classes). Seeds 0-4 = dev. Output: ../results/obs_<family>.csv
"""
import argparse
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


class TFM:
    def __init__(self, seed=0):
        from tabpfn import TabPFNClassifier
        from tabpfn.constants import ModelVersion
        self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed,
                                                             n_estimators=4, ignore_pretraining_limits=True)

    def proba(self, Xc, yc, Xq, K):
        P = np.zeros((len(Xq), K))
        self.m.fit(Xc, yc)
        P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq)
        return P


def tilt(rng, sampler, n, u, beta):
    """n rows from sampler, importance-resampled with weight exp(beta * u.x) (beta=0: no shift)."""
    X = sampler(rng, 20 * n)
    w = np.exp(beta * (X @ u - (X @ u).max()))
    return X[rng.choice(len(X), n, replace=False, p=w / w.sum())]


# ---------------------------------------------------------------- families: sampler, labeller(params), drift params
def hyperplane(rng, d=10):
    w0 = rng.normal(size=d)
    w0 /= np.linalg.norm(w0)
    def sampler(r, n): return r.uniform(-1, 1, size=(n, d))
    def lab(w, X): return (X @ w > 0).astype(int)
    def rotate(theta):
        v = rng.normal(size=d)
        v -= (v @ w0) * w0
        v /= np.linalg.norm(v)
        return np.cos(np.radians(theta)) * w0 + np.sin(np.radians(theta)) * v
    def new(th):
        w = rotate(th)  # drawn once per magnitude, shared by the post window and the fresh context
        return lambda X: lab(w, X)
    return sampler, lambda X: lab(w0, X), new, d


def sea(rng):
    def sampler(r, n): return r.uniform(0, 10, size=(n, 3))
    def lab(th, X): return (X[:, 0] + X[:, 1] <= th).astype(int)
    return sampler, lambda X: lab(8.0, X), lambda dth: (lambda X: lab(8.0 + dth, X)), 3


def blobs(rng, d=8, K=5):
    C = rng.normal(scale=2.0, size=(K, d))
    def sampler_k(r, n, ks):
        k = r.choice(ks, n)
        return C[k] + r.normal(size=(n, d)), k
    return sampler_k, C, d, K


def run(seed, n_ctx=1000, n_post=1000):
    rng = np.random.default_rng(seed)
    f = TFM(seed)
    rows = []
    for fam in ("hyperplane", "sea"):
        sampler, lab0, lab_new, d = hyperplane(rng) if fam == "hyperplane" else sea(rng)
        u = rng.normal(size=d)
        u /= np.linalg.norm(u)
        Xc = sampler(rng, n_ctx)
        yc = lab0(Xc)
        mags = {"virtual": [0, 1, 2, 4, 8], "real": [0, 10, 30, 60, 90] if fam == "hyperplane" else [0, .5, 1, 2, 4]}
        for typ, grid in mags.items():
            for g in grid:
                beta = g if typ == "virtual" else 0
                Xp = tilt(rng, sampler, n_post, u, beta) if fam == "hyperplane" else tilt(rng, sampler, n_post, u, beta / 3)
                labf = lab0 if typ == "virtual" else lab_new(g)
                yp = labf(Xp)
                Xf = tilt(rng, sampler, n_ctx, u, beta) if fam == "hyperplane" else tilt(rng, sampler, n_ctx, u, beta / 3)
                yf = labf(Xf)
                Ps = f.proba(Xc, yc, Xp, 2)
                Pf = f.proba(Xf, yf, Xp, 2)
                dom = f.proba(np.r_[Xc[:500], Xp[:500]], np.r_[np.zeros(500), np.ones(500)].astype(int),
                              np.r_[Xc[500:], Xp[500:]], 2)[:, 1]
                rows.append(dict(seed=seed, family=fam, type=typ, magnitude=g,
                                 acc_stale=(Ps.argmax(1) == yp).mean(), acc_fresh=(Pf.argmax(1) == yp).mean(),
                                 conf_known=Ps.max(1).mean(), conf_novel=np.nan,
                                 shift=roc_auc_score(np.r_[np.zeros(len(Xc) - 500), np.ones(len(Xp) - 500)], dom),
                                 disagree=(lab0(Xp) != yp).mean()))
    # novel classes on blobs: context has classes 0..K-2, the post window adds class K-1 (20% of rows)
    sampler_k, C, d, K = blobs(rng)
    Xc, yc = sampler_k(rng, n_ctx, np.arange(K - 1))
    for frac in (0.0, 0.1, 0.2, 0.4):
        nn = int(frac * n_post)
        Xk, yk = sampler_k(rng, n_post - nn, np.arange(K - 1))
        Xn, yn = sampler_k(rng, nn, np.array([K - 1]))
        Xp, yp = np.r_[Xk, Xn], np.r_[yk, yn]
        Xf, yf = sampler_k(rng, n_ctx, np.arange(K))
        Ps, Pf = f.proba(Xc, yc, Xp, K), f.proba(Xf, yf, Xp, K)
        isn = yp == K - 1
        dom = f.proba(np.r_[Xc[:500], Xp[:500]], np.r_[np.zeros(500), np.ones(500)].astype(int),
                      np.r_[Xc[500:], Xp[500:]], 2)[:, 1]
        rows.append(dict(seed=seed, family="blobs", type="novel", magnitude=frac,
                         acc_stale=(Ps.argmax(1) == yp).mean(), acc_fresh=(Pf.argmax(1) == yp).mean(),
                         conf_known=Ps[~isn].max(1).mean(), conf_novel=Ps[isn].max(1).mean() if isn.any() else np.nan,
                         shift=roc_auc_score(np.r_[np.zeros(len(Xc) - 500), np.ones(len(Xp) - 500)], dom),
                         disagree=isn.mean()))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for s in a.seeds:
        rows += run(s)
        pd.DataFrame(rows).to_csv(f"{OUT}/obs_{'dev' if a.seeds == [0, 1, 2, 3, 4] else 'test'}.csv", index=False)
        print("seed", s, "done", flush=True)
