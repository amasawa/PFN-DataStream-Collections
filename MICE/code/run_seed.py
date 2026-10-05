"""run.py with another random seed of the backbone (MICE_SEED, default 1), without touching run.py: the seed sets
random_state of the TFM, i.e. the feature and class permutations of its ensemble members. Same arguments as run.py."""
import argparse, os
import run

SEED = int(os.environ.get("MICE_SEED", 1))
_TFM = run.TFM
run.TFM = lambda K: _TFM(K, SEED)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", nargs="+"); ap.add_argument("--methods", nargs="+")
    ap.add_argument("--B", type=int, default=100); ap.add_argument("--out", default="../results_dev")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for s in a.streams:
        for meth in a.methods:
            run.run(s, meth, a.B, a.out)
