"""Feasibility check: how does a tabular foundation model treat a class while it emerges, i.e. while the context holds
n_c = 0, 1, 2, ... rows of it and the incoming data already contain it at a much larger share?
(design and decision rule: logs/EXPERIMENT_LOG.md, 2026-10-06). Usage: python check_emergence.py -> ../results/emergence.csv"""
import os, warnings
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
DATA = "../../MICE/data"
SETS = ["covertype", "insects_abrupt_balanced", "h2_poker", "h2_airlines", "elec2", "h2_spam", "h2_phishing", "h2_rialto", "h2_weather"]
N_CTX, N_TEST, SHARE, SEEDS, NC = 1000, 2000, 0.25, range(5), (0, 1, 2, 5, 10, 20, 50, 100)
OUT = "../results/emergence.csv"


def tabpfn(seed):
    from tabpfn import TabPFNClassifier
    from tabpfn.constants import ModelVersion
    return TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed, n_estimators=4,
                                                       ignore_pretraining_limits=True)


def em_prior(P, prior, it=50):
    """Saerens et al.: re-estimate the class priors on the unlabelled batch and reweight the posteriors."""
    q = prior.copy()
    for _ in range(it):
        W = P * (q / np.clip(prior, 1e-9, None)); W /= W.sum(1, keepdims=True); q = W.mean(0)
    return W


def main():
    rows = pd.read_csv(OUT).to_dict("records") if os.path.exists(OUT) else []
    done = {(r["data"], int(r["seed"])) for r in rows if int(r["n_c"]) == NC[-1]}
    rows = [r for r in rows if (r["data"], int(r["seed"])) in done]
    for name in SETS:
        z = np.load(f"{DATA}/{name}.npz"); X, y = np.nan_to_num(z["X"][:100_000].astype(np.float32)), z["y"][:100_000].astype(int)
        for seed in SEEDS:
            if (name, seed) in done:
                continue
            rng = np.random.default_rng(3000 + seed)
            keep = [k for k in np.unique(y) if (y == k).sum() >= 700]            # enough rows to be the emerging class
            if len(keep) < 2:
                print(name, "fewer than two classes with 700 rows, skipped", flush=True); break
            c = keep[seed % len(keep)]; lab = {k: i for i, k in enumerate(keep)}; K = len(keep); ci = lab[c]
            new = rng.permutation(np.flatnonzero(y == c)); old = rng.permutation(np.flatnonzero(np.isin(y, keep) & (y != c)))
            n_new_test = int(SHARE * N_TEST)
            test = np.r_[new[:n_new_test], old[:N_TEST - n_new_test]]; Xt, yt = X[test], np.array([lab[v] for v in y[test]])
            new_pool, old_pool = new[n_new_test:], old[N_TEST - n_new_test:]
            isnew = yt == ci
            for n_c in NC:
                ctx = np.r_[new_pool[:n_c], old_pool[:N_CTX - n_c]]; Xc, yc = X[ctx], np.array([lab[v] for v in y[ctx]])
                f = tabpfn(seed).fit(Xc, yc); P = np.zeros((len(yt), K)); P[:, f.classes_.astype(int)] = f.predict_proba(Xt)
                pred, conf = P.argmax(1), P.max(1)
                r = dict(data=name, seed=seed, K=K, n_c=n_c, recall_new=float((pred[isnew] == ci).mean()),
                         acc_old=float((pred[~isnew] == yt[~isnew]).mean()), acc=float((pred == yt).mean()),
                         nll=float(-np.log(np.clip(P[np.arange(len(yt)), yt], 1e-6, 1)).mean()),
                         conf_new=float(conf[isnew].mean()), conf_old=float(conf[~isnew].mean()),
                         auroc_unc=float(roc_auc_score(isnew, 1 - conf)))
                if n_c > 0:
                    prior = np.bincount(yc, minlength=K) / len(yc); W = em_prior(P, prior); pw = W.argmax(1)
                    r.update(em_recall_new=float((pw[isnew] == ci).mean()), em_acc_old=float((pw[~isnew] == yt[~isnew]).mean()),
                             em_acc=float((pw == yt).mean()), em_share=float(W.mean(0)[ci]))
                rows.append(r)
            print(name, seed, "done", flush=True)
            pd.DataFrame(rows).to_csv(OUT, index=False)
    r = pd.DataFrame(rows); pd.set_option("display.width", 250)
    print("mean over data sets and seeds, by the number of context rows of the emerging class")
    print((100 * r.groupby("n_c")[["recall_new", "em_recall_new", "acc_old", "em_acc_old", "acc", "em_acc", "conf_new", "conf_old", "auroc_unc", "em_share"]].mean()).round(1).to_string())
    g = r.pivot_table(index="data", columns="n_c", values="recall_new"); e = r.pivot_table(index="data", columns="n_c", values="em_recall_new")
    print("recall of the emerging class per data set"); print((100 * g).round(1).to_string())
    ratio = g[10] / g[100]
    print("rule 1: recall at n_c = 10 relative to n_c = 100: mean %.2f (need <= 0.70); <= 0.70 on %d of %d data sets (need 6)" % (ratio.mean(), (ratio <= 0.70).sum(), len(ratio)))
    gap = g[100] - g[10]; rec = (e[10] - g[10]) / gap
    ao = r[r.n_c == 10].groupby("data")[["acc_old", "em_acc_old"]].mean()
    print("rule 2: EM prior correction closes %.2f of the gap at n_c = 10 on average (open if < 0.50); change of old-class accuracy %+.2f points" % (
        float((e[10] - g[10]).sum() / gap.sum()), 100 * (ao.em_acc_old - ao.acc_old).mean()))
    print("EM share of the gap closed per data set:", rec.round(2).to_dict())
    z0 = r[r.n_c == 0].groupby("data")[["auroc_unc", "conf_new", "conf_old"]].mean()
    print("before any labelled row of the class (n_c = 0): AUROC of 1 - max probability for new vs old rows"); print(z0.round(3).to_string())


if __name__ == "__main__":
    main()
