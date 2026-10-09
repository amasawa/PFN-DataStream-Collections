**Rebuttal verdict: Partly answered.**

**Reasons:** The central timing concern is answered. Section 4 now explicitly scores cached predictions before updating contexts, assigns new experts the median loss, and preserves merged experts’ identities and losses. Crucially, the slow level scores the actual default and fast-mixture predictions. These adaptive sequences are compatible with Theorem 2; recomputing their predictions after observing the scored labels would not be.

The provenance statement is sufficiently bounded for this paper-only review: reported results come from causal replays, the cache-generating runs emitted a different mixture, and the theorem’s coverage excludes the stated alternative loss/step configurations. This is a disclosed provenance claim, not independent verification of execution.

However, initialization remains inconsistent between the prose and Algorithm 1.

**Remaining required changes for this issue:**

1. **Severity:** P2 Minor. **Finding status:** Confirmed issue.  
   **Location:** Section 4, Timing paragraph and Algorithm 1, caption and steps 1–4.  
   **Evidence:** The prose specifies uniform weights and \(L_{0,k}=0\) at \(t=1\), but the algorithm unconditionally requests batch-0 predictions and updates \(L_{0,k}=\gamma L_{-1,k}+\ell^k\). Neither \(L_{-1,k}\) nor the warm-up predictions are initialized; scoring batch 0 also need not produce uniform fast weights.  
   **Why it matters:** The first prediction and the starting point of the theorem’s loss sequence remain ambiguous.  
   **Recommended correction:** Add an explicit warm-up/initialization branch defining initial window contents, pool and segment-buffer state, and whether warm-up rows count toward segment closure. Reconcile that branch with uniform first weights and zero slow losses; specify that ordinary cached-prediction scoring begins at \(t=2\).

**Updated overall score: 5 — borderline accept**, conditional on the separately reviewed issues. For this issue, the distance to acceptance is one precise initialization correction.

**Does any remaining gap require a change to the method itself? No.** The identified gap requires a consistent specification of the intended initialization.