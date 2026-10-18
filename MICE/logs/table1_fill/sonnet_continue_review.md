0.0870966 28.769
1. **dtmoe smoke test (Decision 2, "Optional ≤15 min")**
   - Problem: This runs dtmoe locally on the GPU, which contradicts the same item's "dtmoe: wait. Do not run…". It also reuses the three qualification probes that gpu_verify Amendment b item 1 assigns to the H800 ("qualified before the grid"). A local run of them goes beyond the closed stage and is not registered. The GPU is also not free for it, since the plan's "one GPU process" is the DR run.
   - Contradicts: its own item 2, and gpu_verify Amendment b items 0, 1 and 3 ("The dtmoe stage ends here").
   - Fix: Drop it. Or register it in amendment c as diagnostics only, and get the user's approval before it runs.

2. **TOT 12 h cutoff ("stop and defer")**
   - Problem: PLAN_BASELINES and AMENDMENT_BASELINES register only gate (a), "within the paper's reported spread", and gate (b). A CPU-time cutoff is a new unregistered stopping rule. Its outcome, "defer", is neither the registered "skipped" nor "run".
   - Contradicts: AMENDMENT_BASELINES item 2, "If (a) or (b) fails, tot is reported as skipped with the reason."
   - Fix: Put the cutoff in amendment c, with a stated consequence: tot stays "pending", not skipped. Or drop the cutoff.

3. **TOT gate (b) misdescribed (Decision 4)**
   - Problem: "Gate (b), the dev grid and tests also on CPU" treats gate (b) as the grid. Registered gate (b) is a check that lambda = 0 and the official lambda give different predictions on a development stream. The plan never schedules that check.
   - Contradicts: AMENDMENT_BASELINES item 2, gate (b).
   - Fix: Schedule gate (b) explicitly, on CPU, before the tot dev grid. Describe the grid and tests as separate steps.

4. **"Requires user approval" for skipping tot, versus the registration**
   - Problem: The plan says reporting tot as skipped needs user approval. The amendment already registers that outcome, on the user's instruction, and lists it for the user in the README. The plan also says the DR result stays "unverified", but the approval list is otherwise inconsistent with the registrations.
   - Contradicts: AMENDMENT_BASELINES item 2, and its own "Requires user approval" paragraph.
   - Fix: State that skipping on a failed gate is pre-registered. Reserve the approval requirement for the new 12 h rule or for any change to the gate itself.

5. **Missing registered step: timing and memory**
   - Problem: PLAN_BASELINES requires "seconds per batch and peak GPU memory on the three real prefixes of the MICE resource benchmark". The plan schedules this for no method, including DR, which is the one GPU method run tonight.
   - Contradicts: PLAN_BASELINES, "Execution, order, timing".
   - Fix: Add it to the DR start sequence (before or alongside the canary). Schedule it for the four CPU methods after their tests. Or register it as deferred.

6. **Registration for the frozen configurations**
   - Problem: Selection output is "committed before the first test run", but that commit is only the selection output. Amendment c is also supposed to carry the frozen configurations and the tot CPU change. Decision 1 says DR starts after (5) is committed, and (iii) tests start after (ii), but nothing orders amendment c relative to the first test run. It is also unclear whether the amendment c commit carries the dev scores and the boundary-extension outcome ("extended once").
   - Contradicts: PLAN_BASELINES "Tuning" (grid extended once, then re-select, then one run per test stream), and the "registrations before runs" rule.
   - Fix: State that one commit per method holds the dev scores, any extension, and the frozen configuration, and that it lands before that method's first test stream. Do not batch them.

7. **CPU load against the DR run (Decision 1 versus Key risks)**
   - Problem: The plan starts 10–12 CPU lanes alongside DR. Its own risk note says CPU load has preceded FECS failures before. The only mitigation is reactive: halve the lanes after FECS returns. The result is an 83 h DR run exposed to the known trigger.
   - Contradicts: its own Key risks; Amendment b item 2's principle of avoiding FECS exposure.
   - Fix: Start DR, wait for its canary and the first quiet 30 min, then ramp the lanes up in steps (for example 4, then 8, then 12), logging the lane count against the GPU events. Or cap the lanes at what was previously FECS-clean.
