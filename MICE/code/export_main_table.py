"""Data for the main results table (Table 1) from existing runs, no TFM call: per-stream values of every strategy on the
29 real streams, the 24 grid streams and the 30 generator streams, and per-set means.

Sources: ../results_paper/all.csv (accuracy of every strategy, including the 8 trained learners), ../results_paper/
metrics.csv (F1, AUC, ECE, Brier, log-loss of the TFM strategies), and the detected-segmentation runs of round 14
(~/pfn-runs/mice-r14-exist/P/*__micecp1000_500.pkl): MICE with detected segments ("mice_cp") is replayed from its expert
cache with the frozen rule (reweight.simulate2, outer = brier, scale = 0.5, temper) and its metrics are computed with
compute_metrics.metrics; the replayed accuracy is checked against the round-14 tables of the paper (r14_real_streams.csv,
r14_aligned_streams.csv, column cp). The .npz of the run stores the accuracy of the run's online rule, not of this replay.
Missing combinations are left empty (coverage.csv lists them).
Usage: python export_main_table.py -> ../results_paper/main_table/"""
import os, pickle
import numpy as np, pandas as pd
import reweight
from compute_metrics import metrics, stack

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results_paper")
OUT = os.path.join(RES, "main_table")
CP = [os.path.expanduser(f"~/pfn-runs/{r}/P") for r in ("mice-r14-exist", "mice-main-cp-grid10")]   # 2nd: PLAN of
# experiments/mice_main_table_20261017 (grid10)
TRAINED_GRID20 = os.path.expanduser("~/pfn-runs/mice-main-trained-grid20")
SET = {"realC": "real", "realD": "real", "realG": "real", "realH": "real", "realI": "real",
       "grid10": "grid", "grid20": "grid", "fam": "generator"}
TRAINED = ["arf", "srp", "hat", "levbag", "adwinbag", "nse", "mooe_rff2000_100_2_0.01", "mooe_rff4000_100_2_0.01"]
METRICS = ["acc", "f1", "auc", "ece", "brier", "nll"]


def cp_rows(streams):
    rows, chk = [], []
    for g, s in streams:
        f = next((f"{d}/{s}__micecp1000_500.pkl" for d in CP if os.path.exists(f"{d}/{s}__micecp1000_500.pkl")), None)
        if f is None:
            continue
        c = pickle.load(open(f, "rb")); col = []
        reweight.simulate2(c, outer="brier", scale=0.5, temper=True, collect=col)
        P, yy = stack(col, c["y"], c["B"])
        rows.append(dict(group=g, stream=s, method="mice_cp", **metrics(P, yy)))
        chk.append(dict(stream=s, replay=100 * rows[-1]["acc"]))
        del c, col, P
    return rows, pd.DataFrame(chk)


def main():
    os.makedirs(OUT, exist_ok=True)
    a = pd.read_csv(f"{RES}/all.csv")
    a = a[a.group.isin(SET)].copy()
    for b in TRAINED:   # grid20 runs of the trained learners (same accuracy as make_paper_tables.load_acc)
        for i in a.index[a.group == "grid20"]:
            f = f"{TRAINED_GRID20}/{a.at[i, 'stream']}__{b}.npz"
            if os.path.exists(f):
                assert pd.isna(a.at[i, b]); a.at[i, b] = float(np.nanmean(np.load(f)["acc"]))
    acc = a.melt(id_vars=["group", "stream"], value_vars=["mice", "mice10", "fifo", "ltm", "ddm", "winens", "oracle"] + TRAINED,
                 var_name="method", value_name="acc").dropna(subset=["acc"])
    m = pd.read_csv(f"{RES}/metrics.csv")
    m = m[~m.method.str.endswith("_file") & m.group.isin(SET)]
    cpr, chk = cp_rows(a[a.group != "fam"][["group", "stream"]].itertuples(index=False))
    r14 = pd.concat([pd.read_csv(f"{RES}/{n}.csv")[["stream", "cp"]] for n in ("r14_real_streams", "r14_aligned_streams")])
    chk = chk.merge(r14, on="stream", how="left"); chk["diff"] = (chk.replay - chk.cp).abs()
    assert chk["diff"].max() < 1e-9, chk.sort_values("diff").tail()   # streams in the r14 tables (grid10: no reference)
    chk.to_csv(f"{OUT}/check_cp_replay.csv", index=False)
    print(f"mice_cp replay vs r14 tables: max |diff| = {chk['diff'].max():.2e} over {len(chk)} streams")
    m = pd.concat([m, pd.DataFrame(cpr)], ignore_index=True)
    # accuracy: all.csv where it has a value, otherwise the replayed accuracy of metrics.csv (fast, mice_cp, and ltm on
    # the grid, which exists only from run_probs.py)
    long = acc.merge(m, on=["group", "stream", "method"], how="outer", suffixes=("", "_m"))
    both = long.acc.notna() & long.acc_m.notna()
    rerun = long.method.isin(["ddm", "ltm"])   # their metrics come from a separate run (run_probs.py): <= 0.05 points
    dd = (long.acc - long.acc_m).abs()
    assert dd[both & ~rerun].max() < 1e-9 and dd[both & rerun].max() < 1e-3, "all.csv and metrics.csv disagree"
    long["acc"] = long.acc.fillna(long.acc_m); long = long.drop(columns="acc_m")
    long.insert(0, "set", long.group.map(SET))
    long = long.sort_values(["set", "group", "stream", "method"])
    long.to_csv(f"{OUT}/streams_long.csv", index=False)
    for st, d in long.groupby("set"):
        d.pivot_table(index=["group", "stream"], columns="method", values="acc").to_csv(f"{OUT}/acc_{st}.csv")
    # per-set means (values in percent) and the worst per-stream accuracy difference to FIFO
    rows = []
    for (st, me), d in long.groupby(["set", "method"]):
        r = dict(set=st, method=me, streams=d.stream.nunique())
        for k in METRICS:
            v = d[k].dropna(); r[k] = 100 * v.mean() if len(v) else np.nan; r[f"n_{k}"] = len(v)
        f = long[(long.set == st) & (long.method == "fifo")].set_index("stream").acc
        dd = (d.set_index("stream").acc - f).dropna()
        r["worst_vs_fifo"] = 100 * dd.min() if len(dd) else np.nan
        rows.append(r)
    pd.DataFrame(rows).to_csv(f"{OUT}/summary.csv", index=False)
    n = {st: long[long.set == st].stream.nunique() for st in long.set.unique()}
    cov = [dict(set=st, method=me, metric=k, have=int(d[k].notna().sum()), of=n[st])
           for (st, me), d in long.groupby(["set", "method"]) for k in METRICS if d[k].notna().sum() < n[st]]
    pd.DataFrame(cov).to_csv(f"{OUT}/coverage.csv", index=False)
    print("written", OUT); print(pd.DataFrame(rows).round(2).to_string())


if __name__ == "__main__":
    main()
