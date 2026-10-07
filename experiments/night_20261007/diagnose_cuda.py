"""Short real-data CUDA stability probe; writes diagnostics, never experiment results."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--stream', default='h3_insects_b')
    parser.add_argument('--start', type=int, default=140)
    parser.add_argument('--batches', type=int, default=40)
    parser.add_argument('--allocator-mib', type=int, default=1792)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    root = Path.home() / 'pfn-runs/night-20261007/diagnostics' / args.tag
    root.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo / 'MICE/code'))
    import torch
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    if args.allocator_mib:
        torch.cuda.set_per_process_memory_fraction(args.allocator_mib*1024**2 / torch.cuda.get_device_properties(0).total_memory)
    from run import TFM
    with np.load(repo / 'MICE/data' / (args.stream+'.npz')) as z:
        X, y = z['X'], z['y'].astype(int)
    model = TFM(int(y.max())+1, seed=2)
    out = dict(config=vars(args), launch_blocking=os.environ.get('CUDA_LAUNCH_BLOCKING'),
               started=time.time(), calls=0, passed=False)
    probabilities, keys = [], []
    try:
        for t in range(args.start, min(args.start+args.batches, len(y)//100)):
            for window in (100, 300, 1000):
                q = slice(t*100,(t+1)*100); lo=max(0,t*100-window)
                p = model.predict(X[lo:t*100],y[lo:t*100],X[q])
                assert np.isfinite(p).all() and np.allclose(p.sum(1),1,atol=1e-4)
                probabilities.append(p); keys.append((t,window)); out['calls'] += 1
                out['last'] = [t,window]; out['elapsed']=time.time()-out['started']
                (root/'progress.json').write_text(json.dumps(out,indent=2)+'\n')
            print(args.tag,'batch',t,'calls',out['calls'],flush=True)
        out['passed']=True
    except Exception:
        out['error']=traceback.format_exc()
        print(out['error'],flush=True)
    finally:
        out['elapsed']=time.time()-out['started']
        (root/'report.json').write_text(json.dumps(out,indent=2)+'\n')
        if probabilities: np.savez_compressed(root/'probabilities.npz',P=np.stack(probabilities),keys=np.array(keys))
        print(json.dumps(out),flush=True)
    return 0 if out['passed'] else 1


if __name__ == '__main__': sys.exit(main())
