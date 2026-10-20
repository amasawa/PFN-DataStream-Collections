# Operational amendment b of the clean MICE rerun, 2026-10-20 (committed and pushed before any cluster run)

Where this note differs from ACTIVATION_20261019, AMENDMENT_20261020, the phase registrations or HANDOFF.md, this note
holds. Items 1-2 change no computation. Item 3 changes the device of TOT's development grid and tests (user decision).
Item 4 cancels the CURE experiment (user decision).

## 1. Hardware: A800, not H800
- **What the user found.** The cluster of the user's group account has A800 GPUs (partition A800: 8 GPUs and 56 cores
  per node), not H800. The account may use at most 8 GPUs and 500 CPU cores at once, and a job runs at most 7 days.
  The user checked on the cluster that:
  - each GPU may be given at most 7 CPU cores (a hard submission limit, whatever the node layout);
  - memory is about 1.8 GB per requested core;
  - an ordinary user can start CUDA MPS in a job (tested on gpu8017).
- **Every "H800" of the registrations reads "A800".** This covers the device of P1, P3, P5, the gate and the TOT
  steps, the strict-mode probe of dtmoe, and the cost limits (300 GPU-hours). Directory and set names that contain
  "h800" (dev_h800, test_h800, *-h800 benchmark roots) keep their names: they are labels.
- **Architecture.** Every CUDA environment includes sm_80, the A800's architecture:
  - venv: torch 2.14.0+cu126;
  - drtabpfn: 2.1.2+cu121;
  - totgpu: 2.3.1+cu121;
  - venv-tot: 2.3.1+cu121;
  - venv-mitra: 2.13.0+cu126;
  - venv-limix: 2.9.1+cu126.

  The GPU check of HANDOFF step 2 tests for sm_80 instead of sm_90.
- **Determinism.** The determinism probe and the bit-identity of repeated runs are judged on the A800. The runner
  records the GPU name of every task.

## 2. Resources and throughput (no computation changes)
- **Cores.** Each GPU worker gets its 7 cores from the job. Every task keeps its registered thread variables
  (OMP_NUM_THREADS = 4 for the run.py family), even when several workers share the 7 cores.
- **CUDA MPS.** Every GPU job starts the MPS control daemon (`nvidia-cuda-mps-control -d`, with per-job
  CUDA_MPS_PIPE_DIRECTORY and CUDA_MPS_LOG_DIRECTORY) before its workers, and stops it at the end.
- **Workers per GPU: 2 or 3.**
  - The job starts with 3 workers. After 30 minutes, the tasks completed per hour are compared with those of a
    2-worker job.
  - The number with more completed tasks per hour is kept, unless the job's resident memory exceeds 80 % of its
    allocation (about 7 × 1.8 GB per GPU), in which case 2 workers are used.
  - Measured locally, a TabPFN worker uses about 1.8 GB of resident memory. The number and the measurements are
    logged.
- **Probes.** Every determinism probe (qualify; P1 step 3, P3, P4, P6) runs under the same MPS and worker
  configuration as the production that follows it.
- **CPU jobs.** CPU-only jobs (P2) use the cores left under the 500-core account limit.

## 3. TOT on the A800 (user decision 2026-10-20)
- **Why.** The TOT development grid projected on the CPU is about 2180 CPU-hours. That is above the registered limit
  of 1500 (REGISTRATION_P6_GATE_A "Cost limits"). Measured locally on one thread (s per batch):

  | stream | L16 s1 | L32 s1 | L16 s5 | L32 s5 |
  |---|---|---|---|---|
  | elec2 | 1.1 | 3.2 | 4.3 | 14.1 |
  | INSECTS | 25.4 | 57 | 112.6 | 208 |

  In the tests, one covertype task (54 features) could exceed the 7-day job limit. Fable recommended the A800
  (MICE/logs/table1_fill/fable_tot_cost_a.md).
- **User decision** (verbatim, with the options). Options:
  - "改到 A800 跑 (Recommended)";
  - "照旧在 CPU 跑";
  - "不跑 TOT".

  Answer: "改到 A800 跑 (Recommended)".
- **What changes.** The TOT development grid and the stage-2 lists of TOT run on the A800:
  - deterministic mode (TS_DEVICE = cuda, TS_DETERMINISTIC = 1, CUBLAS_WORKSPACE_CONFIG = :4096:8);
  - environment venv-tot ({PYTOTA}: torch 2.3.1+cu121, the authors' versions, as gate (a)). This replaces "the P2
    environment" of REGISTRATION_P6_GATE_A;
  - outputs in mice-table1-newbase/dev_a800 and test_a800.

  The adapter (run_ts_tot.py) is unchanged.
- **Check before the grid** (task p6_tot_check, tot_check.py; exclusive A800; no accuracy reported or kept).
  - It measures the time per batch on 8 configurations: L {16, 32} × n_steps {1, 5} × the first 400 rows of elec2 and
    of insects_abrupt_balanced.
  - It projects the GPU-hours of the 180 grid tasks.
  - It runs gate (b): λ = 0 against λ = 1e-5 on the first 1500 rows of elec2.
  - Verdict:
    - "proceed" if gate (b) holds, the projection is at most 300 GPU-hours, and the aggregate speed-up (projected
      CPU-hours from the table above / projected GPU-hours) is at least 5. The 300 GPU-hours are a limit per list
      (here the TOT grid), as for the stage-2 lists, not a total budget. The total GPU use of the rerun stays under
      HANDOFF rule 5: the user is asked before more than 24 h of 8 GPUs;
    - otherwise "not run (gate b …)" or "not run, for its cost".
  - Local dry run (RTX 5000 Ada, timing only): 192 GPU-hours, speed-up 11.3, gate (b) holds, so "proceed".
- **Order on the cluster.** Gate (a), then the check, then a qualify of one tot_dev task under the production
  configuration, then the grid. The grid runs only if gate (a) passed, the check says "proceed", and the qualify is
  bit-identical.
- **The local GPU.** Used only for that timing dry run and the adapter's functional checks: no TOT number comes from
  it.

## 4. CURE: no experiment (user decision 2026-10-20)
- **User, verbatim.** "还有一件事情你之前让我比对的一篇文章，2026年arxiv上的我觉得没有必要作实验比对，虽然他有代码但是，他没有被接受".
  - The paper is CURE (arXiv 2606.18677; code morcellinus/CURE-ICML-FMSD, a workshop submission).
  - This reverses the main-table part of ACTIVATION user decision 7 ("引用，并加为主表基线").
- **What is cancelled.** P4 does not run:
  - tasks_p4.jsonl (cure_dev, 20 tasks) and its stage 2 are cancelled;
  - run_cure.py stays in the repository, unused;
  - no CURE output exists (none was run).
- **What stays.** CURE stays cited as concurrent work; the user's message cancels only the experiment.
