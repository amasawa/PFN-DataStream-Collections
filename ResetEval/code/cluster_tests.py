"""Source-clustered tests for stage 1 (segments cut from the same data set are not independent samples).

Clusters. Real: covertype, poker, airlines, insects (all INSECTS variants and segments; one sensor study), elec2,
phishing, rialto, spam, weather -> 9 sources. Synthetic: the generator family (agrawal, hyperplane, rbf, sea, sine,
stagger, grid) -> 7 sources. A policy's effect in a source is the mean over its streams of d = acc(policy) - acc(none);
sources are weighted equally.
Tests per policy: Wilcoxon signed-rank over source means (two-sided; with 9 sources the smallest attainable p is 0.0039,
with 7 sources 0.016), sign count, and a 95% cluster-bootstrap interval of the source-weighted mean (resampling sources,
10^4 draws, seed 0). Holm correction over the 8 detectors within each (group, variant). Sensitivity: the same on the real
sources without covertype and poker.
Input ../results/stage1_summary.csv (analyse_stage1.py). Output ../results/stage1_cluster_tests.csv, printed tables.
Usage: python cluster_tests.py"""
import os

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
DETS = ["ddm", "eddm", "fhddm", "hddma", "hddmw", "adwin", "ph", "kswin"]


def source(s):
    for k in ("covertype", "poker", "airlines", "insects", "elec2", "phishing", "rialto", "spam", "weather"):
        if k in s:
            return k
    return s.split("_")[0]                                            # synthetic: generator family (grid_... -> grid)


def holm(p):
    p = np.asarray(p, float); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0.0
    for i, j in enumerate(o):
        run = max(run, (m - i) * p[j]); adj[j] = min(1.0, run)
    return adj


def boot(x, rng, n=10000):
    x = np.asarray(x); m = rng.choice(x, (n, len(x))).mean(1)
    return np.percentile(m, [2.5, 97.5])


def tests(S, group, pols, drop=()):
    x = S[(S.group == group) & ~S.src.isin(drop)]
    rows = []
    rng = np.random.default_rng(0)
    for p in pols:
        m = x[x.pol == p].groupby("src").d_acc.mean()
        lo, hi = boot(m.values, rng)
        rows.append(dict(group=group, drop="+".join(drop) or "-", pol=p, sources=len(m), mean=m.mean(), median=m.median(),
                         pos=int((m > 0).sum()), neg=int((m < 0).sum()), ci_lo=lo, ci_hi=hi,
                         p=wilcoxon(m.values).pvalue if (m != 0).any() else 1.0))
    return pd.DataFrame(rows)


def main():
    S = pd.read_csv(f"{RES}/stage1_summary.csv")
    S["src"] = S.stream.map(source)
    print("sources:", {g: S[S.group == g].groupby("src").stream.nunique().to_dict() for g in ("real", "syn")})
    out = []
    for group, drop in (("real", ()), ("syn", ()), ("real", ("covertype", "poker"))):
        for v in ("", "+half", "+hedge"):
            t = tests(S, group, [d + v for d in DETS], drop)
            t["p_holm"] = holm(t.p)
            out.append(t)
    T = pd.concat(out, ignore_index=True)
    T.to_csv(f"{RES}/stage1_cluster_tests.csv", index=False)
    pd.set_option("display.width", 200, "display.max_rows", 200)
    for (g, d), t in T.groupby(["group", "drop"], sort=False):
        print(f"\n== {g}, dropped: {d}; source-weighted mean of d (points), 95% cluster-bootstrap CI, Wilcoxon over sources")
        print(t.drop(columns=["group", "drop"]).set_index("pol").round({"mean": 2, "median": 2, "ci_lo": 2, "ci_hi": 2,
                                                                       "p": 4, "p_holm": 4}).to_string())


if __name__ == "__main__":
    main()
