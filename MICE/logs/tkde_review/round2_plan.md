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

## Revision after the Codex expert (round2_expert_a1.md), accepted by Claude
- Alternative A, refined: "no cost" is stated as passing the registered mean-accuracy criterion (+0.07, 18/29
  positive), not as equivalence or absence of individual losses; the large recall gains are restricted to the tested
  conditions with sufficiently pure stored segments.
- Contribution (2) keeps the discrepancy as theory: blind spot of R-divergence under conflicting concepts and the
  excess-risk repair under the stated assumptions, with evidence on controlled segment pairs; separated from the
  practical merge statistic, and explicitly not evidence that merging improves streaming accuracy over an archive.
- Contribution (3) becomes a concrete description: a training-free mixture of window and stored-context experts under
  a two-level aggregation rule, with discrepancy-based pool organisation. Contribution (4) and the abstract state the
  failed archive-improvement and misalignment criteria and scope superiority claims to the named comparators.
- Expert calls only as secondary description, with exceptions (checked by Claude: fewer calls than the archive on 8/8
  aligned grid streams and 25/29 real streams, not on CoverType, h2_poker, h2_rialto, h3_covertype_b; wall time lower
  on 20/29 real streams, measured under concurrency).

## Plan v2 after the reviewer's plan check (round2_reviewer_plan_check.md: "Partly satisfies"), Claude's judgement
Accepted: (1) snapshot control missing on the real streams and its budget not specified -> run snap1000_500 on the
29 real streams (new run, registered below before it starts) and state the budgets exactly; (2) per-stream paired
results with uncertainty -> per-stream table (grid and real) and moving-block-bootstrap one-sided 95% bounds for
MICE - arch and MICE - snap on the real streams, as in the RQ3 non-inferiority analysis; (4) registration status per
comparison -> each comparison labelled "registered before the run" or "exploratory (after results)", with streams
reused from earlier analyses identified as such; wording: "pool" = adding the stored-context pool improved the tested
configuration, not isolated concept recall; "sufficiently pure segments" = the tested favourable regime, not an
established cause; archive differences are differences between complete policies.
Partly accepted: (3) resources -> report exactly what is recorded: mean and maximum active experts per batch (from the
cached predictions), total TFM calls per batch including the discrepancy calls at segment closes (the call counter
counts every TFM fit+predict), and stored rows: archive 500 rows per stored expert, snapshot up to 1000, MICE up to
1000 per stored expert (only the cap is known for MICE; per-expert row counts were not recorded). Wall time only as
descriptive (runs shared the GPU). The contradictory CoverType sentence in plan v1 is corrected: MICE uses more calls
than the archive on covertype, h3_covertype_b, h2_poker and h2_rialto.

## Registration draft (to be appended to experiments/mice_tkde_control/PLAN.md before the run)
- Run: snap1000_500 on the same 29 real streams, backbone seed 0, same rule and constants; MICE values are the
  paper's existing caches; no MICE rerun.
- Reported for every stream: MICE, archive, snapshot accuracy, paired differences, one-sided 95% moving-block
  bootstrap lower bounds (blocks of 20 batches, 10 000 resamples; 10 and 50 as sensitivity), active experts, calls.
- Criterion (descriptive companion to criterion 2, fixed now): MICE - snap mean over the 29 real streams >= -0.1
  points. Exploratory analyses remain labelled as such.
