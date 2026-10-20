"""P3 after AMENDMENT_20261020d: the tasks of the registered tasks_p3.jsonl for TabPFN-3.5 and TabDPT only, copied
unchanged (same ids, commands, outputs, structures): their 80 production tasks and their smoke tasks, with the TabPFN v2
reference of the smoke test (6 smoke tasks). tasks_p3.jsonl is not changed. Usage: python make_tasks_p3b.py"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
KEEP = ("tabpfn35", "tabdpt")
def keep(t):
    if t["set"] == "p3_smoke":
        return t["id"].split(":")[1].split("__")[0] in KEEP + ("tabpfn2",)
    return any(t["set"].endswith(f"_{k}") or t["set"].endswith(f"_{k}_e") for k in KEEP)
lines = [l for l in open(f"{HERE}/tasks_p3.jsonl") if keep(json.loads(l))]
sets = {}
for l in lines:
    s = json.loads(l)["set"]; sets[s] = sets.get(s, 0) + 1
assert sum(v for k, v in sets.items() if k != "p3_smoke") == 80 and sets["p3_smoke"] == 6, sets
open(f"{HERE}/tasks_p3b.jsonl", "w").writelines(lines)
print(sets)
