**Decision**
1. GPU order tonight: finish dtmoe dev (incl. task 31 second pass) → recompute the FECS-period dtmoe dev tasks (~1 h) → TOT gate (a) on the official code (short, unblocks the CPU) → drtabpfn worker. Do not preempt drtabpfn for dtmoe test tonight; that is a morning decision for the user (see approval).
2. (b) Recompute all dtmoe dev tasks produced 12:52–14:17, do not spot-check. Compare bit-for-bit with the stored outputs; the clean recompute is the authoritative version either way, and a match doubles as the verification.
3. (c) For drtabpfn: a 12-batch elec2 canary at every worker (re)start, absolute timestamps per batch in the checkpoint, Windows FECS events polled during the run, and three full-stream reruns at the end (one grid, one confirm, one real stream). Any batch whose timestamp falls inside a FECS window, or any stream resumed after a crash, is recomputed from the last pre-fault checkpoint.

**Supporting evidence**
- Silent corruption is demonstrated on this machine, not just crashes: the drtabpfn select_features shape is arithmetically impossible and appeared only during FECS periods (log 14:22). Dev selection is an argmax over 180 tasks, so one corrupted task can change the frozen config; 32 tasks × ~1–2 min on a clean GPU is ~1 h against 83 h of drtabpfn. Spot checks of a few tasks have little power against per-batch corruption.
- dtmoe GPU outputs are bit-deterministic across processes (amendment b item 3), so a bit-identity comparison is a valid test.
- TOT gate (a) decides whether a 180-task tot dev grid exists at all. onenet dev ends ~23:00; after that the CPU idles unless the gate has run. The gate needs no frozen config, so it is the only GPU item with a downstream dependency that is ready tonight.
- dtmoe test cannot start tonight anyway: it needs the full dev grid, the boundary check (n_steps 25 or lr extension would add up to ~4 h of GPU dev tasks), commit, and the Sonnet check. drtabpfn is productive GPU use meanwhile and checkpoints every 25 batches (~3 min lost on preemption).
- drtabpfn has no training state, so resumption from a checkpoint cannot change predictions; the canary (clean-GPU reference matches CPU, max |dP| 4.7e-3, bit-identical GPU-to-GPU) is a cheap per-process sanity check.

**Alternative options**
- drtabpfn strictly first with no interruption (user's 13:07 priority "fill other cells first, dtmoe/tot slowly" read literally): costs the CPU idle hours for tot; otherwise equivalent. Acceptable if the TOT gate is expected to take more than ~2 h on the GPU.
- Spot-check only the FECS-period dtmoe tasks (saves ~45 min): not recommended given the demonstrated silent corruption.

**Key risks**
- FECS may return even with one process; 4 h clean is thin evidence for an 83 h run. Hence timestamps + event-log correlation rather than trusting crash-free as clean.
- The retry path in run_drtabpfn (n_retry, seed retries) can mask real errors. Rule: a retry or the shape error while the Windows log shows zero FECS events in the preceding 10 min is a bug, not a GPU fault; stop the worker and investigate instead of retrying.
- Preempting the worker: kill the bash loop first, then the python child, or the loop counts a FAIL and restarts in 15 s. Write this procedure down before the user wakes.
- Editing run_drtabpfn.py for timestamps is fine only before the worker starts (running scripts must not be edited); log the change as operational.

**Remaining uncertainty**
- TOT gate (a) runtime on the GPU is unknown; if it exceeds ~2 h, defer it to the morning.
- Whether dtmoe hits a grid boundary (adds GPU dev work before test).

**Confidence**
- (b) recompute: high. TOT gate before drtabpfn: moderate-high. Deferring dtmoe test: moderate (depends on user priority).

**Requires user approval**
- Preempting drtabpfn for dtmoe boundary-extension + test + anything beyond the short TOT gate (conflicts with the user's "dtmoe and tot slowly" priority; delays drtabpfn ~10–15 h).
- Reporting tot as skipped if gate (a) fails (registered rule, but it removes a Table 1 column).