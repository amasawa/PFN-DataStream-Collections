**Final score: 3 — weak reject.**  
**Recommendation for TKDE: reject.**  
**Acceptable at TKDE as it stands: no.**

The paper provides useful scientific insight and unusually candid evaluation. However, the completed controls leave insufficient evidence that MICE offers a substantial, robust advance over simpler context policies. My decision concerns the demonstrated contribution, rather than manuscript length.

**Main strengths:**

1. **Useful conceptual analysis.** The learning-curve interpretation explains when recalling stored contexts can outperform relearning. The discrepancy analysis identifies a meaningful failure case, and the discounted aggregation guarantee provides a principled component.
2. **Substantial and transparent evaluation.** The manuscript reports failed hypotheses, boundary sensitivity, pool controls, larger-window comparisons, and the distinction between development and confirmatory evaluations.
3. **Demonstrated benefits in particular regimes.** Gains on difficult aligned recurring concepts are substantial. Real-stream results support protection relative to FIFO 1000, with appropriately qualified non-inferiority evidence and additional backbone evaluations.

**Main weaknesses that determine the decision:**

1. **The central recall benefit is fragile to segment alignment.**  
   **Severity:** P1 Major. **Finding status:** Confirmed issue.  
   **Location:** Section V-B, boundary-alignment experiments.  
   **Evidence:** Both registered robustness criteria fail. On shifted streams, MICE loses to reset on seven of eight, averaging −3.67 points, and the archive beats MICE on every shifted stream. It also beats MICE on all twelve misaligned schedules.  
   **Why it matters:** Unknown concept boundaries are central to the intended application. These results materially restrict the demonstrated usefulness of the proposed pool organisation.  
   **Recommended correction:** Establish a practically identifiable operating regime in which the frozen method remains advantageous without favourable boundary alignment.

2. **The practical advantage over simpler alternatives remains insufficient.**  
   **Severity:** P1 Major. **Finding status:** Confirmed issue.  
   **Location:** Section V-D, pool controls and resource benchmark; Appendix FIFO 3000 comparison.  
   **Evidence:** Merging provides only +0.30 points over the aligned archive, below the registered +0.50 criterion. Real-stream differences against archive and snapshot controls average +0.07 and −0.08 points. FIFO 3000 wins on 21/29 streams and is about 2.5 times cheaper on the benchmark prefixes. MICE nevertheless retains meaningful gains on several strongly drifting streams and uses fewer calls than the pool controls.  
   **Why it matters:** The evidence establishes benefits from retaining contexts more convincingly than it establishes the value of MICE’s particular design. The conditional recall analysis and half-Brier safeguard do not independently establish an accuracy–cost advantage.  
   **Recommended correction:** Demonstrate a convincing accuracy–resource benefit against both simple memory pools and larger windows within the intended deployment regime.

**What would most change the decision, and does it require changing the method or new data?**

Independent evidence that the **frozen method** consistently offers useful accuracy–resource tradeoffs on previously unseen recurring/drifting streams with unknown boundaries would most change my decision. This would require **new evaluation data and experiments, but not necessarily a method change**, with the target regime specified before inspecting outcomes.

Repairing the demonstrated segmentation/merging failure would require **changing the method**. Further wording changes alone would not change my decision; the manuscript already acknowledges the decisive limitations.

**Confidence: high (4/5)** for this manuscript-based assessment. The remaining uncertainty concerns generalisation beyond the reported streams.