"""Table for TKDE round 14.b (experiments/mice_r14/PLAN_14B.md): resources of MICE with detected segmentation against
the archive with the same detected segments (kmax 12) and the snapshot pool (k* prefix-budget-selected, the other
candidate as a sensitivity row, and kmax 12 capacity-matched), from the isolated benchmarks (A1: three 300-batch real
prefixes; A2: four grid streams), and the accuracy difference MICE minus snapshot from part C on the 72 confirmation
streams, the 8 shifted and the 12 misaligned grid streams, with 95% intervals. A separate table from the
fixed-segmentation tables (rule E). Writes tab_cpres_rows.tex."""
import json
import os

import pandas as pd

TEX, RES = "../overleaf/tkde", "../results_paper"
BENCH = os.path.expanduser("~/pfn-runs/mice-r14b-bench")
ks = json.load(open(f"{BENCH}/kstar.json"))
k = int(ks["snap"])
other = 4 if k == 2 else 2
a1 = pd.read_csv(f"{RES}/r14b_a1_policy.csv", index_col=0)
a2 = pd.read_csv(f"{RES}/r14b_a2_stream.csv").groupby("policy").mean(numeric_only=True)
grp = pd.read_csv(f"{RES}/r14b_c_groups.csv").set_index(["control", "group"])
GROUPS = ("confirm_all", "shifted", "misaligned")
NAME = {"mice": "\\method{}", "archcp12": "Archive, $k=12$", f"snap{k}": f"Snapshot, $k={k}$",
        f"snap{other}": f"Snapshot, $k={other}$", "snap12": "Snapshot, $k=12$"}


def cell(p, g):
    if not p.startswith("snap") or (p, g) not in grp.index:
        return "--"
    r = grp.loc[(p, g)]
    return f"${r['mean']:+.2f}$ $[{r.lo95:+.2f},{r.hi95:+.2f}]$"


rows = []
for p, nm in NAME.items():
    r = a1.loc[p]
    g2 = f"{a2.loc[p].mean_s:.2f}" if p in a2.index else "--"
    d = " & ".join("" if p == "mice" else cell(p, g) for g in GROUPS)
    rows.append(f"{nm} & {r.experts:.1f} & {r.calls:.1f} & {r.rows_k:.1f} & {r.mean_s:.2f} & {r.p95_s:.2f} & {g2} & "
                f"{r.peak_reserved_gb:.2f} & {d} \\\\")
open(f"{TEX}/tab_cpres_rows.tex", "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
