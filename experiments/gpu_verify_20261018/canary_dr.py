"""Drift-Resilient TabPFN canary (PLAN.md): run_drtabpfn.run on the first 12 batches of elec2 in a fresh process on the
GPU, output <out>/elec2__drtabpfn.npz. Usage: python canary_dr.py <out dir>"""
import os, sys
import numpy as np
sys.path.insert(0, "/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018")
import run_drtabpfn as r

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
z = np.load("/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/data/elec2.npz")
np.savez(f"{out}/elec2.npz", X=z["X"][:1200], y=z["y"][:1200])
r.run(r.get_model(), out, "elec2", 100, out)
