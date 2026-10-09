# Round 4, attempt 4.b — plan (Claude, 2026-10-09), after the reviewer's rebuttal review (round4_rebuttal.md: partly
# answered, overall 4/8)

## Judgement
- Item 1 holds: the 4.a streams change block length and boundary alignment together, and the learning-curve theory
  predicts a different recall gain for different block lengths, so 4.a cannot say how much of the drop is due to
  misalignment. This is a reason of design (4.a cannot answer the question), not of an unfavourable result, so a
  redesign 4.b is allowed under workflow v3.
- Item 2 holds: add a table with all 12 4.a streams (MICE, DDM, FIFO, window ensemble, archive; overall and first five
  batches after each recurring switch, for 30 and 100 centroids; per data seed).
- Item 3 holds: say that large gains were demonstrated on the tested aligned grid, while the tested misaligned
  schedules gave smaller gains and favoured the archive; carry this into the introduction; drop "nearly pure" and
  "upper end" as established conditions.

## 4.b design: fixed block length, half-segment offset, paired with the aligned grid
- Streams: the aligned confirmatory grid of the paper (data seeds 20 and 21; 30 and 100 centroids; blocks of 500 and
  2000 rows; K=3; three cycles), regenerated with the same generator and seed but with the first block 250 rows
  longer, so that every later boundary falls in the middle of a 500-row segment. Block lengths of all recurring blocks
  are unchanged. Verified: the generator reproduces the 8 aligned grid streams bit for bit when the offset is zero, so
  centroids and labels are identical; only the rows drawn after the first block differ.
- 8 offset streams x 5 policies (MICE micev1000_500, archive arch1000_500, DDM, FIFO, window ensemble), backbone seed
  0, method frozen, same rule and constants: 40 tasks. Aligned values are the existing seed-20/21 results.
- Registered criterion (same form as 4.a): recall survives a half-segment offset if MICE - DDM is positive on at least
  7 of 8 offset streams and its mean is at least +1.0 point.
- Reported regardless: paired offset-minus-aligned change of MICE - DDM per stream (isolates boundary alignment at fixed
  block length); MICE - FIFO, - window ensemble, - archive; overall and first five batches after each recurring
  switch; per centroid count and block length.
- If the criterion fails: report it, keep the restricted claim, add to Limitations.
