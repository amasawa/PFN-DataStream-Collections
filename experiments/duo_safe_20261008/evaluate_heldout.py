"""Frozen evaluation of PLAN_heldout.md. No model calls; reads caches written by the GPU runs."""
import copy
import json
from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT = Path.home() / 'pfn-runs/duo-heldout-20261008'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source/MICE'))
import reweight  # noqa: E402

STREAMS = (['insects_abrupt_balanced', 'insects_gradual_balanced', 'insects_incremental_balanced',
            'insects_incremental_reoccurring_balanced', 'covertype', 'insects_abrupt_imbalanced',
            'insects_gradual_imbalanced', 'insects_incremental_abrupt_balanced']
           + [f'h3_{a}_{b}' for a in ('airlines', 'covertype', 'insects', 'poker') for b in 'bc']
           + [f'h4_{a}_{b}' for a in ('airlines', 'covertype', 'poker') for b in 'de'])
SEEDS = (1, 2)


def family(stream):
    for name in ('airlines', 'covertype', 'poker'):
        if name in stream:
            return name
    return 'insects'


def score(cache):
    rows = []
    reweight.simulate2(cache, outer='brier', scale=.5, temper=True, collect=rows)
    y, B = cache['y'], cache['B']
    acc = np.mean([(P.argmax(1) == y[t * B:(t + 1) * B]).mean() for t, P in rows])
    ll = np.mean([-np.log(np.clip(P[np.arange(B), y[t * B:(t + 1) * B]], 1e-6, 1)).mean() for t, P in rows])
    yt = np.concatenate([y[t * B:(t + 1) * B] for t, _ in rows])
    yp = np.concatenate([P.argmax(1) for _, P in rows])
    return 100 * acc, float(ll), 100 * f1_score(yt, yp, average='macro')


def main():
    out = []
    for seed in SEEDS:
        for stream in STREAMS:
            with (ROOT / f'mice_s{seed}/{stream}__micev1000_500.pkl').open('rb') as handle:
                cache = pickle.load(handle)
            duo = np.load(ROOT / f'duo/s{seed}/{stream}.npz')
            y, B = cache['y'], cache['B']
            gap = max(np.abs(st['P'][-1000] - duo['P_fifo'][st['t']].astype(float)).max() for st in cache['cache'])
            assert gap < 2e-3, (seed, stream, gap)
            fifo = 100 * np.mean([(st['P'][-1000].argmax(1) == y[st['t'] * B:(st['t'] + 1) * B]).mean()
                                  for st in cache['cache']])
            row = dict(seed=seed, stream=stream, family=family(stream), batches=len(cache['cache']) + 1,
                       fifo=fifo, fifo_gap=gap)
            row['mice'], row['mice_ll'], row['mice_f1'] = score(cache)
            aug = copy.copy(cache)
            aug['cache'] = []
            for st in cache['cache']:
                P = duo['P_sel'][st['t']].astype(float)
                aug['cache'].append(dict(st, P={**st['P'], 'duo': P / P.sum(1, keepdims=True)}))
            row['mice_duo'], row['mice_duo_ll'], row['mice_duo_f1'] = score(aug)
            for kind, task in (('mice', f'ho_mice_s{seed}_{stream}'), ('duo', f'ho_duo_s{seed}_{stream}')):
                done = ROOT / 'done' / f'{task}.json'
                row[f'{kind}_task_s'] = json.loads(done.read_text())['elapsed'] if done.exists() else np.nan
            out.append(row)
            print(seed, stream, round(row['mice_duo'] - row['mice'], 3), flush=True)
    r = pd.DataFrame(out)
    r.to_csv(HERE / 'heldout_results.csv', index=False)
    lines = []
    for seed, g in r.groupby('seed'):
        dm, df = g.mice_duo - g.mice, g.mice_duo - g.fifo
        dll = g.mice_duo_ll.mean() - g.mice_ll.mean()
        checks = dict(c1=dm.min() >= -.30, c2=df.min() >= -.30, c3=dm.mean() >= 0, c4=dll <= .005)
        lines.append(dict(seed=seed, mean_vs_mice=dm.mean(), wins=int((dm > 0).sum()), losses=int((dm < 0).sum()),
                          worst_vs_mice=dm.min(), worst_stream=g.stream.iloc[int(np.argmin(dm.values))],
                          worst_vs_fifo=df.min(), d_logloss=dll, d_f1=(g.mice_duo_f1 - g.mice_f1).mean(),
                          **checks, passed=all(checks.values())))
    v = pd.DataFrame(lines)
    v.to_csv(HERE / 'heldout_verdicts.csv', index=False)
    pd.set_option('display.width', 220)
    r['d'] = r.mice_duo - r.mice
    print(r.groupby(['family', 'seed']).d.mean().unstack().round(3).to_string())
    print(v.round(3).to_string(index=False))
    print('CONFIRMED' if v.passed.all() else 'NOT CONFIRMED')


if __name__ == '__main__':
    main()
