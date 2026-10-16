"""Round-14.b isolated resource benchmark (registered in PLAN_14B.md, parts A1 and A2): MICE with detected segments
(micecp1000_500) against the archive with the same detected segments (archcp1000_500) and the snapshot pool
(snap1000_500), protocol of round 13 (experiments/mice_tkde_control/bench_pools.py, from which this file is copied):
GPU alone, 28 GB cap, fresh process per run, checkpointing off, rotated policy order per repetition. Change from
round 13: policies and streams, and the occupancy hook also wraps CPSegments.step (which replaces MiceV1.step in
MiceCP and ArchCP; PoolControl.step calls MiceV1.step, so each batch is recorded once).

Usage: python bench_cp.py <bench root> <repo> a1|a2
  a1: three real prefixes (batches 1-300); micecp, archcp kmax 12, snap kmax 2 and 4 with three repetitions, snap kmax
      12 with one.
  a2: full grid streams (three confirmation streams, one shifted); micecp, archcp kmax 12, snap k* (from
      <root>/kstar.json, written by analyse_bench_cp.py a1), three repetitions.
Each run writes <root>/<stage>/rep<r>/<tag>/<stream>__<method>.npz/.pkl (tag "mice" or "k<kmax>") and
<...>.occ.json (pool occupancy and logical stored context rows per batch); records go to <root>/<stage>.jsonl."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REAL = ["h4_airlines_d", "h4_covertype_d", "insects_abrupt_balanced"]
GRID = ["c_b500_c100_s50_o0", "c_b2000_c100_s50_o0", "c_bvar_c100_s50_o0", "off_c100_b500_s20"]
SRC = Path.home() / "pfn-runs/mice-tkde-control-20261009/data"
SRC_C = Path.home() / "pfn-runs/mice-r14-confirm/data"     # confirmation streams (seeds 50-53)
CHILD = r'''
import json, os, resource, sys, time, torch
sys.path.insert(0, sys.argv[1]); import run
torch.cuda.set_per_process_memory_fraction(28 * 1024 / (torch.cuda.get_device_properties(0).total_memory / 2**20))  # 28 GB rule
run.DATA = sys.argv[2]
K = int(sys.argv[6])
if K > 0:
    _init = run.PoolControl.__init__
    def _init_k(self, *a, **kw):
        _init(self, *a, **kw); self.kmax = K
    run.PoolControl.__init__ = _init_k
occ = []
_step = run.MiceV1.step
def _step_rec(self, X, y, t, B):
    out = _step(self, X, y, t, B)
    occ.append((len(self.experts), int(sum(len(e["y"]) for e in self.experts))))
    return out
run.MiceV1.step = _step_rec
_step_cp = run.CPSegments.step
def _step_cp_rec(self, X, y, t, B):
    out = _step_cp(self, X, y, t, B)
    occ.append((len(self.experts), int(sum(len(e["y"]) for e in self.experts))))
    return out
run.CPSegments.step = _step_cp_rec
dst = os.path.join(sys.argv[5], f"{sys.argv[3]}__{sys.argv[4]}.npz")
assert not os.path.exists(dst), "refusing: output exists, run.run would skip"
t = time.time(); run.run(sys.argv[3], sys.argv[4], 100, sys.argv[5]); el = time.time() - t
import numpy as np
T = len(np.load(os.path.join(run.DATA, f"{sys.argv[3]}.npz"))["y"]) // 100
assert len(occ) == T - 1, (len(occ), T)
json.dump(occ, open(os.path.join(sys.argv[5], f"{sys.argv[3]}__{sys.argv[4]}.occ.json"), "w"))
print("BENCH " + json.dumps(dict(elapsed=el, peak_alloc_mib=torch.cuda.max_memory_allocated() / 2**20,
                                 peak_reserved_mib=torch.cuda.max_memory_reserved() / 2**20,
                                 peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)))
'''


def gpu_state():
    """Utilisation (%), used memory (MiB) and listed compute apps; None if nvidia-smi fails (the listing is often
    empty under WSL2, so utilisation and memory are the primary signals)."""
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True)
        a = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], capture_output=True,
                           text=True)
        if q.returncode != 0 or a.returncode != 0:
            return None
        u, m = (float(x) for x in q.stdout.split(","))
        return u, m, len([x for x in a.stdout.split() if x.strip()])
    except (OSError, ValueError):
        return None


def gpu_busy():
    """Busy unless two readings 5 s apart both show < 5% utilisation, < 1000 MiB used (idle baseline about 520) and
    no listed compute app; a failed query counts as busy."""
    for _ in range(2):
        g = gpu_state()
        if g is None or g[0] >= 5 or g[1] >= 1000 or g[2] > 0:
            return True
        time.sleep(5)
    return False


def plan(root, stage):
    """(rep, method, kmax) triples; kmax 0 = MICE."""
    if stage == "a1":
        pols = [("micecp1000_500", 0, 3), ("archcp1000_500", 12, 3), ("snap1000_500", 2, 3), ("snap1000_500", 4, 3),
                ("snap1000_500", 12, 1)]
    else:
        ks = json.load(open(root / "kstar.json"))
        pols = [("micecp1000_500", 0, 3), ("archcp1000_500", 12, 3), ("snap1000_500", ks["snap"], 3)]
    out = []
    for rep in range(3):
        todo = [p for p in pols if rep < p[2]]
        r = rep % len(todo)
        out += [(rep, m, k) for m, k, _ in todo[r:] + todo[:r]]
    return out


def main(root, repo, stage):
    import numpy as np
    root = Path(root)
    data = root / f"data_{stage}"
    data.mkdir(parents=True, exist_ok=True)
    for s in (REAL if stage == "a1" else GRID):
        z = np.load((SRC_C if s.startswith("c_") else SRC) / f"{s}.npz")
        n = 301 * 100 if stage == "a1" else len(z["y"])
        assert len(z["y"]) >= n, (s, len(z["y"]))
        np.savez_compressed(data / f"{s}.npz", X=z["X"][:n], y=z["y"][:n], concept=z["concept"][:n])
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MICE_CKPT_EVERY="1000000", CUDA_LAUNCH_BLOCKING="0", HF_HUB_OFFLINE="1", TABPFN_DISABLE_TELEMETRY="1",
               TABPFN_MODEL_CACHE_DIR=str(Path.home() / "pfn-venvs/cache/tabpfn"))
    env.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    assert env.get("MICE_BACKBONE", "tabpfn") == "tabpfn"
    log = open(root / f"{stage}.jsonl", "a")
    for rep, pol, k in plan(root, stage):
        for s in (REAL if stage == "a1" else GRID):
            out = root / stage / f"rep{rep}" / ("mice" if k == 0 else f"k{k}")
            out.mkdir(parents=True, exist_ok=True)
            if (out / f"{s}__{pol}.occ.json").exists():
                continue
            for f in out.glob(f"{s}__{pol}*"):          # partial outputs of an interrupted run
                f.unlink()
            ooms = 0
            for attempt in range(5):
                while gpu_busy():                       # before every attempt, retries included
                    time.sleep(30)
                before = gpu_state()
                p = subprocess.run([sys.executable, "-c", CHILD, f"{repo}/MICE/code", str(data), s, pol, str(out), str(k)],
                                   env=env, capture_output=True, text=True)
                line = next((l for l in p.stdout.splitlines() if l.startswith("BENCH ")), None)
                rec = dict(stage=stage, rep=rep, policy=pol, kmax=k, stream=s, attempt=attempt,
                           ok=p.returncode == 0 and line is not None, time=time.time(), gpu_before=before)
                if rec["ok"]:
                    rec.update(json.loads(line[6:]))
                    rec["gpu_after"] = gpu_state()          # another process appearing during the run shows here
                else:
                    rec["stderr"] = p.stderr[-500:]
                    if "OutOfMemory" in p.stderr or "out of memory" in p.stderr:
                        ooms += 1                           # infeasible only on a second OOM after a quiet-GPU wait
                        if ooms >= 2:
                            rec["infeasible"] = "out of memory under the 28 GB cap (twice)"
                    for f in out.glob(f"{s}__{pol}*"):
                        f.unlink()
                log.write(json.dumps(rec) + "\n"); log.flush()
                if rec["ok"] or "infeasible" in rec:
                    break
            else:
                log.write(json.dumps(dict(stage=stage, rep=rep, policy=pol, kmax=k, stream=s, failed_exhausted=True)) + "\n")
                log.flush()
    log.write(json.dumps(dict(stage=stage, done=True, time=time.time())) + "\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
