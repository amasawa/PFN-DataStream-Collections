# Amendment b to PLAN.md, 2026-10-18 22:04 (committed before the verification resumes)

Approved by the user on 2026-10-18 (option B); Codex gpt-6-astra xhigh decision in
MICE/logs/table1_fill/codex_nondeterminism.md; MiMo Pro high review in MICE/logs/table1_fill/mimo_amendment_b.md.

## What happened
The chain stopped at its rule (first mismatch) on dtmoe dev task 15, elec2 L32 lr1e-4 s1 m1. A second clean replay
(21:05, no driver event since 14:22) differed from both the original (13:01-13:03, inside a FECS period) and the first
replay: first differences of max |dP| 1.0e-6 at batch 11 or 22, then growth through online training (overall
0.60-0.86, prediction agreement 0.972-0.983). The 14 replays before it (all L = 16) were bit-identical. The task is
classified "non-reproducible; unresolved by bit comparison"; all three outputs are kept
(~/pfn-runs/verify-20261018/dtmoe_dev/P, P_replay2; original in mice-table1-newbase/dev/P).

## Changes
0. Preservation: every local dtmoe output (GPU grid in mice-table1-newbase/dev/P, CPU results in dev/P_cpu_dtmoe, the
   replays in verify-20261018/dtmoe_dev/P and P_replay2) is kept unchanged and only unused; the three task-15 outputs
   are also copied to verify-20261018/evidence_task15 (read-only).
1. The dtmoe stage ends here. No local dtmoe development result is used (neither the GPU grid nor the CPU results in
   dev/P_cpu_dtmoe): the dtmoe development grid and its test runs are recomputed on the H800 cluster (user decision
   2026-10-18: clean rerun of all paper results there), in strict deterministic mode
   (torch.use_deterministic_algorithms(True, warn_only=False), CUBLAS_WORKSPACE_CONFIG=:4096:8 set before CUDA
   initialisation, cudnn.benchmark False and cudnn.deterministic True, fixed seeds), qualified before the grid by two
   fresh-process runs of each of these development tasks, the two runs of each task bit-identical to each other (not
   to any local output): elec2 L16 lr1e-4 s1 m1, elec2 L32 lr1e-4 s1 m1 (the configuration found non-reproducible
   here) and insects_abrupt_balanced L32 lr1e-3 s5 m3. These probes do not certify other grid points: any later
   nondeterminism found on the H800 re-opens the fallback below. If strict determinism
   cannot be qualified there, the selection procedure is re-specified (equal replication budget, seeds, aggregation,
   tie-breaking) and registered before any development run; no tolerance is derived from the discrepancies above.
2. The remaining stages (confirm_cp, r14_confirm, probs_gen, cp_gen) continue unchanged after a fresh canary, with the
   same monitoring and stopping rules: a mismatch stops the chain; the second independent replay is decided by hand;
   two clean replays that disagree stop the GPU verification again (no blanket exemption for nondeterminism).
3. Supersession: PLAN.md "Order" item 1 (dtmoe tasks 1-38) is cancelled after the 15 tasks replayed (14 identical,
   task 15 non-reproducible); the PLAN.md stopping rule stands, except that this one event (two clean replays of task 15
   disagreeing) is resolved by closing the dtmoe stage and does not stop the remaining stages. Everything else in
   PLAN.md stands.
4. Enforcement in verify_chain.sh (committed with this amendment): "dtmoe" is removed from the default stages and the
   dtmoe stage refuses to run; clean() never deletes the outputs of a stem listed in MISMATCH.txt.

## Record
User approval of option B: 2026-10-18, in the Claude Code session (AskUserQuestion answer "批准 B"), after the Codex
decision (invocation: codex exec -s read-only -m gpt-6-astra -c model_reasoning_effort="xhigh"; the reply notes that the
session identity is not self-verifiable). This amendment is committed before the chain is restarted; the restart time
is in ~/pfn-runs/verify-20261018/progress.txt.
