"""Acceptance test of run_cached.py (criterion written in the log on 2026-10-05 before any run): on development
streams, the expert predictions of the cached and the original call path must agree to 1e-4 in every batch and the
per-batch accuracies must be identical. Compares two output folders produced by run.py and run_cached.py.
Usage: python check_cache_equiv.py <dir_original> <dir_cached>"""
import glob, os, pickle, sys
import numpy as np

a, b = sys.argv[1:3]; ok = True
for f in sorted(glob.glob(f"{a}/*__micev1000_500.pkl")):
    g = f"{b}/{os.path.basename(f)}"
    ca, cb = pickle.load(open(f, "rb")), pickle.load(open(g, "rb"))
    assert len(ca["cache"]) == len(cb["cache"])
    dmax, nexp, flips = 0.0, 0, 0
    for sa, sb in zip(ca["cache"], cb["cache"]):
        assert sa["t"] == sb["t"] and set(sa["P"]) == set(sb["P"]), "different expert sets"
        for u in sa["P"]:
            dmax = max(dmax, float(np.abs(sa["P"][u] - sb["P"][u]).max())); nexp += 1
            flips += int((sa["P"][u].argmax(1) != sb["P"][u].argmax(1)).sum())
    za, zb = np.load(f[:-4] + ".npz"), np.load(g[:-4] + ".npz")
    same_acc = bool(np.array_equal(np.nan_to_num(za["acc"], nan=-1), np.nan_to_num(zb["acc"], nan=-1)))
    t = lambda z: float(z["wt"].sum())
    print(os.path.basename(f), f"max |dP| = {dmax:.2e} over {nexp} expert-batches, argmax flips {flips}, per-batch accuracy identical: {same_acc},",
          f"time {t(za):.0f}s -> {t(zb):.0f}s")
    ok &= dmax <= 1e-4 and same_acc
print("ACCEPT" if ok else "REJECT")
