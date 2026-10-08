# DUO frozen real-stream confirmation

The user authorized iteration after the log review on 2026-10-08. `PLAN.md` fixes the science;
the Linux snapshot, rather than the live repository, runs the experiment.

- Run: `/home/zhwu9808/pfn-runs/duo-heldout-20261008`
- tmux: `duo-heldout-20261008`
- 132 tasks: 22 prefixes x 3 backbone seeds x MICE/DUO; one GPU worker.
- `frozen/` contains the data manifest, task manifest and source hashes copied before launch.
- Freeze SHA256: `14a2fb68b8296d2a7969f009befc2f99da1725537dce73a1c830661839cd8321`.
- `status.json`, `events.log`, `progress/`, `gpu.csv` report operational progress without revealing scores.
- A worker failure triggers STOP. No automated breaker reset or concurrency increase.
- On all tasks completing, `finish.py` runs the frozen evaluator. `reports/heldout.done` is the final
  verdict marker; `heldout_results.csv`, `heldout_sources.csv`, `heldout_source_means.csv`,
  `heldout_verdicts.csv`, `cost_notes.json` hold validated results and costs.

## Validation before launch

`test_pipeline.py` checks unchanged probabilities, exact checkpoint resume, causal selections,
selection-only cost instrumentation, missing-task rejection, and all evaluator outputs against a
132-task synthetic fixture. These fixture results are not experimental results.

## Reading progress / resuming

Read the run's `status.json` and `events.log`. Do not evaluate partial outputs. After an interruption,
inspect the reason, diagnose errors, and only then deliberately clear/rename STOP if appropriate.
Resume by invoking the **existing frozen** `controller/finish.py RUN_ROOT REPO` with the same Python
environment (`/home/zhwu9808/pfn-venvs/venv/bin/python`), single-thread BLAS environment and tmux.
`launch.sh` intentionally refuses to overwrite an existing run. Do not edit the snapshot to resume;
source integrity is checked before every invocation and before final evaluation.

Copy final CSVs into this directory and generate paper tables only after the completion marker and
validation pass. A failed scientific criterion is still a valid completed evaluation; preserve and
report it. An operationally incomplete run has no scientific verdict.

No external scheduled checks or automatic git publication were installed. The run's resource guard
and all-complete evaluation operate inside its own bounded supervisor session.
