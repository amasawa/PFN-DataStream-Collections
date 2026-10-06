"""Probe of training-free repairs of a contaminated context (see logs/EXPERIMENT_LOG.md, 2026-10-06, for the variants
and the decision rule written beforehand). All repairs only rewrite the labels (or the rows) of the context of a frozen
TabPFN; confidences come from 5-fold held-out predictions of the same model (context swaps).
Usage: python check_repair.py -> ../results/repair.csv"""
import warnings
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedKFold
from check_label_noise import DATA, SETS, N_CTX, N_TEST, SEEDS, tabpfn, corrupt

warnings.filterwarnings("ignore")


def oof(Xc, yn, K, seed):
    P = np.zeros((len(yn), K))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(Xc, yn):
        f = tabpfn(seed).fit(Xc[tr], yn[tr]); P[np.ix_(te, f.classes_.astype(int))] = f.predict_proba(Xc[te])
    return P


def acc(Xc, yc, Xt, yt, seed):
    if len(np.unique(yc)) < 2:
        return float((yt == yc[0]).mean())
    return float((tabpfn(seed).fit(Xc, yc).predict(Xt) == yt).mean())


def soft_copies(yn, P, R=4):
    """R copies per row; labels allotted in proportion to c * onehot(given) + (1 - c) * P restricted to the other classes."""
    n, K = P.shape; idx, lab = [], []
    for i in range(n):
        c = P[i, yn[i]]; q = P[i].copy(); q[yn[i]] = 0
        q = (1 - c) * q / q.sum() if q.sum() > 0 else q
        q[yn[i]] = c; q = q / q.sum()
        cnt = np.floor(q * R).astype(int); rem = R - cnt.sum()
        if rem > 0:
            for k in np.argsort(-(q * R - cnt))[:rem]:
                cnt[k] += 1
        for k in np.flatnonzero(cnt):
            idx += [i] * cnt[k]; lab += [k] * cnt[k]
    return np.array(idx), np.array(lab)


import os
rows = pd.read_csv("../results/repair.csv").to_dict("records") if os.path.exists("../results/repair.csv") else []
done = {(r["data"], int(r["seed"])) for r in rows if r["kind"] == "asym"}   # resume after a CUDA failure (added 2026-10-06)
rows = [r for r in rows if (r["data"], int(r["seed"])) in done]
for name in SETS:
    z = np.load(f"{DATA}/{name}.npz"); X, y = np.nan_to_num(z["X"][:100_000].astype(np.float32)), z["y"][:100_000].astype(int)
    for seed in SEEDS:
        if (name, seed) in done:
            continue
        rng = np.random.default_rng(1000 + seed)
        pool = rng.choice(len(y), min(len(y), 20_000), replace=False)
        keep = [k for k in np.unique(y[pool]) if (y[pool] == k).sum() >= 20]
        pool = pool[np.isin(y[pool], keep)]; lab = {k: i for i, k in enumerate(keep)}; K = len(keep)
        ctx, test = pool[:N_CTX], pool[N_CTX:N_CTX + N_TEST]
        Xc, yc = X[ctx], np.array([lab[v] for v in y[ctx]]); Xt, yt = X[test], np.array([lab[v] for v in y[test]])
        a_clean = acc(Xc, yc, Xt, yt, seed)
        for kind in ("sym", "asym"):
            yn, flip = corrupt(yc, kind, 0.2, K, np.random.default_rng(2000 + seed))
            P = oof(Xc, yn, K, seed); pg = P[np.arange(len(yn)), yn]; hat = P.argmax(1)
            sus = (hat != yn) & (pg < 0.2)
            r = dict(clean=a_clean, noisy=acc(Xc, yn, Xt, yt, seed), oracle_drop=acc(Xc[~flip], yn[~flip], Xt, yt, seed),
                     drop_dis=acc(Xc[~sus], yn[~sus], Xt, yt, seed))
            y1 = np.where(sus, hat, yn); r["relabel"] = acc(Xc, y1, Xt, yt, seed)
            P2 = oof(Xc, y1, K, seed); s2 = (P2.argmax(1) != y1) & (P2[np.arange(len(y1)), y1] < 0.2)
            y2 = np.where(s2, P2.argmax(1), y1); r["relabel2"] = acc(Xc, y2, Xt, yt, seed)
            i4, l4 = soft_copies(yn, P); r["soft4"] = acc(Xc[i4], l4, Xt, yt, seed)
            r["rep4"] = acc(np.repeat(Xc, 4, 0), np.repeat(yn, 4), Xt, yt, seed)
            rows.append(dict(data=name, seed=seed, kind=kind, K=K, flipped=float(flip.mean()), flagged=float(sus.mean()),
                             flag_precision=float(flip[sus].mean()) if sus.any() else np.nan, flag_recall=float(sus[flip].mean()),
                             relabel_correct=float((y1[sus] == yc[sus]).mean()) if sus.any() else np.nan,
                             wrong_after_relabel=float((y1 != yc).mean()), wrong_after_relabel2=float((y2 != yc).mean()), **r))
        print(name, seed, "done", flush=True)
        pd.DataFrame(rows).to_csv("../results/repair.csv", index=False)

r = pd.DataFrame(rows); pd.set_option("display.width", 250)
V = ["oracle_drop", "drop_dis", "relabel", "relabel2", "soft4", "rep4"]
for kind in ("sym", "asym"):
    g = r[r.kind == kind].groupby("data").mean(numeric_only=True)
    loss = g.clean - g.noisy
    rec = pd.DataFrame({v: (g[v] - g.noisy) / loss for v in V})
    print(f"== {kind} 20%: accuracy (%), mean over data sets"); print((100 * g[["clean", "noisy"] + V].mean()).round(2).to_string())
    print("share of the loss recovered per data set"); print(rec.round(2).to_string())
    tot = {v: float((g[v] - g.noisy).sum() / loss.sum()) for v in V}
    print("overall share recovered:", {k: round(x, 2) for k, x in tot.items()}, "| data sets not worse than noisy:", {v: int((g[v] >= g.noisy - 1e-9).sum()) for v in V})
    print("flags: share flagged %.3f, precision %.3f, recall %.3f, relabelled to the true class %.3f; wrong labels 20%% -> %.1f%% -> %.1f%%" % (
        g.flagged.mean(), g.flag_precision.mean(), g.flag_recall.mean(), g.relabel_correct.mean(), 100 * g.wrong_after_relabel.mean(), 100 * g.wrong_after_relabel2.mean()))
