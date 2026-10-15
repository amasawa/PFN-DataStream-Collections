"""Table rows for the round-14 test of detected segmentation (experiments/mice_r14/PLAN.md), from the CSVs written by
experiments/mice_r14/analyse_test.py. Writes ../results_paper/r14_regimes.csv (per-regime hierarchical intervals, the
same function and seed as the registered evaluator), ../overleaf/tkde/tab_fresh_rows.tex and tab_segsum_rows.tex.
Names in the CSVs: cp = MICE with detected segments, mice = MICE with fixed 500-row segments, archcp = archive with
detected segments, arch = archive with fixed segments. No number is typed by hand."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "experiments", "mice_r14"))
from analyse_test import hier_lb  # noqa: E402

RES, TEX = "../results_paper", "../overleaf/tkde"
REG = {"b500": "500", "b2000": "2\\,000", "bvar": "500--2\\,500"}


def wshare(d, col):
    """Share over all (context, close) evaluations: per-stream shares weighted by the number of closes."""
    return float((d[col] * d.cp_closes).sum() / d.cp_closes.sum())


def fresh():
    d = pd.read_csv(f"{RES}/r14_t1_streams.csv", index_col="stream")
    assert len(d) == 72
    d["reg"] = [s.split("_")[1] for s in d.index]
    d["nc"] = [int(s.split("_")[2][1:]) for s in d.index]
    rows, regs = [], []
    for reg in ("b500", "b2000", "bvar"):
        for nc in (30, 100):
            x = d[(d.reg == reg) & (d.nc == nc)]
            assert len(x) == 12
            rows.append(f"{REG[reg]} & {nc} & {(x.cp - x.reset).mean():+.2f} & {(x.mice - x.reset).mean():+.2f} & "
                        f"{(x.cp - x.mice).mean():+.2f} & {(x.cp - x.archcp).mean():+.2f} & "
                        f"{(x.cp_rec - x.reset_rec).mean():+.1f} & {(x.mice_rec - x.reset_rec).mean():+.1f} & "
                        f"{100 * wshare(x, 'cp_pure95_share'):.0f} & {100 * x.cp_purity_mean.mean():.1f} & "
                        f"{x.found.sum()}/{x.changes.sum()} & {x.false.sum()} \\\\")
        x = d[d.reg == reg]
        lo, hi = hier_lb(x.cp - x.reset)
        lo2, hi2 = hier_lb(x.mice - x.reset)
        regs.append(dict(regime=reg, streams=len(x), cp_reset=(x.cp - x.reset).mean(), cp_reset_lo=lo, cp_reset_hi=hi,
                         cp_above=int((x.cp > x.reset).sum()), mice_reset=(x.mice - x.reset).mean(),
                         mice_reset_lo=lo2, mice_reset_hi=hi2, mice_above=int((x.mice > x.reset).sum())))
        rows.append(f"\\multicolumn{{2}}{{l}}{{all {REG[reg]}}} & {(x.cp - x.reset).mean():+.2f} & "
                    f"{(x.mice - x.reset).mean():+.2f} & {(x.cp - x.mice).mean():+.2f} & {(x.cp - x.archcp).mean():+.2f} & "
                    f"{(x.cp_rec - x.reset_rec).mean():+.1f} & {(x.mice_rec - x.reset_rec).mean():+.1f} & "
                    f"{100 * wshare(x, 'cp_pure95_share'):.0f} & {100 * x.cp_purity_mean.mean():.1f} & "
                    f"{x.found.sum()}/{x.changes.sum()} & {x.false.sum()} \\\\")
        rows.append("\\addlinespace")
    rows[-1] = "\\midrule"
    rows.append(f"All & & {(d.cp - d.reset).mean():+.2f} & {(d.mice - d.reset).mean():+.2f} & {(d.cp - d.mice).mean():+.2f} & "
                f"{(d.cp - d.archcp).mean():+.2f} & {(d.cp_rec - d.reset_rec).mean():+.1f} & "
                f"{(d.mice_rec - d.reset_rec).mean():+.1f} & {100 * wshare(d, 'cp_pure95_share'):.0f} & "
                f"{100 * d.cp_purity_mean.mean():.1f} & {d.found.sum()}/{d.changes.sum()} & {d.false.sum()} \\\\")
    open(f"{TEX}/tab_fresh_rows.tex", "w").write("\n".join(rows) + "\n")
    r = pd.DataFrame(regs)
    r.to_csv(f"{RES}/r14_regimes.csv", index=False)
    print(r.round(3).to_string(index=False))
    print("T1 majority share", round(wshare(d, "cp_major_share"), 3), "pure95 share", round(wshare(d, "cp_pure95_share"), 3),
          "calls cp/fixed/archcp", round(d.cp_calls.mean(), 2), round(d.mice_calls.mean(), 2), round(d.archcp_calls.mean(), 2),
          "experts", round(d.cp_experts.mean(), 2), round(d.mice_experts.mean(), 2), round(d.archcp_experts.mean(), 2),
          "s/batch cp", round(d.cp_s.mean(), 2))


def segsum():
    """One row per stream group: detected minus fixed segmentation, both against reset (FIFO on real streams)."""
    g = pd.read_csv(f"{RES}/r14_groups.csv")
    rows = []
    for grp, name, ref in (("aligned8", "Aligned grid", "reset"), ("shifted", "Shifted grid", "reset"),
                           ("misaligned", "Misaligned", "reset"), ("T1_fresh", "Fresh, random phase", "reset"),
                           ("real29", "Real", "fifo")):
        x = g[g.group == grp].set_index("diff")
        n = int(x.streams.iloc[0])
        cm = x.loc["cp-mice"]
        fixed = x.loc[f"mice-{ref}", "mean"] if f"mice-{ref}" in x.index else x.loc[f"cp-{ref}", "mean"] - cm["mean"]
        rows.append(f"{name} & {n} & {'Reset' if ref == 'reset' else 'FIFO'} & {x.loc[f'cp-{ref}', 'mean']:+.2f} & "
                    f"{fixed:+.2f} & {cm['mean']:+.2f} & [{cm.lo95:+.2f}, {cm.hi95:+.2f}] & {int(cm.above)}/{n} & "
                    f"{x.loc['cp-archcp', 'mean']:+.2f} \\\\")
    open(f"{TEX}/tab_segsum_rows.tex", "w").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    fresh()
    segsum()
