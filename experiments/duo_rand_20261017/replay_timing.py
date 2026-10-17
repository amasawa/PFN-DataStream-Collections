"""Replay time of the two-level mixture (PLAN.md timing benchmark, last clause), which evaluate.py does not time:
frozen simulate2 on the MICE cache of the three benchmark prefixes (backbone seed 0), without and with the extra
expert, five repetitions each, seconds per batch. CPU only; run after bench.py finished. Appends to <bench root>.

Usage: python replay_timing.py <bench root>"""
import copy
import json
from pathlib import Path
import pickle
import sys
import time

import numpy as np

HELD = Path.home() / 'pfn-runs/duo-heldout-20261008'
sys.path.insert(0, str(HELD / 'source/MICE'))
import reweight  # noqa: E402

from bench import STREAMS  # noqa: E402


def replay(cache, extra):
    c = copy.copy(cache)
    if extra is not None:
        c['cache'] = [dict(st, P={**st['P'], 'duo': extra[st['t']] / extra[st['t']].sum(1, keepdims=True)})
                      for st in cache['cache']]
    start = time.perf_counter()
    reweight.simulate2(c, outer='brier', scale=.5, temper=True, collect=[])
    return (time.perf_counter() - start) / len(c['cache'])


def main(root):
    out = Path(root) / 'replay.jsonl'
    assert not out.exists(), out
    for s in STREAMS:
        cache = pickle.load(open(HELD / f'mice/s0/{s}__micev1000_500.pkl', 'rb'))
        extra = np.load(HELD / f'duo/s0/{s}.npz')['P_sel'].astype(np.float64)
        for name, e in (('mice', None), ('mice+extra', extra)):
            sec = [replay(cache, e) for _ in range(5)]
            with open(out, 'a') as fh:
                fh.write(json.dumps(dict(stream=s, replay=name, s_per_batch=float(np.median(sec)))) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
