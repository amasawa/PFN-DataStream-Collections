"""Table rows for the direct test of Theorem 1 (TKDE round 11): oracle recall versus relearning on the grid
(../results_grid_test/oracle_recall_summary.csv, written by oracle_recall.py --summary).
Writes ../overleaf/tkde/tab_oracle_rows.tex and, from the per-batch file oracle_recall.csv, the first-batch weights
and the identification agreement by accuracy gap (../results_grid_test/oracle_identification.csv). No number is
typed by hand."""
import pandas as pd

TEX = "../overleaf/tkde"

if __name__ == "__main__":
    r = pd.read_csv("../results_grid_test/oracle_recall_summary.csv")
    p, s = (r[r.seeds == t].set_index(["n_centroids", "block"]) for t in ("primary_s40_41", "secondary_s20_21"))
    rows = [f"{nc} & {L} & {p.predicted[nc, L]:.2f} & {p.area[nc, L]:.2f} & {p.ideal[nc, L]:.2f} & "
            f"{s.area[nc, L]:.2f} & {s.observed_mice_s20_21[nc, L]:.2f} \\\\" for nc, L in p.index]
    rows.append("\\midrule")
    rows.append(f"\\multicolumn{{2}}{{l}}{{Mean abs.\\ diff.\\ to Pred.}} & & {p.abs_err.mean():.2f} & "
                f"{p.abs_err_ideal.mean():.2f} & {s.abs_err.mean():.2f} & \\\\")
    open(f"{TEX}/tab_oracle_rows.tex", "w").write("\n".join(rows) + "\n")

    d = pd.read_csv("../results_grid_test/oracle_recall.csv")
    d = d[d.seed.isin([40, 41]) & (d.visit > 1)]
    f = d[d.j == 1]
    print(f"first batches of recurrences: {len(f)}, max w_S {f.w_S.max():.2g}, equal accuracy X = R on "
          f"{(f.acc_X == f.acc_R).mean():.3f}")
    g = d[d.j >= 2].copy()
    g["gap"] = 100 * (g.acc_S - g.acc_R).abs()
    g = g[g.gap > 0]
    g["ok"] = (g.w_S > 0.5) == (g.acc_S > g.acc_R)            # weight > 1/2 on the more accurate expert of the batch
    out = []
    for lo, hi in ((0, 2), (2, 5), (5, 10), (10, 100)):
        x = g[(g.gap > lo) & (g.gap <= hi)]
        out.append(dict(gap_lo=lo, gap_hi=hi, batches=len(x), agree=x.ok.mean(), share_of_gap=x.gap.sum() / g.gap.sum()))
    out = pd.DataFrame(out)
    out.to_csv("../results_grid_test/oracle_identification.csv", index=False)
    print(out.round(3).to_string(index=False))
    print(f"gap-weighted agreement {(g.gap * g.ok).sum() / g.gap.sum():.3f} over {len(g)} batches")
