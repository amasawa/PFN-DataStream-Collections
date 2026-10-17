"""Post-hoc diagnostic for the student's follow-up (exploratory, after the results; not part of the registered
analysis and not reported as evidence in the paper). Per held-out prefix, backbone seed 0, rand draw 0: what the
ranked and the random contexts contain. Columns: alone accuracy of FIFO / sel / rand; mean age of the non-anchor
selected batches (t - b); share of the query batch's labels whose class is absent from the context (class coverage);
total-variation distance between the label histogram of the context and of the query batch (label shift).

Usage: python diagnose.py <rand root>"""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HELD = Path.home() / 'pfn-runs/duo-heldout-20261008'
OUT = Path(__file__).resolve().parents[2] / 'MiceDuo/results/duo_rand_diagnostic.csv'


def describe(chosen, y, K, ts):
    age, miss, tv = [], [], []
    for t in ts:
        b = chosen[t]
        b = b[(b >= 0) & (b < t - 1)]                      # non-anchor batches (anchor a = 1)
        ctx = np.concatenate([y[chosen[t][chosen[t] >= 0]].ravel()])
        hq, hc = np.bincount(y[t], minlength=K) / len(y[t]), np.bincount(ctx, minlength=K) / len(ctx)
        age.append((t - b).mean() if len(b) else np.nan)
        miss.append(100 * hq[hc == 0].sum())
        tv.append(0.5 * np.abs(hq - hc).sum())
    return np.nanmean(age), np.mean(miss), np.mean(tv)


def acc(P, y, ts):
    return 100 * (P[ts].argmax(-1) == y[ts]).mean()


def main(root):
    rows = []
    for e in json.loads((HELD / 'data_manifest.json').read_text()):
        s = e['stream']
        d = np.load(HELD / f'duo/s0/{s}.npz')
        r = np.load(Path(root) / f'out/rand/s0/d0/{s}.npz')
        y = d['y'].astype(int); K = d['P_sel'].shape[-1]
        ts = np.arange(11, len(y))                           # enough history for selection to differ from FIFO
        sa, sm, st = describe(d['chosen'].astype(int), y, K, ts)
        ra, rm, rt = describe(r['chosen'].astype(int), y, K, ts)
        rows.append(dict(stream=s, source=e['source'], fifo=acc(d['P_fifo'], y, ts), sel=acc(d['P_sel'], y, ts),
                         rand=acc(r['P'], y, ts), sel_age=sa, rand_age=ra, sel_missing=sm, rand_missing=rm,
                         sel_tv=st, rand_tv=rt))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(df.round(2).to_string())
    print(df.groupby('source').mean(numeric_only=True).round(2).to_string())


if __name__ == '__main__':
    main(sys.argv[1])
