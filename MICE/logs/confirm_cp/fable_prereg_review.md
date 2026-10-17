**Decision**: Not as is. One evaluator defect contradicts PLAN.md and must be fixed before commit; two disclosure sentences should be added. After that, commit and run. One optional hypothesis change needs the user.

**Supporting evidence** (6 points)

1. **Evaluator bug, H2 scope.** The per-stream loop at `analyse.py:73` runs over primary plus supplementary segments, and fills the FIFO lower-bound dict for all of them. H2 at `analyse.py:94` then takes `all()` over that dict, so the two PokerHand segments can fail H2, contrary to PLAN ("primary segments"). The H1 "value" string at `analyse.py:91` also averages the supplementary differences, while the H1 lower bound uses primary only, so the printed mean and bound would disagree. The CC_TEST dry run empties SUPP and cannot catch this. Fix: restrict both to STREAMS.

2. **Segment selection is label-based and pre-run, so it is legitimate, but the CIC rule has a direction.** The most-mixed aligned block is the block most likely to contain an attack onset or offset inside it, which is exactly where a detector should beat fixed segments. H1, H3 and H4 are therefore tested on ground tilted toward mice_cp and ddm on CIC, and neutral on Bitcoin. Add one sentence to the Data section stating this, and the paper must not call the CIC segments representative. The Bitcoin year choice only excludes degenerate years and is disclosed adequately.

3. **H1 bootstrap matches PLAN and is a valid one-sided noninferiority test, conditional on the nine segments.** block_means draws ⌈999/20⌉ blocks per resample and truncates, the nine resample vectors are averaged elementwise, and the 5th percentile is taken. Because between-segment variance is not resampled, the standard error is roughly one third of a per-segment one, so the −0.2 margin, not the uncertainty, is the operative constant. State "on these nine segments" in the paper. Block 20 equals 2,000 rows. CIC attack bursts are autocorrelated over longer spans, so add block 50 as a descriptive sensitivity, as noninferiority.py already does, with no decision attached.

4. **H2 through H5 match the PLAN text.** Strict inequalities, max over the four context baselines is equivalent to "above each", need equals 6, per-source means via groupby. H3 has no uncertainty and takes the better of two baselines, which biases against mice_cp. That is conservative and acceptable.

5. **Near-majority segments make H4b and H5 fragile.** Bitcoin 2013 and 2015 sit at 99.6% majority. Exact ties count as failures, so the effective rule becomes 6 of 7 informative segments. This is disclosed as expected difficulty, which is sufficient to run.

6. **Binary-only set.** All nine primary segments are binary after grouping, so this confirmation says nothing about multi-class behaviour of the detector. Add one sentence saying so. CIC Wednesday and Friday blocks (DoS, DDoS) are near-trivially separable and will likely sit above 99.5% for every method. That is low power, not uninterpretable.

**Alternative options**
- For H4b and H5, pre-specify that exact ties count neither way and require ⌈2m/3⌉ of the m untied segments, with m ≥ 7 for the hypothesis to be decidable. Cleaner, but a hypothesis change.
- Keep the registered strict rule. My recommendation, since the fragility is already disclosed and the result is honest either way.

**Key risks**
- Bitcoin within-day order. The stable sort keeps file order within a day. If the UCI file lists ransomware rows before white rows, each day's ransomware rows land at the start of the day, producing an artificial periodic label cluster roughly every ten batches. This does not break the comparison, but it should be disclosed. I was not permitted to read the raw file, so verify with one command (first line number of a white row versus first ransomware row) before committing.
- A segment with a NaN batch in any run file trips the identical-batches assertion and halts evaluation. Intended, but plan the fallback.

**Remaining uncertainty**
- The raw file order above.
- Whether the ddm and ltm probability arrays begin at batch 1 as `analyse.py:57` assumes. Descriptive metrics only, not a hypothesis.

**Confidence**: High on points 1, 3, 4 (read the code). Medium on the direction of the CIC selection effect and the Bitcoin ordering artifact.

**Requires user approval**: Only the tie-rule change for H4b and H5. The H2 fix, the block-50 sensitivity, and the three disclosure sentences follow from PLAN as written and need no decision.
