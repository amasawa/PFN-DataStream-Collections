"""Round 14 development: offline evaluation of the change-point segmentation (run.CPSegments._segment) from the cached
window predictions of the original MICE runs on the development streams (windows do not depend on the pool, so the
segments are exactly those an online MiceCP run would close). Reports, per stream and setting: detected cuts, true
changes found within H batches, false cuts, purity of the closed segments (share of rows of the segment's majority
concept), share of stored rows in mixed segments (< 0.95 purity), against the fixed 500-row segmentation.
Usage: python tune_detector.py <root> [SIG,H,R,RMIN,DELTA_CP,LMIN ...]"""
import glob
import os
import pickle
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import run  # noqa: E402


class Sim(run.CPSegments):
    def __init__(self, seg, prm):
        (self.SIG, self.H, self.R, self.RMIN, self.DELTA_CP, self.LMIN) = prm
        self.seg, self.closed, self.err, self.ref0, self.cuts, self.segs, self.closes = seg, 0, {}, 1, [], [], []

    def _merge_or_add(self, Xs, ys, now):
        self.segs.append((self.closed, self.closed + len(ys)))


def evaluate(f, prm, seg=500):
    c = pickle.load(open(f, "rb"))
    assert f.endswith(f"_{seg}.pkl") and prm[0] in (100, 300, 1000), (f, prm)   # SIG must be a cached window
    B = c["B"]
    y, concept, T = c["y"], c["concept"], len(c["y"]) // B
    P = {st["t"]: st["P"][-prm[0]] for st in c["cache"]}
    sim = Sim(seg, prm)
    for t in range(1, T):
        if t - 1 in P:
            sim.err[t - 1] = int((P[t - 1].argmax(1) != y[(t - 1) * B:t * B]).sum())
        sim._segment(_Rows(), _Rows(), t, B)
    changes = np.flatnonzero(concept[1:] != concept[:-1]) + 1
    det = [b * B for _, b in sim.cuts]
    found = sum(any(0 <= d - ch < sim.H * B + B for d in det) for ch in changes)
    false = sum(not any(0 <= d - ch < sim.H * B + B for ch in changes) for d in det)
    pur = np.array([np.bincount(concept[a:b]).max() / (b - a) for a, b in sim.segs])
    rows = np.array([b - a for a, b in sim.segs])
    fixed = [(a, a + seg) for a in range(0, T * B - seg + 1, seg)]
    fpur = np.array([np.bincount(concept[a:b]).max() / (b - a) for a, b in fixed])
    return dict(changes=len(changes), found=found, false=false, segs=len(sim.segs),
                mixed_rows=float(rows[pur < 0.95].sum() / rows.sum()) if len(rows) else 0.0,
                fixed_mixed=float((fpur < 0.95).mean()), minpur=float(pur.min()) if len(pur) else 1.0)


class _Rows:
    """Stand-in for X and y: slicing returns a range object whose length is the number of rows."""
    def __getitem__(self, s):
        return range(s.start, s.stop)


if __name__ == "__main__":
    root = sys.argv[1]
    settings = [tuple(float(v) if "." in v else int(v) for v in a.split(",")) for a in sys.argv[2:]] or \
        [tuple(getattr(run.CPSegments, k) for k in ("SIG", "H", "R", "RMIN", "DELTA_CP", "LMIN"))]
    files = sorted(glob.glob(f"{root}/P/*__micev1000_500.pkl"))
    for prm in settings:
        print("setting SIG,H,R,RMIN,DELTA_CP,LMIN =", prm)
        tot = dict(changes=0, found=0, false=0)
        for f in files:
            r = evaluate(f, prm)
            for k in tot:
                tot[k] += r[k]
            print(f"  {os.path.basename(f).split('__')[0]:24s} " + " ".join(
                f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()))
        print("  TOTAL", tot)
