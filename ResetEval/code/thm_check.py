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
        with np.load(f"{d}/{s}__none.npz") as fifo:
            fifo_ll = fifo['ll'][1:]
        assert len(fifo_ll) and np.isfinite(fifo_ll).all(), (s, 'invalid FIFO loss')
        lf = fifo_ll.sum()
        for k in DETS:
            p = f"{d}/{s}__{k}+hedge@e1g1.npz"
            z = np.load(p)
            assert z['ll'][1:].shape == fifo_ll.shape and np.isfinite(z['ll'][1:]).all(), (s, k)
            lm = z['ll'][1:].sum(); R = len(z["resets"])
            rows.append(dict(stream=s, det=k, R=R, excess=lm - lf, bound=R * np.log(2), ok=lm - lf <= R * np.log(2) + 1e-9))
    D = pd.DataFrame(rows)
    assert len(D) == len(REAL + NEW + SYN)*len(DETS) == 648
    D.to_csv(f"{RES}/thm_check.csv", index=False)
    used = (D.excess / D.bound.where(D.bound > 0)).dropna()
    print(f"{len(D)} cases ({D.stream.nunique()} streams): bound holds in {D.ok.sum()} ({100 * D.ok.mean():.1f}%); "
          f"excess over FIFO: median {D.excess.median():.3f}, max {D.excess.max():.3f}; "
          f"largest share of the bound used {used.max():.3f}; cases with excess < 0 (better than FIFO): {(D.excess < 0).sum()}")
    if (~D.ok).any():
        print("VIOLATIONS:\n", D[~D.ok].to_string())
        raise SystemExit('Numerical bound check failed')
