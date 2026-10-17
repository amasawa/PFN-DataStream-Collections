# Amendment 2026-10-18 (committed before the runs it adds)

The user's merged request of 2026-10-18 ("MICE 表 1 补全与新增基线：实验需求（合并版）") replaces the first request.
Additions to PLAN.md; everything in PLAN.md stays.

1. **ddm and ltm probabilities on the 30 generator streams** (GPU): ddm1000 and ltm1000_75 rerun through
   MICE/code/run_probs.py with experiments/mice_confirm_cp_20261017/run_task.py and worker.sh (unchanged), tasks
   tasks_probs_gen.txt, root ~/pfn-runs/mice-table1-probs-gen (data = copies of MICE/data/<stream>.npz). One worker
   while the mice_cp generator run is on the GPU, a second after it. Reproduction check: the accuracy of each rerun
   against the existing MICE/results_test/<stream>__{ddm1000,ltm1000_75}.npz; the existing accuracy stays in the table,
   and the probability metrics are used only if the rerun's accuracy matches (difference reported otherwise).
2. **worst_vs_fifo on all four sets** (read-out only).
3. **CPU runner (operational)**: the first start (10:38) ran six MOOE-4000 processes at once (4.8 GB each on a
   150,000-row stream); stopped after 50 s, before any output, and restarted at 10:39 with two lanes (MOOE 2 in
   parallel, the others 4). No computation changed.
4. **New baselines** (Drift-Resilient TabPFN; Dynamic TMoE, ADAPT-Z, TOT, OneNet, FSNet, ShifTS adapted to
   classification): not part of this amendment. Each is checked first (title, venue, official code); the adaptations,
   the tuning grid on the five development streams and the frozen settings are registered in a separate plan before
   any test-stream run. A method that cannot be matched to its paper and code is reported and skipped, not replaced.
5. Output folder on the desktop renamed per the request: MICE_table1_full (MICE_table1_fill kept as the first copy).
