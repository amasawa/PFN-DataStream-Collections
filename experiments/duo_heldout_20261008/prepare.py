"""Freeze sources, ordered data prefixes and 132 tasks, without reading any result."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
GROUPS = {
    'covertype': ['covertype', 'h3_covertype_b', 'h3_covertype_c', 'h4_covertype_d', 'h4_covertype_e'],
    'airlines': ['h3_airlines_b', 'h3_airlines_c', 'h4_airlines_d', 'h4_airlines_e'],
    'poker': ['h3_poker_b', 'h3_poker_c', 'h4_poker_d', 'h4_poker_e'],
    'insects': ['insects_abrupt_balanced', 'insects_abrupt_imbalanced', 'insects_gradual_balanced',
                'insects_gradual_imbalanced', 'insects_incremental_abrupt_balanced',
                'insects_incremental_balanced', 'insects_incremental_reoccurring_balanced',
                'h3_insects_b', 'h3_insects_c'],
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(root):
    root = Path(root).resolve()
    if root.exists():
        raise SystemExit('Refusing to overwrite an existing run; resume its frozen controller instead.')
    for directory in ('source/MICE', 'controller', 'data', 'logs', 'done', 'progress', 'reports'):
        (root / directory).mkdir(parents=True, exist_ok=True)
    for name in ('run.py', 'reweight.py'):
        shutil.copy2(REPO / 'MICE/code' / name, root / 'source/MICE' / name)
    for name in ('worker.py', 'supervisor.py', 'checkpointed_baselines.py'):
        shutil.copy2(REPO / 'experiments/night_20261007' / name, root / 'controller' / name)
    for name in ('heldout_worker.py', 'evaluate.py', 'finish.py'):
        shutil.copy2(HERE / name, root / 'controller' / name)
    # The wrapper adds instrumentation but delegates prediction/state semantics to the tested worker.
    shutil.copy2(root / 'controller/worker.py', root / 'controller/base_worker.py')
    shutil.copy2(HERE / 'heldout_worker.py', root / 'controller/worker.py')
    shutil.copy2(HERE / 'PLAN.md', root / 'PLAN.md')
    entries, tasks = [], []
    for source, streams in GROUPS.items():
        for stream in streams:
            src = REPO / 'MICE/data' / (stream + '.npz')
            dst = root / 'data' / src.name
            with np.load(src) as z:
                n = len(z['y']); rows = min(30000, n // 100 * 100)
                assert rows >= 200 and len(z['X']) == n and len(z['concept']) == n
                np.savez_compressed(dst, **{k: z[k][:rows] if z[k].ndim and len(z[k]) == n else z[k]
                                           for k in z.files})
            entries.append(dict(stream=stream, source=source, input_rows=n, rows=rows,
                                input_sha256=digest(src), prefix_sha256=digest(dst)))
    for seed in (0, 1, 2):
        for entry in entries:
            stream = entry['stream']
            for kind in ('mice', 'duo'):
                task = dict(id=f'{kind}_s{seed}_{stream}', stage='heldout', kind=kind,
                            stream=stream, seed=seed, anchor=1)
                task.update(method='micev1000_500', out=f'mice/s{seed}') if kind == 'mice' else task.update(
                    out=f'duo/s{seed}/{stream}.npz')
                tasks.append(task)
    assert len(entries) == 22 and len(tasks) == 132
    (root / 'tasks.json').write_text(json.dumps(tasks, indent=2) + '\n')
    (root / 'data_manifest.json').write_text(json.dumps(entries, indent=2) + '\n')
    files = [p for directory in ('source', 'controller') for p in (root / directory).rglob('*.py')]
    files += [root / p for p in ('PLAN.md', 'tasks.json', 'data_manifest.json')]
    manifest = dict(frozen_at=datetime.now(timezone.utc).isoformat(),
                    files={str(p.relative_to(root)): digest(p) for p in files})
    (root / 'freeze.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(root=str(root), tasks=len(tasks), freeze_sha256=digest(root / 'freeze.json'))))


if __name__ == '__main__':
    main(sys.argv[1])
