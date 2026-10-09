**Rebuttal verdict: Partly answered.** The mathematical objection is resolved, but one summary sentence remains overbroad.

**Reasons:**

- Proposition 1(iii) correctly requires uniform, source-independent tie-breaking and averages risks **before** taking their absolute difference.
- The deterministic expression correctly establishes \(D_R\le\rho\), retains dependence on the disagreement region and tie choices, and makes no unsupported claim that every intermediate value is attainable. The appendix’s endpoint examples are valid.
- The experimental paragraph appropriately distinguishes the finite-context empirical comparison from the population proposition.

**Remaining required changes for this issue:**

1. **Severity:** P2 Minor.  
   **Finding status:** Confirmed issue.  
   **Location:** [Remark rem:merge, lines 244–245](main.tex:244).  
   **Evidence:** “it is again zero for randomised ties” omits the necessary qualifications. Randomisation alone is insufficient: on one disagreement atom, selecting the two labels with probabilities \(0.9\) and \(0.1\) gives \(D_R=0.8\).  
   **Why it matters:** The remark still states a broader claim than the corrected proposition establishes.  
   **Recommended correction:** Replace this with “it is again zero under uniform, source-independent random tie-breaking, with risks averaged before taking their difference.”

**Updated overall score and distance to TKDE acceptance:** **5 — borderline accept**, provisional within this bounded review and excluding the separately handled pool-control issue. This objection now requires only a small textual correction; it no longer constitutes a substantive mathematical barrier. This review does not establish that all other acceptance requirements are satisfied.

**Does any remaining gap require a change to the method itself? No.**