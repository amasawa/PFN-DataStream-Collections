"""Table for TKDE round 13 (PLAN.md "Round 13"): MICE against the archive and snapshot pools at capacities 2, 4 and 12.
Resources from the isolated benchmarks (A1: three 300-batch real prefixes; A2: four grid streams, MICE, k* and k=12
only), accuracy differences MICE - control from part C (k* = 2; k = 4 supplementary when run) with 95% intervals of
the group mean, and the kmax-12 differences on the same streams (no interval). Writes tab_poolcap_rows.tex."""
import os

import pandas as pd

TEX, RES = "../overleaf/tkde", "../results_paper"
a1 = pd.read_csv(f"{RES}/r13_a1_policy.csv", index_col=0)
a2 = (pd.read_csv(f"{RES}/r13_a2_stream.csv").groupby("policy").mean(numeric_only=True)
      if os.path.exists(f"{RES}/r13_a2_stream.csv") else None)
grp = pd.read_csv(f"{RES}/r13_c_groups.csv").set_index(["group", "control"])
st = pd.read_csv(f"{RES}/r13_c_streams.csv")
sup = (pd.read_csv(f"{RES}/r13_c4_groups.csv").set_index(["group", "control"])
       if os.path.exists(f"{RES}/r13_c4_groups.csv") else None)
GROUPS = ("aligned", "shifted", "real")
NAME = {"mice": "\\method{}", "arch2": "Archive, $k=2$", "snap2": "Snapshot, $k=2$", "arch4": "Archive, $k=4$",
        "snap4": "Snapshot, $k=4$", "arch12": "Archive, $k=12$", "snap12": "Snapshot, $k=12$"}


def delta(p, g):
    t = grp if p.endswith("2") and not p.endswith("12") else sup if p.endswith("4") else None
    if p.endswith("12"):
        x = st[st.group == g][f"d_{p[:4]}12"]
        return "--" if x.isna().any() else f"${x.mean():+.2f}$"
    if t is None or (g, p) not in t.index:
        return "--"
    r = t.loc[(g, p)]
    return f"${r.mean_delta:+.2f}$ $[{r.lo95:+.2f},{r.hi95:+.2f}]$"


rows = []
for p, nm in NAME.items():
    r = a1.loc[p]
    g2 = f"{a2.loc[p].mean_s:.2f}" if a2 is not None and p in a2.index else "--"
    d = " & ".join("" if p == "mice" else delta(p, g) for g in GROUPS)
    rows.append(f"{nm} & {r.experts:.1f} & {r.calls:.1f} & {r.rows_k:.1f} & {r.mean_s:.2f} & {g2} & "
                f"{r.peak_reserved_gb:.2f} & {d} \\\\")
    if p == "snap2":
        rows.append("\\midrule")
open(f"{TEX}/tab_poolcap_rows.tex", "w").write("\n".join(rows) + "\n")
print("\n".join(rows))
