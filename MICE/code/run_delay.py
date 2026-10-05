"""Prequential evaluation with labels `d` batches late (d = 1 is the protocol of run.py): batch t is predicted from the
labelled prefix of (t - d + 1) * B rows. Writes
  <stream>__d<d>__fifo.npz, <stream>__d<d>__ddm.npz   baselines (same context budget M)
  <stream>__d<d>__mice.pkl   per batch: predictions of every in-context expert (windows of 100/300/M labelled rows,
                             keys -w; stored experts, keys uid > 0) and the label-free discrepancy between each expert's
                             context and the unlabelled batch (replay_disc.auc). Weighting rules are applied offline
                             (eval_delay.py), causally.
Usage: python run_delay.py --streams s1 s2 --delay 10 --out ../results_delay_dev"""
import argparse, os, pickle, time
import numpy as np
from run import TFM, MiceV1, DDMReset, fifo, DATA
from replay_disc import auc


def run(stream, d, B, M, out):
    tag = f"{out}/{stream}__d{d}__"
    z = np.load(f"{DATA}/{stream}.npz"); X, y, concept = z["X"], z["y"].astype(int), z["concept"]
    K, T = int(y.max()) + 1, len(y) // B
    f = TFM(K)
    for kind in ("fifo", "ddm"):
        if os.path.exists(tag + kind + ".npz"):
            continue
        acc, pol, preds, t0 = np.full(T, np.nan), DDMReset(M), {}, time.time()
        for t in range(d, T):
            tl = t - d + 1  # number of labelled batches
            if kind == "ddm" and tl - 1 in preds:  # labels of batch tl-1 have just arrived
                b = tl - 1
                pol.update((preds.pop(b) != y[b * B:(b + 1) * B]).astype(int), b + 1, B)
            Xc, yc = fifo(X, y, tl, B, M) if kind == "fifo" else pol.context(X, y, tl, B)
            P = f.predict(Xc, yc, X[t * B:(t + 1) * B]).argmax(1)
            preds[t] = P
            acc[t] = (P == y[t * B:(t + 1) * B]).mean()
        np.savez_compressed(tag + kind + ".npz", acc=acc, B=B, concept=concept, resets=np.array(pol.resets))
        print(stream, f"d={d}", kind, f"acc={np.nanmean(acc):.4f}", f"time={time.time() - t0:.0f}s", flush=True)
    if not os.path.exists(tag + "mice.pkl"):
        pol, cache, t0 = MiceV1(f, M, seg=500), [], time.time()
        for t in range(d, T):
            tl = t - d + 1; n = tl * B
            while n - pol.closed >= pol.seg:
                pol._merge_or_add(X[pol.closed:pol.closed + pol.seg], y[pol.closed:pol.closed + pol.seg], t)
                pol.closed += pol.seg
            Xq = X[t * B:(t + 1) * B]
            P, D = {}, {}
            for w in pol.windows:
                Xc, yc = fifo(X, y, tl, B, w)
                P[-w], D[-w] = f.predict(Xc, yc, Xq), auc(Xc, Xq)
            for e in pol.experts:
                P[e["uid"]], D[e["uid"]] = f.predict(e["X"], e["y"], Xq), auc(e["X"], Xq)
            cache.append(dict(t=t, P=P, disc=D))
        pickle.dump(dict(cache=cache, y=y, B=B, concept=concept, K=K, d=d), open(tag + "mice.pkl", "wb"))
        print(stream, f"d={d}", "mice cache", f"experts={len(pol.experts)}", f"time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--delay", type=int, default=1)
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--M", type=int, default=1000)
    ap.add_argument("--out", default="../results_delay_dev")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        run(s, a.delay, a.B, a.M, a.out)
