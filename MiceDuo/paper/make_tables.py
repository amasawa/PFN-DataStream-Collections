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


def mech_table():
    """Controlled recurrence: mean accuracy per recurrence level and concept difficulty (3 data seeds each)."""
    r = pd.read_csv(REPO / 'experiments/duo_safe_20261008/mechanism_results.csv')
    r['d'] = r['mice+sel1'] - r.mice
    level = {'k3': '5 times', 'k5': '3 times', 'k15': 'once'}
    rows = []
    for lvl in ('k3', 'k5', 'k15'):
        for c in (30, 100):
            g = r[(r.level == lvl) & (r.centroids == c)]
            rows.append(f"{level[lvl]} & {c} & {g.fifo.mean():.2f} & {g.mice.mean():.2f} & {g['mice+sel1'].mean():.2f} & "
                        f"{g.d.mean():+.2f} & {g.d.min():+.2f} & {int((g.d > 0).sum())}/{len(g)} \\\\")
        if lvl != 'k15':
            rows.append('\\addlinespace')
    (HERE / 'tab_mech_rows.tex').write_text('\n'.join(rows) + '\n')
    v = pd.read_csv(REPO / 'experiments/duo_safe_20261008/mechanism_verdicts.csv')
    lines = [f"{r.variant}: gain K3 {r.gain_k3:+.3f}, K5 {r.gain_k5:+.3f}, K15 {r.gain_k15:+.3f}; wins K3 {r.wins_k3}/6; "
             f"worst vs MICE {r.worst_vs_mice:+.3f}; worst vs FIFO {r.worst_vs_fifo:+.3f}; dLL {r.d_logloss:+.4f}; "
             f"H1 {r.H1} H2 {r.H2} H3 {r.H3}" for r in v.itertuples()]
    (HERE / 'mech_numbers.txt').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    dev_table()
    verdict_table()
    mech_table()
    print((HERE / 'tab_mech_rows.tex').read_text())
    print((HERE / 'mech_numbers.txt').read_text())
    print((HERE / 'tab_dev_rows.tex').read_text())
    print((HERE / 'tab_verdict_rows.tex').read_text())
