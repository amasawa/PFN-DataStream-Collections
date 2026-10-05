"""Tables of the paper from the cached expert predictions and the baseline outputs (no TFM call).
Replays, on every cache, the single-level rule (eta = 10, last batch), and the two-timescale rule with the outer step
inside the range of the regret bound (half Brier, step 1/2, tempered; the method of the paper) and with step 10 (the
pre-registered variant). Writes ../results_paper/all.csv and the LaTeX tables in ../overleaf/icml/.
Usage: python make_paper_tables.py"""
import glob, os, pickle
import numpy as np, pandas as pd
import reweight

OUT, TEX = "../results_paper", "../overleaf/icml"
DIRS = {"grid10": "../results_grid_test", "grid20": "../results_grid_test3", "fam": "../results_test",
        "realC": "../results_heldout", "realG": "../results_heldout2", "realH": "../results_heldout3", "realI": "../results_heldout4",
        "tabicl": "../results_heldout_tabicl"}
EXTRA = ["../results_river", "../results_trained", "../results_heldout2", "../results_heldout", "../results_heldout34_trained"]
TRAINED = ["arf", "srp", "hat", "levbag", "adwinbag", "nse", "mooe_rff2000_100_2_0.01", "mooe_rff4000_100_2_0.01"]
m = lambda a: float(np.mean(list(a.values())))


def load_acc(stream, method, dirs):
    for d in dirs:
        f = f"{d}/{stream}__{method}.npz"
        if os.path.exists(f):
            return float(np.nanmean(np.load(f)["acc"]))
    return np.nan


def collect():
    rows = []
    for g, d in DIRS.items():
        for f in sorted(glob.glob(f"{d}/*__micev1000_500.pkl")):
            s = os.path.basename(f).split("__")[0]
            c = pickle.load(open(f, "rb"))
            grp = g if g != "fam" else ("fam" if s[-4:-2] == "_s" or s[-3:-1] == "_s" else "realD")
            r = dict(group=grp, stream=s, mice1=m(reweight.simulate(c, 10, 0.0)),
                     mice=m(reweight.simulate2(c, outer="brier", scale=0.5, temper=True)),
                     mice10=m(reweight.simulate2(c, outer="brier")))
            for b in ("fifo1000", "ltm1000_75", "ddm1000", "winens1000", "oracle1000"):
                r[b.replace("1000", "").replace("_75", "")] = load_acc(s, b, [d])
            if g != "tabicl":
                for b in TRAINED:
                    r[b] = load_acc(s, b, EXTRA)
            rows.append(r)
    a = pd.DataFrame(rows)
    a["trained_best"] = a[[c for c in TRAINED if c in a]].max(1)
    tb = a[[c for c in TRAINED if c in a]]
    a["trained_best_name"] = [r.idxmax() if r.notna().any() else "" for _, r in tb.iterrows()]
    return a


def f1(x, best=None, nd=1):
    if pd.isna(x):
        return "--"
    s = f"{100 * x:.{nd}f}"
    return f"\\textbf{{{s}}}" if best is not None and abs(x - best) < 1e-12 else s


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    a = collect(); a.to_csv(f"{OUT}/all.csv", index=False)
    pd.set_option("display.width", 250)
    cols = ["fifo", "ltm", "ddm", "winens", "mice1", "mice10", "mice", "trained_best"]
    print((100 * a.groupby("group")[cols].mean()).round(2).to_string())

    # ---- Table: controlled grid, recall regime (seeds 20, 21 confirmatory for the two-level rule; 10, 11 for the single level)
    pred = {(5, 500): 0.0009, (5, 2000): 0.0003, (30, 500): 0.0191, (30, 2000): 0.0055, (100, 500): 0.1044, (100, 2000): 0.0303}
    g = a[a.group.isin(["grid10", "grid20"])].copy()
    g["c"] = g.stream.str.extract(r"_c(\d+)_")[0].astype(int); g["b"] = g.stream.str.extract(r"_b(\d+)_")[0].astype(int)
    L = []
    for (c, b), p in pred.items():
        x = g[(g.c == c) & (g.b == b)]; x20 = x[x.group == "grid20"]
        vals = [x20[k].mean() for k in ("fifo", "winens", "ddm", "mice1", "mice")]
        L.append(f"    {c} & {b} & " + " & ".join(f1(v, max(vals)) for v in vals) + f" & {100 * p:.1f} & {100 * (x20.mice - x20.ddm).mean():+.1f} \\\\")
    x20 = g[g.group == "grid20"]; x10 = g[g.group == "grid10"]
    vals = [x20[k].mean() for k in ("fifo", "winens", "ddm", "mice1", "mice")]
    L.append("    \\midrule\n    \\multicolumn{2}{l}{Mean} & " + " & ".join(f1(v, max(vals)) for v in vals) + f" & & {100 * (x20.mice - x20.ddm).mean():+.1f} \\\\")
    open(f"{TEX}/tab_grid_rows.tex", "w").write("\n".join(L) + "\n")
    sp = pd.DataFrame([dict(p=p, o1=(g[(g.c == c) & (g.b == b) & (g.group == "grid10")].eval("mice1 - ddm")).mean(),
                            o2=(g[(g.c == c) & (g.b == b) & (g.group == "grid20")].eval("mice - ddm")).mean()) for (c, b), p in pred.items()])
    print("Spearman predicted vs observed gain: seeds 10-11 single level %.3f; seeds 20-21 two-level %.3f" %
          (sp.p.corr(sp.o1, method="spearman"), sp.p.corr(sp.o2, method="spearman")))
    print("grid20: mice > ddm on hard streams:", int((x20[x20.c > 5].mice > x20[x20.c > 5].ddm).sum()), "of", len(x20[x20.c > 5]),
          "; mice > winens:", int((x20[x20.c > 5].mice > x20[x20.c > 5].winens).sum()),
          "; mean mice - mice1 %+.4f; mice10 - mice1 %+.4f" % ((x20.mice - x20.mice1).mean(), (x20.mice10 - x20.mice1).mean()))

    # ---- Table: real streams
    names = {"realD": "development", "realC": "first held-out set", "realG": "second held-out set", "realH": "third held-out set", "realI": "fourth held-out set (confirmatory)"}
    L = []
    r = a[a.group.isin(names)].copy()
    for grp, title in names.items():
        x = r[r.group == grp]
        L.append(f"    \\multicolumn{{10}}{{l}}{{\\emph{{{title}}}}} \\\\")
        for _, z in x.iterrows():
            vals = [z[k] for k in ("fifo", "ltm", "ddm", "winens", "mice1", "mice10", "mice")]
            nm = z.stream.replace("insects_", "ins-").replace("_balanced", "-bal").replace("_imbalanced", "-imb").replace("incremental", "incr") \
                .replace("reoccurring", "reoc").replace("h2_", "").replace("h3_", "").replace("h4_", "").replace("_", "-")
            L.append(f"    {nm} & " + " & ".join(f1(v, max(vals)) for v in vals) + f" & {f1(z.trained_best)} & " + f"{100 * (z.mice - z.fifo):+.2f}".replace("-", "$-$") + " \\\\")
        vals = [x[k].mean() for k in ("fifo", "ltm", "ddm", "winens", "mice1", "mice10", "mice")]
        L.append("    \\quad mean & " + " & ".join(f1(v, max(vals)) for v in vals) + f" & {f1(x.trained_best.mean())} & {100 * (x.mice - x.fifo).mean():+.2f} \\\\")
        L.append("    \\midrule")
    vals = [r[k].mean() for k in ("fifo", "ltm", "ddm", "winens", "mice1", "mice10", "mice")]
    L.append("    All streams & " + " & ".join(f1(v, max(vals)) for v in vals) + f" & & {100 * (r.mice - r.fifo).mean():+.2f} \\\\")
    open(f"{TEX}/tab_real_rows.tex", "w").write("\n".join(L) + "\n")
    S = []
    for grp, title in list(names.items()) + [("all", "all streams")]:
        x = r if grp == "all" else r[r.group == grp]
        vals = [x[k].mean() for k in ("fifo", "ltm", "ddm", "winens", "mice1", "mice")]
        worst = [100 * (x[k] - x.fifo).min() for k in ("ddm", "winens", "mice1", "mice")]
        S.append(f"    {title} & {len(x)} & " + " & ".join(f1(v, max(vals)) for v in vals) + " & " + " & ".join(f"{w:+.1f}".replace("-", "$-$") for w in worst) + " \\\\")
        if grp == "realI":
            S.append("    \\midrule")
    open(f"{TEX}/tab_real_summary_rows.tex", "w").write("\n".join(S) + "\n")
    tfm = ["fifo", "ltm", "ddm", "winens"]
    for nm, k in (("mice (eta2 = 1/2)", "mice"), ("mice10 (eta2 = 10)", "mice10"), ("mice1 (single level)", "mice1")):
        d = r[k] - r[tfm].max(1); df = r[k] - r.fifo
        print(f"{nm}: real streams best on {(d > 0).sum()}/29; vs best TFM baseline min {100 * d.min():+.2f} mean {100 * d.mean():+.2f};"
              f" vs fifo min {100 * df.min():+.2f} mean {100 * df.mean():+.2f} wins {(df > 0).sum()}/29; per group vs fifo:",
              (100 * df.groupby(r.group).mean()).round(2).to_dict(), "worst per group vs fifo", (100 * df.groupby(r.group).min()).round(2).to_dict())
    print("ddm - fifo on real streams: min %+.2f, mean %+.2f; winens - fifo: min %+.2f mean %+.2f; mice1 - fifo min %+.2f" % (
        100 * (r.ddm - r.fifo).min(), 100 * (r.ddm - r.fifo).mean(), 100 * (r.winens - r.fifo).min(), 100 * (r.winens - r.fifo).mean(), 100 * (r.mice1 - r.fifo).min()))
    print("trained best below fifo on", int((r.trained_best < r.fifo).sum()), "of", int(r.trained_best.notna().sum()), "streams with trained baselines")
    print(r[["group", "stream", "fifo", "ddm", "winens", "mice1", "mice10", "mice", "trained_best", "trained_best_name"]].round(4).to_string())
    f = a[a.group == "fam"].copy(); f["fam"] = f.stream.str.replace(r"_s\d+$", "", regex=True)
    print((100 * f.groupby("fam")[["fifo", "ltm", "ddm", "winens", "mice1", "mice10", "mice", "oracle"]].mean()).round(2).to_string())
    print("family streams: mean mice - ddm %+.4f, positive on %d of %d" % ((f.mice - f.ddm).mean(), (f.mice > f.ddm).sum(), len(f)))
    t = a[a.group == "tabicl"]
    print("TabICL:\n", (100 * t.set_index("stream")[["fifo", "ddm", "winens", "mice1", "mice10", "mice"]]).round(2).to_string())
    g10 = a[a.group == "grid10"]
    print("grid10 means:", (100 * g10[["fifo", "winens", "ddm", "mice1", "mice10", "mice", "oracle", "arf", "srp", "mooe_rff4000_100_2_0.01"]].mean()).round(2).to_dict())
