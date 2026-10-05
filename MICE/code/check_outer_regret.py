"""Cache replay (no TFM call) of the outer level of the two-timescale meta expert on the DEVELOPMENT caches only
(replay_rules.GROUPS; the third held-out set is not read). Outer loss: half Brier score in [0, 1], discount g2 = 0.9.
For each step eta (in half-Brier units; the frozen mice3 uses 10) and for plain weights exp(-eta L) or tempered weights
exp(-eta g2 L) it reports the accuracy and the discounted regret max_T sum_t g2^(T-t) (loss_mix - loss_k) against the
default expert and against the inner mixture. The half Brier score is 1/2-exp-concave on the simplex, so for
eta <= 1/2 and tempered weights the discounted regret is at most ln(2) / eta.
Usage: python check_outer_regret.py -> ../results_rules/outer_regret.csv"""
import glob, os
import numpy as np, pandas as pd
from replay_rules import GROUPS, DEF, load

ETAS, G2 = (0.5, 1.0, 2.0, 10.0), 0.9
VARIANTS = [(e, t) for e in ETAS for t in (False, True)]


def replay(steps):
    hb = lambda Q, yq: 0.5 * ((Q - np.eye(Q.shape[1])[yq]) ** 2).sum(1).mean()
    L = {k: np.zeros(2) for k in VARIANTS}      # discounted losses of (default, inner)
    R = {k: np.zeros(2) for k in VARIANTS}      # discounted regret of the outer mixture against (default, inner)
    out = {k: dict(acc=[], loss=[], rmax=np.full(2, -np.inf)) for k in VARIANTS}
    base = dict(default=[], inner=[], hb_default=[], hb_inner=[])
    prev = None
    for P, loss, yq in steps:
        keys = list(P)
        if prev is None:
            w = np.ones(len(keys))
        else:
            Lk = np.array([prev[u].mean() if u in prev else np.median([v.mean() for v in prev.values()]) for u in keys])
            w = np.exp(-10 * (Lk - Lk.min()))
        w /= w.sum()
        inner, dflt = sum(wi * P[u] for wi, u in zip(w, keys)), P[DEF]
        l2 = np.array([hb(dflt, yq), hb(inner, yq)])
        base["default"].append((dflt.argmax(1) == yq).mean()); base["inner"].append((inner.argmax(1) == yq).mean())
        base["hb_default"].append(l2[0]); base["hb_inner"].append(l2[1])
        for k in VARIANTS:
            eta, temp = k
            s = eta * (G2 if temp else 1.0) * L[k]
            a = np.exp(-(s - s.min())); a /= a.sum()
            mix = a[0] * dflt + a[1] * inner
            lm = hb(mix, yq)
            out[k]["acc"].append((mix.argmax(1) == yq).mean()); out[k]["loss"].append(lm)
            R[k] = G2 * R[k] + (lm - l2); out[k]["rmax"] = np.maximum(out[k]["rmax"], R[k])
            L[k] = G2 * L[k] + l2
        prev = loss
    r = {k: float(np.mean(v)) for k, v in base.items()}
    for (eta, temp), o in out.items():
        n = f"{eta:g}{'t' if temp else ''}"
        r.update({f"acc_{n}": np.mean(o["acc"]), f"hb_{n}": np.mean(o["loss"]), f"rdef_{n}": o["rmax"][0], f"rinn_{n}": o["rmax"][1]})
    return r


if __name__ == "__main__":
    from joblib import Parallel, delayed
    jobs = []
    for g, d in GROUPS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if not (g == "real_dev5" and s[-4:-2] == "_s"):
                jobs.append((g, s, f))
    res = pd.DataFrame(Parallel(n_jobs=16)(delayed(lambda g, s, f: dict(group=g, stream=s, **replay(load(f))))(*j) for j in jobs))
    res.to_csv("../results_rules/outer_regret.csv", index=False)
    pd.set_option("display.width", 250)
    names = [f"{e:g}{'t' if t else ''}" for e, t in VARIANTS]
    print("accuracy (%) per group")
    print((100 * res.groupby("group")[["default", "inner"] + [f"acc_{n}" for n in names]].mean()).round(2).T.to_string())
    print("mean half Brier per group")
    print(res.groupby("group")[["hb_default", "hb_inner"] + [f"hb_{n}" for n in names]].mean().round(4).T.to_string())
    print("max discounted regret over all streams (bound ln2/eta for eta <= 0.5, tempered: %.3f)" % (np.log(2) / 0.5))
    print(pd.DataFrame({n: dict(vs_default=res[f"rdef_{n}"].max(), vs_inner=res[f"rinn_{n}"].max(),
                                bound=np.log(2) / float(n.rstrip("t"))) for n in names}).round(3).to_string())
    real = res[res.group.str.startswith("real")].set_index("stream")
    best = real[["default", "inner"]].max(1)
    print("15 real streams, accuracy gap (points) to max(default, inner): worst / mean")
    print(pd.DataFrame({n: dict(worst=100 * (real[f"acc_{n}"] - best).min(), mean=100 * (real[f"acc_{n}"] - best).mean(),
                                vs_default_worst=100 * (real[f"acc_{n}"] - real.default).min()) for n in names}).round(2).to_string())
