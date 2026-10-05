"""Summaries of stream_bench.py outputs: overall prequential accuracy, accuracy in the first `h` scored batches after
each event type, novel-row detection AUROC in the first `h` batches after the novel event (before its labels can
enter the context), and resets per event type (a reset in the h batches after a tilt is a needless reset).
Usage: python stream_eval.py ../results/stream_dev [h]"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def summarise(d, h=10):
    rows = []
    for f in sorted(glob.glob(f"{d}/*.npz")):
        stream, pol = os.path.basename(f)[:-4].split("__")
        z = np.load(f)
        acc, ev, B, y, rej, resets = z["acc"], z["ev"], int(z["B"]), z["y"], z["rej"], z["resets"]
        T = len(acc)
        bev = np.array([ev[t * B] for t in range(T)])
        starts = [t for t in range(1, T) if bev[t] != bev[t - 1]]
        r = dict(stream=stream, policy=pol, acc=np.nanmean(acc), resets=len(resets))
        for e in ("tilt", "translate", "real", "novel"):
            ts = [t for t in starts if bev[t] == e]
            win = [acc[t:t + h] for t in ts]
            r[f"acc_{e}"] = np.nanmean(np.concatenate(win)) if win else np.nan
            r[f"resets_{e}"] = sum(((resets >= t) & (resets < t + h)).sum() for t in ts)
            if e == "novel" and ts:
                K = int(z["K"])
                idx = np.r_[[np.arange(t * B, (t + h) * B) for t in ts]].ravel()
                idx = idx[idx < len(y)]
                isn = y[idx] == K - 1
                r["auroc_novel"] = roc_auc_score(isn, rej[idx]) if 0 < isn.sum() < len(isn) else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    d = sys.argv[1]
    h = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    s = summarise(d, h)
    s.to_csv(f"{d}/summary.csv", index=False)
    s["family"] = s.stream.str.replace(r"_s\d+$", "", regex=True)
    pd.set_option("display.width", 220)
    print(s.groupby(["family", "policy"]).mean(numeric_only=True).round(3).to_string())
