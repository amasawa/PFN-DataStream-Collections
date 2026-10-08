"""Verify instrumentation preserves causal predictions and checkpoint recovery, without a GPU."""
import importlib.util
import json
import hashlib
import pickle
import shutil
from pathlib import Path
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class FakeEstimator:
    def fit(self, X, y):
        self.counts = np.bincount(y, minlength=3)+1
        return self

    def predict_proba(self, X):
        p = (np.cos(X[:, :1]+np.arange(3))+2)*self.counts
        return p/p.sum(1, keepdims=True)


class FakeModel:
    def __init__(self):
        self.m, self.calls, self.K = FakeEstimator(), 0, 3

    def predict(self, X, y, q):
        self.m.fit(X,y)
        p = np.concatenate([self.m.predict_proba(q[i:i+1000]) for i in range(0,len(q),1000)])
        self.calls += 1
        return p


def main():
    base = load('base_worker', REPO/'experiments/night_20261007/worker.py')
    measured = load('heldout_worker', HERE/'heldout_worker.py')
    evaluate = load('heldout_evaluate', HERE/'evaluate.py')
    with tempfile.TemporaryDirectory() as d:
        root = Path(d); (root/'logs').mkdir()
        rng = np.random.default_rng(17)
        np.savez(root/'toy.npz', X=rng.normal(size=(2500,3)).astype(np.float32), y=rng.integers(0,3,2500))
        task = dict(id='toy', seed=0, anchor=1)
        assert base.duo_run(task,root/'toy.npz',root/'reference.npz',FakeModel(),root/'progress.json')
        measured.install_cost_recorder(root,'toy')
        assert not base.duo_run(task,root/'toy.npz',root/'actual.npz',FakeModel(),root/'progress.json',stop_after=13)
        assert base.duo_run(task,root/'toy.npz',root/'actual.npz',FakeModel(),root/'progress.json')
        with np.load(root/'reference.npz') as a, np.load(root/'actual.npz') as b:
            for key in a.files:
                np.testing.assert_array_equal(a[key],b[key])
            for t in range(1,25):
                chosen = b['chosen'][t]; assert np.all(chosen[chosen>=0] < t)
        costs = [json.loads(line) for line in (root/'logs/toy.cost.jsonl').read_text().splitlines()]
        assert [v['batch'] for v in costs] == list(range(1,25))
        for row in costs:
            t = row['batch']
            assert row['logical_calls'] == row['fits'] == (1 if t <= 10 else 2)
            assert row['forward_calls'] == (1 if t <= 10 else 1+int(np.ceil((t-1)/10)))
            assert row['seconds'] > 0
        perfect = evaluate.metrics(np.eye(3)[[0,1,2]], np.array([0,1,2]))
        assert perfect['acc'] == perfect['f1'] == perfect['auc'] == 100
        assert perfect['ll'] == perfect['ece'] == perfect['brier'] == 0
        # Exercise the entire evaluator on synthetic cache fixtures; reject incomplete queues.
        (root/'source/MICE').mkdir(parents=True)
        shutil.copy2(REPO/'MICE/code/reweight.py', root/'source/MICE/reweight.py')
        (root/'freeze.json').write_text(json.dumps({'files': {'source/MICE/reweight.py':
            hashlib.sha256((root/'source/MICE/reweight.py').read_bytes()).hexdigest()}}))
        (root/'done').mkdir(); (root/'reports').mkdir()
        tasks = [dict(id=f'{kind}_s{s}_toy{i}') for s in range(3) for i in range(22) for kind in ('mice','duo')]
        (root/'tasks.json').write_text(json.dumps(tasks))
        try:
            evaluate.main(root)
        except AssertionError as error:
            assert 'Incomplete' in str(error)
        else:
            raise AssertionError('Incomplete queue was accepted')
        entries = [dict(stream=f'toy{i}',source=f'group{i%4}', rows=300) for i in range(22)]
        (root/'data_manifest.json').write_text(json.dumps(entries))
        for task in tasks:
            (root/'done'/(task['id']+'.json')).write_text('{}')
            (root/'logs'/(task['id']+'.attempts.jsonl')).write_text(json.dumps(
                dict(started=0,ended=1,success=True,peak_allocated_mib=1))+'\n')
        for seed in range(3):
            (root/f'mice/s{seed}').mkdir(parents=True); (root/f'duo/s{seed}').mkdir(parents=True)
            for entry in entries:
                stream = entry['stream']; labels=np.arange(300)%3
                P = np.eye(3)[labels].reshape(3,100,3)
                cache = dict(B=100,y=labels,cache=[dict(t=t,P={-1000:P[t]}) for t in (1,2)])
                prefix = root/f'mice/s{seed}/{stream}__micev1000_500'
                with prefix.with_suffix('.pkl').open('wb') as handle:
                    pickle.dump(cache,handle)
                np.savez(str(prefix)+'.npz',wt=np.array([0,1,1]),calls=2)
                chosen=np.full((3,10),-1); chosen[1,0]=0; chosen[2,:2]=[0,1]
                np.savez(root/f'duo/s{seed}/{stream}.npz',y=labels.reshape(3,100),chosen=chosen,P_fifo=P,P_sel=P)
                (root/'logs'/f'duo_s{seed}_{stream}.cost.jsonl').write_text(''.join(json.dumps(dict(
                    batch=t,seconds=.5,logical_calls=1,fits=1,forward_calls=1))+'\n' for t in (1,2)))
        (root/'gpu.csv').write_text('gpu_mib\n100\n')
        evaluate.main(root)
        verdict=json.loads((root/'reports/heldout.done').read_text())
        assert verdict['passed'] and len(verdict['verdicts']) == 3
        assert all(v['gain'] == 0 and v['ties'] == 22 for v in verdict['verdicts'])
    print('PASS: unchanged predictions, exact resume, causal indices, selection-only cost counts, metric sanity')
    print('PASS: incomplete-queue rejection and all 132 synthetic fixture tasks evaluated with expected verdicts')


if __name__ == '__main__':
    main()
