"""Round-9 isolated resource benchmark (registered in PLAN.md, "Round 9 addition", part A).

Usage: python bench_resources.py <bench root> <repo>
Waits until no other process uses the GPU, then runs each (repetition, policy, stream) in a fresh process on data
truncated to 301 batches, with checkpointing disabled, recording run.py's per-batch wall time, peak GPU memory
(allocated, reserved), peak process RAM, TFM calls and the cached predictions. Writes <root>/bench.jsonl."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STREAMS = ["h4_airlines_d", "h4_covertype_d", "insects_abrupt_balanced"]
POLICIES = ["micev1000_500", "fifo1000", "fifo1500", "fifo2000", "fifo3000", "fifo5000", "fifo13400", "winens1000"]
REPS = 3
CHILD = r'''
import json, os, resource, sys, time, torch
sys.path.insert(0, sys.argv[1]); import run
torch.cuda.set_per_process_memory_fraction(28 * 1024 / (torch.cuda.get_device_properties(0).total_memory / 2**20))  # 28 GB rule
run.DATA = sys.argv[2]
t = time.time(); run.run(sys.argv[3], sys.argv[4], 100, sys.argv[5]); el = time.time() - t
print("BENCH " + json.dumps(dict(elapsed=el, peak_alloc_mib=torch.cuda.max_memory_allocated() / 2**20,
                                 peak_reserved_mib=torch.cuda.max_memory_reserved() / 2**20,
                                 peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)))
'''


def gpu_busy():
    q = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], capture_output=True, text=True)
    return [p for p in q.stdout.split() if p.strip()]


def main(root, repo):
    import numpy as np
    root = Path(root)
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    src = Path.home() / "pfn-runs/mice-tkde-control-20261009/data"
    for s in STREAMS:
        z = np.load(src / f"{s}.npz")
        n = 301 * 100
        np.savez_compressed(data / f"{s}.npz", X=z["X"][:n], y=z["y"][:n], concept=z["concept"][:n])
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MICE_CKPT_EVERY="1000000", CUDA_LAUNCH_BLOCKING="0", HF_HUB_OFFLINE="1", TABPFN_DISABLE_TELEMETRY="1",
               TABPFN_MODEL_CACHE_DIR=str(Path.home() / "pfn-venvs/cache/tabpfn"))
    env.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    log = open(root / "bench.jsonl", "a")
    for rep in range(REPS):
        order = POLICIES[rep % len(POLICIES):] + POLICIES[:rep % len(POLICIES)]
        for pol in order:
            for s in STREAMS:
                out = root / f"rep{rep}"
                out.mkdir(exist_ok=True)
                if (out / f"{s}__{pol}.npz").exists():
                    continue
                while gpu_busy():
                    time.sleep(30)
                for attempt in range(5):
                    p = subprocess.run([sys.executable, "-c", CHILD, f"{repo}/MICE/code", str(data), s, pol, str(out)],
                                       env=env, capture_output=True, text=True)
                    line = next((l for l in p.stdout.splitlines() if l.startswith("BENCH ")), None)
                    rec = dict(rep=rep, policy=pol, stream=s, attempt=attempt, ok=p.returncode == 0 and line is not None,
                               time=time.time())
                    if rec["ok"]:
                        rec.update(json.loads(line[6:]))
                    elif "OutOfMemory" in p.stderr or "out of memory" in p.stderr:
                        rec["infeasible"] = "out of memory under the 28 GB cap"
                        rec["stderr"] = p.stderr[-300:]
                        for f in out.glob(f"{s}__{pol}*"):
                            f.unlink()
                        log.write(json.dumps(rec) + "\n"); log.flush()
                        break
                    else:
                        rec["stderr"] = p.stderr[-500:]
                        for f in out.glob(f"{s}__{pol}*"):
                            f.unlink()
                    log.write(json.dumps(rec) + "\n"); log.flush()
                    if rec["ok"]:
                        break
    log.write(json.dumps(dict(done=True, time=time.time())) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
