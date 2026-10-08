"""LaTeX tables of the TMLR draft (../overleaf/tmlr/tables/*.tex), computed from the result files; also prints the
numbers quoted in the text so that they can be checked against the tables.
Source-weighted: a source's value is the mean over its streams; real statistics are over the 19 real sources,
synthetic ones over the 7 generator families. Worst/best source: for each detector the min/max over sources of the
source mean, averaged over the 8 detectors. Harmful share: non-zero single-reset effects (Proposition 1) that are < 0.
Usage: python make_tables.py"""
import os

import numpy as np
import pandas as pd

from analyse_stage1 import DETS, REAL, RES, SYN
from cluster_tests import source
from reset_effects import effects

NEW = ["gas", "occupancy", "room", "bank", "kdd", "eeg", "news", "home", "wall", "chest"]
REALS = REAL + NEW
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "overleaf", "tmlr", "tables")
DATA = {s: "../data" if s in NEW else "../../MICE/data" for s in REALS + SYN}
TFM = [("TabPFN", "tabpfn_M1000"), ("TabICL", "tabicl_M1000"), ("TabDPT", "tabdpt_M1000")]
NUM = []


def say(k, v):
    NUM.append(f"{k}: {v}"); return v


def f(x, d=1):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "--"
    return f"{0:.{d}f}" if round(x, d) == 0 else f"{x:+.{d}f}".replace("-", "$-$")


def d_table(d, pols, base="none", groups=("real", "syn")):
    """per-stream d (points) and per-reset effects for the policies present in directory d."""
    rows, rr = [], []
    for grp in groups:
        for s in (REALS if grp == "real" else SYN):
            if not all(os.path.exists(f"{d}/{s}__{p}.npz") for p in pols + [base]):
                continue
            a0 = np.load(f"{d}/{s}__{base}.npz")["acc"]
            for p in pols:
                z = np.load(f"{d}/{s}__{p}.npz"); a = z["acc"]
                rows.append(dict(group=grp, stream=s, src=source(s), pol=p, d=100 * (np.nanmean(a) - np.nanmean(a0))))
                if "+" not in p and p in DETS:
                    r = z["resets"]
                    for gain in effects(a, a0, r, int(z['B']), int(z['M']) if 'M' in z else None):
                        rr.append(dict(group=grp, det=p, gain=gain))
    return pd.DataFrame(rows), pd.DataFrame(rr)


def tail(S, v, grp="real"):
    x = S[(S.group == grp) & S.pol.isin([k + v for k in DETS])].groupby(["pol", "src"]).d.mean().unstack()
    if x.empty:
        return dict(mean=np.nan, worst=np.nan, best=np.nan)
    return dict(mean=x.mean(1).mean(), worst=x.min(1).mean(), best=x.max(1).mean(),
                worst_src=x.idxmin(1).mode().iloc[0], second_src=x.mean(0).sort_values().index[1])


def harmful(R, grp="real"):
    z = R[(R.group == grp) & (R.gain != 0)]
    return 100 * (z.gain < 0).mean() if len(z) else np.nan


def write(name, body):
    os.makedirs(OUT, exist_ok=True)
    open(f"{OUT}/{name}.tex", "w").write(body)


def main_table():
    T = pd.read_csv(f"{RES}/stage2_tabpfn_tests.csv").set_index(["group", "pol"])
    lines = []
    for k in DETS:
        r = lambda g, v: T.loc[(g, k + v)]
        ci = lambda g, v: f"{f(r(g, v)['mean'], 2)} {{\\scriptsize[{f(r(g, v).ci_lo)}, {f(r(g, v).ci_hi)}]}}"
        name = {"hddma": "HDDM$_A$", "hddmw": "HDDM$_W$", "ph": "Page--Hinkley"}.get(k, k.upper())
        lines.append(f"{name} & {ci('real', '')} & {r('real', '')['p_holm']:.2f} & {f(r('real', '+half')['mean'], 2)} & "
                     f"{ci('real', '+hedge')} & {f(r('syn', '')['mean'], 2)} & {f(r('syn', '+half')['mean'], 2)} & "
                     f"{f(r('syn', '+hedge')['mean'], 2)} \\\\")
    full = T.loc["real"].loc[DETS]
    say("TabPFN real full source-weighted mean range", (round(full["mean"].min(), 2), round(full["mean"].max(), 2)))
    say("TabPFN real full p_holm min", round(full.p_holm.min(), 3))
    say("TabPFN real full sources positive range", (int(full.pos.min()), int(full.pos.max())))
    say("TabPFN syn full mean range", (round(T.loc["syn"].loc[DETS]["mean"].min(), 2), round(T.loc["syn"].loc[DETS]["mean"].max(), 2)))
    say("TabPFN real hedge mean range", (round(T.loc["real"].loc[[k + "+hedge" for k in DETS]]["mean"].min(), 2),
                                         round(T.loc["real"].loc[[k + "+hedge" for k in DETS]]["mean"].max(), 2)))
    write("main_tabpfn", r"""\begin{table}[t]
\centering
\caption{Effect of error-driven resets on TabPFN ($M=1000$): accuracy of each policy minus FIFO, in points.
Real: source-weighted mean over 19 sources with 95\% cluster-bootstrap interval, and Holm-corrected Wilcoxon $p$ over
sources for the full reset. Synthetic: mean over 7 generator families.}
\label{tab:main}
\small
\begin{tabular}{l rrrr rrr}
\toprule
& \multicolumn{4}{c}{Real (19 sources)} & \multicolumn{3}{c}{Synthetic (7 families)} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-8}
Detector & \full & $p_{\mathrm{Holm}}$ & \half & \hedge & \full & \half & \hedge \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def tails_table():
    lines = []
    for name, tag in TFM:
        S, R = d_table(f"{RES}/{tag}", [k + v for k in DETS for v in ("", "+half", "+hedge")])
        t = {v: tail(S, v) for v in ("", "+half", "+hedge")}; sy = {v: tail(S, v, "syn")["mean"] for v in ("", "+hedge")}
        h = harmful(R); hs = harmful(R, "syn")
        for v in t:
            say(f"{name} {v or 'full'} real mean/worst/best", tuple(round(t[v][x], 2) for x in ("mean", "worst", "best")))
        say(f"{name} worst sources (mode, second)", (t[""]["worst_src"], t[""]["second_src"]))
        say(f"{name} harmful share real/syn", (round(h, 1), round(hs, 1) if not np.isnan(hs) else None))
        say(f"{name} syn full/hedge", (round(sy[""], 2), round(sy["+hedge"], 2)))
        lines.append(f"{name} & {f(t[''][  'worst'])} & {f(t['']['best'])} & {f(t['+half']['worst'])} & {f(t['+half']['best'])} & "
                     f"{f(t['+hedge']['worst'])} & {f(t['+hedge']['best'])} & {f(t['']['mean'])} & {f(t['+hedge']['mean'])} & "
                     f"{h:.1f} & {f(sy[''])} & {f(sy['+hedge'])} \\\\")
    write("tails", r"""\begin{table}[t]
\centering
\caption{The tail of resets on three TFMs ($M=1000$), accuracy minus FIFO in points. Worst/best: for each detector the
worst/best of the 19 real sources, averaged over the 8 detectors. Harm: share (\%) of the single resets with a
non-zero effect $\Delta_j$ (\cref{prop:memory}) that are net losses, on real streams. TabDPT was run on real streams
only.}
\label{tab:tails}
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{l rr rr rr rr r rr}
\toprule
& \multicolumn{2}{c}{\full} & \multicolumn{2}{c}{\half} & \multicolumn{2}{c}{\hedge} & \multicolumn{2}{c}{Real mean} & & \multicolumn{2}{c}{Synthetic} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){11-12}
Model & worst & best & worst & best & worst & best & \full & \hedge & Harm & \full & \hedge \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def learners_table():
    lines = []; per = {}
    for name, d in (("Naive Bayes", f"{RES}/trained_nb"), ("Hoeffding tree", f"{RES}/trained_ht"), ("TabPFN", f"{RES}/tabpfn_M1000")):
        S, R = d_table(d, [k + v for k in DETS for v in ("", "+hedge")])
        t, th = tail(S, ""), tail(S, "+hedge"); sy, syh = tail(S, "", "syn")["mean"], tail(S, "+hedge", "syn")["mean"]
        h = harmful(R)
        say(f"{name} full real mean/worst/best/syn", tuple(round(x, 2) for x in (t["mean"], t["worst"], t["best"], sy)))
        say(f"{name} hedge real mean/worst/syn", tuple(round(x, 2) for x in (th["mean"], th["worst"], syh)))
        say(f"{name} harmful share", round(h, 1))
        per[name] = S[(S.group == "real") & S.pol.isin(DETS)].groupby("src").d.mean()
        lines.append(f"{name} & {f(t['mean'])} & {f(t['worst'])} & {f(t['best'])} & {f(sy)} & {h:.1f} & "
                     f"{f(th['mean'])} & {f(th['worst'])} & {f(th['best'])} & {f(syh)} \\\\")
    P = pd.DataFrame(per)
    say("per-source full d (eeg, chest, home, covertype, wall)", P.loc[["eeg", "chest", "home", "covertype", "wall"]].round(1).to_dict())
    write("learners", r"""\begin{table}[t]
\centering
\caption{The same detectors on trained incremental learners and on TabPFN (all 81 streams), accuracy minus the
never-reset learner in points, averaged over the 8 detectors. For trained learners, Harm measures negative
non-zero differences within the first ten batches after an alarm (cut at the next alarm), not the full
effect of the reset. For TabPFN, Harm uses the exact finite-memory attribution in \cref{tab:tails}.}
\label{tab:learners}
\small
\begin{tabular}{l rrrr r rrrr}
\toprule
& \multicolumn{5}{c}{\full} & \multicolumn{4}{c}{\hedge} \\
\cmidrule(lr){2-6}\cmidrule(lr){7-10}
Learner & real & worst & best & synth. & Harm & real & worst & best & synth. \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
    # appendix: absolute accuracy of the never-reset learners and per-source full-reset effects
    absrow = []
    for name, d in (("Naive Bayes", f"{RES}/trained_nb"), ("Hoeffding tree", f"{RES}/trained_ht"), ("TabPFN", f"{RES}/tabpfn_M1000")):
        acc = {g: pd.Series({s: 100 * np.nanmean(np.load(f"{d}/{s}__none.npz")["acc"]) for s in ss
                             if os.path.exists(f"{d}/{s}__none.npz")}) for g, ss in (("real", REALS), ("syn", SYN))}
        sw = lambda a: a.groupby(a.index.map(source)).mean().mean()
        absrow.append(f"{name} & {sw(acc['real']):.1f} & {sw(acc['syn']):.1f} \\\\")
        say(f"{name} absolute acc of none real/syn", (round(sw(acc["real"]), 1), round(sw(acc["syn"]), 1)))
    src_rows = "\n".join(f"{s} & " + " & ".join(f(P.loc[s, c]) for c in P.columns) + " \\\\"
                         for s in P.sort_values("Naive Bayes").index)
    write("learners_abs", r"""\begin{table}[h]
\centering
\caption{Left: accuracy (\%) of the never-reset learner, source-weighted. Right: effect of a full reset per real
source, averaged over the 8 detectors (points).}
\label{tab:learners_abs}
\small
\begin{tabular}{lrr}
\toprule
Learner & Real & Synthetic \\
\midrule
""" + "\n".join(absrow) + r"""
\bottomrule
\end{tabular}\hspace{2em}
\begin{tabular}{lrrr}
\toprule
Source & NB & HT & TabPFN \\
\midrule
""" + src_rows + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def budget_table():
    lines = []
    for M in (500, 1000, 2000):
        S, R = d_table(f"{RES}/tabpfn_M{M}", [k + v for k in DETS for v in ("", "+half", "+hedge")])
        t, th = tail(S, ""), tail(S, "+hedge"); sy = tail(S, "", "syn")["mean"]; h = harmful(R)
        say(f"M{M} full mean/worst/best syn harmful", (round(t["mean"], 2), round(t["worst"], 2), round(t["best"], 2), round(sy, 2), round(h, 1)))
        say(f"M{M} hedge mean/worst/best", (round(th["mean"], 2), round(th["worst"], 2), round(th["best"], 2)))
        lines.append(f"{M} & {M // 100 - 1} & {f(t['mean'])} & {f(t['worst'])} & {f(t['best'])} & {h:.1f} & {f(sy)} & "
                     f"{f(th['mean'])} & {f(th['worst'])} & {f(th['best'])} \\\\")
    write("budget", r"""\begin{table}[t]
\centering
\caption{TabPFN with three context budgets, accuracy minus FIFO in points (detector average; real: 19 sources).
$H-1$ is the number of batches a reset can affect (\cref{prop:memory}).}
\label{tab:budget}
\small
\begin{tabular}{rr rrrr r rrr}
\toprule
& & \multicolumn{5}{c}{\full} & \multicolumn{3}{c}{\hedge} \\
\cmidrule(lr){3-7}\cmidrule(lr){8-10}
$M$ & $H-1$ & real & worst & best & Harm & synth. & real & worst & best \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def hsens_table():
    d = f"{RES}/tabpfn_M1000"
    var = ["+hedge"] + [f"+hedge@e{e}g{g}" for e, g in [(0.5, 0.5), (1, 0.5), (4, 0.5), (8, 0.5), (2, 0.25), (2, 0.75), (2, 0.9), (1, 1)]]
    S, _ = d_table(d, [k + v for k in DETS for v in [""] + var])
    full = tail(S, ""); fs = tail(S, "", "syn")["mean"]; lines = []
    for v in var:
        e, g = (2.0, 0.5) if v == "+hedge" else (float(x) for x in v[8:].split("g"))
        t = tail(S, v); sy = tail(S, v, "syn")["mean"]
        say(f"hsens {v} mean/worst/syn", (round(t["mean"], 2), round(t["worst"], 2), round(sy, 2)))
        mark = " (default)" if v == "+hedge" else " (\\cref{thm:hedge})" if v.endswith("e1g1") else ""
        lines.append(f"{e:g} & {g:g}{mark} & {f(t['mean'], 2)} & {f(t['worst'], 2)} & {f(t['best'], 2)} & {f(sy, 2)} \\\\")
    write("hsens", r"""\begin{table}[t]
\centering
\caption{Sensitivity of the hedge to $\eta$ and $\gamma$ (TabPFN, $M=1000$; detector average, points). For reference,
the full reset has real mean """ + f(full["mean"], 2) + ", worst source " + f(full["worst"], 2) + ", best source " +
          f(full["best"], 2) + " and synthetic mean " + f(fs, 2) + r""".}
\label{tab:hsens}
\small
\begin{tabular}{rl rrrr}
\toprule
$\eta$ & $\gamma$ & real & worst & best & synth. \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def metrics_table():
    lines = []
    for name, tag in TFM:
        fs = [f"{RES}/metrics/{tag}/{s}.csv" for s in REALS]
        if not all(os.path.exists(x) for x in fs):
            say(f"metrics {name}", "MISSING"); continue
        D = pd.concat([pd.read_csv(x) for x in fs]); D["src"] = D.stream.map(source)
        D["act"] = D.pol.map(lambda p: "FIFO" if p == "none" else None if p == "ddmM" else
                             {"": "\\full", "+half": "\\half", "+hedge": "\\hedge"}[p[len(p.split("+")[0]):]])
        D = D.dropna(subset=["act"])
        m = D.groupby(["act", "pol", "src"])[["acc", "f1", "auc", "ece", "logloss", "brier"]].mean().groupby(["act", "pol"]).mean() \
            .groupby("act").mean()
        for i, a in enumerate(["FIFO", "\\full", "\\half", "\\hedge"]):
            r = m.loc[a]
            say(f"metrics {name} {a}", r.round(3).to_dict())
            lines.append((f"\\multirow{{4}}{{*}}{{{name}}}" if i == 0 else "") +
                         f" & {a} & {r.acc:.2f} & {r.f1:.2f} & {r.auc:.2f} & {r.ece:.2f} & {r.logloss:.3f} & {r.brier:.3f} \\\\")
        lines.append("\\midrule")
    write("metrics", r"""\begin{table}[t]
\centering
\caption{Metrics beyond accuracy on the 19 real sources ($M=1000$; source-weighted means; reset actions averaged over
the 8 detectors). Accuracy, macro-F1, macro one-vs-rest ROC AUC and ECE in \%.}
\label{tab:metrics}
\small
\begin{tabular}{ll rrrrrr}
\toprule
Model & Policy & Acc. & F1 & AUC & ECE & Log-loss & Brier \\
\midrule
""" + "\n".join(lines[:-1]) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def data_table():
    rows = []
    for s in REALS:
        z = np.load(f"{DATA[s]}/{s}.npz"); rows.append(dict(src=source(s), stream=s, n=len(z["y"]), p=z["X"].shape[1],
                                                           k=len(np.unique(z["y"]))))
    D = pd.DataFrame(rows)
    g = D.groupby("src").agg(streams=("stream", "count"), rows=("n", "sum"), p=("p", "max"), k=("k", "max"))
    say("real streams/sources/rows", (len(D), D.src.nunique(), int(D.n.sum())))
    body = "\n".join(f"{s} & {r.streams} & {r.rows:,} & {r.p} & {r.k} \\\\" for s, r in g.iterrows())
    write("data", r"""\begin{table}[h]
\centering
\caption{The 19 real sources: number of streams (segments), total rows, features and classes.}
\label{tab:data}
\small
\begin{tabular}{lrrrr}
\toprule
Source & Streams & Rows & Features & Classes \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
""")


if __name__ == "__main__":
    for fn in (main_table, tails_table, learners_table, budget_table, hsens_table, metrics_table, data_table):
        fn()
    open(f"{OUT}/numbers.txt", "w").write("\n".join(NUM) + "\n")
    print("\n".join(NUM))
