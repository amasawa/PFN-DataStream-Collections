"""Round 14: run one (stream, method) of MICE/code/run.py on <root>/data, output in <root>/P (skipped if present).
Round 14.b (PLAN_14B.md, part C): a method "<method>.k<K>" runs <method> with pool capacity kmax = K (the archive or
snapshot pool; as in MICE/code/pool_cap_run.py), output in <root>/P_k<K>.
Usage: python run_task.py <root> <stream> <method>"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import run  # noqa: E402

if __name__ == "__main__":
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn"
    root, stream, method = sys.argv[1:4]
    run.DATA = f"{root}/data"
    out = f"{root}/P"
    if ".k" in method:
        method, k = method.split(".k")
        k = int(k)
        assert method.startswith(("snap", "arch")), method
        _init = run.PoolControl.__init__

        def _init_k(self, *a, **kw):
            _init(self, *a, **kw)
            self.kmax = k
        run.PoolControl.__init__ = _init_k
        out = f"{root}/P_k{k}"
    os.makedirs(out, exist_ok=True)
    run.run(stream, method, 100, out)
