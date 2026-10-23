import glob, os, sys
import numpy as np
from sklearn.metrics import f1_score, roc_auc_score
ROOT = "/ssdfs/datahome/u2105445/mice_rerun"
DATA = f"{ROOT}/repo/MICE/data"; NB = f"{ROOT}/home/pfn-runs/mice-table1-newbase"

def metrics(P, y, nb=15):      # = MICE/code/compute_metrics.py metrics()
    P = np.clip(P, 0, 1); P = P / P.sum(1, keepdims=True)
    pred, conf = P.argmax(1), P.max(1); labs = np.unique(y)
    aucs = [roc_auc_score(y == k, P[:, k]) for k in labs if 0 < (y == k).sum() < len(y)]
    b = np.minimum((conf * nb).astype(int), nb - 1); ece = 0.0
    for i in range(nb):
        m = b == i
        if m.any(): ece += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    E = np.zeros_like(P); E[np.arange(len(y)), y] = 1
    return dict(f1=f1_score(y, pred, average="macro", labels=labs), auc=float(np.mean(aucs)), ece=ece,
                brier=0.5 * ((P - E) ** 2).sum(1).mean())

files = glob.glob(f"{NB}/test_cluster/P/*.npz") + glob.glob(f"{NB}/drtabpfn/*.npz")
print("stream,method,acc,f1,auc,ece,brier,n")
for f in sorted(files):
    s, m = os.path.basename(f)[:-4].split("__"); m = m.split("_")[0]
    z = np.load(f); P = z["P"].astype(float); B = int(z["B"])
    y = np.load(f"{DATA}/{s}.npz")["y"].astype(int)[B:B + len(P)]
    r = metrics(P, y); acc = float(np.nanmean(z["acc"]))
    print(f"{s},{m},{acc},{r['f1']},{r['auc']},{r['ece']},{r['brier']},{len(P)}", flush=True)
