"""Checks the hypotheses of pre-registration A (grid test, seeds 10 and 11) exactly as written in the log."""
import numpy as np
import pandas as pd

D = "../results_grid_test"
PRED = {(5, 500): 0.0009, (5, 2000): 0.0003, (30, 500): 0.0191, (30, 2000): 0.0055, (100, 500): 0.1044,
        (100, 2000): 0.0303}  # written in the log before the test was run
rows = []
for nc in (5, 30, 100):
    for b in (500, 2000):
        for s in (10, 11):
            r = dict(nc=nc, block=b, seed=s)
            for m in ("mice", "ddm1000", "winens1000", "fifo1000", "oracle1000"):
                r[m] = np.nanmean(np.load(f"{D}/grid_c{nc}_b{b}_s{s}__{m}.npz")["acc"])
            rows.append(r)
d = pd.DataFrame(rows)
d["gain"] = d.mice - d.ddm1000
d["mice_minus_win"] = d.mice - d.winens1000
pd.set_option("display.width", 200)
print(d.round(4).to_string(index=False))
cell = d.groupby(["nc", "block"])[["gain", "mice_minus_win"]].mean()
cell["predicted"] = [PRED[k] for k in cell.index]
print(cell.round(4))
hard = d[d.nc >= 30]
print("H1a gain > 0 on all 8 c30/c100 streams:", bool((hard.gain > 0).all()), hard.gain.round(4).tolist())
print("H1b b500 > b2000 at c30 and c100:", bool(cell.loc[(30, 500), "gain"] > cell.loc[(30, 2000), "gain"]),
      bool(cell.loc[(100, 500), "gain"] > cell.loc[(100, 2000), "gain"]))
print("H1c c100 > c30 at b500 and b2000:", bool(cell.loc[(100, 500), "gain"] > cell.loc[(30, 500), "gain"]),
      bool(cell.loc[(100, 2000), "gain"] > cell.loc[(30, 2000), "gain"]))
sp = cell[["predicted", "gain"]].corr(method="spearman").iloc[0, 1]
print("H2 Spearman(predicted, observed) over 6 cells:", round(sp, 3), "(>= 0.8?)", sp >= 0.8)
print("H3 winens < mice on c30/c100 streams:", bool((hard.mice_minus_win > 0).all()), hard.mice_minus_win.round(4).tolist())
c5 = d[d.nc == 5]
print("c5 |gain| < 0.01:", bool((c5.gain.abs() < 0.01).all()), c5.gain.round(4).tolist())
