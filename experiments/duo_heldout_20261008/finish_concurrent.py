"""Operational amendment (AMENDMENT_20261008.md): run the frozen snapshot with 4 workers instead of 1.

Same as the frozen controller/finish.py except --max-workers 4 and a breaker-window check before start.
The snapshot under RUN_ROOT is not modified; its hashes are verified before the run and before evaluation.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def verify(root):
    for name, expected in json.loads((root / 'freeze.json').read_text())['files'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    for entry in json.loads((root / 'data_manifest.json').read_text()):
        path = root / 'data' / (entry['stream'] + '.npz')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['prefix_sha256'], path


def recent_failures(root, window=600):
    count = 0
    if (root / 'events.log').exists():
        for line in (root / 'events.log').read_text().splitlines():
            if ' RETRY ' in line:
                try:
                    stamp = datetime.fromisoformat(line.split()[0]).timestamp()
                except ValueError:
                    continue
                count += stamp > time.time() - window
    return count


root, repo = map(Path, sys.argv[1:3])
verify(root)
if (root / 'STOP').exists():
    raise SystemExit('STOP present: inspect the reason and rename it deliberately before resuming.')
if recent_failures(root) >= 6:
    raise SystemExit('Breaker window already at 6 failures in ten minutes; wait or investigate.')
subprocess.run([sys.executable, str(root / 'controller/supervisor.py'), str(root), str(repo),
                '--hours', '24', '--max-workers', '4', '--breaker', '6', '--no-publish'], check=True)
tasks = json.loads((root / 'tasks.json').read_text())
if not all((root / 'done' / (task['id'] + '.json')).exists() for task in tasks):
    raise SystemExit('INCOMPLETE: inspect status/events; no held-out results evaluated.')
verify(root)
subprocess.run([sys.executable, str(root / 'controller/evaluate.py'), str(root)], check=True)
