"""CURE (context management via uncertainty-aware admission and redundancy-aware eviction; arXiv 2606.18677) as a
Table 1 baseline (phase P4 of the clean rerun). Memory policy: the official CUREMemoryPolicy, imported unchanged from
~/ext-baselines/CURE-ICML-FMSD (commit f7c6b2f) through its build_cure_policy, with its defaults budget_B = 1000
(= M of every Table 1 policy) and short_ratio = 0.75; tau (entropy_threshold) from --tau.
Backbone: the Table 1 backbone, MICE/code/run.py TFM (TabPFN v2, 4 estimators, seed 0).
Protocol of Table 1 (B = 100, labels one batch late, batch 0 warm-up and not scored). CURE itself predicts one row and
appends it at once; here labels arrive per batch, so:
  batch t >= 1 is predicted from memory.arrays() (one call per batch); after scoring, its rows are appended in stream
  order, each with CURE's record_prediction_signal(probs = the probabilities predicted for that row over the classes
  of the context, renormalised) and then append_then_evict. The entropy is thus normalised by the number of context
  classes, as with CURE's TabICL (predict_proba over classes_). The rows of batch 0 are appended with no signal
  (entropy 0), as CURE's own warm-up rows; a one-class context gives entropy 0 (one column), as CURE's runner (no
  prediction when the memory has one class).
Output <out>/<stream>__cure_tau<tau>.npz: acc (per batch, NaN at 0), pred, P (float32, rows of batches 1..T-1), C, B,
wt, te, peak_mem, and per batch: mem (memory size before prediction), short, long (sizes after the append), left
(rows that left the short memory), gate (rows dropped by the entropy gate), warm (rows admitted while warm-fill
bypassed the gate), tau, calls (backbone calls). Admitted by the gate = left - gate - warm. A checkpoint (memory state, arrays) every 25 batches,
written atomically; a restarted process resumes from it with identical results.
Usage: python run_cure.py --data <dir> --out <dir> --tau 0.3 --streams s1 s2 ..."""
import argparse, os, pickle, sys, time
import numpy as np

CURE = os.path.expanduser(os.environ.get("CURE_ROOT", "~/ext-baselines/CURE-ICML-FMSD"))
sys.path.insert(0, CURE)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
from src.stream.memory import build_cure_policy   # noqa: E402
import run                                         # noqa: E402  (MICE/code/run.py: TFM, the Table 1 backbone)

M, SHORT, CKPT = 1000, 0.75, 25


def append_batch(mem, Xb, yb, t0, Pb=None):
    """Append the rows of one batch in stream order; Pb[i] = probabilities predicted for row i (None: no signal).
    Returns (left, gate, warm) for the batch."""
    left = gate = warm = 0
    labs = np.unique(mem.labels()) if Pb is not None else None
    for i in range(len(yb)):
        if Pb is None:
            mem.record_prediction_signal(y_true=int(yb[i]), y_pred=None, probs=None)
        else:
            p = Pb[i, labs].astype(np.float64); p = p / p.sum()
            mem.record_prediction_signal(y_true=int(yb[i]), y_pred=int(labs[p.argmax()]), probs=p)
        s0, l0 = mem.short_size(), mem.long_size()
        bypass = l0 < int(round(mem.long_capacity * mem.warm_fill_ratio))
        ev = mem.append_then_evict(np.asarray(Xb[i], np.float32), int(yb[i]), t0 + i)
        out = s0 + 1 - mem.short_size()                     # rows that left the short memory at this append (0 or 1)
        # invariant of CUREMemoryPolicy.append_then_evict (f7c6b2f): a gate drop adds 1 timestamp and no index, a long-bank
        # eviction 1 timestamp and 1 index; at most one row leaves the short memory per append
        g = len(ev.evicted_timestamps) - len(ev.evicted_indices)
        left += out; gate += g; warm += (out - g) if bypass else 0
    return left, gate, warm


def run_stream(data, stream, B, out, tau):
    tag = f"cure_tau{tau:g}"
    dst = f"{out}/{stream}__{tag}.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{data}/{stream}.npz"); X, y = z["X"].astype(np.float32), z["y"].astype(int)
    C, T = int(y.max()) + 1, len(y) // B
    f = run.TFM(C)                                          # one backbone per stream, as run.py
    acc, wt, te = np.full(T, np.nan), np.zeros(T), np.zeros(T)
    stats = np.zeros((T, 6), np.int64)                       # mem, short, long, left, gate, warm
    P = np.zeros(((T - 1) * B, C), np.float32)
    ck = f"{out}/{stream}__{tag}.ckpt.pkl"
    if os.path.exists(ck):
        with open(ck, "rb") as fh:
            c = pickle.load(fh)
        assert (c["B"], c["tau"]) == (B, tau), ("checkpoint of another run", c["B"], c["tau"])
        mem, t0_ = c["mem"], c["t"]; P[:len(c["P"])] = c["P"]; acc, wt, te, stats = c["acc"], c["wt"], c["te"], c["stats"]; f.calls = c["calls"]
        print(stream, tag, "resumed at batch", t0_, flush=True)
    else:
        mem = build_cure_policy(budget_B=M, short_ratio=SHORT, entropy_threshold=tau, seed=0)
        stats[0, 3:] = append_batch(mem, X[:B], y[:B], 0)        # batch 0: warm-up, no prediction, no signal
        stats[0, 1:3] = mem.short_size(), mem.long_size(); t0_ = 1
    for t in range(t0_, T):
        ts = time.time(); r = slice((t - 1) * B, t * B); q = slice(t * B, (t + 1) * B)
        Xm, ym = mem.arrays(); stats[t, 0] = len(ym)
        P[r] = f.predict(Xm, ym, X[q])
        acc[t] = (P[r].argmax(1) == y[q]).mean()
        stats[t, 3:] = append_batch(mem, X[q], y[q], t * B, P[r])
        stats[t, 1:3] = mem.short_size(), mem.long_size()
        wt[t] = time.time() - ts; te[t] = time.time()
        if t % CKPT == 0 and t < T - 1:
            with open(ck + ".tmp", "wb") as fh:
                pickle.dump(dict(mem=mem, t=t + 1, P=P[:t * B], acc=acc, wt=wt, te=te, stats=stats, calls=f.calls, B=B,
                                 tau=tau), fh)
            os.replace(ck + ".tmp", ck)
    import torch
    tmp = dst[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, acc=acc, pred=P.argmax(1), P=P, C=C, B=B, wt=wt, te=te, tau=tau,
                        mem=stats[:, 0], short=stats[:, 1], long=stats[:, 2], left=stats[:, 3], gate=stats[:, 4],
                        warm=stats[:, 5], calls=f.calls,
                        peak_mem=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0)
    os.replace(tmp, dst)
    if os.path.exists(ck):
        os.remove(ck)
    adm = stats[1:, 3].sum() - stats[1:, 4].sum() - stats[1:, 5].sum()
    print(stream, tag, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s",
          f"admitted_by_gate={adm}/{max(1, stats[1:, 3].sum() - stats[1:, 5].sum())}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--tau", type=float, required=True); ap.add_argument("--streams", nargs="+")
    ap.add_argument("--B", type=int, default=100)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        run_stream(a.data, s, a.B, a.out, a.tau)
