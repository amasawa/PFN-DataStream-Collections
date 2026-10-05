"""Checks pre-registration H exactly as written in the log. Written before any result was available.
Part 0 replays the frozen two-timescale rule on the synthetic TEST caches; part 1 evaluates the third held-out set."""
import glob, os, pickle, sys
import numpy as np, pandas as pd
import reweight
from evaluate import summarise

pd.set_option("display.width", 250)
if "syn" in sys.argv:
    rows = []
    for d in ("../results_grid_test", "../results_test"):
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if not s[-4:-2] == "_s":
                continue
            c = pickle.load(open(f, "rb"))
            r = dict(stream=s, mice=np.mean(list(reweight.simulate(c, 10, 0.0).values())), mice2=np.mean(list(reweight.simulate2(c).values())))
            for b in ("ddm1000", "fifo1000", "winens1000"):
                r[b] = float(np.nanmean(np.load(f"{d}/{s}__{b}.npz")["acc"]))
            rows.append(r)
    a = pd.DataFrame(rows); a["cell"] = a.stream.str.replace(r"_s\d+$", "", regex=True); a.to_csv("../results_rules/h0_syn.csv", index=False)
    print(a.groupby("cell").mean(numeric_only=True).round(4).to_string())
    g, f = a[a.stream.str.startswith("grid")], a[~a.stream.str.startswith("grid")]
    print("H0a grid test: mean mice2 - mice = %+.4f (>= -0.005?)" % (g.mice2 - g.mice).mean(), "; hard cells (c30, c100): mice2 > ddm on",
          int((g[g.stream.str.contains("c30|c100")].mice2 > g[g.stream.str.contains("c30|c100")].ddm1000).sum()), "of 8")
    print("H0b family test: mean mice2 - mice = %+.4f (>= -0.003?)" % (f.mice2 - f.mice).mean(), "; mean mice2 - ddm = %+.4f" % (f.mice2 - f.ddm1000).mean())
else:
    D = "../results_heldout3"
    reweight.freeze(D, "micev1000_500", 10, 0.0, "mice"); reweight.freeze2(D, "micev1000_500", "mice2")
    reweight.freeze2(D, "micev1000_500", "mice3", outer="brier")   # added 2026-10-05 03:58, before any result existed
    # exploratory, added 2026-10-05 10:41 (after the baselines of three segments were visible, before any mice result):
    # the outer step inside the range covered by the regret bound (half Brier, step 1/2, tempered weights)
    reweight.freeze2(D, "micev1000_500", "mice3t", outer="brier", scale=0.5, temper=True)
    s = summarise(D, 5); s.to_csv(f"{D}/summary.csv", index=False)
    a = s.pivot_table(index="stream", columns="method", values="acc").drop(columns="micev1000_500", errors="ignore")
    print(a.round(4).to_string()); print("mean", a.mean().round(4).to_dict())
    tfm = ["fifo1000", "ltm1000_75", "ddm1000", "winens1000"]
    d1 = a.mice2 - a[["fifo1000", "ddm1000"]].max(1)
    print("H1 mice2 - max(fifo, ddm):", d1.round(4).to_dict(), "all >= -0.005:", bool((d1 >= -0.005).all()))
    d2 = a.mice2 - a[tfm].max(1)
    print("H2a mice2 best among the TFM context methods on", int((d2 > 0).sum()), "of", len(a), "(>= 5?); margins", d2.round(4).to_dict())
    print("H2b mice2 has the highest mean:", bool(a.mice2.mean() > a[tfm].mean().max()), "; mean margin %+.4f" % d2.mean())
    d3 = a.mice2 - a.mice
    print("H3 mice2 - mice:", d3.round(4).to_dict(), "all >= -0.003:", bool((d3 >= -0.003).all()))
    for name, col in (("H1", a.mice3 - a[["fifo1000", "ddm1000"]].max(1)), ("H2", a.mice3 - a[tfm].max(1)), ("H3", a.mice3 - a.mice)):
        print(f"mice3 {name}:", col.round(4).to_dict(), "min %+.4f, mean %+.4f, positive on %d of %d" % (col.min(), col.mean(), (col > 0).sum(), len(col)))
    print("mice3 has the highest mean among the TFM context methods:", bool(a.mice3.mean() > a[tfm].mean().max()))
    print("exploratory mice3t - mice3:", (a.mice3t - a.mice3).round(4).to_dict(), "; mice3t - best TFM baseline:", (a.mice3t - a[tfm].max(1)).round(4).to_dict())
    src = a.index.str.replace(r"_[bc]$", "", regex=True)
    print("mice3 per source, mean margin to the best TFM baseline:", (a.mice3 - a[tfm].max(1)).groupby(src).mean().round(4).to_dict())
    print("per source, mean margin to the best TFM baseline:", d2.groupby(src).mean().round(4).to_dict())
