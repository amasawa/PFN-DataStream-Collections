"""Drift-Resilient TabPFN (Helli et al., NeurIPS 2024) as a Table 1 baseline (PLAN_BASELINES.md). Official package
(~/ext-baselines/Drift-Resilient_TabPFN, commit a6e75af, venv ~/pfn-venvs/drtabpfn), model tabpfn_dist_model_1 loaded
as in the official demo notebook (get_best_tabpfn, task_type dist_shift_multiclass, model_type best_dist), default
inference settings, seed 0 (the notebook sets 1; the paper protocol of Table 1 uses 0).
Batch t >= 1: context = the M = 1000 most recent labelled rows (batches < t), dist_shift_domain = batch index minus the
batch index of the oldest context row (the model min-max scales it per call); one fit + predict_proba per batch.
A context with a single class predicts that class with probability 1 (counted in n_single). Batch 1 (context = batch 0
only, a single domain, which the model cannot use: it drops the constant domain feature and fails) uses the two halves of
batch 0 as domains 0 and 1, test domain 2. Raw features (the package
preprocesses them). Stateless across batches: a checkpoint of the probabilities is written every 25 batches
(atomically) and a restarted process resumes from it, with identical results.
Output <out>/<stream>__drtabpfn.npz: acc (per batch, NaN at 0), pred, P (float32, rows of batches 1..T-1), C, B, wt,
te (absolute end time of every batch, for matching against the Windows driver-event log; amendment c).
Usage: python run_drtabpfn.py --data <dir> --out <dir> --streams s1 s2 ..."""
import argparse, os, time
from importlib import resources
import numpy as np
import torch
import tabpfn
from tabpfn.best_models import get_best_tabpfn, TabPFNModelPathsConfig

M, CKPT = 1000, 25


def get_model():
    lib = resources.files(tabpfn)
    cfg = TabPFNModelPathsConfig(paths=[f"{lib}/model_cache/tabpfn_dist_model_1.cpkt"], task_type="dist_shift_multiclass")
    m = get_best_tabpfn(task_type="dist_shift_multiclass", model_type="best_dist", paths_config=cfg, debug=False, device="auto")
    m.show_progress = False
    m.seed = 0
    return m


def run(model, data, stream, B, out):
    dst = f"{out}/{stream}__drtabpfn.npz"
    if os.path.exists(dst):
        return
    z = np.load(f"{data}/{stream}.npz"); X, y = z["X"].astype(np.float32), z["y"].astype(int)
    C, T = int(y.max()) + 1, len(y) // B
    acc, wt, te = np.full(T, np.nan), np.zeros(T), np.zeros(T)   # te: absolute end time of each batch (FECS matching)
    P = np.zeros(((T - 1) * B, C), np.float32); n_single = 0; n_retry = 0; t0_ = 1
    ck = f"{out}/{stream}__drtabpfn.ckpt.npz"
    if os.path.exists(ck):
        c = np.load(ck); t0_ = int(c["t"]); P[:len(c["P"])] = c["P"]; acc[:t0_] = c["acc"][:t0_]; wt[:t0_] = c["wt"][:t0_]
        if "te" in c.files:                              # checkpoints written before amendment c have no te
            te[:t0_] = c["te"][:t0_]
        n_single, n_retry = int(c["n_single"]), int(c["n_retry"]); print(stream, "drtabpfn resumed at batch", t0_, flush=True)
    for t in range(t0_, T):
        ts = time.time(); lo = max(0, t * B - M)
        Xc, yc = X[lo:t * B], y[lo:t * B]; dom = np.arange(lo, t * B) // B - lo // B; dt = t - lo // B
        if t == 1:   # one context batch = one domain: the model drops the constant domain feature and fails;
            dom = (np.arange(B) >= B // 2).astype(int); dt = 2   # batch 1 only: its two halves as two domains
        r = slice((t - 1) * B, t * B)
        labs = np.unique(yc)
        if len(labs) == 1:
            P[r] = 0; P[r, labs[0]] = 1; n_single += 1
        else:
            for k in range(4):   # the official select_features fails at random on some calls (shape error, not a CUDA
                try:             # fault); the batch is redone with the next seed, counted in n_retry
                    model.seed = k
                    model.fit(Xc, yc, additional_x={"dist_shift_domain": torch.tensor(dom, dtype=torch.float32)})
                    p = model.predict_proba(X[t * B:(t + 1) * B], additional_x={"dist_shift_domain": torch.full((B,), float(dt))})
                    break
                except RuntimeError as e:
                    if "expanded size of the tensor" not in str(e) or k == 3:
                        raise
                    n_retry += 1
            model.seed = 0
            cls = np.asarray(model.classes_).astype(int)
            assert p.shape == (B, len(cls)), (p.shape, cls)
            Q = np.zeros((B, C), np.float32); Q[:, cls] = p; P[r] = Q
        acc[t] = (P[r].argmax(1) == y[t * B:(t + 1) * B]).mean(); wt[t] = time.time() - ts; te[t] = time.time()
        if t % CKPT == 0 and t < T - 1:
            tmp = ck[:-4] + ".tmp.npz"
            np.savez(tmp, t=t + 1, P=P[:t * B], acc=acc, wt=wt, te=te, n_single=n_single, n_retry=n_retry); os.replace(tmp, ck)
    tmp = dst[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, acc=acc, pred=P.argmax(1), P=P, C=C, B=B, wt=wt, te=te, n_single=n_single, n_retry=n_retry,
                        peak_mem=torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0)
    os.replace(tmp, dst)
    if os.path.exists(ck):
        os.remove(ck)
    print(stream, "drtabpfn", f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", f"single={n_single}", f"retry={n_retry}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--B", type=int, default=100)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    model = get_model()
    for s in a.streams:
        run(model, a.data, s, a.B, a.out)
