**Verdict: Partly satisfies.** The plan resolves most missing parameters, but the claim that curve and stream rows are independent remains unsupported. I checked the manuscript; the result-producing code is not present in this directory.

Before revision, address these three items:

1. **Establish the actual random-number relationship.** “Same generator and seed” does not establish “fresh rows.” Reinitializing the generator can replay draws after generating the same concept definitions; changing requested block lengths does not establish independence either. Document the actual initialization, continuation, or substream mechanism and verify overlap between curve samples and stream samples. Distinguish disjoint rows from independent sampling conditional on the concept definitions. If overlap occurred, disclose it and reconsider the “documentation only” judgment.

2. **Specify how curves become reported predictions.** Give the aggregation order: whether curves are averaged before applying the positive-part area formula or gains are computed separately and then averaged; how first visits and subsequent cycles are weighted; and how stream gains are aggregated into the six points used for Spearman correlation. State explicitly that the same 1,000 query rows are reused across context sizes and repetitions, if so. The 18 measurements per size are not 18 independent concept draws.

3. **Describe four nominal classes, without implying guaranteed coverage or balanced priors.** Independent centroid labels can leave classes absent, particularly with five centroids, and class probabilities depend on the sampled weights and labels. Clarify whether any rejection or coverage constraint exists. Replace “permuted” consistently and avoid implying that every centroid changes label between concepts.

**Consequences for claims:** Even if rows are independently sampled, the seed-10/11 result is prediction for already sampled concept definitions using additional labeled data from those concepts. It does not establish transfer to unseen concepts. The seed-20/21 result supplies the evidence for transfer to new concept draws within the same generator family, with only two data seeds. Reflect this distinction in RQ1 and qualify “measured before deployment” by its requirement for representative labeled concept data. Shared concept definitions alone do not invalidate the experiment.

No new experiment is necessary if the documented sampling mechanism supports the stated independence. If it does not, revised interpretation or a separately approved confirmatory test is needed.

**Confidence:** High on these requirements; sample independence remains unverified. **User approval:** Required for any consequential amendment to the frozen experimental protocol.