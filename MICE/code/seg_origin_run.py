"""TKDE round 12, direction B (registered in experiments/mice_tkde_control/PLAN.md, "Round 12"): MICE and the
archive on the 4.b offset streams with the segment origin moved to row 200, so every stored segment lies inside one
concept block. Everything else is run.run unchanged (method, rule, constants, backbone seed 0).
Usage: python seg_origin_run.py <task index> ... (indices into TASKS); outputs in RUN/P, skipped if present."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run

ORIGIN = 200
CTRL = os.path.expanduser("~/pfn-runs/mice-tkde-control-20261009")
RUN = os.path.expanduser("~/pfn-runs/mice_seg_origin_r12")
STREAMS = [f"off_c{nc}_b{blk}_s{s}" for blk in (500, 2000) for nc in (30, 100) for s in (20, 21)]
TASKS = [(s, m) for s in STREAMS for m in ("micev1000_500", "arch1000_500")]

_init = run.MiceV1.__init__


def _init_origin(self, *a, **kw):
    _init(self, *a, **kw)
    self.closed = ORIGIN            # first segment closes at row ORIGIN + seg; rows < ORIGIN go to no segment


if __name__ == "__main__":
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn", "registered backbone is TabPFN v2"
    run.MiceV1.__init__ = _init_origin          # PoolControl (archive) inherits it through super().__init__
    run.DATA = f"{CTRL}/data"
    os.makedirs(f"{RUN}/P", exist_ok=True)
    for i in map(int, sys.argv[1:]):
        s, m = TASKS[i]
        run.run(s, m, 100, f"{RUN}/P")
