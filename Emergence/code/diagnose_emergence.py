"""Diagnosis (2026-10-06, design in logs/EXPERIMENT_LOG.md), derived from check_emergence.py with the same protocol.
For every n_c it adds: auroc_c (AUROC of P(c|x) for new vs old rows: ranking quality, free of any prior/threshold);
oracle_all (rescale every class to the true test prior); oracle_c (rescale class c only, to its true test share,
other classes keep their relative probabilities); em_c (EM on the prior of class c only); and the best accuracy a
single multiplicative weight on class c can reach (best_w_acc, an upper bound for any c-only prior correction).
Original docstring of check_emergence.py follows.
Feasibility check: how does a tabular foundation model treat a class while it emerges, i.e. while the context holds
n_c = 0, 1, 2, ... rows of it and the incoming data already contain it at a much larger share?
(design and decision rule: logs/EXPERIMENT_LOG.md, 2026-10-06). Usage: python check_emergence.py -> ../results/emergence.csv;
python check_emergence.py <out.csv> <set> [<set> ...] runs other data sets (multi-class replication, 2026-10-06)."""
import os, sys, warnings
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
DATA = "../../MICE/data"
SETS = ["covertype", "insects_abrupt_balanced", "h2_poker", "h2_airlines", "elec2", "h2_spam", "h2_phishing", "h2_rialto", "h2_weather"]
N_CTX, N_TEST, SHARE, SEEDS, NC = 1000, 2000, 0.25, range(5), (0, 1, 2, 5, 10, 20, 50, 100)
OUT = "../results/diagnosis.csv"
if len(sys.argv) > 2:
    OUT, SETS = sys.argv[1], sys.argv[2:]


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


def reweight(P, w):
    W = P * w; return W / W.sum(1, keepdims=True)


def em_c(P, prior, ci, it=50):
    """EM on the prior of class ci only; the other classes keep their context proportions."""
    q = prior[ci]
    for _ in range(it):
        w = np.ones(P.shape[1]) * (1 - q) / max(1 - prior[ci], 1e-9); w[ci] = q / max(prior[ci], 1e-9)
        q = reweight(P, w)[:, ci].mean()
    return reweight(P, w)


def scores(W, yt, isnew, ci, tag):
    p = W.argmax(1)
    return {f"{tag}_recall_new": float((p[isnew] == ci).mean()), f"{tag}_acc_old": float((p[~isnew] == yt[~isnew]).mean()),
            f"{tag}_acc": float((p == yt).mean())}


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
                         auroc_unc=float(roc_auc_score(isnew, 1 - conf)),
                         auroc_ent=float(roc_auc_score(isnew, -(P * np.log(np.clip(P, 1e-12, 1))).sum(1))))
                r["auroc_c"] = float(roc_auc_score(isnew, P[:, ci]))
                if n_c > 0:
                    prior = np.bincount(yc, minlength=K) / len(yc); W = em_prior(P, prior); pw = W.argmax(1)
                    r.update(em_recall_new=float((pw[isnew] == ci).mean()), em_acc_old=float((pw[~isnew] == yt[~isnew]).mean()),
                             em_acc=float((pw == yt).mean()), em_share=float(W.mean(0)[ci]))
                    true = np.bincount(yt, minlength=K) / len(yt)
                    r.update(scores(reweight(P, true / np.clip(prior, 1e-9, None)), yt, isnew, ci, "oracle_all"))
                    w = np.ones(K) * (1 - true[ci]) / max(1 - prior[ci], 1e-9); w[ci] = true[ci] / max(prior[ci], 1e-9)
                    r.update(scores(reweight(P, w), yt, isnew, ci, "oracle_c"))
                    r.update(scores(em_c(P, prior, ci), yt, isnew, ci, "emc"))
                    best = 0.0
                    for lw in np.linspace(-2, 8, 101):
                        w = np.ones(K); w[ci] = 10.0 ** lw; best = max(best, float((reweight(P, w).argmax(1) == yt).mean()))
                    r["best_w_acc"] = best
                rows.append(r)
            print(name, seed, "done", flush=True)
            pd.DataFrame(rows).to_csv(OUT, index=False)
    r = pd.DataFrame(rows); pd.set_option("display.width", 250)
    cols = ["recall_new", "acc_old", "acc", "auroc_c", "em_recall_new", "em_acc_old", "em_acc", "emc_recall_new", "emc_acc_old",
            "emc_acc", "oracle_c_recall_new", "oracle_c_acc_old", "oracle_c_acc", "oracle_all_acc", "best_w_acc"]
    print("diagnosis: mean over data sets and seeds by n_c"); print((100 * r.groupby("n_c")[cols].mean()).round(1).T.to_string())
    print("AUROC of P(c|x), new vs old, per data set"); print(r.pivot_table(index="data", columns="n_c", values="auroc_c").round(3).to_string())
    return; pd.set_option("display.width", 250)
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
    z0 = r[r.n_c == 0].groupby("data")[[c for c in ("auroc_unc", "auroc_ent", "conf_new", "conf_old") if c in r]].mean()
    print("before any labelled row of the class (n_c = 0): AUROC of 1 - max probability for new vs old rows"); print(z0.round(3).to_string())


if __name__ == "__main__":
    main()
