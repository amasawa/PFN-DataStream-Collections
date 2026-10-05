"""run.py with a key-value cache for contexts that repeat (TabPFN only), without touching run.py.
A stored expert keeps the same context between two segment closings, so its context side can be computed once
(fit_mode="fit_with_cache") and reused for every batch; window contexts change every batch and are computed as before.
A context is identified by a hash of its rows and labels. The first time a context is seen it is fitted in the normal
mode; the second time a cached estimator is built; from then on only the query side is computed. At most MAXC cached
estimators are kept (least recently used out).
REJECTED by the acceptance test on 2026-10-05 (max probability difference 1e-2 against run.py, 17% faster on one
development stream): do NOT use it for results
(see logs/EXPERIMENT_LOG.md, 2026-10-05, speed-up plan). Same arguments as run.py."""
import argparse, hashlib, os
from collections import OrderedDict

import numpy as np
import run

MAXC = int(os.environ.get("MICE_MAXC", 16))


class CachedTFM(run.TFM):
    def __init__(self, n_classes, seed=0):
        super().__init__(n_classes, seed)
        self.seed, self.seen, self.cached, self.hits = seed, OrderedDict(), OrderedDict(), 0

    def _new_cached(self):
        from tabpfn import TabPFNClassifier
        from tabpfn.constants import ModelVersion
        return TabPFNClassifier.create_default_for_version(ModelVersion.V2, device="cuda", random_state=self.seed, n_estimators=4,
                                                           ignore_pretraining_limits=True, fit_mode="fit_with_cache")

    def predict(self, Xc, yc, Xq):
        labs = np.unique(yc)
        if len(labs) == 1:
            return super().predict(Xc, yc, Xq)
        key = hashlib.blake2b(np.ascontiguousarray(Xc).tobytes() + np.ascontiguousarray(yc).tobytes() + str(Xc.shape).encode(),
                              digest_size=16).hexdigest()
        if key in self.cached:
            m = self.cached[key]; self.cached.move_to_end(key); self.hits += 1
        elif key in self.seen:                      # second sight: this context repeats, build its cache
            m = self._new_cached(); m.fit(Xc, yc); self.cached[key] = m
            if len(self.cached) > MAXC:
                self.cached.popitem(last=False)
        else:                                       # first sight: normal path, remember the key
            self.seen[key] = True
            if len(self.seen) > 4096:
                self.seen.popitem(last=False)
            return super().predict(Xc, yc, Xq)
        P = np.zeros((len(Xq), self.K))
        P[:, m.classes_.astype(int)] = m.predict_proba(Xq)
        self.calls += 1
        return P


run.TFM = CachedTFM

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_dev")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for meth in a.methods:
            run.run(s, meth, a.B, a.out)
