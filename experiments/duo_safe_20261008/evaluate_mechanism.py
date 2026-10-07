"""Pre-registered evaluation of PLAN_mechanism.md. No model calls; reads caches written by the GPU runs."""
import copy
from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = Path.home() / 'pfn-runs/duo-safe-20261008'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'source/MICE'))
import reweight  # noqa: E402
from make_streams import names  # noqa: E402

VARIANTS = {'mice+sel1': (1, 'P_sel'), 'mice+sel3': (3, 'P_sel')}


def score(cache, concept):
    rows = []
    reweight.simulate2(cache, outer='brier', scale=.5, temper=True, collect=rows)
    y, B = cache['y'], cache['B']
    acc = {t: (P.argmax(1) == y[t * B:(t + 1) * B]).mean() for t, P in rows}
    ll = np.mean([-np.log(np.clip(P[np.arange(B), y[t * B:(t + 1) * B]], 1e-6, 1)).mean() for t, P in rows])
    recur = reweight.metrics(acc, dict(B=B, concept=concept), h=5).get('acc_recur', np.nan)
    return 100 * np.mean(list(acc.values())), float(ll), 100 * recur


def main():
    out = []
    for stream in names():
        with (ROOT / f'mech/{stream}__micev1000_500.pkl').open('rb') as handle:
            cache = pickle.load(handle)
        concept = cache['concept']
        duo = {a: np.load(ROOT / f'duo/a{a}/{stream}.npz') for a in (1, 3)}
        y, B = cache['y'], cache['B']
        gap = max(np.abs(st['P'][-1000] - duo[1]['P_fifo'][st['t']].astype(float)).max() for st in cache['cache'])
        assert gap < 2e-3, (stream, gap)
        fifo = 100 * np.mean([(st['P'][-1000].argmax(1) == y[st['t'] * B:(st['t'] + 1) * B]).mean()
                              for st in cache['cache']])
        lvl, c, s = stream.split('_')[1:]
        row = dict(stream=stream, level=lvl, centroids=int(c[1:]), seed=int(s[1:]), fifo=fifo, fifo_gap=gap)
        row['mice'], row['mice_ll'], row['mice_recur'] = score(cache, concept)
        for name, (anchor, key) in VARIANTS.items():
            aug = copy.copy(cache)
            aug['cache'] = []
            for st in cache['cache']:
                P = duo[anchor][key][st['t']].astype(float)
                aug['cache'].append(dict(st, P={**st['P'], 'duo': P / P.sum(1, keepdims=True)}))
            row[name], row[name + '_ll'], row[name + '_recur'] = score(aug, concept)
        out.append(row)
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
    r = pd.DataFrame(out)
    r.to_csv(HERE / 'mechanism_results.csv', index=False)
    lines = []
    for name in VARIANTS:
        dm, df = r[name] - r.mice, r[name] - r.fifo
        by = dm.groupby(r.level).mean()
        none = r.level == 'k15'
        h1 = bool(dm[none].min() >= -.30 and df[none].min() >= -.30)
        h2 = bool(dm.min() >= -.30 and df.min() >= -.30 and r[name + '_ll'].mean() <= r.mice_ll.mean() + .005)
        k3 = dm[r.level == 'k3']
        h3 = bool(by['k3'] > by['k5'] > by['k15'] and k3.mean() > 0 and (k3 > 0).sum() >= 5)
        lines.append(dict(variant=name, gain_k3=by['k3'], gain_k5=by['k5'], gain_k15=by['k15'],
                          wins_k3=int((k3 > 0).sum()), worst_vs_mice=dm.min(), worst_vs_fifo=df.min(),
                          d_logloss=r[name + '_ll'].mean() - r.mice_ll.mean(), H1=h1, H2=h2, H3=h3))
    v = pd.DataFrame(lines)
    v.to_csv(HERE / 'mechanism_verdicts.csv', index=False)
    pd.set_option('display.width', 220)
    print(r.groupby('level')[['fifo', 'mice', 'mice+sel1', 'mice+sel3', 'mice_recur', 'mice+sel1_recur']]
          .mean().round(2).to_string())
    print(v.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
