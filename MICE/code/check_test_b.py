"""Checks the hypotheses of pre-registration B (family test seeds 10-14 and real streams) exactly as written in the
log. Written before the test results were available."""
import numpy as np
import pandas as pd

from evaluate import summarise

D = "../results_test"
REAL = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
        "insects_incremental_reoccurring_balanced"]
s = summarise(D, 5)
s.to_csv(f"{D}/summary.csv", index=False)
s["family"] = s.stream.str.replace(r"_s\d+$", "", regex=True)
pd.set_option("display.width", 220)
acc = s.pivot_table(index=["family", "stream"], columns="method", values="acc")
rec = s.pivot_table(index=["family", "stream"], columns="method", values="acc_recur")
fam = acc[~acc.index.get_level_values("family").isin(REAL)]
real = acc[acc.index.get_level_values("family").isin(REAL)].droplevel("family")
print("family means, overall accuracy\n", fam.groupby("family").mean().round(4).to_string())
print("real streams, overall accuracy\n", real.round(4).to_string())

g = fam.mice - fam.ddm1000
print(f"B1 family mean mice-ddm = {g.mean():+.4f} over {len(g)} streams (>= -0.002?)", g.mean() >= -0.002,
      f"wins {(g > 0).sum()}/{len(g)}")
print("   per family:", g.groupby("family").mean().round(4).to_dict(), "all <= 0.01:",
      bool((g.groupby("family").mean() <= 0.01).all()))
r = rec.groupby("family").mean().loc[["sine", "stagger", "agrawal"]]
print("B2 accuracy in the first 5 batches after a recurrence\n", r.round(4).to_string())
print("   fifo, ltm <= 0.6:", bool((r[["fifo1000", "ltm1000_75"]] <= 0.6).all().all()), " oracle >= 0.98:",
      bool((r.oracle1000 >= 0.98).all()))
gr = real.mice - real.ddm1000
print("B3 real streams mice-ddm:", gr.round(4).to_dict(), "all >= -0.005:", bool((gr >= -0.005).all()))
ins = gr.drop("elec2")
print("B4 (exploratory) reoccurring gain is the largest INSECTS gain:",
      bool(ins.idxmax() == "insects_incremental_reoccurring_balanced"))
d = (acc.ltm1000_75 - acc.fifo1000)
print(f"B5 ltm-fifo: mean {d.mean():+.4f}, max |diff| over streams {d.abs().max():.4f} (< 0.01?)",
      bool(d.abs().max() < 0.01), "per family:", d.groupby("family").mean().round(4).to_dict())
print("mice-winens:", (acc.mice - acc.winens1000).groupby("family").mean().round(4).to_dict())
