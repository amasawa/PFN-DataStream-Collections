"""Isolated, causal GPU workers for the pre-registered overnight experiment."""
import argparse
import json
import os
from pathlib import Path
import pickle
import signal
import sys
import time

import numpy as np

STOP = False


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def checkpoint(path, value):
    temporary = Path(str(path) + '.tmp')
    with temporary.open('wb') as handle:
        pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
    temporary.replace(path)


def nll(probability, labels):
    return -np.log(np.clip(probability[np.arange(len(labels)), labels], 1e-6, 1)).mean()


def anchor_selection(model, X, y, t, anchor, B=100, M=1000, H=100):
    """Every context and selection label precedes query batch t."""
    recent = list(range(max(0, t - anchor), t))
    candidates = list(range(max(0, t - H), max(0, t - anchor)))
    slots = M // B - len(recent)
    if len(candidates) <= slots:
        return candidates + recent
    idx = np.concatenate([np.arange(b * B, (b + 1) * B) for b in candidates])
    lo = recent[0] * B
    probability = model.predict(X[lo:t * B], y[lo:t * B], X[idx])
    loss = -np.log(np.clip(probability[np.arange(len(idx)), y[idx]], 1e-6, 1))
    loss = loss.reshape(len(candidates), B).mean(1)
    return sorted([candidates[i] for i in np.argsort(loss)[:slots]] + recent)


def duo_run(task, data, output, model, progress, stop_after=None):
    """Checkpoint all numerical state; resume does not replay a label update."""
    global STOP
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    part = output.with_suffix('.part.pkl')
    z = np.load(data)
    X, y = z['X'].astype(np.float32), z['y'].astype(int)
    B, T, K = 100, min(300, len(y) // 100), int(y.max()) + 1
    keys = ('fifo', 'sel', 'duo', 'safe')
    state = dict(t=1, P={k: np.zeros((T, B, K), np.float16) for k in keys},
                 L=np.zeros(2), Lsafe=np.zeros(2), prev=None,
                 chosen=np.full((T, 10), -1), weights=np.full((T, 2), np.nan))
    if part.exists():
        with part.open('rb') as handle:
            saved = pickle.load(handle)
        assert saved['task'] == task, 'Checkpoint configuration mismatch'
        state = saved['state']
    t_start = state['t']
    for t in range(t_start, T):
        q = slice(t * B, (t + 1) * B)
        if state['prev'] is not None:
            yb = y[(t - 1) * B:t * B]
            state['L'] = .5 * state['L'] + np.array([nll(p, yb) for p in state['prev']])
            target = np.eye(K)[yb]
            loss = np.array([.5 * ((p - target) ** 2).sum(1).mean() for p in state['prev']])
            state['Lsafe'] = .9 * state['Lsafe'] + .5 * loss
        Pf = model.predict(X[max(0, t * B - 1000):t * B], y[max(0, t * B - 1000):t * B], X[q])
        selected = anchor_selection(model, X, y, t, task['anchor'])
        assert selected == sorted(set(selected)) and max(selected) < t and len(selected) <= 10
        idx = np.concatenate([np.arange(b * B, (b + 1) * B) for b in selected])
        Ps = model.predict(X[idx], y[idx], X[q])
        w = np.exp(-2 * (state['L'] - state['L'].min())); w /= w.sum()
        ws = np.exp(-.9 * (state['Lsafe'] - state['Lsafe'].min())); ws /= ws.sum()
        for key, p in zip(keys, (Pf, Ps, w[0] * Pf + w[1] * Ps, ws[0] * Pf + ws[1] * Ps)):
            assert np.isfinite(p).all() and np.allclose(p.sum(1), 1, atol=1e-4)
            state['P'][key][t] = p
        state['prev'] = (Pf, Ps)
        state['chosen'][t, :len(selected)] = selected
        state['weights'][t] = (w[1], ws[1])
        state['t'] = t + 1
        if t % 10 == 0 or STOP or (stop_after is not None and t >= stop_after):
            checkpoint(part, dict(task=task, state=state))
            atomic_json(progress, dict(batch=t, total=T, time=time.time()))
        if STOP or (stop_after is not None and t >= stop_after):
            return False
    tmp = str(output) + '.tmp.npz'
    np.savez_compressed(tmp, y=y[:T * B].reshape(T, B), chosen=state['chosen'],
                        weights=state['weights'], B=B, M=1000, H=100,
                        **{f'P_{k}': p for k, p in state['P'].items()})
    os.replace(tmp, output)
    if part.exists():
        part.unlink()
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root'); parser.add_argument('task_id')
    args = parser.parse_args()
    root = Path(args.root)
    task = next(t for t in json.loads((root / 'tasks.json').read_text()) if t['id'] == args.task_id)
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    total = torch.cuda.get_device_properties(0).total_memory
    torch.cuda.set_per_process_memory_fraction(1792 * 1024**2 / total)
    sys.path.insert(0, str(root / 'source' / 'MICE'))
    import run
    seed = task.get('seed', 2)
    original = run.TFM
    progress = root / 'progress' / (task['id'] + '.json')

    class ObservedTFM(original):
        def __init__(self, K):
            super().__init__(K, seed=seed)
            self.last_report = 0

        def predict(self, Xc, yc, Xq):
            if STOP and task['kind'] == 'mice':
                sys.exit(75)  # resume the most recent original MICE checkpoint
            # Chunk only DUO's large ranking queries; the 100-row queries of MICE are unchanged.
            if len(Xq) > 1000:
                P = np.zeros((len(Xq), self.K)); labs = np.unique(yc)
                if len(labs) == 1:
                    P[:, labs[0]] = 1
                else:
                    self.m.fit(Xc, yc)
                    for i in range(0, len(Xq), 1000):
                        P[i:i + 1000, self.m.classes_.astype(int)] = self.m.predict_proba(Xq[i:i + 1000])
                self.calls += 1
            else:
                P = super().predict(Xc, yc, Xq)
            if time.time() - self.last_report > 20:
                atomic_json(progress, dict(calls=self.calls, time=time.time()))
                self.last_report = time.time()
            return P

    run.TFM = ObservedTFM
    started = time.time()
    print('START', task, flush=True)
    if task['kind'] == 'mice':
        run.DATA = str(root / ('data_dev' if task['stage'] == 'duo_replicates' else 'data'))
        out = root / task['out']
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"{task['stream']}__{task['method']}.npz"
        if task['method'].startswith('micev') and dst.exists() and not dst.with_suffix('.pkl').exists():
            dst.unlink()  # only this task's incomplete result, never an input/archive
        run.run(task['stream'], task['method'], 100, str(out))
        with np.load(dst) as z:
            assert np.isfinite(z['acc'][1:]).all()
        if task['method'].startswith('micev'):
            with dst.with_suffix('.pkl').open('rb') as handle:
                cached = pickle.load(handle)
            assert len(cached['cache']) == len(cached['y']) // 100 - 1
    else:
        data = root / 'data' / (task['stream'] + '.npz')
        with np.load(data) as z:
            model = ObservedTFM(int(z['y'].max()) + 1)
        if not duo_run(task, data, root / task['out'], model, progress):
            sys.exit(75)
    atomic_json(root / 'done' / (task['id'] + '.json'), dict(task=task, elapsed=time.time() - started, ended=time.time()))
    print('DONE', task['id'], flush=True)


if __name__ == '__main__':
    def stop(signum, frame):
        global STOP
        STOP = True
    signal.signal(signal.SIGTERM, stop)
    main()
