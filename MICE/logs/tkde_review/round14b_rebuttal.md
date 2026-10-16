1. **Verdict: answered substantively.** Table `tab:cpres` explicitly states “The archive uses the segments of MICE” and reports mean/p95 batch latency, retained rows and peak reserved GPU memory, with archive accuracy cross-referenced to `tab:segsum`. MICE takes **1.07 versus 2.58 s/batch**, retains **1,900 versus 5,200 rows**, but uses **more GPU memory (1.15 versus 0.76 GB)**. The referenced benchmark includes the two-level rule and segment processing.

   Snapshot comparisons cover random-phase confirmation streams, shifted boundaries and misaligned/irregular schedules. Storage rules, capacities and timing selection are explicit—including the failure of either candidate capacity to meet MICE’s latency on every prefix. The twelve-expert control and its long-block accuracy tie are disclosed. Fixed-segmentation results remain separately identified, and the registration appendix documents the added comparison.

2. **Remaining change: P2 editorial consistency only.**
   - **Finding status:** Confirmed issue.
   - **Location:** Conclusion, “Limitations,” `main.tex:1298`.
   - **Evidence:** “the pool controls and all timings were obtained with fixed segmentation” contradicts the new detected-segment benchmark.
   - **Why it matters:** It misstates which method the resource evidence evaluates.
   - **Concrete fix:** Add “except the detected-segment resource and snapshot comparisons in Table `tab:cpres`,” matching the updated experimental protocol. **No further experiment is required for this issue.**

3. **Updated overall score: 7/8 — accept.** The previously conditional acceptance is now supported by the reported results. The paper is acceptable at TKDE, subject to the minor wording correction above.

4. **Other required issue: none within this bounded rebuttal review.**