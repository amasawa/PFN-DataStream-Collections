"""Bit-identity check of a verification replay against the original outputs (GPU integrity incident 2026-10-18,
PLAN.md). The output files of one task are <stem>.npz, <stem>.pkl, <stem>.closes.pkl and <stem>__probs.npz (those that
exist in either directory); each must exist in both and be equal: npz every array except wall time "wt" and
"peak_mem", compared byte for byte (dtype, shape and raw bytes); pkl the whole object (arrays byte for byte).
Prints only IDENTICAL / DIFFERENT / MISSING and the names of the differing keys, never values or scores.
Exit 1 if any file differs or is missing, or if no file of the stem exists. Without a stem, every file of the
verify directory is compared (diagnostic use).
Usage: python verify_compare.py <verify P dir> <original P dir> [<stem>]"""
import os, pickle, sys
import numpy as np

SKIP = {"wt", "te", "peak_mem"}


def same(a, b):
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return type(a) == type(b) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, np.ndarray):
        if not (isinstance(b, np.ndarray) and a.shape == b.shape and a.dtype == b.dtype):
            return False
        if a.dtype.kind == "O":
            return all(same(x, y) for x, y in zip(a.ravel(), b.ravel()))
        return np.ascontiguousarray(a).tobytes() == np.ascontiguousarray(b).tobytes()
    if isinstance(a, np.generic):
        return type(a) == type(b) and a.tobytes() == b.tobytes()
    if isinstance(a, float) and isinstance(b, float):
        return np.float64(a).tobytes() == np.float64(b).tobytes()
    return type(a) == type(b) and a == b


def compare(vf, of):
    if not os.path.exists(of):
        return False, "original missing"
    if vf.endswith(".npz"):
        zv, zo = np.load(vf, allow_pickle=True), np.load(of, allow_pickle=True)
        keys = (set(zv.files) | set(zo.files)) - SKIP
        bad = sorted(k for k in keys if k not in zv.files or k not in zo.files or not same(zv[k], zo[k]))
        return not bad, ",".join(bad)
    return same(pickle.load(open(vf, "rb")), pickle.load(open(of, "rb"))), "pkl"


if __name__ == "__main__":
    vd, od = sys.argv[1], sys.argv[2]; stem = sys.argv[3] if len(sys.argv) > 3 else None
    if stem:
        names = [stem + e for e in (".npz", ".pkl", ".closes.pkl", "__probs.npz")
                 if os.path.exists(f"{vd}/{stem}{e}") or os.path.exists(f"{od}/{stem}{e}")]
    else:
        names = [f for f in sorted(os.listdir(vd)) if (f.endswith(".npz") or f.endswith(".pkl")) and ".ckpt" not in f and ".tmp" not in f]
    n = bad = 0
    for f in names:
        n += 1
        if not os.path.exists(f"{vd}/{f}"):
            bad += 1; print(f, "MISSING in verify"); continue
        ok, why = compare(f"{vd}/{f}", f"{od}/{f}"); bad += not ok
        print(f, "IDENTICAL" if ok else f"DIFFERENT {why}")
    print(f"{n} files, {bad} different")
    sys.exit(1 if bad or n == 0 else 0)
