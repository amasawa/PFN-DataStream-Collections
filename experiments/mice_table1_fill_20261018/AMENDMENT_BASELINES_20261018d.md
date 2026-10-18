# Amendment d to PLAN_BASELINES.md, 2026-10-18 (committed before any GPU run it covers)

User decisions of 2026-10-18 23:3x: "do not use the H800 for now; finish the experiments yourself"; then, asked
explicitly: dtmoe runs on the local GPU under the protocol of gpu_verify AMENDMENT_20261018b (device moved, protocol
unchanged); GPU order probes -> Drift-Resilient TabPFN -> dtmoe; the one-time full extension rule also for dtmoe;
bookend probes, a mismatch flags the affected outputs "unverified". Expert: Fable (MICE/logs/table1_fill/
fable_local.md); review: Sonnet (sonnet_local_review.md).

1. **Supersessions.** Amendment c item 6 (GPU work to the H800) and the device of gpu_verify AMENDMENT_20261018b item 1
   (H800) are replaced by the local GPU. The H800 clean rerun (experiments/clean_rerun_mice_h800) is suspended, not
   cancelled; it stays a draft.
2. **Local GPU rules.** One GPU process at a time; fecs_watch.sh active throughout; no restart after ~/pfn-runs/GPU_STOP
   without the user; per-batch end times (DR) and the fecs_watch log kept beside every GPU output.
3. **Order (gpu_local.sh).** (a) dtmoe determinism probes; (b) Drift-Resilient TabPFN on the 92 streams (dr_chain.sh:
   canary at every process start, quarantine and restart from batch 1 after a death, at most 3 deaths per stream);
   (c) if (a) passed: the dtmoe development grid (180 tasks), then the post-grid bookend probes; then the chain stops
   for the coordinator (selection, extension, freezing, tests: below).
4. **dtmoe probes (amendment b item 1, locally).** Strict deterministic mode (TS_DEVICE=cuda, TS_DETERMINISTIC=1,
   CUBLAS_WORKSPACE_CONFIG=:4096:8). Each of elec2 L16 lr1e-4 s1 m1, elec2 L32 lr1e-4 s1 m1, insects_abrupt_balanced
   L32 lr1e-3 s5 m3 runs twice in fresh processes; the two runs of each must be bit-identical (every array except wall
   time; verify_compare.py). Outputs: ~/pfn-runs/mice-table1-newbase/dtmoe_local/probe_pre/{a,b}. Failure: a raised
   "no deterministic implementation" or a mismatch stops the dtmoe path (a mismatching probe is run a third time for
   classification only); DR goes on; the fallback selection procedure of amendment b needs the user. The earlier local
   dtmoe outputs (dev/P, dev/P_cpu_dtmoe, verify replays) stay unused.
5. **dtmoe development grid**: the registered grid (lr {1e-4, 1e-3, 1e-2} x n_steps {1, 5} x L {16, 32} x mech
   {1, 2, 3}, 5 development streams) fresh into dtmoe_local/dev/P, strict mode, each task in a fresh process; a task
   whose process dies has its partial outputs moved to dtmoe_local/quarantine and is rerun once from the start; a
   second death gives it up (reported; the selection then refuses, amendment c item 3).
6. **Selection, extension, freezing, tests**: as amendment c items 1-4 (same select_frozen.py rule, full one-time
   extension of every boundary axis, re-selection with the original grid first in ties, frozen even on a boundary,
   one freeze commit before the first test stream), on the local GPU in strict mode.
7. **Bookend probes**: the three probes rerun once each after the development grid (and after the extension) and after
   the tests, into dtmoe_local/probe_post_<stage>; each must be bit-identical to probe_pre/a. A mismatch flags every
   output of the stage it closes "unverified"; nothing is selected or frozen from flagged outputs.
8. **Provenance flags** (amendment c item 8): "GPU local, guarded" = fecs_watch active from start to end with no
   nvlddmkm event in that window, canaries and bookends passed, strict mode for dtmoe; otherwise "GPU local,
   unverified". Timing and peak memory of the GPU methods (amendment c item 7) are measured on the local GPU.
