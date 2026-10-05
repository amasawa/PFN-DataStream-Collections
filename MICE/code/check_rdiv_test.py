"""Pre-registration D (see logs/EXPERIMENT_LOG.md, 2026-10-04 17:11): the model-oriented discrepancies of
overleaf/icml/theory_v2.tex on the TEST grid (seeds 10, 11). Same pairs and estimators as check_rdiv.py (500-row
segments, 2-fold cross-fitting), plus the log-loss versions and the disagreement mass rho of each concept pair, which
is computed from the generator (grid_streams.stream draws centroids, weights, then the labellings, in this order).
Usage: python check_rdiv_test.py   -> ../results_grid_test/rdiv_test.csv and the checks D1-D4."""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from run import TFM, DATA

OUT = "../results_grid_test/rdiv_test.csv"


def rho_matrix(nc, seed, d=10, n_classes=4, K=3):
    rng = np.random.default_rng(seed)
    rng.uniform(0, 1, size=(nc, d)); w = rng.uniform(size=nc); w /= w.sum()
    lab = [rng.integers(n_classes, size=nc) for _ in range(K)]
    return np.array([[w[lab[a] != lab[b]].sum() for b in range(K)] for a in range(K)])


def risks(f, Xc, yc, Xq, yq):
    P = f.predict(Xc, yc, Xq)
    return np.array([(P.argmax(1) != yq).mean(), -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)).mean()])


import os
if not os.path.exists(OUT):  # the TFM part runs once; the checks below can be recomputed from the csv
    rng = np.random.default_rng(0)
    rows = []
    for nc in (5, 30, 100):
        for b in (500, 2000):
            for seed in (10, 11):
                stream = f"grid_c{nc}_b{b}_s{seed}"
                z = np.load(f"{DATA}/{stream}.npz"); X, y, c = z["X"], z["y"].astype(int), z["concept"]
                f, R = TFM(int(y.max()) + 1), rho_matrix(nc, seed)
                starts = [0] + [i for i in range(1, len(c)) if c[i] != c[i - 1]]
                segs = [(s, c[s]) for s in starts]
                pairs = [(i, j) for i in range(len(segs)) for j in range(i + 1, len(segs))]
                same = [p for p in pairs if segs[p[0]][1] == segs[p[1]][1]]
                diff = [p for p in pairs if segs[p[0]][1] != segs[p[1]][1]]
                pick = [same[k] for k in rng.permutation(len(same))[:6]] + [diff[k] for k in rng.permutation(len(diff))[:6]]
                for i, j in pick:
                    (sp, cp), (sq, cq) = segs[i], segs[j]
                    Xp, yp, Xq, yq = X[sp:sp + 500], y[sp:sp + 500], X[sq:sq + 500], y[sq:sq + 500]
                    h = 250; A, Bh = slice(0, h), slice(h, 500)
                    own_p = 0.5 * (risks(f, Xp[A], yp[A], Xp[Bh], yp[Bh]) + risks(f, Xp[Bh], yp[Bh], Xp[A], yp[A]))
                    own_q = 0.5 * (risks(f, Xq[A], yq[A], Xq[Bh], yq[Bh]) + risks(f, Xq[Bh], yq[Bh], Xq[A], yq[A]))
                    up, uq = np.zeros(2), np.zeros(2)
                    for tr, te in ((A, Bh), (Bh, A)):
                        Xc, yc = np.r_[Xp[tr], Xq[tr]], np.r_[yp[tr], yq[tr]]
                        up += 0.5 * risks(f, Xc, yc, Xp[te], yp[te]); uq += 0.5 * risks(f, Xc, yc, Xq[te], yq[te])
                    tr_ = risks(f, Xp, yp, Xq, yq) - own_q
                    for li, loss in enumerate(("01", "log")):
                        rows.append(dict(stream=stream, nc=nc, block=b, seed=seed, loss=loss, different=int(cp != cq),
                                         rho=R[cp, cq], rdiv=abs(up[li] - uq[li]), transfer=tr_[li],
                                         excess2=up[li] - own_p[li] + uq[li] - own_q[li],
                                         excess_max=max(up[li] - own_p[li], uq[li] - own_q[li]), own=0.5 * (own_p[li] + own_q[li])))
                print(stream, "done", flush=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
d = pd.read_csv(OUT)
pd.set_option("display.width", 220)
z, l = d[d.loss == "01"], d[d.loss == "log"]
print("D1 AUROC (0-1 loss, 144 pairs):", {k: round(roc_auc_score(z.different, z[k]), 3) for k in ("rdiv", "transfer", "excess_max")})
print("   per cell:\n", z.groupby(["nc", "block"]).apply(lambda g: pd.Series({k: roc_auc_score(g.different, g[k]) for k in ("rdiv", "transfer", "excess_max")})).round(3).to_string())
zd = z[z.different == 1]
print("D2 different pairs (0-1): Spearman(rho, transfer) %.3f, Spearman(rho, excess2) %.3f, Spearman(rho, rdiv) %.3f; mean rho %.3f transfer %.3f excess2 %.3f rdiv %.3f"
      % (spearmanr(zd.rho, zd.transfer)[0], spearmanr(zd.rho, zd.excess2)[0], spearmanr(zd.rho, zd["rdiv"])[0], zd.rho.mean(), zd.transfer.mean(), zd.excess2.mean(), zd["rdiv"].mean()))
print("   per cell:\n", zd.groupby(["nc", "block"])[["rho", "transfer", "excess2", "rdiv", "own"]].mean().round(3).to_string())
ld = l[(l.different == 1) & (l.nc < 100)]
print("D3 (exploratory, log-loss, c5 and c30): slope of excess2 on rho through the origin %.3f (theory 2 ln 2 = 1.386); mean rdiv %.3f; Spearman(rho, excess2) %.3f"
      % ((ld.rho * ld.excess2).sum() / (ld.rho ** 2).sum(), ld["rdiv"].mean(), spearmanr(ld.rho, ld.excess2)[0]))
print("D4 same pairs, mean excess2 per cell (0-1; pooling gain, expected <= 0.005):\n", z[z.different == 0].groupby(["nc", "block"]).excess2.mean().round(4).to_string())
