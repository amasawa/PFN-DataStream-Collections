"""TKDE round 12, direction B: contrasts of the segment-phase diagnostic (registered in
experiments/mice_tkde_control/PLAN.md, "Round 12"). A = aligned streams, O = offset streams with segment origin 0 (4.b),
P = offset streams with segment origin 200 (seg_origin_run.py). MICE - DDM on matched batches, points.
C_imp = P - O is the phase-restoration effect at fixed observed history (segment contents, closure times and expert
availability change together); C_hist = P - A is the prefix effect on the relative advantage under restored phase.
Writes ../results_paper/seg_origin.csv."""
import os

import numpy as np
import pandas as pd

from check_offset import ALIGNED, SHIFT, policies, recurring, replay

CTRL = os.path.expanduser("~/pfn-runs/mice-tkde-control-20261009")
RUN = os.path.expanduser("~/pfn-runs/mice_seg_origin_r12")

if __name__ == "__main__":
    rows = []
    for blk in (500, 2000):
        for nc in (30, 100):
            for s in (20, 21):
                al, of = f"grid_c{nc}_b{blk}_s{s}", f"off_c{nc}_b{blk}_s{s}"
                a0, c0 = replay(f"{ALIGNED}/{al}__micev1000_500.pkl")
                t = np.array(sorted(a0))
                assert t[0] == 1 and t[-1] == len(c0["y"]) // c0["B"] - 1 and (np.diff(t) == 1).all(), al
                rec = np.isin(t, recurring(c0["concept"], c0["B"]))
                pol = dict(A=policies(ALIGNED, f"{CTRL}/arch", ALIGNED, al, t)[0],
                           O=policies(f"{CTRL}/off", f"{CTRL}/off", f"{CTRL}/off", of, t + SHIFT)[0],
                           P=policies(f"{RUN}/P", f"{RUN}/P", f"{CTRL}/off", of, t + SHIFT)[0])
                assert np.array_equal(pol["O"]["ddm"], pol["P"]["ddm"])
                r = dict(block=blk, nc=nc, seed=s)
                for k, P in pol.items():
                    r[f"{k}_d_ddm"], r[f"{k}_d_ddm_rec5"] = (P["mice"] - P["ddm"]).mean(), (P["mice"] - P["ddm"])[rec].mean()
                    r[f"{k}_d_arch"], r[f"{k}_d_arch_rec5"] = (P["mice"] - P["arch"]).mean(), (P["mice"] - P["arch"])[rec].mean()
                    for b in ("mice", "ddm", "arch"):
                        r[f"{k}_{b}"] = P[b].mean()              # raw accuracies, for the per-method differences
                for k in ("", "_rec5"):
                    r[f"C_imp{k}"] = r[f"P_d_ddm{k}"] - r[f"O_d_ddm{k}"]
                    r[f"C_hist{k}"] = r[f"P_d_ddm{k}"] - r[f"A_d_ddm{k}"]
                r["mice_P_minus_A"], r["ddm_O_minus_A"] = r["P_mice"] - r["A_mice"], r["O_ddm"] - r["A_ddm"]
                r["mice_P_minus_O"] = r["P_mice"] - r["O_mice"]
                rows.append(r)
    m = pd.DataFrame(rows)
    m.to_csv("../results_paper/seg_origin.csv", index=False)
    pd.set_option("display.width", 250)
    print(m.round(2).to_string(index=False))
    print(m.groupby("block")[["A_d_ddm", "O_d_ddm", "P_d_ddm", "C_imp", "C_hist", "P_d_arch"]].mean().round(2))
    pos, mean = int((m.P_d_ddm > 0).sum()), m.P_d_ddm.mean()
    print(f"H1: P MICE - DDM positive {pos}/8 (>= 7), mean {mean:+.3f} (>= +1.0) -> "
          f"{'HOLDS' if pos >= 7 and mean >= 1.0 else 'FAILS'}")
    print(f"H2: mean C_imp {m.C_imp.mean():+.3f} (>= +5.0) -> {'HOLDS' if m.C_imp.mean() >= 5.0 else 'FAILS'}")
    print(f"H3: mean C_hist {m.C_hist.mean():+.3f} (|.| <= 1.0) -> {'HOLDS' if abs(m.C_hist.mean()) <= 1.0 else 'FAILS'}")
    print(f"descriptive: MICE - archive A {m.A_d_arch.mean():+.3f}, O {m.O_d_arch.mean():+.3f}, P {m.P_d_arch.mean():+.3f} "
          f"(P positive {int((m.P_d_arch > 0).sum())}/8); recurrence windows C_imp {m.C_imp_rec5.mean():+.3f}, "
          f"C_hist {m.C_hist_rec5.mean():+.3f}; MICE - archive in recurrence windows A {m.A_d_arch_rec5.mean():+.3f}, "
          f"O {m.O_d_arch_rec5.mean():+.3f}, P {m.P_d_arch_rec5.mean():+.3f}")
    print(f"raw differences (mean): MICE P - A {m.mice_P_minus_A.mean():+.3f}, DDM O - A {m.ddm_O_minus_A.mean():+.3f}, "
          f"MICE P - O {m.mice_P_minus_O.mean():+.3f}")
