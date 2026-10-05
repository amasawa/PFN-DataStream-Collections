"""Check of the reruns of ddm and ltm with stored probabilities (run_probs.py): the per-batch accuracy of the rerun, and
the accuracy recomputed from the stored probabilities, must both equal the per-batch accuracy of the original run.
Usage: python check_probs.py"""
import glob, os
import numpy as np
from make_paper_tables import DIRS

bad = 0; n = 0
for f in sorted(glob.glob("../results_probs/*__probs.npz")):
    s, meth = os.path.basename(f).split("__")[:2]
    orig = next((f"{d}/{s}__{meth}.npz" for g, d in DIRS.items() if g != "tabicl" and os.path.exists(f"{d}/{s}__{meth}.npz")), None)
    new = np.load(f"../results_probs/{s}__{meth}.npz")["acc"]; P = np.load(f)["P"].astype(np.float32)
    y = np.load(f"../data/{s}.npz")["y"].astype(int); B = 100
    T = len(new); accP = np.array([(P[(t - 1) * B:t * B].argmax(1) == y[t * B:(t + 1) * B]).mean() for t in range(1, T)])
    a = np.load(orig)["acc"] if orig else None
    same_rerun = a is not None and np.allclose(a[1:], new[1:], equal_nan=True)
    dP = np.abs(accP - new[1:]).max()
    n += 1; ok = same_rerun and dP <= 0.02 + 1e-9
    bad += not ok
    print(s, meth, "rerun equals original per batch:", same_rerun, "| mean acc orig %.4f rerun %.4f from stored P %.4f" % (
        np.nanmean(a) if a is not None else np.nan, np.nanmean(new), accP.mean()), "| max per-batch diff from float16 P %.3f" % dP, "" if ok else "<-- CHECK")
print(n, "files,", bad, "to check")
