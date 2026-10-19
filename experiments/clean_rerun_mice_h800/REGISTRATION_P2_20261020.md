# Phase P2 of the clean MICE rerun: the CPU-computed results (registered 2026-10-20, before any P2 run)

Scope: ACTIVATION_20261019.md item 4, user decision 5 ("CPU 的也搬到集群重跑"). The rules of PLAN.md and
ACTIVATION_20261019.md apply unless stated here: acceptance, attempts, quarantine, determinism probe, provenance, and
the "CPU local" rule.

## Task list: tasks_p2.jsonl (make_tasks_p2.py; 2358 tasks, about 125 CPU-h of original wall time)
| set | tasks | origin of the command (thread setting) |
|---|---|---|
| results_river | 51 | run_river.sh: arf, srp, hat on 17 streams (none set) |
| results_heldout (CPU part) | 12 | run_river_heldout.sh (none set) |
| results_trained_dev | 435 | run_trained.sh, run_trained_ext.sh (1), run_trained_ext2.sh for rff4000 (2): MOOE development grid |
| results_trained | 126 | run_trained.sh (nse, levbag, adwinbag, mooe_rff_100_1_0.01: 1), ext2 (mooe_rff2000: 1), ext3 (mooe_rff4000: 2) |
| results_heldout2 (CPU part) | 48 | run_heldout2_cpu.sh (2) |
| results_heldout34_trained | 112 | run_heldout34_cpu.sh (2) |
| mice-main-trained-grid20 | 96 | experiments/mice_main_table_20261017/PLAN.md item 1 (not recorded; 1) |
| mice-table1-trained-probs | 736 | experiments/mice_table1_fill_20261018/run_cpu.sh (1) |
| mice-confirm-cp-20261017-cpu | 22 | arf, srp through experiments/mice_confirm_cp_20261017/run_task.py (1) |
| ts_dev | 720 | development grid of fsnet, onenet, adaptz, shifts (tune_ts.sh grid; 1), into mice-table1-newbase/dev_cluster/P |

- **dtmoe.** dtmoe is a Table 1 baseline of P1 (set dtmoe_dev of tasks.jsonl, H800 strict mode), not of P2.
- **Not tasks.** The derived replays ("mice", "mice2", "mice3", "mice3t") are recomputed by the analysis scripts.
  Outputs of GPU methods are in P1.
- **Development copies.** In results_trained, the development-stream outputs of the frozen MOOE configurations were
  copies of results_trained_dev files. Here they are separate tasks that run the same command into results_trained,
  with the thread setting of the development run.
- **Selection rule.** Two cases:
  - **Completed selections stay inputs.** A selection whose registered procedure was completed and frozen before
    ACTIVATION_20261019 stays an input. This covers MOOE: pre-registration E and its three addenda froze
    mooe_rff_100_1_0.01, then mooe_rff2000/4000_100_2_0.01, all chosen on the original CPU outputs of 2026-10-04/05,
    which the GPU fault never touched.
  - **Incomplete selections are completed on cluster outputs.** A selection whose procedure was incomplete at
    activation is finished on the cluster. This covers the four CPU baselines: their extension was unfinished and
    there was no final freeze.

  The MOOE development grid is recomputed for the numbers it reports. select_mooe.py may be run only to regenerate
  grid.csv, and its printed name is not used. If the recomputed grid ranks another configuration first, this is
  reported in the rerun appendix and not acted on. The paper states both facts: MOOE was selected on the original
  local development runs, the four baselines on cluster development runs.
- **Thread settings** are those of the original scripts, not the OMP_NUM_THREADS = 4 of PLAN.md, which describes the
  GPU scripts.
  - Tasks with no setting run with the variables unset, so BLAS uses the cores of the worker's Slurm allocation. Each
    CPU worker is allocated a fixed core count, recorded with the node type.
  - rff4000 in ext2 set OMP and OPENBLAS to 2, with MKL inherited at 1; the task sets all three to 2.
  - For grid20 the setting was not recorded (EXPERIMENT_LOG 2026-10-17 22:12), so 1 thread is used: the grid20 run
    reproduced the grid_c5_b500_s10 outputs batch for batch, and those were made with 1 thread (seven learners) and
    2 threads (rff4000).
  - Recorded versus assumed. Only the variables written in the original scripts are recorded. The following are
    assumptions, labelled as such in the rerun appendix: the environment of grid20 (threads, PYTHONWARNINGS); the
    launch environment of the confirmation arf / srp runs; and the shell environment of run_river.sh and
    run_river_heldout.sh, which set no thread variable.

## CPU baselines of Table 1 (fsnet, onenet, adaptz, shifts)
- **P2.** P2 runs the registered development grid only (720 tasks, the grid of PLAN_BASELINES.md / tune_ts.sh).
- **P2b.** Selection, the one-time full extension of every boundary axis, re-selection, freezing and the tests follow
  amendment c items 1-4, applied to the cluster grid. The extension depends on the selection, so P2b (extension
  tasks, then test tasks) is registered from the committed cluster selection before it runs.
- **When P2b selection may run.** Only when `rerun.py status --tasks tasks_p2.jsonl` shows 720 ts_dev tasks done and 0
  given up. A given-up task stops the selection of its method until its disposition is registered.
- **Local outputs are not inputs.** No local selection, extension or test output enters P2/P2b
  (ACTIVATION_20261019.md item 4).

## Environments (env_lock/)
- `stream.txt`: the river / trained-learner venv (Python 3.12.15; river 0.26.1, numpy 2.5.3, scikit-learn 1.9.1).
- `tsbase.txt`: the CPU-baseline venv (Python 3.12.15; torch 2.14.1+cpu).
- Both are frozen from the current local venvs. The stream venv was created on 2026-10-04 with river 0.26.1
  (EXPERIMENT_LOG); its other versions then were not recorded.
- Every dist-info of the current stream venv dates from 2026-10-07 22:29 (logged 2026-10-20), so the venv was
  reinstalled or copied without timestamps after the runs of 2026-10-04/05 (results_river, results_heldout, results_trained_dev,
  results_trained, results_heldout2) and before the later CPU runs. The tsbase venv dates from 2026-10-18 11:11-11:58,
  before its grid.
- Differences to the originals are reported, not corrected (PLAN.md "What changes").

## Runner (rerun.py)
- `--tasks tasks_p2.jsonl` selects this list.
- Every task has gpu = "cpu" and CUDA_VISIBLE_DEVICES = "", and is taken by `worker <slot> --gpu cpu --tasks
  tasks_p2.jsonl` on CPU nodes.
- New placeholders: PYST (stream venv), PYTS (tsbase venv). A placeholder whose variable is unset stops the task with
  an error.
- Before claiming anything, a worker (and qualify) stops if a selected task uses an unset placeholder variable.
- An unknown mode, or `--tasks` without a file, is an error.
- No other change. P1 behaviour is unchanged: tasks.jsonl is the default list, and its sha256 is unchanged.

## Inputs
- The P1 bundle covers MICE/data, the confirmation data and the run roots.
- New in P2: the baseline clones of ~/ext-baselines (ADAPT-Z, OneNet, ShifTS, fsnet), in a supplement bundle
  `mice_h800_bundle_p2` on the Windows desktop with per-file SHA-256. Their commits are recorded in it.

## Checks
- **Determinism probe, before production.** One task per pipeline (river, trained, MOOE, trained with probabilities,
  run_task CPU branch, run_ts), run twice in fresh processes on a cluster CPU node; the outputs must be bit-identical
  (`rerun.py qualify ... --tasks tasks_p2.jsonl`).
- **Local evidence.** Seven tasks were qualified locally (two fresh runs each) before this registration; the result is
  in MICE/logs/EXPERIMENT_LOG.md. The tasks: results_river:elec2__hat, results_trained_dev:elec2__mooe_lin_50_0.1_0.01,
  mice-main-trained-grid20:grid_c5_b500_s20__nse, mice-table1-trained-probs:h2_phishing__levbag,
  mice-confirm-cp-20261017-cpu:cc_btc_2013__arf, ts_dev:elec2__adaptz_L1_lr0.001_s1_m0.001,
  results_heldout34_trained:h3_poker_b__mooe_rff2000_100_2_0.01.
- **Duplicate development pairs.** The development-stream pairs in results_trained and results_trained_dev (same
  command, two tasks) must be byte-identical. A difference pauses the trained pipeline, as in PLAN.md check 1.
- **Timing.** Timing and peak memory of the CPU methods of Table 1 are measured on one cluster CPU node type
  (ACTIVATION item 3). The node type is recorded with the first P2 job; every P2 task runs on that type.
