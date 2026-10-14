"""Round-13 analysis (registered in PLAN.md, "Round 13"). Stages, in this order:
  a1   timings and memory on the three real prefixes; fixes k* by rule B and writes <bench>/kstar.json (no accuracy).
  a1acc  prefix accuracies (only after kstar.json exists).
  a2   timings, memory and accuracy on the four grid streams; whether each control at k* meets MICE's budget there.
  c    accuracy at benchmark-calibrated capacity on the three stream groups, Delta = MICE - control, bootstrap.
Usage: python analyse_pools.py a1|a1acc|a2|c   (writes ../../MICE/results_paper/r13_*.csv)"""
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "MICE/code"))
import reweight
from noninferiority import block_means
from pool_cap_run import GRID, REAL, SHIFT

BENCH = Path.home() / "pfn-runs/mice-r13-bench"
ACC = Path.home() / "pfn-runs/mice-r13-acc"
CTRL = Path.home() / "pfn-runs/mice-tkde-control-20261009"
OUT = REPO / "MICE/results_paper"
NB = 10_000


def replay(f):
    c = pickle.load(open(f, "rb"))
    t0 = time.perf_counter()
    a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    el = time.perf_counter() - t0
    t = np.array(sorted(a))
    return t, 100 * np.array([a[k] for k in t]), el / len(c["cache"])


def runs(stage):
    recs = [json.loads(l) for l in open(BENCH / f"{stage}.jsonl")]
    ok = {(r["rep"], r["policy"], r["kmax"], r["stream"]): r for r in recs if r.get("ok")}
    bad = [r for r in recs if r.get("infeasible") or r.get("failed_exhausted")]
    return ok, bad


def cost_rows(stage):
    ok, bad = runs(stage)
    rows = []
    for (rep, pol, k, s), r in ok.items():
        d = BENCH / stage / f"rep{rep}" / ("mice" if k == 0 else f"k{k}")
        z = np.load(d / f"{s}__{pol}.npz")
        wt = z["wt"][1:]
        tt = np.arange(1, len(z["wt"]))
        closing = (tt * 100) % 500 == 0
        _, _, rep_s = replay(d / f"{s}__{pol}.pkl")
        occ = np.array(json.load(open(d / f"{s}__{pol}.occ.json")))
        late = tt >= 61
        rows.append(dict(rep=rep, policy="mice" if k == 0 else f"{pol[:4]}{k}", stream=s,
                         mean_s=wt.mean() + rep_s, replay_s=rep_s, median_s=np.median(wt), p95_s=np.percentile(wt, 95),
                         max_s=wt.max(), closing_s=wt[closing].mean(), nonclosing_s=wt[~closing].mean(),
                         mean_s_61=wt[late].mean() + rep_s, calls=float(z["calls"]) / len(wt),
                         experts=occ[:, 0].mean(), rows_k=occ[:, 1].mean() / 1000,
                         peak_alloc_gb=r["peak_alloc_mib"] / 1024, peak_reserved_gb=r["peak_reserved_mib"] / 1024,
                         peak_rss_gb=r["peak_rss_mib"] / 1024, gpu_after=str(r.get("gpu_after"))))
    return pd.DataFrame(rows), bad


def summarise(d):
    per = d.groupby(["policy", "stream"]).mean(numeric_only=True).reset_index()
    spread = d.groupby(["policy", "stream"]).mean_s.std().groupby("policy").mean().rename("rep_sd_s")
    agg = per.groupby("policy").mean(numeric_only=True).drop(columns="rep").join(spread)
    return per, agg


def a1():
    d, bad = cost_rows("a1")
    per, agg = summarise(d)
    pd.set_option("display.width", 250)
    print(agg.round(3).to_string())
    print("infeasible / failed:", bad)
    mice = agg.loc["mice", "mean_s"]
    ks = {}
    for m in ("arch", "snap"):
        feas = [k for k in (2, 4) if f"{m}{k}" in agg.index and per[per.policy == f"{m}{k}"].stream.nunique() == 3
                and not any(b["policy"].startswith(m) and b["kmax"] == k for b in bad)]
        under = [k for k in feas if agg.loc[f"{m}{k}", "mean_s"] <= mice]
        ks[m] = max(under) if under else 2
        ks[f"{m}_status"] = "within MICE's budget" if under else "over-budget fallback"
    ks["mice_mean_s"] = mice
    ks.update({f"{p}_mean_s": agg.loc[p, "mean_s"] for p in agg.index if p != "mice"})
    print("k* (timings only):", ks)
    assert not (BENCH / "kstar.json").exists(), "k* already fixed"
    json.dump(ks, open(BENCH / "kstar.json", "w"), indent=1)
    d.to_csv(OUT / "r13_a1_runs.csv", index=False); agg.to_csv(OUT / "r13_a1_policy.csv")


def accuracy_of(stage, streams):
    ok, _ = runs(stage)
    rows = []
    for (rep, pol, k, s), r in ok.items():
        d = BENCH / stage / f"rep{rep}" / ("mice" if k == 0 else f"k{k}")
        rows.append(dict(rep=rep, policy="mice" if k == 0 else f"{pol[:4]}{k}", stream=s,
                         acc=replay(d / f"{s}__{pol}.pkl")[1].mean()))
    return pd.DataFrame(rows).groupby(["policy", "stream"]).acc.mean().unstack()


def a1acc():
    assert (BENCH / "kstar.json").exists(), "fix k* first"
    t = accuracy_of("a1", None)
    print(t.round(2).to_string())
    t.to_csv(OUT / "r13_a1_accuracy.csv")


def a2():
    ks = json.load(open(BENCH / "kstar.json"))
    d, bad = cost_rows("a2")
    per, agg = summarise(d)
    pd.set_option("display.width", 250)
    print(per.round(3).to_string(index=False))
    print("infeasible / failed:", bad)
    acc = accuracy_of("a2", None)
    print(acc.round(2).to_string())
    m = per[per.policy == "mice"].set_index("stream").mean_s
    for c in (f"arch{ks['arch']}", f"snap{ks['snap']}"):
        x = per[per.policy == c].set_index("stream").mean_s
        print(f"{c} meets MICE's amortised mean s/batch on:", {s: bool(x[s] <= m[s]) for s in m.index})
    d.to_csv(OUT / "r13_a2_runs.csv", index=False); per.to_csv(OUT / "r13_a2_stream.csv", index=False)
    acc.to_csv(OUT / "r13_a2_accuracy.csv")


def mice_pkl(s):
    if s.startswith("grid_"):
        return REPO / "MICE/results_grid_test3" / f"{s}__micev1000_500.pkl"
    if s.startswith("off_"):
        return CTRL / "off" / f"{s}__micev1000_500.pkl"
    d = {"h4": "results_heldout4", "h2": "results_heldout2"}.get(s[:2], "results_test")
    return REPO / "MICE" / d / f"{s}__micev1000_500.pkl"


def c(k=None):
    """k=None: registered analysis at k* (r13_c_*); k=4: the supplementary capacity (r13_c4_*, same statistics)."""
    ks = json.load(open(BENCH / "kstar.json")) if k is None else dict(arch=k, snap=k)
    rng = np.random.default_rng(0)
    rows, boots = [], {}
    for grp, streams, blk in (("aligned", GRID, 10), ("shifted", SHIFT, 10), ("real", REAL, 20)):
        for s in streams:
            t, m, _ = replay(mice_pkl(s))
            r = dict(group=grp, stream=s, batches=len(t), mice=m.mean())
            for name in ("arch", "snap"):
                tc, x, _ = replay(ACC / f"k{ks[name]}" / f"{s}__{name}1000_500.pkl")
                assert (tc == t).all(), (s, name)
                dd = m - x
                bm = block_means(dd, blk, rng)
                boots[(s, name)] = bm
                r.update({name: x.mean(), f"d_{name}": dd.mean(), f"lo_{name}": np.percentile(bm, 2.5),
                          f"hi_{name}": np.percentile(bm, 97.5), f"lb95_{name}": np.percentile(bm, 5)})
                f12 = CTRL / ("off" if s.startswith("off_") else name) / f"{s}__{name}1000_500.pkl"
                if f12.exists():
                    r[f"d_{name}12"] = (m - replay(f12)[1]).mean()
            rows.append(r)
    d = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(d.round(3).to_string(index=False))
    out = []
    for grp, g in d.groupby("group", sort=False):
        for name in ("arch", "snap"):
            agg = np.mean([boots[(s, name)] for s in g.stream], axis=0)
            mean = g[f"d_{name}"].mean()
            out.append(dict(group=grp, control=f"{name}{ks[name]}", streams=len(g), mean_delta=mean,
                            lo95=np.percentile(agg, 2.5), hi95=np.percentile(agg, 97.5),
                            positive=int((g[f"d_{name}"] > 0).sum()), report_rule=mean <= 0.1))
    o = pd.DataFrame(out)
    print(o.round(3).to_string(index=False))
    for r in o.itertuples():
        if r.report_rule:
            print(f"REPORTING RULE E: {r.control} on the {r.group} group is within +0.1 of MICE or better "
                  f"(mean Delta {r.mean_delta:+.3f}) -> abstract and conclusion must say so")
    tag = "r13_c" if k is None else f"r13_c{k}"
    d.to_csv(OUT / f"{tag}_streams.csv", index=False); o.to_csv(OUT / f"{tag}_groups.csv", index=False)


if __name__ == "__main__":
    dict(a1=a1, a1acc=a1acc, a2=a2, c=c, c4=lambda: c(4))[sys.argv[1]]()
