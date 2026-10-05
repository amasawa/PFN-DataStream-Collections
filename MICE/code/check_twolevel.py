"""Offline (cached expert predictions, no TFM call). Two-level meta expert: for each discount gamma in G a base
forecaster w ~ exp(-eta * L_gamma) over the in-context experts; a top forecaster mixes the base forecasters by
exponential weights on their own discounted log-loss (discount g_top). The frozen rule is G = {0}.
Usage: python check_twolevel.py dir [dir ...]"""
import glob, pickle, sys
import numpy as np, pandas as pd


def run(c, G, eta=10.0, eta_top=10.0, g_top=0.9):
    cache, y, B = c["cache"], c["y"], c["B"]
    L = {g: {} for g in G}; Ltop = {g: 0.0 for g in G}; prev = None; acc = []
    for i, st in enumerate(cache):
        if i > 0:
            pv = cache[i - 1]; yb = y[pv["t"] * B:(pv["t"] + 1) * B]
            for g in G:  # top level: loss of each base forecaster's last prediction
                Ltop[g] = g_top * Ltop[g] - np.log(np.clip(prev[g][np.arange(len(yb)), yb], 1e-6, 1)).mean()
            for u, P in pv["P"].items():
                l = -np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean()
                for g in G:
                    L[g][u] = g * L[g][u] + l if u in L[g] else l
        keys = list(st["P"]); prev = {}
        for g in G:
            Lk = np.array([L[g].get(u, np.median(list(L[g].values())) if L[g] else 0.0) for u in keys])
            w = np.exp(-eta * (Lk - Lk.min())); w /= w.sum()
            prev[g] = sum(wi * st["P"][u] for wi, u in zip(w, keys))
        lt = np.array([Ltop[g] for g in G]); wt = np.exp(-eta_top * (lt - lt.min())); wt /= wt.sum()
        P = sum(wi * prev[g] for wi, g in zip(wt, G))
        yq = y[st["t"] * B:(st["t"] + 1) * B]; acc.append((P.argmax(1) == yq).mean())
    return float(np.mean(acc))


if __name__ == "__main__":
    rows = []
    for d in sys.argv[1:]:
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            c = pickle.load(open(f, "rb")); s = f.split("/")[-1].split("__")[0]
            rows.append(dict(stream=s, frozen=run(c, (0.0,)), g05=run(c, (0.5,)), g09=run(c, (0.9,)),
                             two=run(c, (0.0, 0.5, 0.9)), two_fast=run(c, (0.0, 0.5, 0.9), g_top=0.5), two_wide=run(c, (0.0, 0.5, 0.9, 0.98))))
    r = pd.DataFrame(rows); r["family"] = r.stream.str.replace(r"_s\d+$", "", regex=True)
    pd.set_option("display.width", 200)
    print(r.groupby("family").mean(numeric_only=True).round(4).to_string())
    print("mean", r.mean(numeric_only=True).round(4).to_dict())
