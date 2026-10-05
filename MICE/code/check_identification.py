"""Dev grid only: how well does the frozen rule (eta=10, last labelled batch) identify the best expert?"""
import glob, pickle, numpy as np, pandas as pd
rows = []
for f in sorted(glob.glob("../results_grid_dev/*__micev1000_500.pkl")):
    c = pickle.load(open(f, "rb")); cache, y, B, conc = c["cache"], c["y"], c["B"], c["concept"]
    name = f.split("/")[-1].split("__")[0]
    seen = set(); prevc = None; pos = 0
    for i, st in enumerate(cache):
        t = st["t"]; ck = conc[t * B]
        if ck != prevc: pos = 0; recur = ck in seen; seen.add(ck); prevc = ck
        else: pos += 1
        if i == 0: continue
        pv = cache[i - 1]; yb = y[pv["t"] * B:(pv["t"] + 1) * B]; yq = y[t * B:(t + 1) * B]
        keys = [u for u in st["P"] if u in pv["P"]]
        if not keys: continue
        L = np.array([-np.log(np.clip(pv["P"][u][np.arange(len(yb)), yb], 1e-6, 1)).mean() for u in keys])
        w = np.exp(-10 * (L - L.min())); w /= w.sum()
        accs = np.array([(st["P"][u].argmax(1) == yq).mean() for u in keys])
        lls = np.array([-np.log(np.clip(st["P"][u][np.arange(len(yq)), yq], 1e-6, 1)).mean() for u in keys])
        mix = sum(wi * st["P"][u] for wi, u in zip(w, keys))
        srt = np.sort(L)
        rows.append(dict(stream=name[:-3], recur=recur, pos=min(pos, 3), wmax=w.max(), gap=srt[1] - srt[0] if len(srt) > 1 else np.nan,
                         acc_mix=(mix.argmax(1) == yq).mean(), acc_best=accs.max(), acc_leader=accs[L.argmin()],
                         ll_mix=-np.log(np.clip(mix[np.arange(len(yq)), yq], 1e-6, 1)).mean(), ll_best=lls.min(), K=len(keys)))
d = pd.DataFrame(rows); pd.set_option("display.width", 220)
print(d[d.recur].groupby(["stream", "pos"]).mean(numeric_only=True).round(3).to_string())
