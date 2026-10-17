"""Matched timing benchmark of PLAN.md: MICE (micev1000_500), the sel expert (ranking call + context prediction) and the
rand expert (context prediction) on three held-out prefixes, backbone seed 0, two repetitions in rotated order, one
fresh process per run, started only when no other process uses the GPU above 5% (an idle resident process is
recorded in the log). The replay of the two-level mixture is timed by the evaluator.

Usage: python bench.py <bench root>            (driver; refuses an existing root)
       python bench.py <bench root> --one <rep> <policy> <stream>   (one run, called by the driver)"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
HELD = Path.home() / 'pfn-runs/duo-heldout-20261008'
STREAMS = ('insects_abrupt_balanced', 'covertype', 'h3_airlines_b')
POLICIES = ('mice', 'sel', 'rand')
B = 100


def gpu_state():
    q = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
                       capture_output=True, text=True).stdout.split(',')
    apps = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'],
                          capture_output=True, text=True).stdout.split()
    return float(q[0]), float(q[1]), apps


def one(root, rep, policy, stream):
    sys.path.insert(0, str(HERE))
    import worker
    import torch
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(1792 * 1024**2 / total)
    out = Path(root) / f'rep{rep}'; out.mkdir(parents=True, exist_ok=True)
    if policy == 'mice':
        import run
        # run.TFM(K) uses backbone seed 0 by default
        run.DATA = str(HELD / 'data')
        os.environ['MICE_CKPT_EVERY'] = '100000'
        run.run(stream, 'micev1000_500', B, str(out))
        sec = np.load(out / f'{stream}__micev1000_500.npz')['wt'][1:]
    else:
        z = np.load(HELD / 'data' / f'{stream}.npz')
        X, y = z['X'].astype(np.float32), z['y'].astype(int)
        T, K = min(300, len(y) // B), int(y.max()) + 1
        model = worker.make_tfm(K, 0)
        if policy == 'sel':
            import base_worker
        sec = []
        for t in range(1, T):
            start = time.perf_counter()
            sel = (base_worker.anchor_selection(model, X, y, t, 1) if policy == 'sel'
                   else worker.rand_selection(t, 1, 0, 0, stream))
            idx = np.concatenate([np.arange(b * B, (b + 1) * B) for b in sel])
            model.predict(X[idx], y[idx], X[t * B:(t + 1) * B])
            sec.append(time.perf_counter() - start)
        sec = np.array(sec)
    rec = dict(rep=rep, policy=policy, stream=stream, mean_s=float(sec.mean()), median_s=float(np.median(sec)),
               p95_s=float(np.percentile(sec, 95)), batches=len(sec),
               peak_alloc_mib=torch.cuda.max_memory_allocated() / 2**20)
    with open(Path(root) / 'bench.jsonl', 'a') as fh:
        fh.write(json.dumps(rec) + '\n')


def driver(root):
    root = Path(root)
    root.mkdir(parents=False, exist_ok=False)
    order = [(r, p, s) for r in (0, 1) for i, s in enumerate(STREAMS)
             for p in (POLICIES[(i + r) % 3:] + POLICIES[:(i + r) % 3])]
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', CUDA_LAUNCH_BLOCKING='0', HF_HUB_OFFLINE='1',
               TABPFN_DISABLE_TELEMETRY='1', TABPFN_MODEL_CACHE_DIR=str(Path.home() / 'pfn-venvs/cache/tabpfn'))
    env.pop('PYTORCH_CUDA_ALLOC_CONF', None)
    for rep, p, s in order:
        for attempt in range(3):
            while True:
                util, mem, apps = gpu_state()
                busy = subprocess.run(['pgrep', '-f', 'duo_rand_20261017/worker.py'], capture_output=True).stdout.strip()
                if util < 5 and not busy:
                    break
                time.sleep(30)
            with open(root / 'log.txt', 'a') as fh:
                fh.write(f'{time.strftime("%H:%M:%S")} start rep{rep} {p} {s} gpu {util}% {mem} MiB apps {apps}\n')
            rc = subprocess.run([sys.executable, __file__, str(root), '--one', str(rep), p, s], env=env,
                                stdout=open(root / 'runs.log', 'a'), stderr=subprocess.STDOUT).returncode
            with open(root / 'log.txt', 'a') as fh:
                fh.write(f'{time.strftime("%H:%M:%S")} end rep{rep} {p} {s} rc {rc}\n')
            if rc == 0:
                break
            for f in (root / f'rep{rep}').glob(f'{s}__micev1000_500*'):   # a failed MICE run restarts from scratch
                f.unlink()
    with open(root / 'log.txt', 'a') as fh:
        fh.write(f'{time.strftime("%H:%M:%S")} done\n')


if __name__ == '__main__':
    if '--one' in sys.argv:
        i = sys.argv.index('--one')
        sys.path.insert(0, str(HELD / 'source/MICE')); sys.path.insert(0, str(HELD / 'controller'))
        one(sys.argv[1], int(sys.argv[i + 1]), sys.argv[i + 2], sys.argv[i + 3])
    else:
        driver(sys.argv[1])
