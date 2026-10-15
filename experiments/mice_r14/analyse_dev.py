"""Round 14 development: accuracy (%) of MICE (original), MICE-CP, archive and archive-CP replayed with the paper's
two-level rule (reweight.simulate2(outer="brier", scale=0.5, temper=True)), DDM-reset from its per-batch accuracy;
mean over batches 1..T-1 and over the first five batches of each recurring block (blocks 4-9). Development streams
only. Usage: python analyse_dev.py <root>"""
import glob
import os
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import reweight  # noqa: E402

POOL = {"mice": "micev1000_500", "cp": "micecp1000_500", "arch": "arch1000_500", "archcp": "archcp1000_500"}


def recurring(concept, B, K=3, first=5):
    starts = np.flatnonzero(np.r_[True, concept[1:] != concept[:-1]])
    return sorted({b for r in starts[K:] for b in range(-(-r // B), -(-r // B) + first)})


def main(root):
    rows = []
    for f in sorted(glob.glob(f"{root}/data/*.npz")):
        s = os.path.basename(f)[:-4]
        concept = np.load(f)["concept"]
        T = len(concept) // 100
        acc = {}
        for k, m in POOL.items():
            p = f"{root}/P/{s}__{m}.pkl"
            if os.path.exists(p):
                a = reweight.simulate2(pickle.load(open(p, "rb")), outer="brier", scale=0.5, temper=True)
                acc[k] = np.array([a.get(t, np.nan) for t in range(T)])
        p = f"{root}/P/{s}__ddm1000.npz"
        if os.path.exists(p):
            acc["reset"] = np.load(p)["acc"]
        if "cp" not in acc or "reset" not in acc:
            continue
        rec = [t for t in recurring(concept, 100) if t < T]
        r = dict(stream=s)
        for k, a in acc.items():
            r[k] = 100 * np.nanmean(a[1:])
            r[k + "_rec"] = 100 * np.nanmean(a[rec])
        rows.append(r)
    d = pd.DataFrame(rows).set_index("stream")
    for k in ("mice", "cp", "arch", "archcp"):
        if k in d:
            d[f"{k}-reset"] = d[k] - d["reset"]
    if "mice" in d:
        d["cp-mice"] = d["cp"] - d["mice"]
    if "archcp" in d:
        d["cp-archcp"] = d["cp"] - d["archcp"]
    cols = [c for c in ("mice-reset", "cp-reset", "arch-reset", "archcp-reset", "cp-mice", "cp-archcp") if c in d]
    pd.set_option("display.width", 200)
    print(d[cols].round(2).to_string())
    print(d[cols].mean().round(2).to_string())
    d.to_csv(f"{root}/dev_summary.csv")


if __name__ == "__main__":
    main(sys.argv[1])
