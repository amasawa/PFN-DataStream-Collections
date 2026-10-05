"""Metrics beyond accuracy from the cached expert predictions (no TFM call): macro-F1, one-vs-rest ROC AUC (macro over
the classes that occur), expected calibration error (15 bins, top label), half Brier score and log-loss, per stream and
method. Methods available from a cache: the method of the paper (mice), the pre-registered step (mice10), the fast
level alone (fast), the window ensemble (winens, replay of its rule eta = 2, gamma = 0.5 over the three windows) and
FIFO (the M-row window expert). ddm and ltm are added when run_probs.py has stored their probabilities.
Usage: python compute_metrics.py -> ../results_paper/metrics.csv"""
import glob, os, pickle
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score
import reweight
from make_paper_tables import DIRS


def metrics(P, y, nb=15):
    P = np.clip(P, 0, 1); P = P / P.sum(1, keepdims=True)
    pred, conf = P.argmax(1), P.max(1)
    labs = np.unique(y)
    aucs = [roc_auc_score(y == k, P[:, k]) for k in labs if 0 < (y == k).sum() < len(y)]
    b = np.minimum((conf * nb).astype(int), nb - 1); ece = 0.0
    for i in range(nb):
        m = b == i
        if m.any():
            ece += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    E = np.zeros_like(P); E[np.arange(len(y)), y] = 1
    return dict(acc=(pred == y).mean(), f1=f1_score(y, pred, average="macro", labels=labs), auc=float(np.mean(aucs)), ece=ece,
                brier=0.5 * ((P - E) ** 2).sum(1).mean(), nll=-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean(),
                entropy=-(P * np.log(np.clip(P, 1e-12, 1))).sum(1).mean())


def stack(col, y, B):
    col = sorted(col, key=lambda z: z[0])
    return np.concatenate([P for _, P in col]), np.concatenate([y[t * B:(t + 1) * B] for t, _ in col])


def one(g, d, f):
    s = os.path.basename(f).split("__")[0]; c = pickle.load(open(f, "rb")); y, B = c["y"], c["B"]
    grp = g if g != "fam" else ("fam" if s[-4:-2] == "_s" or s[-3:-1] == "_s" else "realD")
    out, win = [], lambda u: u < 0
    runs = {"mice": lambda col: reweight.simulate2(c, outer="brier", scale=0.5, temper=True, collect=col),
            "mice10": lambda col: reweight.simulate2(c, outer="brier", collect=col),
            "fast": lambda col: reweight.simulate(c, 10, 0.0, collect=col),
            "winens": lambda col: reweight.simulate(c, 2.0, 0.5, subset=win, collect=col)}
    for name, fn in runs.items():
        col = []; fn(col); P, yy = stack(col, y, B)
        out.append(dict(group=grp, stream=s, method=name, **metrics(P, yy)))
    P, yy = stack([(st["t"], st["P"][-1000]) for st in c["cache"]], y, B)
    out.append(dict(group=grp, stream=s, method="fifo", **metrics(P, yy)))
    for b, name in (("ddm1000", "ddm"), ("ltm1000_75", "ltm")):     # stored by run_probs.py
        h = f"../results_probs/{s}__{b}__probs.npz"
        if os.path.exists(h):
            z = np.load(h); out.append(dict(group=grp, stream=s, method=name, **metrics(z["P"].astype(float), y[B:B + len(z["P"])])))
    # reference accuracies of the baseline files, to check the replays
    for b, name in (("fifo1000", "fifo"), ("winens1000", "winens")):
        h = f"{d}/{s}__{b}.npz"
        if os.path.exists(h):
            out.append(dict(group=grp, stream=s, method=name + "_file", acc=float(np.nanmean(np.load(h)["acc"]))))
    return out


if __name__ == "__main__":
    from joblib import Parallel, delayed
    jobs = [(g, d, f) for g, d in DIRS.items() if g != "tabicl" for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl"))]
    rows = sum(Parallel(n_jobs=4)(delayed(one)(*j) for j in jobs), [])
    a = pd.DataFrame(rows); a.to_csv("../results_paper/metrics.csv", index=False)
    pd.set_option("display.width", 250)
    chk = a.pivot_table(index="stream", columns="method", values="acc")
    for k in ("fifo", "winens"):
        if k + "_file" in chk:
            d = (chk[k] - chk[k + "_file"]).abs()
            print(f"replay check {k}: max |accuracy difference| to the baseline file = {d.max():.5f} over {d.notna().sum()} streams")
    a = a[~a.method.str.endswith("_file")]
    a["set"] = a.group.replace({"grid10": "grid", "grid20": "grid", "realD": "real", "realC": "real", "realG": "real", "realH": "real", "realI": "real"})
    for m in ("acc", "f1", "auc", "ece", "brier", "nll", "entropy"):
        print(m); print((100 * a.pivot_table(index="set", columns="method", values=m)).round(2).to_string())
    r = a[a.set == "real"]
    for m, sign in (("f1", 1), ("auc", 1), ("ece", -1), ("brier", -1), ("nll", -1)):
        p = r.pivot_table(index="stream", columns="method", values=m); d = sign * (p.mice - p.fifo)
        print(f"real streams, {m}: mice better than fifo on {(d > 0).sum()} of {len(d)}; worst {100 * d.min():+.2f}, mean {100 * d.mean():+.2f} (positive = mice better)")
