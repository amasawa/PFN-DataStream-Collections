"""Runner of the clean MICE rerun on the H800 cluster (PLAN.md, HANDOFF.md). Every task of tasks.jsonl is the command
of its original run; this runner only resolves the placeholders, runs the command in a fresh process and records
what happened. It never changes a computation.

Placeholders, from the environment: REPO (repository clone at the registered commit), RUNS (run roots, = $HOME/pfn-runs
on the cluster: several drivers use ~/pfn-runs), PY (MICE venv), PYDR (Drift-Resilient TabPFN venv), PYTOT (dtmoe/TOT),
PYST (river / trained learners, P2), PYTS (CPU baselines of Table 1, P2). A variable may be unset when no task of the
list uses it; a task that uses an unset one stops with an error.
Task list: tasks.jsonl (P1), or the file given by "--tasks <file>" (e.g. tasks_p2.jsonl), in every mode below.
CPU tasks (gpu = "cpu", P2) are taken by "worker <slot> --gpu cpu".

  python rerun.py worker <slot> [--sets s1,s2] [--gpu shared|exclusive|cpu] [--tasks <file>]
      claims tasks one at a time (atomic mkdir in $RUNS/_rerun/claims) and runs them until none is left. Before the
      first attempt and after every failed attempt, any partial output or checkpoint of the task is moved to
      $RUNS/_rerun/quarantine/<task>/<attempt>/, so every attempt starts from initialisation (no resumed state).
      At most 3 attempts in all, counted across workers and restarts ($RUNS/_rerun/attempts/; benchmarks: 1, a failed
      benchmark is reported, not retried); then the task is given up. Done = the attempt returned 0 and every expected
      output parses and has the structure of the original output (keys, shapes, dtypes; pkl type and keys; csv
      columns and rows; jsonl lines; never values). Outputs found without such an attempt are quarantined, never
      accepted. GPU health (ECC errors, throttling) is recorded before and after every attempt.
  python rerun.py qualify <task id> <dir>
      runs one task twice in fresh processes with RUNS redirected to <dir>/a and <dir>/b (inputs linked) and compares
      the two output sets byte for byte (determinism probe, PLAN.md checks 1).
  python rerun.py recheck <task id> <dir>
      during production (PLAN.md, checks 2): runs one finished task once more into <dir>/a (as qualify) and compares
      it byte for byte with its production outputs.
  python rerun.py status
      counts done / given up / claimed / left per set.
  python rerun.py release
      after the jobs of a worker ended (Slurm time limit, node failure): removes the claims of tasks that are neither
      done nor given up, so the next workers take them (from initialisation: their partial outputs are quarantined
      first). Run it only when no worker is running.
Records: $RUNS/_rerun/done/<id>.json (host, GPU, start, end, attempts, return codes), logs in $RUNS/_rerun/logs/."""
import json, os, shutil, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
if "--tasks" in sys.argv:                                   # removed from argv before the mode is read
    _i = sys.argv.index("--tasks")
    if _i + 1 >= len(sys.argv):
        raise SystemExit("--tasks needs a file name")
    TASK_FILE = sys.argv[_i + 1]; del sys.argv[_i:_i + 2]
else:
    TASK_FILE = "tasks.jsonl"
TASKS = [json.loads(l) for l in open(os.path.join(HERE, TASK_FILE)) if l.strip()]
VARS = ("REPO", "RUNS", "PY", "PYDR", "PYTOT", "PYST", "PYTS")


def fill(x, env):
    if isinstance(x, list):
        return [fill(v, env) for v in x]
    if isinstance(x, dict):
        return {k: fill(v, env) for k, v in x.items()}
    for v in VARS:
        if "{" + v + "}" in x and not env.get(v):
            raise SystemExit(f"placeholder {{{v}}} used but the environment variable {v} is not set")
        x = x.replace("{" + v + "}", env.get(v, ""))
    return x


def check_vars(tasks, env):
    """Stop before anything is claimed or run if a selected task uses a placeholder whose variable is unset."""
    used = {v for t in tasks for v in VARS if "{" + v + "}" in json.dumps(t)}
    missing = sorted(v for v in used if not env.get(v))
    if missing:
        raise SystemExit(f"environment variables not set for the selected tasks: {missing}")


def safe(task_id):
    return task_id.replace("/", "_").replace(":", "__")


def gpu_name():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader", "-i",
                               os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"unknown ({e})"


def health():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=index,ecc.errors.uncorrected.volatile.total,"
                               "clocks_throttle_reasons.active,temperature.gpu,memory.used", "--format=csv,noheader"],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"unknown ({e})"


def valid(o, sch):
    """Parse the output and compare its structure with that of the original (tasks.jsonl "schema"; never values)."""
    if not os.path.exists(o):
        return False
    try:
        import numpy as np, pickle, csv
        if o.endswith(".npz"):
            with np.load(o, allow_pickle=True) as z:
                got = {k: [list(z[k].shape), "<U" if z[k].dtype.kind == "U" else str(z[k].dtype)]
                       for k in z.files if k not in ("wt", "te", "peak_mem")}
            return bool(sch) and got == sch["npz"]          # every task registers its structure (tasks.jsonl)
        if o.endswith(".pkl"):
            x = pickle.load(open(o, "rb"))
            got = [type(x).__name__, sorted(map(str, x.keys())) if isinstance(x, dict) else len(x) if isinstance(x, (list, tuple)) else None]
            return bool(sch) and got == sch["pkl"]
        if o.endswith(".csv"):
            r = list(csv.reader(open(o)))
            return bool(sch) and [r[0], len(r) - 1] == sch["csv"]
        if o.endswith(".jsonl"):
            n = 0
            for l in open(o):
                if l.strip():
                    json.loads(l); n += 1
            return bool(sch) and n == sch["jsonl"]
        if o.endswith(".json"):
            x = json.load(open(o))
            return bool(sch) and sorted(x) == sch["json"]
        return os.path.getsize(o) > 0
    except Exception:
        return False


def complete(t, env):
    outs = fill(t["outputs"], env)
    sch = t.get("schema", {})
    return bool(outs) and all(valid(o, sch.get(k)) for o, k in zip(outs, t["outputs"])) and not any(
        os.path.exists(o[:-4] + e) for o in outs if o.endswith(".npz") for e in (".ckpt", ".ckpt.npz"))


def quarantine(t, env, base, attempt):
    """Move partial outputs and checkpoints of the task out of the way (never delete them)."""
    q = f"{base}/quarantine/{safe(t['id'])}/{attempt}"
    moved = []
    for o in fill(t["outputs"], env):
        stem = o[:-4] if o.endswith((".npz", ".pkl", ".csv")) else o
        for cand in (o, stem + ".ckpt", stem + ".ckpt.tmp", stem + ".ckpt.npz", stem + ".ckpt.tmp.npz", stem + ".tmp.npz",
                     o + ".tmp"):
            if os.path.exists(cand):
                os.makedirs(q, exist_ok=True); shutil.move(cand, f"{q}/{os.path.basename(cand)}"); moved.append(cand)
    return moved


KEEP = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TMPDIR", "LD_LIBRARY_PATH", "CUDA_VISIBLE_DEVICES",
        "TABPFN_MODEL_CACHE_DIR", "HF_HOME", "HF_HUB_OFFLINE", "TABPFN_DISABLE_TELEMETRY")


def run_once(t, env, log, home=None):
    """The child environment is a whitelist (KEEP, SLURM_*) plus the task's registered variables, so no variable of
    the job (MICE_BACKBONE, MICE_SEED, OMP_NUM_THREADS, ...) leaks into a task that does not set it."""
    e = {k: v for k, v in os.environ.items() if k in KEEP or k.startswith("SLURM_")}
    e.update(fill(t["env"], env))
    if home:
        e["HOME"] = home
    with open(log, "a") as f:
        f.write(f"\n=== {time.strftime('%F %T')} {socket.gethostname()} {' '.join(fill(t['cmd'], env))}\n"); f.flush()
        return subprocess.run(fill(t["cmd"], env), cwd=fill(t["cwd"], env), env=e, stdout=f, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL).returncode


def worker(slot, sets=None, gpu=None):
    env = {v: os.environ.get(v, "") for v in VARS}
    base = f"{env['RUNS']}/_rerun"
    check_vars([t for t in TASKS if not ((sets and t["set"] not in sets) or (gpu and t["gpu"] != gpu))], env)
    for d in ("claims", "done", "gaveup", "logs"):
        os.makedirs(f"{base}/{d}", exist_ok=True)
    for t in TASKS:
        if (sets and t["set"] not in sets) or (gpu and t["gpu"] != gpu):
            continue
        sid = safe(t["id"])
        if os.path.exists(f"{base}/done/{sid}.json") or os.path.exists(f"{base}/gaveup/{sid}.json"):
            continue
        try:
            os.mkdir(f"{base}/claims/{sid}")
        except FileExistsError:
            continue
        # attempts of this task by every worker so far (persisted: a restarted worker continues the count)
        hist_f = f"{base}/attempts/{sid}.json"; os.makedirs(f"{base}/attempts", exist_ok=True)
        hist = json.load(open(hist_f)) if os.path.exists(hist_f) else []
        rec = dict(task=t["id"], host=socket.gethostname(), gpu=gpu_name(), slot=slot, start=time.time(), rc=[],
                   health=[], quarantined=[], earlier_attempts=len(hist))
        log = f"{base}/logs/{sid}.log"
        limit = 1 if t["gpu"] == "exclusive" else 3          # a benchmark is never retried (timings)
        ok = False
        while len(hist) < limit:
            attempt = len(hist)
            # whatever exists now did not come from a successful attempt of this worker: quarantine, start fresh
            rec["quarantined"] += quarantine(t, env, base, attempt)
            rec["health"].append(health())
            t0 = time.time()
            hist.append(dict(attempt=attempt, host=socket.gethostname(), start=t0, end=None, rc=None, accepted=False))
            json.dump(hist, open(hist_f + ".tmp", "w")); os.replace(hist_f + ".tmp", hist_f)   # counted before it runs
            rc = run_once(t, env, log); rec["rc"].append(rc)
            rec["health"].append(health())
            ok = rc == 0 and complete(t, env)
            hist[-1].update(end=time.time(), rc=rc, accepted=ok)
            json.dump(hist, open(hist_f + ".tmp", "w")); os.replace(hist_f + ".tmp", hist_f)
            if ok:
                break
            time.sleep(10)
        rec["end"] = time.time()
        dst = f"{base}/{'done' if ok else 'gaveup'}/{sid}.json"
        json.dump(rec, open(dst + ".tmp", "w")); os.replace(dst + ".tmp", dst)
        print(time.strftime("%T"), "ok" if ok else "GAVE UP", t["id"], f"{rec['end'] - rec['start']:.0f}s", flush=True)


INPUTS = ("data", "held", "source", "controller", "tasks", "kstar", "m_star")


def qualify(task_id, d, against_production=False):
    """Fresh run(s) of one task in a sandbox: HOME = <d>/<k>, RUNS = <d>/<k>/pfn-runs, where every run root holds
    links to its inputs only (drivers with hard-coded ~/pfn-runs paths therefore write into the sandbox too), and
    ~/ext-baselines links to the real one."""
    t = next(x for x in TASKS if x["id"] == task_id)
    env0 = {v: os.environ.get(v, "") for v in VARS}
    check_vars([t], env0)
    sets = []
    for k in (("a",) if against_production else ("a", "b")):
        home = os.path.join(d, k); runs = f"{home}/pfn-runs"
        os.makedirs(runs, exist_ok=False)
        for name in os.listdir(env0["RUNS"]):
            src = f"{env0['RUNS']}/{name}"
            if name.startswith("_") or not os.path.isdir(src):
                continue
            os.makedirs(f"{runs}/{name}")
            for x in os.listdir(src):
                if x.startswith(INPUTS):
                    os.symlink(f"{src}/{x}", f"{runs}/{name}/{x}")
        if os.path.exists(os.path.expanduser("~/ext-baselines")):
            os.symlink(os.path.expanduser("~/ext-baselines"), f"{home}/ext-baselines")
        env = dict(env0, RUNS=runs)
        t2 = json.loads(json.dumps(t))
        if "{REPO}/MICE/results" in json.dumps(t2):       # run.py family: redirect --out to the probe directory
            out = f"{home}/out"; os.makedirs(out)
            t2["cmd"] = [out if c.startswith("../results") else c for c in t2["cmd"]]
            t2["outputs"] = [o.replace(o[:o.rfind("/")], out) for o in t2["outputs"]]
        log = f"{home}/log.txt"
        rc = run_once(t2, env, log, home=home)
        sets.append((rc, fill(t2["outputs"], env)))
        print(k, "rc", rc, flush=True)
    import numpy as np
    if against_production:
        sets.append((0, fill(t["outputs"], env0)))
    same = bool(sets[0][1]) and len(sets[0][1]) == len(sets[1][1]) and all(os.path.exists(o) for o in sets[0][1] + sets[1][1])
    if not same:
        print("MISSING outputs", [o for o in sets[0][1] + sets[1][1] if not os.path.exists(o)])
    for oa, ob in zip(sets[0][1], sets[1][1]):
        if not (os.path.exists(oa) and os.path.exists(ob)):
            continue
        if oa.endswith(".npz"):
            za, zb = np.load(oa, allow_pickle=True), np.load(ob, allow_pickle=True)
            for key in sorted(set(za.files) | set(zb.files)):
                if key in ("wt", "te", "peak_mem"):
                    continue
                eq = key in za.files and key in zb.files and za[key].dtype == zb[key].dtype and \
                    za[key].shape == zb[key].shape and za[key].tobytes() == zb[key].tobytes()
                same &= eq
                if not eq:
                    print("DIFFERENT", os.path.basename(oa), key)
        else:
            eq = open(oa, "rb").read() == open(ob, "rb").read()
            same &= eq
            if not eq:
                print("DIFFERENT (bytes)", os.path.basename(oa))
    print("QUALIFIED (bit-identical)" if same and sets[0][0] == sets[1][0] == 0 else "NOT QUALIFIED")


def status():
    base = f"{os.environ['RUNS']}/_rerun"
    import collections
    c = collections.defaultdict(collections.Counter)
    for t in TASKS:
        sid = safe(t["id"])
        k = ("done" if os.path.exists(f"{base}/done/{sid}.json") else "gaveup" if os.path.exists(f"{base}/gaveup/{sid}.json")
             else "claimed" if os.path.exists(f"{base}/claims/{sid}") else "left")
        c[t["set"]][k] += 1
    for s, v in c.items():
        print(f"{s:34s} " + " ".join(f"{k}={v[k]}" for k in ("done", "claimed", "gaveup", "left")))


def release():
    base = f"{os.environ['RUNS']}/_rerun"
    n = 0
    for sid in os.listdir(f"{base}/claims"):
        if not (os.path.exists(f"{base}/done/{sid}.json") or os.path.exists(f"{base}/gaveup/{sid}.json")):
            os.rmdir(f"{base}/claims/{sid}"); n += 1
    print(n, "claims released")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit("usage: see the docstring")
    if a[0] == "worker":
        sets = a[a.index("--sets") + 1].split(",") if "--sets" in a else None
        gpu = a[a.index("--gpu") + 1] if "--gpu" in a else None
        worker(a[1], sets, gpu)
    elif a[0] == "qualify":
        qualify(a[1], a[2])
    elif a[0] == "recheck":
        qualify(a[1], a[2], against_production=True)
    elif a[0] == "status":
        status()
    elif a[0] == "release":
        release()
    else:
        raise SystemExit(f"unknown mode {a[0]!r} (worker, qualify, recheck, status, release)")
