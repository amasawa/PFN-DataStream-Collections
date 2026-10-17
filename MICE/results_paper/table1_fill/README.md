# Table 1 fill (experiments/mice_table1_fill_20261018/PLAN.md, registered 6f48db0 before any run)

All values here are descriptive table entries; no registered hypothesis is re-decided. Fractions in streams_long.csv,
percent (x100) in summary.csv. set: real (29), grid (24), generator (30), confirm (9 primary segments of the
confirmation of detected segmentation). Read-out: experiments/mice_table1_fill_20261018/export_table1_fill.py.

## Status (updated after each item)
- Item 3, cache replays on the confirmation set: **done** (2026-10-18 10:21). mice10 and fast are replayed from the
  fixed-segmentation cache (micev1000_500), the same definitions as the other sets (MICE/code/compute_metrics.py);
  fast_cp is the fast rule on the detected-segmentation cache, as the request asked. Confirm means (%): mice10 98.61,
  fast 98.50, fast_cp 98.49. The confirm rows of the other methods are those of MICE/results_paper/confirm_detected
  (accuracy from its acc.csv, which decided the hypotheses), plus mice_cp_nopool.
- Item 4, LTM on the grid from the raw runs: **done**. Accuracy from MICE/results_probs/grid_*__ltm1000_75.npz (the
  run's own per-batch accuracy, as every other method), probability metrics from its __probs.npz. F1, AUC, ECE, Brier,
  log-loss equal the previous values (max difference 2e-16). Accuracy: the previous value was the arg max of the
  stored float32 probabilities; it differs from the run's own accuracy on 5 of 24 streams by 0.006-0.045 points
  (ties between classes; checks.csv), grid mean 62.19 -> 62.20 (the paper's 62.2 unchanged).
- Item 2, mice_cp on the 30 generator streams (GPU): pending (waiting for a free GPU, then about 1.5 hours).
- Item 1, trained learners with probabilities (CPU): pending (about 20-30 CPU hours, 6 in parallel).

## Cells that cannot be filled
- MOOE (both configurations): ECE, Brier and log-loss. MOOE minimises a squared loss on linear outputs and gives no
  probability; its scores give AUC (rank-based); accuracy and F1 from its labels.
- oracle is not part of the request (it stays as before: accuracy only).

Files: streams_long.csv, summary.csv (per set and method: means, n_* streams per metric, worst_vs_fifo on real),
coverage.csv (every missing (set, method, metric) with a reason), checks.csv (reproduction checks).
