"""Held-out real streams (after pre-registration C; cache replay, no TFM call): does the margin condition of
theory_v2.tex (Lemma "Margin", Proposition "block") hold outside the synthetic grid? For every batch: gap g between the
best and second-best expert on the last labelled batch, weight of the leader (eta = 10), kappa = ln(1+(K-1)e^{-eta g}),
and whether the leader of the last labelled batch is still the best expert on the current batch."""
import glob, pickle, numpy as np, pandas as pd
rows = []
for f in sorted(glob.glob("../results_heldout/*__micev1000_500.pkl")):
    c = pickle.load(open(f, "rb")); cache, y, B = c["cache"], c["y"], c["B"]
    name = f.split("/")[-1].split("__")[0]
    for i in range(1, len(cache)):
        pv, st = cache[i - 1], cache[i]
        yb = y[pv["t"] * B:(pv["t"] + 1) * B]; yq = y[st["t"] * B:(st["t"] + 1) * B]
        keys = [u for u in st["P"] if u in pv["P"]]
        ll = lambda P, yy: -np.log(np.clip(P[np.arange(len(yy)), yy], 1e-6, 1)).mean()
        L = np.array([ll(pv["P"][u], yb) for u in keys]); Ln = np.array([ll(st["P"][u], yq) for u in keys])
        A = np.array([(st["P"][u].argmax(1) == yq).mean() for u in keys])
        w = np.exp(-10 * (L - L.min())); w /= w.sum(); k = L.argmin(); g = np.sort(L)[1] - L.min()
        mix = sum(wi * st["P"][u] for wi, u in zip(w, keys))
        rows.append(dict(stream=name, K=len(keys), gap=g, wmax=w.max(), kappa=np.log(1 + (len(keys) - 1) * np.exp(-10 * g)),
                         ll_mix_minus_leader=ll(mix, yq) - Ln[k], leader_ll_regret=Ln[k] - Ln.min(),
                         acc_mix=(mix.argmax(1) == yq).mean(), acc_leader=A[k], acc_best=A.max(), acc_M=A[keys.index(-1000)],
                         leader_is_pool=keys[k] > 0))
d = pd.DataFrame(rows); d.to_csv("../results_heldout/margin_real.csv", index=False)
pd.set_option("display.width", 220)
g = d.groupby("stream")
print(pd.DataFrame(dict(K=g.K.mean(), gap_median=g.gap.median(), gap_q25=g.gap.quantile(.25), frac_gap_ge_0_3=g.gap.apply(lambda x: (x >= 0.3).mean()),
                        w_leader_median=g.wmax.median(), frac_w_ge_0_9=g.wmax.apply(lambda x: (x >= 0.9).mean()), kappa_mean=g.kappa.mean(),
                        ll_mix_minus_leader=g.ll_mix_minus_leader.mean(), lemma_holds=g.apply(lambda x: (x.ll_mix_minus_leader <= x.kappa + 1e-9).mean()),
                        leader_ll_regret=g.leader_ll_regret.mean(), acc_mix=g.acc_mix.mean(), acc_leader=g.acc_leader.mean(),
                        acc_window_M=g.acc_M.mean(), acc_best=g.acc_best.mean(), leader_is_pool=g.leader_is_pool.mean())).round(3).T.to_string())
