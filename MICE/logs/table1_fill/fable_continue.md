Finished reading the plans, amendments, logs and the DR/watch scripts. Writing the decision now.

**Decision**

1. **Order tonight.**
   - CPU, now, in this order: (i) `export_table1_fill` readout of the finished items, with a per-cell provenance flag (CPU-clean / GPU accuracy-matched / GPU FECS-exposed-unverified); (ii) frozen-config selection for shifts, adaptz, fsnet, onenet by the registered rule, boundary check, selection output committed before the first test run; any boundary extension (lr ×10 or /10, n_steps 25) runs on CPU before that method's tests; (iii) test runs of the four methods, real + confirm first, then grid + generator, 10–12 single-thread lanes bounded by RAM (31 GB total, keep > 8 GB free), not 20; (iv) TOT adapter implementation (code only) + MiMo audit, in the remaining lanes.
   - GPU, one process: Drift-Resilient TabPFN, started after the operational items in (5) are committed. No other GPU item tonight.
2. **dtmoe: wait.** Do not run the local dev grid or tests, deterministic or not. Amendment b (user-approved, committed) closed the local dtmoe stage; reopening it is a user decision, not mine. Strict determinism addresses run-to-run reproducibility, not the demonstrated FECS silent corruption, and the single GPU slot is better spent on the authorized 83 h DR run. Optional, ≤15 min before DR starts: the three qualification probes with `TS_DETERMINISTIC=1` twice each, as a smoke test of the switch (does deterministic mode even run for the dtmoe ops; it is set for every H800 dtmoe task in `make_tasks.py`). Outputs under a diagnostics directory, never used for selection. dtmoe cells read out as "pending (H800)".
3. **DR-TabPFN locally now: yes**, under the authorization of 18:33 (92 streams, one process). It is the only GPU item that is authorized, needs no frozen config, and is stateless per batch, so a corrupted batch cannot propagate.
4. **TOT: implement now, gate on CPU, not GPU.** Gate (a) is "within the paper's reported spread", a device-agnostic criterion; run the unchanged official code on ETTh2 pred_len 1 on CPU. If CPU time exceeds ~12 h, stop and defer. Gate (b), the dev grid and tests also on CPU, after the four methods' tests are queued (user priority "tot slowly"). tot's device changes from the cuda note to CPU, dev and test on the same device, never mixed (same rule as dtmoe amendment b).
5. **Register before running** (amendment c to PLAN_BASELINES, operational; plus one README/coverage change):
   - frozen configurations and dev scores of the four methods, committed before any test stream;
   - tot device = CPU (item 4), gate criteria unchanged;
   - DR operational rules: `run_drtabpfn.py` gets absolute per-batch end timestamps (currently only durations `wt`), edited and checked before the worker starts; canary (two fresh-process 12-batch elec2 runs, bit-identical to each other and to the clean reference) at every process start; `fecs_watch.sh` stays up, no auto-restart after a GPU_STOP: the in-progress stream is recomputed from scratch after a fresh canary and 30 quiet minutes; any stream with n_retry > 0 or the select_features shape error is recomputed from scratch and flagged, never accepted silently;
   - the end-of-run full-stream reruns of the earlier overnight plan are dropped (user verifies this week); the per-batch timestamps and the retained Windows event export are what the user verifies against;
   - readout flags: mice_cp generator 30/30 (pre-reboot fault storm) and ddm/ltm generator probabilities (accuracy bit-identical, probabilities unverified) marked unverified in coverage.csv and README until the user's verification; nothing replaced.

**Supporting evidence**
- The four CPU methods' dev grids ran on CPU, so their selection is untouched by the GPU incident; the tests are the largest unblocked, clean workload.
- DR GPU-to-GPU bit identity on clean hardware and CPU agreement (max |dP| 4.7e-3) make the canary a valid per-process check; checkpoints every 25 batches bound the loss per stop.
- Amendment b item 1 explicitly states no local dtmoe development result is used and assigns dtmoe to the H800; Codex astra's decision rejected any blanket nondeterminism exemption.
- `run_drtabpfn.py:46-69` records only durations, not absolute times, so FECS correlation needs the edit before start.

**Alternative options**
- Run the local deterministic dtmoe grid + tests as amendment c after DR, or preempting DR (~10–15 h). Viable only with explicit user approval, and it should still carry the "not FECS-clean" flag.
- TOT gate (a) on the GPU between DR streams: saves CPU hours, costs a DR restart + canary each time; not worth it while CPU is free.

**Key risks**
- CPU load alongside the GPU process has correlated with CUDA failures before (log 2026-10-05 21:59, three toggles). If FECS returns under 10–12 CPU lanes, halve the lanes before touching the DR run, and log the lane count.
- 4 event-free hours do not certify 83 h; the DR result is "unverified" until the user checks timestamps against events.
- Selection boundary extensions can add a day of CPU for the heavier methods (onenet, fsnet).

**Remaining uncertainty**
- CPU runtime of the official LSTD-TOT on ETTh2, and of the four methods' test streams (longest 1500 batches each). Whether deterministic mode runs for the dtmoe ops at all.

**Confidence**
- DR now, dtmoe wait, CPU tests first: high. TOT on CPU: moderate-high. Lane count: moderate.

**Requires user approval**
- Yes: any local dtmoe grid or test run (reverses amendment b). Yes: reporting tot as skipped if a gate fails (removes a Table 1 column). No: everything else above, which stays inside the 18:33 authorization and the "continue, no verification now" instruction; a Sonnet or MiMo check of the selection script, the DR timestamp edit and amendment c precedes execution.