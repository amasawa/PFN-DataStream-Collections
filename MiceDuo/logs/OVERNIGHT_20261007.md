# MICE-DUO overnight development — 2026-10-07

User authorized overnight experiments, GPU utilization target >=90%, GPU memory <25 GB, findings
logged and substantive results/changes pushed. Main experiment history is in `EXPERIMENT_LOG.md`.

## Registration before execution

Question: does ranking history from only the latest 100 labelled rows make relevance selection
unstable? Compare anchors of 300/500 rows, always retaining the anchor, adding the best older batches
from H=100 to reach M=1000. Both ranking reference and mandatory recent data change together;
this experiment does not separate their individual contributions.

Only the seven original development streams are used: elec2, h2_airlines, h2_phishing, h2_poker,
h2_rialto, h2_spam, h2_weather. First 300 batches, B=100, labels one batch late; frozen TabPFN v2,
four estimators. The 22 held-out streams remain unused for selection.

For each candidate report selection alone, original DUO weighting, and a conservative half-Brier
mixture (scale=.5, discount=.9, tempered weights). Use seed 0 for exploratory comparison; repeat
all fixed variants, original anchor=1 and MICE references on seeds 1 and 2. No adaptive threshold search.

Advancement requires all of: mean >= MICE +0.50 points; above MICE on >=5/7 streams; every stream
>= FIFO -0.30 points. Report all candidates and all seeds, including failures. A candidate must pass
on all three seeds before recommending a separate frozen held-out test. No held-out test starts tonight.
Report accuracy, macro-F1, macro OvR AUC, ECE, log-loss. This is development evidence, not a final test.

Raw outputs/checkpoints: `~/pfn-runs/night-20261007/`. Small summary tables will be placed in
`MiceDuo/results/night_20261007/`. Full execution design: `experiments/night_20261007/README.md`.
