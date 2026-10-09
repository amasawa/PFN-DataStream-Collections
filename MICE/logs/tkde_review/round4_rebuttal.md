**Rebuttal verdict: Partly answered.** The substantive concern is substantially addressed; the remaining gaps concern experimental completeness and interpretation.

**Reasons:** The authors performed a relevant stress test: non-multiple and variable block lengths create mixed segments, and the paper explicitly reports failure of the registered criterion—8/12 wins over reset and only +0.47 percentage points on average. Reporting that the archive wins on all twelve streams is valuable negative evidence. The abstract, conclusion and Limitations now appropriately restrict the large gains. A failed robustness experiment can answer a reviewer’s concern; success is not required.

However, the paper does not describe a separate boundary-offset comparison that preserves block length. Changing block lengths also changes the predicted recall benefit, so the reduction relative to the aligned grid cannot be attributed entirely to segment impurity. Reporting is also incomplete: recurrence-local gains against reset appear only for 100-centroid streams, and the full baseline comparisons are not tabulated. Finally, “established for stored segments that are nearly pure” extrapolates beyond the demonstrated aligned setting: no purity threshold or relationship between purity and performance is established.

The archive comparison supports its observed superiority in these runs. The authors correctly acknowledge that it does **not** isolate merging as the cause.

**Remaining required changes for this issue:**

1. **Complete the robustness protocol description.**  
   **Severity:** P1. **Finding status:** Missing information.  
   **Location:** RQ2, “Misaligned boundaries”; pre-registration appendix.  
   **Evidence:** The random-length distribution, boundary-offset construction and explicit freezing/no-retuning statement for this experiment are missing.  
   **Why it matters:** The reader cannot fully reconstruct the test or determine which alignment effects it separates.  
   **Recommended correction:** State the frozen configuration, exact schedule-generation procedure and registered evaluation rules. Add a paired, fixed-length boundary-offset comparison if retaining an interpretation that attributes the degradation specifically to misalignment.

2. **Report complete overall and recurrence-local results.**  
   **Severity:** P1. **Finding status:** Missing information.  
   **Location:** RQ2 robustness results.  
   **Evidence:** Selected means and ranges replace a complete comparison; recurrence-local results against reset omit the 30-centroid conditions.  
   **Why it matters:** The reader cannot assess consistency across schedules, difficulties and comparators.  
   **Recommended correction:** Add a compact table covering all twelve streams, the requested baselines and archive, with overall and recurrence-local accuracy, the precise recurrence-window definition, and variability across the two data seeds.

3. **Tighten the remaining generalization.**  
   **Severity:** P2. **Finding status:** Confirmed issue.  
   **Location:** RQ2’s final sentence and introduction’s evidence contribution.  
   **Evidence:** “Nearly pure” is unquantified, and “upper end” is not an established bound.  
   **Why it matters:** These formulations imply a broader validated operating condition than the experiment establishes.  
   **Recommended correction:** Say that **large gains were demonstrated on the tested aligned grid**, while the tested misaligned schedules produced smaller gains and favored the archive. Carry that qualification into the introduction.

**Updated overall score: 4/8 — borderline reject**, excluding the separately pending real-stream pool-control issue as requested. The revision materially improves scientific credibility, but also narrows the demonstrated contribution. It remains a substantive revision away from TKDE acceptance: complete this evidence presentation and make the case for MICE’s added value over the simpler archive within its supported operating conditions.