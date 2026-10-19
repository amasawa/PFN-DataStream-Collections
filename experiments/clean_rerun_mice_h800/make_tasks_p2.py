"""Task list of phase P2 of the clean MICE rerun (ACTIVATION_20261019.md, item 4): every CPU-computed output that a
MICE paper table or number depends on, with the command and thread settings of its original run, plus the registered
development grid of the four CPU baselines of Table 1. Enumerated from the original outputs on the local machine (one
task per output), so the list is complete by construction. Derived replays ("mice", "mice2", "mice3", "mice3t") are not
tasks: the analysis scripts recompute them from the new caches.
Placeholders resolved on the cluster: {REPO}, {RUNS} as in P1; {PYST} the river / trained-learner venv (stream),
{PYTS} the venv of the CPU baselines of Table 1 (tsbase). Every task has gpu = "cpu" and CUDA_VISIBLE_DEVICES = "".
Output: tasks_p2.jsonl (same fields as tasks.jsonl). Usage: python make_tasks_p2.py (on the local machine)."""
import collections, glob, json, os
import numpy as np

REPO = "/mnt/c/Users/zhwu9808/Desktop/dataStream"; RUNS = os.path.expanduser("~/pfn-runs")
tasks = []
SKIPPED = collections.Counter()


def est(f):   # as make_tasks.py (not imported: importing it would rewrite the frozen tasks.jsonl)
    try:
        return round(float(np.nansum(np.load(f)["wt"])))
    except Exception:
        return None


def schema(orig):   # as make_tasks.py, npz only (every P2 output is an npz): {key: [shape, dtype]}, never values
    with np.load(orig, allow_pickle=True) as z:
        return {"npz": {k: [list(z[k].shape), "<U" if z[k].dtype.kind == "U" else str(z[k].dtype)]
                        for k in z.files if k not in ("wt", "te", "peak_mem")}}


RIVER = ("arf", "srp", "hat", "levbag", "adwinbag")
NOGPU = {"CUDA_VISIBLE_DEVICES": ""}
OMP = lambda n: {"OMP_NUM_THREADS": str(n), "OPENBLAS_NUM_THREADS": str(n), "MKL_NUM_THREADS": str(n), "PYTHONWARNINGS": "ignore"}


def add(set_, id_, cwd, cmd, env, outputs, orig):
    assert os.path.exists(orig), orig
    tasks.append(dict(id=f"{set_}:{id_}", set=set_, gpu="cpu", cwd=cwd, cmd=cmd, env={**env, **NOGPU}, outputs=outputs,
                      est_s=est(orig), schema={outputs[0]: schema(orig)}))


def env_results(d, m):
    """Thread settings of the original run_scripts (MICE/code/run_scripts): run_river.sh and run_river_heldout.sh set
    none; run_trained.sh, run_trained_ext.sh, run_trained_ext2.sh 1 (rff4000 in ext2: 2); run_trained_ext3.sh,
    run_heldout2_cpu.sh, run_heldout34_cpu.sh 2."""
    if d in ("results_river", "results_heldout"):
        return {}
    if d in ("results_heldout2", "results_heldout34_trained") or m.startswith("mooe_rff4000"):
        return OMP(2)
    return OMP(1)


# 1. MICE/results_*: river learners (run_river.py) and trained learners (run_trained.py: mooe_*, nse)
for d in ("results_river", "results_heldout", "results_trained_dev", "results_trained", "results_heldout2",
          "results_heldout34_trained"):
    for f in sorted(glob.glob(f"{REPO}/MICE/{d}/*__*.npz")):
        s, m = os.path.basename(f)[:-4].split("__")
        if not (m in RIVER or m == "nse" or m.startswith("mooe_")):
            SKIPPED[(d, m)] += 1; continue             # GPU methods (P1) and derived replays ("mice", "mice2", ...)
        drv = "run_river.py" if m in RIVER else "run_trained.py"
        add(d, f"{s}__{m}", "{REPO}/MICE/code", ["{PYST}", "-u", drv, "--streams", s, "--methods", m, "--out", f"../{d}"],
            env_results(d, m), [f"{{REPO}}/MICE/{d}/{s}__{m}.npz"], f)

# 2. Trained learners on grid20 (experiments/mice_main_table_20261017/PLAN.md item 1). The thread setting of the
#    original launch was not recorded; 1 thread (its reproduction check against grid10, run with 1 and 2 threads,
#    matched exactly).
R = "mice-main-trained-grid20"
for f in sorted(glob.glob(f"{RUNS}/{R}/*__*.npz")):
    s, m = os.path.basename(f)[:-4].split("__")
    drv = "run_river.py" if m in RIVER else "run_trained.py"
    add(R, f"{s}__{m}", "{REPO}/MICE/code", ["{PYST}", "-u", drv, "--streams", s, "--methods", m, "--out", "{RUNS}/" + R],
        OMP(1), [f"{{RUNS}}/{R}/{s}__{m}.npz"], f)

# 3. Trained learners with probabilities on the 92 streams of Table 1 (experiments/mice_table1_fill_20261018/run_cpu.sh)
R = "mice-table1-trained-probs"
for name in ("tasks_mooe.txt", "tasks_other.txt"):
    for line in open(f"{RUNS}/{R}/{name}"):
        data, s, m = line.split()
        data = "{REPO}/MICE/data" if data.endswith("MICE/data") else "{RUNS}/mice-confirm-cp-20261017/data"
        add(R, f"{s}__{m}", "{REPO}", ["{PYST}", "{REPO}/experiments/mice_table1_fill_20261018/run_trained_probs.py",
            "--data", data, "--out", "{RUNS}/" + R + "/P", "--streams", s, "--methods", m],
            {k: v for k, v in OMP(1).items() if k != "PYTHONWARNINGS"}, [f"{{RUNS}}/{R}/P/{s}__{m}.npz"],
            f"{RUNS}/{R}/P/{s}__{m}.npz")

# 4. arf / srp of the confirmation set (experiments/mice_confirm_cp_20261017/run_task.py, CPU branch)
R = "mice-confirm-cp-20261017"
for f in sorted(glob.glob(f"{RUNS}/{R}/P/*__arf.npz") + glob.glob(f"{RUNS}/{R}/P/*__srp.npz")):
    s, m = os.path.basename(f)[:-4].split("__")
    add(R + "-cpu", f"{s}__{m}", "{RUNS}/" + R, ["{PYST}", "{REPO}/experiments/mice_confirm_cp_20261017/run_task.py",
        "{RUNS}/" + R, s, m], {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
        [f"{{RUNS}}/{R}/P/{s}__{m}.npz"], f)

# 5. CPU baselines of Table 1: the registered development grid (PLAN_BASELINES.md "Tuning", tune_ts.sh) into
#    dev_cluster/P. Selection, the one-time extension and the tests follow amendment c and are registered as P2b
#    after this grid returns (the extension depends on the selection).
DEV = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
       "insects_incremental_reoccurring_balanced"]
GRID = {"fsnet": ("16 32", "0.5 0.75 0.9"), "onenet": ("16 32", "0.5 0.75 0.9"), "adaptz": ("1 16", "1e-4 1e-3 1e-2"),
        "shifts": ("16 32", "0.5 1 2")}
for m, (LS, MS) in GRID.items():
    for lr in ("1e-4", "1e-3", "1e-2"):
        for st in ("1", "5"):
            for L in LS.split():
                for mech in MS.split():
                    for s in DEV:
                        tag = f"{m}_L{L}_lr{float(lr):g}_s{st}_m{float(mech):g}"
                        add("ts_dev", f"{s}__{tag}", "{REPO}", ["{PYTS}", "{REPO}/experiments/mice_table1_fill_20261018/run_ts.py",
                            "--data", "{REPO}/MICE/data", "--out", "{RUNS}/mice-table1-newbase/dev_cluster/P", "--streams", s,
                            "--method", m, "--L", L, "--lr", lr, "--steps", st, "--mech", mech],
                            {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
                            [f"{{RUNS}}/mice-table1-newbase/dev_cluster/P/{s}__{tag}.npz"],
                            f"{RUNS}/mice-table1-newbase/dev/P/{s}__{tag}.npz")

print("skipped (GPU methods of P1 or derived replays; check):", sorted(SKIPPED))
ids = [t["id"] for t in tasks]
assert len(ids) == len(set(ids)), "duplicate task ids"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks_p2.jsonl"), "w") as f:
    for t in tasks:
        f.write(json.dumps(t) + "\n")
c = collections.Counter(t["set"] for t in tasks); e = collections.defaultdict(float)
for t in tasks:
    e[t["set"]] += (t["est_s"] or 0) / 3600
for k, v in c.items():
    print(f"{k:32s} {v:5d} tasks  {e[k]:7.1f} CPU-h (original wall time)")
print(len(tasks), "tasks;", round(sum(e.values())), "CPU-h recorded")
