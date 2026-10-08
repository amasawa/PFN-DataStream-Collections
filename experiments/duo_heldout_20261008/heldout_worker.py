"""Instrumentation wrapper; prediction and checkpoint code remain in frozen base_worker."""
import json
from pathlib import Path
import signal
import sys
import time

import base_worker as base

atomic_json = base.atomic_json  # supervisor interface


def install_cost_recorder(root, task_id):
    original_duo, original_select = base.duo_run, base.anchor_selection

    def measured_duo(task, data, output, model, progress, stop_after=None):
        counts = dict(fits=0, forward_calls=0)
        for name, key in (('fit', 'fits'), ('predict_proba', 'forward_calls')):
            original = getattr(model.m, name)
            def counted(*args, _original=original, _key=key, **kwargs):
                counts[_key] += 1
                return _original(*args, **kwargs)
            setattr(model.m, name, counted)
        active = {}
        path = root / 'logs' / (task_id + '.cost.jsonl')

        class Proxy:
            def __getattr__(self, name):
                return getattr(model, name)

            def predict(self, *args, **kwargs):
                probability = model.predict(*args, **kwargs)
                # The first prediction after selection returns is the selected-context query.
                if active.get('selected'):
                    row = dict(batch=active['batch'], seconds=time.perf_counter() - active['start'],
                               logical_calls=model.calls-active['calls'],
                               **{k: counts[k]-active[k] for k in counts})
                    with path.open('a') as handle:
                        handle.write(json.dumps(row) + '\n')
                    active.clear()
                return probability

        def selection(proxy, X, y, t, anchor, **kwargs):
            active.update(batch=t, start=time.perf_counter(), calls=model.calls, **counts)
            chosen = original_select(proxy, X, y, t, anchor, **kwargs)
            active['selected'] = True
            return chosen

        base.anchor_selection = selection
        try:
            return original_duo(task, data, output, Proxy(), progress, stop_after=stop_after)
        finally:
            base.anchor_selection = original_select

    base.duo_run = measured_duo


def main():
    root, task_id = Path(sys.argv[1]), sys.argv[2]
    install_cost_recorder(root, task_id)
    def stop(signum, frame):
        base.STOP = True
    signal.signal(signal.SIGTERM, stop)
    started = time.time()
    success = False
    try:
        base.main()
        success = True
    finally:
        import torch
        row = dict(started=started, ended=time.time(), success=success,
                   peak_allocated_mib=torch.cuda.max_memory_allocated()/1024**2)
        with (root / 'logs' / (task_id + '.attempts.jsonl')).open('a') as handle:
            handle.write(json.dumps(row) + '\n')


if __name__ == '__main__':
    main()
