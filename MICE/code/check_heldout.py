"""Checks the hypotheses of pre-registration C (held-out real streams) exactly as written in the log. Written before
any held-out result was available."""
import pandas as pd

from evaluate import summarise

D = "../results_heldout"
s = summarise(D, 5)
s.to_csv(f"{D}/summary.csv", index=False)
pd.set_option("display.width", 220)
a = s.pivot_table(index="stream", columns="method", values="acc").drop(columns="micev1000_500", errors="ignore")
print(a.round(4).to_string())
print("time (s)\n", s.pivot_table(index="stream", columns="method", values="time").round(0).to_string())
base = [c for c in a.columns if c != "mice"]
g = a.mice - a.ddm1000
print("C1 mice-ddm:", g.round(4).to_dict(), "all >= -0.005:", bool((g >= -0.005).all()))
best = a[base].max(1)
print("C2a mice is the best method on", int((a.mice > best).sum()), "of", len(a), "streams (>= 3?); margin to the best baseline:",
      (a.mice - best).round(4).to_dict())
m = a.mean()
print("C2b mean over streams:", m.round(4).to_dict(), "mice highest:", bool(m.mice > m[base].max()))
riv = [c for c in ("arf", "srp", "hat") if c in a]
print("C3 every river learner below TabPFN fifo on every stream:", bool((a[riv].max(1) < a.fifo1000).all()),
      (a[riv].max(1) - a.fifo1000).round(4).to_dict())
print("C4 ltm-fifo:", (a.ltm1000_75 - a.fifo1000).round(4).to_dict())
