"""Task list of P6 (TOT): gate (a) (REGISTRATION_P6_GATE_A_20261020.md, amended: one A800), the TOT check (tot_check.py,
AMENDMENT_20261020b item 3) and the TOT development grid on the A800 (lr {1e-4, 1e-3, 1e-2} x n_steps {1, 5} x
L {16, 32} x lambda {1e-6, 1e-5, 1e-4} x the 5 development streams = 180 tasks; deterministic mode; venv-tot). Order on
the cluster: gate (a), then the check, then the grid only if gate (a) passed and the check says "proceed".
Usage: python make_tasks_p6.py (writes tasks_p6.jsonl)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_tasks_stage2 as M

tasks = []
out = "{RUNS}/mice-tot-gate-a"
tasks.append(dict(id="p6_gate_a:etth2_h1", set="p6_gate_a", gpu="exclusive", cwd="{REPO}/experiments/clean_rerun_mice_h800",
                  cmd=["bash", "{REPO}/experiments/clean_rerun_mice_h800/tot_gate_a.sh", "{PYTOTA}", out], env={},
                  outputs=[out + "/gate_a.json"], est_s=None,
                  schema={out + "/gate_a.json": {"json": sorted(["rc", "wall_s", "mse", "mae", "target_mean", "target_sd",
                                                                  "threshold", "verdict"])}}))
chk = "{RUNS}/mice-tot-check/tot_check.json"
tasks.append(dict(id="p6_tot_check:a800", set="p6_tot_check", gpu="exclusive", cwd="{REPO}",
                  cmd=["{PYTOTA}", "{REPO}/experiments/clean_rerun_mice_h800/tot_check.py", chk],
                  env=dict(M.DEVICE["tot"]["env"]), outputs=[chk], est_s=None,
                  schema={chk: {"json": sorted(["gpu", "s_per_batch", "projected_dev_gpu_h", "projected_dev_cpu_h",
                                                "aggregate_speedup", "gate_b_predictions_differ", "verdict"])}}))
for lr in M.LR:
    for st in M.ST:
        for L in M.AXES["tot"][0].split():
            for lam in M.AXES["tot"][1].split():
                for s in M.DEV:
                    t = M.task("tot_dev", "tot", s, "{REPO}/MICE/data", f"{M.REPO}/MICE/data", L, lr, st, lam, "dev_a800")
                    tasks.append(t)
n = {k: sum(t["set"] == k for t in tasks) for k in ("p6_gate_a", "p6_tot_check", "tot_dev")}
assert n == {"p6_gate_a": 1, "p6_tot_check": 1, "tot_dev": 180}, n
assert len({t["id"] for t in tasks}) == len(tasks)
with open(f"{HERE}/tasks_p6.jsonl", "w") as f:
    for t in tasks:
        f.write(json.dumps(t) + "\n")
print(n)
