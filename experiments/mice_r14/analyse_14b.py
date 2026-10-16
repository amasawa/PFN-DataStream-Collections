"""Round-14.b analysis (registered in PLAN_14B.md). Stages, in this order:
  a1     timings and memory on the three real prefixes; fixes the snapshot k* by rule B and writes <bench>/kstar.json
         (no accuracy is read).
  a1acc  prefix accuracies (only after kstar.json exists).
  a2     timings, memory and accuracy on the four grid streams.
  c      accuracy of MICE (detected segments) against the snapshot pool at kmax 2, 4 and 12 on the 72 confirmation
         streams, the 8 shifted and the 12 misaligned grid streams; Delta = MICE - snapshot. Primary: k* (kstar.json)
         and kmax 12; the other candidate is a sensitivity row.
The timing code is that of experiments/mice_tkde_control/analyse_pools.py (round 13), with the bench root and policy
labels changed. Usage: python analyse_14b.py a1|a1acc|a2|c   (writes ../../MICE/results_paper/r14b_*.csv)"""
import glob
import json
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from analyse_test import CTRL, OUT, R14, RUNS, boot_ci, hier_lb, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "MICE/code"))
import reweight  # noqa: E402

BENCH = Path(RUNS) / "mice-r14b-bench"
ACC = f"{RUNS}/mice-r14b-acc"
CONF = f"{RUNS}/mice-r14-confirm"


def label(pol, k):
    return "mice" if k == 0 else f"{pol.split('1000')[0]}{k}"


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
        _, _, rep_s = replay(d / f"{s}__{pol}.pkl")
        occ = np.array(json.load(open(d / f"{s}__{pol}.occ.json")))
        late = tt >= 61
        rows.append(dict(rep=rep, policy=label(pol, k), stream=s,
                         mean_s=wt.mean() + rep_s, replay_s=rep_s, median_s=np.median(wt), p95_s=np.percentile(wt, 95),
                         max_s=wt.max(), mean_s_61=wt[late].mean() + rep_s, calls=float(z["calls"]) / len(wt),
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
    mice = per[per.policy == "mice"].set_index("stream").mean_s
    feas = []
    for k in (2, 4):
        x = per[per.policy == f"snap{k}"].set_index("stream").mean_s
        if len(x) == 3 and not any(b["policy"].startswith("snap") and b["kmax"] == k for b in bad):
            feas.append((k, bool((x <= mice[x.index]).all())))
    under = [k for k, ok in feas if ok]
    ks = dict(snap=max(under) if under else 2, snap_status="within MICE's budget on all three prefixes" if under
              else "over-budget fallback", mice_mean_s=agg.loc["mice", "mean_s"])
    ks.update({f"{p}_mean_s": agg.loc[p, "mean_s"] for p in agg.index if p != "mice"})
    print("snapshot k* (timings only):", ks)
    assert not (BENCH / "kstar.json").exists(), "k* already fixed"
    json.dump(ks, open(BENCH / "kstar.json", "w"), indent=1)
    d.to_csv(OUT / "r14b_a1_runs.csv", index=False)
    agg.to_csv(OUT / "r14b_a1_policy.csv")
    per.to_csv(OUT / "r14b_a1_stream.csv", index=False)


def accuracy_of(stage):
    ok, _ = runs(stage)
    rows = []
    for (rep, pol, k, s), r in ok.items():
        d = BENCH / stage / f"rep{rep}" / ("mice" if k == 0 else f"k{k}")
        rows.append(dict(rep=rep, policy=label(pol, k), stream=s, acc=replay(d / f"{s}__{pol}.pkl")[1].mean()))
    return pd.DataFrame(rows).groupby(["policy", "stream"]).acc.mean().unstack()


def a1acc():
    assert (BENCH / "kstar.json").exists(), "fix k* first"
    t = accuracy_of("a1")
    print(t.round(2).to_string())
    t.to_csv(OUT / "r14b_a1_accuracy.csv")


def a2():
    ks = json.load(open(BENCH / "kstar.json"))
    d, bad = cost_rows("a2")
    per, agg = summarise(d)
    pd.set_option("display.width", 250)
    print(per.round(3).to_string(index=False))
    print("infeasible / failed:", bad)
    acc = accuracy_of("a2")
    print(acc.round(2).to_string())
    m = per[per.policy == "mice"].set_index("stream").mean_s
    x = per[per.policy == f"snap{ks['snap']}"].set_index("stream").mean_s
    print(f"snap{ks['snap']} meets MICE's amortised mean s/batch on:", {s: bool(x[s] <= m[s]) for s in m.index})
    d.to_csv(OUT / "r14b_a2_runs.csv", index=False)
    per.to_csv(OUT / "r14b_a2_stream.csv", index=False)
    acc.to_csv(OUT / "r14b_a2_accuracy.csv")


def c():
    ks = json.load(open(BENCH / "kstar.json"))
    kstar = int(ks["snap"])
    conf = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{CONF}/data/c_*.npz"))
    off = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{CTRL}/data/off_*.npz"))
    mis = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{CTRL}/data/mis_*.npz"))
    assert (len(conf), len(off), len(mis)) == (72, 8, 12), (len(conf), len(off), len(mis))
    rows, series = [], {}
    for grp, names, mdir in (("confirm", conf, f"{CONF}/P"), ("shifted", off, f"{R14}/P"), ("misaligned", mis, f"{R14}/P")):
        for s in names:
            acc = {"cp": pool(f"{mdir}/{s}__micecp1000_500.pkl")[0]}
            for k in (2, 4, 12):
                acc[f"snap{k}"] = pool(f"{ACC}/P_k{k}/{s}__snap1000_500.pkl")[0]
            T = len(acc["cp"])
            assert all(len(v) == T for v in acc.values()), s
            r = dict(group=grp, stream=s, **{k: v.mean() for k, v in acc.items()})
            rows.append(r)
            series[s] = acc
    d = pd.DataFrame(rows).set_index("stream")
    d.to_csv(OUT / "r14b_c_streams.csv")
    out = []
    for k in (2, 4, 12):
        sk = f"snap{k}"
        for grp in ("confirm", "shifted", "misaligned"):
            x = d[d.group == grp]
            dx = x.cp - x[sk]
            if grp == "confirm":
                parts = [("all", dx)] + [(reg, dx[[s.split("_")[1] == reg for s in dx.index]])
                                         for reg in ("b500", "b2000", "bvar")]
                for name, v in parts:
                    lo, hi = hier_lb(v)
                    out.append(dict(control=sk, group=f"confirm_{name}", streams=len(v), mean=v.mean(), lo95=lo,
                                    hi95=hi, above=int((v > 0).sum()), min=v.min(), max=v.max(),
                                    interval="hierarchical bootstrap"))
            else:
                lo, hi = boot_ci([series[s]["cp"] - series[s][sk] for s in x.index], 10)
                out.append(dict(control=sk, group=grp, streams=len(dx), mean=dx.mean(), lo95=lo, hi95=hi,
                                above=int((dx > 0).sum()), min=dx.min(), max=dx.max(),
                                interval="moving-block bootstrap, blocks of 10"))
    g = pd.DataFrame(out)
    g.to_csv(OUT / "r14b_c_groups.csv", index=False)
    pd.set_option("display.width", 250)
    print(g.round(3).to_string(index=False))
    flag_reg = g[(g.control == f"snap{kstar}") & (g.mean <= 0.1)]
    print(f"rule E (snapshot k*={kstar}, mean Delta <= +0.1): groups {list(flag_reg.group)}"
          f"{' -> state in abstract and conclusion' if len(flag_reg) else ' (none)'}")
    hb = g[(g.control == "snap12") & (g.mean < 0)]
    print("snapshot kmax 12 more accurate than MICE (report 'at higher budget' with the s/batch ratio):", list(hb.group))


if __name__ == "__main__":
    {"a1": a1, "a1acc": a1acc, "a2": a2, "c": c}[sys.argv[1]]()
