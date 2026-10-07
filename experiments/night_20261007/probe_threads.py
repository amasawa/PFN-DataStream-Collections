"""Single-process, multi-thread CUDA probe: one CUDA context shared by N TabPFN models.

Multi-process runs failed with illegal memory access; this tests whether thread-level
concurrency inside one context is stable and raises utilization. Diagnostics only.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--batches', type=int, default=60)
    parser.add_argument('--streams', default='h3_insects_b,h3_covertype_b,h3_airlines_b,h3_poker_b')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    root = Path.home() / 'pfn-runs/night-20261007/diagnostics' / args.tag
    root.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo / 'MICE/code'))
    import torch
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    from run import TFM
    streams = args.streams.split(',')
    out = dict(config=vars(args), launch_blocking=os.environ.get('CUDA_LAUNCH_BLOCKING'),
               started=datetime.now().astimezone().isoformat(), calls=[0] * args.threads,
               errors=[None] * args.threads, samples=[])
    stop = threading.Event()

    def work(i):
        stream = streams[i % len(streams)]
        try:
            with np.load(repo / 'MICE/data' / (stream + '.npz')) as z:
                X, y = z['X'], z['y'].astype(int)
            model = TFM(int(y.max()) + 1, seed=2)
            P = []
            for t in range(140, min(140 + args.batches, len(y) // 100)):
                for window in (100, 300, 1000):
                    if stop.is_set(): return
                    q = slice(t * 100, (t + 1) * 100); lo = max(0, t * 100 - window)
                    p = model.predict(X[lo:t * 100], y[lo:t * 100], X[q])
                    assert np.isfinite(p).all() and np.allclose(p.sum(1), 1, atol=1e-4)
                    P.append(p); out['calls'][i] += 1
            np.save(root / f'P{i}_{stream}.npy', np.stack(P))
        except Exception:
            out['errors'][i] = traceback.format_exc(); stop.set()

    t0 = time.time()
    workers = [threading.Thread(target=work, args=(i,), daemon=True) for i in range(args.threads)]
    for w in workers: w.start()
    while any(w.is_alive() for w in workers) and time.time() - t0 < 900:
        s = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
        u, m = map(int, s.stdout.split(','))
        out['samples'].append((round(time.time() - t0, 1), u, m))
        if m > 22000: out['errors'].append('memory guard'); stop.set()
        time.sleep(2)
    stop.set()
    for w in workers: w.join(30)
    out['elapsed'] = time.time() - t0
    utils = [u for _, u, _ in out['samples'][3:]] or [0]
    out['mean_util'] = sum(utils) / len(utils)
    out['max_mib'] = max((m for *_, m in out['samples']), default=0)
    out['passed'] = not any(out['errors'])
    out['calls_per_s'] = sum(out['calls']) / out['elapsed']
    (root / 'suite.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'samples'}, indent=1), flush=True)
    return 0 if out['passed'] else 1


if __name__ == '__main__': sys.exit(main())
