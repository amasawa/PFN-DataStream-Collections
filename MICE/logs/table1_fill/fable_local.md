**Decision**
dtmoe first, then DR. Sequence on the single GPU process: (a) commit amendment d; (b) the six probe runs, sequentially, through the same chain script the grid will use (canary at process start, strict mode); (c) the full dtmoe dev grid fresh into a new output directory; (d) freeze commit (`frozen_dtmoe_final.json`), then dtmoe tests; (e) `dr_chain.sh` for the 92 DR streams. Reopening the local dtmoe stage is covered by the user's decision: amendment b approved the protocol, the user has now moved the device. Only the fallback (a re-specified selection procedure) needs a new approval.

**Supporting evidence**
- Total wall-clock is the same either way (DR is the long pole, ~83 h). dtmoe first removes the only dependency chain (grid → freeze → tests) from the end of the schedule, and the probes answer within an hour whether strict mode is qualifiable locally. If it is not, DR starts immediately and the fallback re-specification is drafted and approved while DR runs; with DR first, that question would sit unanswered for 3.5 days.
- Amendment b's qualification rule is device-agnostic as written (two fresh-process runs per probe, bit-identical to each other, not to any earlier output; no tolerance). Re-running it on the local GPU is the correct way to move the device. `run_ts.py:26-30` already implements strict mode with the required cuBLAS assertion.
- The three probes include the configuration that failed (elec2 L32 lr1e-4 s1 m1) in non-deterministic mode; a bit-identical pair there is the most informative local result available.

**Probe failure rule (write it into amendment d)**
- Strict mode raises "no deterministic implementation": hard stop of the dtmoe GPU path; fallback as in amendment b item 1 (re-specified selection with equal replication budget, seeds, aggregation, tie-breaking, registered before any dev run). Requires user approval.
- Silent mismatch under strict mode: run that probe a third time for classification only (never to pick a winner), record the fecs_watch window, then the same fallback. No tolerance is derived; the old local grid and `dev/P_cpu_dtmoe` stay unused either way.
- Add bookend probes: after the grid and after the tests, rerun the three probes fresh and require bit-identity with the pre-grid outputs. This is a device-health canary against silent corruption during a long run, not a certification of other grid points. Cost: minutes.

**Amendment d must contain**
1. The user decision quoted with its time; supersession of amendment c item 6 and of the device in amendment b item 1 (protocol unchanged); the H800 clean rerun is "suspended, not cancelled" and stays a draft.
2. GPU order above, the one-process rule, no restart after GPU_STOP (user decides), per-batch end times and fecs_watch timestamps recorded beside every GPU output.
3. dtmoe: new output paths for probes, grid, tests; probe pass and fail rules; bookend probes; freeze commit before the first test stream; whether the one-time boundary extension rule of amendment c items 2-3 applies to dtmoe (I recommend yes, same rule, stated in advance; it costs GPU time, so say so).
4. Provenance flags (item 8): add "GPU local, guarded" (fecs_watch active throughout, no nvlddmkm event between start and end, canary and bookends passed, strict mode for dtmoe), distinct from "GPU local, unverified" (pre-reboot). Keep "GPU H800" in the exporter, currently empty. Nothing replaced in place.
5. Item 7 timing and peak memory for GPU methods now measured on the local GPU; the paper names the device.
6. `verify_chain.sh` still refuses the dtmoe replay stage; the new grid is a fresh computation, not a replay.

**Alternative options**
- DR first: same total time, defers the determinism question; rejected.
- dtmoe dev grid on the CPU, single-thread, deterministic by construction, after the 450-run extension frees lanes: a clean fallback if strict GPU mode fails, but only if the per-task CPU time is measured and registered first; it needs the same user approval as any fallback.

**Key risks**
- Strict mode may raise on an MoE routing op (scatter/index ops) or be 2-3x slower; the probes expose both within the hour.
- About 4.5 days of continuous single-GPU work next to 12 CPU lanes, with only ~9 h of event-free evidence; one nvlddmkm event stops everything until the user restarts. Acceptable, but the user should know the idle-time risk.
- Extension rule for dtmoe at n_steps 25 could add roughly a day of GPU time if its boundary is hit.

**Remaining uncertainty**
Whether every dtmoe op has a deterministic CUDA kernel on the local architecture. Whether the user intends the H800 draft to be dropped rather than suspended; treat as suspended until told otherwise.

**Confidence**
High on the order and on reusing the amendment b protocol locally. Moderate that strict mode qualifies on the local GPU.

**Requires user approval**
- No (covered by the decision; register in amendment d and report): DR local, local dtmoe under the amendment b protocol, GPU order, provenance flag change, bookend probes.
- Notify, do not block: extension rule applied to dtmoe; timing measured on the local GPU.
- Yes, blocking: any fallback selection procedure after a failed probe; any use of pre-existing local dtmoe outputs; any restart after a GPU_STOP.