**Score: 4 — borderline reject.**

**Overall assessment:** The paper offers a useful learning-curve perspective and substantial empirical evidence, with appropriately candid restrictions on its claims. Excluding pending item (2), the principal remaining concern is whether the algorithm’s loss calculations actually match the prediction sequence covered by its guarantees.

**Distance to TKDE acceptance:** Potentially one substantive clarification away, if the frozen method scores previously issued predictions. The manuscript currently leaves this essential detail unresolved.

**Issue (Severity P1): Expert-loss timing is underspecified, preventing verification of the algorithm–guarantee correspondence.**

**Finding status:** Missing information; this is not a finding of confirmed experimental leakage.

**Location:** Section 4, Algorithm 1, steps 2–5; `main.tex` lines 408–416. Related definitions: Section 3.4, lines 336–351.

**Evidence:** Algorithm 1 first inserts batch \(t-1\), including its labels, into the windows and potentially into the pool. It subsequently computes expert losses on that same batch. It never specifies whether these losses score cached predictions issued before those labels arrived or predictions recomputed using the updated contexts. Under the latter interpretation, the 100-row window contains the entire scored batch. The paper itself recognizes context memorization when requiring cross-fitting for the merge statistic (lines 390–391). Moreover, newly created experts have no previously issued prediction on that batch, yet step 3 assigns losses to every current expert without an initialization rule.

For the slow level, Theorem 2 requires losses of the actual default and fast predictions used at the corresponding round; retrospective predictions from updated states cannot simply substitute for them.

**Why it is the most severe:** This ambiguity concerns the operational definition of both weighting levels and the applicability of a central guarantee. It could be a documentation omission, but the paper alone cannot establish that.

**Required fix:** Specify prediction caching, the exact score/update order, expert identity across merges, and loss initialization for newly created experts. Explicitly connect the slow-level losses to the predictions previously issued. This is feasible without changing the method if it already follows that convention. If it uses retrospective slow-level losses, documenting the frozen method requires withdrawing the unsupported application of Theorem 2; recovering that guarantee through the stated update rule would require a method change.

**Confidence:** High that the specification is incomplete; implementation behavior remains unknown.