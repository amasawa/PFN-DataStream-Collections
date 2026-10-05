"""Checks pre-registrations I (fourth held-out set, TabPFN v2) and J (TabICL on four segments of the third held-out
set) exactly as written in the log (2026-10-05). Written before any of these runs produced a result.
The method under test is the method of the paper: two-timescale rule, half Brier outer loss, step 1/2, tempered.
Usage: python check_heldout4.py I | J | K"""
import glob, os, pickle, sys
import numpy as np, pandas as pd
import reweight

pd.set_option("display.width", 250)
which = sys.argv[1]
D = {"I": "../results_heldout4", "J": "../results_heldout3_tabicl", "K": "../results_heldout3_seed1", "L": "../results_heldout4_seed1", "M": "../results_heldout4_tabicl", "M2": "../results_heldout4_tabicl_e"}[which]   # K added 2026-10-05, before its run
m = lambda a: float(np.mean(list(a.values())))
kw = dict(outer="brier", scale=0.5, temper=True)
rows = []
for f in sorted(glob.glob(f"{D}/*__micev1000_500.pkl")):
    s = os.path.basename(f).split("__")[0]; c = pickle.load(open(f, "rb"))
    r = dict(stream=s, mice=m(reweight.simulate2(c, **kw)), mice10=m(reweight.simulate2(c, outer="brier")),
             fast=m(reweight.simulate(c, 10, 0.0)), windows=m(reweight.simulate2(c, subset=lambda u: u < 0, **kw)))
    for b in ("fifo1000", "ltm1000_75", "ddm1000", "winens1000"):
        g = f"{D}/{s}__{b}.npz"   # key fixed 2026-10-05: the first version turned ltm1000_75 into "ltm100"
        r[b.replace("1000", "").replace("_75", "")] = float(np.nanmean(np.load(g)["acc"])) if os.path.exists(g) else np.nan
    rows.append(r)
a = pd.DataFrame(rows).set_index("stream"); a.to_csv(f"{D}/summary_{which}.csv")
print((100 * a).round(2).to_string()); print("mean", (100 * a.mean()).round(2).to_dict())
tfm = [c for c in ("fifo", "ltm", "ddm", "winens") if a[c].notna().all()]
d1 = a.mice - a[["fifo", "ddm"]].max(1); d2 = a.mice - a[tfm].max(1); d3 = a.mice - a.fifo; d4 = a.mice - a.windows
n = len(a)
print(f"{which}1 non-inferiority, mice - max(fifo, ddm) >= -0.5 on every segment:", bool((d1 >= -0.005).all()), (100 * d1).round(2).to_dict())
print(f"{which}2a mice above all of {tfm} on {(d2 > 0).sum()} of {n} (majority = {n // 2 + 1}):", bool((d2 > 0).sum() >= n // 2 + 1), (100 * d2).round(2).to_dict())
print(f"{which}2b highest mean:", bool(a.mice.mean() > a[tfm].mean().max()), "mean margin %+.2f" % (100 * d2.mean()))
print(f"{which}3 safety, mice - fifo >= -0.3 on every segment:", bool((d3 >= -0.003).all()), (100 * d3).round(2).to_dict(), "mean %+.2f" % (100 * d3.mean()))
print(f"{which}4 memory, mice above the windows-only variant on {(d4 > 0).sum()} of {n} (majority?):", bool((d4 > 0).sum() >= n // 2 + 1), (100 * d4).round(2).to_dict())
print("report only: step 10 minus step 1/2", (100 * (a.mice10 - a.mice)).round(2).to_dict(), "; fast level alone minus fifo", (100 * (a.fast - a.fifo)).round(2).to_dict(),
      "; ddm minus fifo", (100 * (a.ddm - a.fifo)).round(2).to_dict())
