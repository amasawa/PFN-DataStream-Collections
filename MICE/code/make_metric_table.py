"""LaTeX rows of the metric table from ../results_paper/metrics.csv (written by compute_metrics.py).
Rows: methods; columns: accuracy, macro-F1, ROC AUC, ECE, half Brier on the real streams and on the grid.
ddm and ltm appear on the real streams once run_probs.py has stored their probabilities for all of them.
Usage: python make_metric_table.py -> ../overleaf/icml/tab_metrics_rows.tex"""
import pandas as pd

a = pd.read_csv("../results_paper/metrics.csv"); a = a[~a.method.str.endswith("_file")]
a["set"] = a.group.replace({"grid10": "grid", "grid20": "grid", "realD": "real", "realC": "real", "realG": "real", "realH": "real", "realI": "real"})
n_real = a[a.set == "real"].stream.nunique()
cols, low = ["acc", "f1", "auc", "ece", "brier"], {"ece", "brier"}
names = [("fifo", "FIFO"), ("ltm", "LTM"), ("ddm", "Reset"), ("winens", "Window ensemble"), ("fast", "Fast level only"),
         ("mice10", "\\method{}, $\\eta_2=10$"), ("mice", "\\method{}")]
tab = {s: a[a.set == s].pivot_table(index="method", columns="stream", values=cols) for s in ("real", "grid")}
mean = {s: a[a.set == s].groupby("method")[cols].mean() * 100 for s in ("real", "grid")}
cnt = {s: a[a.set == s].groupby("method").stream.nunique() for s in ("real", "grid")}
full = {s: [m for m, _ in names if m in mean[s].index and cnt[s][m] == a[a.set == s].stream.nunique()] for s in ("real", "grid")}
L = []
for m, lab in names:
    cells = []
    for s in ("real", "grid"):
        for c in cols:
            if m not in full[s]:
                cells.append("--"); continue
            v = mean[s].loc[m, c]; ref = mean[s].loc[full[s], c]
            best = ref.min() if c in low else ref.max()
            cells.append(f"\\textbf{{{v:.1f}}}" if abs(v - best) < 1e-9 else f"{v:.1f}")
    if any(x != "--" for x in cells):
        L.append(f"    {lab} & " + " & ".join(cells) + " \\\\")
open("../overleaf/icml/tab_metrics_rows.tex", "w").write("\n".join(L) + "\n")
print("\n".join(L)); print("real streams:", n_real, "| methods with all real streams:", full["real"])
