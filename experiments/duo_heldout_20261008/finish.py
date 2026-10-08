"""Run the bounded frozen queue, then evaluate only if every task is complete."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root, repo = map(Path, sys.argv[1:3])
for name, expected in json.loads((root / 'freeze.json').read_text())['files'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
for entry in json.loads((root / 'data_manifest.json').read_text()):
    assert hashlib.sha256((root / 'data' / (entry['stream']+'.npz')).read_bytes()).hexdigest() == entry['prefix_sha256']
subprocess.run([sys.executable, str(root/'controller/supervisor.py'), str(root), str(repo),
                '--hours', '24', '--max-workers', '1', '--no-publish'], check=True)
tasks = json.loads((root / 'tasks.json').read_text())
if not all((root / 'done' / (task['id']+'.json')).exists() for task in tasks):
    raise SystemExit('INCOMPLETE: inspect status/events; no held-out results evaluated.')
subprocess.run([sys.executable, str(root/'controller/evaluate.py'), str(root)], check=True)
