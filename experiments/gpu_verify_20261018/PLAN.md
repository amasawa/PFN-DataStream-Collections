# GPU integrity verification, 2026-10-18 (committed before any verification replay)

## Incident (P0, Codex gpt-6-astra xhigh, MICE/logs/table1_fill/codex_fecs_integrity.md)
Silent output corruption on this GPU during Windows nvlddmkm event 13 "Graphics FECS Exception" periods: a
Drift-Resilient TabPFN replay of elec2 (12 batches, stateless per batch) matched a previous GPU run bit for bit on
batches 1-10 and differed on batch 11 (max |dP| 0.868, accuracy 0.32 vs 0.76, no error), finishing 14:17:18, the second
of the last FECS event (evidence: ~/pfn-runs/mice-table1-newbase/evidence_fecs_20261018; events:
env/gpu_events/nvlddmkm_20261018_1850.csv.gz, retained from 2026-10-16 05:45). FECS events occur in every retained hour
with multi-process GPU work. Past GPU outputs from those periods are suspected, not proven wrong: they are kept
unchanged and not used for new conclusions until verified. Replacing any reported result needs user approval.

## Method
Replay each task completely (from initialisation, no resumed checkpoints) in a fresh process with the same code
(MICE/code computation unchanged since 2026-10-15; only export / table scripts changed), environment, data and seeds;
outputs under ~/pfn-runs/verify-20261018/<set>, never in the original directories. Compare every saved array and
pickle except wall time (verify_compare.py: bit identity; prints only IDENTICAL / DIFFERENT and key names, no scores).
GPU outputs of these pipelines are bit-deterministic across processes (DR batches 1-10, dtmoe, 60 TabPFN reruns).

## Order (verify_chain.sh; one GPU process; a canary before every stage)
0. canary: two 12-batch DR replays in fresh processes, bit-identical to each other and to the clean reference run.
1. dtmoe development tasks 1-38 (q_dtmoe_dev; 1-5 ran during the pre-reboot fault storm or at the FECS onset, 6-38 in
   the FECS window); before any configuration is selected.
2. mice-confirm-cp-20261017: all 66 tasks (micecp, micev, fifo, ddm, ltm, winens in this order).
3. mice-r14-confirm: all 216 tasks.
4. mice-table1-probs-gen: all 60 tasks (probabilities included). 5. mice-table1-cp-gen: all 30 tasks.
Later (separate decision): mice-main-cp-grid10, then min(12, N) tasks of mice-r14-exist, mice-r14b-acc,
duo-rand-20261017, duo-rand-verify, then 12 earlier tasks across dates.

## Stopping rule
fecs_watch.sh reads the Windows event log every 60 s; any nvlddmkm event or an unreadable log writes ~/pfn-runs/GPU_STOP
and stops every GPU job. The chain also stops on a failed canary, a task that crashes twice (a crash gets one fresh
retry with its checkpoints removed) and on the first mismatch: the second independent replay of a mismatching task is
decided by hand (two new runs disagreeing -> stop GPU verification; agreeing against the original -> confirmed
non-reproduction, the whole result family is replayed, all versions kept). No retry until a preferred answer appears.
