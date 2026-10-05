"""Cache replay (no TFM call) of a two-timescale meta expert. Inner level: the frozen MICE rule (weights from the last
labelled batch, eta = 10). Outer level: exponential weights between the default expert (the M-row FIFO window) and the
inner mixture, on their discounted cumulative log-loss L <- g2 * L + (mean loss on the last labelled batch), step e2.
The outer level is the cumulative meta expert of MOOE with two experts, so it is never much worse than the default.
Usage: python replay_safe.py -> ../results_rules/safe.csv"""
import glob, os
import numpy as np, pandas as pd
from replay_rules import GROUPS, DEF, load

OUTER = [(e2, g2) for e2 in (1.0, 3.0, 10.0) for g2 in (0.9, 0.97, 0.99, 1.0)]


def replay(steps, OUTER=OUTER):
    acc = {k: [] for k in ["inner", "default"] + OUTER}
    Lo = {k: np.zeros(2) for k in OUTER}
    prev = None; last = None
    for P, loss, yq in steps:
        keys = list(P)
        if prev is None:
            w = np.ones(len(keys))
        else:
            Lk = np.array([prev[u].mean() if u in prev else np.median([v.mean() for v in prev.values()]) for u in keys])
            w = np.exp(-10 * (Lk - Lk.min()))
        w /= w.sum()
        inner = sum(wi * P[u] for wi, u in zip(w, keys)); dflt = P[DEF]
        ll = lambda Q: -np.log(np.clip(Q[np.arange(len(yq)), yq], 1e-6, 1)).mean()
        acc["inner"].append((inner.argmax(1) == yq).mean()); acc["default"].append((dflt.argmax(1) == yq).mean())
        for k in OUTER:
            e2, g2 = k
            if last is not None:      # the losses of the previous batch have arrived
                Lo[k] = g2 * Lo[k] + last
            a = np.exp(-e2 * (Lo[k] - Lo[k].min())); a /= a.sum()
            acc[k].append(((a[0] * dflt + a[1] * inner).argmax(1) == yq).mean())
        last = np.array([ll(dflt), ll(inner)]); prev = loss
    return {str(k): float(np.mean(v)) for k, v in acc.items()}


if __name__ == "__main__":
    from joblib import Parallel, delayed
    jobs = []
    for g, d in GROUPS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if not (g == "real_dev5" and s[-4:-2] == "_s"):
                jobs.append((g, s, f))
    res = pd.DataFrame(Parallel(n_jobs=16)(delayed(lambda g, s, f: dict(group=g, stream=s, **replay(load(f))))(*j) for j in jobs))
    res.to_csv("../results_rules/safe.csv", index=False)
    pd.set_option("display.width", 250)
    print((100 * res.groupby("group").mean(numeric_only=True)).round(2).T.to_string())
    real = res[res.group.str.startswith("real")].set_index("stream").drop(columns="group")
    print((100 * real[["default", "inner", "(1.0, 0.99)", "(3.0, 0.99)", "(3.0, 1.0)", "(10.0, 0.97)", "(10.0, 0.99)"]]).round(2).to_string())
    worst = (real.drop(columns=["default", "inner"]).sub(real[["default", "inner"]].max(1), axis=0) * 100)
    print("worst and mean gap to max(default, inner) over the 15 real streams:\n", pd.DataFrame(dict(worst=worst.min(), mean=worst.mean())).round(2).T.to_string())
