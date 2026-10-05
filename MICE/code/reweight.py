"""Offline weighting rules for the cached expert predictions of run.py (method micecache<M>). No TFM call.
Each rule maps the history of per-expert log-losses (labels one batch late) and, optionally, the label-free
discrepancy between each expert's context and the current batch to mixture weights.
Rules:
  hedge(eta, gamma)          w ~ exp(-eta * L), L <- gamma * L + loss of the last labelled batch (MOOE meta expert
                             with discount; gamma = 0 means "last batch only")
  prior(eta, gamma, lam)     hedge times exp(-lam * (disc - 0.5)): the label-free discrepancy acts before labels arrive
  leader                     all weight on the expert with the lowest discounted loss (gamma = 0.5)
Usage: python reweight.py ../results_dev [h]   -> accuracy overall / after recurrences per rule"""
import glob
import itertools
import pickle
import sys

import numpy as np
import pandas as pd


def simulate(c, eta, gamma, lam=0.0, leader=False, subset=None, collect=None):
    cache, y, B = c["cache"], c["y"], c["B"]
    L, acc = {}, {}
    for i, step in enumerate(cache):
        t = step["t"]
        if i > 0:  # labels of the previous batch arrive: update the losses of the experts that predicted it
            prev = cache[i - 1]
            yb = y[prev["t"] * B:(prev["t"] + 1) * B]
            for u, P in prev["P"].items():
                l = -np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean()
                L[u] = gamma * L[u] + l if u in L else l  # a new expert starts with its first loss
        keys = [u for u in step["P"] if subset is None or subset(u)]
        Lk = np.array([L.get(u, np.median(list(L.values())) if L else 0.0) for u in keys])  # unseen: median
        if leader:
            w = (Lk == Lk.min()).astype(float)
        else:
            w = np.exp(-eta * (Lk - Lk.min()))
        if lam and step["disc"]:
            d = np.array([step["disc"].get(u, 0.5) for u in keys])
            w = w * np.exp(-lam * (d - 0.5))
        w /= w.sum()
        P = sum(wi * step["P"][u] for wi, u in zip(w, keys))
        yq = y[t * B:(t + 1) * B]
        acc[t] = (P.argmax(1) == yq).mean()
        if collect is not None:   # per-row mixture probabilities, for metrics other than accuracy
            collect.append((t, P))
    return acc


def metrics(acc, c, h=5):
    T, B, conc = max(acc) + 1, c["B"], c["concept"]
    a = np.full(T, np.nan)
    for t, v in acc.items():
        a[t] = v
    out = dict(acc=np.nanmean(a))
    if conc[0] >= 0:
        bc = np.array([conc[t * B] for t in range(T)])
        starts = [t for t in range(1, T) if bc[t] != bc[t - 1]]
        rec = [a[t:t + h] for t in starts if (bc[:t] == bc[t]).any()]
        out["acc_recur"] = np.nanmean(np.concatenate(rec)) if rec else np.nan
    return out


if __name__ == "__main__":
    d = sys.argv[1]
    h = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    rules = [("hedge", e, g, 0.0) for e, g in itertools.product((1, 2, 5, 10, 20), (0.0, 0.5, 0.8))]
    subsets = {"all": None, "windows": lambda u: u < 0, "pool+M": lambda u: u > 0 or u == -1000}
    rules += [("prior", e, g, l) for e, g, l in itertools.product((5, 10), (0.0, 0.5), (2, 5, 10))]
    rules += [("leader", 0, 0.5, 0.0)]
    rows = []
    for f in sorted(glob.glob(f"{d}/*__mice*.pkl")):
        c = pickle.load(open(f, "rb"))
        stream = f.split("/")[-1].split("__")[0]
        has_windows = any(u < -1 and u != -1 for st in c["cache"] for u in st["P"])
        for sub, fn in (subsets.items() if has_windows else [("all", None)]):
            for name, e, g, l in rules:
                if name == "prior" and not any(st["disc"] for st in c["cache"]):
                    continue
                m = metrics(simulate(c, e, g, l, leader=name == "leader", subset=fn), c, h)
                rows.append(dict(stream=stream, subset=sub, rule=name, eta=e, gamma=g, lam=l, **m))
    r = pd.DataFrame(rows)
    r.to_csv(f"{d}/reweight.csv", index=False)
    r["family"] = r.stream.str.replace(r"_s\d+$", "", regex=True)
    pd.set_option("display.width", 200)
    print(r.groupby(["subset", "rule", "eta", "gamma", "lam"])[["acc", "acc_recur"]].mean().round(4)
          .sort_values("acc").tail(int(sys.argv[3]) if len(sys.argv) > 3 else 40).to_string())


def freeze(d, method, eta, gamma, out_name):
    """Write <stream>__<out_name>.npz (same format as run.py) for one frozen weighting rule applied to the cached
    experts of `method`. The rule only uses losses of batches whose labels have arrived, so the replay is causal and
    equals running the method online."""
    for f in sorted(glob.glob(f"{d}/*__{method}.pkl")):
        c = pickle.load(open(f, "rb"))
        acc = simulate(c, eta, gamma)
        T = len(c["y"]) // c["B"]
        a = np.full(T, np.nan)
        for t, v in acc.items():
            a[t] = v
        z = np.load(f[:-4] + ".npz")
        np.savez_compressed(f.replace(f"__{method}.pkl", f"__{out_name}.npz"), acc=a, ll=np.full(T, np.nan), wt=z["wt"],
                            B=c["B"], concept=c["concept"], calls=z["calls"], n_experts=z["n_experts"])


def simulate2(c, eta=10.0, e2=1.0, g2=0.9, default=-1000, outer="log", scale=10.0, temper=False, subset=None,
              collect=None):
    """MICE with a two-timescale meta expert (frozen 2026-10-05). Inner level: weights ~ exp(-eta * loss on the last
    labelled batch) over all experts (the rule frozen on 2026-10-04). Outer level: exponential weights between the
    default expert (the M-row FIFO window) and the inner mixture on their discounted cumulative log-loss,
    L <- g2 * L + mean loss on the last labelled batch, step e2. Causal: only labelled batches are used.
    outer="brier" uses scale x the half Brier score; temper=True uses the weights exp(-e2 * g2 * L), for which the
    discounted regret bound ln(2) / (e2 * scale) holds when e2 * scale <= 1/2 (see check_outer_regret.py)."""
    cache, y, B = c["cache"], c["y"], c["B"]
    acc, Lo, prev, last = {}, np.zeros(2), None, None
    ll = lambda Q, yy: -np.log(np.clip(Q[np.arange(len(yy)), yy], 1e-6, 1))
    for st in cache:
        t, keys = st["t"], [u for u in st["P"] if subset is None or subset(u)]   # subset: ablation of the expert set
        yq = y[t * B:(t + 1) * B]
        if prev is None:
            w = np.ones(len(keys))
        else:
            Lk = np.array([prev[u] if u in prev else np.median(list(prev.values())) for u in keys])
            w = np.exp(-eta * (Lk - Lk.min()))
        w /= w.sum()
        inner, dflt = sum(wi * st["P"][u] for wi, u in zip(w, keys)), st["P"][default]
        if last is not None:
            Lo = g2 * Lo + last
        a = np.exp(-e2 * (g2 if temper else 1.0) * (Lo - Lo.min())); a /= a.sum()
        mix = a[0] * dflt + a[1] * inner
        acc[t] = (mix.argmax(1) == yq).mean()
        if collect is not None:
            collect.append((t, mix))
        if outer == "brier":  # v3: bounded outer loss, 10 x the half Brier score in [0, 1] (MOOE assumes losses in [0, 1])
            hb = lambda Q: 0.5 * ((Q - np.eye(Q.shape[1])[yq]) ** 2).sum(1).mean()
            last = scale * np.array([hb(dflt), hb(inner)])
        else:
            last = np.array([ll(dflt, yq).mean(), ll(inner, yq).mean()])
        prev = {u: ll(P, yq).mean() for u, P in st["P"].items()}
    return acc


def freeze2(d, method, out_name, **kw):
    """Write <stream>__<out_name>.npz for the two-timescale rule applied to the cached experts of `method`."""
    for f in sorted(glob.glob(f"{d}/*__{method}.pkl")):
        c = pickle.load(open(f, "rb"))
        acc = simulate2(c, **kw)
        T = len(c["y"]) // c["B"]
        a = np.full(T, np.nan)
        for t, v in acc.items():
            a[t] = v
        z = np.load(f[:-4] + ".npz")
        np.savez_compressed(f.replace(f"__{method}.pkl", f"__{out_name}.npz"), acc=a, ll=np.full(T, np.nan), wt=z["wt"],
                            B=c["B"], concept=c["concept"], calls=z["calls"], n_experts=z["n_experts"])
