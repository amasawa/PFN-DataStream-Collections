"""Table rows for the pool controls of the TKDE revision (round 2): aligned grid (pool_control_grid.csv, registered
criterion 1) and real streams (pool_control_real_full.csv, registered criterion 2 and the registered snapshot
addition; MICE - archive bounds retrospective). Writes ../overleaf/tkde/tab_pool_grid_rows.tex and
tab_pool_real_rows.tex. No number is typed by hand."""
import pandas as pd

TEX = "../overleaf/tkde"
NAME = {"elec2": "Electricity", "insects_abrupt_balanced": "INSECTS abr.", "insects_gradual_balanced": "INSECTS grad.",
        "insects_incremental_balanced": "INSECTS inc.", "insects_incremental_reoccurring_balanced": "INSECTS inc.-rec.",
        "covertype": "CoverType", "insects_abrupt_imbalanced": "INSECTS abr.-imb.",
        "insects_gradual_imbalanced": "INSECTS grad.-imb.", "insects_incremental_abrupt_balanced": "INSECTS inc.-abr.",
        "h2_airlines": "Airlines", "h2_phishing": "Phishing", "h2_poker": "PokerHand", "h2_rialto": "Rialto",
        "h2_spam": "Spam", "h2_weather": "Weather"}


def name(s):
    if s in NAME:
        return NAME[s]
    h, src, seg = s.split("_")
    return {"airlines": "Airlines", "covertype": "CoverType", "insects": "INSECTS", "poker": "PokerHand"}[src] + \
        f" {h[1]}{seg}"


g = pd.read_csv("../results_paper/pool_control_grid.csv").sort_values(["nc", "block", "stream"])
rows = [f"{r.nc} & {r.block} & {r.stream[-2:]} & {r.mice:.1f} & {r.arch:.1f} & {r.snap:.1f} & {r.d_arch:+.2f} & "
        f"{r.d_snap:+.2f} & {r.mice_calls:.1f} & {r.arch_calls:.1f} \\\\" for r in g.itertuples()]
h = g[g.nc >= 30]
rows += ["\\midrule", f"30/100 & & & {h.mice.mean():.1f} & {h.arch.mean():.1f} & {h.snap.mean():.1f} & "
         f"{h.d_arch.mean():+.2f} & {h.d_snap.mean():+.2f} & {h.mice_calls.mean():.1f} & {h.arch_calls.mean():.1f} \\\\"]
open(f"{TEX}/tab_pool_grid_rows.tex", "w").write("\n".join(rows) + "\n")

r = pd.read_csv("../results_paper/pool_control_real_full.csv")
rows = [f"{name(x.stream)} & {x.batches} & {x.mice:.2f} & {x.d_arch:+.2f} & {x.lb_arch_b20_retro:+.2f} & {x.d_snap:+.2f} & "
        f"{x.lb_snap_b20:+.2f} & {x.mice_experts_mean:.1f} & {x.arch_experts_mean:.1f} & {x.mice_calls_per_batch:.1f} & "
        f"{x.arch_calls_per_batch:.1f} \\\\" for x in r.itertuples()]
rows += ["\\midrule", f"Mean & & {r.mice.mean():.2f} & {r.d_arch.mean():+.2f} & & {r.d_snap.mean():+.2f} & & "
         f"{r.mice_experts_mean.mean():.1f} & {r.arch_experts_mean.mean():.1f} & {r.mice_calls_per_batch.mean():.1f} & "
         f"{r.arch_calls_per_batch.mean():.1f} \\\\"]
open(f"{TEX}/tab_pool_real_rows.tex", "w").write("\n".join(rows) + "\n")
print(open(f"{TEX}/tab_pool_grid_rows.tex").read()); print(open(f"{TEX}/tab_pool_real_rows.tex").read()[-600:])
