"""Label-free coverage statistic: mean NN distance from window rows to the context, divided by the mean leave-one-out NN
distance within the context (1 = the window is as covered as the context itself). Checks whether it separates the
in-support tilt of obs.py from the out-of-support translation of obs_out.py. No TFM. Seeds 0-4 = dev."""
import os, sys
import numpy as np, pandas as pd
from sklearn.neighbors import NearestNeighbors
sys.path.insert(0, os.path.dirname(__file__))
from obs import hyperplane, sea, tilt, OUT
from obs_out import sample

def cov(Xc, Xp):
    nn = NearestNeighbors(n_neighbors=2).fit(Xc)
    own = nn.kneighbors(Xc)[0][:, 1].mean()
    return nn.kneighbors(Xp, n_neighbors=1)[0].mean() / own

SEEDS = [int(v) for v in sys.argv[1:]] or list(range(5))
rows = []
for seed in SEEDS:
    rng = np.random.default_rng(seed)
    for fam, mk in (("hyperplane", hyperplane), ("sea", sea)):
        sampler, lab0, _, d = mk(rng); u = rng.normal(size=d); u /= np.linalg.norm(u)
        Xc = sampler(rng, 1000)
        for b in (0, 1, 2, 4, 8):
            Xp = tilt(rng, sampler, 1000, u, b if fam == "hyperplane" else b / 3)
            rows.append(dict(seed=seed, family=fam, type="virtual_tilt", magnitude=b, coverage=cov(Xc, Xp)))
    rng = np.random.default_rng(100 + seed); Xc = sample(rng, 1000, 0.0)
    for s in (0, 1, 2, 4, 8):
        rows.append(dict(seed=seed, family="sine2d", type="virtual_translate", magnitude=s, coverage=cov(Xc, sample(rng, 1000, s))))
d = pd.DataFrame(rows); d.to_csv(f"{OUT}/coverage_{'dev' if SEEDS == list(range(5)) else 'test'}.csv", index=False)
print(d.groupby(["family", "type", "magnitude"]).coverage.mean().round(2).to_string())
