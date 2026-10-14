"""Table rows for the direct test of Theorem 1 (TKDE round 11): oracle recall versus relearning on the grid
(../results_grid_test/oracle_recall_summary.csv, written by oracle_recall.py --summary).
Writes ../overleaf/tkde/tab_oracle_rows.tex. No number is typed by hand."""
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
