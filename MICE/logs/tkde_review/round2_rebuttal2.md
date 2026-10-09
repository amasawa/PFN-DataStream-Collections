**Rebuttal verdict: Partly answered.**

**Reasons:**

- **Resource accounting is substantially improved but incomplete.** The paper specifies context caps and discrepancy overhead, including the maximum of 29 calls on a closing batch. Real-stream storage clearly distinguishes bounds from exact reconstructions. However, `tab:poolgrid` supplies no per-stream storage figures, and `tab:poolreal` substitutes “within 0.6” of archive calls for actual snapshot-policy calls.
- **Grid uncertainty is substantially answered.** Both comparisons now have per-stream intervals and criterion-subset aggregate intervals, explicitly labelled retrospective. The archive difference of **+0.30 points [ +0.12, +0.41 ]** supports a small positive difference while clearly failing the registered +0.5-point criterion. The bootstrap description should explicitly confirm that identical batch indices are used for both policies within each comparison.
- **Claim restriction is answered.** The conclusion limits the ranking to the four original in-context baselines and disclaims attributing recall gains to discrepancy-based merging. The pool-control discussion distinguishes registered criteria, secondary controls, retrospective intervals, and the real-stream snapshot comparison registered after examining results. These remain comparisons between complete policies, as the authors now acknowledge.

**Remaining required changes for this issue:**

1. **Severity:** P2 Minor, given the narrowed claims.  
   **Finding status:** Missing information.  
   **Location:** “Pool controls,” `tab:poolgrid`, `tab:poolreal`.  
   **Evidence:** Grid storage is absent; real-stream snapshot calls are only bounded relative to archive calls.  
   **Why it matters:** Readers still cannot compare storage and inference usage for every policy on every stream.  
   **Recommended correction:** Complete those entries, retaining explicit measurement/reconstruction/bound labels. Where exact storage is unavailable, report defensible per-stream bounds and say so.

2. **Severity:** P2 Minor.  
   **Finding status:** Missing information.  
   **Location:** Grid bootstrap description.  
   **Evidence:** Moving-block resampling is specified, but within-stream pairing is not explicit.  
   **Why it matters:** The requested uncertainty concerns paired policy differences.  
   **Recommended correction:** State whether aligned per-batch differences were resampled, and how replicates were combined for the eight-stream criterion aggregate.

**Updated overall score: 6/8**, up from 5/8. Close to acceptance on this issue, with a bounded reporting revision remaining. This assessment excludes the pending resource/latency benchmark.

**Does any remaining gap require a change to the method itself? No.**