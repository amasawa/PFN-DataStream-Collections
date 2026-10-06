"""Metrics and decision rules for ../results/duo/*.npz (design: logs/EXPERIMENT_LOG.md, 2026-10-06). MICE's final
method and FIFO per batch come from ../results/mice_reference.npz (exported once from MICE's results; same protocol and
backbone), compared on the same batches. Metrics: accuracy, macro-F1, ROC AUC, ECE (Drift-Resilient TabPFN) + log-loss."""
import glob, os
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

ref = np.load("../results/mice_reference.npz")


def met(P, y):
    P = P.astype(np.float64); P /= np.clip(P.sum(1, keepdims=True), 1e-12, None); pred, conf = P.argmax(1), P.max(1); pres = np.unique(y)
    bins = np.minimum((conf * 15).astype(int), 14)
    ece = sum(abs((pred[bins == b] == y[bins == b]).mean() - conf[bins == b].mean()) * (bins == b).mean() for b in range(15) if (bins == b).any())
    auc = roc_auc_score(y == pres[1], P[:, pres[1]]) if len(pres) == 2 else roc_auc_score(
        y, P[:, pres] / np.clip(P[:, pres].sum(1, keepdims=True), 1e-12, None), labels=pres, multi_class="ovr")
    return dict(acc=100 * (pred == y).mean(), macro_f1=100 * f1_score(y, pred, labels=pres, average="macro", zero_division=0),
                roc_auc=100 * auc, ece=100 * ece, logloss=-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean())


rows = []
for f in sorted(glob.glob("../results/duo/*.npz")):
    s = os.path.basename(f)[:-4]; z = np.load(f); y = z["y"]; T = len(y)
    for k in ("fifo", "sel", "duo"):
        rows.append(dict(stream=s, method=k, **met(z[f"P_{k}"][1:].reshape(-1, z[f"P_{k}"].shape[2]), y[1:].reshape(-1))))
    rows.append(dict(stream=s, method="mice", acc=100 * np.nanmean(ref[s][1:T])))
    rows.append(dict(stream=s, method="fifo_ref", acc=100 * np.nanmean(ref[s + "__fifo"][1:T])))
r = pd.DataFrame(rows); r.to_csv("../results/duo_metrics.csv", index=False); pd.set_option("display.width", 200)
a = r.pivot_table(index="stream", columns="method", values="acc")
print(a.round(2).to_string()); print("mean", a.mean().round(2).to_dict())
print(r[r.method.isin(["fifo", "sel", "duo"])].groupby("method")[["acc", "macro_f1", "roc_auc", "ece", "logloss"]].mean().round(3).to_string())
d1 = a.duo - a.fifo; d2 = a.duo - a.mice
print(f"check: fifo here vs MICE's fifo, max abs diff {(a.fifo - a.fifo_ref).abs().max():.3f}")
print(f"D1: duo - fifo mean {d1.mean():+.2f} (need >= +0.50), better on {(d1 > 0).sum()}/{len(d1)} (need 5/7)")
print(f"D2: duo - mice mean {d2.mean():+.2f} (need >= 0), better on {(d2 > 0).sum()}/{len(d2)}")
