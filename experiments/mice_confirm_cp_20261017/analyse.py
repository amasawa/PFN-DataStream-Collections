"""Evaluator of the confirmation of detected segmentation (PLAN.md), written and committed before any run.
Reads <root>/P (all tasks of tasks.txt and the CPU tasks must be present: refuses partial outputs) and writes
MICE/results_paper/confirm_detected/: acc.csv (segment x method, fractions), metrics.csv (F1, AUC, ECE, half Brier,
log-loss; fractions), hypotheses.csv (H1..H5 with their numbers), summary.csv (per method: mean accuracy in percent,
worst difference to FIFO in points, per source means).

Accuracies: mice (fixed segments, micev1000_500) and mice_cp (micecp1000_500) are replayed from their expert caches
with the frozen rule reweight.simulate2(outer = brier, scale = 0.5, temper = True); mice_cp_nopool is the same replay
on the cache of mice_cp restricted to the window experts (keys < 0, as check_heldout4.py "windows"); fifo, ltm, ddm,
winens, arf, srp: nanmean of the per-batch accuracy of their run files. Batch 0 is warm-up and not scored.
Hypotheses use the 9 primary segments only (STREAMS); the supplementary segments (SUPP) are reported.
Bootstrap: moving blocks of 20 batches (noninferiority.block_means), 10 000 resamples, default_rng(0), one-sided 95%
lower bound = 5th percentile. Usage: python analyse.py <root>"""
import math
import os
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import reweight  # noqa: E402
from compute_metrics import metrics, stack  # noqa: E402
from noninferiority import block_means  # noqa: E402

STREAMS = [f"cc_btc_{y}" for y in range(2013, 2018)] + [f"cc_cic_{d}" for d in ("tue", "wed", "thu", "fri")]
SUPP = ["cc_poker_f", "cc_poker_g"]   # supplementary: reported, not part of any hypothesis
SOURCE = lambda s: "bitcoinheist" if s.startswith("cc_btc") else "cicids2017" if s.startswith("cc_cic") else "poker"
FILES = {"fifo": "fifo1000", "ltm": "ltm1000_75", "ddm": "ddm1000", "winens": "winens1000", "arf": "arf", "srp": "srp"}
CONTEXT = ["fifo", "ltm", "ddm", "winens"]
KW = dict(outer="brier", scale=0.5, temper=True)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "results_paper", "confirm_detected")
if os.environ.get("CC_TEST"):   # dry run of this script on existing streams (never on the confirmation outputs)
    STREAMS, SUPP, OUT = os.environ["CC_TEST"].split(","), [], os.environ["CC_TEST_OUT"]
BLOCK, NBOOT = 20, 10_000


def per_batch(root, s):
    """Per-batch accuracy (dict t -> fraction) of every method and the replayed predictions for the metrics."""
    P = f"{root}/P"
    acc, pred = {}, {}
    for name, f, sub in (("mice", "micev1000_500", None), ("mice_cp", "micecp1000_500", None),
                         ("mice_cp_nopool", "micecp1000_500", lambda u: u < 0)):
        c = pickle.load(open(f"{P}/{s}__{f}.pkl", "rb")); col = []
        acc[name] = reweight.simulate2(c, subset=sub, collect=col, **KW)
        pred[name] = stack(col, c["y"], c["B"])
        if name == "mice":
            pred["fifo"] = stack([(st["t"], st["P"][-1000]) for st in c["cache"]], c["y"], c["B"])
            colw = []; reweight.simulate(c, 2.0, 0.5, subset=lambda u: u < 0, collect=colw)
            pred["winens"] = stack(colw, c["y"], c["B"]); y, B = c["y"], c["B"]
        del c
    for name, f in FILES.items():
        a = np.load(f"{P}/{s}__{f}.npz")["acc"]
        acc[name] = {t: float(a[t]) for t in range(1, len(a)) if np.isfinite(a[t])}
    for name, f in (("ddm", "ddm1000"), ("ltm", "ltm1000_75")):
        z = np.load(f"{P}/{s}__{f}__probs.npz")
        pred[name] = (z["P"].astype(float), y[B:B + len(z["P"])])
    keys = sorted(acc["mice_cp"])
    for name, a in acc.items():
        assert sorted(a) == keys, (s, name, len(a), len(keys))   # the same scored batches for every method
    return acc, pred, keys


def lb(x, rng):
    return float(np.percentile(block_means(np.asarray(x), BLOCK, rng, NBOOT), 5))


def main():
    root = sys.argv[1]
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(0)
    A, M, D_cp_mice, LB_fifo, D_cp_fifo = {}, [], {}, {}, {}
    for s in STREAMS + SUPP:
        acc, pred, keys = per_batch(root, s)
        A[s] = {k: float(np.mean([v[t] for t in keys])) for k, v in acc.items()}
        x = lambda k: np.array([acc[k][t] for t in keys])
        if s in STREAMS:   # the hypotheses use the primary segments only
            D_cp_mice[s] = 100 * (x("mice_cp") - x("mice"))
            LB_fifo[s] = lb(100 * (x("mice_cp") - x("fifo")), rng)
            D_cp_fifo[s] = 100 * (x("mice_cp") - x("fifo"))
        for k, v in pred.items():
            M.append(dict(stream=s, method=k, **metrics(*v)))
    a = pd.DataFrame(A).T; a.index.name = "stream"; a["source"] = [SOURCE(s) for s in a.index]
    a["role"] = ["supplementary" if s in SUPP else "primary" for s in a.index]
    a.to_csv(f"{OUT}/acc.csv"); pd.DataFrame(M).to_csv(f"{OUT}/metrics.csv", index=False)
    a_all, a = a, a[a.role == "primary"]
    n = len(a); need = math.ceil(2 * n / 3)
    H = []
    # H1: mean over segments of (mice_cp - mice), each segment resampled by moving blocks, lower bound > -0.2
    boots = np.mean([block_means(D_cp_mice[s], BLOCK, rng, NBOOT) for s in STREAMS], axis=0)
    h1_lb = float(np.percentile(boots, 5))
    H.append(dict(h="H1", rule="mean over segments of mice_cp - mice: one-sided 95% lower bound > -0.2 points",
                  value=f"mean {np.mean([d.mean() for d in D_cp_mice.values()]):+.3f}, lb {h1_lb:+.3f}", met=h1_lb > -0.2))
    # H2: every segment, lower bound of mean(mice_cp - fifo) > -0.3
    H.append(dict(h="H2", rule="every segment: one-sided 95% lower bound of mice_cp - fifo > -0.3 points",
                  value="; ".join(f"{s} {v:+.3f}" for s, v in LB_fifo.items()), met=all(v > -0.3 for v in LB_fifo.values())))
    # H3: every segment, mice_cp >= max(fifo, ddm) - 0.5 points
    d3 = 100 * (a.mice_cp - a[["fifo", "ddm"]].max(axis=1))
    H.append(dict(h="H3", rule="every segment: mice_cp - max(fifo, ddm) >= -0.5 points",
                  value="; ".join(f"{s} {v:+.3f}" for s, v in d3.items()), met=bool((d3 >= -0.5).all())))
    # H4: within each source the mean of mice_cp is above the mean of each context baseline, and mice_cp is above all
    # four on at least ceil(2n/3) segments (strictly)
    src = a.groupby("source")[["mice_cp"] + CONTEXT].mean()
    h4a = bool((src.mice_cp > src[CONTEXT].max(axis=1)).all())
    d4 = 100 * (a.mice_cp - a[CONTEXT].max(axis=1))
    h4b = int((d4 > 0).sum())
    H.append(dict(h="H4", rule=f"per source mean above all four context baselines, and above all four on >= {need} of {n}",
                  value="per source margins " + "; ".join(f"{k} {100 * v:+.3f}" for k, v in (src.mice_cp - src[CONTEXT].max(axis=1)).items())
                  + f"; above on {h4b} of {n}: " + "; ".join(f"{s} {v:+.3f}" for s, v in d4.items()),
                  met=h4a and h4b >= need))
    # H5: mice_cp above its window-only variant on at least ceil(2n/3) segments
    d5 = 100 * (a.mice_cp - a.mice_cp_nopool)
    H.append(dict(h="H5", rule=f"mice_cp above mice_cp_nopool on >= {need} of {n} segments",
                  value=f"{int((d5 > 0).sum())} of {n}: " + "; ".join(f"{s} {v:+.3f}" for s, v in d5.items()),
                  met=bool((d5 > 0).sum() >= need)))
    # descriptive sensitivity (no decision): H1 and H2 bounds with blocks of 50 batches
    r50 = np.random.default_rng(1)
    b50 = np.mean([block_means(D_cp_mice[s], 50, r50, NBOOT) for s in STREAMS], axis=0)
    H.append(dict(h="H1_b50", rule="descriptive: H1 lower bound with blocks of 50 batches",
                  value=f"lb {np.percentile(b50, 5):+.3f}", met=np.nan))
    H.append(dict(h="H2_b50", rule="descriptive: H2 lower bounds with blocks of 50 batches",
                  value="; ".join(f"{s} {np.percentile(block_means(D_cp_fifo[s], 50, r50, NBOOT), 5):+.3f}" for s in STREAMS),
                  met=np.nan))
    h = pd.DataFrame(H); h.to_csv(f"{OUT}/hypotheses.csv", index=False)
    meth = [c for c in a.columns if c not in ("source", "role")]
    summ = pd.DataFrame({"mean_acc_pct": 100 * a[meth].mean(),
                         "worst_vs_fifo_pts": (100 * a[meth].sub(a.fifo, axis=0)).min()})   # primary segments
    for k, g in a_all.groupby("source"):
        summ[f"mean_{k}_pct"] = 100 * g[meth].mean()
    summ.index.name = "method"; summ.to_csv(f"{OUT}/summary.csv")
    pd.set_option("display.width", 250)
    print((100 * a_all[meth]).round(2).to_string()); print(summ.round(3).to_string())
    for r in H:
        print(r["h"], "MET" if r["met"] is True else "NOT MET" if r["met"] is False else "-", "|", r["rule"], "|", r["value"])


if __name__ == "__main__":
    main()
