# Round 2 — plan for narrowing the claims (Claude, 2026-10-09)

## Evidence (all pre-registered unless marked)
- Round 2, criterion 1 (aligned grid, seeds 20-21, 8 streams with 30/100 centroids): MICE - archive (`arch1000_500`,
  every closed 500-row segment its own expert, no discrepancy test, no merging, same windows, pool 12, same two-level
  rule) mean +0.295 points (needed >= +0.5), positive 7/8 -> FAIL.
- Round 2, criterion 2 (29 real streams): MICE - archive mean +0.074 (needed >= -0.1), positive 18/29 -> PASS;
  min -0.32 (INSECTS abrupt imbalanced), max +0.94 (Rialto).
- Storage-matched snapshots (`snap1000_500`, latest 1000 rows at every segment close): MICE - snap on the aligned grid
  c30/c100 +3.25 (5/8 positive; +5.0..+9.9 on 500-row blocks, -0.7..-0.9 on c100 2000-row blocks).
- Round 4 (misaligned boundaries, 12 streams): registered recall criterion FAILED (MICE - DDM +0.47, 8/12); archive
  above MICE on 12/12 (0.17-1.84). Exploratory, not registered: MICE - snap -0.42, 5/12 (MICE wins on 700-row
  blocks, loses on 1300-row and variable blocks).
- Expert calls per batch: grid MICE 6.2-6.5 vs archive 7.1-12.9; real MICE 4.6-17.4 vs archive 8.0-14.7 (fewer on
  CoverType/Airlines/INSECTS, similar or more on Rialto/Poker).
- Unchanged: removing the pool lowers accuracy on 24/24 grid streams (-5.6) and 28/29 real streams (-0.35); the
  excess-risk discrepancy separates same/different-concept segment pairs with AUROC 1.00 vs 0.85 for R-divergence.

## Proposed change (method frozen; only claims and reporting change)
1. Source of the gain: attribute the recall gain to keeping past contexts as in-context experts under the two-level
   rule (the pool), not to concept identification or merging.
2. The excess-risk discrepancy stays a theoretical contribution (blind spot of R-divergence and its repair, verified
   on segment pairs), and merging is described as one way to organise the pool. Measured effect versus an unmerged
   archive: +0.3 points on aligned recurring concepts (below the registered +0.5), no cost on real streams (+0.07),
   fewer expert calls on some streams; worse than the archive when boundaries are misaligned.
3. New paragraph and table in the ablation section, "Pool control", with both registered criteria and their verdicts,
   the snapshot control, and calls per batch; labelled as added in response to review, registered before the run.
4. Abstract, Approach, Contributions, Conclusion and Limitations: remove or qualify every sentence that credits
   concept identification or merging with the gain; add the archive result to the Limitations.
5. No new experiment. The method, constants and all earlier results stay as they are.
