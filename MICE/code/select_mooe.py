"""Freezes the MOOE configuration: highest mean accuracy over the five development real streams (ties: first in
sorted order). Prints the method name; writes the full table to ../results_trained_dev/grid.csv."""
import sys
import pandas as pd
from evaluate import summarise
s = summarise("../results_trained_dev", 5)
p = s.pivot_table(index="method", columns="stream", values="acc")
p = p[p.notna().all(1)]
p["mean"] = p.mean(1)
p.sort_values("mean", ascending=False).to_csv("../results_trained_dev/grid.csv")
if len(p) < 72:
    sys.exit(f"only {len(p)} of 72 configurations complete")
print(p["mean"].sort_index().idxmax())
