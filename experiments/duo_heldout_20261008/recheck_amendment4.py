"""Amendment 4 check (2026-10-09): two held-out tasks that completed during the 7-8-worker phase with retries were
rerun alone (one process, OMP_NUM_THREADS=1, same frozen worker/source/data) into ~/pfn-runs/duo-heldout-recheck-20261009
(run_recheck.sh there), and compared bit for bit with the originals. Only wall time (wt) may differ."""
import pickle
import numpy as np

A = '/home/zhwu9808/pfn-runs/duo-heldout-20261008'
B = '/home/zhwu9808/pfn-runs/duo-heldout-recheck-20261009'


def cmp_npz(a, b):
    za, zb = np.load(a), np.load(b)
    for k in sorted(set(za) | set(zb)):
        x, y = za[k], zb[k]
        print(f'  {k:12s} {x.shape} identical={x.shape == y.shape and np.array_equal(x, y, equal_nan=x.dtype.kind == "f")}')


print('duo_s1_h4_poker_e (3 retries in the original run)')
cmp_npz(f'{A}/duo/s1/h4_poker_e.npz', f'{B}/duo/s1/h4_poker_e.npz')
print('mice_s1_insects_abrupt_balanced (2 retries in the original run)')
cmp_npz(f'{A}/mice/s1/insects_abrupt_balanced__micev1000_500.npz', f'{B}/mice/s1/insects_abrupt_balanced__micev1000_500.npz')
ca = pickle.load(open(f'{A}/mice/s1/insects_abrupt_balanced__micev1000_500.pkl', 'rb'))
cb = pickle.load(open(f'{B}/mice/s1/insects_abrupt_balanced__micev1000_500.pkl', 'rb'))
same = len(ca['cache']) == len(cb['cache']) and all(
    sa['t'] == sb['t'] and sa['P'].keys() == sb['P'].keys() and all(np.array_equal(sa['P'][k], sb['P'][k]) for k in sa['P'])
    for sa, sb in zip(ca['cache'], cb['cache']))
print(f'  cached expert predictions, {len(ca["cache"])} batches: identical={same}')
