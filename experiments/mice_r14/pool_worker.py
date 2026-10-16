"""Round 14.b: long-lived worker. One process runs many (stream, method) tasks of run_task.py in turn, so a CUDA context
is created once per process instead of once per task (the driver faults of env/MACHINE_LOG.md, 2026-10-16, grow with
process churn and concurrency). Each task is run exactly as run_task.py runs it: same run.run, same data, same output
paths, the kmax patch applied for ".k<K>" methods and removed afterwards; checkpoints and resumption are those of run.run.

Claims use the same mkdir directories as worker.sh (<root>/claims/<stream>__<method>). The task held by a process is
written to <root>/held/w<id> before it starts and removed when it ends, so that a restarted process (pool_worker.sh)
resumes it first. Usage: python pool_worker.py <root> <worker id> [--tasks <file>] [--verify <out dir>]
  --verify: run the tasks of <file> into <out dir> without claims (bit-identity test against existing outputs)."""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import run  # noqa: E402

_INIT = run.PoolControl.__init__


def run_one(data, out_root, stream, method):
    """Same effect as `python run_task.py <root> <stream> <method>` with run.DATA = data."""
    run.DATA = data
    out = f"{out_root}/P"
    run.PoolControl.__init__ = _INIT
    if ".k" in method:
        method, k = method.split(".k")
        k = int(k)
        assert method.startswith(("snap", "arch")), method

        def _init_k(self, *a, **kw):
            _INIT(self, *a, **kw)
            self.kmax = k
        run.PoolControl.__init__ = _init_k
        out = f"{out_root}/P_k{k}"
    os.makedirs(out, exist_ok=True)
    try:
        run.run(stream, method, 100, out)
    finally:
        run.PoolControl.__init__ = _INIT


def log(root, wid, msg):
    with open(f"{root}/progress.txt", "a") as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} p{wid} {msg}\n")


if __name__ == "__main__":
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn"
    root, wid = sys.argv[1], sys.argv[2]
    opts = dict(zip(sys.argv[3::2], sys.argv[4::2]))
    tasks = [ln.split() for ln in open(opts.get("--tasks", f"{root}/tasks.txt")) if ln.strip()]
    if "--verify" in opts:
        for s, m in tasks:
            t0 = time.time()
            run_one(f"{root}/data", opts["--verify"], s, m)
            print("verify", s, m, f"{time.time() - t0:.0f}s", flush=True)
        sys.exit(0)
    os.makedirs(f"{root}/held", exist_ok=True)
    held = f"{root}/held/w{wid}"
    queue = []
    if os.path.exists(held):                       # the task this worker held when its previous process died
        queue.append(open(held).read().split())
    queue += tasks
    for s, m in queue:
        if not (os.path.exists(held) and open(held).read().split() == [s, m]):
            try:
                os.mkdir(f"{root}/claims/{s}__{m}")
            except FileExistsError:
                continue
            with open(held + ".tmp", "w") as fh:
                fh.write(f"{s} {m}")
            os.replace(held + ".tmp", held)
        print("TASK", s, m, flush=True)
        run_one(f"{root}/data", root, s, m)
        log(root, wid, f"ok {s} {m}")
        os.remove(held)
    log(root, wid, "finished")
