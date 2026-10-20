"""dtmoe on the cluster CPU (user decision 2026-10-20 "cpu 跑呗", approved protocol 2026-10-21; Fable advice in
CLUSTER_RERUN_LOG.md). Writes a CPU copy of a dtmoe task list: every line unchanged except
  - set and id: dtmoe_dev -> dtmoe_cpu_dev (stage-2 sets likewise: <set> -> <set>_cpu);
  - device: gpu = "cpu"; TS_DEVICE, TS_DETERMINISTIC, CUBLAS_WORKSPACE_CONFIG removed (run_ts.py defaults to the CPU and
    sets torch.set_num_threads(1)); CUDA_VISIBLE_DEVICES = "" as in every P2 task;
  - python: {PYTOT} (totgpu, CUDA torch) -> {PYTS} (tsbase, torch 2.14.1+cpu, the CPU-baseline venv);
  - output directory: mice-table1-newbase/<dev_h800|test_h800> -> mice-table1-newbase/dtmoe_cpu/<dev|test> (new; never
    mixed with GPU outputs), in cmd, outputs and schema.
Usage: python make_tasks_dtmoe_cpu.py <input.jsonl> <output.jsonl>"""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
DIRS = {"mice-table1-newbase/dev_h800/": "mice-table1-newbase/dtmoe_cpu/dev/",
        "mice-table1-newbase/test_h800/": "mice-table1-newbase/dtmoe_cpu/test/"}


def move(s):
    for a, b in DIRS.items():
        s = s.replace(a, b)
    return s


out = []
for line in open(src):
    if not line.strip():
        continue
    t = json.loads(line)
    assert "dtmoe" in t["id"] and t["cmd"][0] == "{PYTOT}", t["id"]
    new_set = "dtmoe_cpu_dev" if t["set"] == "dtmoe_dev" else t["set"] + "_cpu"
    t["id"] = new_set + t["id"][len(t["set"]):]
    t["set"] = new_set
    t["gpu"] = "cpu"
    t["cmd"] = [move(c) for c in t["cmd"]]
    t["cmd"][0] = "{PYTS}"
    t["env"] = {k: v for k, v in t["env"].items() if k not in ("TS_DEVICE", "TS_DETERMINISTIC", "CUBLAS_WORKSPACE_CONFIG")}
    t["env"]["CUDA_VISIBLE_DEVICES"] = ""
    t["outputs"] = [move(o) for o in t["outputs"]]
    t["schema"] = {move(k): v for k, v in t["schema"].items()}
    assert "h800" not in json.dumps(t) and "TS_DEVICE" not in json.dumps(t), t["id"]
    out.append(t)
with open(dst, "w") as f:
    for t in out:
        f.write(json.dumps(t) + "\n")
print(len(out), "tasks ->", dst)
