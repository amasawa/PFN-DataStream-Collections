"""Checks the decision rule for the locally referenced error policy exactly as written in the log (2026-10-05 13:44),
on the development data. Written before the last five real streams had finished.
Usage: python check_lref.py -> ../results/stream_lref_dev/summary_lref.csv"""
import glob, os
import numpy as np, pandas as pd
from stream_eval import summarise

pd.set_option("display.width", 250)
rows = {}
for d in ("../results/stream_real", "../results/stream_heldout", "../results/stream_lref_dev"):
    for f in glob.glob(f"{d}/*.npz"):
        s, p = os.path.basename(f)[:-4].split("__")
        if p in ("fifo", "ddm", "lref", "lref_min", "triage_np"):
            z = np.load(f); rows[(s, p)] = dict(acc=float(np.nanmean(z["acc"])), resets=len(z["resets"]))
a = pd.DataFrame(rows).T; acc = a.acc.unstack().astype(float); res = a.resets.unstack()
acc = acc.dropna(subset=["lref"]); acc.to_csv("../results/stream_lref_dev/summary_lref.csv")
print((100 * acc).round(2).to_string()); print("resets\n", res.loc[acc.index, ["ddm", "lref", "lref_min"]].to_string())
print("mean", (100 * acc.mean()).round(2).to_dict(), "n =", len(acc))
d = acc.lref - acc[["fifo", "ddm"]].max(1)
print("rule 1a: mean lref > mean fifo and > mean ddm:", bool(acc.lref.mean() > acc.fifo.mean() and acc.lref.mean() > acc.ddm.mean()))
print("rule 1b: lref >= max(fifo, ddm) - 0.005 on every stream:", bool((d >= -0.005).all()), "; violations:", (100 * d[d < -0.005]).round(2).to_dict())
harm, help_ = acc[acc.ddm - acc.fifo < -0.005], acc[acc.ddm - acc.fifo > 0.005]
print("rule 2a: where ddm is harmful, lref - fifo:", (100 * (harm.lref - harm.fifo)).round(2).to_dict(), "all >= -0.3:", bool((harm.lref - harm.fifo >= -0.003).all()))
print("rule 2b: where ddm helps, lref - ddm:", (100 * (help_.lref - help_.ddm)).round(2).to_dict(), "all >= -0.3:", bool((help_.lref - help_.ddm >= -0.003).all()))
print("lref - ddm: wins %d of %d, mean %+.2f, min %+.2f; lref - fifo: wins %d, mean %+.2f, min %+.2f" % (
    (acc.lref > acc.ddm).sum(), len(acc), 100 * (acc.lref - acc.ddm).mean(), 100 * (acc.lref - acc.ddm).min(),
    (acc.lref > acc.fifo).sum(), 100 * (acc.lref - acc.fifo).mean(), 100 * (acc.lref - acc.fifo).min()))
s = pd.concat([summarise("../results/stream_lref_syn", 10), summarise("../results/stream_dev_v2", 10)])
s["family"] = s.stream.str.replace(r"_s\d+$", "", regex=True)
g = s[s.policy.isin(["ddm", "lref"])].groupby(["family", "policy"])[["acc", "acc_real"]].mean().unstack()
print("rule 3: per family, lref - ddm overall %s (>= -0.3), after real drift %s (>= -1.0)" % (
    (100 * (g[("acc", "lref")] - g[("acc", "ddm")])).round(2).to_dict(), (100 * (g[("acc_real", "lref")] - g[("acc_real", "ddm")])).round(2).to_dict()))
