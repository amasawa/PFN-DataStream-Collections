"""Stage-1 analysis of the reset evaluation (hypotheses H1-H4, written before the run: logs/EXPERIMENT_LOG.md, 2026-10-06 13:37).

Per stream, a policy's accuracy is the mean over scored batches; streams are weighted equally. Differences are against
`none` (FIFO). Per-reset effect (H3): a full reset at batch t changes the context of batches t .. t+9 only (budget M = 1000,
batch B = 100), after which the context equals FIFO's; the effect of one reset is the summed accuracy difference to `none`
over batches t .. min(t+9, next reset - 1), so overlapping resets are not double counted.
Output: ../results/stage1_summary.csv (per stream x policy), ../results/stage1_resets.csv (per reset), printed verdicts.
Usage: python analyse_stage1.py"""
import glob
import os

import numpy as np
import pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
DIR = f"{RES}/tabpfn_M1000"
DETS = ["ddm", "eddm", "fhddm", "hddma", "hddmw", "adwin", "ph", "kswin"]
REAL = ("covertype insects_abrupt_imbalanced insects_gradual_imbalanced insects_incremental_abrupt_balanced h2_airlines "
        "h2_phishing h2_poker h2_rialto h2_spam h2_weather h3_airlines_b h3_airlines_c h3_covertype_b h3_covertype_c "
        "h3_insects_b h3_insects_c h3_poker_b h3_poker_c h4_airlines_d h4_airlines_e h4_covertype_d h4_covertype_e "
        "h4_poker_d h4_poker_e elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced "
        "insects_incremental_reoccurring_balanced").split()
SYN = [f"{f}_s{s}" for f in ("agrawal", "hyperplane", "rbf", "sea", "sine", "stagger") for s in range(10, 15)] + \
      [f"grid_c{c}_b{b}_s{s}" for c in (5, 30, 100) for b in (500, 2000) for s in (10, 11)]
POLS = ["none", "ddmM"] + [d + v for d in DETS for v in ("", "+half", "+hedge")]


def load(s, p):
    z = np.load(f"{DIR}/{s}__{p}.npz")
    return z["acc"], z["ll"], z["resets"]


def summary():
    rows, rrows = [], []
    for grp, streams in (("real", REAL), ("syn", SYN)):
        for s in streams:
            a0, l0, _ = load(s, "none")
            for p in POLS:
                a, l, r = load(s, p)
                rows.append(dict(group=grp, stream=s, pol=p, acc=100 * np.nanmean(a), ll=np.nanmean(l), resets=len(r),
                                 d_acc=100 * (np.nanmean(a) - np.nanmean(a0))))
                if p in DETS:                                     # per-reset effect of full resets
                    T = len(a)
                    for i, t in enumerate(r):
                        end = min(t + 10, r[i + 1] if i + 1 < len(r) else T, T)
                        rrows.append(dict(group=grp, stream=s, det=p, t=int(t), n=int(end - t),
                                          gain=100 * np.nansum(a[t:end] - a0[t:end])))
    return pd.DataFrame(rows), pd.DataFrame(rrows)


def main():
    S, R = summary()
    S.to_csv(f"{RES}/stage1_summary.csv", index=False)
    R.to_csv(f"{RES}/stage1_resets.csv", index=False)
    d = S.groupby(["group", "pol"]).d_acc
    tab = pd.DataFrame({"mean": d.mean(), "median": d.median(), "worst": d.min(), "best": d.max(),
                        "wins": S.assign(w=S.d_acc > 0).groupby(["group", "pol"]).w.sum(),
                        "resets": S.groupby(["group", "pol"]).resets.mean()}).round(2)
    pd.set_option("display.width", 200, "display.max_rows", 200)
    for g in ("real", "syn"):
        n = (S.group == g).sum() // len(POLS)
        print(f"\n== {g} ({n} streams): accuracy difference to none, points; wins = streams with d > 0")
        print(tab.loc[g].reindex(POLS[1:]).to_string())

    full = {g: tab.loc[g].reindex(DETS)["mean"] for g in ("real", "syn")}
    h1 = (full["real"] < 0).sum()
    h2 = (full["syn"] > 0).sum()
    print(f"\nH1: full reset below none on real streams for {h1}/8 detectors (need >= 6) -> {'holds' if h1 >= 6 else 'fails'}")
    print(f"H2: full reset above none on synthetic streams for {h2}/8 detectors (need >= 6) -> {'holds' if h2 >= 6 else 'fails'}")

    R["loss"] = R.gain < 0
    R["win"] = R.gain > 0
    print("\nH3: share of single full resets with a net loss (sum over batches t .. t+9, cut at the next reset)")
    h3 = {}
    for g in ("real", "syn"):
        x = R[R.group == g]
        per = x.groupby("det").agg(n=("gain", "size"), loss=("loss", "mean"), win=("win", "mean"), mean_gain=("gain", "mean"))
        per[["loss", "win"]] *= 100
        print(f"-- {g}: all {len(x)} resets, loss {100 * x.loss.mean():.1f}%, win {100 * x.win.mean():.1f}%, "
              f"tie {100 * (1 - x.loss.mean() - x.win.mean()):.1f}%, mean gain {x.gain.mean():.2f} points")
        print(per.reindex(DETS).round(2).to_string())
        h3[g] = x.loss.mean(), x.win.mean()
    ok3 = h3["real"][0] > 0.5 and h3["syn"][1] > 0.5
    print(f"H3: real loss share {100 * h3['real'][0]:.1f}% (need > 50%), synthetic win share {100 * h3['syn'][1]:.1f}% "
          f"(need > 50%) -> {'holds' if ok3 else 'fails'}")

    print("\nH4 per detector: real mean d(+hedge) >= -0.2 and synthetic d(+hedge) >= 0.5 * d(full) (when d(full) > 0); "
          "+half between full and +hedge on real")
    rows = []
    for det in DETS:
        rf, rh, rhalf = (tab.loc[("real", det + v), "mean"] for v in ("", "+hedge", "+half"))
        sf, sh, shalf = (tab.loc[("syn", det + v), "mean"] for v in ("", "+hedge", "+half"))
        a = rh >= -0.2
        b = sh >= 0.5 * sf if sf > 0 else None
        rows.append(dict(det=det, real_full=rf, real_half=rhalf, real_hedge=rh, syn_full=sf, syn_half=shalf, syn_hedge=sh,
                         real_ok=a, syn_ok=b, half_between=min(rf, rh) <= rhalf <= max(rf, rh)))
    H4 = pd.DataFrame(rows).set_index("det")
    print(H4.to_string())
    mean = H4[["real_full", "real_hedge", "syn_full", "syn_hedge"]].mean()
    ok_mean = mean.real_hedge >= -0.2 and (mean.syn_full <= 0 or mean.syn_hedge >= 0.5 * mean.syn_full)
    print(f"H4 on the detector average: real d(+hedge) {mean.real_hedge:.2f}, synthetic d(+hedge) {mean.syn_hedge:.2f} vs "
          f"half of d(full) {0.5 * mean.syn_full:.2f} -> {'holds' if ok_mean else 'fails'}; per detector both parts hold for "
          f"{int((H4.real_ok & (H4.syn_ok == True)).sum())}/8")
    print(f"info (not a check; different DDM implementations): ddmM (MICE copy) vs river ddm on real streams, max |acc diff| "
          f"{(S[S.pol == 'ddmM'].set_index('stream').acc - S[S.pol == 'ddm'].set_index('stream').acc).abs().max():.2f} points")


if __name__ == "__main__":
    main()
