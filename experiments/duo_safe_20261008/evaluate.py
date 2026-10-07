"""Offline evaluation of DUO's selection as an extra MICE expert (see PLAN.md). No model calls."""
import copy
from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = Path.home() / 'pfn-runs/night-20261007'
sys.path.insert(0, str(ROOT / 'source/MICE'))
import reweight  # noqa: E402

STREAMS = ['elec2', 'h2_airlines', 'h2_phishing', 'h2_poker', 'h2_rialto', 'h2_spam', 'h2_weather']
EXTRA = 'duo'  # key of the added expert in the cached steps
VARIANTS = {'mice+sel1': (1, 'P_sel'), 'mice+sel3': (3, 'P_sel'), 'mice+sel5': (5, 'P_sel'),
            'mice+duo1': (1, 'P_duo')}


def run_rule(cache):
    rows = []
    acc = reweight.simulate2(cache, outer='brier', scale=.5, temper=True, collect=rows)
    y, B = cache['y'], cache['B']
    ll = [-np.log(np.clip(P[np.arange(B), y[t * B:(t + 1) * B]], 1e-6, 1)).mean() for t, P in rows]
    return 100 * np.mean(list(acc.values())), float(np.mean(ll))


def main():
    out = []
    for seed in (1, 2):
        for stream in STREAMS:
            with (ROOT / f'duo_mice_s{seed}/{stream}__micev1000_500.pkl').open('rb') as handle:
                cache = pickle.load(handle)
            duo = {a: np.load(ROOT / f'duo/s{seed}_a{a}/{stream}.npz') for a in (1, 3, 5)}
            y, B = cache['y'], cache['B']
            # Alignment check: MICE's 1000-row FIFO expert must equal DUO's FIFO prediction.
            fifo_gap = max(np.abs(st['P'][-1000] - duo[1]['P_fifo'][st['t']].astype(float)).max()
                           for st in cache['cache'])
            assert fifo_gap < 2e-3, (seed, stream, fifo_gap)  # P_fifo is stored as float16
            fifo_acc = 100 * np.mean([(st['P'][-1000].argmax(1) == y[st['t'] * B:(st['t'] + 1) * B]).mean()
                                      for st in cache['cache']])
            row = dict(seed=seed, stream=stream, fifo=fifo_acc, fifo_gap=fifo_gap)
            row['mice'], row['mice_ll'] = run_rule(cache)
            for name, (anchor, key) in VARIANTS.items():
                augmented = copy.copy(cache)
                augmented['cache'] = []
                for st in cache['cache']:
                    P = duo[anchor][key][st['t']].astype(float)
                    P /= P.sum(1, keepdims=True)
                    augmented['cache'].append(dict(st, P={**st['P'], EXTRA: P}))
                row[name], row[name + '_ll'] = run_rule(augmented)
            out.append(row)
            print(seed, stream, {k: round(v, 3) for k, v in row.items() if isinstance(v, float)}, flush=True)
    r = pd.DataFrame(out)
    here = Path(__file__).resolve().parent
    r.to_csv(here / 'results.csv', index=False)
    lines = []
    for name in VARIANTS:
        for seed, g in r.groupby('seed'):
            dm, df = g[name] - g.mice, g[name] - g.fifo
            dll = g[name + '_ll'].mean() - g.mice_ll.mean()
            checks = [dm.min() >= -.30, df.min() >= -.30, dm.mean() >= 0, dll <= .005]
            lines.append(dict(variant=name, seed=seed, mean_vs_mice=dm.mean(), wins_vs_mice=int((dm > 0).sum()),
                              worst_vs_mice=dm.min(), worst_vs_fifo=df.min(), d_logloss=dll,
                              rialto_vs_mice=float(dm[g.stream == 'h2_rialto'].iloc[0]), passed=all(checks)))
    v = pd.DataFrame(lines)
    v.to_csv(here / 'verdicts.csv', index=False)
    pd.set_option('display.width', 200)
    print(v.round(3).to_string(index=False))
    for name in VARIANTS:
        print(name, 'passes on every seed:', bool(v[v.variant == name].passed.all()))


if __name__ == '__main__':
    main()
