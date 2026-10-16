"""Writes <root>/tasks.txt (PLAN.md): rand x 3 draws and orc on the 18 mechanism streams (backbone seed 1), rand x 3
draws on the 22 held-out prefixes x backbone seeds 0-2; and <root>/selcheck.txt (pipeline check). Refuses to
overwrite an existing root."""
import json
from pathlib import Path
import sys

HOME = Path.home() / 'pfn-runs'
MECH, HELD = HOME / 'duo-safe-20261008/data', HOME / 'duo-heldout-20261008/data'


def main(root):
    root = Path(root)
    mech = sorted(p.stem for p in MECH.glob('mech_*.npz'))
    held = [e['stream'] for e in json.loads((HOME / 'duo-heldout-20261008/data_manifest.json').read_text())]
    assert mech == sorted(f'mech_{k}_c{c}_s{s}' for k in ('k3', 'k5', 'k15') for c in (30, 100) for s in (30, 31, 32))
    assert len(held) == len(set(held)) == 22 and all((HELD / f'{s}.npz').exists() for s in held)
    lines = []
    for s in mech:
        lines += [f'rand {s} 1 {d} {MECH}/{s}.npz' for d in range(3)] + [f'orc {s} 1 0 {MECH}/{s}.npz']
    for seed in range(3):
        for s in held:
            lines += [f'rand {s} {seed} {d} {HELD}/{s}.npz' for d in range(3)]
    assert len(lines) == 270
    root.mkdir(parents=False, exist_ok=False)
    (root / 'tasks.txt').write_text('\n'.join(lines) + '\n')
    (root / 'selcheck.txt').write_text(f'selcheck mech_k3_c30_s30 1 0 {MECH}/mech_k3_c30_s30.npz\n'
                                       f'selcheck h3_poker_b 0 0 {HELD}/h3_poker_b.npz\n')


if __name__ == '__main__':
    main(sys.argv[1])
