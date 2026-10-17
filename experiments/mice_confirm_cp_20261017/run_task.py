"""Confirmation of detected segmentation (PLAN.md): run one (stream, method) on <root>/data, output in <root>/P
(skipped if present). TFM methods use MICE/code/run.py unchanged; ddm1000 and ltm1000_75 go through
MICE/code/run_probs.py (records the per-row probabilities, one TFM call per batch); arf and srp use
MICE/code/run_river.py (CPU). Usage: python run_task.py <root> <stream> <method>"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))

if __name__ == "__main__":
    root, stream, method = sys.argv[1:4]
    out = f"{root}/P"
    os.makedirs(out, exist_ok=True)
    if method in ("arf", "srp"):
        import run_river
        run_river.DATA = f"{root}/data"
        run_river.run(stream, method, 100, out)
        sys.exit(0)
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn"
    if method in ("ddm1000", "ltm1000_75"):
        import run_probs   # replaces run.TFM by the recording subclass
        import run
        run.DATA = f"{root}/data"
        dst = f"{out}/{stream}__{method}__probs.npz"
        if os.path.exists(dst):
            sys.exit(0)
        if os.path.exists(f"{out}/{stream}__{method}.npz"):   # died between the two files: redo it (as run_probs.py)
            os.remove(f"{out}/{stream}__{method}.npz")
        run_probs.REC.clear(); run.run(stream, method, 100, out)
        np.savez_compressed(dst, P=np.concatenate(run_probs.REC).astype(np.float16), n_calls=len(run_probs.REC))
        sys.exit(0)
    import run
    assert method in ("fifo1000", "winens1000", "micev1000_500", "micecp1000_500"), method
    run.DATA = f"{root}/data"
    run.run(stream, method, 100, out)
