"""TKDE round 11 (registered in experiments/mice_tkde_control/PLAN.md, "Round 11 addition"): direct test of the
magnitude in Theorem 1. On the grid streams, with oracle concept boundaries and identities, compare
  R  relearning: reset at the block boundary (FIFO over the last M rows before any label of the block arrives),
  S  the stored expert of the concept: its last n_c = min(M, (c-1)L) rows from earlier visits,
  X  the theorem's mixture of {S, R}: weights ~ exp(-eta * log-loss on the last labelled batch), eta = 10.
Every stream is written atomically to RUN/<stream>.csv (one row per batch) and skipped if present, so a failed
process is rerun from the streams already done. `--summary` writes ../results_grid_test/oracle_recall.csv and
oracle_recall_summary.csv and evaluates H1 and H2."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from grid_streams import stream

B, M, ETA, NCLS = 100, 1000, 10.0, 4
RUN = os.path.expanduser("~/pfn-runs/mice_oracle_r11")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results_grid_test")
CELLS = [(nc, L) for nc in (5, 30, 100) for L in (500, 2000)]


def logloss(P, y):
    return -np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean()


def run_stream(f, nc, L, seed):
    X, y, con = stream(nc, L, seed)
    J, nblocks = L // B, len(y) // L
    pred = lambda ctx, q: (f.predict(X[ctx], y[ctx], X[q]) if len(ctx)
                           else np.full((len(q), NCLS), 1.0 / NCLS))
    rows, prev_R = [], None          # prev_R: (query indices, prediction) issued by R on the previous batch
    for b in range(nblocks):
        start, k = b * L, con[b * L]
        earlier = [i for i in range(b) if con[i * L] == k]
        visit = len(earlier) + 1
        S_ctx = np.concatenate([np.arange(i * L, (i + 1) * L) for i in earlier])[-min(M, (visit - 1) * L):] \
            if earlier else None
        for j in range(1, J + 1):
            q = np.arange(start + (j - 1) * B, start + j * B)
            R_ctx = np.arange(max(0, start - M), start) if j == 1 else \
                np.arange(start + max(0, (j - 1) * B - M), start + (j - 1) * B)
            PR = pred(R_ctx, q)
            if S_ctx is None or prev_R is None:
                PS, PX, wS = None, PR, 0.0
            else:
                PS = pred(S_ctx, q)
                q_prev, PR_prev = prev_R                     # last labelled batch, out of sample for both experts
                lS, lR = logloss(pred(S_ctx, q_prev), y[q_prev]), logloss(PR_prev, y[q_prev])
                w = np.exp(-ETA * (np.array([lS, lR]) - min(lS, lR)))
                wS = w[0] / w.sum()
                PX = wS * PS + (1 - wS) * PR
            acc = lambda P: float((P.argmax(1) == y[q]).mean())
            rows.append(dict(n_centroids=nc, block=L, seed=seed, b=b, concept=k, visit=visit, j=j,
                             acc_R=acc(PR), acc_S=np.nan if PS is None else acc(PS), acc_X=acc(PX), w_S=wS))
            prev_R = (q, PR)
    return pd.DataFrame(rows)


def summary():
    need = [f"c{nc}_b{L}_s{seed}.csv" for seed in (40, 41, 20, 21) for nc, L in CELLS]
    missing = [f for f in need if not os.path.exists(f"{RUN}/{f}")]
    assert not missing, f"refusing summary, missing streams: {missing}"
    d = pd.concat([pd.read_csv(f"{RUN}/{f}") for f in need])
    assert (d.groupby(["n_centroids", "block", "seed"]).b.nunique() == 9).all(), "a stream has != 9 blocks"
    d.to_csv(f"{OUT}/oracle_recall.csv", index=False)
    J = d.block // B
    d["dX"] = 100 * (d.acc_X - d.acc_R) / J
    d["dI"] = 100 * (np.fmax(d.acc_S, d.acc_R) - d.acc_R) / J       # fmax: S is NaN on first visits -> R
    per_block = d.groupby(["n_centroids", "block", "seed", "b"]).apply(
        lambda g: pd.Series(dict(area=g.dX[g.j >= 2].sum(), zeta=g.dX[g.j == 1].sum(), ideal=g.dI[g.j >= 2].sum())),
        include_groups=False).reset_index()
    per_seed = per_block.groupby(["n_centroids", "block", "seed"])[["area", "zeta", "ideal"]].mean().reset_index()
    pv = pd.read_csv(f"{OUT}/predicted_indep.csv").rename(columns=dict(centroids="n_centroids"))
    res = []
    for seeds, tag in (((40, 41), "primary_s40_41"), ((20, 21), "secondary_s20_21")):
        s = per_seed[per_seed.seed.isin(seeds)].groupby(["n_centroids", "block"])[["area", "zeta", "ideal"]].mean()
        s = s.reset_index().merge(pv[["n_centroids", "block", "indep_visit_specific", "observed_mice_s20_21"]])
        assert len(s) == 6, f"{tag}: {len(s)} of 6 cells after merge with predicted_indep.csv"
        s.insert(0, "seeds", tag)
        res.append(s)
    r = pd.concat(res).rename(columns=dict(indep_visit_specific="predicted"))
    r["abs_err"] = (r.area - r.predicted).abs()
    r["abs_err_ideal"] = (r.ideal - r.predicted).abs()          # descriptive: oracle identification vs prediction
    r.to_csv(f"{OUT}/oracle_recall_summary.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.round(3).to_string(index=False))
    p = r[r.seeds == "primary_s40_41"]
    n_ok, mae, rho = int((p.abs_err <= 1.0).sum()), p.abs_err.mean(), p.area.corr(p.predicted, method="spearman")
    print(f"H1: |area - predicted| <= 1.0 on {n_ok}/6 cells (need >= 5), mean abs diff {mae:.3f} (need <= 0.5) -> "
          f"{'HOLDS' if n_ok >= 5 and mae <= 0.5 else 'FAILS'}")
    print(f"H2: Spearman {rho:.3f} (need >= 0.8) -> {'HOLDS' if rho >= 0.8 else 'FAILS'}")
    print(f"descriptive: |ideal - predicted| <= 1.0 on {int((p.abs_err_ideal <= 1.0).sum())}/6, mean "
          f"{p.abs_err_ideal.mean():.3f}, Spearman {p.ideal.corr(p.predicted, method='spearman'):.3f}; "
          f"identification loss ideal - area mean {(p.ideal - p.area).mean():.3f}")
    s2 = r[r.seeds == "secondary_s20_21"]
    print("seeds 20, 21: deployed MICE - DDM (points, run.py scores batches >= 1) vs oracle area + zeta (all batches; "
          "batch 0 contributes 0); remainder = delay, identification, slow level")
    print(pd.DataFrame(dict(n_centroids=s2.n_centroids, block=s2.block, mice_minus_ddm=s2.observed_mice_s20_21,
                            oracle=s2.area + s2.zeta,
                            remainder=s2.observed_mice_s20_21 - s2.area - s2.zeta)).round(3).to_string(index=False))


if __name__ == "__main__":
    if "--summary" in sys.argv:
        summary()
        sys.exit()
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn", "registered backbone is TabPFN v2"
    from run import TFM
    os.makedirs(RUN, exist_ok=True)
    f = TFM(NCLS, 0)
    seeds = [int(a) for a in sys.argv[1:]] or [40, 41, 20, 21]     # one worker per seed subset; no shared streams
    for seed in seeds:
        for nc, L in CELLS:
            out = f"{RUN}/c{nc}_b{L}_s{seed}.csv"
            if os.path.exists(out):
                continue
            df = run_stream(f, nc, L, seed)
            df.to_csv(out + ".tmp", index=False)
            os.replace(out + ".tmp", out)
            print(out, f"X-R {100 * (df.acc_X - df.acc_R).mean():+.2f}", flush=True)
