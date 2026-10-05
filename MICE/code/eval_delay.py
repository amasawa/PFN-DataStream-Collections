"""Applies weighting rules to the caches of run_delay.py, causally: at batch t the losses are those of the experts'
predictions for batch t - d (the newest batch whose labels have arrived); the discrepancy uses the unlabelled batch t.
  w ~ exp(-eta * (L - min L)) * exp(-lam * (disc - min disc))
Rules: label (lam = 0), prior (eta = 0), both; `win` = the same rules restricted to the window experts (no memory).
Usage: python eval_delay.py <dir>"""
import glob, os, pickle, sys
import numpy as np, pandas as pd


def rule(c, eta=10.0, lam=0.0, subset=None):
    cache, y, B, d = c["cache"], c["y"], c["B"], c["d"]
    acc = []
    for i, st in enumerate(cache):
        L = {}
        if i >= d:
            pv = cache[i - d]; yb = y[pv["t"] * B:(pv["t"] + 1) * B]
            L = {u: -np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean() for u, P in pv["P"].items()}
        keys = [u for u in st["P"] if subset is None or subset(u)]
        med = np.median(list(L.values())) if L else 0.0
        Lk = np.array([L.get(u, med) for u in keys]); dk = np.array([st["disc"][u] for u in keys])
        w = np.exp(-(eta * (Lk - Lk.min()) + lam * (dk - dk.min()))); w /= w.sum()
        P = sum(wi * st["P"][u] for wi, u in zip(w, keys)); yq = y[st["t"] * B:(st["t"] + 1) * B]
        acc.append((P.argmax(1) == yq).mean())
    return float(np.mean(acc))


if __name__ == "__main__":
    rows = []
    for f in sorted(glob.glob(f"{sys.argv[1]}/*__mice.pkl")):
        c = pickle.load(open(f, "rb")); stream, dd, _ = os.path.basename(f).split("__")
        win = lambda u: u < 0
        r = dict(stream=stream, d=c["d"])
        for k in ("fifo", "ddm"):
            g = f.replace("mice.pkl", k + ".npz")
            r[k] = float(np.nanmean(np.load(g)["acc"])) if os.path.exists(g) else np.nan
        r.update(win_label=rule(c, subset=win), win_both=rule(c, lam=10.0, subset=win), mice_label=rule(c),
                 mice_prior=rule(c, eta=0.0, lam=10.0), mice_both=rule(c, lam=10.0))
        rows.append(r)
    r = pd.DataFrame(rows); pd.set_option("display.width", 220)
    print(r.round(4).to_string(index=False)); print(r.groupby("d").mean(numeric_only=True).round(4).to_string())
    r.to_csv(f"{sys.argv[1]}/eval_delay.csv", index=False)
