I could not read the DUO expert code (read permission to `/home/zhwu9808/pfn-runs/...` was denied), so the decision is based on PLAN.md alone. Two implementation points below are therefore flagged as checks rather than verified.

**Decision**

1. **One uniform draw per batch is sufficient as the primary control.** Each stream already averages 300 independent draws, so the Monte Carlo component of a per-stream mean is about 1/√300 of the per-batch spread. Add two extra rng seeds only on the 6 K=3 mechanism streams (12 tasks, under 30 min) and report the between-draw SD of the stream mean next to Δ. On held-out, the rng is already seeded by backbone seed, so the 3 seeds give 3 distinct draws per prefix. No further draws needed.

2. **Keep R1's sign-and-interval part, drop the K=3 > K=15 ordering from the pass condition.** The ordering was inherited from the DUO-vs-MICE gains, but the sel-vs-rand contrast need not be monotone in K: at K=3 a uniform draw already lands about 3 of 9 slots on the current concept, at K=15 under 1 slot, so the context-quality gap is not obviously larger at K=3. Report the ordering descriptively. Change the inference unit: the claim generalises over streams, so the primary interval should be stream-level (paired t over the 6 per-stream means, plus the count of positive streams, 6/6 gives one-sided sign p=0.016). Keep the moving-block bootstrap as a per-stream complement, but use block length near the concept segment length (or ~17 ≈ √300), with a sensitivity at 10 and 30. Blocks of 10 will under-cover if segments are 30 batches long. Make Δ_ll co-primary with the same sign requirement.

3. **Held-out: one-stage cluster bootstrap over sources is right**, resample sources with replacement and keep every prefix of a chosen source intact. The two-stage variant adds within-source noise that the cluster means already carry. First average the 3 seeds per prefix, then bootstrap once, and report the between-seed SD separately, instead of per-seed intervals. If there are fewer than about 6 sources, the cluster bootstrap is unstable; then report a per-source table of Δ and the sign across sources, and state that no interval is claimed.

4. **Missing items, in order of likely next reviewer ask:**
   - **Selection hit rate** on mechanism streams: fraction of chosen context batches from the current concept, sel vs rand, per K. Concept labels are known, cost zero, and it is the direct "ranking recovers information" evidence. Add it.
   - **sel alone vs rand alone** is the sensitive test (no mixture absorbing the difference). Report it as the mechanism result, with MICE+sel vs MICE+rand as the "usable by MICE" result.
   - **Mixture weight on the extra expert** over time, sel vs rand, from the existing caches. Shows the safeguard working and that sel is used more.
   - **Oracle concept-matched context** on the 18 mechanism streams (18 tasks). Bounds what any ranking could achieve and locates sel between rand and oracle. Recommended if budget allows.
   - **Recency-window context** (last 10 batches) is the next natural null after uniform. Do not run now, but say in the paper why uniform is the pre-registered control and which MICE expert already covers recency.
   - **Runtime** as total seconds per batch for both experts, so sel's ranking cost is the difference.
   - **Sensitivity** restricted to batches where sel and rand actually differ (t > slots + a), since early batches contribute Δ=0.

**Supporting evidence**: PLAN.md lines 12-18 (identical slots, causal rng), lines 32-35 (current interval design), lines 39-44 (R1/R2). DUO gains by level +0.28/+0.15/+0.01 are gains over MICE, not sel-vs-rand contrasts, hence the ordering caveat.

**Alternative options**: 3 rng seeds for all 84 tasks (about 3 h GPU) buys little beyond the K=3 replicate. Jonckheere trend test across K is possible but over-engineered for 6 streams per level.

**Key risks**: (a) Context ordering inside the TFM call must be the same convention for sel and rand (chronological for both) if the backbone is order-sensitive. (b) rand must not be re-drawn on cache hits in a way that breaks reproducibility. (c) With the mixture absorbing weak experts, MICE+sel vs MICE+rand may be near zero even when sel alone clearly beats rand alone. Pre-state that the expert-alone comparison carries the ranking claim and the in-MICE comparison carries the deployed-gain claim, so a null in one is not read as a null in the other.

**Remaining uncertainty**: number of held-out sources (determines whether a cluster interval is reportable). Whether MICE already contains a recency-context expert, which decides how the recency objection is answered.

**Confidence**: high on Q1 and Q3, moderate-high on Q2 (the ordering caveat is a reasoning argument, not measured), moderate on Q4 ordering of asks.

**Requires user approval**: the 1-draw plan, K=3 replicates and the zero-cost diagnostics fall under the 2026-10-09 standing authorisation (existing generator and streams, method unchanged). The oracle-context control is a new expert and should be logged and confirmed with the user before running.