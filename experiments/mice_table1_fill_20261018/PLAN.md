# MICE Table 1: fill the remaining cells (registered when committed, before any run)

Requested by the user on 2026-10-18 ("表 1 补齐数据需求"). Every value produced here is a **descriptive** table entry:
no registered hypothesis is re-decided, nothing is tuned, the constants are those of the paper (TabPFN v2 backbone,
backbone seed 0, B = 100 rows, labels one batch late, batch 0 warm-up). Every existing number is kept; where a new run
reproduces an existing one, the new value is used only if it matches (checks below), and every difference is reported.

State before this plan (MICE/results_paper/main_table, 2026-10-17): grid20 accuracy of the trained learners and grid10
of mice_cp are already filled (experiments/mice_main_table_20261017). Missing: probabilities of the trained learners
everywhere, their accuracy on the generator streams, mice_cp on the generator streams, and the confirmation set
(MICE/results_paper/confirm_detected, 9 primary segments) for mice10, fast and the trained learners other than ARF, SRP.

## Items (in this order)
3. **Cache replays on the confirmation set** (no TFM call): on the 9 primary segments, from the expert caches of the
   confirmation run (~/pfn-runs/mice-confirm-cp-20261017/P): mice10 = reweight.simulate2(outer = brier) on the fixed
   cache (micev1000_500), fast = reweight.simulate(c, 10, 0.0) on the fixed cache — the same definitions as
   MICE/code/compute_metrics.py for the other sets — and, as the user's note asks, fast_cp = the same fast rule on the
   detected-segmentation cache (micecp1000_500). Accuracy and the probability metrics.
4. **LTM on the grid from the raw run files**: MICE/results_probs/grid_*__ltm1000_75.npz (accuracy) and
   __probs.npz (probabilities), the run_probs.py run; compared with the values currently in main_table (and the
   paper's metric row, which was generated from the same files).
2. **mice_cp on the 30 generator streams** (GPU): micecp1000_500 with experiments/mice_r14/run_task.py and worker.sh
   (MICE/code/run.py unchanged since 2026-10-15 15:14), tasks_cp_gen.txt, root ~/pfn-runs/mice-table1-cp-gen
   (data = copies of MICE/data/<stream>.npz), 2 workers, started by wait_gpu.sh only when the GPU is free (memory used
   < 12 GB, utilisation < 30 %, RAM available > 8 GB, 5 checks a minute apart). Read-out by replay with the frozen rule
   reweight.simulate2(outer = brier, scale = 0.5, temper = True), as for the other sets.
1. **Trained learners with probabilities** (CPU, stream venv): arf, srp, hat, levbag, adwinbag, nse,
   mooe_rff2000_100_2_0.01, mooe_rff4000_100_2_0.01 on the 29 real, 24 grid, 30 generator streams (streams_main.txt,
   data MICE/data) and the 9 confirmation segments (streams_confirm.txt, data of the confirmation run), with
   run_trained_probs.py (same code paths as MICE/code/run_river.py and run_trained.py; MOOE configurations = the ones
   already reported). Root ~/pfn-runs/mice-table1-trained-probs, one process per (stream, method), 6 in parallel.
   - What each learner gives: river learners predict_proba_one (label = its arg max, which is river's predict_one);
     Learn++.NSE the normalised weighted votes; MOOE has no probability (squared loss on linear outputs): its linear
     scores are stored and used only for AUC (rank-based); ECE, Brier and log-loss of MOOE stay empty, with this reason.
   - Reproduction check: smoke test on grid_c5_b500_s20 (2026-10-18): the per-batch accuracy of all eight equals the
     existing runs bit for bit. In the read-out, every new accuracy is compared with the existing one (all.csv /
     grid20 runs / confirm acc.csv for arf, srp); a stream whose accuracy differs by more than 1e-9 is reported and
     its probability metrics are not used.

## Metrics
MICE/code/compute_metrics.metrics: macro-F1, one-vs-rest AUC (macro over the classes present), ECE (15 bins, top
label), half Brier, log-loss; for the trained learners acc and F1 from their own labels. Read-out:
export_table1_fill.py → MICE/results_paper/table1_fill/ (streams_long.csv, summary.csv, coverage.csv, README.md),
copied to the desktop (MICE_table1_fill). Updated after each item.
