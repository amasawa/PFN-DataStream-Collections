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
