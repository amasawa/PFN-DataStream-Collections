"""Task list of the clean MICE rerun on the H800 cluster (PLAN.md): every GPU-computed output that a MICE paper
table, figure or number depends on, with the command of its original run. Enumerated from the original outputs on the
local machine (one task per output that the original driver produces), so the list is complete by construction.
CPU-only outputs (river and trained learners, derived replays such as "mice", "mice2") are not tasks: the CPU outputs
are kept, the replays are recomputed by the analysis scripts from the new caches.
Placeholders resolved on the cluster: {REPO} repository clone, {RUNS} run roots ($HOME/pfn-runs), {PY} MICE venv,
{PYDR} Drift-Resilient TabPFN venv, {PYTOT} dtmoe / TOT venv.
Output: tasks.jsonl (one JSON object per task: id, set, gpu (shared | exclusive), cwd, cmd, env, outputs, est_s).
Usage: python make_tasks.py   (on the local machine, where the original outputs are)"""
import glob, json, os, re
import numpy as np

REPO = "/mnt/c/Users/zhwu9808/Desktop/dataStream"; RUNS = os.path.expanduser("~/pfn-runs")
GPU_METHOD = re.compile(r"^(fifo\d+|ddm\d+|ltm\d+_\d+|winens\d+|oracle\d+|mice\d{3,}|micev\d{3,}(_\d+)?|micecp\d+_\d+|archcp\d+_\d+|arch\d+_\d+|snap\d+_\d+)(\.k\d+)?$")
ENV_OLD = {"OMP_NUM_THREADS": "4", "PYTHONWARNINGS": "ignore"}
ENV_NEW = {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "CUDA_LAUNCH_BLOCKING": "0",
           "MICE_CKPT_EVERY": "10", "HF_HUB_OFFLINE": "1", "TABPFN_DISABLE_TELEMETRY": "1"}
tasks = []
FILTERED = set()   # (set, method) of original outputs that are not GPU tasks: printed for reconciliation


def est(f):
    try:
        return round(float(np.nansum(np.load(f)["wt"])))
    except Exception:
        return None


def schema(orig):
    """Structure of an original output (never its values): npz -> {key: [shape, dtype]} (wall time, peak memory
    excepted), pkl -> type and keys, csv -> columns and rows, jsonl -> lines, json -> keys. None if no original."""
    import pickle, csv
    if not os.path.exists(orig):
        return None
    if orig.endswith(".npz"):
        with np.load(orig, allow_pickle=True) as z:
            return {"npz": {k: [list(z[k].shape), str(z[k].dtype)] for k in z.files if k not in ("wt", "peak_mem")}}
    if orig.endswith(".pkl"):
        o = pickle.load(open(orig, "rb"))
        return {"pkl": [type(o).__name__, sorted(map(str, o.keys())) if isinstance(o, dict) else len(o) if isinstance(o, (list, tuple)) else None]}
    if orig.endswith(".csv"):
        r = list(csv.reader(open(orig)))
        return {"csv": [r[0], len(r) - 1]}
    if orig.endswith(".jsonl"):
        return {"jsonl": sum(1 for l in open(orig) if l.strip())}
    if orig.endswith(".json"):
        return {"json": sorted(json.load(open(orig)))}
    return None


def local(o):
    """Original location of an output template (benchmark roots "<root>-h800" -> the original root)."""
    return o.replace("{REPO}", REPO).replace("{RUNS}", RUNS).replace("-h800/", "/")


def add(set_, id_, cwd, cmd, env, outputs, est_s, gpu="shared"):
    assert outputs, f"no expected output for {set_}:{id_}"
    tasks.append(dict(id=f"{set_}:{id_}", set=set_, gpu=gpu, cwd=cwd, cmd=cmd, env=env, outputs=outputs, est_s=est_s,
                      schema={o: schema(local(o)) for o in outputs}))


# 1. MICE/results_* (run.py family; the run_scripts used OMP_NUM_THREADS=4)
RESULTS = {"results_grid_test": {}, "results_grid_test3": {}, "results_test": {}, "results_heldout": {},
           "results_heldout2": {}, "results_heldout3": {}, "results_heldout4": {},
           "results_heldout_tabicl": {"MICE_BACKBONE": "tabicl"}, "results_heldout3_tabicl": {"MICE_BACKBONE": "tabicl"},
           "results_heldout4_tabicl": {"MICE_BACKBONE": "tabicl"}, "results_heldout4_tabicl_e": {"MICE_BACKBONE": "tabicl"},
           "results_heldout3_seed1": {"MICE_SEED": "1"}, "results_heldout4_seed1": {"MICE_SEED": "1"},
           # development runs (numbers in the text, e.g. the regret over 33 development streams); selections stay frozen
           "results_dev": {}, "results_grid_dev": {}, "results_dt_dev": {}}
for d, extra in RESULTS.items():
    script = "run_seed.py" if "MICE_SEED" in extra else "run.py"
    for f in sorted(glob.glob(f"{REPO}/MICE/{d}/*__*.npz")):
        s, m = os.path.basename(f)[:-4].split("__")
        if not GPU_METHOD.match(m):
            FILTERED.add((d, m)); continue
        outs = [f"{{REPO}}/MICE/{d}/{s}__{m}{e}" for e in (".npz", ".pkl", ".closes.pkl") if os.path.exists(f[:-4] + e)]
        add(d, f"{s}__{m}", "{REPO}/MICE/code", ["{PY}", "-u", script, "--streams", s, "--methods", m, "--out", f"../{d}"],
            {**ENV_OLD, **extra}, outs, est(f))
for f in sorted(glob.glob(f"{REPO}/MICE/results_probs/*__probs.npz")):   # run_probs.py writes the npz and __probs
    s, m = os.path.basename(f)[:-len("__probs.npz")].split("__")
    add("results_probs", f"{s}__{m}", "{REPO}/MICE/code", ["{PY}", "-u", "run_probs.py", "--streams", s, "--methods", m,
        "--out", "../results_probs"], dict(ENV_OLD), [f"{{REPO}}/MICE/results_probs/{s}__{m}.npz", f"{{REPO}}/MICE/results_probs/{s}__{m}__probs.npz"],
        est(f"{REPO}/MICE/results_probs/{s}__{m}.npz"))

for s in sorted({os.path.basename(f).split("__")[0] for f in glob.glob(f"{REPO}/MICE/results_delay_dev/*__d10__*")}):
    outs = sorted("{REPO}/MICE/results_delay_dev/" + os.path.basename(f) for f in glob.glob(f"{REPO}/MICE/results_delay_dev/{s}__d10__*"))
    add("results_delay_dev", s, "{REPO}/MICE/code", ["{PY}", "-u", "run_delay.py", "--delay", "10", "--streams", s,   # label delay 10
        "--out", "../results_delay_dev"], dict(ENV_OLD), outs, est(f"{REPO}/MICE/results_delay_dev/{s}__d10__fifo.npz"))

# 2. run roots with a tasks.txt (fresh process per task; outputs P/ or P_k<K>/)
ROOTS = {"mice-r14-test": "mice_r14", "mice-r14-exist": "mice_r14", "mice-r14b-acc": "mice_r14", "mice-r14-confirm": "mice_r14",
         "mice-table1-cp-gen": "mice_r14", "mice-main-cp-grid10": "mice_r14",
         "mice-confirm-cp-20261017": "mice_confirm_cp_20261017", "mice-table1-probs-gen": "mice_confirm_cp_20261017",
         # reconstructed with the committed code (PLAN.md, "Reconstructed runs"; user decision 2026-10-18)
         "mice-r14-dev": "mice_r14", "mice-r14-devtrim": "trim1"}
for r, exp in ROOTS.items():
    for line in open(f"{RUNS}/{r}/tasks.txt"):
        if not line.strip():
            continue
        s, m = line.split()[:2]
        if not GPU_METHOD.match(m) and m not in ("ddm1000", "ltm1000_75"):
            FILTERED.add((r, m)); continue             # arf / srp (CPU, run_river) are kept
        k = re.search(r"\.k(\d+)$", m); sub = f"P_k{k.group(1)}" if k else "P"; base = m.split(".k")[0]
        orig = f"{RUNS}/{r}/{sub}/{s}__{base}.npz"
        if not os.path.exists(orig):
            print("no original, skipped:", r, s, m); continue
        outs = [f"{{RUNS}}/{r}/{sub}/{s}__{base}{e}" for e in (".npz", ".pkl", ".closes.pkl", "__probs.npz")
                if os.path.exists(f"{RUNS}/{r}/{sub}/{s}__{base}{e}")]
        drv = ("{REPO}/experiments/clean_rerun_mice_h800/run_task_trim1.py" if exp == "trim1"
               else f"{{REPO}}/experiments/{exp}/run_task.py")
        add(r, f"{s}__{m}", "{RUNS}/" + r, ["{PY}", drv, "{RUNS}/" + r, s, m], dict(ENV_NEW), outs, est(orig))

# 3. TKDE control run (supervisor tasks.json; its own code snapshot in source/ and controller/)
R = "mice-tkde-control-20261009"
for t in json.load(open(f"{RUNS}/{R}/tasks.json")):
    f = f"{RUNS}/{R}/{t['out']}/{t['stream']}__{t['method']}.npz"
    outs = [f"{{RUNS}}/{R}/{t['out']}/{t['stream']}__{t['method']}{e}" for e in (".npz", ".pkl", ".closes.pkl") if os.path.exists(f[:-4] + e)]
    add(R, t["id"], "{RUNS}/" + R, ["{PY}", f"{{RUNS}}/{R}/controller/worker.py", "{RUNS}/" + R, t["id"]],
        {**ENV_NEW, "PYTHONDONTWRITEBYTECODE": "1"}, outs, est(f))

# 4. Round 13 pool capacity (pool_cap_run.py <index>, MICE_R13_K; reads kstar.json of mice-r13-bench as an input)
import subprocess
IDX = json.loads(subprocess.run([os.path.expanduser("~/pfn-venvs/venv/bin/python"), "-c",
    "import importlib.util, json, sys; sys.argv = ['x']; r = {}\n"
    "for n in ('pool_cap_run', 'seg_origin_run'):\n"
    "    sp = importlib.util.spec_from_file_location(n, n + '.py'); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)\n"
    "    r[n] = m.TASKS\n"
    "print(json.dumps(r))"], cwd=f"{REPO}/MICE/code", capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1])
for k in (2, 4):
    for i, (st, m) in enumerate(IDX["pool_cap_run"]):
        f = f"{RUNS}/mice-r13-acc/k{k}/{st}__{m}.npz"
        add("mice-r13-acc", f"k{k}_{i}", "{REPO}/MICE/code", ["{PY}", "{REPO}/MICE/code/pool_cap_run.py", str(i)],
            {**ENV_NEW, "MICE_R13_K": str(k)}, [f"{{RUNS}}/mice-r13-acc/k{k}/{st}__{m}{e}" for e in (".npz", ".pkl", ".closes.pkl")
                                                if os.path.exists(f[:-4] + e)], est(f))

# 5. Segment-origin control (seg_origin_run.py <index>, 16 tasks) and the oracle recall (oracle_recall.py, one job)
for i, (st, m) in enumerate(IDX["seg_origin_run"]):
    f = f"{RUNS}/mice_seg_origin_r12/P/{st}__{m}.npz"
    add("mice_seg_origin_r12", str(i), "{REPO}/MICE/code", ["{PY}", "{REPO}/MICE/code/seg_origin_run.py", str(i)], dict(ENV_NEW),
        [f"{{RUNS}}/mice_seg_origin_r12/P/{st}__{m}{e}" for e in (".npz", ".pkl", ".closes.pkl") if os.path.exists(f[:-4] + e)], est(f))
add("mice_oracle_r11", "all", "{REPO}/MICE/code", ["{PY}", "{REPO}/MICE/code/oracle_recall.py"], dict(ENV_NEW),
    sorted("{RUNS}/mice_oracle_r11/" + os.path.basename(f) for f in glob.glob(f"{RUNS}/mice_oracle_r11/*.csv")), None)

# 6. Benchmarks (timing: one process alone on its GPU). They write into new roots "<root>-h800" (inputs copied there),
#    so the frozen selections of the original roots (kstar.json, m_star.json, read by later runs) are never replaced.
add("mice-tkde-bench-20261009-h800", "bench", "{REPO}", ["{PY}", "{REPO}/experiments/mice_tkde_control/bench_resources.py",
    "{RUNS}/mice-tkde-bench-20261009-h800", "{REPO}"], dict(ENV_NEW), ["{RUNS}/mice-tkde-bench-20261009-h800/bench.jsonl"], None, gpu="exclusive")
for a in ("a1", "a2"):
    add("mice-r13-bench-h800", a, "{REPO}", ["{PY}", "{REPO}/experiments/mice_tkde_control/bench_pools.py", "{RUNS}/mice-r13-bench-h800", "{REPO}", a],
        dict(ENV_NEW), [f"{{RUNS}}/mice-r13-bench-h800/{a}.jsonl"], None, gpu="exclusive")
    add("mice-r14b-bench-h800", a, "{REPO}", ["{PY}", "{REPO}/experiments/mice_r14/bench_cp.py", "{RUNS}/mice-r14b-bench-h800", "{REPO}", a],
        dict(ENV_NEW), [f"{{RUNS}}/mice-r14b-bench-h800/{a}.jsonl"], None, gpu="exclusive")

# 7. Table 1 new baselines on the GPU: Drift-Resilient TabPFN (92 streams). dtmoe and TOT are added after their
#    qualification / implementation (PLAN.md), the CPU baselines (fsnet, onenet, adaptz, shifts) are kept.
for line in open(f"{RUNS}/mice-table1-newbase/q_drtabpfn/tasks.txt"):
    t = json.loads(line)
    data = t["data"].replace(f"{REPO}", "{REPO}").replace(RUNS, "{RUNS}")
    add("drtabpfn", t["stream"], "{REPO}", ["{PYDR}", "{REPO}/experiments/mice_table1_fill_20261018/run_drtabpfn.py",
        "--data", data, "--out", "{RUNS}/mice-table1-newbase/drtabpfn", "--streams", t["stream"]],
        {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
        [f"{{RUNS}}/mice-table1-newbase/drtabpfn/{t['stream']}__drtabpfn.npz"], None)

# 8. dtmoe (gpu_verify AMENDMENT_20261018b): strict determinism on the H800; the development grid of PLAN_BASELINES.md
#    (180 tasks) into dev_h800/P. Its test runs are added after the configuration is frozen from this grid.
DEV5 = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
        "insects_incremental_reoccurring_balanced"]
TSENV = {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "TS_DEVICE": "cuda",
         "TS_DETERMINISTIC": "1", "CUBLAS_WORKSPACE_CONFIG": ":4096:8"}
for lr in ("1e-4", "1e-3", "1e-2"):
    for st in ("1", "5"):
        for L in ("16", "32"):
            for mech in ("1", "2", "3"):
                for s in DEV5:
                    tag = f"dtmoe_L{L}_lr{float(lr):g}_s{st}_m{float(mech):g}"
                    add("dtmoe_dev", f"{s}__{tag}", "{REPO}", ["{PYTOT}", "{REPO}/experiments/mice_table1_fill_20261018/run_ts.py",
                        "--data", "{REPO}/MICE/data", "--out", "{RUNS}/mice-table1-newbase/dev_h800/P", "--streams", s,
                        "--method", "dtmoe", "--L", L, "--lr", lr, "--steps", st, "--mech", mech], dict(TSENV),
                        [f"{{RUNS}}/mice-table1-newbase/dev_h800/P/{s}__{tag}.npz"], None)

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.jsonl"), "w") as f:
    for t in tasks:
        f.write(json.dumps(t) + "\n")
print("original outputs that are not tasks (CPU or derived; check):", sorted(FILTERED))
import collections
c = collections.Counter(t["set"] for t in tasks); e = collections.defaultdict(float)
for t in tasks:
    e[t["set"]] += (t["est_s"] or 0) / 3600
for k, v in c.items():
    print(f"{k:32s} {v:5d} tasks  {e[k]:7.1f} h (original wall time, where recorded)")
print(len(tasks), "tasks;", round(sum(e.values())), "h recorded")
