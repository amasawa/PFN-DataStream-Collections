"""Fresh synthetic streams with controlled concept recurrence (PLAN_mechanism.md). Writes to <root>/data."""
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'MICE/code'))
from grid_streams import stream  # noqa: E402  (unchanged MICE generator)

LEVELS = {'k3': (3, 5), 'k5': (5, 3), 'k15': (15, 1)}  # K concepts, cycles; always 15 blocks
CENTROIDS, SEEDS, BLOCK = (30, 100), (30, 31, 32), 2000


def names():
    return [f'mech_{lvl}_c{nc}_s{s}' for lvl in LEVELS for nc in CENTROIDS for s in SEEDS]


def main(root):
    out = Path(root) / 'data'
    out.mkdir(parents=True, exist_ok=True)
    for name in names():
        lvl, c, s = name.split('_')[1:]
        K, cycles = LEVELS[lvl]
        X, y, concept = stream(int(c[1:]), BLOCK, int(s[1:]), K=K, cycles=cycles)
        assert len(y) == 30000 and len(np.unique(concept)) == K
        np.savez_compressed(out / f'{name}.npz', X=X, y=y, concept=concept)
        print(name, X.shape, np.bincount(y), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
