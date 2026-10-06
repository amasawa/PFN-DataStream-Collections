"""Metrics and decision rules for ../results/featevo/*.npz (design: logs/EXPERIMENT_LOG.md, 2026-10-06).
Periods relative to the first post-switch batch ts: pre = ts-10..ts-1, early = ts..ts+9, late = ts+30..ts+59.
Metrics: accuracy, macro-F1, ROC AUC (one-vs-rest macro), ECE (15 bins), log-loss (Drift-Resilient TabPFN metrics plus)."""
import glob, os
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

POLS = ("union", "shared", "new", "settled", "oracle"); FEAS = ("union", "shared", "new")


def met(P, y):
    P = P.astype(np.float64); P /= np.clip(P.sum(1, keepdims=True), 1e-12, None); pred, conf = P.argmax(1), P.max(1); pres = np.unique(y)
    bins = np.minimum((conf * 15).astype(int), 14)
    ece = sum(abs((pred[bins == b] == y[bins == b]).mean() - conf[bins == b].mean()) * (bins == b).mean() for b in range(15) if (bins == b).any())
    try:
        auc = roc_auc_score(y == pres[1], P[:, pres[1]]) if len(pres) == 2 else roc_auc_score(
            y, P[:, pres] / np.clip(P[:, pres].sum(1, keepdims=True), 1e-12, None), labels=pres, multi_class="ovr")
    except (ValueError, IndexError):
        auc = np.nan
    return dict(acc=(pred == y).mean(), macro_f1=f1_score(y, pred, labels=pres, average="macro", zero_division=0), roc_auc=auc, ece=ece,
                logloss=-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean())


rows = []
for f in sorted(glob.glob("../results/featevo/*.npz")):
    z = np.load(f); t, ts, y = z["t"], int(z["ts"]), z["y"]
    for per, (a, b) in {"pre": (ts - 10, ts), "early": (ts, ts + 10), "late": (ts + 30, ts + 60)}.items():
        w = (t >= a) & (t < b)
        if not w.any():
            continue
        for p in POLS:
            rows.append(dict(stream=os.path.basename(f)[:-4], source=os.path.basename(f).split("__")[0], split=os.path.basename(f)[:-4].split("__")[1],
                             period=per, policy=p, **met(z[f"P_{p}"][w].reshape(-1, z[f"P_{p}"].shape[2]), y[w].reshape(-1))))
r = pd.DataFrame(rows); r.to_csv("../results/featevo_metrics.csv", index=False); pd.set_option("display.width", 220)
for per in ("pre", "early", "late"):
    m = r[r.period == per].groupby("policy")[["acc", "macro_f1", "roc_auc", "ece", "logloss"]].mean().loc[list(POLS)]
    m[["acc", "macro_f1", "roc_auc", "ece"]] *= 100
    print(f"== {per} ({r.stream.nunique()} streams)"); print(m.round(2).to_string())
acc = r.pivot_table(index=["stream", "period"], columns="policy", values="acc")
e, l = acc.xs("early", level=1), acc.xs("late", level=1)
gap_e = 100 * (e.settled - e[list(FEAS)].max(1)); gap_l = 100 * (l.settled - l[list(FEAS)].max(1))
print(f"F1: early gap settled - best feasible {gap_e.mean():+.2f} (need >= 3), >= 3 on {(gap_e >= 3).sum()}/{len(gap_e)} (need 2/3); late gap {gap_l.mean():+.2f}")
print("best feasible policy early:", e[list(FEAS)].idxmax(1).value_counts().to_dict(), " late:", l[list(FEAS)].idxmax(1).value_counts().to_dict())
print(f"F2: best feasible policy differs between early and late on {(e[list(FEAS)].idxmax(1) != l[list(FEAS)].idxmax(1)).sum()}/{len(e)} streams")
print("early gap by split:", gap_e.groupby(gap_e.index.str.split("__").str[1]).mean().round(2).to_dict())
print("early gap by source:", gap_e.groupby(gap_e.index.str.split("__").str[0]).mean().round(2).to_dict())
print(f"union - shared early {100 * (e.union - e.shared).mean():+.2f}, union - new early {100 * (e.union - e.new).mean():+.2f}; oracle - settled late {100 * (l.oracle - l.settled).mean():+.2f}")
