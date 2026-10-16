"""MICE-DUO round 1 controls (PLAN.md): the random-selection expert `rand` and the oracle expert `orc`.

Only the choice of context batches differs from DUO's `sel` (frozen base_worker.anchor_selection): same anchor, candidate
horizon, number of slots, chronological order, TFM wrapper (frozen run.TFM with the backbone seed), thread and memory
settings. One long-lived process runs many tasks (CUDA faults grow with process churn, env/MACHINE_LOG.md 2026-10-16);
each task writes its output atomically, and a restarted process skips finished tasks.

Tasks file lines: <kind> <stream> <seed> <draw> <data npz>   (kind in rand, orc, selcheck)
Output: <root>/out/<kind>/s<seed>/d<draw>/<stream>.npz with P (T, B, K) float32, chosen (T, 10), sec (T,).
Usage: python worker.py <root> <worker id> [--tasks f]
"""
import json
import os
import shutil
from pathlib import Path
import sys
import time
import zlib

import numpy as np

FROZEN = Path.home() / 'pfn-runs/duo-heldout-20261008'
sys.path.insert(0, str(FROZEN / 'source/MICE'))
sys.path.insert(0, str(FROZEN / 'controller'))
B, M, H = 100, 1000, 100


def split(t, anchor):
    """Recent, candidate batches and slots exactly as in base_worker.anchor_selection."""
    recent = list(range(max(0, t - anchor), t))
    candidates = list(range(max(0, t - H), max(0, t - anchor)))
    return recent, candidates, M // B - len(recent)


def rng_for(seed, draw, t, stream):
    return np.random.default_rng([seed, draw, t, zlib.crc32(stream.encode())])


def rand_selection(t, anchor, seed, draw, stream):
    recent, candidates, slots = split(t, anchor)
    if len(candidates) <= slots:
        return candidates + recent
    pick = rng_for(seed, draw, t, stream).choice(len(candidates), size=slots, replace=False)
    return sorted([candidates[i] for i in pick] + recent)


def oracle_selection(t, anchor, seed, stream, concept):
    """Most recent candidates of the query batch's concept; the rest from rand draw 0 among the other candidates."""
    recent, candidates, slots = split(t, anchor)
    if len(candidates) <= slots:
        return candidates + recent
    c = concept[t * B]
    assert (concept[t * B:(t + 1) * B] == c).all()
    same = [b for b in reversed(candidates) if concept[b * B] == c][:slots]
    others = [b for b in candidates if b not in same]
    need = slots - len(same)
    if need:
        pick = rng_for(seed, 0, t, stream).choice(len(others), size=need, replace=False)
        same += [others[i] for i in pick]
    return sorted(same + recent)


def make_tfm(K, seed):
    import run

    class ObservedTFM(run.TFM):
        """base_worker.ObservedTFM without progress reporting: chunks only queries above 1000 rows (sel's ranking)."""

        def __init__(self, K):
            super().__init__(K, seed=seed)

        def predict(self, Xc, yc, Xq):
            if len(Xq) > 1000:
                P = np.zeros((len(Xq), self.K)); labs = np.unique(yc)
                if len(labs) == 1:
                    P[:, labs[0]] = 1
                else:
                    self.m.fit(Xc, yc)
                    for i in range(0, len(Xq), 1000):
                        P[i:i + 1000, self.m.classes_.astype(int)] = self.m.predict_proba(Xq[i:i + 1000])
                self.calls += 1
                return P
            return super().predict(Xc, yc, Xq)
    return ObservedTFM(K)


def run_task(root, kind, stream, seed, draw, data, models):
    out = Path(root) / 'out' / kind / f's{seed}' / f'd{draw}' / f'{stream}.npz'
    if out.exists():
        return False
    z = np.load(data)
    X, y = z['X'].astype(np.float32), z['y'].astype(int)
    concept = z['concept'] if 'concept' in z.files else None
    if kind == 'orc':   # every batch holds one concept (blocks of 20 batches), so a batch's first row gives its concept
        cb = concept[:len(concept) // B * B].reshape(-1, B)
        assert (cb == cb[:, :1]).all()
    T, K = min(300, len(y) // B), int(y.max()) + 1
    if (K, seed) not in models:
        models[(K, seed)] = make_tfm(K, seed)
    model = models[(K, seed)]
    if kind == 'selcheck':
        import base_worker
    P = np.zeros((T, B, K), np.float32); chosen = np.full((T, 10), -1); sec = np.full(T, np.nan)
    for t in range(1, T if kind != 'selcheck' else 31):
        q = slice(t * B, (t + 1) * B)
        start = time.perf_counter()
        if kind == 'rand':
            selected = rand_selection(t, 1, seed, draw, stream)
        elif kind == 'orc':
            selected = oracle_selection(t, 1, seed, stream, concept)
        else:
            selected = base_worker.anchor_selection(model, X, y, t, 1)
        assert selected == sorted(set(selected)) and max(selected) < t and len(selected) == min(t, 10) and t - 1 in selected
        idx = np.concatenate([np.arange(b * B, (b + 1) * B) for b in selected])
        p = model.predict(X[idx], y[idx], X[q])
        sec[t] = time.perf_counter() - start
        assert np.isfinite(p).all() and np.allclose(p.sum(1), 1, atol=1e-4)
        P[t], chosen[t, :len(selected)] = p, selected
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = f'{out}.{os.getpid()}.tmp.npz'
    np.savez_compressed(tmp, P=P, chosen=chosen, sec=sec, y=y[:T * B].reshape(T, B))
    os.replace(tmp, out)
    return True


def mine(claim, wid):
    """A claim this worker id owns (a task its previous process did not finish)."""
    try:
        return open(claim + '/owner').read() == wid
    except FileNotFoundError:
        return False


def take(claim, wid):
    """Atomic claim: a directory holding the owner is renamed onto the claim path; the rename fails if another worker
    already holds it (the existing claim directory is never empty), so a claim always names its owner."""
    tmp = f'{claim}.tmp{wid}'
    os.makedirs(tmp, exist_ok=True)
    with open(tmp + '/owner', 'w') as fh:
        fh.write(wid)
    try:
        os.rename(tmp, claim)
        return True
    except OSError:
        shutil.rmtree(tmp)
        return False


def main():
    root, wid = sys.argv[1], sys.argv[2]
    opts = dict(zip(sys.argv[3::2], sys.argv[4::2]))
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(int(os.environ.get('MICE_ALLOC_MIB', '1792')) * 1024**2 / total)
    tasks = [ln.split() for ln in open(opts.get('--tasks', f'{root}/tasks.txt')) if ln.strip()]
    models = {}
    os.makedirs(f'{root}/claims', exist_ok=True)
    held = f'{root}/held/w{wid}'   # informational: the task this process runs (read by worker.sh after a death)
    os.makedirs(f'{root}/held', exist_ok=True)
    for kind, stream, seed, draw, data in tasks:
        claim = f'{root}/claims/{kind}_{stream}_s{seed}_d{draw}'
        out = Path(root) / 'out' / kind / f's{seed}' / f'd{draw}' / f'{stream}.npz'
        if out.exists() or os.path.exists(claim + '/FAILED'):
            continue
        if not (mine(claim, wid) or take(claim, wid)):
            continue
        with open(held + '.tmp', 'w') as fh:
            fh.write(claim)
        os.replace(held + '.tmp', held)
        t0 = time.time()
        run_task(root, kind, stream, int(seed), int(draw), data, models)
        with open(f'{root}/progress.txt', 'a') as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} w{wid} ok {kind} {stream} s{seed} d{draw} {time.time() - t0:.0f}s\n")
        os.remove(held)
    with open(f'{root}/progress.txt', 'a') as fh:
        fh.write(f"{time.strftime('%H:%M:%S')} w{wid} finished\n")


if __name__ == '__main__':
    main()
