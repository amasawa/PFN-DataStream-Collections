"""All-or-nothing frozen confirmation; no model calls or parameter search."""
import copy
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score


def metrics(P, y):
    assert np.isfinite(P).all() and (P >= 0).all()
    assert np.allclose(P.sum(1), 1, atol=.002)
    P = P / P.sum(1, keepdims=True)
    predicted, confidence = P.argmax(1), P.max(1)
    correct = predicted == y
    bins = np.minimum((confidence * 15).astype(int), 14)
    ece = sum(np.mean(bins == b) * abs(correct[bins == b].mean()-confidence[bins == b].mean())
              for b in range(15) if (bins == b).any())
    valid = [k for k in range(P.shape[1]) if (y == k).any() and (y != k).any()]
    return dict(acc=100*correct.mean(), ll=-np.log(np.clip(P[np.arange(len(y)), y], 1e-6, 1)).mean(),
                f1=100*f1_score(y, predicted, average='macro', zero_division=0),
                auc=100*np.mean([roc_auc_score(y == k, P[:, k]) for k in valid]) if valid else np.nan,
                auc_classes=len(valid), classes=P.shape[1], ece=100*ece,
                brier=np.mean(np.sum((P-np.eye(P.shape[1])[y])**2, axis=1)))


def main(root):
    root = Path(root)
    for name, expected in json.loads((root/'freeze.json').read_text())['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected, name
    tasks = json.loads((root/'tasks.json').read_text())
    assert len(tasks) == 132
    assert all((root/'done'/(t['id']+'.json')).exists() for t in tasks), 'Incomplete: no partial verdict'
    sys.path.insert(0, str(root/'source/MICE'))
    import reweight
    entries = json.loads((root/'data_manifest.json').read_text())
    rows = []
    for seed in (0, 1, 2):
        for entry in entries:
            stream, T = entry['stream'], entry['rows']//100
            prefix = root/f'mice/s{seed}/{stream}__micev1000_500'
            with prefix.with_suffix('.pkl').open('rb') as handle:
                cache = pickle.load(handle)
            with np.load(root/f'duo/s{seed}/{stream}.npz') as duo, np.load(str(prefix)+'.npz') as mz:
                assert cache['B'] == 100 and len(cache['y']) == T*100
                np.testing.assert_array_equal(cache['y'], duo['y'].reshape(-1))
                assert [s['t'] for s in cache['cache']] == list(range(1, T))
                for t in range(1, T):
                    selected = duo['chosen'][t]; selected = selected[selected >= 0]
                    assert len(selected) == min(t, 10) and len(set(selected)) == len(selected)
                    assert selected.max() < t and selected.min() >= max(0, t-100) and t-1 in selected
                gap = max(np.abs(s['P'][-1000]-duo['P_fifo'][s['t']].astype(float)).max() for s in cache['cache'])
                assert gap < .002, (seed, stream, gap)
                aug = copy.copy(cache); aug['cache'] = []
                for s in cache['cache']:
                    P = duo['P_sel'][s['t']].astype(float)
                    assert np.isfinite(P).all() and np.allclose(P.sum(1), 1, atol=.002)
                    aug['cache'].append(dict(s, P={**s['P'], 'duo': P/P.sum(1, keepdims=True)}))
                row = dict(stream=stream, source=entry['source'], seed=seed, batches=T-1, fifo_gap=gap)
                y = cache['y'][100:]
                for name, c in (('mice', cache), ('method', aug)):
                    collected = []; start = time.perf_counter()
                    reweight.simulate2(c, outer='brier', scale=.5, temper=True, collect=collected)
                    row[name+'_replay_seconds'] = time.perf_counter()-start
                    row.update({name+'_'+k: v for k,v in metrics(np.concatenate([P for _,P in collected]), y).items()})
                row.update({'fifo_'+k: v for k,v in metrics(np.concatenate([s['P'][-1000] for s in cache['cache']]), y).items()})
                costs = {}
                for line in (root/'logs'/f'duo_s{seed}_{stream}.cost.jsonl').read_text().splitlines():
                    cost = json.loads(line); costs[cost['batch']] = cost
                assert set(costs) == set(range(1,T))
                row['mice_seconds_per_batch'] = mz['wt'][1:].mean()
                row['mice_logical_calls'] = int(mz['calls'])
                row['selection_seconds_per_batch'] = np.mean([v['seconds'] for v in costs.values()])
                for key in ('logical_calls', 'fits', 'forward_calls'):
                    row['selection_'+key] = sum(v[key] for v in costs.values())
                row['component_time_ratio'] = 1+row['selection_seconds_per_batch']/row['mice_seconds_per_batch']
                for kind in ('mice', 'duo'):
                    attempts = [json.loads(line) for line in
                                (root/'logs'/f'{kind}_s{seed}_{stream}.attempts.jsonl').read_text().splitlines()]
                    row[kind+'_attempt_seconds'] = sum(v['ended']-v['started'] for v in attempts)
                    row[kind+'_recorded_failed_attempts'] = sum(not v['success'] for v in attempts)
                    row[kind+'_peak_allocated_mib'] = max(v['peak_allocated_mib'] for v in attempts)
                row['d_mice'] = row['method_acc']-row['mice_acc']
                row['d_fifo'] = row['method_acc']-row['fifo_acc']
                row['d_ll'] = row['method_ll']-row['mice_ll']
                rows.append(row)
    result = pd.DataFrame(rows)
    verdicts = []
    for seed, r in result.groupby('seed'):
        checks = dict(per_stream_mice=bool((r.d_mice >= -.30).all()),
                      per_stream_fifo=bool((r.d_fifo >= -.30).all()),
                      mean_gain=bool(r.d_mice.mean() >= 0), logloss=bool(r.d_ll.mean() <= .005))
        verdicts.append(dict(seed=int(seed), **checks, passed=all(checks.values()),
                             gain=r.d_mice.mean(), worst_mice=r.d_mice.min(), worst_fifo=r.d_fifo.min(),
                             negative=int((r.d_mice < 0).sum()), ties=int((r.d_mice == 0).sum()),
                             d_ll=r.d_ll.mean()))
    out = root/'reports'
    result.to_csv(out/'heldout_results.csv', index=False)
    source = result.groupby(['seed','source']).mean(numeric_only=True).reset_index()
    source.to_csv(out/'heldout_sources.csv', index=False)
    source.groupby('seed').mean(numeric_only=True).to_csv(out/'heldout_source_means.csv')
    gpu = pd.read_csv(root/'gpu.csv')
    (out/'cost_notes.json').write_text(json.dumps(dict(
        device_peak_mib=int(gpu.gpu_mib.max()),
        timing='Component estimate, not deployed end-to-end latency. Model initialization excluded.',
        retries='Batch costs keep the last completed execution per batch; attempt times include replayed work. '
                'SIGKILL can prevent an attempt record; events.log is authoritative for all launches/failures.',
        concurrency=1), indent=2)+'\n')
    pd.DataFrame(verdicts).to_csv(out/'heldout_verdicts.csv', index=False)
    (out/'heldout.done').write_text(json.dumps(dict(passed=all(v['passed'] for v in verdicts),
                                                   verdicts=verdicts), indent=2)+'\n')
    print(pd.DataFrame(verdicts).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1])
