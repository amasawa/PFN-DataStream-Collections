"""Observation 1b: virtual drift inside versus outside the support of the context (main venv).
Family 'sine2d': x ~ U([a, a+L] x [-1, 1]), y = 1[x2 < sin(3 x1)] (a periodic boundary, as in the Sine generator of
Gama et al. 2004). Context: a = 0, L = 4. Post windows: the same labelling function with the x1-range translated by
s in {0, 1, 2, 4, 8} (s >= 4: disjoint support) and, as control, tilted inside the support (importance resampling).
Same TFM and outputs as obs.py. Seeds 0-4 = dev. Output: ../results/obs_out_dev.csv"""
import os, sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
sys.path.insert(0, os.path.dirname(__file__))
from obs import TFM, OUT

def lab(X): return (X[:, 1] < np.sin(3 * X[:, 0])).astype(int)
def sample(r, n, a, L=4.0): return np.c_[r.uniform(a, a + L, n), r.uniform(-1, 1, n)]

if __name__ == "__main__":
  rows = []
  SEEDS = [int(v) for v in sys.argv[1:]] or list(range(5))
  for seed in SEEDS:
      rng = np.random.default_rng(100 + seed); f = TFM(seed)
      Xc = sample(rng, 1000, 0.0); yc = lab(Xc)
      for s in (0, 1, 2, 4, 8):
          Xp = sample(rng, 1000, s); yp = lab(Xp); Xf = sample(rng, 1000, s); yf = lab(Xf)
          Ps, Pf = f.proba(Xc, yc, Xp, 2), f.proba(Xf, yf, Xp, 2)
          dom = f.proba(np.r_[Xc[:500], Xp[:500]], np.r_[np.zeros(500), np.ones(500)].astype(int), np.r_[Xc[500:], Xp[500:]], 2)[:, 1]
          dist = np.sqrt(((Xp[:, None, :] - Xc[None, :, :]) ** 2).sum(-1)).min(1).mean()
          rows.append(dict(seed=seed, family="sine2d", type="virtual_translate", magnitude=s,
                           acc_stale=(Ps.argmax(1) == yp).mean(), acc_fresh=(Pf.argmax(1) == yp).mean(),
                           conf_known=Ps.max(1).mean(), shift=roc_auc_score(np.r_[np.zeros(500), np.ones(500)], dom),
                           nn_dist=dist))
      pd.DataFrame(rows).to_csv(f"{OUT}/obs_out_{'dev' if SEEDS == list(range(5)) else 'test'}.csv", index=False); print("seed", seed, flush=True)
