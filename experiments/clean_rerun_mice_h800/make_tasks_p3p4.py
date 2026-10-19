"""Task lists of phases P3 (extra backbones) and P4 stage 1 (CURE development runs) of the clean MICE rerun
(ACTIVATION_20261019.md; REGISTRATION_P3_P4_20261020.md). Same fields as tasks.jsonl.
P3: for each of the 7 backbones, the TabICL check of P1 (results_heldout3_tabicl, results_heldout4_tabicl,
results_heldout4_tabicl_e: 10 segments x ddm1000, fifo1000, micev1000_500, winens1000) with MICE/code/run_backbone.py
instead of run.py and the backbone's venv; structures and time estimates copied from the TabICL task of the same
segment and policy. Plus the H800 smoke test (set p3_smoke, exclusive): 8 backbones (the 7 and the TabPFN v2
reference) x 2 segments (h3_covertype_b: most features; h3_poker_b: most classes), 20 calls each, time and memory only.
P4 stage 1: CURE with tau in {0.1, 0.2, 0.3, 0.4} on the five development streams of the Table 1 baselines.
Placeholders: {REPO}, {RUNS}, {PY} as in P1; {PYDPT}, {PYMITRA}, {PYLIMIX} the venvs of TabDPT, Mitra, LimiX; {W3} the
directory of the P3 weights. Usage: python make_tasks_p3p4.py (local machine)."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BB = {"tabpfn_v2.5": ("tabpfn25", "{PY}"), "tabpfn_v2.6": ("tabpfn26", "{PY}"), "tabpfn_v3": ("tabpfn3", "{PY}"),
      "tabpfn_v3.5": ("tabpfn35", "{PY}"), "tabdpt": ("tabdpt", "{PYDPT}"), "mitra2": ("mitra2", "{PYMITRA}"),
      "limix2": ("limix2", "{PYLIMIX}")}
ENV = {"OMP_NUM_THREADS": "4", "PYTHONWARNINGS": "ignore", "P3_WEIGHTS": "{W3}"}
p1 = [json.loads(l) for l in open(f"{HERE}/tasks.jsonl")]
tabicl = [t for t in p1 if t["set"] in ("results_heldout3_tabicl", "results_heldout4_tabicl", "results_heldout4_tabicl_e")]
assert len(tabicl) == 40, len(tabicl)

p3 = []
for bb, (tag, py) in BB.items():
    for t in tabicl:
        sset = t["set"].replace("tabicl", tag)
        cmd = [py if c == "{PY}" else "run_backbone.py" if c == "run.py" else c.replace("tabicl", tag) for c in t["cmd"]]
        outs = [o.replace("tabicl", tag) for o in t["outputs"]]
        p3.append(dict(id=f"{sset}:{t['id'].split(':')[1]}", set=sset, gpu="shared", cwd=t["cwd"], cmd=cmd,
                       env={**ENV, "P3_BACKBONE": bb}, outputs=outs, est_s=t["est_s"],
                       schema={o2: v for o2, v in zip(outs, (t["schema"][o] for o in t["outputs"]))}))
SMOKE_KEYS = sorted(["backbone", "stream", "n_classes", "n_features", "mem_cap_gb", "gpu", "s_per_call", "error",
                     "median_s_after_first", "peak_mem_gb"])
for bb, (tag, py) in [("tabpfn_v2", ("tabpfn2", "{PY}"))] + list(BB.items()):
    for s in ("h3_covertype_b", "h3_poker_b"):
        out = f"{{RUNS}}/mice-p3-smoke/{tag}__{s}.json"
        p3.append(dict(id=f"p3_smoke:{tag}__{s}", set="p3_smoke", gpu="exclusive", cwd="{REPO}/MICE/code",
                       cmd=[py, "-u", "run_backbone.py", "--streams", s, "--smoke", "20", "--smoke-out", out],
                       env={**ENV, "P3_BACKBONE": bb, "P3_MEM_CAP_GB": "28"}, outputs=[out], est_s=None,
                       schema={out: {"json": SMOKE_KEYS}}))

DEV = ["elec2", "insects_abrupt_balanced", "insects_gradual_balanced", "insects_incremental_balanced",
       "insects_incremental_reoccurring_balanced"]
p4 = []
for tau in ("0.1", "0.2", "0.3", "0.4"):
    for s in DEV:
        y = np.load(f"{REPO}/MICE/data/{s}.npz")["y"]; T, C = len(y) // 100, int(y.max()) + 1
        out = f"{{RUNS}}/mice-table1-newbase/cure_dev/P/{s}__cure_tau{float(tau):g}.npz"
        sch = {"acc": [[T], "float64"], "pred": [[(T - 1) * 100], "int64"], "P": [[(T - 1) * 100, C], "float32"],
               "C": [[], "int64"], "B": [[], "int64"], "tau": [[], "float64"], "calls": [[], "int64"],
               **{k: [[T], "int64"] for k in ("mem", "short", "long", "left", "gate", "warm")}}
        p4.append(dict(id=f"cure_dev:{s}__cure_tau{float(tau):g}", set="cure_dev", gpu="shared", cwd="{REPO}",
                       cmd=["{PY}", "-u", "{REPO}/experiments/mice_table1_fill_20261018/run_cure.py", "--data",
                            "{REPO}/MICE/data", "--out", "{RUNS}/mice-table1-newbase/cure_dev/P", "--tau", tau,
                            "--streams", s],
                       env={"OMP_NUM_THREADS": "4", "PYTHONWARNINGS": "ignore"}, outputs=[out], est_s=None,
                       schema={out: {"npz": sch}}))

for name, L in (("tasks_p3.jsonl", p3), ("tasks_p4.jsonl", p4)):
    ids = [t["id"] for t in L]; assert len(ids) == len(set(ids))
    with open(f"{HERE}/{name}", "w") as f:
        for t in L:
            f.write(json.dumps(t) + "\n")
    print(name, len(L), "tasks;", round(sum(t["est_s"] or 0 for t in L) / 3600, 1), "h of TabICL-time estimates")
