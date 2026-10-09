"""Tables for the resource benchmark of the TKDE revision (round 9): tab_cost_rows.tex (isolated benchmark, three
300-batch prefixes, mean over prefixes of the mean over three repetitions) and tab_fifo3000_rows.tex (MICE versus
FIFO 3000 on the 29 real streams). From ../results_paper/bench/ and ../results_paper/fifo3000_real*.csv."""
import pandas as pd

TEX, BEN = "../overleaf/tkde", "../results_paper/bench"
NAME = {"micev1000_500": "\\method{}", "fifo1000": "FIFO 1000", "fifo1500": "FIFO 1500", "fifo2000": "FIFO 2000",
        "fifo3000": "FIFO 3000 ($M^\\ast$)", "fifo5000": "FIFO 5000", "fifo13400": "FIFO 13\\,400",
        "winens1000": "Window ens."}
c = pd.read_csv(f"{BEN}/bench_cost_policy.csv", index_col=0)
acc = pd.read_csv(f"{BEN}/bench_accuracy_runs.csv").groupby(["policy", "stream"]).acc.mean().unstack()
rows = []
for p in NAME:
    r, a = c.loc[p], acc.loc[p]
    rows.append(f"{NAME[p]} & {r.mean_s:.2f} & {r.median_s:.2f} & {r.p95_s:.2f} & {r.max_s:.2f} & {r.rows_per_s:.0f} & "
                f"{r.peak_alloc_mib/1024:.1f} & {r.peak_reserved_mib/1024:.1f} & {r.peak_rss_mib/1024:.1f} & "
                f"{a.h4_airlines_d:.1f} & {a.h4_covertype_d:.1f} & {a.insects_abrupt_balanced:.1f} \\\\")
open(f"{TEX}/tab_cost_rows.tex", "w").write("\n".join(rows) + "\n")
f = pd.read_csv("../results_paper/fifo3000_real.csv")
import make_pool_tables as mpt
rows = [f"{mpt.name(x.stream)} & {x.batches} & {x.mice:.2f} & {x.fifo3000:.2f} & {x.d:+.2f} & [{x.lo:+.2f}, {x.hi:+.2f}] \\\\"
        for x in f.itertuples()]
g = pd.read_csv("../results_paper/fifo3000_real_aggregate.csv").iloc[0]
rows += ["\\midrule", f"Mean & & {f.mice.mean():.2f} & {f.fifo3000.mean():.2f} & {g['mean']:+.2f} & [{g.lo:+.2f}, {g.hi:+.2f}] \\\\"]
open(f"{TEX}/tab_fifo3000_rows.tex", "w").write("\n".join(rows) + "\n")
print(open(f"{TEX}/tab_cost_rows.tex").read()); print(rows[-1])
