"""Stream observation for contaminated labels (design: logs/EXPERIMENT_LOG.md, 2026-10-06). Self-contained.
Batches of B rows, labels one batch late, context budget M. The labels that enter the context and drive the detector
are the CONTAMINATED ones; accuracy is measured against the clean labels.
Policies: fifo | ddm (reset on the DDM rule, errors against the given labels) | pf (prequential filter: a row whose
given label had predicted probability < TAU and differs from the predicted class is not added) | pr (such a row is
added with the predicted class instead). Usage: python stream_obs.py <stream> [<stream> ...] -> ../results/stream/"""
import os, sys, time, warnings
import numpy as np

warnings.filterwarnings("ignore")
DATA, OUT = "../../MICE/data", "../results/stream"
B, M, NMAX, TAU = 100, 1000, 30_000, 0.2
CONDS, POLS = ("clean", "sym20", "burst"), ("fifo", "ddm", "pf", "pr")


class TFM:
    def __init__(self, K, seed=0):
        from tabpfn import TabPFNClassifier
        from tabpfn.constants import ModelVersion
        self.K = K
        self.m = TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=seed, n_estimators=4,
                                                             ignore_pretraining_limits=True)

    def predict(self, Xc, yc, Xq):
        P = np.zeros((len(Xq), self.K)); labs = np.unique(yc)
        if len(labs) == 1:
            P[:, labs[0]] = 1.0; return P
        self.m.fit(Xc, yc); P[:, self.m.classes_.astype(int)] = self.m.predict_proba(Xq); return P


def contaminate(y, cond, K, rng):
    yn = y.copy()
    if cond == "sym20":
        f = rng.random(len(y)) < 0.2; yn[f] = (y[f] + rng.integers(1, K, f.sum())) % K
    elif cond == "burst":
        c = np.bincount(y, minlength=K).argsort()[::-1]; lo, hi = int(0.4 * len(y)), int(0.6 * len(y))
        f = np.zeros(len(y), bool); f[lo:hi] = (y[lo:hi] == c[0]) & (rng.random(hi - lo) < 0.5); yn[f] = c[1]
    return yn


def run(stream, cond, pol):
    dst = f"{OUT}/{stream}__{cond}__{pol}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{DATA}/{stream}.npz"); X, y = np.nan_to_num(z["X"][:NMAX].astype(np.float32)), z["y"][:NMAX].astype(int)
    K, T = int(y.max()) + 1, len(y) // B
    yn = contaminate(y, cond, K, np.random.default_rng(7))
    f = TFM(K); cx, cy = np.zeros((0, X.shape[1]), np.float32), np.zeros(0, int)
    acc = np.full(T, np.nan); dropped = np.zeros(T); changed = np.zeros(T); wrong_in_ctx = np.full(T, np.nan); resets = []
    n = err = 0; pmin = smin = np.inf; P_prev = None; t0 = time.time()
    for t in range(1, T):
        lab = slice((t - 1) * B, t * B); Xl, yl = X[lab], yn[lab].copy(); keep = np.ones(B, bool)
        if P_prev is not None and pol in ("pf", "pr"):
            hat = P_prev.argmax(1); sus = (hat != yl) & (P_prev[np.arange(B), yl] < TAU)
            if pol == "pf":
                keep = ~sus; dropped[t] = sus.sum()
            else:
                yl[sus] = hat[sus]; changed[t] = sus.sum()
        if P_prev is not None and pol == "ddm":
            for e in (P_prev.argmax(1) != yl).astype(int):
                n += 1; err += e; p = err / n; s = np.sqrt(p * (1 - p) / n)
                if n >= 30 and p + s < pmin + smin:
                    pmin, smin = p, s
                if n >= 30 and p + s > pmin + 3 * smin:
                    resets.append(t); cx, cy = cx[:0], cy[:0]; n = err = 0; pmin = smin = np.inf; break
        cx, cy = np.r_[cx, Xl[keep]][-M:], np.r_[cy, yl[keep]][-M:]
        q = slice(t * B, (t + 1) * B)
        P_prev = f.predict(cx, cy, X[q]) if len(cy) else np.full((B, K), 1 / K)
        acc[t] = (P_prev.argmax(1) == y[q]).mean()
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(dst, acc=acc, dropped=dropped, changed=changed, resets=np.array(resets), noise=float((yn != y).mean()))
    print(stream, cond, pol, f"acc={np.nanmean(acc):.4f} resets={len(resets)} dropped={int(dropped.sum())} changed={int(changed.sum())} time={time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        for c in CONDS:
            for p in POLS:
                run(s, c, p)
