"""Cache replay of weighting rules (no TFM call). Every rule sees, for each expert, the per-row log-losses on the batches
whose labels have arrived, and returns mixture weights for the next batch.
  hedge(eta, gamma)        w ~ exp(-eta L), L <- gamma L + mean loss on the last labelled batch (frozen rule: 10, 0)
  gate(eta, z0, H)         default = the M-row window. Another expert enters the mixture only if it beats the default
                           significantly: paired one-sided z-statistic of the per-row loss difference over the last h
                           labelled batches, for some h in H, above z0. Weights among the admitted experts and the
                           default ~ exp(-eta * mean loss on the last labelled batch).
  prior(eta, pi)           hedge(eta, 0) with prior weight pi on the default and (1 - pi) spread over the others
Usage: python replay_rules.py   -> ../results_rules/rules.csv and a table per group of streams."""
import glob, os, pickle, sys
import numpy as np, pandas as pd

GROUPS = {"grid_dev": "../results_grid_dev", "fam_dev": "../results_dev", "real_dev5": "../results_test",
          "real_C": "../results_heldout", "real_G": "../results_heldout2"}
DEF = -1000


def load(f):
    c = pickle.load(open(f, "rb")); y, B = c["y"], c["B"]
    steps = []
    for st in c["cache"]:
        yq = y[st["t"] * B:(st["t"] + 1) * B]
        steps.append((st["P"], {u: -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)) for u, P in st["P"].items()}, yq))
    return steps


def replay(steps, rule):
    acc, hist = [], []            # hist: per-row loss dicts of labelled batches, newest last
    L = {}
    for P, loss, yq in steps:
        keys = list(P)
        if rule[0] == "hedge":
            _, eta, gamma = rule
            if hist:
                for u, l in hist[-1].items():
                    L[u] = gamma * L[u] + l.mean() if u in L else l.mean()
            Lk = np.array([L.get(u, np.median(list(L.values())) if L else 0.0) for u in keys])
            w = np.exp(-eta * (Lk - Lk.min()))
        elif rule[0] == "prior":
            _, eta, pi = rule
            Lk = np.array([hist[-1][u].mean() if hist and u in hist[-1] else np.nan for u in keys])
            Lk = np.where(np.isnan(Lk), np.nanmedian(Lk) if hist else 0.0, Lk)
            pr = np.array([pi if u == DEF else (1 - pi) / max(len(keys) - 1, 1) for u in keys])
            w = pr * np.exp(-eta * (Lk - Lk.min()))
        else:
            _, eta, z0, H = rule
            adm, Lk = [], []
            for u in keys:
                ok = u == DEF
                if not ok and hist and u in hist[-1]:
                    for h in H:
                        d = np.concatenate([b[DEF] - b[u] for b in hist[-h:] if u in b and DEF in b])
                        if len(d) and d.mean() / (d.std() / np.sqrt(len(d)) + 1e-12) > z0:
                            ok = True; break
                adm.append(ok); Lk.append(hist[-1][u].mean() if hist and u in hist[-1] else 0.0)
            adm, Lk = np.array(adm), np.array(Lk)
            w = np.where(adm, np.exp(-eta * (Lk - Lk[adm].min())), 0.0)
        w = w / w.sum()
        mix = sum(wi * P[u] for wi, u in zip(w, keys))
        acc.append((mix.argmax(1) == yq).mean())
        hist.append(loss); hist = hist[-10:]
    return float(np.mean(acc))


RULES = {"frozen": ("hedge", 10, 0.0), "orig": ("hedge", 2, 0.5), "hedge5_0": ("hedge", 5, 0.0), "hedge10_.5": ("hedge", 10, 0.5),
         "prior.5": ("prior", 10, 0.5), "prior.8": ("prior", 10, 0.8), "prior.95": ("prior", 10, 0.95)}
for z0 in (1.0, 2.0, 3.0):
    for H in ((1,), (1, 3), (1, 3, 10)):
        RULES[f"gate_z{z0:g}_H{'-'.join(map(str, H))}"] = ("gate", 10, z0, H)

if __name__ == "__main__":
    from joblib import Parallel, delayed
    os.makedirs("../results_rules", exist_ok=True)
    jobs = []
    for g, d in GROUPS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if g == "real_dev5" and s[-4:-2] == "_s":   # the family test streams live in the same folder: not here
                continue
            jobs.append((g, d, s, f))

    def one(g, d, s, f):
        steps = load(f)
        r = dict(group=g, stream=s)
        for b in ("fifo1000", "ddm1000", "winens1000"):
            p = f"{d}/{s}__{b}.npz"
            r[b[:-4]] = float(np.nanmean(np.load(p)["acc"])) if os.path.exists(p) else np.nan
        for name, rule in RULES.items():
            r[name] = replay(steps, rule)
        return r
    res = pd.DataFrame(Parallel(n_jobs=16)(delayed(one)(*j) for j in jobs))
    res.to_csv("../results_rules/rules.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.groupby("group").size().to_dict())
    print((100 * res.groupby("group").mean(numeric_only=True)).round(2).T.to_string())
    real = res[res.group.str.startswith("real")].set_index("stream")
    print((100 * real[["fifo", "ddm", "winens", "frozen"] + [c for c in real.columns if c.startswith("gate_z2") or c.startswith("prior")]]).round(2).to_string())
