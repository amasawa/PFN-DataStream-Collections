"""Evaluation of PLAN.md (written before the runs; no model calls). Reads the MICE caches and DUO outputs of the
mechanism and held-out runs and the rand/orc outputs of <root>/out; writes MiceDuo/results/duo_rand_*.csv and prints
the pre-specified readings R1-R3. All Deltas are oriented so that positive = sel better (accuracy in points, log-loss
as rand minus sel).

Usage: python evaluate.py <root>   (refuses to run unless all 270 outputs exist)"""
import copy
import json
from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd
from scipy import stats

HOME = Path.home() / 'pfn-runs'
MECH, HELD = HOME / 'duo-safe-20261008', HOME / 'duo-heldout-20261008'
sys.path.insert(0, str(HELD / 'source/MICE'))
import reweight  # noqa: E402  (frozen simulate2)

OUT = Path(__file__).resolve().parents[2] / 'MiceDuo/results'
B, DRAWS, ETA = 100, (0, 1, 2), 10.0


def per_batch(P, y):
    """Per-batch accuracy (points) and log-loss of predictions P (T', B, K) against labels y (T', B)."""
    P = P / P.sum(-1, keepdims=True)
    acc = 100 * (P.argmax(-1) == y).mean(1)
    ll = -np.log(np.clip(np.take_along_axis(P, y[..., None], -1)[..., 0], 1e-6, 1)).mean(1)
    return acc, ll


def deployed(cache, extra):
    """MICE with `extra` (T, B, K) as one more expert under the frozen rule; per-batch accuracy, log-loss and the
    fast-level weight of the extra expert (recomputed with simulate2's formula)."""
    c = copy.copy(cache)
    if extra is not None:
        c['cache'] = [dict(st, P={**st['P'], 'duo': extra[st['t']] / extra[st['t']].sum(1, keepdims=True)})
                      for st in cache['cache']]
    rows = []
    reweight.simulate2(c, outer='brier', scale=.5, temper=True, collect=rows)
    ts = np.array([t for t, _ in rows])
    y = np.stack([cache['y'][t * B:(t + 1) * B] for t in ts])
    acc, ll = per_batch(np.stack([P for _, P in rows]), y)
    w, prev = [], None
    for st in c['cache']:
        yq = cache['y'][st['t'] * B:(st['t'] + 1) * B]
        keys = list(st['P'])
        if prev is None:
            wk = np.ones(len(keys))
        else:
            Lk = np.array([prev[u] if u in prev else np.median(list(prev.values())) for u in keys])
            wk = np.exp(-ETA * (Lk - Lk.min()))
        wk /= wk.sum()
        w.append(wk[keys.index('duo')] if 'duo' in keys else np.nan)
        prev = {u: -np.log(np.clip(P[np.arange(B), yq], 1e-6, 1)).mean() for u, P in st['P'].items()}
    return ts, acc, ll, np.array(w)


def alone(P, y, ts):
    return per_batch(P[ts].astype(np.float64), y[ts])


def hit_rate(chosen, concept, ts):
    hits = []
    for t in ts[ts > 10]:
        sel = [b for b in chosen[t] if b >= 0 and b != t - 1]
        hits.append(np.mean([concept[b * B] == concept[t * B] for b in sel]))
    return 100 * np.mean(hits)


def mbb(diff, block, n=2000, seed=0):
    """Moving-block bootstrap 95% interval of the mean of a per-batch series."""
    rng, T = np.random.default_rng(seed), len(diff)
    k = int(np.ceil(T / block))
    means = [np.concatenate([diff[s:s + block] for s in rng.integers(0, T - block + 1, k)])[:T].mean() for _ in range(n)]
    return np.percentile(means, [2.5, 97.5])


def mbb_pooled(series, block=17, n=2000, seed=0):
    """Conditional interval of the pooled mean over fixed prefixes: blocks resampled within every prefix."""
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        m = []
        for d in series:
            T = len(d); k = int(np.ceil(T / block))
            m.append(np.concatenate([d[s:s + block] for s in rng.integers(0, T - block + 1, k)])[:T].mean())
        means.append(np.mean(m))
    return np.percentile(means, [2.5, 97.5])


def tci(x):
    x = np.asarray(x, float)
    h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), x.mean() - h, x.mean() + h


def load(root, kind, seed, draw, stream):
    return np.load(Path(root) / 'out' / kind / f's{seed}' / f'd{draw}' / f'{stream}.npz')


def mechanism(root):
    rows, series = [], {}
    for path in sorted((MECH / 'data').glob('mech_*.npz')):
        s = path.stem
        with (MECH / f'mech/{s}__micev1000_500.pkl').open('rb') as fh:
            cache = pickle.load(fh)
        concept, y = np.load(path)['concept'], cache['y'].reshape(-1, B)
        duo = np.load(MECH / f'duo/a1/{s}.npz')
        rnd = [load(root, 'rand', 1, d, s) for d in DRAWS]
        orc = load(root, 'orc', 1, 0, s)
        for z in rnd + [orc]:
            assert np.array_equal(z['y'], y[:len(z['y'])])
        ts, m_acc, m_ll, _ = deployed(cache, None)
        r = dict(stream=s, K=int(s.split('_')[1][1:]), centroids=int(s.split('_')[2][1:]), seed=int(s.split('_')[3][1:]))
        r['mice_acc'], r['mice_ll'] = m_acc.mean(), m_ll.mean()
        res = {}
        for name, P, ch in [('sel', duo['P_sel'], duo['chosen']), ('orc', orc['P'], orc['chosen'])] + \
                [(f'rand{d}', z['P'], z['chosen']) for d, z in zip(DRAWS, rnd)]:
            a_acc, a_ll = alone(P, y, ts)
            _, d_acc, d_ll, w = deployed(cache, P.astype(np.float64))
            res[name] = dict(a_acc=a_acc, a_ll=a_ll, d_acc=d_acc, d_ll=d_ll, w=w, hit=hit_rate(ch, concept, ts))
        late = ts > 10
        for name in ('sel', 'orc') + tuple(f'rand{d}' for d in DRAWS):
            for k in ('a_acc', 'a_ll', 'd_acc', 'd_ll'):
                r[f'{name}_{k}'] = res[name][k].mean()
            r[f'{name}_w'], r[f'{name}_hit'] = np.nanmean(res[name]['w']), res[name]['hit']
        for k in ('a_acc', 'a_ll', 'd_acc', 'd_ll', 'w', 'hit'):
            r[f'rand_{k}'] = np.mean([r[f'rand{d}_{k}'] for d in DRAWS])
        for k in ('a', 'd'):
            per_d_acc = [res['sel'][f'{k}_acc'] - res[f'rand{d}'][f'{k}_acc'] for d in DRAWS]
            per_d_ll = [res[f'rand{d}'][f'{k}_ll'] - res['sel'][f'{k}_ll'] for d in DRAWS]
            r[f'D{k}_acc'] = np.mean([x.mean() for x in per_d_acc])
            r[f'D{k}_ll'] = np.mean([x.mean() for x in per_d_ll])
            r[f'D{k}_acc_drawsd'] = np.std([x.mean() for x in per_d_acc], ddof=1)
            r[f'D{k}_acc_late'] = np.mean([x[late].mean() for x in per_d_acc])
            series[(s, k)] = np.mean(per_d_acc, 0)
            for blk in (10, 17, 30):
                r[f'D{k}_acc_mbb{blk}_lo'], r[f'D{k}_acc_mbb{blk}_hi'] = mbb(series[(s, k)], blk)
        rows.append(r)
    d = pd.DataFrame(rows)
    g = []
    for K, x in d.groupby('K'):
        row = dict(K=K, streams=len(x))
        for k in ('Da_acc', 'Da_ll', 'Dd_acc', 'Dd_ll'):
            row[k], row[k + '_lo'], row[k + '_hi'] = tci(x[k])
            row[k + '_pos'] = int((x[k] > 0).sum())
        for k in ('mice_acc', 'sel_a_acc', 'rand_a_acc', 'orc_a_acc', 'sel_d_acc', 'rand_d_acc', 'orc_d_acc',
                  'sel_hit', 'rand_hit', 'orc_hit', 'sel_w', 'rand_w', 'orc_w', 'Dd_acc_late', 'Da_acc_drawsd'):
            row[k] = x[k].mean()
        g.append(row)
    return d, pd.DataFrame(g)


def heldout(root):
    entries = json.loads((HELD / 'data_manifest.json').read_text())
    rows, series = [], {}
    for e in entries:
        s = e['stream']
        acc_d, ll_d, per_seed = [], [], []
        for seed in (0, 1, 2):
            with (HELD / f'mice/s{seed}/{s}__micev1000_500.pkl').open('rb') as fh:
                cache = pickle.load(fh)
            y = cache['y'].reshape(-1, B)
            duo = np.load(HELD / f'duo/s{seed}/{s}.npz')
            ts, m_acc, _, _ = deployed(cache, None)
            _, s_acc, s_ll, _ = deployed(cache, duo['P_sel'].astype(np.float64))
            sa_acc, sa_ll = alone(duo['P_sel'], y, ts)
            dd, da = [], []
            for d in DRAWS:
                z = load(root, 'rand', seed, d, s)
                assert np.array_equal(z['y'], y[:len(z['y'])])
                _, r_acc, r_ll, _ = deployed(cache, z['P'].astype(np.float64))
                ra_acc, ra_ll = alone(z['P'], y, ts)
                dd.append((s_acc - r_acc, r_ll - s_ll)); da.append((sa_acc - ra_acc, ra_ll - sa_ll))
                rows.append(dict(stream=s, source=e['source'], seed=seed, draw=d, Dd_acc=(s_acc - r_acc).mean(),
                                 Dd_ll=(r_ll - s_ll).mean(), Da_acc=(sa_acc - ra_acc).mean(),
                                 Da_ll=(ra_ll - sa_ll).mean(), sel_d_acc=s_acc.mean(), rand_d_acc=r_acc.mean(),
                                 mice_acc=m_acc.mean()))
            acc_d.append(np.mean([x[0] for x in dd], 0)); ll_d.append(np.mean([x[1] for x in dd], 0))
        series[s] = (np.mean(acc_d, 0), np.mean(ll_d, 0))
    d = pd.DataFrame(rows)
    pref = d.groupby(['stream', 'source']).mean(numeric_only=True).drop(columns=['seed', 'draw']).reset_index()
    src = pref.groupby('source').mean(numeric_only=True)
    sel_sd = d.groupby(['stream', 'seed']).Dd_acc.std(ddof=1).mean()
    seed_sd = d.groupby(['stream', 'seed']).Dd_acc.mean().groupby('stream').std(ddof=1).mean()
    ci_acc = mbb_pooled([v[0] for v in series.values()])
    ci_ll = mbb_pooled([v[1] for v in series.values()])
    pooled = dict(Dd_acc=pref.Dd_acc.mean(), Dd_acc_lo=ci_acc[0], Dd_acc_hi=ci_acc[1], Dd_ll=pref.Dd_ll.mean(),
                  Dd_ll_lo=ci_ll[0], Dd_ll_hi=ci_ll[1], Da_acc=pref.Da_acc.mean(), Da_ll=pref.Da_ll.mean(),
                  sources_pos=int((src.Dd_acc > 0).sum()), selector_sd=sel_sd, backbone_sd=seed_sd)
    return d, src, pooled


def main(root):
    have = len(list((Path(root) / 'out').glob('[ro]*/s*/d*/*.npz')))
    assert have == 270, f'incomplete: {have}/270, no partial evaluation'
    OUT.mkdir(exist_ok=True)
    md, mg = mechanism(root)
    md.to_csv(OUT / 'duo_rand_mech_streams.csv', index=False); mg.to_csv(OUT / 'duo_rand_mech_levels.csv', index=False)
    hd, hs, hp = heldout(root)
    hd.to_csv(OUT / 'duo_rand_heldout_runs.csv', index=False); hs.to_csv(OUT / 'duo_rand_heldout_sources.csv')
    pd.DataFrame([hp]).to_csv(OUT / 'duo_rand_heldout_pooled.csv', index=False)
    pd.set_option('display.width', 250)
    print(mg.round(3).to_string(index=False)); print(hs.round(3).to_string()); print(hp)
    k3 = mg.set_index('K').loc[3]
    r1 = k3.Da_acc_lo > 0 and k3.Da_ll_lo > 0
    r2 = k3.Dd_acc_lo > 0 and k3.Dd_ll_lo > 0
    r3 = hp['Dd_acc_lo'] > 0 and hp['Dd_ll_lo'] > 0 and hp['sources_pos'] >= 3
    verdict = {'R1 ranking (expert alone, K=3)': bool(r1), 'R2 deployed (K=3)': bool(r2), 'R3 deployed (held-out)': bool(r3)}
    print({k: 'established' if v else 'no advantage established' for k, v in verdict.items()})
    pd.Series(verdict).to_csv(OUT / 'duo_rand_readings.csv')


if __name__ == '__main__':
    main(sys.argv[1])
