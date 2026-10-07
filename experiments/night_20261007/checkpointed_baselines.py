"""The original MICE FIFO/DDM/window ensemble loops with atomic 20-batch checkpoints.

Prediction, detector and weighting formulas are unchanged. The original implementation
already checkpoints micev; this module extends that operational protection to baselines.
"""
import os
from pathlib import Path
import pickle
import re
import time

import numpy as np


def run_baseline(module, stream, method, B, out):
    dst = Path(out) / f'{stream}__{method}.npz'
    if dst.exists(): return
    with np.load(Path(module.DATA) / f'{stream}.npz') as z:
        X, y, concept = z['X'], z['y'].astype(int), z['concept']
    K, T = int(y.max()) + 1, len(y) // B
    f = module.TFM(K)
    match = re.fullmatch(r'([a-z]+)(\d+)', method)
    kind, M = match.group(1), int(match.group(2))
    assert kind in ('fifo', 'ddm', 'winens')
    pol = module.DDMReset(M) if kind == 'ddm' else None
    acc, ll, wt = np.full(T, np.nan), np.full(T, np.nan), np.zeros(T)
    Lw, errs, Pw_last, begin = {}, None, None, 1
    ck = dst.with_suffix('.ckpt')
    if ck.exists():
        with ck.open('rb') as handle: st = pickle.load(handle)
        assert st['signature'] == (stream, method, B, T)
        acc, ll, wt, Lw, errs, Pw_last = (st[k] for k in ('acc', 'll', 'wt', 'Lw', 'errs', 'Pw_last'))
        if pol is not None: pol.__dict__.update(st['pol'])
        f.calls, begin = st['calls'], st['t'] + 1
        print(stream, method, f'resumed at batch {begin}', flush=True)
    for t in range(begin, T):
        started = time.time()
        Xq, yq = X[t*B:(t+1)*B], y[t*B:(t+1)*B]
        if kind == 'fifo':
            P = f.predict(*module.fifo(X, y, t, B, M), Xq)
        elif kind == 'ddm':
            if errs is not None: pol.update(errs, t, B)
            P = f.predict(*pol.context(X, y, t, B), Xq)
            errs = (P.argmax(1) != yq).astype(int)
        else:
            if Pw_last is not None:
                yb = y[(t-1)*B:t*B]
                for wsz, Pp in Pw_last.items():
                    Lw[wsz] = .5*Lw.get(wsz, 0.) - np.log(np.clip(Pp[np.arange(len(yb)), yb], 1e-6, 1)).mean()
            Pw_last = {wsz: f.predict(*module.fifo(X, y, t, B, wsz), Xq) for wsz in (100, 300, M)}
            losses = np.array([Lw.get(wsz, 0.) for wsz in Pw_last])
            w = np.exp(-2.*(losses - losses.min())); w /= w.sum()
            P = sum(wi*Pp for wi, Pp in zip(w, Pw_last.values()))
        acc[t] = (P.argmax(1) == yq).mean()
        ll[t] = -np.log(np.clip(P[np.arange(len(yq)), yq], 1e-6, 1)).mean()
        wt[t] = time.time() - started
        if t % int(os.environ.get('MICE_CKPT_EVERY', 20)) == 0:
            state = dict(signature=(stream, method, B, T), acc=acc, ll=ll, wt=wt, Lw=Lw,
                         errs=errs, Pw_last=Pw_last, calls=f.calls, t=t,
                         pol=pol.__dict__ if pol is not None else None)
            with Path(str(ck)+'.tmp').open('wb') as handle: pickle.dump(state, handle)
            os.replace(str(ck)+'.tmp', ck)
    np.savez_compressed(str(dst)+'.tmp.npz', acc=acc, ll=ll, wt=wt, B=B, concept=concept, calls=f.calls, n_experts=0)
    os.replace(str(dst)+'.tmp.npz', dst)
    if ck.exists(): ck.unlink()
    print(stream, method, f'acc={np.nanmean(acc):.4f}', f'time={wt.sum():.0f}s', flush=True)
