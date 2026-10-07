"""Report completed registered stages, including negative results; no GPU work."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import pickle
import subprocess
import sys

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root'); parser.add_argument('repo'); parser.add_argument('stage')
    args = parser.parse_args()
    root, repo = Path(args.root), Path(args.repo)
    tasks = json.loads((root / 'tasks.json').read_text())
    needed = [t for t in tasks if t['stage'] == args.stage]
    assert needed and all((root / 'done' / (t['id'] + '.json')).exists() for t in needed)
    sys.path.insert(0, str(root / 'source/MICE'))
    import reweight
    if args.stage == 'k2':
        project = 'MICE'
        # Run the original checker unchanged, with an isolated sibling result directory.
        link = root / 'source/results_heldout3_seed2'
        if not link.exists():
            link.symlink_to(root / 'results_heldout3_seed2', target_is_directory=True)
        checked = subprocess.run([sys.executable, 'check_heldout4.py', 'K2'],
                                 cwd=root / 'source/MICE', capture_output=True, text=True, check=True)
        summary = pd.read_csv(root / 'results_heldout3_seed2/summary_K2.csv')
        assert len(summary) == 4 and summary[['mice', 'fifo', 'ddm', 'winens']].notna().all().all()
        text = checked.stdout
        # Existing seed summaries are read only; replication units are backbone seeds, not data sources.
        rows = []
        for seed, path in [(0, repo / 'MICE/results_heldout3'),
                           (1, repo / 'MICE/results_heldout3_seed1'), (2, root / 'results_heldout3_seed2')]:
            for stream in summary.stream:
                with (path / f'{stream}__micev1000_500.pkl').open('rb') as handle:
                    cache = pickle.load(handle)
                mice = np.mean(list(reweight.simulate2(cache, outer='brier', scale=.5, temper=True).values()))
                with np.load(path / f'{stream}__fifo1000.npz') as z:
                    fifo = np.nanmean(z['acc'])
                rows.append(dict(seed=seed, stream=stream, mice=100*mice, fifo=100*fifo, delta=100*(mice-fifo)))
        seeds = pd.DataFrame(rows)
        text += '\nThree backbone seeds (same fixed data, not independent data replicates):\n'
        text += seeds.groupby('stream').delta.agg(['mean', 'min', 'max']).to_string() + '\n'
        outputs = {'summary_K2.csv': summary, 'seed_comparison.csv': seeds}
    else:
        project = 'MiceDuo'
        from sklearn.metrics import f1_score, roc_auc_score
        seeds_to_report = [0] if args.stage == 'duo_dev' else [0, 1, 2]
        refs = np.load(repo / 'MiceDuo/results/mice_reference.npz')
        streams = ['elec2', 'h2_airlines', 'h2_phishing', 'h2_poker', 'h2_rialto', 'h2_spam', 'h2_weather']
        rows = []
        for seed in seeds_to_report:
            for stream in streams:
                if seed == 0:
                    ref = refs[stream]
                else:
                    with (root / f'duo_mice_s{seed}/{stream}__micev1000_500.pkl').open('rb') as handle:
                        cache = pickle.load(handle)
                    acc = reweight.simulate2(cache, outer='brier', scale=.5, temper=True)
                    ref = np.full(len(cache['y']) // 100, np.nan)
                    for t, value in acc.items(): ref[t] = value
                for anchor in (1, 3, 5):
                    path = (repo / f'MiceDuo/results/duo/{stream}.npz' if seed == 0 and anchor == 1
                            else root / f'duo/s{seed}_a{anchor}/{stream}.npz')
                    with np.load(path) as z:
                        yy = z['y']; T = len(yy); y = yy[1:].reshape(-1)
                        for method in ('fifo', 'sel', 'duo', 'safe'):
                            if f'P_{method}' not in z: continue
                            p = z[f'P_{method}'][1:].reshape(len(y), -1).astype(float)
                            p /= np.maximum(p.sum(1, keepdims=True), 1e-12)
                            pred = p.argmax(1); correct = pred == y
                            confidence = p.max(1); bins = np.minimum((confidence*15).astype(int), 14)
                            ece = sum(abs(correct[bins == b].mean() - confidence[bins == b].mean()) * (bins == b).mean()
                                      for b in range(15) if (bins == b).any())
                            labels = np.unique(y)
                            auc = np.nan
                            if len(labels) == 2:
                                auc = roc_auc_score(y == labels[1], p[:, labels[1]])
                            elif len(labels) > 2:
                                pp = p[:, labels]; pp /= np.maximum(pp.sum(1, keepdims=True), 1e-12)
                                auc = roc_auc_score(y, pp, labels=labels, multi_class='ovr')
                            rows.append(dict(seed=seed, stream=stream, anchor=anchor, method=method,
                                             acc=100*correct.mean(), macro_f1=100*f1_score(y, pred, average='macro', zero_division=0),
                                             auc=100*auc, ece=100*ece,
                                             logloss=-np.log(np.clip(p[np.arange(len(y)), y], 1e-6, 1)).mean(),
                                             mice=100*np.nanmean(ref[1:T])))
        frame = pd.DataFrame(rows)
        text = 'DEVELOPMENT ONLY: all pre-specified variants reported; the 22 held-out streams remain untouched.\n'
        text += frame.groupby(['seed', 'anchor', 'method'])[['acc', 'macro_f1', 'auc', 'ece', 'logloss']].mean().round(4).to_string() + '\n'
        verdicts = []
        for (seed, anchor), sub in frame.groupby(['seed', 'anchor']):
            wide = sub.pivot(index='stream', columns='method', values='acc')
            mice = sub.drop_duplicates('stream').set_index('stream').mice
            for method in ('duo', 'safe'):
                if method not in wide: continue
                d = wide[method] - mice
                delta = wide[method] - wide.fifo
                verdicts.append(dict(seed=int(seed), anchor=int(anchor), method=method,
                    delta_mice=float(d.mean()), wins_mice=int((d > 0).sum()), worst_fifo=float(delta.min()),
                    go=bool(d.mean() >= .5 and (d > 0).sum() >= 5 and delta.min() >= -.3)))
        text += '\nADVANCEMENT RULE: mean >= MICE +0.50 points, >=5/7 wins over MICE, every stream >= FIFO -0.30 points.\n'
        text += pd.DataFrame(verdicts).to_string(index=False) + '\n'
        text += 'Seed 0 is exploratory. Independent backbone seeds check stability on these same development data.\n'
        if args.stage == 'duo_replicates':
            stable = []
            for anchor in (3, 5):
                for method in ('duo', 'safe'):
                    selected = [v for v in verdicts if v['anchor'] == anchor and v['method'] == method]
                    if len(selected) == 3 and all(v['go'] for v in selected): stable.append((anchor, method))
            text += f'Variants meeting all criteria on every seed: {stable}. No held-out evaluation was launched.\n'
        outputs = {f'{args.stage}_metrics.csv': frame, f'{args.stage}_verdicts.csv': pd.DataFrame(verdicts)}
    destination = repo / project / 'results/night_20261007'
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items(): frame.to_csv(destination / name, index=False)
    (destination / f'{args.stage}_report.txt').write_text(text)
    marker = f'<!-- stage:{args.stage}:complete -->'
    log = repo / project / 'logs/OVERNIGHT_20261007.md'
    if marker not in log.read_text():
        with log.open('a') as handle:
            handle.write(f'\n## {datetime.now().astimezone().isoformat(timespec="seconds")} — {args.stage} 完成\n\n')
            handle.write('全部任务完成后自动核验；原始数据与旧结果保持只读。以下含全部判定，包括不成立项。\n\n```text\n')
            handle.write(text + '```\n' + marker + '\n')
    (root / 'reports' / f'{args.stage}.done').write_text(text)
    print(text)


if __name__ == '__main__': main()
