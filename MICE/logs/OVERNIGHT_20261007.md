# MICE overnight replication — 2026-10-07

User authorized overnight experiments, GPU utilization target >=90%, GPU memory <25 GB, findings
logged and substantive results/changes pushed. Main experiment history is in `EXPERIMENT_LOG.md`.

## Registration before execution

Complete previously paused K2 without changing its thresholds: TabPFN v2 seed 2; four third-set b
segments (airlines, covertype, insects, poker); FIFO, DDM, window ensemble, and cached MICE experts.
The final paper rule is evaluated with outer="brier", scale=0.5, temper=True.

- K1: MICE >= max(FIFO, DDM) -0.5 points on every segment.
- K2a: MICE strictly above FIFO, DDM, window ensemble on at least 3/4 segments; K2b: highest mean.
- K3: MICE >= FIFO -0.3 points on every segment.
- K4: MICE above windows-only on at least 3/4 segments.

No old results are overwritten. New raw outputs: `~/pfn-runs/night-20261007/results_heldout3_seed2/`.
The original checker is copied unchanged, and the seed 0/1/2 comparison reports means/ranges on
identical data segments, not independent data replications. Negative verdicts will also be recorded.
The controller plan and checks are in `experiments/night_20261007/README.md`.
