# P2 registration reviews (2026-10-20)

## Fable (00:09-00:12, ~1.74 USD)
You are the senior expert (read-only). Review the uncommitted registration experiments/clean_rerun_mice_h800/REGISTRATION_P2_20261020.md (phase P2: CPU results of MICE rerun on the cluster) against ACTIVATION_20261019.md, PLAN.md in the same directory and experiments/mice_table1_fill_20261018/AMENDMENT_BASELINES_20261018c.md. Generator: make_tasks_p2.py. The user's decisions are final.
Answer: Decision (register as is / with changes) / required changes (at most 5, exact replacement text) / Key risks / Confidence. <= 350 words. Focus on integrity: (a) MOOE selection kept frozen while the grid is recomputed vs re-selecting on cluster outputs (the four Table 1 CPU baselines ARE re-selected on the cluster under P2b; is the asymmetry defensible, and how must the paper state it?), (b) unrecorded thread setting for grid20, (c) env versions frozen from today's local venvs, (d) anything an executor could misread.

**Decision:** register with changes (5).

**Required changes**

1. Replace the "Frozen selections stay inputs" bullet with:
   "**Selection rule.** A selection whose registered procedure was completed and frozen before ACTIVATION_20261019 stays an input: MOOE (pre-registration E and its three addenda; FROZEN mooe_rff_100_1_0.01, then mooe_rff2000/4000_100_2_0.01, all chosen on the original CPU outputs of 2026-10-04/05, never exposed to the GPU fault). A selection whose procedure was incomplete at activation (the four CPU baselines: extension unfinished, no final freeze) is completed on cluster outputs. The MOOE development grid is recomputed for the numbers it reports; select_mooe.py may be run only to regenerate grid.csv, and its printed name is not used. If the recomputed grid ranks another configuration first, this is reported in the rerun appendix and not acted on. The paper states both facts: MOOE selected on the original local development runs, the four baselines on cluster development runs."

2. Replace the "Thread settings" bullet with:
   "**Thread settings** are those of the original scripts (not the OMP_NUM_THREADS = 4 of PLAN.md, which describes the GPU scripts). Tasks with none set run with the variables unset, so BLAS uses the cores of the worker's Slurm allocation; each CPU worker is allocated a fixed core count, recorded with the node type. rff4000 in ext2 set OMP and OPENBLAS to 2 with MKL inherited at 1; the task sets all three to 2. For grid20 the setting was not recorded (EXPERIMENT_LOG 2026-10-17 22:12); 1 thread is used, since the grid20 run reproduced grid_c5_b500_s10 outputs made with 1 thread (seven learners) and 2 threads (rff4000) batch for batch."

3. Replace "Versions at the time ... not recorded" with:
   "river 0.26.1 is recorded at the venv's creation (EXPERIMENT_LOG 2026-10-04); other versions were not. Before the first P2 run, the modification times of site-packages/*.dist-info of both local venvs are logged as evidence that they were not changed since the original runs."

4. Replace "Local evidence" with the seven task ids and the log path holding the local qualify result. Six pipelines are listed but "seven tasks" claimed; an executor cannot reconstruct the set.

5. Append to P2b: "P2b selection runs only when rerun.py status shows 720 ts_dev done and 0 given up; a given-up task stops the selection of its method until its disposition is registered. The development-stream pairs in results_trained and results_trained_dev (same command, two tasks) must be byte-identical; a difference pauses the trained pipeline as in PLAN.md check 1."

**Key risks**
- Float differences on the cluster CPU can reorder the MOOE grid; without change 1 that reads as a hidden choice.
- Unset thread variables on a shared node slow neighbours and distort any wall time read from npz.
- Env freeze is a claim without evidence until change 3.

**Confidence:** high on 1, 4, 5; medium on 2 (MKL irrelevance assumes OpenBLAS numpy, unverified).

Disposition: 5/5 accepted; item 3 corrected with verified facts (stream venv dist-info dated 2026-10-07 22:29).

## MiMo Flash medium (00:09-00:17)
esults_trained `cp` files are re-run with the dev run's thread setting, as registered; ts_dev writes to `dev_cluster/P` while taking structure from `dev/P`, exactly as registered. `os.path.exists(orig)` in `add()` means the script completed, so all tags/paths resolve to real original files.

**rerun.py diff (P1 safety)** — default list stays `tasks.jsonl`; `--tasks` only overrides; `fill()` now raises instead of `KeyError` but only when a placeholder is actually used, and no P1 task uses `{PYST}`/`{PYTS}`; the worker gpu filter is unchanged; child env is still the `KEEP` whitelist, so no ambient `OMP_NUM_THREADS` can leak into a task that doesn't register it. Stale-output skip is not a hazard: `quarantine()` moves each task's outputs before every attempt.

## Findings

**1. P1 · Suspected issue — output-directory creation was dropped with the `mkdir -p` of the original scripts**
- **Location:** `make_tasks_p2.py` sections 1–5 (commands contain no mkdir); `rerun.py run_once`; interacts with `qualify()`.
- **Evidence:** every original driver pre-creates its out dir (`mkdir -p ../results_river`, `mkdir -p $D $O`, `mkdir -p $R/P`, `mkdir -p $OUT` in run_river.sh, run_trained.sh, run_cpu.sh, tune_ts.sh, run_heldout2/34_cpu.sh). The new task commands invoke only the python driver. `run_task.py` calls `os.makedirs(out, exist_ok=True)` itself, which suggests the underlying `run_river.run` may not. On the cluster `results_river`, `results_trained_dev`, `mice-table1-newbase/dev_cluster/P` etc. are not in the P1 input bundle (data + run roots only), so they may not exist.
- **Why it matters:** if any driver lacks `makedirs`, whole sets fail 3 attempts each and are given up — the determinism probe catches this only for the 7 probed pipelines, not for e.g. grid20/heldout2/heldout34/dev_cluster.
- **Recommended correction:** confirm `makedirs` in run_river.py / run_trained.py / run_trained_probs.py / run_ts.py (see items under "needs execution"); if absent, add a mkdir step to the task cmd or pre-create the directories — creating an empty directory does not change any computation, so this is registration-compatible.

**2. P2 · Confirmed issue — `--tasks` placed before the mode makes rerun.py exit silently**
- **Location:** `rerun.py:272-285` (`a = sys.argv[1:]; if a[0] == "worker" ... elif ...`, no `else`); `rerun.py:37` (`sys.argv.index("--tasks") + 1`).
- **Evidence:** `python rerun.py --tasks tasks_p2.jsonl status` matches none of the branches and exits 0 having done nothing; `python rerun.py status --tasks` (missing value) raises `IndexError`.
- **Why it matters:** an operator can believe a status/worker command ran when it did not (misleading `status` is the more dangerous half).
- **Recommended correction:** parse `--tasks` out of argv first, and raise an error on an unknown/absent mode instead of falling through.

**3. P2 · Confirmed issue — an unset `{PYST}`/`{PYTS}` aborts the whole worker *after* the claim is taken, leaving the task stuck**
- **Location:** `rerun.py:47-50` (`fill` raises `SystemExit`), called from `worker` at line 171 (`quarantine(...)`) — after `os.mkdir(claims/<sid>)` at line 157.
- **Evidence:** claim → `quarantine` → `fill` → `SystemExit` propagates out of `worker`; the claim is never released and no `gaveup` record is written, so every later worker skips the task (`FileExistsError: continue`) until a manual `release`.
- **Why it matters:** contradicts the docstring ("a task that uses an unset one stops with an error" — it stops the *worker*, and blocks that task cluster-wide); one forgotten variable on a CPU node kills the job with a half-held claim.
- **Recommended correction:** catch the unset-variable condition per task in `worker` (record `gaveup` with the message and release the claim) instead of letting `SystemExit` escape.

**4. P2 · Missing information — original environment provenance for two sets is unverifiable from the attached evidence**
- **Location:** `make_tasks_p2.py:66-71` (grid20), `:88-90` (confirm); `env_results` (`:41-49`).
- **Evidence:** grid20's thread setting is admitted as "not recorded" (registration says so); `PYTHONWARNINGS=ignore` is nevertheless set for grid20 (`OMP(1)` includes it) although no original record of that variable was shown; the confirm launch script is not in the evidence, so its `(1)` thread claim and absence of `PYTHONWARNINGS` rest on the registration alone; `run_river.sh` never sets `OMP_NUM_THREADS`, so "none set" assumes the operator's ambient shell had none.
- **Why it matters:** these are exactly the values that determine bit-level agreement in the recheck; differences will be reported rather than corrected, but they should be labelled "unknown/assumed" rather than looking reproduced.
- **Recommended correction:** state in REGISTRATION_P2 that grid20's and confirm's original env vars (including PYTHONWARNINGS) and the ambient shell env of run_river.sh are not recorded and the registered values are assumptions.

**5. P2 · Missing information — `dtmoe` appears in the original grid but is absent from `GRID`**
- **Location:** `make_tasks_p2.py:97-98` (`GRID` has fsnet, onenet, adaptz, shifts) vs `original_drivers.txt` tune_ts.sh (`case ... dtmoe) LS="16 32"; MS="1 2 3"`, run with `nice 19`).
- **Evidence:** tune_ts.sh enumerates a dtmoe grid; `GRID` does not, so any dtmoe dev outputs are neither tasks nor in the SKIPPED report. dtmoe's venv is `PYTOT`, suggesting it belongs to P1 (GPU).
- **Why it matters:** if any Table-1 dtmoe number comes from that local CPU dev grid, P2 would not reproduce it — the "complete by construction" claim only holds relative to the four registered methods.
- **Recommended correction:** confirm from PLAN_BASELINES.md / P1's tasks.jsonl that dtmoe is a GPU/P1 method; if not, add its grid as tasks or record why it is out of scope.

## Points that need execution (not confirmable by reading)

1. `grep -n "makedirs\|mkdir" MICE/code/run_river.py MICE/code/run_trained.py experiments/mice_table1_fill_20261018/run_trained_probs.py experiments/mice_table1_fill_20261018/run_ts.py` — decides Finding 1.
2. Intersection of task ids: `python -c` over tasks.jsonl vs tasks_p2.jsonl — both share `$RUNS/_rerun/{claims,done}` keyed only by id, so any id present in both would make the P2 worker silently skip a finished P1 task (or vice versa). Construction suggests disjoint method names, but this must be checked, not assumed.
3. The `SKIPPED` counter printed by `make_tasks_p2.py` (GPU methods / derived replays) against the P1 method list — the summary file captured does not include that line.
4. Whether the seven local qualify probes ran in directories that already existed (they would not have exercised item 1).

No P0: no leakage, frozen-criteria change, or confirmed wrong-location write was found in the reviewed scope; all output paths, counts, and thread settings I could reconstruct match the registered originals.
rc=0
Tue Oct 20 00:17:40 AEDT 2026

Disposition: 1 rejected (all four drivers makedirs; dev_cluster/P absent in the sandbox and the probe passed); 2, 3 fixed; 4 added to the registration; 5 rejected (dtmoe is P1, set dtmoe_dev). Execution points: id intersection 0; SKIPPED list printed (GPU methods and replays only).

## MiMo Flash low re-check of the fix (00:18-00:22): none

## Sonnet 复审 P2（2026-10-20 09:14，用户要求“之前做过的让sonet 审查一下”）

材料：登记、make_tasks_p2.py、rerun.py diff、HANDOFF diff、原脚本线程设置、每组一个任务样例。耗时 32.5 秒，0.13 美元。原文：

> **Defect 1**
> - **Severity:** P2
> - **Location:** `rerun.py` `worker()`, the first lines after the diff change.
> - **Evidence:** `env = {v: os.environ.get(v, "") for v in VARS}` is followed by `base = f"{env['RUNS']}/_rerun"`, and `check_vars(...)` only comes after that line.
> - **Why it matters:** `RUNS` used to raise a `KeyError` when unset. Now it silently becomes `""`, so `base` is `/_rerun`. `results_river`, `results_heldout` and the other `results_*` sets use only `{REPO}` in their commands. For these, `check_vars` never flags a missing `RUNS`. The worker then creates claims, done records and quarantine directories under `/_rerun` (or fails there), away from the run root.
> - **Correction:** Check `RUNS` first and stop if it is empty, for example `if not env["RUNS"]: raise SystemExit("RUNS not set")`. Do this before computing `base`, and in `qualify` too.
> 
> **Defect 2**
> - **Severity:** P2
> - **Location:** `HANDOFF.md` P2 "Stop point" against `REGISTRATION_P2` "When P2b selection may run".
> - **Evidence:** HANDOFF says "When ts_dev shows 720 done and 0 given up, stop and push." The registration says "A given-up task stops the selection of its method until its disposition is registered."
> - **Why it matters:** The handoff has no case for a ts_dev task that is given up. A cluster operator could wait forever, or push without saying that selection is blocked. The handoff also never says that the other nine sets keep running until the task list is empty. Read literally, the stop condition could be taken to cover only ts_dev.
> - **Correction:** Add this to HANDOFF: "If any ts_dev task is given up, stop and report it. Do not select. The coordinator registers the disposition. All other P2 sets run until `status` shows no task left."
> 
> Everything else you asked about matched. I found no mismatches for item 1, the count and name checks in item 2, the `--tasks` parsing in item 3, or the integrity question in item 4.
处理：两条都核实成立并修正。1）check_vars 总是要求 RUNS，并移到 base 计算之前（worker、qualify 都经过它）；实测未设 RUNS 时 worker 报错退出、rc=1。2）HANDOFF 停止点写明其他 P2 组跑到 status 为空，ts_dev 有放弃任务时推送并报告，由协调者先登记处置。修正 diff 交 Sonnet 复查，结果 none。
