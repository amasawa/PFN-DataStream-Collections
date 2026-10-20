import sys, numpy as np
a, b = np.load(sys.argv[1], allow_pickle=False), np.load(sys.argv[2], allow_pickle=False)
for k in a.files:
    x, y = a[k], b[k]
    same = x.shape == y.shape and x.dtype == y.dtype and x.tobytes() == y.tobytes()
    line = f"{k}: shape {x.shape} {x.dtype} " + ("identical" if same else "DIFFERENT")
    if not same and x.shape == y.shape and np.issubdtype(x.dtype, np.floating):
        xd, yd = x.astype(np.float64), y.astype(np.float64)
        d = np.abs(xd - yd); m = x.ravel() != y.ravel()
        rel = d / np.maximum(np.abs(xd), 1e-300)
        line += (f"; differing elements {int(m.sum())}/{x.size}; max abs diff {d.max():.3e}; "
                 f"max rel diff {rel.max():.3e}; differing indices (first 10) {np.flatnonzero(m)[:10].tolist()}")
    print(line)
