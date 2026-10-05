"""run.py for the single-context baselines (fifo, ltm, ddm) that also stores their per-row predicted probabilities, so
that metrics other than accuracy can be computed later. run.py is not touched: every call of the TFM is recorded.
These methods call the TFM exactly once per scored batch, in batch order, so the recorded calls are the batches
1, 2, ... of the stream. Writes <out>/<stream>__<method>.npz as run.py does and <out>/<stream>__<method>__probs.npz
(P as float16, rows B onwards). Same arguments as run.py."""
import argparse, os
import numpy as np
import run

REC = []


class RecTFM(run.TFM):
    def predict(self, Xc, yc, Xq):
        P = super().predict(Xc, yc, Xq); REC.append(P.astype(np.float32)); return P


run.TFM = RecTFM

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_probs")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for meth in a.methods:
            assert meth.startswith(("fifo", "ltm", "ddm")), "one TFM call per batch is assumed"
            dst = f"{a.out}/{s}__{meth}__probs.npz"
            if os.path.exists(dst):
                continue
            if os.path.exists(f"{a.out}/{s}__{meth}.npz"):   # a run that died between the two files: redo it
                os.remove(f"{a.out}/{s}__{meth}.npz")
            REC.clear(); run.run(s, meth, a.B, a.out)
            np.savez_compressed(dst, P=np.concatenate(REC).astype(np.float16), n_calls=len(REC))
