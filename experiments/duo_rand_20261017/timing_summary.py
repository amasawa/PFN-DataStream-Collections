"""Summary of the matched timing benchmark (bench.py, replay_timing.py): seconds per batch of MICE, MICE+sel and
MICE+rand per prefix (mean over the two repetitions), the extra expert's time added to MICE's online step plus the
replay increment. Writes MiceDuo/results/duo_rand_timing.csv.

Usage: python timing_summary.py <bench root>"""
from pathlib import Path
import sys

import pandas as pd

OUT = Path(__file__).resolve().parents[2] / 'MiceDuo/results/duo_rand_timing.csv'


def main(root):
    b = pd.read_json(Path(root) / 'bench.jsonl', lines=True)
    assert len(b) == 18 and (b.groupby(['policy', 'stream']).size() == 2).all()
    r = pd.read_json(Path(root) / 'replay.jsonl', lines=True).pivot(index='stream', columns='replay',
                                                                     values='s_per_batch')
    m = b.groupby(['stream', 'policy']).mean_s.mean().unstack()
    rep_sd = b.groupby(['stream', 'policy']).mean_s.std(ddof=1).unstack()
    t = pd.DataFrame({'mice': m['mice'], 'replay_extra': r['mice+extra'] - r['mice']})
    t['mice_sel'] = t.mice + m['sel'] + t.replay_extra
    t['mice_rand'] = t.mice + m['rand'] + t.replay_extra
    t['ratio_sel'], t['ratio_rand'] = t.mice_sel / t.mice, t.mice_rand / t.mice
    t['sel_expert'], t['rand_expert'] = m['sel'], m['rand']
    t['max_rep_sd'] = rep_sd.max(axis=1)
    t.loc['mean'] = t.mean()
    t.to_csv(OUT)
    print(t.round(4).to_string())


if __name__ == '__main__':
    main(sys.argv[1])
