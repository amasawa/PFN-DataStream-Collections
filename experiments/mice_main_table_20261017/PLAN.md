# MICE main table (Table 1): fill the grid columns (registered when committed, before any run)

Purpose: the main table reports every strategy on the same 24 grid streams (grid10 = seeds 10, 11; grid20 = seeds
20, 21). Two combinations are missing; this run fills them with the existing, unchanged code. Descriptive table
entries, no decision criterion; nothing already reported is rerun or replaced.

1. Trained learners on grid20 (12 streams): arf, srp, hat, levbag, adwinbag (MICE/code/run_river.py) and nse,
   mooe_rff2000_100_2_0.01, mooe_rff4000_100_2_0.01 (MICE/code/run_trained.py), the configurations already reported
   on grid10 and the real streams, B = 100. CPU only. Output ~/pfn-runs/mice-main-trained-grid20/.
2. MICE with detected segmentation (micecp1000_500, round 14 code, experiments/mice_r14/run_task.py and worker.sh)
   on grid10 (12 streams), TabPFN v2, backbone seed 0, the same settings as its grid20 and real-stream runs. GPU.
   Root ~/pfn-runs/mice-main-cp-grid10/ (data = copies of MICE/data/grid_*_s1[01].npz). Started by
   wait_gpu.sh only when the GPU is free (memory used < 12 GB, utilisation < 30 %) and RAM available > 8 GB, 2 workers.

Read-out: MICE/code/export_main_table.py (metrics of mice_cp by replay from its expert cache with the frozen rule
reweight.simulate2(outer = brier, scale = 0.5, temper = True)); outputs MICE/results_paper/main_table/.
Fixed facts: the grid10 streams were already used for the other strategies of Table 1; mice_cp on them is a new
evaluation of the final method, reported in full whatever it shows.

Reproduction check: tasks_cp.txt also reruns grid_c5_b500_s20 (grid20, already in ~/pfn-runs/mice-r14-exist); the new
grid10 results are used only if the replayed accuracy of this rerun matches the existing run (MICE/code/run.py is
unchanged since 2026-10-15 15:14, before the round-14 runs). Differences are reported, not hidden.
