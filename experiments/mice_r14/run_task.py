"""Round 14: run one (stream, method) of MICE/code/run.py on <root>/data, output in <root>/P (skipped if present).
Usage: python run_task.py <root> <stream> <method>"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "MICE", "code"))
import run  # noqa: E402

if __name__ == "__main__":
    assert os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn"
    root, stream, method = sys.argv[1:4]
    run.DATA = f"{root}/data"
    os.makedirs(f"{root}/P", exist_ok=True)
    run.run(stream, method, 100, f"{root}/P")
