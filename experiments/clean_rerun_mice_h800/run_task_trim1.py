"""Reconstruction of the TRIM = 1 development control of round 14 (~/pfn-runs/mice-r14-devtrim; PLAN.md, "Reconstructed
runs"): the original ran from uncommitted code minutes before commit 991a1f9 introduced CPSegments.TRIM (frozen 0).
This runs experiments/mice_r14/run_task.py unchanged with the class attribute CPSegments.TRIM set to 1 on the
committed code; nothing else differs. Usage: python run_task_trim1.py <root> <stream> <method>"""
import os, runpy, sys

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, os.path.join(REPO, "MICE", "code"))
import run  # noqa: E402  (the module object that run_task.py imports)

run.CPSegments.TRIM = 1
sys.argv = [os.path.join(REPO, "experiments", "mice_r14", "run_task.py")] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
