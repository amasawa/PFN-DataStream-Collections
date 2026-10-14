"""TKDE round 13, part C (registered in experiments/mice_tkde_control/PLAN.md, "Round 13"): the archive and snapshot
pools at the benchmark-calibrated capacity k* (kstar.json, fixed from the A1 timings before this runs) on the aligned
grid, the shifted grid and the prespecified source-balanced real subset. run.run unchanged apart from the pool
capacity (backbone seed 0). Usage: python pool_cap_run.py <task index> ...; outputs in RUN/k<k*>/, skipped if present.
Amendment 2026-10-14 (PLAN.md): with MICE_R13_K in {2, 4} the candidate capacity is run before kstar.json exists,
outputs in RUN/k<MICE_R13_K>/."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run

CTRL = os.path.expanduser("~/pfn-runs/mice-tkde-control-20261009")
BENCH = os.path.expanduser("~/pfn-runs/mice-r13-bench")
RUN = os.path.expanduser("~/pfn-runs/mice-r13-acc")
GRID = [f"grid_c{nc}_b{blk}_s{s}" for blk in (500, 2000) for nc in (30, 100) for s in (20, 21)]
SHIFT = [g.replace("grid_", "off_") for g in GRID]
REAL = ["h4_airlines_d", "h4_covertype_d", "h4_poker_d", "insects_abrupt_balanced", "h2_rialto", "elec2", "h2_weather",
        "h2_phishing", "h2_spam"]
TASKS = [(s, m) for s in REAL + GRID + SHIFT for m in ("arch1000_500", "snap1000_500")]

if __name__ == "__main__":
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn", "registered backbone is TabPFN v2"
    kenv = os.environ.get("MICE_R13_K")      # amendment 2026-10-14: candidates run before k* is fixed
    assert kenv in (None, "2", "4"), kenv
    ks = None if kenv else json.load(open(f"{BENCH}/kstar.json"))
    run.DATA = f"{CTRL}/data"
    _init = run.PoolControl.__init__
    for i in map(int, sys.argv[1:]):
        s, m = TASKS[i]
        k = int(kenv) if kenv else int(ks[m[:4]])

        def _init_k(self, *a, _k=k, **kw):
            _init(self, *a, **kw)
            self.kmax = _k
        run.PoolControl.__init__ = _init_k
        os.makedirs(f"{RUN}/k{k}", exist_ok=True)
        run.run(s, m, 100, f"{RUN}/k{k}")
