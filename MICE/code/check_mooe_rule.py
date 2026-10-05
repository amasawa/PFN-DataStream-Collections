"""Dev caches only (no TFM call): the frozen MICE rule (eta=10 on the last labelled batch) against a meta expert that
follows MOOE Algorithm 1: exponential weights on the cumulative loss inside an interval of T rows, restarted at every
interval boundary, with step nu = 4 sqrt(ln K / T) per row (MOOE Thm 2). `loss` is the log-loss or the 0-1 loss."""
import glob, pickle, sys
import numpy as np, pandas as pd


def simulate(c, rule, T=500, loss="log", eta=10.0):
    cache, y, B = c["cache"], c["y"], c["B"]
    L, acc, n_lab = {}, [], 0
    for i, st in enumerate(cache):
        if i > 0:
            pv = cache[i - 1]
            yb = y[pv["t"] * B:(pv["t"] + 1) * B]
            if rule == "mooe" and n_lab % T == 0:
                L = {}  # interval boundary: restart the meta expert
            for u, P in pv["P"].items():
                l = (-np.log(np.clip(P[np.arange(len(yb)), yb], 1e-6, 1)).mean() if loss == "log"
                     else (P.argmax(1) != yb).mean())
                L[u] = (L.get(u, 0.0) + l) if rule in ("mooe", "cum") else l
            n_lab += len(yb)
        keys = list(st["P"])
        Lk = np.array([L.get(u, np.median(list(L.values())) if L else 0.0) for u in keys])
        K = len(keys)
        e = eta if rule == "last" else 4 * np.sqrt(np.log(max(K, 2)) / T) * B  # per-row step times rows per batch
        w = np.exp(-e * (Lk - Lk.min())); w /= w.sum()
        P = sum(wi * st["P"][u] for wi, u in zip(w, keys))
        yq = y[st["t"] * B:(st["t"] + 1) * B]
        acc.append((P.argmax(1) == yq).mean())
    return float(np.mean(acc))


rows = []
for d in sys.argv[1:]:
    for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
        c = pickle.load(open(f, "rb"))
        s = f.split("/")[-1].split("__")[0]
        rows.append(dict(stream=s, frozen=simulate(c, "last"), mooe_log=simulate(c, "mooe"), mooe_01=simulate(c, "mooe", loss="01"),
                         mooe_T100=simulate(c, "mooe", T=100), cum_log=simulate(c, "cum", T=500)))
r = pd.DataFrame(rows); r["family"] = r.stream.str.replace(r"_s\d+$", "", regex=True)
pd.set_option("display.width", 200)
print(r.groupby("family").mean(numeric_only=True).round(4).to_string())
print("mean", r.mean(numeric_only=True).round(4).to_dict())
