# Operational amendment to the frozen held-out run, 2026-10-08

Written at 2026-10-08T15:46:01+11:00, before any held-out score has been inspected (no partial evaluation was run).

**What changes:** only the number of concurrent workers, from 1 to 4. The run is resumed through
`finish_concurrent.py` (SHA-256 `4d3154e62aca334d682bf60b371fbf2d8a94808f9ad56104164898057581aceb`) instead of the frozen `controller/finish.py`. The
snapshot under `~/pfn-runs/duo-heldout-20261008` is not modified; its source and data hashes are verified
before the run and again before evaluation. All 132 tasks, seeds, data prefixes, the method (MICE+sel1), the
four decision criteria and the frozen evaluator are unchanged. No task is dropped and no result is selected across
retries.

**Why:** the user's standing instruction is GPU utilisation >= 90% with memory < 90%. With one worker the run
was projected at about 18 h with about 40% utilisation. Predictions are bit-identical between 1 and 4–6
concurrent processes (experiments/night_20261007/STABILITY_MANUAL.md); intermittent CUDA failures resume from
checkpoints without changing results (MiceDuo/logs/DUO_SAFE_20261008.md). Codex, which designed the frozen run,
was consulted and agreed conditionally; its safeguards are adopted below.

**Command:** `tmux new -s duo-heldout-20261008 "python finish_concurrent.py RUN_ROOT REPO"` with the same
venv and single-thread BLAS environment; the supervisor runs with
`--hours 24 --max-workers 4 --breaker 6 --no-publish`.

**Safeguards:** the old supervisor and all workers are drained before the restart; queue state, failure history and
logs are kept; the wrapper refuses to start if a STOP file exists or if the last ten minutes already contain six
failures; the breaker is not reset automatically.

**Cost reporting:** call counts remain valid. Timings after the switch are elapsed times under contention from up to
four processes, so per-component time ratios cannot be read as isolated overhead or deployed latency. They are
reported descriptively with the concurrency phases, total elapsed and GPU time, throughput, retries and utilisation.
`cost_notes.json` written by the frozen evaluator states `concurrency=1`; that statement is superseded by this
amendment. A latency comparison, if needed, requires a separately declared single-worker benchmark.

State at the switch: {"time":"2026-10-08T15:45:58.548424+11:00","utilization":33,"gpu_mib":1493,"ram_available_mib":28754,"target":1,"running":{"mice_s0_h3_airlines_c":255026},"done":12,"total":132,"blocked":0}

## Amendment 2 — back to one worker (2026-10-08T15:56:23+11:00)

Written before any held-out score was inspected.

- **Incident:** after the switch at 15:46:58, six worker failures in five minutes tripped the breaker at 15:51:58
  (STOP written by the supervisor). All six were on airlines streams (h3_airlines_c, h4_airlines_d; 7 features,
  2 classes) while several airlines tasks ran together: unspecified launch failure, illegal memory access and one
  CUBLAS_STATUS_EXECUTION_FAILED; all but one advanced their checkpoint. With one worker, 12 tasks had run for
  1.5 h without a failure.
- **Hypothesis, not established:** the failure hazard under concurrency grows with the kernel-launch rate, which is
  higher on low-dimensional streams (today's 10-feature synthetic streams also failed more often than last
  night's 33–54-feature streams).
- **Decision (recommended by Codex, accepted):** run the remaining 120 tasks with **one worker**, using the
  original frozen `controller/finish.py` (`--max-workers 1`), which also restores the frozen stop-on-first-failure
  rule. This is an explicit stability exception to the user's >= 90% utilisation goal: expected about 35–40%
  utilisation for about 17 h. No automatic escalation.
- **Breaker reset:** deliberate and manual after this review. The STOP file is renamed `STOP.breaker_20261008_1551`;
  failure history, logs, queue state and checkpoints are kept; all workers had exited.
- **Cost reporting:** three concurrency phases (1 worker until 15:46:29, 4 workers 15:46:58–15:51:58,
  1 worker from this restart), reported as in amendment 1.

State before restart: {"time":"2026-10-08T15:51:58.183363+11:00","utilization":15,"gpu_mib":1493,"ram_available_mib":28599,"target":1,"running":{},"done":12,"total":132,"blocked":0,"state":"stopped","stopped_at":"2026-10-08T15:51:59.051936+11:00","reason":"Circuitbreaker:6workerfailure(s)withintenminutes;investigatebeforeresuming."}

## Amendment 3 — two workers at the user's request (2026-10-08T19:08:14+11:00)

Written before any held-out score was inspected.

- **Decision:** the user chose two workers ("2 worker 吧") after being told the trade-off: about 8–9 h remaining
  with one worker at 30–50% GPU utilisation, versus a faster run with an unvalidated concurrency level (Amendment 2
  recorded that two workers had not been shown to be stable).
- **Execution:** the single-worker run is drained gracefully; the run resumes through `finish_concurrent.py` (now
  taking workers and breaker as arguments, SHA-256 `430a493ec8a91e1b8d1a391415c83f6e5ad34d8885b0e8dfe81624ca4b4546ed`)
  with **2 workers** and a breaker of **3 failures in ten minutes**. Snapshot, tasks, order, data, method, criteria and
  the frozen evaluator are unchanged; hashes are verified before the run and before evaluation.
- **Fallback, decided now:** if this breaker trips, the run returns to one worker with the original frozen
  `controller/finish.py` (stop on first failure), as in Amendment 2; no escalation beyond two workers.
- **Cost reporting:** a fourth concurrency phase (2 workers from this restart), reported as in amendment 1.

State before switch: {"time":"2026-10-08T19:08:11.946327+11:00","utilization":47,"gpu_mib":2343,"ram_available_mib":28715,"target":1,"running":{"duo_s0_h3_insects_b":311536},"done":41,"total":132,"blocked":0}

## Amendment 4 — resource-scaled concurrency, no failure-rate breaker (2026-10-08T20:58:58+11:00)

Written before any held-out score was inspected. User instruction: adopt the strategy proven on another run of this
machine (10 workers, 99% utilisation): scale workers by resources, not by failure counts.

- **Why the breaker goes:** worker failures do not change results (each retry is a fresh process resuming from an
  atomically written checkpoint; predictions are bit-identical across concurrency levels). Of the six failures in the
  4-worker phase, five advanced their checkpoints. A failure-rate breaker therefore protects procedure, not results,
  at the cost of an under-used GPU.
- **New rules** (`finish_resource.py`, SHA-256 `92debe0278d151e62f280020eff27e86fd21fe1b944238fe8781e91ac1923a1a`;
  repository supervisor `experiments/night_20261007/supervisor.py`, SHA-256
  `0ca8e3e7d2bc2f465076364b83d170932188ec7c84d8c42aab7f3a11bbcda56f`, `--resource-mode`): start with 4 workers,
  add workers while mean utilisation < 94% up to 8; no failure-rate breaker and no error cooldown; every failed task
  is retried in a new process after a back-off, and a task is blocked only after 4 failures without checkpoint
  progress (or 20 in total); memory guards unchanged (pause at 22 000 MiB, emergency 23 200 MiB, RAM < 4 GB);
  **stop only** if no worker writes progress for 15 minutes or nvidia-smi is unresponsive for 5 minutes.
- **Unchanged:** the frozen worker (`RUN_ROOT/controller/worker.py`, launched via `--worker-dir`), tasks, order,
  data, method, criteria and the frozen evaluator; hashes verified before the run and before evaluation;
  `OMP_NUM_THREADS=1` (more BLAS threads could change floating-point summation order relative to the 66 tasks
  already completed).
- **Check after completion:** rerun 2–3 completed tasks alone and confirm bit-identical predictions; report it.
- **Smoke test:** a fake worker failing three times per task completed all tasks with no breaker or cooldown.

State before switch: {"time":"2026-10-08T20:49:48.642509+11:00","utilization":16,"gpu_mib":1365,"ram_available_mib":28703,"target":2,"running":{},"done":67,"total":132,"blocked":0,"state":"stopped","stopped_at":"2026-10-08T20:49:50.265843+11:00","reason":"Circuitbreaker:3workerfailure(s)withintenminutes;investigatebeforeresuming."}

## Amendment 5 — cap three workers in resource mode (2026-10-08T21:32:29+11:00)

Written before any held-out score was inspected.

- **Observation:** under Amendment 4 the run scaled to 7–8 workers at 97–99% utilisation, but from 21:01 to now there
  were 20 worker failures (16 in the last ten minutes, mostly INSECTS tasks) and only 3 tasks completed in 30 minutes
  (70/132). Compute went into crashes, restarts and replayed batches. Throughput was 12–13 tasks/hour with one or two
  workers. The strategy that ran 10 workers without failures on another workload does not transfer to this one.
- **Decision:** keep resource mode (no failure-rate breaker, retries in new processes, stop only on a global stall or an
  unresponsive nvidia-smi) but cap at **3 workers** (start 3), between two (mostly stable) and four (failure clusters).
  `finish_resource.py` now takes the cap and start count as arguments (SHA-256 `6f38a06bf3ac7f54104174f4d7f269244c52af56fa484b95b7c5d081ebf93c29`). Everything frozen is unchanged.
- **If three workers still fail in clusters without completions,** the cap goes to two in a further amendment.

## Amendment 6 — two workers for the remaining INSECTS tasks (2026-10-09T01:07:58+11:00)

Written before any held-out score was inspected. Applies the fallback pre-stated in Amendment 5 ("if three workers
still fail in clusters without completions, the cap goes to two").

- **Observation:** 00:56–01:07, seven worker failures and no completed task (123/132; the nine remaining tasks are
  seed-2 INSECTS streams of 300 batches). One task (mice_s2_insects_incremental_balanced) resumed twice at batch 101
  without checkpoint progress; four consecutive failures without progress would block it and leave the run
  INCOMPLETE, so the frozen evaluator would not run.
- **Decision:** resource mode unchanged (no failure-rate breaker, retries in new processes), cap and start **2
  workers** via `finish_resource.py RUN_ROOT REPO 2 2`. Everything frozen is unchanged.

State before switch: {"time":"2026-10-09T01:07:57.010014+11:00","utilization":95,"gpu_mib":4023,"ram_available_mib":24975,"target":3,"running":{"mice_s2_insects_incremental_balanced":416941,"duo_s2_insects_incremental_balanced":417650,"mice_s2_insects_incremental_reoccurring_balanced":418589},"done":123,"total":132,"blocked":0}
