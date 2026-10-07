"""Small controlled CUDA probes; stop the whole probe at its first failed worker."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--workers', type=int, choices=(1, 2, 3, 4), default=1)
    parser.add_argument('--poll', type=int, default=0)
    parser.add_argument('--batches', type=int, default=120)
    parser.add_argument('--blocking', choices=('0', '1'), default='1')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    root = Path.home() / 'pfn-runs/night-20261007/diagnostics' / args.tag
    root.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', CUDA_LAUNCH_BLOCKING=args.blocking,
               TABPFN_MODEL_CACHE_DIR=str(Path.home() / 'pfn-venvs/cache/tabpfn'))
    jobs = []
    started, last_sample = time.time(), 0
    result = dict(config=vars(args), started=datetime.now().astimezone().isoformat(), samples=[], failed=False)
    try:
        for i in range(args.workers):
            tag = f'{args.tag}/worker{i}'
            handle = (root / f'worker{i}.log').open('w')
            cmd = [sys.executable, '-u', str(repo / 'experiments/night_20261007/diagnose_cuda.py'),
                   '--tag', tag, '--batches', str(args.batches)]
            p = subprocess.Popen(cmd, env=env, stdout=handle, stderr=subprocess.STDOUT)
            jobs.append((p, handle))
            time.sleep(3)
        while any(p.poll() is None for p, _ in jobs):
            if any(p.poll() not in (None, 0) for p, _ in jobs):
                result['failed'] = True; result['reason'] = 'worker failed'; break
            if time.time()-started > 900:
                result['failed'] = True; result['reason'] = '15 minute probe timeout'; break
            if args.poll and time.time()-last_sample >= args.poll:
                sample = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                                         '--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
                last_sample = time.time()
                if sample.returncode:
                    result['failed']=True; result['reason']='NVML query failed'; break
                util, mem = map(int, sample.stdout.strip().splitlines()[0].split(','))
                result['samples'].append(dict(elapsed=time.time()-started, util=util, gpu_mib=mem))
                if mem > 22000:
                    result['failed']=True; result['reason']='memory headroom guard'; break
            time.sleep(1)
    finally:
        for p, handle in jobs:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=10)
                except subprocess.TimeoutExpired: p.kill(); p.wait()
            handle.close()
        result['codes']=[p.returncode for p,_ in jobs]
        result['failed'] |= any(code != 0 for code in result['codes'])
        result['elapsed']=time.time()-started
        (root/'suite.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2),flush=True)
    return int(result['failed'])


if __name__ == '__main__': sys.exit(main())
