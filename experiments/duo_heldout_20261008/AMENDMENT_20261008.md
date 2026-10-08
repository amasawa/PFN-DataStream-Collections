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
