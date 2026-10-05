"""Cache replay, no TFM call. Small-margin regime of the meta expert: with weights w from the losses of the last
labelled batch (eta = 10), Jensen gives  ll_mix(j) <= min_k l_k(j) + sum_k w_k D_k + delta_j,  where
D_k = l_k(j-1) - min l(j-1) and delta_j = max_k [(l_k(j) - l_best(j)) - (l_k(j-1) - l_best(j-1))] measures how much
the relative losses move between consecutive batches. Reports each term. Usage: python check_persist.py <dir>"""
import glob, pickle, sys, numpy as np, pandas as pd
rows = []
for f in sorted(glob.glob(f"{sys.argv[1]}/*__micev1000_500.pkl")):
    c = pickle.load(open(f, "rb")); cache, y, B = c["cache"], c["y"], c["B"]
    name = f.split("/")[-1].split("__")[0]
    ll = lambda P, yy: -np.log(np.clip(P[np.arange(len(yy)), yy], 1e-6, 1)).mean()
    for i in range(1, len(cache)):
        pv, st = cache[i - 1], cache[i]
        yb = y[pv["t"] * B:(pv["t"] + 1) * B]; yq = y[st["t"] * B:(st["t"] + 1) * B]
        keys = [u for u in st["P"] if u in pv["P"]]
        L = np.array([ll(pv["P"][u], yb) for u in keys]); Ln = np.array([ll(st["P"][u], yq) for u in keys])
        D = L - L.min(); w = np.exp(-10 * D); w /= w.sum(); b = Ln.argmin()
        delta = np.max((Ln - Ln[b]) - (L - L[b]))
        mix = ll(sum(wi * st["P"][u] for wi, u in zip(w, keys)), yq)
        rows.append(dict(stream=name, regret=mix - Ln.min(), jensen=w @ Ln - Ln.min(), wD=w @ D, meanD=D.mean(), lnK_eta=np.log(len(keys)) / 10,
                         delta=delta, bound=w @ D + delta, holds=mix - Ln.min() <= w @ D + delta + 1e-9))
d = pd.DataFrame(rows); d["family"] = d.stream.str.replace(r"_s\d+$", "", regex=True)
pd.set_option("display.width", 200)
print(d.groupby("family").mean(numeric_only=True).round(3).to_string())
