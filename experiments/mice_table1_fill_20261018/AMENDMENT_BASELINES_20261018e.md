# Amendment e to PLAN_BASELINES.md, 2026-10-19 (operational: dtmoe on the CPU; CPU process limit 16)

Written before any dtmoe run on the CPU under this amendment; no dtmoe development score has been looked at for
selection (amendment d, deviation record: the strict-mode GPU probe was aborted, neither passed nor failed). User
decisions of 2026-10-19: dtmoe runs on the CPU, development and test ("选1，CPU 上跑"); the CPU process limit of
amendment c is raised from 12 to 16 with a guard ("提到 16，附守卫"). Fable 5.1 proposed the protocol
(MICE/logs/table1_fill/fable_dtmoe_cpu.md); Sonnet reviewed this amendment and the scripts before commit.

1. **Device and lanes.** This applies the fallback of amendment b item 1: every dtmoe run, development and test, on
   the CPU, never mixed with GPU outputs. At most 16 CPU processes in all (was 12, amendment c): the 12 lanes of the
   running extension of the other CPU baselines stay as they are; 4 lanes for dtmoe, `nice 19`, single-threaded.
   After that extension ends, dtmoe gets 8 lanes and the frozen-configuration tests of the other methods 8. The GPU
   stays at one process (Drift-Resilient TabPFN). Guard (dtmoe_guard.sh, every 60 s): GPU_STOP present, fecs_watch
   heartbeat older than 150 s, 1-minute load > 18 on two consecutive checks, or the running Drift-Resilient TabPFN
   stream > 20% slower (median batch time of its last 25 checkpointed batches against that of its earlier batches
   from batch 11 on) writes dtmoe_cpu/STOP and kills the dtmoe processes; their partial outputs are quarantined and
   not counted as deaths; dtmoe restarts only after the cause is logged and STOP is removed. Limitation: a DR stream
   that starts after dtmoe has no unloaded reference for the slowdown check.
2. **Where and how** (dtmoe_cpu.sh). Root ~/pfn-runs/mice-table1-newbase/dtmoe_cpu/ (new: dev/P, probe_pre/b,
   probe_post_<stage>, logs, quarantine). Environment tsbase; TS_DEVICE, TS_DETERMINISTIC and CUBLAS_WORKSPACE_CONFIG
   unset (cpu); OMP/MKL/OPENBLAS_NUM_THREADS = 1. Each task in a fresh process; a task whose process dies has its
   partial outputs moved to quarantine and is rerun once from the start; a second death is GAVE UP and reported (deaths
   are recorded per task in dtmoe_cpu/deaths/ and persist across restarts; guard stops are not deaths). The grid starts
   only with the marker PROBE_PRE_PASSED and no UNVERIFIED_* marker; every invocation starts the guard (one instance). An
   output counts only if the process returned 0, the file loads, and its config records device "cpu". The old GPU
   dtmoe outputs in dev/P, dtmoe_local/ and the three CPU files of dev/P_cpu_dtmoe stay unused (amendments b, d).
3. **Determinism probe before the grid.** The three probes of amendment d (elec2 L16 lr1e-4 s1 m1; elec2 L32 lr1e-4
   s1 m1; insects_abrupt_balanced L32 lr1e-3 s5 m3), each twice in fresh processes: run a into dev/P (it is the grid
   output of that configuration), run b into probe_pre/b; verify_compare.py: every array except wall time byte
   identical. Any difference or missing output stops the dtmoe path and goes to the user. The probe times give the
   first measured n_steps 5 / L32 CPU times; the projected budget is logged before the grid starts. Informational
   only, after the grid (oldcmp): the three P_cpu_dtmoe files against the new outputs of the same configurations;
   the result is logged and never used for selection.
4. **Grid, selection, extension, freezing, tests** as registered for the CPU baselines: the 180-task grid of
   PLAN_BASELINES.md into dev/P; select_frozen.py on dtmoe_cpu/dev/P with the selection, tie and one-time extension
   rules of amendment c (user 2026-10-18: the same extension rule for dtmoe), the freeze committed before its tests;
   the frozen configuration on the 92 test streams on the CPU, same lanes and death rule; outputs under dtmoe_cpu/.
   Before the extension and the tests run, the projected CPU time is logged and reported to the user.
5. **Bookends.** After the grid, after the extension (if any) and after the tests: elec2 L16 lr1e-4 s1 m1 once more
   into probe_post_<stage>, byte identical (except wall time) to its dev/P output; otherwise UNVERIFIED_<stage> is
   written and that stage is neither selected from nor reported as verified.
6. **Reporting.** Provenance flag "CPU" (as the other CPU baselines) plus the probe and bookend status. Table 1
   footnote: dtmoe evaluated on the CPU because the CPU and GPU runs of the same configuration differ (amendment b:
   prediction agreement 0.83-0.97) and the GPU strict deterministic mode was too slow on the local GPU. Timing and
   peak memory measured on the local CPU (amendment c item 7).

## Deviation 1 (2026-10-19 12:4x, before any dtmoe output under this amendment)
The probe of item 3 started at 12:35:47 with 16 running CPU processes. The guard tripped at 12:41:59 as registered:
Drift-Resilient TabPFN stream h3_airlines_b, median batch time 7.35 s over 659 batches before dtmoe started (last 50:
7.69 s) against 10.60 s over 31 batches after, +44%; 1-minute load 13.4 to 16.7. The four dtmoe processes were killed;
their partial outputs are in quarantine as "stop"; no death was recorded (dtmoe_cpu/deaths/ empty). The "probe pre
FAILED" line that dtmoe_cpu.sh then logged is an artifact of the missing outputs, not a determinism result (a note
says so in progress.txt); probe_pre/ and its comparison files were moved to probe_pre_stopped_20261019_1241/ and
nothing of them is used. dtmoe_cpu.sh now logs "probe pre STOPPED" and exits before comparing when STOP exists (the
commit of this deviation). Likely cause (a hypothesis, not measured separately): the machine has 10 physical cores
(20 logical); nice 19 did not keep the DR process from slowing down. From now on at most 12 running CPU processes
plus the GPU process: four processes of the running extension were suspended with SIGSTOP at 12:46:27 (pids and
tasks in dev/suspended_20261019.txt); their outputs will carry invalid wall-time arrays, which are not used anywhere
(select_frozen.py reads only acc; timing and peak memory are measured under amendment c item 7). The extension
continues on 8 lanes, dtmoe on 4. The four are resumed (SIGCONT) when the dtmoe path ends or stops, or when the
extension's queue is empty, whichever comes first; lanes then follow item 1, scaled to at most 12 running CPU processes (dtmoe 6, other tests 6).
The guard is unchanged. A second trip on the DR criterion with 12 running processes means the cause is not the
process count; dtmoe then waits for the end of the extension. Fable 5.1 (MICE/logs/table1_fill/fable_dtmoe_trip.md)
proposed this; Sonnet reviewed it (4 findings, accepted: no watchdog in the extension, checked - xargs without
timeout, CPU only; wt marked invalid; evidence moved, not deleted; a manual DR check about 15 min after the restart).
