"""Causality, reference equivalence and exact restart checks without using a GPU."""
import importlib.util
from pathlib import Path
import tempfile

import numpy as np

import worker


class FakeTFM:
    def __init__(self, K=3): self.K = K
    def predict(self, Xc, yc, Xq):
        counts = np.bincount(yc, minlength=self.K).astype(float) + 1
        features = np.cos(Xq[:, 1:2] + np.arange(self.K)[None]) + 2
        p = features * counts[None]
        return p / p.sum(1, keepdims=True)


def main():
    repo = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='pfn-worker-test-') as directory:
        root = Path(directory)
        rng = np.random.default_rng(1)
        X = np.column_stack([np.arange(2400), rng.normal(size=2400)]).astype(np.float32)
        y = rng.integers(0, 3, size=2400)
        np.savez(root / 'toy.npz', X=X, y=y, concept=np.zeros(2400))
        for anchor in (1, 3, 5):
            task = dict(anchor=anchor, seed=0, id=f'a{anchor}')
            full = root / f'full{anchor}.npz'; resumed = root / f'resumed{anchor}.npz'
            assert worker.duo_run(task, root / 'toy.npz', full, FakeTFM(), root / 'progress.json')
            assert not worker.duo_run(task, root / 'toy.npz', resumed, FakeTFM(), root / 'progress.json', stop_after=13)
            assert worker.duo_run(task, root / 'toy.npz', resumed, FakeTFM(), root / 'progress.json')
            with np.load(full) as a, np.load(resumed) as b:
                for key in a.files: np.testing.assert_array_equal(a[key], b[key])
                for t in range(1, len(a['y'])):
                    chosen = a['chosen'][t]; chosen = chosen[chosen >= 0]
                    assert np.all(chosen < t)
                    assert set(range(max(0, t-anchor), t)).issubset(chosen)
            future_y = y.copy(); future_y[1700:] = (future_y[1700:] + 1) % 3
            assert worker.anchor_selection(FakeTFM(), X, y, 17, anchor) == worker.anchor_selection(FakeTFM(), X, future_y, 17, anchor)
        spec = importlib.util.spec_from_file_location('original_duo', repo / 'MiceDuo/code/check_duo.py')
        old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
        old.TFM = FakeTFM; old.DATA = str(root); old.OUT = str(root / 'original'); old.run('toy')
        with np.load(root / 'original/toy.npz') as a, np.load(root / 'full1.npz') as b:
            for method in ('fifo', 'sel', 'duo'):
                np.testing.assert_array_equal(a[f'P_{method}'], b[f'P_{method}'].astype(np.float16))
            np.testing.assert_array_equal(a['chosen'], b['chosen'])
            np.testing.assert_allclose(a['wsel'], b['weights'][:, 0], equal_nan=True)
        print('PASS: original DUO equivalence, exact checkpoint resume (3 anchors), no future-label selection')


if __name__ == '__main__': main()
