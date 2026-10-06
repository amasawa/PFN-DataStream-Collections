"""Control for the emergence streams (design: logs/EXPERIMENT_LOG.md, 2026-10-06, "抢救"): FIFO on the ORIGINAL first
NROWS rows of a source (no class removed), same protocol as stream_emerge.py. Rows at or after T0 are identical in the
emergence stream and here (only rows before T0 were removed), so the cost of emergence can be measured on the same rows.
Output: ../results/stream_control/<source>.npz with y and P_fifo per batch. Usage: python stream_control.py <source> [...]"""
import os, sys, time
import numpy as np
from stream_emerge import TFM, B, M, NROWS, DATA

OUT = "../results/stream_control"
if __name__ == "__main__":
    for src in sys.argv[1:]:
        dst = f"{OUT}/{src}.npz"
        if os.path.exists(dst):
            continue
        z = np.load(f"{DATA}/{src}.npz")
        X, y = np.nan_to_num(z["X"][:NROWS].astype(np.float32)), z["y"][:NROWS].astype(int)
        K, T = int(y.max()) + 1, len(y) // B; f = TFM(K); P = np.zeros((T, B, K), np.float16); t0 = time.time()
        for t in range(1, T):
            lo = max(0, t * B - M); P[t] = f.predict(X[lo:t * B], y[lo:t * B], X[t * B:(t + 1) * B])
        os.makedirs(OUT, exist_ok=True)
        np.savez_compressed(dst, y=y[:T * B].reshape(T, B), P_fifo=P, B=B, M=M)
        print(src, f"acc={(P[1:].argmax(2) == y[B:T * B].reshape(T - 1, B)).mean():.4f} time={time.time() - t0:.0f}s", flush=True)
