"""TKDE round 8: the disclosure numbers of app:grid, computed from the generator (no TFM call).
(1) identical rows (bit-identical float32 feature vectors) between the registered learning-curve data
    (grid_streams.stream(m, 4000, seed, cycles=1)) and each evaluated grid stream of seeds 10 and 11; they arise
    where the two NumPy draw sequences of the same seed realign, in runs at a constant offset;
(2) the independent curve rows of learning_curve_indep.py share no row with any grid stream of seeds 10, 11, 20, 21;
(3) per seed and m: classes present per concept, and the weight of centroids with equal labels for a pair of concepts.
Writes ../results_grid_test/grid_overlap_check.txt."""
import numpy as np

from grid_streams import stream
from learning_curve_indep import concept_rows

out = []
for seed in (10, 11):
    for m in (5, 30, 100):
        Xc, _, _ = stream(m, 4000, seed, cycles=1)
        pos = {bytes(r): i for i, r in enumerate(Xc)}
        for L in (500, 2000):
            Xg, _, _ = stream(m, L, seed)
            hit = [(i, pos[bytes(r)]) for i, r in enumerate(Xg) if bytes(r) in pos]
            offs = sorted({b - a for a, b in hit})
            out.append(f"identical rows seed {seed} m {m} L {L}: {len(hit)}" + (f" (offsets {offs[:4]})" if hit else ""))
new = {bytes(r) for s in (10, 11) for m in (5, 30, 100) for k in range(3) for r in concept_rows(m, s, k, 4000)[0]}
cnt = sum(bytes(r) in new for s in (10, 11, 20, 21) for m in (5, 30, 100) for L in (500, 2000) for r in stream(m, L, s)[0])
out.append(f"independent curve rows found in grid streams of seeds 10, 11, 20, 21: {cnt}")
for seed in (10, 11, 20, 21):
    for m in (5, 30, 100):
        rng = np.random.default_rng(seed)
        rng.uniform(0, 1, size=(m, 10)); w = rng.uniform(size=m); w /= w.sum()
        lab = [rng.integers(4, size=m) for _ in range(3)]
        X, y, c = stream(m, 500, seed)
        present = [len(np.unique(y[c == k])) for k in range(3)]
        agree = [(w * (lab[a] == lab[b])).sum() for a, b in ((0, 1), (0, 2), (1, 2))]
        out.append(f"seed {seed} m {m}: classes present {present}; equal-label weight per pair "
                   f"{[round(a, 2) for a in agree]} (mean {np.mean(agree):.2f})")
open("../results_grid_test/grid_overlap_check.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
