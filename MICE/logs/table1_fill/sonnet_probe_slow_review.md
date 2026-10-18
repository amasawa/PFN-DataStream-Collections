0.0441266 12.838
Problems found: 4.

**1. The decision treats the stop as harmless, but the stop changes the chain's behavior.**
- Problem: Killing the probe makes `dtmoe_local.sh probe pre` exit non-zero. `gpu_local.sh` then goes on to DR, which is what the decision wants. But it also skips the dtmoe grid for good, because the grid runs only if the probes exited 0. The decision says only "dtmoe 的去留提交用户裁决", and it never says the chain will end the dtmoe path by itself.
- Evidence: The stated fact about `gpu_local.sh`. Amendment d item 4 says a "mismatch stops the dtmoe path", and "fallback ... needs the user". An aborted probe is neither a raise nor a mismatch, so the registered rule doesn't cover it. Stopping the probe by hand in effect decides the outcome of probe step (a) without the registered evidence.
- Fix: Record the stop as "probe aborted by the coordinator, not failed and not passed". Record that the chain's skip of the grid is a side effect and not a verdict. If the user later allows dtmoe, the grid has to be started by hand. State this in the deviation record.

**2. The decision swaps the order of steps (a) and (b), and that is not "just scheduling".**
- Problem: Amendment d item 3 and the user's decision on 2026-10-18 fix the order as probes -> DR -> dtmoe. The decision calls the swap "调度变更" and says no approval is needed. It also says the probe stage runs after DR, but the chain as written will not run it after DR at all. A hand-made reorder therefore needs a matching edit or a manual run of `gpu_local.sh`.
- Evidence: Amendment d item 3 order (a)→(b)→(c). The decision's "探针顺序改为 DR 之后" contradicts the chain's actual behavior given the fact above.
- Fix: Don't claim a reorder. Describe the action as "abort probe, DR proceeds by the chain's own continuation". State separately that the probes are not scheduled after DR and need a user decision. Any edit to the scripts must be committed and recorded before it is used.

**3. The record skips the probe's own evidence and the invalidation of the earlier probe design.**
- Problem: The probe is moved to `aborted_<ts>`, but amendment d item 4 puts probe outputs at `probe_pre/{a,b}`. The decision doesn't say whether the three other registered probes (five runs remain) are voided or only deferred, or that `probe_pre/a` is absent. Nothing records that bookend probes (item 7) have no `probe_pre/a` to compare against.
- Evidence: Amendment d item 4 (output paths, six runs) and item 7 ("bit-identical to probe_pre/a").
- Fix: State that `probe_pre` is incomplete and that item 7 can't be met for dtmoe until the probes are done. Any dtmoe output produced later stays "unverified" under item 8.

**4. An unverified numbers claim sits in the evidence.**
- Problem: The decision says the grid is "≥150 GPU hours" and "远超本地 GPU 预算". The observation says 180 GPU-hours, from a 51-minute run against a 71–75 s reference. No local GPU budget is cited in the amendment, and the 40x figure comes from a single probe that has not finished.
- Evidence: The observation says "at least ~40x" and "likely" fallbacks. The stack snapshot is not yet taken. The decision's "已知下界已足够" rests on an unmeasured slowdown that may include CPU contention from the 12-lane extension. The decision itself says it cannot exclude this.
- Fix: Cite the numbers as an estimate with its basis. Record the extension's CPU load at both the 12:48 and 21:0x reference runs and at the current run. Remove "远超预算" unless a budget is written somewhere.
