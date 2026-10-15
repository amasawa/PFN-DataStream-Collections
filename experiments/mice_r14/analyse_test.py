"""Round 14 frozen evaluation (registered in experiments/mice_r14/PLAN.md before any test run). Committed with the
registration; not changed after the runs except for fixes of crashes, recorded as amendments.

Accuracy of a stream: mean over batches 1..T-1 of the per-batch accuracy (%), pool methods replayed with the paper's
two-level rule reweight.simulate2(outer="brier", scale=0.5, temper=True); reset (ddm1000), FIFO (fifo1000) and the
window ensemble (winens1000) from their per-batch accuracies. Differences in points.
Registered criteria (each reported as MET / NOT MET):
  C1 (primary; fresh streams T1: 4 seeds x {30,100} centroids x 3 length regimes x 3 offsets = 72): within each
     length regime (24 streams): mean(MICE-CP - reset) >= +1.0, MICE-CP above reset on >= 18 of 24, and the 95%
     hierarchical-bootstrap lower bound of the regime mean > 0 (resample the 4 seeds within each centroid count, then
     the 3 offsets within each drawn concept draw; 10 000 resamples, seed 0).
  C2 (shifted grid, 8 off_ streams): mean(MICE-CP - MICE) >= +2.0.
  C3 (aligned grid, the 8 streams with 30 or 100 centroids, seeds 20/21): mean(MICE-CP - MICE) >= -0.3.
  C4 (29 real streams): mean(MICE-CP - FIFO) >= -0.1 and mean(MICE-CP - MICE) >= -0.2.
  C5 (resources, T1): MICE-CP uses no more TFM calls per batch and no more stored experts per batch than ArchCP
     (means over the 72 streams) and mean(MICE-CP - ArchCP) >= -0.3.
  P (purity rule, T1): the paper states that MICE-CP's stored contexts satisfy the single-concept premise only if at
     least 90% of the (stored context, segment close) evaluations -- the context that received a segment, right after
     receiving it, over all closes of the 72 streams -- hold >= 95% rows of one concept; otherwise
     the recall theorem is presented as conditional on purity and the measured purity is reported.
Reported without criterion: per-cell means; misaligned schedules (12); archive (k=12) on the existing streams; first
five batches of recurring blocks (synthetic); 95% moving-block bootstrap intervals of the group means (blocks of 10
batches on synthetic, 20 on real streams, 10 000 resamples, seed 0, streams resampled independently; every interval uses its own default_rng(0)); detected cuts,
false cuts; stored experts, TFM calls and seconds per batch (wall time of the runs, not an isolated benchmark).
Usage: python analyse_test.py   (writes ../../MICE/results_paper/r14_*.csv)"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.join(HERE, "..", "..", "MICE", "code")
sys.path.insert(0, CODE)
import reweight  # noqa: E402

RUNS = os.path.expanduser("~/pfn-runs")
TEST, R14 = f"{RUNS}/mice-r14-test", f"{RUNS}/mice-r14-exist"
CTRL = f"{RUNS}/mice-tkde-control-20261009"
MICE = os.path.join(HERE, "..", "..", "MICE")
OUT = f"{MICE}/results_paper"
REAL = {"realD": "results_test", "realC": "results_heldout", "realG": "results_heldout2", "realH": "results_heldout3",
        "realI": "results_heldout4"}
REAL_D = {"elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
          "insects_incremental_reoccurring_balanced"}
GRID8 = [f"grid_c{nc}_b{b}_s{s}" for b in (500, 2000) for nc in (30, 100) for s in (20, 21)]
NBOOT = 10_000


def pool(f):
    c = pickle.load(open(f, "rb"))
    a = reweight.simulate2(c, outer="brier", scale=0.5, temper=True)
    T = len(c["y"]) // c["B"]
    assert sorted(a) == list(range(1, T)), f
    return 100 * np.array([a[t] for t in range(1, T)]), c


def plain(f):
    a = np.load(f)["acc"]
    assert np.isfinite(a[1:]).all(), f
    return 100 * a[1:]


def recurring(concept, B=100, K=3, first=5):
    starts = np.flatnonzero(np.r_[True, concept[1:] != concept[:-1]])
    return sorted({b for r in starts[K:] for b in range(-(-r // B), -(-r // B) + first)})


def segments(f_npz, concept, B=100):
    """Detected cuts (batch index), true changes found within H+1 batches, false cuts, from the run's npz."""
    cuts = np.load(f_npz)["cuts"]
    ch = np.flatnonzero(concept[1:] != concept[:-1]) + 1
    det = [b * B for _, b in cuts]
    found = sum(any(0 <= d - c_ < 4 * B for d in det) for c_ in ch)
    false = sum(not any(0 <= d - c_ < 4 * B for c_ in ch) for d in det)
    return len(ch), found, false


def purity(f, concept, M=1000):
    """Share of rows of the majority concept in the stored context that received each closed segment (last M rows of
    the segments it holds), at every close."""
    out = []
    for _, a, b, u, src in pickle.load(open(f, "rb")):
        idx = np.concatenate([np.arange(x, y) for x, y in src])[-M:]
        out.append(np.bincount(concept[idx]).max() / len(idx))
    return np.array(out)


def hier_lb(d):
    """95% interval of the mean of d (per-stream differences indexed by t_<regime>_c<nc>_s<seed>_o<k>) resampling seeds
    within each centroid count, then offsets within each drawn seed."""
    keys = [s.rsplit("_", 3)[1:] for s in d.index]       # [c<nc>, s<seed>, o<k>]
    tab = {}
    for (nc, sd, o), v in zip(keys, d.values):
        tab.setdefault(nc, {}).setdefault(sd, []).append(v)
    rng, means = np.random.default_rng(0), np.zeros(NBOOT)
    for i in range(NBOOT):
        vals = []
        for nc, seeds in tab.items():
            names = list(seeds)
            for sd in rng.choice(names, len(names)):
                x = np.array(seeds[sd])
                vals.extend(rng.choice(x, len(x)))
        means[i] = np.mean(vals)
    return np.percentile(means, [2.5, 97.5])


def resources(c, npz):
    n = [sum(u > 0 for u in st["P"]) for st in c["cache"]]         # stored experts (windows have keys < 0)
    return np.mean(n), float(np.load(npz)["calls"]) / len(c["cache"])


def boot_ci(series_list, block):
    """95% percentile interval of the mean over streams of per-stream mean differences; each stream resampled
    independently by a moving-block bootstrap of its batch sequence; each interval uses its own default_rng(0)."""
    rng, means = np.random.default_rng(0), np.zeros(NBOOT)
    for x in series_list:
        n = len(x); b = block if n >= 2 * block else max(1, n // 2); k = int(np.ceil(n / b))
        st = rng.integers(0, n - b + 1, size=(NBOOT, k))
        idx = (st[:, :, None] + np.arange(b)[None, None, :]).reshape(NBOOT, -1)[:, :n]
        means += x[idx].mean(1)
    means /= len(series_list)
    return np.percentile(means, [2.5, 97.5])


def synthetic(names, d_new, d_old, ddir):
    """Rows for synthetic streams: d_new holds the round-14 runs (micecp, archcp [, micev, arch, ddm, fifo, winens]),
    d_old the earlier runs of the original method and baselines (None: all in d_new)."""
    rows, series = [], {}
    for s in names:
        concept = np.load(f"{ddir}/{s}.npz")["concept"]
        old = d_old(s) if d_old else d_new
        acc, r = {}, dict(stream=s)
        acc["cp"], ccp = pool(f"{d_new}/{s}__micecp1000_500.pkl")
        acc["archcp"], _ = pool(f"{d_new}/{s}__archcp1000_500.pkl")
        acc["mice"], cm = pool(f"{old}/{s}__micev1000_500.pkl")
        aold = old if os.path.exists(f"{old}/{s}__arch1000_500.pkl") else f"{CTRL}/arch"
        if os.path.exists(f"{aold}/{s}__arch1000_500.pkl"):
            acc["arch"], _ = pool(f"{aold}/{s}__arch1000_500.pkl")
        for k, m in (("reset", "ddm1000"), ("fifo", "fifo1000"), ("winens", "winens1000")):
            if os.path.exists(f"{old}/{s}__{m}.npz"):
                acc[k] = plain(f"{old}/{s}__{m}.npz")
        T = len(acc["cp"])
        assert all(len(v) == T for v in acc.values()), s
        rec = [t - 1 for t in recurring(concept) if 1 <= t <= T]
        for k, v in acc.items():
            r[k], r[k + "_rec"] = v.mean(), v[rec].mean()
        r["changes"], r["found"], r["false"] = segments(f"{d_new}/{s}__micecp1000_500.npz", concept)
        for k, m in (("cp", "micecp1000_500"), ("archcp", "archcp1000_500")):
            pur = purity(f"{d_new}/{s}__{m}.closes.pkl", concept)
            r[f"{k}_purity_mean"], r[f"{k}_pure95_share"], r[f"{k}_closes"] = pur.mean(), (pur >= 0.95).mean(), len(pur)
        r["archcp_experts"], r["archcp_calls"] = resources(pickle.load(open(f"{d_new}/{s}__archcp1000_500.pkl", "rb")),
                                                           f"{d_new}/{s}__archcp1000_500.npz")
        r["cp_s"] = float(np.load(f"{d_new}/{s}__micecp1000_500.npz")["wt"][1:].mean())
        r["cp_experts"], r["cp_calls"] = resources(ccp, f"{d_new}/{s}__micecp1000_500.npz")
        r["mice_experts"], r["mice_calls"] = resources(cm, f"{old}/{s}__micev1000_500.npz")
        rows.append(r)
        series[s] = acc
    return pd.DataFrame(rows).set_index("stream"), series


def report(name, d, series, block, pairs):
    out = []
    for a, b in pairs:
        if a not in d or b not in d:
            continue
        x = d[a] - d[b]
        lo, hi = boot_ci([series[s][a] - series[s][b] for s in d.index], block)
        out.append(dict(group=name, diff=f"{a}-{b}", streams=len(x), mean=x.mean(), lo95=lo, hi95=hi,
                        above=int((x > 0).sum()), min=x.min(), max=x.max()))
    return out


def main():
    t1 = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{TEST}/data/t_*.npz"))
    assert len(t1) == 72
    d1, s1 = synthetic(t1, f"{TEST}/P", None, f"{TEST}/data")
    off = [g.replace("grid_", "off_") for g in GRID8]
    d2, s2 = synthetic(off, f"{R14}/P", lambda s: f"{CTRL}/off", f"{CTRL}/data")
    grid = sorted(os.path.basename(f).split("__")[0] for f in glob.glob(f"{MICE}/results_grid_test3/grid_*__micev1000_500.pkl"))
    d3, s3 = synthetic(grid, f"{R14}/P", lambda s: f"{MICE}/results_grid_test3", f"{CTRL}/data")
    mis = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{CTRL}/data/mis_*.npz"))
    d5, s5 = synthetic(mis, f"{R14}/P", lambda s: f"{CTRL}/mis", f"{CTRL}/data")
    real_rows, s4 = [], {}
    for grp, sub in REAL.items():
        for f in sorted(glob.glob(f"{MICE}/{sub}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            if grp == "realD" and s not in REAL_D:
                continue
            acc = {}
            acc["mice"], _ = pool(f)
            acc["cp"], ccp = pool(f"{R14}/P/{s}__micecp1000_500.pkl")
            acc["fifo"] = plain(f"{MICE}/{sub}/{s}__fifo1000.npz")
            if os.path.exists(f"{R14}/P/{s}__archcp1000_500.pkl"):
                acc["archcp"], _ = pool(f"{R14}/P/{s}__archcp1000_500.pkl")
            assert all(len(v) == len(acc["cp"]) for v in acc.values()), s
            r = dict(stream=s, group=grp, **{k: v.mean() for k, v in acc.items()})
            r["cuts"] = len(np.load(f"{R14}/P/{s}__micecp1000_500.npz")["cuts"])
            r["cp_experts"], r["cp_calls"] = resources(ccp, f"{R14}/P/{s}__micecp1000_500.npz")
            real_rows.append(r)
            s4[s] = acc
    d4 = pd.DataFrame(real_rows).set_index("stream")
    assert len(d4) == 29, len(d4)
    pairs = [("cp", "reset"), ("mice", "reset"), ("cp", "mice"), ("cp", "archcp"), ("cp", "arch"), ("archcp", "reset"),
             ("cp", "fifo"), ("cp", "winens")]
    assert set(GRID8) <= set(d3.index) and len(d3) == 12 and len(d2) == 8 and len(d5) == 12
    g8 = d3.loc[GRID8]
    summ = (report("T1_fresh", d1, s1, 10, pairs) + report("shifted", d2, s2, 10, pairs)
            + report("aligned8", g8, s3, 10, pairs) + report("misaligned", d5, s5, 10, pairs)
            + report("real29", d4, s4, 20, [("cp", "fifo"), ("cp", "mice"), ("mice", "fifo"), ("cp", "archcp")]))
    summ = pd.DataFrame(summ)
    for k, d in (("t1", d1), ("shifted", d2), ("aligned", d3), ("misaligned", d5), ("real", d4)):
        d.to_csv(f"{OUT}/r14_{k}_streams.csv")
    summ.to_csv(f"{OUT}/r14_groups.csv", index=False)
    pd.set_option("display.width", 220)
    print(summ.round(3).to_string(index=False))
    d1["cell"] = ["_".join(s.split("_")[1:3]) for s in d1.index]
    print((d1.assign(cp_reset=d1.cp - d1.reset, mice_reset=d1.mice - d1.reset, cp_mice=d1.cp - d1.mice)
           .groupby("cell")[["cp_reset", "mice_reset", "cp_mice"]].mean().round(2)))
    assert len(d1) == 72
    c1 = True
    for reg in ("b500", "b2000", "bvar"):
        x = (d1.cp - d1.reset)[[s.split("_")[1] == reg for s in d1.index]]
        assert len(x) == 24, reg
        lo, hi = hier_lb(x)
        ok = x.mean() >= 1.0 and (x > 0).sum() >= 18 and lo > 0
        c1 &= ok
        print(f"C1 {reg}: mean(CP-reset) {x.mean():+.3f} (>= +1.0), above {(x > 0).sum()}/{len(x)} (>= 18), "
              f"hierarchical 95% [{lo:+.3f}, {hi:+.3f}] (lower > 0): {'met' if ok else 'not met'}")
        lo2, hi2 = hier_lb((d1.mice - d1.reset)[x.index])
        print(f"   original MICE - reset {(d1.mice - d1.reset)[x.index].mean():+.3f} [{lo2:+.3f}, {hi2:+.3f}]")
    c5 = (d1.cp_calls.mean() <= d1.archcp_calls.mean() and d1.cp_experts.mean() <= d1.archcp_experts.mean()
          and (d1.cp - d1.archcp).mean() >= -0.3)
    pshare = np.concatenate([[d1.cp_pure95_share[s]] * int(d1.cp_closes[s]) for s in d1.index]).mean()
    c2 = (d2.cp - d2.mice).mean() >= 2.0
    c3 = (g8.cp - g8.mice).mean() >= -0.3
    c4 = (d4.cp - d4.fifo).mean() >= -0.1 and (d4.cp - d4.mice).mean() >= -0.2
    print(f"C1 (primary, all three regimes): {'MET' if c1 else 'NOT MET'}")
    print(f"C5 calls CP {d1.cp_calls.mean():.2f} vs ArchCP {d1.archcp_calls.mean():.2f}; experts {d1.cp_experts.mean():.2f} vs "
          f"{d1.archcp_experts.mean():.2f}; mean(CP-ArchCP) {(d1.cp - d1.archcp).mean():+.3f} (>= -0.3): {'MET' if c5 else 'NOT MET'}")
    print(f"P purity: share of (context, close) evaluations >= 95% one concept {pshare:.3f} (>= 0.90 -> premise holds; else conditional); "
          f"mean purity {d1.cp_purity_mean.mean():.3f}")
    print(f"C2 shifted mean(CP-MICE) {(d2.cp - d2.mice).mean():+.3f} (>= +2.0): {'MET' if c2 else 'NOT MET'}")
    print(f"C3 aligned8 mean(CP-MICE) {(g8.cp - g8.mice).mean():+.3f} (>= -0.3): {'MET' if c3 else 'NOT MET'}")
    print(f"C4 real29 mean(CP-FIFO) {(d4.cp - d4.fifo).mean():+.3f} (>= -0.1), mean(CP-MICE) {(d4.cp - d4.mice).mean():+.3f} "
          f"(>= -0.2): {'MET' if c4 else 'NOT MET'}")
    print("T1 detection: changes", d1.changes.sum(), "found", d1.found.sum(), "false", d1.false.sum())


if __name__ == "__main__":
    main()
