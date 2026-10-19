# Sonnet 核对 AMENDMENT_20261020（09:3x）

**(a) Findings not implemented, or implemented wrongly**

- **Finding 1 (m_star.json):** `make_bundle.sh`: `ls -d data* kstar.json`. The review said "`m_star.json` 一并", but only `kstar.json` is added. rerun.py's own `INPUTS = (..., "kstar", "m_star")` shows `m_star` is a frozen input. If a benchmark root has it, a2 or a later stage fails on its single attempt.
- **Finding 3 (ref reference time):** `rerun.py` ref branch: `json.dump(dict(task=task_id, rc=rc, wall_s=wall, ...))`, then `return`. A crashed reference run (rc≠0) is still written as `ref.json` and printed as "REFERENCE wall time". The 10×R cap then comes from a failure time that is far too short. The branch should refuse to write `ref.json` when rc≠0.
- **Finding 4 (paused sets):** HANDOFF step 4 only excludes `dtmoe_dev` (plus NOT QUALIFIED sets). The shared production workers still claim `mice_oracle_r11`, `results_delay_dev` and `drtabpfn` in file order. HANDOFF says these run "in their own jobs … (use `--sets`)", but the production command doesn't exclude them. They can be claimed in a 24 h shared job and then killed.
- **Finding 5 (where results land):**
  - The `~/h800/` layout exists only in AMENDMENT item 5.
  - HANDOFF step 5 and PLAN.md "Benchmarks" were not changed; the diff doesn't touch PLAN.md at all.
  - The review asked for it to be written into both.
- **Finding 7 (time-limit kills):**
  - Nothing in `rerun.py` implements "a2 … not counted". Quote: "A benchmark is never rerun without that commit."
  - Nothing in the diff stops a benchmark that `release` has returned to the queue from being claimed again.
  - The only attempt limit, "benchmark only 1 attempt (rerun.py:181)", is unchanged. After `release` the benchmark may be GAVE UP at once, or run again with no commit.
  - The old HANDOFF line, "after a job ends with tasks left: `release`, then resubmit", is still there and contradicts the new rule.
- **Finding 2 (cache check):** The existence check is only in step 1. The review also asked for one before the benchmarks run.

**(b) Bugs the diff introduces**

- **Orphaned child processes:** `run_once`: `subprocess.Popen(..., start_new_session=True)`. This applies to every production task, not only to the timeout case.
  - Ctrl-C or SIGTERM to the worker no longer reaches the task.
  - Interrupting a worker can leave GPU processes running.
  - `p.wait(timeout=...)` only handles `TimeoutExpired`. Any other exception, such as `KeyboardInterrupt`, leaves the child alive.
- **Stale sandbox after TOO SLOW:** `qualify` returns on timeout but leaves `<d>/a`. A re-run in the same `<d>` fails on `os.makedirs(runs, exist_ok=False)`.
- **Import moved before the existence check:** In `valid()`, `import numpy as np, pickle, csv` now runs before `os.path.exists(o)`. The claim that this stops the runner holds only if the callers of `valid()` don't catch `Exception`. The diff doesn't show them.

**(c) Amendment statements the diff contradicts**

- **Item 3, `ref` "writes only its wall time to <dir>/ref.json":** The code writes `task, rc, wall_s, host, gpu, removed`.
- **Item 7, "Tasks without a time estimate run in their own jobs … drtabpfn and dtmoe_dev":** The HANDOFF production command doesn't enforce this (see the finding 4 point above).
- **Item 5, "Nothing goes into ~/pfn-runs …":** HANDOFF step 5 and PLAN.md don't carry this rule. The amendment alone holds it.

## 处置
采纳：ref 失败不写 ref.json；生产排除无估计的组；HANDOFF 第 5 步指向 ~/h800 布局；release 说明；基准前缓存检查；worker 中断杀进程组；ref.json 措辞。
不采纳：m_star.json（bench_resources.py 不读）；超时后沙盒残留（qualify 本来就要新目录）；release 后的基准（attempts 已满 1 次，下个 worker 直接记为放弃，不会重跑）；valid() 的 import（调用者不捕获异常，实测会报错）。

## 复查
Sonnet 复查新发现：SIGTERM 不触发异常，任务进程会残留。成立，已加 SIGTERM 处理（转为 SystemExit），实测无残留进程。
