"""Amendment 4 (AMENDMENT_20261008.md): resource-scaled run of the frozen held-out snapshot.

Runs the repository supervisor in --resource-mode (no failure-rate breaker; stop only on a global stall or an
unresponsive nvidia-smi), launching the FROZEN worker from RUN_ROOT/controller. Snapshot hashes are verified before
the run and before the frozen evaluator.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def verify(root):
    for name, expected in json.loads((root / 'freeze.json').read_text())['files'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    for entry in json.loads((root / 'data_manifest.json').read_text()):
        path = root / 'data' / (entry['stream'] + '.npz')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['prefix_sha256'], path


root, repo = map(Path, sys.argv[1:3])
verify(root)
if (root / 'STOP').exists():
    raise SystemExit('STOP present: inspect the reason and rename it deliberately before resuming.')
subprocess.run([sys.executable, str(HERE.parent / 'night_20261007/supervisor.py'), str(root), str(repo),
                '--hours', '24', '--max-workers', sys.argv[3] if len(sys.argv) > 3 else '8', '--start-workers', sys.argv[4] if len(sys.argv) > 4 else '4', '--breaker', '0', '--resource-mode',
                '--stall-minutes', '15', '--worker-dir', str(root / 'controller'), '--no-publish'], check=True)
tasks = json.loads((root / 'tasks.json').read_text())
if not all((root / 'done' / (task['id'] + '.json')).exists() for task in tasks):
    raise SystemExit('INCOMPLETE: inspect status/events; no held-out results evaluated.')
verify(root)
subprocess.run([sys.executable, str(root / 'controller/evaluate.py'), str(root)], check=True)
