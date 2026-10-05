"""Checks pre-registration G (second set of held-out real streams) exactly as written in the log. Written before any
result was available."""
import pandas as pd
from evaluate import summarise
D = "../results_heldout2"
s = summarise(D, 5); s.to_csv(f"{D}/summary.csv", index=False)
pd.set_option("display.width", 250)
a = s.pivot_table(index="stream", columns="method", values="acc").drop(columns="micev1000_500", errors="ignore")
a.columns = [c.replace("mooe_rff2000_100_2_0.01", "mooe2000").replace("mooe_rff4000_100_2_0.01", "mooe4000") for c in a.columns]
print(a.round(4).to_string()); print("mean", a.mean().round(4).to_dict())
base = [c for c in a.columns if c != "mice"]; tfm = ["fifo1000", "ltm1000_75", "ddm1000", "winens1000"]
g = a.mice - a.ddm1000
print("G1 mice-ddm:", g.round(4).to_dict(), "all >= -0.005:", bool((g >= -0.005).all()))
best = a[base].max(1)
print("G2a mice best on", int((a.mice > best).sum()), "of", len(a), "(>= 4?); margin to the best baseline:", (a.mice - best).round(4).to_dict(),
      "best baseline:", a[base].idxmax(1).to_dict())
m = a.mean(); print("G2b mice has the highest mean:", bool(m.mice > m[base].max()))
print("G3 mice - best TFM context baseline:", (a.mice - a[tfm].max(1)).round(4).to_dict())
print("G4 best trained baseline - TabPFN fifo:", (a[[c for c in base if c not in tfm]].max(1) - a.fifo1000).round(4).to_dict())
