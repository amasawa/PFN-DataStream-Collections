"""Summaries of run.py outputs. For streams with known concepts: overall accuracy, accuracy in the first `h` scored
batches after a concept switch, split into first visits and recurrences (Observation 1), and accuracy in the last
`h` batches of each block (steady state). Usage: python evaluate.py ../results_dev [h]"""
import glob
import os
import sys

import numpy as np
import pandas as pd


def summarise(d, h=5):
    rows = []
    for f in sorted(glob.glob(f"{d}/*.npz")):
        stream, meth = os.path.basename(f)[:-4].split("__")
        z = np.load(f)
        acc, B, c = z["acc"], int(z["B"]), z["concept"]
        T = len(acc)
        r = dict(stream=stream, method=meth, acc=np.nanmean(acc), time=z["wt"].sum())
        if c[0] >= 0:
            bc = np.array([c[t * B] for t in range(T)])
            starts = [t for t in range(1, T) if bc[t] != bc[t - 1]]
            first, rec = [], []
            for t in starts:
                (rec if (bc[:t] == bc[t]).any() else first).append(acc[t:t + h])
            ends = [acc[max(t - h, 1):t] for t in starts[1:]] + [acc[T - h:]]
            r.update(acc_first=np.nanmean(np.concatenate(first)) if first else np.nan,
                     acc_recur=np.nanmean(np.concatenate(rec)) if rec else np.nan,
                     acc_steady=np.nanmean(np.concatenate(ends)))
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = sys.argv[1]
    h = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    s = summarise(d, h)
    s.to_csv(f"{d}/summary.csv", index=False)
    s["family"] = s.stream.str.replace(r"_s\d+$", "", regex=True)
    pd.set_option("display.width", 200)
    print(s.groupby(["family", "method"]).mean(numeric_only=True).round(4).to_string())
