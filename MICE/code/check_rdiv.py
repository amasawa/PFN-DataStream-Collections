"""Dev streams only. Which model-oriented discrepancy tells a recurring concept from a new one for a frozen TFM?
For pairs of 500-row segments p, q from different blocks of a dev stream (same concept or not) compare
  rdiv      R-divergence (Zhao & Cao, 2023): |risk_p(h_u) - risk_q(h_u)|, h_u = TFM conditioned on the mixed data,
            cross-fitted (context = one half of p and of q, risks on the other halves)
  transfer  risk_q(h_p) - risk_q(h_q): the rule used by MICE so far (h_q cross-fitted)
  excess    max over the two sets of risk(h_u) - risk(h_own): what mixing the two sets costs each of them
Reports the AUROC of each score for "different concept". Usage: python check_rdiv.py <out.csv> stream [stream ...]"""
import sys
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from run import TFM, DATA

rng = np.random.default_rng(0)
rows = []
for stream in sys.argv[2:]:
    z = np.load(f"{DATA}/{stream}.npz"); X, y, c = z["X"], z["y"].astype(int), z["concept"]
    f = TFM(int(y.max()) + 1)
    starts = [0] + [i for i in range(1, len(c)) if c[i] != c[i - 1]]
    segs = [(s, c[s]) for s in starts]
    pairs = [(i, j) for i in range(len(segs)) for j in range(i + 1, len(segs))]
    same = [p for p in pairs if segs[p[0]][1] == segs[p[1]][1]]; diff = [p for p in pairs if segs[p[0]][1] != segs[p[1]][1]]
    pick = [same[k] for k in rng.permutation(len(same))[:6]] + [diff[k] for k in rng.permutation(len(diff))[:6]]
    err = lambda Xc, yc, Xq, yq: float((f.predict(Xc, yc, Xq).argmax(1) != yq).mean())
    for i, j in pick:
        (sp, cp), (sq, cq) = segs[i], segs[j]
        Xp, yp, Xq, yq = X[sp:sp + 500], y[sp:sp + 500], X[sq:sq + 500], y[sq:sq + 500]
        h = 250; A, Bh = slice(0, h), slice(h, 500)
        own_p = 0.5 * (err(Xp[A], yp[A], Xp[Bh], yp[Bh]) + err(Xp[Bh], yp[Bh], Xp[A], yp[A]))
        own_q = 0.5 * (err(Xq[A], yq[A], Xq[Bh], yq[Bh]) + err(Xq[Bh], yq[Bh], Xq[A], yq[A]))
        up, uq = [], []
        for tr, te in ((A, Bh), (Bh, A)):
            P = f.predict(np.r_[Xp[tr], Xq[tr]], np.r_[yp[tr], yq[tr]], np.r_[Xp[te], Xq[te]]).argmax(1)
            up.append((P[:h] != yp[te]).mean()); uq.append((P[h:] != yq[te]).mean())
        up, uq = float(np.mean(up)), float(np.mean(uq))
        rows.append(dict(stream=stream, different=int(cp != cq), rdiv=abs(up - uq), transfer=err(Xp, yp, Xq, yq) - own_q,
                         excess=max(up - own_p, uq - own_q), own_p=own_p, own_q=own_q, u_p=up, u_q=uq))
    print(stream, "done", flush=True)
d = pd.DataFrame(rows); d.to_csv(sys.argv[1], index=False)
d["family"] = d.stream.str.replace(r"_s\d+$", "", regex=True)
pd.set_option("display.width", 200)
print(d.groupby(["family", "different"])[["rdiv", "transfer", "excess"]].mean().round(3).to_string())
for name, g in list(d.groupby("family")) + [("ALL", d)]:
    print(name, {k: round(roc_auc_score(g.different, g[k]), 3) for k in ("rdiv", "transfer", "excess")})
