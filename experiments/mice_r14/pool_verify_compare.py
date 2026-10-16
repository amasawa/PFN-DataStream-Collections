"""Bit-identity check: pool outputs vs reference outputs (prints only equal / not equal, never values)."""
import pickle, sys
import numpy as np
T = "/home/zhwu9808/pfn-runs/mice-r14b-pooltest"
A = "/home/zhwu9808/pfn-runs/mice-r14b-acc"
C = "/home/zhwu9808/pfn-runs/mice-r14-confirm"
pairs = [(f"{T}/pool/P_k2/c_b2000_c100_s50_o1__snap1000_500", f"{A}/P_k2/c_b2000_c100_s50_o1__snap1000_500"),
         (f"{T}/pool/P_k4/c_b500_c100_s51_o1__snap1000_500", f"{T}/fresh/P_k4/c_b500_c100_s51_o1__snap1000_500"),
         (f"{T}/pool/P/c_b500_c100_s50_o0__micecp1000_500", f"{C}/P/c_b500_c100_s50_o0__micecp1000_500"),
         (f"{T}/pool/P_k2/c_b500_c100_s50_o2__snap1000_500", f"{A}/P_k2/c_b500_c100_s50_o2__snap1000_500")]


def same(a, b):
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, np.ndarray):
        return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b, equal_nan=True)
    return a == b


ok = True
for p, r in pairs:
    zp, zr = np.load(p + ".npz"), np.load(r + ".npz")
    keys = sorted(set(zp.files) | set(zr.files))
    res = {k: same(zp[k], zr[k]) for k in keys if k != "wt"}
    cache = same(pickle.load(open(p + ".pkl", "rb")), pickle.load(open(r + ".pkl", "rb")))
    good = all(res.values()) and cache
    ok &= good
    print(p.split("/")[-2], p.split("/")[-1], "IDENTICAL" if good else f"DIFFERENT npz={res} cache={cache}")
print("ALL IDENTICAL" if ok else "NOT IDENTICAL")
