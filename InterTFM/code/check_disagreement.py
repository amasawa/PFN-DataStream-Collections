"""Feasibility check of Idea 3 (inter-TFM drift), from cached predictions only (no TFM call).
Reads the expert caches written by the MICE runs for TabPFN v2 and TabICL on the same streams and takes, for every
row, the prediction of the M-row FIFO window expert of each backbone: the same context, two models.
Row level: does the disagreement (Jensen-Shannon divergence) detect errors of TabPFN beyond its own uncertainty?
Batch level: does the mean disagreement of a batch track its error rate better than the mean uncertainty?
Also: accuracy of the two models and of their average, overall and on the 10% of rows with the largest disagreement.
Usage: python check_disagreement.py -> ../results/disagreement.csv   (decision rule: see logs/EXPERIMENT_LOG.md)"""
import os, pickle
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

M = "../../MICE"
PAIRS = {"results_heldout": "results_heldout_tabicl", "results_heldout3": "results_heldout3_tabicl",
         "results_heldout4": ["results_heldout4_tabicl", "results_heldout4_tabicl_e"]}


def fifo_probs(f):
    c = pickle.load(open(f, "rb")); y, B = c["y"], c["B"]
    st = sorted(c["cache"], key=lambda s: s["t"])
    return (np.concatenate([s["P"][-1000] for s in st]), np.concatenate([y[s["t"] * B:(s["t"] + 1) * B] for s in st]), B,
            [s["t"] for s in st])


def js(P, Q):
    P, Q = np.clip(P, 1e-12, 1), np.clip(Q, 1e-12, 1); Mx = 0.5 * (P + Q)
    return 0.5 * (P * np.log(P / Mx)).sum(1) + 0.5 * (Q * np.log(Q / Mx)).sum(1)


def one(stream, fa, fb):
    Pa, y, B, ta = fifo_probs(fa); Pb, yb, _, tb = fifo_probs(fb)
    assert ta == tb and np.array_equal(y, yb), "the two runs must cover the same batches"
    K = max(Pa.shape[1], Pb.shape[1])
    pad = lambda P: np.pad(P, ((0, 0), (0, K - P.shape[1])))
    Pa, Pb = pad(Pa), pad(Pb)
    d, u, ub = js(Pa, Pb), 1 - Pa.max(1), 1 - Pb.max(1)
    ea, eb = Pa.argmax(1) != y, Pb.argmax(1) != y
    Pm = 0.5 * (Pa + Pb); em = Pm.argmax(1) != y
    r = dict(stream=stream, n=len(y), acc_pfn=1 - ea.mean(), acc_icl=1 - eb.mean(), acc_avg=1 - em.mean(),
             agree=(Pa.argmax(1) == Pb.argmax(1)).mean(), auc_u=roc_auc_score(ea, u), auc_d=roc_auc_score(ea, d),
             auc_u_icl=roc_auc_score(ea, ub), spearman_u_d=spearmanr(u, d)[0])
    h = len(y) // 2                                   # fit on the first half of the stream, test on the second
    Z = np.c_[np.log(u + 1e-4), np.log(d + 1e-6)]
    r["auc_u_test"] = roc_auc_score(ea[h:], u[h:])
    r["auc_ud_test"] = roc_auc_score(ea[h:], LogisticRegression(max_iter=500).fit(Z[:h], ea[:h]).predict_proba(Z[h:])[:, 1])
    Z3 = np.c_[Z, np.log(ub + 1e-4)]
    r["auc_u_uicl_d_test"] = roc_auc_score(ea[h:], LogisticRegression(max_iter=500).fit(Z3[:h], ea[:h]).predict_proba(Z3[h:])[:, 1])
    nb = len(y) // B; bm = lambda v: v[:nb * B].reshape(nb, B).mean(1)
    r["batch_rho_u"] = spearmanr(bm(u), bm(ea.astype(float)))[0]; r["batch_rho_d"] = spearmanr(bm(d), bm(ea.astype(float)))[0]
    top = d >= np.quantile(d, 0.9)
    r.update(top_acc_pfn=1 - ea[top].mean(), top_acc_icl=1 - eb[top].mean(), top_acc_avg=1 - em[top].mean(),
             top_share_of_errors=ea[top].sum() / max(ea.sum(), 1))
    return r


if __name__ == "__main__":
    from joblib import Parallel, delayed
    import glob
    jobs = []
    for a, bs in PAIRS.items():
        for b in ([bs] if isinstance(bs, str) else bs):
            for fb in sorted(glob.glob(f"{M}/{b}/*__micev1000_500.pkl")):
                s = os.path.basename(fb).split("__")[0]; fa = f"{M}/{a}/{s}__micev1000_500.pkl"
                if os.path.exists(fa):
                    jobs.append((s, fa, fb))
    res = pd.DataFrame(Parallel(n_jobs=4)(delayed(one)(*j) for j in jobs)).set_index("stream")
    res.to_csv("../results/disagreement.csv")
    pd.set_option("display.width", 250)
    print((100 * res[["acc_pfn", "acc_icl", "acc_avg", "agree"]]).round(2).to_string())
    print(res[["auc_u", "auc_d", "auc_u_icl", "spearman_u_d", "auc_u_test", "auc_ud_test", "auc_u_uicl_d_test", "batch_rho_u", "batch_rho_d"]].round(3).to_string())
    print((100 * res[["top_acc_pfn", "top_acc_icl", "top_acc_avg", "top_share_of_errors"]]).round(1).to_string())
    g = res.auc_ud_test - res.auc_u_test; b = res.batch_rho_d - res.batch_rho_u
    print("mean", res.mean(numeric_only=True).round(3).to_dict())
    print("rule (a): AUROC gain of u + d over u >= 0.02 on %d of %d streams (need 10); gains %s" % ((g >= 0.02).sum(), len(g), g.round(3).to_dict()))
    print("rule (b): batch Spearman of d exceeds that of u by >= 0.10 on %d of %d streams (need 10); differences %s" % ((b >= 0.10).sum(), len(b), b.round(3).to_dict()))
    print("consensus minus the better single model, points:", (100 * (res.acc_avg - res[["acc_pfn", "acc_icl"]].max(1))).round(2).to_dict())
