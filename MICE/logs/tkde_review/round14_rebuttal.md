**Rebuttal verdict: Partly answered.**

**Reasons:**

The empirical boundary-phase failure is substantially resolved. The replacement constructs segments causally from previously issued window predictions, with frozen detector settings and delayed closure. The unused-seed confirmation reports gains over reset of **+5.07, +1.35 and +1.64 points** in the three length regimes, with respective hierarchical 95% lower bounds **+4.31, +1.20 and +1.48**. All 72 streams improve. Resampling concept-draw seeds before offsets addresses the requested experimental unit, although four seeds per centroid count still limit generalisation.

The original failures and oracle realignment are preserved. The seed reuse is disclosed, and the separately registered confirmation supplies substantially stronger evidence than the retrospective unused-seed subset.

However, two requirements remain incompletely satisfied. Majority purity does not establish the pure-context learning-curve theorem, despite language suggesting that it does. Also, the revised method has a same-segmentation archive comparison in expert counts and TFM calls, but its operational timing and memory comparison—and its comparison against the snapshot alternative—remain incomplete.

**Remaining required changes for this issue that do not change the method:**

1. **Severity: P1. Finding status: Confirmed issue.**  
   **Location:** “Which Rows Form a Concept,” “Segment Purity and Boundary Phase,” and the appendix purity verdict.  
   **Evidence:** The paper explicitly acknowledges that the majority-purity proposition supplies no finite-context learning curve and that the recall theorem assumes pure contexts. Nevertheless, it describes the theorem’s premise as having a “majority form” and says detected segmentation supplies that premise. The registered near-purity threshold fails: 88% initially and 87% on confirmation, versus 90% required.  
   **Why it matters:** Population classification under deterministic, equal-marginal concepts does not establish the accuracy of a finite contaminated context or the stated area formula.  
   **Concrete fix:** Keep the recall theorem explicitly conditional on pure contexts throughout. Present majority purity as a restricted population identification result and the new gains as empirical evidence of contamination tolerance. Separate detection, boundary localisation and stored-context purity rather than implying that one guarantees all three.

2. **Severity: P1. Finding status: Missing information.**  
   **Location:** “Archive and resources,” protocol “Segmentation,” and the resource tables.  
   **Evidence:** The detected method uses 6.26 calls and 2.42 stored experts versus the archive’s 10.64 and 7.64, but the paper states that all timings use fixed segmentation. The snapshot comparisons likewise concern the original segmentation.  
   **Why it matters:** Calls with different context sizes and discrepancy workloads need not have equal cost. The original snapshot control was competitive precisely where fixed segmentation failed.  
   **Concrete fix:** Benchmark the frozen detected method against the archive using identical detected segments, reporting end-to-end latency, retained rows and peak memory alongside accuracy. Include the snapshot control on the unknown-phase and irregular schedules, with explicitly stated storage and timing budgets. Preserve the existing results separately.

**Updated overall score: 4 — borderline reject.**  
The paper now has credible evidence for causal recall under unknown phases, useful failure analysis, and substantial controls. It is close to borderline acceptance, but the theoretical interpretation and revised-method resource evidence still need a focused correction and validation round. The broader contribution remains promising but chiefly established on a controlled generator; real-stream gains are modest and a cheaper larger window often wins.

**Single most severe remaining issue for the next round:** Not applicable—the current issue is not fully closed.

**Does any remaining gap require a change to the method itself? No.** The required work concerns claims, comparative evaluation and resource measurement.