"""Check Theorem 1(ii) of the TMLR draft on every (stream, detector) of the variant <det>+hedge@e1g1 (eta 1, gamma 1):
  sum_t ll_mix,t <= sum_t ll_FIFO,t + R ln 2 / eta,
with ll the stored per-batch mean log-loss (probabilities clipped at 1e-6, as in the implementation) and R the number
of detections. Prints the share of cases that satisfy it, the largest slack used and any violation.
Usage: python thm_check.py -> ../results/thm_check.csv"""
import os

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, REAL, RES, SYN

NEW = ["gas", "occupancy", "room", "bank", "kdd", "eeg", "news", "home", "wall", "chest"]

if __name__ == "__main__":
    d = f"{RES}/tabpfn_M1000"; rows = []
    for s in REAL + NEW + SYN:
        if not os.path.exists(f"{d}/{s}__none.npz"):
            continue
        lf = np.nansum(np.load(f"{d}/{s}__none.npz")["ll"][1:])
        for k in DETS:
            p = f"{d}/{s}__{k}+hedge@e1g1.npz"
            if not os.path.exists(p):
                continue
            z = np.load(p); lm = np.nansum(z["ll"][1:]); R = len(z["resets"])
            rows.append(dict(stream=s, det=k, R=R, excess=lm - lf, bound=R * np.log(2), ok=lm - lf <= R * np.log(2) + 1e-9))
    D = pd.DataFrame(rows); D.to_csv(f"{RES}/thm_check.csv", index=False)
    used = (D.excess / D.bound.where(D.bound > 0)).dropna()
    print(f"{len(D)} cases ({D.stream.nunique()} streams): bound holds in {D.ok.sum()} ({100 * D.ok.mean():.1f}%); "
          f"excess over FIFO: median {D.excess.median():.3f}, max {D.excess.max():.3f}; "
          f"largest share of the bound used {used.max():.3f}; cases with excess < 0 (better than FIFO): {(D.excess < 0).sum()}")
    if (~D.ok).any():
        print("VIOLATIONS:\n", D[~D.ok].to_string())
