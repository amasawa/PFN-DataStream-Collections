"""Generate the paper's table rows from result CSVs; no number in the paper is typed by hand."""
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NAMES = {'elec2': 'Elec2', 'h2_airlines': 'Airlines', 'h2_phishing': 'Phishing', 'h2_poker': 'Poker',
         'h2_rialto': 'Rialto', 'h2_spam': 'Spam', 'h2_weather': 'Weather'}


def dev_table():
    """Development streams, backbone seeds 1-2 (the seeds with MICE caches): standalone and plugged-in DUO."""
    m = pd.read_csv(REPO / 'MiceDuo/results/night_20261007/duo_replicates_metrics.csv')
    m = m[(m.seed > 0) & (m.anchor == 1)]
    alone = m.pivot_table(index='stream', columns='method', values='acc')
    plug = pd.read_csv(REPO / 'experiments/duo_safe_20261008/results.csv').groupby('stream').mean(numeric_only=True)
    rows, cols = [], []
    for s, name in NAMES.items():
        vals = [plug.fifo[s], alone['sel'][s], alone['duo'][s], plug.mice[s], plug['mice+sel1'][s]]
        cols.append(vals)
        best = max(vals)
        cells = [f'\\textbf{{{v:.2f}}}' if abs(v - best) < 5e-3 else f'{v:.2f}' for v in vals]
        rows.append(f'{name} & ' + ' & '.join(cells) + f' & {vals[4] - vals[3]:+.2f} \\\\')
    mean = pd.DataFrame(cols).mean()
    rows.append('\\midrule')
    rows.append('Mean & ' + ' & '.join(f'{v:.2f}' for v in mean) + f' & {mean[4] - mean[3]:+.2f} \\\\')
    (HERE / 'tab_dev_rows.tex').write_text('\n'.join(rows) + '\n')


def verdict_table():
    v = pd.read_csv(REPO / 'experiments/duo_safe_20261008/verdicts.csv')
    label = {'mice+sel1': '+sel (anchor 100)', 'mice+sel3': '+sel (anchor 300)',
             'mice+sel5': '+sel (anchor 500)', 'mice+duo1': '+DUO mixture'}
    rows = [f"{label[r.variant]} & {r.seed} & {r.mean_vs_mice:+.2f} & {r.wins_vs_mice}/7 & {r.worst_vs_mice:+.2f} & "
            f"{r.worst_vs_fifo:+.2f} & {r.d_logloss:+.4f} & {'yes' if r.passed else 'no'} \\\\" for r in v.itertuples()]
    (HERE / 'tab_verdict_rows.tex').write_text('\n'.join(rows) + '\n')


if __name__ == '__main__':
    dev_table()
    verdict_table()
    print((HERE / 'tab_dev_rows.tex').read_text())
    print((HERE / 'tab_verdict_rows.tex').read_text())
