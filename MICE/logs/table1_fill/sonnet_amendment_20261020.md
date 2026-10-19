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
# MiMo Flash medium 审计 rerun.py（AMENDMENT_20261020 第 3、4、9 项），09:39:40–09:49:29

## Findings

**1. P1 · Missing information — the reference may not actually be "default mode"**
- **Location:** `rerun.py:247-249`, `rerun.py:262-263`; AMENDMENT item 3.
- **Evidence:** `ref` removes exactly two variables. Whether the three dtmoe probe tasks *register* these two in their `env`, and — more importantly — whether they register any *other* strict-mode variable (e.g. `PYTHONHASHSEED` or a project flag), cannot be checked: `tasks.jsonl` is not attached to the audit package (Glob over the copy returns no `.jsonl`).
- **Why it matters:** if strictness comes only from these two vars, the cap is sound; if the tasks register a third strict-mode var, or register neither of these two, `ref` runs in the same mode as the strict probe, `ref wall ≈ strict wall`, the 10× timeout never binds, and the item-3 cap check on `dtmoe_dev` cannot fail — a toothless control right before an unfrozen set starts.
- **Correction:** attach the dtmoe lines of `tasks.jsonl` (or the full file) for re-review; additionally confirm on the MICE side (code reading `TS_DETERMINISTIC`, not attached) that no other variable forces determinism.

**2. P2 · Confirmed — `--exclude-sets` / `--sets` names are unvalidated, so a typo fails open**
- **Location:** `rerun.py:176` (`skip = lambda t: … or t["set"] in exclude`), `rerun.py:327-328`.
- **Evidence:** neither `exclude` nor `sets` is checked against `{t["set"] for t in TASKS}`; a misspelled excluded name matches no task, so `skip` never filters it.
- **Why it matters:** the amendment makes `--exclude-sets dtmoe_dev` the guard that keeps a paused set from starting before the cap verdict and the user's decision; on a typo the worker silently *runs* it and its outputs would be accepted as ordinary production `done` results. (The symmetric typo in `--sets` silently runs nothing and exits 0, which is only a wasted job.)
- **Correction:** before the loop, `known = {t["set"] for t in TASKS}`; `raise SystemExit(f"unknown set(s) {sorted(set(excl) - known)}")` (and likewise for `--sets`), so both directions fail loudly.

**3. P2 · Confirmed — `ref` exits 0 when the reference run fails**
- **Location:** `rerun.py:259-261`.
- **Evidence:** on `rc != 0` the code prints `"REFERENCE FAILED …"` and `return`s; `__main__` then ends normally → exit status 0, identical to a successful `ref` (which also exits 0 after writing `ref.json`).
- **Why it matters:** the printed message is the only difference; any scripted sequence (`ref` → compute 10× → `qualify --timeout`) that gates on the exit status proceeds as if the reference succeeded, and only fails later when `ref.json` is missing (loud, but at the wrong step and after the strict probe may already have been launched with a wrong limit).
- **Correction:** after the message, `raise SystemExit(1)` (keep `ref.json` absent as the marker).

**4. P2 · Confirmed — unknown-mode error message omits the new `ref` mode**
- **Location:** `rerun.py:340`.
- **Evidence:** `raise SystemExit(f"unknown mode {a[0]!r} (worker, qualify, recheck, status, release)")`, while `ref` is implemented at `rerun.py:331-332` and documented in the docstring (`rerun.py:26-29`).
- **Why it matters:** a mistyped mode prints a list from which `ref` is absent, suggesting the mode does not exist; the docstring is the only place that knows it.
- **Correction:** extend the tuple to `(worker, qualify, ref, recheck, status, release)`.

## Confirmable only by running

- **No orphaned GPU work on timeout/SIGTERM** — the group-kill structure is correct, but that the real task command lines (`bash -c`-style with GPU children) all sit in the child's new session can only be seen live: run one probe with a small `--timeout`, then check `nvidia-smi`/`ps` after the kill; repeat while sending SIGTERM (scancel) mid-run and confirm exit code 143 with the group gone.
- **numpy-missing stop behaviour (item 9)** — needs a Python without numpy: expect one traceback at the first `rc == 0` task, not per-task `GAVE UP` records; also observe the leftover state (attempt persisted with `end=None, rc=None`, claim held → `release` needed), which is code-derivable but only exercised in that run.
- **The dtmoe cap itself** — `ref` wall vs strict wall and whether 10× binds: only observable by running `ref` then `qualify --timeout` on the three probe tasks (depends on finding 1).

## 处置（09:50）
- 1 不成立：run_ts.py 第 26–30 行只以 TS_DETERMINISTIC=1 切换严格模式（并要求 CUBLAS_WORKSPACE_CONFIG）；dtmoe 任务两者都登记了，ref 去掉的正是这两个。
- 2 采纳：--sets/--exclude-sets 中未知组名报错退出（实测；同时修正了自己引入的运算符优先级错误）。
- 3 采纳：参照跑失败时 SystemExit，退出码非 0。
- 4 采纳：错误提示加入 ref。
