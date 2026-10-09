**Rebuttal verdict: Partly answered.**

**Reasons:** The revision substantially addresses the scientific concern. The archive and snapshot controls use identical windows and aggregation without discrepancy-based merging. The authors acknowledge that the archive improvement criterion failed (+0.30 versus +0.50 points), report near-zero mean differences on real streams (+0.07/−0.08), and appropriately withdraw the claim that discrepancy-based organisation explains the recall gain.

The real-stream table supplies paired differences and pointwise uncertainty, with useful qualifications about descriptive thresholds and retrospective analysis. However, grid uncertainty is missing, actual storage remains unmeasured, and a shared pool-size cap does not establish matched total call budgets. These are remaining requirements of this issue, independently of the later latency benchmark.

**Remaining required changes for this issue:**

1. **Severity: P1. Finding status: Missing information.**  
   **Location:** “Pool controls”; Tables `tab:poolgrid` and `tab:poolreal`.  
   **Evidence:** MICE’s stored-row counts were not recorded; storage is bounded using per-expert caps. Snapshot resource figures are omitted or approximated. MICE additionally incurs discrepancy calls.  
   **Why it matters:** The paper establishes shared capacity limits and some observed call counts, but incompletely documents the requested resource-controlled comparison.  
   **Recommended correction:** State each policy’s total storage and call budget explicitly, including discrepancy overhead, and report actual per-stream storage and calls for all three policies. Distinguish measurements, reconstructed counts and bounds. This does not require waiting for latency measurements.

2. **Severity: P1. Finding status: Confirmed issue.**  
   **Location:** Table `tab:poolgrid`.  
   **Evidence:** Per-stream paired differences are present, but no uncertainty accompanies either comparison.  
   **Why it matters:** Two seed-specific point estimates cannot establish the precision of the small archive differences or the snapshot advantage.  
   **Recommended correction:** Add paired uncertainty for both grid comparisons, specifying its inferential scope and accounting for temporal dependence; report uncertainty for the criterion-relevant aggregate.

3. **Severity: P2. Finding status: Confirmed issue.**  
   **Location:** Conclusion and pool-table captions.  
   **Evidence:** The conclusion still calls MICE the “most accurate in-context policy on 23” streams, although it beats the snapshot control on only 11. Registration distinctions are clearer in the paragraph than in the real-stream table caption.  
   **Why it matters:** Readers could interpret the ranking as including the newly added controls or mistake retrospective comparisons for independent confirmation.  
   **Recommended correction:** Restrict the ranking explicitly to the four original baselines, and label each control comparison and uncertainty analysis by registration status in its table or footnote.

**Updated overall score: 5 — borderline accept.** On this issue, the paper is close: the substantive interpretation is now appropriately restrained, but targeted experimental reporting and wording corrections remain. This assessment excludes the ongoing latency issue.

**Does any remaining gap require a change to the method itself? No.**