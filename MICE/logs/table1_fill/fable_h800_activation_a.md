**Decision**
P1–P5 are sound in structure. Reactivate, with four mandatory changes: correct the draft's now-false DR statement, stop the local DR run at H800 DR launch rather than after the probe, record the option list behind "选A", and get explicit user confirmation for moving dtmoe back off the CPU. Do not move the CPU baselines.

**Supporting evidence**
- PLAN.md lines 22–23 state that Drift-Resilient TabPFN "is not run on the local GPU (no local output exists; none would be merged)". That is false now (13/92 local streams exist under amendment d). An activation note that reactivates the draft verbatim would register a false premise. The note must say: local DR outputs exist, are kept, never merged, reported run = H800.
- Amendment d item 1 and amendment e item 1 both quote explicit user decisions ("do not use the H800 for now"; "选1，CPU 上跑"). The new quote "选A 整个mice 重新跑" reverses the first clearly. It reverses the second only by implication, since "整个 MICE" was the draft's scope and the draft included dtmoe. That inference is reasonable but the dtmoe CPU decision was the later, more specific one. Specific beats general unless the user says otherwise.
- The quote appears in no committed file. The activation note must reproduce the options offered (A/B/…) verbatim, otherwise "选A" is uninterpretable to a reviewer.
- tasks.jsonl and MANIFEST.md are frozen at 959aae3; code unchanged; the table1-fill outputs live in a separate root, so the task list stays valid. Do not regenerate it.
- CPU baselines were never GPU-exposed. Moving them changes timing hardware for no integrity gain. Keep them local and state mixed timing hardware in the appendix.

**Alternative options**
- Stop local DR now instead of at H800 launch. Cleaner, costs nothing of value (the suspect GPU's output is "GPU local, unverified" at best), frees the GPU. I prefer this.
- Keep dtmoe on CPU (amendment e) and mark the 180 dtmoe_dev tasks "not executed, superseded by amendment e". Valid if the user prefers; must be written before any H800 dtmoe output exists.

**Key risks**
- Public repo: HANDOFF.md already carries the SSH port and path pattern. Grep for account names, OneDrive links, and SHA sums of weights before pushing the activation note.
- The strict deterministic dtmoe probe that stalled 54 min locally may stall on the H800 too. P3 needs a registered failure rule (reuse amendment d item 4 wording) and the fallback stays the user's call.
- TabICL checkpoint and wheels downloaded on the Mac mini must have SHA256 recorded in the bundle's SHA256SUMS, or provenance of the backbone breaks.
- Trigger "stop local DR when the H800 probe passes" is result-dependent. Use a time trigger (H800 DR production start) instead.

**Remaining uncertainty**
Whether option A as presented to the user named dtmoe or Table 1 baselines at all. Whether the cluster has internet (affects wheel set completeness).

**Confidence**
High on P1, P2 (amended), P4, P5. Medium on P3 pending user confirmation.

**Requires user approval**
1. dtmoe device: H800 strict mode (draft) or stay CPU (amendment e). One yes/no.
2. Confirm "整个 MICE" includes the Table 1 GPU baselines (DR, dtmoe) and excludes CPU baselines.
3. Stopping local DR at activation versus at H800 launch (I recommend now).
