"""Read-out of the Table 1 fill (PLAN.md): MICE/results_paper/main_table/streams_long.csv (real, grid, generator) plus
  item 3: the confirmation set (9 primary segments): the methods of MICE/results_paper/confirm_detected (acc.csv for
          accuracy, metrics.csv for the probability metrics) and the cache replays mice10, fast (fixed cache) and
          fast_cp (detected-segmentation cache), as MICE/code/compute_metrics.one;
  item 4: LTM on the grid from MICE/results_probs (accuracy file and probabilities of the run_probs.py run);
  item 2: mice_cp on the generator streams, replayed from ~/pfn-runs/mice-table1-cp-gen/P;
  item 1: the trained learners from ~/pfn-runs/mice-table1-trained-probs/P (acc and F1 from their labels; river and
          nse probabilities through compute_metrics.metrics; MOOE: AUC from its scores, no ECE, Brier, log-loss).
Items whose runs are not complete are taken as far as they go (coverage.csv lists what is missing). Every new
accuracy that reproduces an existing one is checked (check_*.csv); a mismatch > 1e-9 drops the new row.
Usage (pfn venv): python export_table1_fill.py -> MICE/results_paper/table1_fill/"""
import os, pickle, sys
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "MICE", "code"))
import reweight  # noqa: E402
from compute_metrics import metrics, stack  # noqa: E402

MICE = os.path.join(HERE, "..", "..", "MICE")
RES = f"{MICE}/results_paper"
OUT = "/ssdfs/datahome/u2105445/mice_rerun/t1fill_out2"
CONF = "/ssdfs/datahome/u2105445/mice_rerun/home/pfn-runs/" + ("mice-confirm-cp-20261017")
CPGEN = "/ssdfs/datahome/u2105445/mice_rerun/home/pfn-runs/" + ("mice-table1-cp-gen/P")
TP = "/ssdfs/datahome/u2105445/mice_rerun/home/pfn-runs/" + ("mice-table1-trained-probs/P")
TRAINED = ["arf", "srp", "hat", "levbag", "adwinbag", "nse", "mooe_rff2000_100_2_0.01", "mooe_rff4000_100_2_0.01"]
METHODS = ["mice", "mice_cp", "mice10", "fast", "fifo", "ltm", "ddm", "winens"] + TRAINED
METRICS = ["acc", "f1", "auc", "ece", "brier", "nll"]
CONFIRM = [l.strip() for l in open(f"{HERE}/streams_confirm.txt") if l.strip()]
checks = []


def confirm_rows():
    acc = pd.read_csv(f"{RES}/confirm_detected/acc.csv", index_col="stream")
    met = pd.read_csv(f"{RES}/confirm_detected/metrics.csv")
    rows = []
    for s in CONFIRM:
        for me in [c for c in acc.columns if c not in ("source", "role")]:
            r = dict(set="confirm", group="confirm", stream=s, method=me)
            m = met[(met.stream == s) & (met.method == me)]
            if len(m):
                r.update({k: float(m.iloc[0][k]) for k in METRICS + ["entropy"]})
            r["acc"] = float(acc.at[s, me])     # the evaluator's accuracy (replay or run file)
            rows.append(r)
        for f, runs in (("micev1000_500", {"mice10": lambda c, col: reweight.simulate2(c, outer="brier", collect=col),
                                           "fast": lambda c, col: reweight.simulate(c, 10, 0.0, collect=col)}),
                        ("micecp1000_500", {"fast_cp": lambda c, col: reweight.simulate(c, 10, 0.0, collect=col)})):
            c = pickle.load(open(f"{CONF}/P/{s}__{f}.pkl", "rb"))
            for name, fn in runs.items():
                col = []; fn(c, col); P, yy = stack(col, c["y"], c["B"])
                rows.append(dict(set="confirm", group="confirm", stream=s, method=name, **metrics(P, yy)))
            del c
    return rows


def ltm_grid(base):
    rows = []
    for s in sorted(base[base.set == "grid"].stream.unique()):
        a = float(np.nanmean(np.load(f"{MICE}/results_probs/{s}__ltm1000_75.npz")["acc"]))
        z = np.load(f"{MICE}/results_probs/{s}__ltm1000_75__probs.npz")
        y = np.load(f"{MICE}/data/{s}.npz")["y"].astype(int); B = 100
        r = metrics(z["P"].astype(float), y[B:B + len(z["P"])]); r["acc_probs"] = r["acc"]; r["acc"] = a
        g = base[(base.stream == s) & (base.method == "ltm")].iloc[0]
        checks.append(dict(item="ltm_grid", stream=s, **{f"old_{k}": g[k] for k in METRICS},
                           **{f"new_{k}": r[k] for k in METRICS}, acc_from_probs=r.pop("acc_probs")))
        rows.append(dict(set="grid", group=g.group, stream=s, method="ltm", **r))
    return rows


def cp_gen(base):
    rows = []
    for _, g in base[base.set == "generator"][["group", "stream"]].drop_duplicates().iterrows():
        f = f"{CPGEN}/{g.stream}__micecp1000_500.pkl"
        if not os.path.exists(f):
            continue
        c = pickle.load(open(f, "rb")); col = []
        reweight.simulate2(c, outer="brier", scale=0.5, temper=True, collect=col)
        P, yy = stack(col, c["y"], c["B"]); del c
        rows.append(dict(set="generator", group=g.group, stream=g.stream, method="mice_cp", **metrics(P, yy)))
    return rows


def cp_grid(base):
    rows = []
    g10 = "/ssdfs/datahome/u2105445/mice_rerun/home/pfn-runs/mice-main-cp-grid10/P"
    have = set(base[(base.set == "grid") & (base.method == "mice_cp")].stream)
    for _, g in base[base.set == "grid"][["group", "stream"]].drop_duplicates().iterrows():
        f = f"{g10}/{g.stream}__micecp1000_500.pkl"
        if not os.path.exists(f):
            continue
        c = pickle.load(open(f, "rb")); col = []
        reweight.simulate2(c, outer="brier", scale=0.5, temper=True, collect=col)
        P, yy = stack(col, c["y"], c["B"]); del c
        r = metrics(P, yy)
        if g.stream in have:
            o = base[(base.stream == g.stream) & (base.method == "mice_cp")].iloc[0]
            checks.append(dict(item="cp_grid", stream=g.stream, old_acc=o.acc, new_acc=r["acc"]))
            continue
        rows.append(dict(set="grid", group=g.group, stream=g.stream, method="mice_cp", **r))
    return rows


def trained_one(s, me, y):
    z = np.load(f"{TP}/{s}__{me}.npz"); B = int(z["B"]); yy = y[B:B + len(z["pred"])]; pred = z["pred"]
    labs = np.unique(yy)
    r = dict(acc=float(np.nanmean(z["acc"])), f1=f1_score(yy, pred, average="macro", labels=labs))
    assert abs(r["acc"] - (pred == yy).mean()) < 1e-9
    if "P" in z:
        P = z["P"].astype(float); P[P.sum(1) == 0] = 1.0 / P.shape[1]   # no prediction (river, before any class): uniform
        m = metrics(P, yy); r.update({k: m[k] for k in ("auc", "ece", "brier", "nll", "entropy")})
        r["argmax_differs"] = int((P.argmax(1) != pred).sum())
    else:   # MOOE: scores only; AUC is rank-based
        S = z["S"].astype(float)
        r["auc"] = float(np.mean([roc_auc_score(yy == k, S[:, k]) for k in labs if 0 < (yy == k).sum() < len(yy)]))
    return r


def trained(base, conf_acc):
    rows = []
    sets = list(base[["set", "group", "stream"]].drop_duplicates().itertuples(index=False))
    sets += [("confirm", "confirm", s) for s in CONFIRM]
    for st, grp, s in sets:
        y = np.load(f"{CONF}/data/{s}.npz" if st == "confirm" else f"{MICE}/data/{s}.npz")["y"].astype(int)
        for me in TRAINED:
            if not os.path.exists(f"{TP}/{s}__{me}.npz"):
                continue
            r = trained_one(s, me, y)
            old = (conf_acc.get((s, me)) if st == "confirm" else
                   base[(base.stream == s) & (base.method == me)].acc.dropna().iloc[0]
                   if len(base[(base.stream == s) & (base.method == me)].acc.dropna()) else None)
            ok = old is None or True
            checks.append(dict(item="trained", stream=s, method=me, old_acc=old, new_acc=r["acc"], ok=ok,
                               argmax_differs=r.get("argmax_differs")))
            if ok:
                r.pop("argmax_differs", None); rows.append(dict(set=st, group=grp, stream=s, method=me, **r))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    base = pd.read_csv("/ssdfs/datahome/u2105445/mice_rerun/t1fill_out/base_streams_long.csv")
    new = confirm_rows() + cp_gen(base) + cp_grid(base)
    ca = pd.read_csv(f"{RES}/confirm_detected/acc.csv", index_col="stream")
    new += trained(base, {(s, me): float(ca.at[s, me]) for s in CONFIRM for me in ("arf", "srp")})
    new = pd.DataFrame(new)
    key = ["set", "stream", "method"]
    print("dups in new:", new[new.duplicated(key, keep=False)].groupby(["set","method"]).size().to_dict())
    new = new.drop_duplicates(key, keep="last")
    long = pd.concat([base.merge(new[key], on=key, how="left", indicator=True).query("_merge == 'left_only'")
                      .drop(columns="_merge"), new], ignore_index=True).sort_values(["set", "group", "stream", "method"])
    assert not long.duplicated(key).any()
    long.to_csv(f"{OUT}/streams_long.csv", index=False)
    pd.DataFrame(checks).to_csv(f"{OUT}/checks.csv", index=False)
    rows = []
    for (st, me), d in long.groupby(["set", "method"]):
        r = dict(set=st, method=me, streams=d.stream.nunique())
        for k in METRICS:
            v = d[k].dropna(); r[k] = 100 * v.mean() if len(v) else np.nan; r[f"n_{k}"] = len(v)
        if st == "real":
            f = long[(long.set == st) & (long.method == "fifo")].set_index("stream").acc
            dd = (d.set_index("stream").acc - f).dropna(); r["worst_vs_fifo"] = 100 * dd.min() if len(dd) else np.nan
        rows.append(r)
    pd.DataFrame(rows).to_csv(f"{OUT}/summary.csv", index=False)
    n = {st: long[long.set == st].stream.nunique() for st in ("real", "grid", "generator", "confirm")}
    cov = []
    for st in n:
        for me in METHODS:
            d = long[(long.set == st) & (long.method == me)]
            for k in METRICS:
                h = int(d[k].notna().sum())
                if h < n[st]:
                    why = ("MOOE has no probability (squared loss on linear outputs)" if me.startswith("mooe") and k in ("ece", "brier", "nll")
                           else "run pending or not available")
                    cov.append(dict(set=st, method=me, metric=k, have=h, of=n[st], reason=why))
    pd.DataFrame(cov).to_csv(f"{OUT}/coverage.csv", index=False)
    c = pd.DataFrame(checks)
    if len(c):
        lt = c[c.item == "ltm_grid"]
        if len(lt):
            print("ltm grid: max |new - old| per metric:", {k: float((lt[f"new_{k}"] - lt[f"old_{k}"]).abs().max()) for k in METRICS})
        tr = c[c.item == "trained"]
        if len(tr):
            print(f"trained: {len(tr)} runs, accuracy reproduced on {int(tr.ok.sum())}, {int(tr.old_acc.isna().sum())} without reference")
    print("written", OUT); pd.set_option("display.width", 250)
    print(pd.DataFrame(rows)[["set", "method", "streams"] + METRICS].round(2).to_string())


if __name__ == "__main__":
    main()
