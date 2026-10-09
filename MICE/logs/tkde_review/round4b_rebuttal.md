**Rebuttal verdict: Answered.**

**Reasons:** The revision addresses the three substantive requests:

- Test (b) preserves recurring-block lengths and the original evaluated rows, providing a matched boundary-offset comparison. The added initial history is explicitly acknowledged, so the paper appropriately avoids claiming a pure causal effect of segment mixing.
- Both tables report every tested configuration and recurrence-local results. The failed registered criteria are disclosed: the offset comparison changes the mean advantage over reset from **+3.09 to −3.67 points**, with losses on **7/8** shifted streams.
- The abstract, contribution (4), conclusion and Limitations explicitly restrict the large gains to the aligned setting. The unsupported “nearly pure”/“upper end” extrapolation has been removed.

Answering the objection does not restore the original empirical strength: these results establish a substantial limitation of the proposed method.

**Remaining required changes for this issue:**

1. **Severity:** P2 Minor. **Finding status:** Confirmed issue.  
   **Location:** RQ2’s synthesis paragraph and conclusion.  
   **Evidence:** For shifted 500-row blocks with 100 centroids, recurrence-local differences against reset are **−3.9 and −6.3 points**; the positive **+7.3 and +5.7** results occur with 2,000-row blocks.  
   **Why it matters:** “Recall right after a recurrence still helps on hard concepts” obscures the failure on short hard-concept blocks.  
   **Recommended correction:** Specify that recurrence-local gains survive in *some tested misaligned settings*, including the shifted 2,000-row hard-concept blocks, but fail in the shifted 500-row counterparts. Describe the average advantage as failing the registered robustness criteria; test (a) still has a small positive mean.

**Updated overall score: 4/8 — borderline reject.** Excluding the separate pool-control issue, this objection is substantively resolved, with a small wording correction remaining. TKDE acceptance remains uncertain because the strongest recall gains depend on favorable segmentation, while the controlled offset test reveals substantial degradation. The paper now needs to stand on the significance of its explicitly restricted contribution.

**Does the remaining gap require a change to the method itself? No.** The remaining correction concerns interpretation; establishing a broadly alignment-robust recall method would require additional methodological work.