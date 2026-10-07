"""Figure 1 of the TMLR draft: per-source effect of the three reset actions on three TFMs (detector average, points
against FIFO). Sources are ordered by the full-reset effect on TabPFN. -> ../overleaf/tmlr/figs/fig_sources.pdf"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from make_tables import DETS, OUT, RES, TFM, d_table

COL = {"": "#eb6834", "+half": "#1baf7a", "+hedge": "#2a78d6"}          # reference palette slots 2, 3, 1
LAB = {"": "full reset", "+half": "keep half", "+hedge": "hedge"}
MRK = {"": "o", "+half": "s", "+hedge": "D"}

if __name__ == "__main__":
    per = {}
    for name, tag in TFM:
        S, _ = d_table(f"{RES}/{tag}", [k + v for k in DETS for v in COL], groups=("real",))
        per[name] = {v: S[S.pol.isin([k + v for k in DETS])].groupby(["pol", "src"]).d.mean().groupby("src").mean() for v in COL}
    order = per["TabPFN"][""].sort_values().index
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": "#888888", "axes.linewidth": 0.6,
                         "xtick.color": "#555555", "ytick.color": "#333333"})
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.4), sharey=True)
    y = np.arange(len(order))
    for ax, (name, _) in zip(axes, TFM):
        ax.axvline(0, color="#999999", lw=0.8, zorder=0)
        ax.grid(axis="x", color="#e5e5e5", lw=0.5, zorder=0)
        for i, s in enumerate(order):                      # thin connector from hedge to full reset per source
            ax.plot([per[name]["+hedge"][s], per[name][""][s]], [i, i], color="#cccccc", lw=0.8, zorder=1)
        for v, off in (("", -0.22), ("+half", 0.0), ("+hedge", 0.22)):  # small vertical offsets so coincident marks stay visible
            ax.scatter(per[name][v][order], y + off, s=16, marker=MRK[v], color=COL[v], edgecolor="white", linewidth=0.6,
                       zorder=3, label=LAB[v])
        ax.set_title(name, fontsize=9)
        ax.set_xlim(-37, 10)
        ax.set_xlabel("accuracy vs. FIFO (points)")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_yticks(y); axes[0].set_yticklabels(order)
    axes[0].invert_yaxis()
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.55, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    d = os.path.join(OUT, "..", "figs"); os.makedirs(d, exist_ok=True)
    fig.savefig(f"{d}/fig_sources.pdf"); fig.savefig(f"{d}/fig_sources.png", dpi=200)
    print("saved", {n: {LAB[v]: round(per[n][v].min(), 1) for v in COL} for n in per})
