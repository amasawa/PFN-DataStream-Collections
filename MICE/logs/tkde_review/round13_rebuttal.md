**Rebuttal verdict: Answered.**

**Reasons:** The new comparison supplies the missing evidence against the closest competitors. Table `tab:poolcap` reports latency, stored rows, calls and GPU memory; selects smaller capacities using timings alone; and evaluates aligned, shifted and real streams.

At capacity 12, the archive and snapshot pools take 2.49 and 2.84 seconds per batch versus MICE’s 1.11 on the measured real prefixes. The timing-selected capacity-2 controls are faster than MICE, yet less accurate on the aligned grid and nine-stream real subset. The shifted-grid snapshot tie is explicitly reported. This establishes a bounded accuracy–latency tradeoff; superiority everywhere was unnecessary. Memory results are mixed: MICE’s reserved GPU memory is higher, 0.99 versus 0.76 GB.

**Remaining required changes for this issue that do not change the method:**

1. Scope the resource claims precisely. “About two stored experts” describes the benchmark prefixes, whereas the full real-stream table reports 8.4 total active experts—approximately 5.4 stored experts after subtracting the three windows. Likewise, describe capacities as *selected to fit the measured prefix budget*, rather than implying equal cost across all evaluated streams or an optimal accuracy–cost frontier.
2. Identify the nine real streams and exact evaluated ranges in the manuscript. Clarify the evaluation-window difference, if any, behind the shifted archive comparison of −2.88 points in `tab:poolcap` versus −2.99 in `tab:offset`.

These are reporting corrections, not grounds for another broad experimental campaign.

**Updated overall score: 4/8 — borderline reject.** The resource objection is substantially closed. The learning-curve characterization, oracle validation, transparent negative results and two-backbone evidence give the paper substance. However, the practical method’s main recall advantage remains strongly dependent on favorable segment alignment, while real-stream gains are modest and a cheaper larger window wins on 21/29 streams. The paper is close to the acceptance boundary, but the remaining obstacle is substantive rather than presentational.

**Single most severe remaining issue for the next round:**

- **Severity:** P1 Major.
- **Finding status:** Confirmed issue.
- **Location:** “Concept-Pure Memory and Boundary Sensitivity,” Table `tab:offset`, and the fixed-segment pool construction.
- **Evidence:** Prepending 200 rows while preserving subsequent observations and recurring-block lengths changes MICE’s mean advantage over reset from +3.09 to −3.67 points. It falls below reset on seven of eight shifted streams, with a worst deficit of 10.75 points. Realigning segments using the known phase restores +3.01 points.
- **Why it matters:** The deployed method does not know this phase. The strongest practical benefit therefore depends on an alignment its memory construction cannot reliably establish. The restoration experiment diagnoses the failure convincingly, but does not solve it. This does not invalidate the conditional recall theorem.
- **Concrete fix:** Establish a causal memory-construction or retention mechanism that tolerates mixed segments without supplied boundary phases, then evaluate it on frozen unseen offsets and irregular schedules against reset and the closest pools, including its resource cost. Alternatively, retain the method and frame the contribution primarily as a conditional characterization; that would narrow the claim without resolving the practical weakness.

**Does any remaining gap require a method change? Yes**, to resolve this boundary robustness failure. The present rebuttal’s reporting corrections do not. A convincing resolution preserving the demonstrated resource tradeoff would likely raise my score from **4 to 6**, conditional on independent evaluation.