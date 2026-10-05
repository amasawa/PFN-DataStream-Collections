"""Figure 1 of the paper: (a) learning curves of the grid concepts (seeds 10, 11, measured before the grid was run);
(b) gain of memory over reset, predicted from these curves against observed. Reads results_grid_test/learning_curve.csv
and results_paper/all.csv. Usage: python make_paper_fig.py -> ../overleaf/icml/fig_recall.pdf"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, AQUA, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "pdf.fonttype": 42})
fig, (a, b) = plt.subplots(1, 2, figsize=(3.3, 1.75), gridspec_kw=dict(wspace=0.55, left=0.15, right=0.985, bottom=0.21, top=0.9))

lc = pd.read_csv("../results_grid_test/learning_curve.csv").groupby(["n_centroids", "n"]).acc.mean().unstack()
for c, col, mk in ((5, BLUE, "o"), (30, ORANGE, "s"), (100, AQUA, "^")):
    a.plot(lc.columns, 100 * lc.loc[c], color=col, lw=1.4, marker=mk, ms=3, mec="white", mew=0.5, label=f"{c} centroids")
a.set_xscale("log"); a.set_xticks([50, 200, 1000]); a.set_xticklabels(["50", "200", "1000"]); a.minorticks_off()
a.set_xlim(42, 2400); a.set_ylim(30, 103); a.grid(axis="y", color=GRID, lw=0.5); a.set_axisbelow(True)
a.set_xlabel("context rows $n$"); a.set_ylabel("accuracy (%)"); a.set_title("(a) learning curves", fontsize=7, color=INK, loc="left")
a.legend(frameon=False, fontsize=5.5, loc="lower right", handlelength=1.4, borderaxespad=0.1)

pred = {(5, 500): 0.0009, (5, 2000): 0.0003, (30, 500): 0.0191, (30, 2000): 0.0055, (100, 500): 0.1044, (100, 2000): 0.0303}
g = pd.read_csv("../results_paper/all.csv"); g = g[g.group.isin(["grid10", "grid20"])].copy()
g["c"] = g.stream.str.extract(r"_c(\d+)_")[0].astype(int); g["b"] = g.stream.str.extract(r"_b(\d+)_")[0].astype(int)
b.plot([0, 11], [0, 11], color=MUTED, lw=0.6, ls=(0, (3, 2)), zorder=1)
for grp, col, mk, key, lab in (("grid10", BLUE, "o", "mice1", "seeds 10, 11"), ("grid20", ORANGE, "s", "mice", "seeds 20, 21")):
    x = g[g.group == grp]
    obs = [100 * (x[(x.c == c) & (x.b == bb)][key] - x[(x.c == c) & (x.b == bb)].ddm).mean() for (c, bb) in pred]
    b.scatter([100 * p for p in pred.values()], obs, s=16, color=col, marker=mk, edgecolor="white", linewidth=0.6, zorder=3, label=lab)
b.annotate("100 centroids,\nblock 500", (10.44, 8.55), xytext=(-6, -14), textcoords="offset points", ha="right", color=INK, fontsize=5.5)
b.set_xlim(-0.6, 11.5); b.set_ylim(-0.6, 11.5); b.set_xticks([0, 5, 10]); b.set_yticks([0, 5, 10])
b.grid(color=GRID, lw=0.5); b.set_axisbelow(True)
b.set_xlabel("predicted gain (points)"); b.set_ylabel("observed gain (points)")
b.set_title("(b) recall vs. relearn", fontsize=7, color=INK, loc="left")
b.legend(frameon=False, fontsize=5.5, loc="upper left", handletextpad=0.2, borderaxespad=0.1)
fig.savefig("../overleaf/icml/fig_recall.pdf"); fig.savefig("../overleaf/icml/fig_recall.png", dpi=300)
