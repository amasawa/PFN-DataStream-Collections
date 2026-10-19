# Sonnet 核对阶段 2 登记与 gate (a) 修订

**(a) Registration vs. generator / select_frozen**
- The registration lists "dtmoe and tot routing" among the self-test fixtures. The self-test checks only dtmoe routing (shared GPU, deterministic env, `dev_h800`) and fsnet routing (CPU). The tot cases only count tasks, so tot routing is never checked.
- The registration says tests use "83 streams on MICE/data and 9 on the confirmation data". `make_test` hard-codes 92 and checks only the total. A wrong split, such as 82+10, passes the count check. The self-test checks the 9 only because its fixture happens to have 9.
- The self-test calls `np.load` on real stream files under `MICE/data` and `~/pfn-runs/.../data` (via `CONF`). The registration says the fixtures are hand-written only, and the test fails on any machine without that copy.

**(b) Generator bugs**
- None that produce a wrong list. I checked these and they are consistent:
  - tag format against `run_ts.py` (`:g` on lr and mech, `_m` suffix);
  - ext counts, including the corner;
  - the `select_frozen` regex against `1e-05` and `0.1`;
  - output directories (`dev_cluster`, `dev_h800`, `test_cluster`, `test_h800`).
- One risk is not a bug: the `P`, `pred` and `acc` shapes in the schema are copied by assumption and were not checked against `run_ts.py`.

**(c) Choices left after results are seen**
- "A given-up task stops the selection … until its disposition is registered." The disposition is chosen after the failure is known, and no rule is fixed now.
- "If its projected cost exceeds 3000 CPU-hours or 300 H800-hours, it goes to the user." What happens next is open, so the outcome of seeing the cost is open. The same applies to dtmoe's "user's decision" after its probe cap.
- "If the generator changes after a list has been generated, that is a new registration." This leaves open what counts as a change and who decides.

**(d) Contradictions with amendment c**
- Item 4 says tests are "one run per test stream (92), then the grid and generator streams". The registration and generator cover the 92 streams only. The grid and generator streams are neither included nor explicitly dropped.
- Items 1–2 and 5 fix at most 12 CPU processes at once. The registration states no process limit for stage 2.

**(e) P6 gate (a) amendment vs. `tot_gate_a.sh`**
- The unamended body of the registration still contradicts the script. It says CPU, `CUDA_VISIBLE_DEVICES` empty, "main.py sets use_gpu False", torch "CPU wheel", and a local run first. The script uses `--gpu 0` and leaves `CUDA_VISIBLE_DEVICES` unset. The "Where" bullet is marked superseded, but the Run and Environment bullets are not.
- The amendment says the code uses its own `CUBLAS_WORKSPACE_CONFIG`. The script does not export it. If `main.py` does not set it, `use_deterministic_algorithms` will fail on CUDA matmul and the verdict will be "skipped (did not finish)". Check this before the run.
- The script exits if `$OUT` exists (`test -e $OUT`). If the runner creates the parent directory of the declared output `…/mice-tot-gate-a/gate_a.json` first, the script exits with rc 1 and the verdict is "skipped".
- The task uses the placeholder `{PYTOTA}`, while stage 2 uses `{PYTOT}` and `{PYTS}`. Confirm the runner defines `{PYTOTA}` as the rebuilt cu121 venv.

## 处置
采纳：tot 路由加入自测；测试清单断言 83+9 与 29 条真实流，并按修正案 c 第 4 条排序（真实与确认在前）；放弃任务的处置现在写定（基础设施故障再试一次，方法自身报错交用户）；生成器变更以 manifest 中的 sha256 判定；集群固定核数取代本地 12 进程上限；成本超限时用户只有"照清单跑"或"不跑、报告为因成本未跑"两种选择；gate (a) 登记中被取代的 CPU 语句加标记。
不采纳：自测读真实流数据（只用于形状，选择文件夹具是手写的，措辞已改）；CUBLAS_WORKSPACE_CONFIG（main.py 第 52 行先设置，第 55 行才 use_deterministic_algorithms）；输出目录预先存在（rerun.py 不建输出目录，基准任务只一次）；PYTOTA（已加入 rerun.py VARS）。
