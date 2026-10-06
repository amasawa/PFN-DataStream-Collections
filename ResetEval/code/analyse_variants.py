"""Verdicts of the unattended stages registered 2026-10-07 06:22 (logs/EXPERIMENT_LOG.md).
hsens (TabPFN seed 0, M 1000; 7 variants v = +hedge@e<eta>g<gamma>, eta in {0.5, 1, 4, 8} at gamma 0.5, gamma in
{0.25, 0.75, 0.9} at eta 2), per variant:
  HS1 detector-averaged source-weighted mean d on real >= -0.2
  HS2 detector-averaged worst real source: v - full >= 10
  HS3 detector-averaged family-weighted mean d on synthetic >= half of full reset's
trained <ht|nb> (river learner, policies none, <det>, <det>+hedge), against TabPFN seed 0 on the same streams:
  TR1 detector-averaged source-weighted full-reset d on real: learner - TabPFN >= 2 points
  TR2 detector-averaged worst real source of full reset: learner - TabPFN >= 10 points
  TR3 real: share of non-zero single resets that are net losses (next 10 batches against none) < 70%
d = acc(policy) - acc(none) in points, per stream; only streams with every policy present.
Usage: python analyse_variants.py hsens | trained ht|nb -> ../results/<stage>_summary.csv, printed verdicts"""
import os
import sys

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, POLS, REAL, RES, SYN
from cluster_tests import source

NEW = ["gas", "occupancy", "room", "bank", "kdd", "eeg", "news", "home", "wall", "chest"]
HSENS = [f"+hedge@e{e}g{g}" for e, g in [(0.5, 0.5), (1, 0.5), (4, 0.5), (8, 0.5), (2, 0.25), (2, 0.75), (2, 0.9)]]


def collect(d, pols, base="none"):
    rows, rr = [], []
    for grp, streams in (("real", REAL + NEW), ("syn", SYN)):
        done = [s for s in streams if all(os.path.exists(f"{d}/{s}__{p}.npz") for p in pols + [base])]
        if len(done) < len(streams):
            print(f"PARTIAL {grp} in {os.path.basename(d)}: {len(done)}/{len(streams)}; missing {sorted(set(streams) - set(done))}")
        for s in done:
            a0 = np.load(f"{d}/{s}__{base}.npz")["acc"]
            for p in pols:
                z = np.load(f"{d}/{s}__{p}.npz"); a, r = z["acc"], z["resets"]
                rows.append(dict(group=grp, stream=s, src=source(s), pol=p, d=100 * (np.nanmean(a) - np.nanmean(a0))))
                if p in DETS:
                    for i, t in enumerate(r):
                        end = min(t + 10, r[i + 1] if i + 1 < len(r) else len(a), len(a))
                        rr.append(dict(group=grp, stream=s, det=p, gain=100 * np.nansum(a[t:end] - a0[t:end])))
    return pd.DataFrame(rows), pd.DataFrame(rr)


def stats(S, v, streams=None):
    """detector-averaged (source-weighted real mean, worst real source, family-weighted synthetic mean) of variant v."""
    x = S[S.pol.isin([k + v for k in DETS])]
    if streams is not None:
        x = x[x.stream.isin(streams)]
    src = x[x.group == "real"].groupby(["pol", "src"]).d.mean().unstack()
    syn = x[x.group == "syn"].groupby(["pol", "src"]).d.mean().unstack()
    return src.mean(1).mean(), src.min(1).mean(), syn.mean(1).mean() if len(syn) else np.nan


def hsens():
    d = f"{RES}/tabpfn_M1000"
    S, _ = collect(d, [k + v for k in DETS for v in ["", "+hedge"] + HSENS])
    S.to_csv(f"{RES}/hsens_summary.csv", index=False)
    full = stats(S, ""); rows = []
    for v in ["+hedge"] + HSENS:
        m, w, sy = stats(S, v)
        ok = (m >= -0.2, w - full[1] >= 10, sy >= 0.5 * full[2])
        rows.append(dict(variant=v, real_mean=m, worst_src=w, syn_mean=sy, HS1=ok[0], HS2=ok[1], HS3=ok[2]))
    T = pd.DataFrame(rows).set_index("variant")
    print(f"full reset: real mean {full[0]:.2f}, worst source {full[1]:.2f}, synthetic {full[2]:.2f}")
    print(T.round(2).to_string())
    n = int(T.loc[HSENS, ["HS1", "HS2", "HS3"]].all(1).sum())
    print(f"HS variants passing HS1-HS3: {n}/7 -> {'robust' if n == 7 else 'not robust'}; "
          f"HS1 {int(T.loc[HSENS].HS1.sum())}/7, HS2 {int(T.loc[HSENS].HS2.sum())}/7, HS3 {int(T.loc[HSENS].HS3.sum())}/7")


def trained(model):
    pols = [k + v for k in DETS for v in ("", "+hedge")]
    S, R = collect(f"{RES}/trained_{model}", pols)
    S.to_csv(f"{RES}/trained_{model}_summary.csv", index=False)
    P, PR = collect(f"{RES}/tabpfn_M1000", pols)
    common = sorted(set(S.stream) & set(P.stream))
    a, b = stats(S, "", common), stats(P, "", common)
    ah, bh = stats(S, "+hedge", common), stats(P, "+hedge", common)
    print(f"{len(common)} common streams; detector-averaged (real mean, worst real source, synthetic mean):")
    print(f"  full reset: {model} {np.round(a, 2)}, TabPFN {np.round(b, 2)}")
    print(f"  +hedge:     {model} {np.round(ah, 2)}, TabPFN {np.round(bh, 2)}")
    per = S[(S.group == "real") & S.stream.isin(common)].groupby(["pol", "src"]).d.mean().unstack().mean(1)
    print("  per-policy source-weighted real d:", per.round(2).to_dict())
    rz = R[(R.group == "real") & (R.gain != 0) & R.stream.isin(common)]; loss = (rz.gain < 0).mean()
    pz = PR[(PR.group == "real") & (PR.gain != 0) & PR.stream.isin(common)]
    print(f"TR1 full-reset real mean: {model} - TabPFN = {a[0] - b[0]:.2f} (need >= 2) -> {'holds' if a[0] - b[0] >= 2 else 'fails'}")
    print(f"TR2 worst real source: {model} - TabPFN = {a[1] - b[1]:.2f} (need >= 10) -> {'holds' if a[1] - b[1] >= 10 else 'fails'}")
    print(f"TR3 real: {100 * loss:.1f}% of {len(rz)} non-zero resets are losses for {model} (TabPFN {100 * (pz.gain < 0).mean():.1f}% "
          f"of {len(pz)}; need < 70%) -> {'holds' if loss < 0.7 else 'fails'}")


if __name__ == "__main__":
    hsens() if sys.argv[1] == "hsens" else trained(sys.argv[2])
