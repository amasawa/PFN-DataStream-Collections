"""Adds a label-free discrepancy to an existing micev cache without re-running the stream: the expert pool is rebuilt
with the same merge rule (TFM calls only when a segment closes), and for every batch the discrepancy between each
expert's context and the incoming unlabelled batch is the cross-fitted AUC of a domain classifier (kNN on features
standardised by the pooled rows), 0.5 = indistinguishable. The pool is checked against the expert ids in the cache.
Usage: python replay_disc.py <results dir> stream [stream ...]   -> <stream>__micev1000_500.disc.pkl"""
import pickle, sys
import numpy as np
from sklearn.model_selection import cross_val_predict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import roc_auc_score
from run import TFM, MiceV1, fifo, DATA


def auc(Xa, Xb):
    Z = np.r_[Xa, Xb]; Z = (Z - Z.mean(0)) / (Z.std(0) + 1e-12)
    lab = np.r_[np.zeros(len(Xa)), np.ones(len(Xb))]
    s = cross_val_predict(KNeighborsClassifier(10), Z, lab, cv=2, method="predict_proba")[:, 1]
    return roc_auc_score(lab, s)


if __name__ == "__main__":
    d = sys.argv[1]
    for stream in sys.argv[2:]:
        c = pickle.load(open(f"{d}/{stream}__micev1000_500.pkl", "rb")); B = c["B"]
        z = np.load(f"{DATA}/{stream}.npz"); X, y = z["X"], z["y"].astype(int)
        pol = MiceV1(TFM(int(y.max()) + 1), 1000, seg=500)
        disc, bad = [], 0
        for st in c["cache"]:
            t = st["t"]; n = t * B
            while n - pol.closed >= pol.seg:
                pol._merge_or_add(X[pol.closed:pol.closed + pol.seg], y[pol.closed:pol.closed + pol.seg], t)
                pol.closed += pol.seg
            Xq = X[n:n + B]
            dd = {-w: auc(fifo(X, y, t, B, w)[0], Xq) for w in pol.windows if n >= 2 * 10}
            for e in pol.experts:
                dd[e["uid"]] = auc(e["X"], Xq)
            bad += set(k for k in st["P"] if k > 0) != set(e["uid"] for e in pol.experts)
            disc.append(dd)
        pickle.dump(disc, open(f"{d}/{stream}__micev1000_500.disc.pkl", "wb"))
        print(stream, "batches", len(disc), "pool mismatches", bad, flush=True)
