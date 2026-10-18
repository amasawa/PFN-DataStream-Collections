"""Long-lived GPU worker for the Table 1 fill (operational; env/MACHINE_LOG.md 2026-10-16: the fatal CUDA faults of this
machine are triggered mainly by process / context creation, so one process runs many tasks). <queue>/tasks.txt: one
JSON object per line, {"kind": "ts" | "dr", ...arguments of run_ts.run / run_drtabpfn.run}. A task is claimed with an
atomic mkdir (<queue>/claims/<line>); the claim of the task in progress is written to <queue>/running_<worker>, so the
restart loop (pool_gpu.sh) releases it when the process dies. Outputs are written atomically by the run functions,
which skip finished outputs (and run_drtabpfn resumes from its checkpoint).
Usage: python pool_gpu.py <queue dir> <worker id>"""
import json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    q, w = sys.argv[1], sys.argv[2]
    os.makedirs(f"{q}/claims", exist_ok=True)
    tasks = [json.loads(l) for l in open(f"{q}/tasks.txt") if l.strip()]
    kinds = {t["kind"] for t in tasks}
    assert len(kinds) == 1, "one kind per queue (one venv)"
    kind = kinds.pop()
    if kind == "ts":
        import torch
        import run_ts
        torch.set_num_threads(1)
        meth = {t["method"] for t in tasks}; assert len(meth) == 1
        sys.path.insert(0, f"{run_ts.EXT}/{run_ts.METHODS[meth.pop()].REPO}")
    else:
        import run_drtabpfn
        model = run_drtabpfn.get_model()
    for i, t in enumerate(tasks):
        try:
            os.mkdir(f"{q}/claims/{i}")
        except FileExistsError:
            continue
        open(f"{q}/running_{w}", "w").write(str(i))
        t0 = time.time(); a = {k: v for k, v in t.items() if k != "kind"}
        if kind == "ts":
            run_ts.run(a["data"], a["out"], a["stream"], a["method"], a["L"], a["lr"], a["steps"], a.get("mech"))
        else:
            run_drtabpfn.run(model, a["data"], a["stream"], 100, a["out"])
        os.remove(f"{q}/running_{w}")
        with open(f"{q}/progress.txt", "a") as f:
            f.write(f"{time.strftime('%T')} w{w} ok {i} {a.get('stream')} {time.time() - t0:.0f}s\n")


if __name__ == "__main__":
    main()
