**Rebuttal verdict: Answered.**

**Reasons:**

1. The deployed–oracle difference is now explicitly an aggregate departure. The paragraph no longer assigns its magnitude to individual components without a decomposition.
2. First-batch weighting is specified: weights use the preceding concept’s last batch. The stored expert’s weight is negligible but not mathematically zero; equal measured accuracies on all 72 recurrence-first batches establish the reported **empirical** zero.
3. “Nearly exact identification” has been replaced by informative agreement measurements: 100% for accuracy gaps above 10 points, 90% for gaps of 5–10 points, and 0.87 gap-weighted agreement overall. The 0.03-point cost is explicitly net of batches where mixing improves on both experts.

Together with the oracle experiment’s 0.37-point mean absolute prediction error, these changes adequately address the requested direct measurement. They support the conditional characterisation without establishing that its identification assumptions hold universally.

**Remaining required changes for this issue: None.**

**Updated overall score: 5/8 — borderline accept.**  
The measurement objection is resolved, but I would retain 5 rather than move to 6. The learning-curve characterisation, direct oracle test, and candid controls provide a credible contribution. The main obstacle to a comfortable ICML acceptance is now the practical method’s dependence on segment alignment. This requires substantive evidence or a methodological improvement, rather than another clarification of the oracle paragraph.

**Single most severe remaining issue for the next round:**

- **Severity:** P1 Major.
- **Finding status:** Confirmed issue within the reported experiments.
- **Location:** Section “Concept-Pure Memory and Boundary Sensitivity,” particularly the shifted-boundary table; the fixed-segment merge rule in the Method section.
- **Evidence:** Prepending 200 rows leaves subsequent recurring blocks unchanged but moves their boundaries inside stored segments. On matched batches, mean gain over reset changes from **+3.09 to −3.67 points**; MICE loses on seven of eight shifted streams. The unmerged archive outperforms MICE on every shifted stream and all twelve misaligned-schedule streams. Both registered robustness criteria fail. The prefix also changes initial history, so these results establish phase sensitivity without uniquely identifying memory contamination as its cause.
- **Why it matters:** The deployed method does not ensure the concept-pure memory required by its principal theory. Its strongest practical recall advantage therefore depends on a favourable relationship between unknown concept boundaries and an arbitrary segmentation origin. Explicitly acknowledging this limitation improves the paper’s credibility but does not resolve the methodological weakness.
- **Concrete fix:** Develop and freeze a boundary-robust segmentation or memory-update rule, then evaluate it on fresh concept draws with several independently chosen boundary offsets and variable block lengths. Compare against reset and the unmerged archive under stated resource budgets, preserving the current failures as results of the original method. Establish that useful recall gains survive without favourable alignment.

**Does any remaining gap require a change to the method itself? Yes**—to resolve this practical robustness weakness. The round-11 measurement issue itself requires no method change.