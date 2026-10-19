# Operational amendment of the clean MICE rerun, 2026-10-20 (committed and pushed before any cluster run)

Origin: the user asked for an expert review of the work already done ("之前任务也让fable审核一下"). Fable reviewed the
P1 path end to end (MICE/logs/table1_fill/fable_prior_review_a.md): 8 findings, all verified by the coordinator and
accepted. Nothing here changes a computation, a task, a criterion or a reported quantity, except item 6, which fixes
where timings come from. Where this note and HANDOFF.md / PLAN.md differ, this note holds.

1. **Frozen k\* in the benchmark roots (Fable 1, P0).** bench_pools.py and bench_cp.py read `<root>/kstar.json` in
   stage a2. PLAN.md "Benchmarks" keeps the original k\* as a frozen input, but the bundle put only the data into
   `<root>-h800`, so a2 would have failed on its only attempt. The tars `mice-r13-bench-h800` and `mice-r14b-bench-h800`
   now also hold the original kstar.json (sha256 identical to ~/pfn-runs/<root>/kstar.json). The desktop bundle was
   rebuilt and its SHA256SUMS recomputed. make_bundle.sh does the same.
2. **TabPFN cache path of the benchmarks (Fable 2, P0).** bench_pools.py, bench_cp.py and bench_resources.py set
   `TABPFN_MODEL_CACHE_DIR=~/pfn-venvs/cache/tabpfn` themselves, with HOME = $WORK/home. The cache is therefore untarred
   to `$WORK/home/pfn-venvs/cache/tabpfn`, and the job variable TABPFN_MODEL_CACHE_DIR points to the same directory
   (HANDOFF steps 1 and 2).
3. **dtmoe cap (Fable 3).** The procedure of ACTIVATION item 2 can now be run:
   - `rerun.py ref <task> <dir>` runs the task once in the sandbox, with TS_DETERMINISTIC and CUBLAS_WORKSPACE_CONFIG
     removed. If the run returns 0, it writes its wall time (with rc, host and GPU) to <dir>/ref.json; otherwise it
     writes nothing and the failure is reported. The wall time is the only value used.
   - `rerun.py qualify <task> <dir> --timeout <s>` kills a run that exceeds the limit and prints TOO SLOW, with no
     verdict.

   For each of the three dtmoe probe tasks, the reference runs first, then the strict probe with the timeout set to
   10 times the reference time.
4. **Paused sets (Fable 4).** `rerun.py worker ... --exclude-sets s1,s2` skips those sets. P1 production runs with
   `--exclude-sets dtmoe_dev`, plus any set whose probe is NOT QUALIFIED. dtmoe_dev starts only after the cap verdict
   and the user's decision, on an instruction that the coordinator commits.
5. **Where returned results go (Fable 5).** The cluster returns whole run roots by rsync (inputs included; their hashes
   are known). On the Windows machine they go to a separate tree, `~/h800/` (HOME for the analyses of the H800
   results):
   - `~/h800/pfn-runs/<root>` holds the run roots;
   - `~/h800/repo` holds a checkout at the registered commit, with `MICE/results_*` from the cluster.

   Nothing goes into ~/pfn-runs or the working repository's `MICE/results_*`. The H800 analyses run with HOME=~/h800,
   from ~/h800/repo. The path adaptations of the benchmark analyses (PLAN.md "Benchmarks") are registered before they
   run.
6. **Timings (Fable 6).** The wall times of tasks on a shared GPU are records, not reported timings. The Table 1 time
   and peak memory per method come only from exclusive timing tasks: one process alone on an H800, and for CPU
   methods the P2 node type. These tasks are registered as a separate list before they run, after P1 production
   (they measure; they write no reported accuracy). Until then, no timing of Table 1 is reported from the rerun.
7. **Job time limit (Fable 7).**
   - Tasks without a time estimate run in their own jobs, at the partition's maximum time limit: the 5 benchmarks,
     mice_oracle_r11:all, results_delay_dev, drtabpfn and dtmoe_dev.
   - The shared production workers exclude these sets (`--exclude-sets`), so they never start inside a 24 h job.
   - A shared task killed by a time limit is released and restarted from initialisation, as in HANDOFF step 4. The
     kill counts as one of its 3 attempts and is logged.
   - A benchmark has 1 attempt. After a kill and `release`, the runner records it as given up and never restarts it.
     It runs again only if the coordinator commits a reset of its attempt record.
8. **CPU cores per GPU worker (Fable 8).** Every GPU worker gets at least 4 cores, because the run.py family runs with
   OMP_NUM_THREADS = 4. A job with N workers per GPU therefore requests `--cpus-per-task` of at least 4N, recorded in
   the log.
9. **Runner hardening (found while testing items 3-4, and in the Sonnet check of this amendment).**
   - The task runs in its own session (so a timeout kills its whole process group). If the worker is interrupted, the
     task's process group is killed too, so no GPU work is orphaned.
   - rerun.py's output check imports numpy outside its try block.
   Run under a Python without numpy, the runner now stops with an error, instead of failing every task as "given
   up". rerun.py is run with $PY (the MICE venv), never with the system python.
