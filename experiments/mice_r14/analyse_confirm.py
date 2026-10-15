"""Registered evaluator of the round-14 confirmation set (PLAN_CONFIRM.md): 72 streams c_<regime>_c<nc>_s<seed>_o<k>
(seeds 50-53) in ~/pfn-runs/mice-r14-confirm. Criterion C1 exactly as in PLAN.md (per regime: mean(CP - reset) >= +1.0,
CP above reset on >= 18 of 24, hierarchical-bootstrap 95% lower bound > 0); descriptive: CP - fixed segmentation,
first five batches of recurring blocks, purity, detection. Uses the functions of analyse_test.py unchanged.
Usage: python analyse_confirm.py   (writes ../../MICE/results_paper/r14c_streams.csv, r14c_regimes.csv)"""
import glob
import os

import numpy as np
import pandas as pd

from analyse_test import OUT, RUNS, hier_lb, plain, pool, purity, recurring, segments

ROOT = f"{RUNS}/mice-r14-confirm"


def main():
    names = sorted(os.path.basename(f)[:-4] for f in glob.glob(f"{ROOT}/data/c_*.npz"))
    assert len(names) == 72, len(names)
    rows = []
    for s in names:
        concept = np.load(f"{ROOT}/data/{s}.npz")["concept"]
        acc = {}
        acc["cp"], _ = pool(f"{ROOT}/P/{s}__micecp1000_500.pkl")
        acc["mice"], _ = pool(f"{ROOT}/P/{s}__micev1000_500.pkl")
        acc["reset"] = plain(f"{ROOT}/P/{s}__ddm1000.npz")
        T = len(acc["cp"])
        assert all(len(v) == T for v in acc.values()), s
        rec = [t - 1 for t in recurring(concept) if 1 <= t <= T]
        r = dict(stream=s)
        for k, v in acc.items():
            r[k], r[k + "_rec"] = v.mean(), v[rec].mean()
        r["changes"], r["found"], r["false"] = segments(f"{ROOT}/P/{s}__micecp1000_500.npz", concept)
        pur = purity(f"{ROOT}/P/{s}__micecp1000_500.closes.pkl", concept)
        r["closes"], r["pure95"], r["major"], r["purity_mean"] = len(pur), (pur >= 0.95).sum(), (pur > 0.5).sum(), pur.mean()
        rows.append(r)
    d = pd.DataFrame(rows).set_index("stream")
    d.to_csv(f"{OUT}/r14c_streams.csv")
    reg_rows, c1 = [], True
    for reg in ("b500", "b2000", "bvar"):
        x = d[[s.split("_")[1] == reg for s in d.index]]
        assert len(x) == 24, reg
        dx = x.cp - x.reset
        lo, hi = hier_lb(dx)
        ok = dx.mean() >= 1.0 and (dx > 0).sum() >= 18 and lo > 0
        c1 &= ok
        reg_rows.append(dict(regime=reg, cp_reset=dx.mean(), lo=lo, hi=hi, above=int((dx > 0).sum()),
                             mice_reset=(x.mice - x.reset).mean(), cp_mice=(x.cp - x.mice).mean(), met=ok))
        print(f"C1 {reg}: mean(CP-reset) {dx.mean():+.3f} (>= +1.0), above {(dx > 0).sum()}/24 (>= 18), "
              f"hierarchical 95% [{lo:+.3f}, {hi:+.3f}] (lower > 0): {'met' if ok else 'not met'}; "
              f"fixed - reset {(x.mice - x.reset).mean():+.3f}")
    pd.DataFrame(reg_rows).to_csv(f"{OUT}/r14c_regimes.csv", index=False)
    print(f"C1 (confirmation, all three regimes): {'MET' if c1 else 'NOT MET'}")
    print(f"all 72: CP-reset {(d.cp - d.reset).mean():+.3f} above {(d.cp > d.reset).sum()}; fixed-reset "
          f"{(d.mice - d.reset).mean():+.3f}; CP-fixed {(d.cp - d.mice).mean():+.3f}; rec CP-reset "
          f"{(d.cp_rec - d.reset_rec).mean():+.2f} fixed-reset {(d.mice_rec - d.reset_rec).mean():+.2f}")
    print(f"purity: >=95% {d.pure95.sum() / d.closes.sum():.3f}, >50% {d.major.sum() / d.closes.sum():.3f}, "
          f"mean over streams of the per-stream mean {d.purity_mean.mean():.3f} (as in analyse_test.py); detection: changes {d.changes.sum()} found {d.found.sum()} false {d.false.sum()}")


if __name__ == "__main__":
    main()
