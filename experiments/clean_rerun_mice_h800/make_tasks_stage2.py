"""Stage 2 of the tuned Table 1 baselines (REGISTRATION_STAGE2_20261020.md): P2b (fsnet, onenet, adaptz, shifts; cluster
CPU), P5 (dtmoe; H800 strict mode), and the TOT part of P6 (CPU). A mechanical function of the committed selection
files of select_frozen.py (amendment c items 1-4), so no choice is left to the coordinator:
  ext   <method> <frozen_<m>.json>        the one full extension: every new value of a boundary axis (lr / 10 at the
                                          lower edge, lr x 10 at the upper edge, n_steps 25 at the upper edge; n_steps 1
                                          is the smallest value) crossed with every value of the other axes, minus the
                                          original grid; 5 development streams; into the development directory
  test  <method> <frozen_<m>_final.json>  the frozen configuration on the 92 Table 1 streams (83 of MICE/data, 9 of the
                                          confirmation data)
Writes tasks_stage2_<method>_<ext|test>.jsonl and a manifest (sha256 of the selection file, expected and actual task
count). A count that differs from the expected one stops with an error. --selftest checks the rules on hand-written
fixtures of selection files (never a real one; stream shapes are read from the data). Usage: python make_tasks_stage2.py ext|test <method> <json> | --selftest"""
import hashlib, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CONF = os.path.expanduser("~/pfn-runs/mice-confirm-cp-20261017/data")      # local copy, used only for array shapes
DEV = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
       "insects_incremental_reoccurring_balanced"]
LR, ST = ("1e-4", "1e-3", "1e-2"), ("1", "5")                                  # the registered grid
AXES = {"fsnet": ("16 32", "0.5 0.75 0.9"), "onenet": ("16 32", "0.5 0.75 0.9"), "adaptz": ("1 16", "1e-4 1e-3 1e-2"),
        "shifts": ("16 32", "0.5 1 2"), "dtmoe": ("16 32", "1 2 3"), "tot": ("16 32", "1e-6 1e-5 1e-4")}
THREADS = {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}
DEVICE = {"dtmoe": dict(py="{PYTOT}", gpu="shared", env={**THREADS, "TS_DEVICE": "cuda", "TS_DETERMINISTIC": "1",
                                                        "CUBLAS_WORKSPACE_CONFIG": ":4096:8"},
                        dev="dev_h800", test="test_h800"),
          "tot": dict(py="{PYTOTA}", gpu="shared", env={**THREADS, "TS_DEVICE": "cuda", "TS_DETERMINISTIC": "1",   # A800
                                                       "CUBLAS_WORKSPACE_CONFIG": ":4096:8"},       # (AMENDMENT_20261020b)
                      dev="dev_a800", test="test_a800")}
CPU = dict(py="{PYTS}", gpu="cpu", env={**THREADS, "CUDA_VISIBLE_DEVICES": ""}, dev="dev_cluster", test="test_cluster")


def g(x):
    return f"{float(x):g}"


def stream_shape(s, data_dir):
    y = np.load(f"{data_dir}/{s}.npz")["y"]
    return len(y) // 100, int(y.max()) + 1


def task(set_, method, s, data, data_dir, L, lr, st, mech, outdir):
    d = DEVICE.get(method, CPU)
    tag = f"{method}_L{L}_lr{g(lr)}_s{st}_m{g(mech)}"
    out = f"{{RUNS}}/mice-table1-newbase/{outdir}/P/{s}__{tag}.npz"
    T, C = stream_shape(s, data_dir)
    sch = {"acc": [[T], "float64"], "pred": [[(T - 1) * 100], "int64"], "P": [[(T - 1) * 100, C], "float32"],
           "C": [[], "int64"], "B": [[], "int64"], "fires": [[T], "int64"], "added": [[T], "int64"],
           "pruned": [[T], "int64"], "config": [[], "<U"]}
    return dict(id=f"{set_}:{s}__{tag}", set=set_, gpu=d["gpu"], cwd="{REPO}",
                cmd=[d["py"], "{REPO}/experiments/mice_table1_fill_20261018/" + ("run_ts_tot.py" if method == "tot" else "run_ts.py"),
                     "--data", data, "--out",
                     f"{{RUNS}}/mice-table1-newbase/{outdir}/P", "--streams", s, "--method", method, "--L", str(L),
                     "--lr", lr, "--steps", st, "--mech", mech],
                env=dict(d["env"]), outputs=[out], est_s=None, schema={out: {"npz": sch}})


def ext_values(frozen):
    e = frozen["boundary_extension_needed"]
    lrs = list(LR) + ([g(e["lr"])] if "lr" in e else [])
    sts = list(ST) + ([str(int(e["steps"]))] if "steps" in e else [])
    if "lr" in e:
        assert g(e["lr"]) in ("1e-05", "0.1"), e                      # / 10 at 1e-4 or x 10 at 1e-2 only
    if "steps" in e:
        assert int(e["steps"]) == 25, e
    return lrs, sts


def make_ext(method, frozen, data_dir=f"{REPO}/MICE/data"):
    assert frozen["method"] == method and not frozen["final"], "needs the first selection file of this method"
    LS, MS = (v.split() for v in AXES[method])
    lrs, sts = ext_values(frozen)
    out = [task(f"stage2_ext_{method}", method, s, "{REPO}/MICE/data", data_dir, L, lr, st, mech, DEVICE.get(method, CPU)["dev"])
           for lr in lrs for st in sts if not (lr in LR and st in ST) for L in LS for mech in MS for s in DEV]
    expect = (len(lrs) * len(sts) - len(LR) * len(ST)) * len(LS) * len(MS) * len(DEV)
    return out, expect


def make_test(method, frozen, data_dir=f"{REPO}/MICE/data", conf_dir=CONF):
    assert frozen["method"] == method and frozen["final"], "needs the --final selection file of this method"
    b = frozen["best"]
    main = [l.strip() for l in open(f"{REPO}/experiments/mice_table1_fill_20261018/streams_main.txt") if l.strip()]
    conf = [l.strip() for l in open(f"{REPO}/experiments/mice_table1_fill_20261018/streams_confirm.txt") if l.strip()]
    assert len(main) == 83 and len(conf) == 9 and not set(main) & set(conf), (len(main), len(conf))
    real = [s for s in main if not s.startswith(("grid_", "agrawal_", "hyperplane_", "rbf_", "sea_", "sine_", "stagger_"))]
    assert len(real) == 29, len(real)                     # amendment c item 4: real and confirmation first, then the
    lr, st, mech = g(b["lr"]), str(int(b["steps"])), g(b["mech"])     # grid and generator streams
    d = DEVICE.get(method, CPU)
    mk = lambda s, data, ddir: task(f"stage2_test_{method}", method, s, data, ddir, b["L"], lr, st, mech, d["test"])
    out = [mk(s, "{REPO}/MICE/data", data_dir) for s in real]
    out += [mk(s, "{RUNS}/mice-confirm-cp-20261017/data", conf_dir) for s in conf]
    out += [mk(s, "{REPO}/MICE/data", data_dir) for s in main if s not in real]
    return out, 92


def write(kind, method, path):
    raw = open(path, "rb").read(); frozen = json.loads(raw)
    tasks, expect = (make_ext if kind == "ext" else make_test)(method, frozen)
    if len(tasks) != expect or len({t["id"] for t in tasks}) != len(tasks):
        sys.exit(f"{len(tasks)} tasks, {expect} expected (or duplicate ids): nothing written")
    name = f"tasks_stage2_{method}_{kind}.jsonl"
    if os.path.exists(f"{HERE}/{name}"):
        sys.exit(f"{name} exists: a list is generated once")
    with open(f"{HERE}/{name}", "w") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")
    man = dict(list=name, method=method, kind=kind, selection_file=os.path.relpath(path, REPO),
               selection_sha256=hashlib.sha256(raw).hexdigest(), expected=expect, tasks=len(tasks),
               generator_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest())
    json.dump(man, open(f"{HERE}/{name[:-6]}.manifest.json", "w"), indent=1); print(json.dumps(man))


def selftest():
    """Hand-written fixtures of select_frozen.py outputs (no real selection file is read)."""
    fx = lambda m, ext, final=False, best=None: dict(method=m, final=final, boundary_extension_needed=ext,
                                                     best=best or dict(L=16, lr=1e-3, steps=5, mech=0.75))
    cases = [("fsnet", {}, 0), ("fsnet", {"steps": 25}, 3 * 2 * 3 * 5),                       # interior; upper steps
             ("shifts", {"lr": 0.1}, 1 * 2 * 2 * 3 * 5),                                         # upper lr
             ("adaptz", {"lr": 1e-5, "steps": 25}, (4 * 3 - 6) * 2 * 3 * 5),                     # lower lr + upper steps
             ("dtmoe", {"steps": 25}, 3 * 2 * 3 * 5), ("tot", {"lr": 1e-5}, 2 * 2 * 3 * 5)]
    for m, e, n in cases:
        t, expect = make_ext(m, fx(m, e))
        assert len(t) == expect == n, (m, e, len(t), expect, n)
        if "lr" in e and "steps" in e:                                                         # the corner is included
            assert any(f"_lr{g(e['lr'])}_s25_" in x["id"] for x in t), "corner missing"
        assert not any(f"_lr{lr}_s{st}_" in x["id"] for x in t for lr in ("0.0001", "0.001", "0.01") for st in ("1", "5"))
    t, _ = make_ext("dtmoe", fx("dtmoe", {"steps": 25}))
    assert all(x["gpu"] == "shared" and x["env"]["TS_DETERMINISTIC"] == "1" and "/dev_h800/" in x["outputs"][0] for x in t)
    t, _ = make_ext("tot", fx("tot", {"steps": 25}))
    assert all(x["gpu"] == "shared" and x["cmd"][0] == "{PYTOTA}" and x["cmd"][1].endswith("/run_ts_tot.py")
               and x["env"]["TS_DETERMINISTIC"] == "1" and "/dev_a800/" in x["outputs"][0] for x in t)
    t, _ = make_ext("dtmoe", fx("dtmoe", {"steps": 25}))
    assert all(x["cmd"][1].endswith("/run_ts.py") for x in t)
    t, _ = make_ext("fsnet", fx("fsnet", {"steps": 25}))
    assert all(x["gpu"] == "cpu" and x["env"]["CUDA_VISIBLE_DEVICES"] == "" and "/dev_cluster/" in x["outputs"][0] for x in t)
    for bad in ({"lr": 0.5}, {"steps": 10}):
        try:
            make_ext("fsnet", fx("fsnet", bad)); raise SystemExit(f"accepted {bad}")
        except AssertionError:
            pass
    t, n = make_test("adaptz", fx("adaptz", {}, final=True, best=dict(L=1, lr=1e-5, steps=25, mech=1e-3)))
    assert len(t) == n == 92 and len({x["id"] for x in t}) == 92
    assert all("adaptz_L1_lr1e-05_s25_m0.001" in x["id"] and "/test_cluster/" in x["outputs"][0] for x in t)
    assert sum("mice-confirm-cp-20261017/data" in " ".join(x["cmd"]) for x in t) == 9
    assert all("mice-confirm-cp-20261017/data" in " ".join(x["cmd"]) for x in t[29:38])          # order: real, confirm, rest
    try:
        make_test("adaptz", fx("adaptz", {})); raise SystemExit("accepted a non-final file")
    except AssertionError:
        pass
    print("selftest ok:", len(cases), "extension cases, test list, device routing, guards")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        write(*sys.argv[1:4])
