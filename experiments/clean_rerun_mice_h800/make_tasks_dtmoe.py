"""The dtmoe development grid of the clean rerun after AMENDMENT_20261020c: the 60 tasks of set dtmoe_dev of the frozen
tasks.jsonl with drift_k_sigma = 2 (its default), copied unchanged (same ids, commands, outputs, structures).
tasks.jsonl itself is not changed; P1 production excludes dtmoe_dev, and dtmoe runs only from tasks_dtmoe.jsonl.
Usage: python make_tasks_dtmoe.py (writes tasks_dtmoe.jsonl)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
sel = [l for l in open(f"{HERE}/tasks.jsonl") if json.loads(l)["set"] == "dtmoe_dev" and json.loads(l)["id"].endswith("_m2")]
assert len(sel) == 60, len(sel)
assert all(json.loads(l)["cmd"][-2:] == ["--mech", "2"] for l in sel)
open(f"{HERE}/tasks_dtmoe.jsonl", "w").writelines(sel)
print(len(sel), "tasks")
