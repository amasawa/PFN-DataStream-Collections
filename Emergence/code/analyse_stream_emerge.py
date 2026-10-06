"""Metrics for ../results/stream_emerge/*.npz (design: logs/EXPERIMENT_LOG.md, 2026-10-06, "流上的 Observation").
Periods: window = the 10 batches after the first batch that contains the emerging class c; late = batches 31-60 after
it; all = the whole stream (batch 0 excluded). Metrics: accuracy, macro-F1, F1 and recall of c, accuracy on the old
classes, log-loss, ECE (15 equal-width bins on the max probability), Brier, mean predictive entropy on rows of c and
on old rows; ROC AUC (one-vs-rest, macro over the classes present). The four metrics of Drift-Resilient TabPFN
(Helli et al., NeurIPS 2024: accuracy, F1, ROC AUC, ECE) are a subset. Seeds: every ../results/stream_emerge*/ folder
is one TabPFN initialisation; 95% intervals over seeds are printed when there are several. Writes ../results/stream_emerge_metrics.csv and prints the summary and the checks E1-E3."""
import glob
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

TAG = sys.argv[1] if len(sys.argv) > 1 else ""      # e.g. _d1_thin0.02: analyse ../results/stream_emerge<TAG>/ instead
OUT = f"../results/stream_emerge{TAG}_metrics.csv"
POLS = ("fifo", "ltm", "em", "rp", "rp5", "oracle")   # ltm equals fifo in runs made with EMERGE_NOLTM=1


def metrics(P, y, c):
    P = P.astype(np.float64); P /= np.clip(P.sum(1, keepdims=True), 1e-12, None)
    pred, conf, new = P.argmax(1), P.max(1), y == c
    K = P.shape[1]
    ent = -(P * np.log(np.clip(P, 1e-12, 1))).sum(1)
    bins = np.minimum((conf * 15).astype(int), 14)
    ece = sum(abs((pred[bins == b] == y[bins == b]).mean() - conf[bins == b].mean()) * (bins == b).mean() for b in range(15) if (bins == b).any())
    pres = np.unique(y)
    try:
        auc = roc_auc_score(y, P[:, pres] / np.clip(P[:, pres].sum(1, keepdims=True), 1e-12, None), labels=pres, multi_class="ovr",
                            average="macro") if len(pres) > 2 else roc_auc_score(y == pres[1], P[:, pres[1]]) if len(pres) == 2 else np.nan
    except ValueError:
        auc = np.nan
    return dict(acc=(pred == y).mean(), roc_auc=auc, weighted_f1=f1_score(y, pred, labels=pres, average="weighted", zero_division=0),
                macro_f1=f1_score(y, pred, labels=np.unique(y), average="macro", zero_division=0),
                f1_c=f1_score(new, pred == c, zero_division=0), recall_c=(pred[new] == c).mean() if new.any() else np.nan,
                acc_old=(pred[~new] == y[~new]).mean(), logloss=-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean(),
                ece=ece, brier=((P - np.eye(K)[y]) ** 2).sum(1).mean(),
                ent_c=ent[new].mean() if new.any() else np.nan, ent_old=ent[~new].mean())


rows = []
for f in sorted(glob.glob(f"../results/stream_emerge{TAG}/*.npz") + ([] if TAG else glob.glob("../results/stream_emerge_s*/*.npz"))):
    seed = int(os.path.basename(os.path.dirname(f)).rpartition("_s")[2]) if "_s" in os.path.basename(os.path.dirname(f)) else 0
    z = np.load(f); y, c, B = z["y"], int(z["c"]), int(z["B"]); te = int(z["first"]) // B; T = len(y)
    D = int(z["delay"]) if "delay" in z else 1      # window = the 10 batches after the first labels of c arrive
    periods = {"window": range(te + D, min(te + D + 10, T)), "late": range(te + D + 30, min(te + D + 60, T)), "all": range(D, T)}
    for p in POLS:
        for per, ts in periods.items():
            ts = list(ts)
            if not ts:
                continue
            r = metrics(z[f"P_{p}"][ts].reshape(-1, z[f"P_{p}"].shape[2]), y[ts].reshape(-1), c)
            rows.append(dict(seed=seed, stream=os.path.basename(f)[:-4], source=os.path.basename(f).split("__")[0], c=c, policy=p, period=per,
                             n_c_mean=float(z["n_c"][ts].mean()), **r))
r = pd.DataFrame(rows); r.to_csv(OUT, index=False); pd.set_option("display.width", 250)
if r.seed.nunique() > 1:
    print(f"seeds {sorted(r.seed.unique())}: 95% interval (t, over seeds) of the mean over streams")
    for per in ("window", "all"):
        g = r[r.period == per].groupby(["policy", "seed"])[["acc", "macro_f1", "roc_auc", "ece"]].mean().groupby("policy")
        n = r.seed.nunique(); from scipy.stats import t as tdist
        ci = g.std() * tdist.ppf(0.975, n - 1) / np.sqrt(n)
        print(per); print((100 * g.mean()).round(2).astype(str).add(" ± ").add((100 * ci).round(2).astype(str)).to_string())
r = r[r.seed == 0]
cols = ["acc", "roc_auc", "weighted_f1", "macro_f1", "f1_c", "recall_c", "acc_old", "logloss", "ece", "brier", "ent_c", "ent_old"]
for per in ("window", "late", "all"):
    print(f"== {per}: mean over {r.stream.nunique()} streams (x100 except logloss, entropy)")
    m = r[r.period == per].groupby("policy")[cols].mean().loc[list(POLS)]
    m[["acc", "roc_auc", "weighted_f1", "macro_f1", "f1_c", "recall_c", "acc_old", "ece", "brier"]] *= 100
    print(m.round(2).to_string())
w = r[(r.policy == "fifo") & (r.period == "window")].set_index("stream").recall_c
l = r[(r.policy == "fifo") & (r.period == "late")].set_index("stream").recall_c
ok = (w < 0.5 * l).dropna()
print(f"E1: fifo recall of c in the window < half of late on {ok.sum()}/{len(ok)} streams (need 2/3); means {100 * w.mean():.1f} vs {100 * l.mean():.1f}")
acc = r.pivot_table(index=["stream", "period"], columns="policy", values="acc")
for p in ("rp", "rp5", "em", "ltm", "oracle"):
    dw = 100 * (acc.xs("window", level=1)[p] - acc.xs("window", level=1).fifo)
    da = 100 * (acc.xs("all", level=1)[p] - acc.xs("all", level=1).fifo)
    print(f"{p:6s} vs fifo: window {dw.mean():+.2f} (better on {(dw > 0).sum()}/{len(dw)}), whole stream {da.mean():+.2f} (worst {da.min():+.2f})")
print("E2 needs rp or rp5: window >= +3.00 and whole stream >= -0.30; E3: em window gain below rp/rp5, or whole stream <= -0.50")
