"""Cost of emergence (design: logs/EXPERIMENT_LOG.md, 2026-10-06, "抢救"): FIFO on the emergence stream versus FIFO on
the original stream (../results/stream_control/), on the same rows. Row j of an emergence stream is row j + r of the
original stream, r = number of rows of c removed before T0 (identical for every row at or after T0). Periods as in
analyse_stream_emerge.py (window = 10 batches after the first labels of c, late = batches 31-60 after them)."""
import glob
import os

import numpy as np
import pandas as pd

rows = []
for f in sorted(glob.glob("../results/stream_emerge/*.npz")):
    src = os.path.basename(f).split("__")[0]
    z, ctl = np.load(f), np.load(f"../results/stream_control/{src}.npz")
    y, c, B = z["y"].reshape(-1), int(z["c"]), int(z["B"]); te = int(z["first"]) // B
    yo, Pc = ctl["y"].reshape(-1), ctl["P_fifo"].reshape(-1, ctl["P_fifo"].shape[2])
    pe = z["P_fifo"].reshape(-1, z["P_fifo"].shape[2]).argmax(1)
    y0 = np.load(f"../../MICE/data/{src}.npz")["y"][:len(yo)].astype(int)
    removed = int(((np.arange(len(y0)) < 8000) & (y0 == c)).sum())
    for per, (a, b) in {"window": (te + 1, te + 11), "late": (te + 31, te + 61)}.items():
        j = np.arange(a * B, min(b * B, len(y)))
        o = j + removed
        ok = o < len(yo)
        j, o = j[ok], o[ok]
        assert (yo[o] == y[j]).all(), (f, per)
        pc = Pc[o].astype(np.float64).argmax(1)
        new = y[j] == c
        rows.append(dict(stream=os.path.basename(f)[:-4], period=per, acc_em=(pe[j] == y[j]).mean(), acc_ctl=(pc == y[j]).mean(),
                         old_em=(pe[j][~new] == y[j][~new]).mean(), old_ctl=(pc[~new] == y[j][~new]).mean(),
                         new_em=(pe[j][new] == c).mean(), new_ctl=(pc[new] == c).mean()))
d = pd.DataFrame(rows); pd.set_option("display.width", 200)
d.to_csv("../results/control_cost.csv", index=False)
m = (100 * d.groupby("period")[["acc_em", "acc_ctl", "old_em", "old_ctl", "new_em", "new_ctl"]].mean()).round(2)
print(m.to_string())
w = d[d.period == "window"]
print(f"C1: window cost (control - emergence) {100 * (w.acc_ctl - w.acc_em).mean():+.2f} points (need >= 3); "
      f"on old rows {100 * (w.old_ctl - w.old_em).mean():+.2f} (C2 needs >= 1.5), on new rows {100 * (w.new_ctl - w.new_em).mean():+.2f}; "
      f"cost >= 3 on {((w.acc_ctl - w.acc_em) >= 0.03).sum()}/{len(w)} streams")
