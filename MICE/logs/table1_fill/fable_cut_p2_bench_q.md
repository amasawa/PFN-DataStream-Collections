You are the senior methodology adviser for the clean rerun of the MICE paper (a streaming tabular-foundation-model
paper). Read-only. Answer two bounded questions. Repository: current directory. Files you may read if needed:
experiments/clean_rerun_mice_h800/{ACTIVATION_20261019.md,PLAN.md,REGISTRATION_P2_20261020.md,AMENDMENT_20261020b.md,
AMENDMENT_20261020c.md,AMENDMENT_20261020d.md}, experiments/mice_tkde_control/analyse_bench.py, MICE/code/make_cost_tables.py.
Do not explore further.

## Context
- Why the rerun: the local RTX 5000 Ada (WSL2) had a GPU fault that can silently corrupt GPU-computed outputs. The
  user decided to rerun all of MICE on a cluster (8 A800, 7 cores per GPU, 500 cores per account, 7-day jobs).
- GPU work left after the user's cuts (TOT removed, dtmoe at one drift threshold, P3 only TabPFN-3.5 + TabDPT, CURE
  not run): about 760-960 GPU process-hours, about 1.5-2 days of computation on 8 A800; calendar 3-4+ days because of
  the select/extend/test round trips (dtmoe stage 2 and the four CPU baselines' stage 2 = P2b).
- The user asked "what else is unnecessary to run". I proposed two candidates. The user asked you to evaluate them.

## Candidate 1: do not rerun P2 (CPU-computed results) on the cluster
Facts:
- P2 = 2358 CPU-only tasks, about 125 CPU-hours of original wall time (river learners, trained learners incl. MOOE
  grid, trained-probability runs, confirmation arf/srp, and ts_dev = 720-task development grid of the four CPU Table 1
  baselines fsnet, onenet, adaptz, shifts). None of these ever touched the faulty GPU.
- It was moved to the cluster by user decision 5 of ACTIVATION ("CPU 的也搬到集群重跑"); the alternative offered was
  "CPU results stay local". Dropping P2 reverses that user decision.
- ACTIVATION item 4: no local extension, selection (--final) or test score of the four CPU baselines may be read
  before the P2 selection is committed from cluster outputs. Nothing has been read.
- Local status: the four baselines' local extension grid (450 tasks) finished 2026-10-20 01:54. Four of its processes
  were SIGSTOPped/SIGCONTed on 10-19 (deviation 1 of amendment e): their per-batch wall-time arrays are invalid; their
  predictions are not affected. Local tests (4 methods x 92 test streams) have not run.
- Local evidence: 7 P2 tasks, one per pipeline, were run twice in fresh processes locally: bit-identical.
- Environment caveat: the local stream venv was reinstalled on 2026-10-07 after the 10-04/05 runs, so the original
  CPU outputs of results_river/heldout/trained(_dev)/heldout2 were made with a venv whose versions are not recorded
  (river 0.26.1 is recorded).
- ACTIVATION item 3: timing and peak memory of every Table 1 method are measured on the cluster (CPU methods on one
  cluster CPU node type).
- Cluster cost of P2: CPU cores only; it runs alongside P1 on the ~444 cores not attached to GPUs, so it costs almost
  no calendar time by itself. P2b (selection/extension/tests of the four baselines) needs a round trip, but dtmoe's
  stage 2 needs one at the same time anyway.
- If dropped: the four baselines' selection, extension (already done) and tests are finished locally; the paper
  states CPU results are from the local machine; CPU timings stay local (Intel desktop CPU).

## Candidate 2: do not rerun the 5 benchmark tasks; keep the local benchmark measurements
Facts:
- 5 exclusive tasks, one attempt each (a failed/killed benchmark is given up, no retry):
  mice-tkde-bench-20261009-h800 (bench_resources.py: 8 policies x 3 streams x 3 reps, 301 batches; time, peak GPU
  memory, RSS, TFM calls, cached predictions); mice-r13-bench-h800 a1/a2 (bench_pools.py: pool-capacity timing; a1
  times kmax 2/4/12, from which k* is derived; a2 runs full grid streams at frozen k*, checks budget compliance);
  mice-r14b-bench-h800 a1/a2 (bench_cp.py, same for detected-segment variants).
- Local durations on the RTX 5000 Ada: r13 a1 5.6 h (3 runs not ok), r13 a2 1.5 h, r14b a1 5.2 h, r14b a2 2.0 h,
  tkde bench 4.4 h; total about 19 exclusive GPU-hours (5 GPUs in parallel: about 6 h wall).
- k* and M* of the original roots are frozen inputs; PLAN.md says the A800 benchmarks are measurements only and
  "claims of cost matching are re-evaluated on the H800 [A800] numbers, not carried over".
- IMPORTANT: the benchmarks are not timing-only. analyse_bench.py "accuracy" stage writes bench_accuracy_runs.csv
  from the benchmark runs' predictions, and make_cost_tables.py uses that accuracy in tab_cost_rows.tex. Those
  predictions were computed on the faulty GPU. bench_pools/bench_cp also save predictions (.npz) per run.
- A silent GPU fault corrupts values, not wall time; but the local timings were measured on the machine that had the
  fault (crash retries happened in r13 a1: 3 runs not ok).
- If dropped: cost tables say "measured on an RTX 5000 Ada"; the accuracy column of tab_cost_rows would need another
  source or would stay on the faulty GPU.

## Questions
Q1. Should P2 stay on the cluster (as registered) or be dropped in favour of local CPU outputs?
Q2. Should the 5 benchmarks stay on the cluster or be dropped in favour of local measurements?
For each, consider: integrity (what the fault can and cannot touch), consistency of the paper (hardware of reported
numbers), protocol (reversing a user decision; amendment before any score is read), and real savings (GPU-hours,
calendar time, coordination). The user's goal is to cut what is unnecessary, not to cut for its own sake.

## Output (no essays; at most ~400 words)
Decision (Q1, Q2) / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence /
Requires user approval.
