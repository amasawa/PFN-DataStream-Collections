**Rebuttal verdict: Answered.**

**Reasons:**

- The generator is now specified sufficiently: centroid and weight distributions, Gaussian noise, independent concept-specific label assignments, recurrence order, block lengths, cycles and seeds. “Four nominal classes” is correctly distinguished from guaranteed class coverage.
- The learning-curve protocol specifies the context/test split, context sizes, repetitions, shared test rows, backbone randomness, averaging and interpolation. It explicitly avoids treating the 18 measurements as independent concept draws.
- The conversion from curves to predictions is now traceable, including recurrence weighting, the original full-memory approximation, the corrected stored-context sizes and the unpredicted first-batch term. Registered predictions remain distinguishable from subsequent corrections.
- The appendix discloses shared random draws and identical feature vectors in the seed-10/11 evaluation. The separately identified sensitivity analysis reports independently sampled rows and largely unchanged predictions. RQ1 appropriately distinguishes prediction for already sampled concepts from transfer to seed-20/21 concepts, acknowledges the two-seed limitation, and explains why comparison with DDM is only an approximate test of the theorem.

These disclosures resolve the reporting issue. They support a limited demonstration of predictive ranking within this generator family, rather than broad validation of prediction accuracy.

**Remaining required changes for this issue: None.**  
No verified issues within the reviewed scope.

**Updated overall score: 5 — borderline accept**, provisional with the separately reviewed pool-control issue excluded. This issue no longer creates distance to acceptance; the manuscript’s broader acceptance case remains constrained by the demonstrated boundary-alignment sensitivity and limited independent concept draws. Resolving the present reporting concern does not itself establish that those broader limitations are acceptable for TKDE.

**Does any remaining gap require a change to the method itself? No**, for this issue.