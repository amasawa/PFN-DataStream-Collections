"""Feasibility check: how much does label noise in the context cost a tabular foundation model, compared with
classical learners? (see logs/EXPERIMENT_LOG.md, 2026-10-06, for the design and the decision rule written beforehand)
Usage: python check_label_noise.py -> ../results/label_noise.csv"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
DATA = "../../MICE/data"
SETS = ["covertype", "insects_abrupt_balanced", "h2_poker", "h2_airlines", "elec2", "h2_spam", "h2_phishing", "h2_rialto", "h2_weather"]
N_CTX, N_TEST, SEEDS = 1000, 2000, range(5)


def tabpfn(seed):
    from tabpfn import TabPFNClassifier
    from tabpfn.constants import ModelVersion
    return TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed, n_estimators=4,
                                                       ignore_pretraining_limits=True)


def models(seed):
    return {"tabpfn": lambda: tabpfn(seed),
            "rf": lambda: RandomForestClassifier(300, random_state=seed, n_jobs=2),
            "hgb": lambda: HistGradientBoostingClassifier(random_state=seed),
            "knn": lambda: make_pipeline(StandardScaler(), KNeighborsClassifier(15)),
            "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=300))}


def corrupt(y, kind, rate, K, rng):
    y2, flip = y.copy(), np.zeros(len(y), bool)
    if kind == "sym":
        idx = rng.choice(len(y), int(rate * len(y)), replace=False)
        y2[idx] = (y[idx] + rng.integers(1, K, len(idx))) % K; flip[idx] = True
    elif kind == "asym":                               # the largest class is partly relabelled as the second largest
        c = np.bincount(y, minlength=K).argsort()[::-1]
        src = np.flatnonzero(y == c[0]); idx = rng.choice(src, min(len(src), int(rate * len(y))), replace=False)
        y2[idx] = c[1]; flip[idx] = True
    return y2, flip


if __name__ == "__main__":   # guard added 2026-10-06: check_repair.py imports this module and re-ran the whole experiment
    rows = []
    for name in SETS:
        z = np.load(f"{DATA}/{name}.npz"); X, y = z["X"][:100_000].astype(np.float32), z["y"][:100_000].astype(int)
        X = np.nan_to_num(X)
        for seed in SEEDS:
            rng = np.random.default_rng(1000 + seed)
            pool = rng.choice(len(y), min(len(y), 20_000), replace=False)
            keep = [k for k in np.unique(y[pool]) if (y[pool] == k).sum() >= 20]
            pool = pool[np.isin(y[pool], keep)]; lab = {k: i for i, k in enumerate(keep)}; K = len(keep)
            ctx, test = pool[:N_CTX], pool[N_CTX:N_CTX + N_TEST]
            Xc, yc = X[ctx], np.array([lab[v] for v in y[ctx]]); Xt, yt = X[test], np.array([lab[v] for v in y[test]])
            for kind, rate in (("clean", 0.0), ("sym", 0.1), ("sym", 0.2), ("sym", 0.4), ("asym", 0.2)):
                yn, flip = corrupt(yc, kind, rate, K, np.random.default_rng(2000 + seed))
                for m, make in models(seed).items():
                    try:
                        acc = float((make().fit(Xc, yn).predict(Xt) == yt).mean())
                    except Exception as e:
                        acc = np.nan; print("failed", name, seed, kind, rate, m, repr(e)[:80], flush=True)
                    rows.append(dict(data=name, seed=seed, kind=kind, rate=rate, model=m, acc=acc, K=K, flipped=float(flip.mean())))
                if kind == "sym" and rate == 0.2:          # can the model find the flipped rows, and does dropping them help?
                    p_given = np.zeros(len(yn))
                    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(Xc, yn):
                        f = tabpfn(seed).fit(Xc[tr], yn[tr]); P = np.zeros((len(te), K)); P[:, f.classes_.astype(int)] = f.predict_proba(Xc[te])
                        p_given[te] = P[np.arange(len(te)), yn[te]]
                    auc = roc_auc_score(flip, -p_given)
                    keepr = p_given > np.quantile(p_given, 0.2)
                    acc_f = float((tabpfn(seed).fit(Xc[keepr], yn[keepr]).predict(Xt) == yt).mean())
                    rows.append(dict(data=name, seed=seed, kind="sym_filtered", rate=0.2, model="tabpfn", acc=acc_f, K=K,
                                     flipped=float(flip[keepr].mean()), detect_auc=auc))
            print(name, seed, "done", flush=True)
            pd.DataFrame(rows).to_csv("../results/label_noise.csv", index=False)

    r = pd.DataFrame(rows); r.to_csv("../results/label_noise.csv", index=False)
    pd.set_option("display.width", 250)
    r["cond"] = r.kind + "_" + r.rate.astype(str)
    t = r[r.kind != "sym_filtered"].pivot_table(index=["data", "model"], columns="cond", values="acc")
    drop = (t.sub(t["clean_0.0"], axis=0) * 100).drop(columns="clean_0.0")
    print("clean accuracy (%)"); print((100 * t["clean_0.0"].unstack()).round(1).to_string())
    print("drop in points, mean over data sets"); print(drop.groupby("model").mean().round(2).to_string())
    d20 = drop["sym_0.2"].unstack()
    print("drop at 20% symmetric noise per data set"); print(d20.round(2).to_string())
    tp = d20["tabpfn"]; others = d20.drop(columns="tabpfn").mean()
    print("rule 1: TabPFN mean drop %.2f (need <= -3) and %d of %d data sets with a drop of 2 points or more (need 6)" % (tp.mean(), (tp <= -2).sum(), len(tp)))
    print("rule 2: TabPFN mean drop %.2f against the most robust classical learner %s %.2f (TabPFN must not be more robust)" % (tp.mean(), others.idxmax(), others.max()))
    f = r[r.kind == "sym_filtered"].groupby("data")[["acc", "detect_auc", "flipped"]].mean()
    f["clean"] = t["clean_0.0"].unstack()["tabpfn"]; f["noisy"] = t["sym_0.2"].unstack()["tabpfn"]
    f["recovered"] = (f.acc - f.noisy) / (f.clean - f.noisy)
    print("TabPFN at 20% symmetric noise: detection of flipped rows and accuracy after dropping the 20% least plausible rows")
    print(f.round(3).to_string()); print("mean detection AUROC %.3f; mean share of the loss recovered %.2f" % (f.detect_auc.mean(), ((f.acc - f.noisy).sum() / (f.clean - f.noisy).sum())))
