# Fable 5.1, 2026-10-16 12:15, on round14b_plan.md (draft)

**Decision:** Sufficient in structure; register only after four changes. (a) Keep the fixed snapshot as the sole snapshot control. (b) Add the 2000-row regime stream to A2 and a timing budget for snapshot kmax 12. (c) Rule E is right; add one sentence on separate tables. (d) Add the appendix verdict and a grep-level removal of "majority form".

**Supporting evidence:**
- (a) The reviewer's point is that the snapshot "was competitive precisely where fixed segmentation failed" and needs "no boundary information". A detected-segment snapshot would just be MICE's stored context without recall weighting, confounded with the archive. The no-detector snapshot is the conservative comparison: its budget excludes detector cost, so a MICE win is a win against a cheaper control. State that asymmetry explicitly in the budget line.
- (b) The reviewer's cost concern is context size. A2 times only 500-row and variable blocks; MICE contexts on 2000-row segments are four times larger per call. Add c_b2000_c100_s50_o0 (3 reps). Part C reports snapshot kmax 12 accuracy, but A1 times only kmax 2 and 4. Either cite round 13 snap12 (2.84 s/batch, identical snapshot code and prefixes, say so) or run one rep. The k* rule is unchanged from round 13 and already accepted; re-selection is legitimate because MICE's reference time changed (micecp vs micev).
- (c) Add: new detected-segmentation resource table is separate from the fixed-segmentation tables, never merged, and if snapshot kmax 12 beats MICE it is reported "at higher budget" with the budget ratio.
- (d) Part 1 must also cover the appendix purity verdict ("registered 90% rule failed"), the contributions list and the RQ2 heading; remove "near-pure" and "majority form" everywhere.

**Alternative options:** archcp at k* = 2 on A1 (9 short runs) would give a budget-matched archive point; optional.

**Key risks:** micecp slower than 1.38 s/batch makes snap4 feasible, raising the snapshot's capacity; that is the rule working, report it. CUDA failure storms with 3 workers (round 13 addendum): plan 2 workers.

**Remaining uncertainty:** whether the reviewer wants misaligned-schedule timings too; A1/A2 budgets stated per row should cover it.

**Confidence:** high on (a), (c), (d); moderate on (b) scope.

**Requires user approval:** no; within the standing authorisation. Register the amended plan in PLAN.md before any run.
