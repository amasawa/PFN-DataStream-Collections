"""Create a frozen Linux-filesystem run; existing experiment results are read-only."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np

repo = Path(__file__).resolve().parents[2]
root = Path(sys.argv[1]).resolve()
root.mkdir(parents=True, exist_ok=True)
dev = ['elec2', 'h2_airlines', 'h2_phishing', 'h2_poker', 'h2_rialto', 'h2_spam', 'h2_weather']
streams = ['h3_airlines_b', 'h3_covertype_b', 'h3_insects_b', 'h3_poker_b']
for directory in ('source/MICE', 'data_dev', 'logs', 'done', 'progress', 'reports'):
    (root / directory).mkdir(parents=True, exist_ok=True)
snapshot = {}
for name in ('run.py', 'reweight.py', 'check_heldout4.py'):
    src = repo / 'MICE/code' / name
    dst = root / 'source/MICE' / name
    if not dst.exists():
        shutil.copy2(src, dst)
    snapshot[str(src.relative_to(repo))] = hashlib.sha256(dst.read_bytes()).hexdigest()
if not (root / 'data').exists():
    (root / 'data').symlink_to(repo / 'MICE/data', target_is_directory=True)
for stream in dev:
    dst = root / 'data_dev' / (stream + '.npz')
    if not dst.exists():
        with np.load(root / 'data' / (stream + '.npz')) as z:
            np.savez_compressed(dst, **{k: z[k][:30000] if z[k].ndim else z[k] for k in z.files})
tasks = []
for method in ('micev1000_500', 'fifo1000', 'ddm1000', 'winens1000'):
    for stream in streams:
        tasks.append(dict(id=f'k2_{stream}_{method}', stage='k2', kind='mice', stream=stream,
                          seed=2, method=method, out='results_heldout3_seed2'))
for seed in (0, 1, 2):
    stage = 'duo_dev' if seed == 0 else 'duo_replicates'
    if seed:
        for stream in dev:
            tasks.append(dict(id=f'duo_ref_s{seed}_{stream}', stage=stage, kind='mice', stream=stream,
                              seed=seed, method='micev1000_500', out=f'duo_mice_s{seed}'))
    for anchor in ((3, 5) if seed == 0 else (1, 3, 5)):
        for stream in dev:
            tasks.append(dict(id=f'duo_s{seed}_a{anchor}_{stream}', stage=stage, kind='duo',
                              stream=stream, seed=seed, anchor=anchor,
                              out=f'duo/s{seed}_a{anchor}/{stream}.npz'))
manifest = root / 'tasks.json'
if manifest.exists():
    assert json.loads(manifest.read_text()) == tasks, 'Do not silently change a started experiment'
else:
    manifest.write_text(json.dumps(tasks, indent=2) + '\n')
(root / 'source_manifest.json').write_text(json.dumps(snapshot, indent=2) + '\n')
print(root, len(tasks), 'tasks', flush=True)
