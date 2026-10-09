# MICE review control: does merging by discrepancy add value beyond an archive of past contexts? (2026-10-09)

Added at the TKDE review stage (Codex reviewer, round 2), after all MICE results were known. Frozen before running.
The MICE method is unchanged; this only adds controls.

## Controls (MICE/code/run.py, class PoolControl; identical windows 100/300/1000, pool size 12, constants and the
two-level rule simulate2(outer='brier', scale=.5, temper=True))
- **arch1000_500** (primary): every closed 500-row segment becomes its own expert, no discrepancy test, no merging;
  the oldest expert is evicted beyond 12.
- **snap1000_500** (secondary): every closed segment stores a snapshot of the latest 1000 rows (storage matched to
  MICE's 1000-row experts); oldest evicted beyond 12.

## Streams and runs
- Grid with recurring concepts, the confirmatory seeds 20 and 21 of the paper (12 streams), backbone seed 0, as MICE.
- The 29 real streams of the paper (arch only), backbone seed 0, as MICE.
- MICE values are the paper's existing micev1000_500 results with the same rule; no MICE rerun.

## Reported (all, per stream and averaged)
Paired difference MICE − control in accuracy points; expert calls per batch and wall time per batch.

## Decision, fixed now
- **Merging adds value on recurring concepts** if, on the 8 grid streams with 30 or 100 centroids, MICE − arch has
  mean ≥ +0.5 points and is positive on ≥ 6 of 8 streams.
- **No cost on real streams** if MICE − arch has mean ≥ −0.1 points over the 29 real streams.
- If the first criterion fails, the paper's claims about concept identification are narrowed to "a pool of past
  contexts under the two-level rule", and the discrepancy-based merging is described as one way to organise the
  pool, not as the source of the gain. Results are reported either way.

## Round 4 addition (frozen before running): boundaries not aligned with the 500-row segments

Codex reviewer, round 4: every controlled grid concept lasts 500 or 2000 rows from row 0, so each closed segment
holds one concept. Streams (`make_misaligned.py`, fresh data seeds 30 and 31, 30 or 100 centroids): fixed blocks of
700 rows, fixed blocks of 1300 rows, and variable blocks drawn from {500, 600, ..., 2500} rows; K=3 concepts, nine
blocks; 12 streams. Methods: micev1000_500 (MICE, two-level rule replayed as in the paper), arch1000_500,
ddm1000, fifo1000, winens1000; backbone seed 0.

Decision, fixed now:
- **Recall survives misalignment** if MICE − DDM is positive on at least 10 of 12 streams and its mean is at least
  +1.0 point.
- Reported regardless: MICE − FIFO, MICE − window ensemble, MICE − arch, per condition and centroid count, next to
  the aligned grid (seeds 20 and 21) for comparison; accuracy in the first five batches after each recurring switch.
- If the criterion fails, the contribution is restricted in the paper to conditions where stored segments are
  sufficiently pure, and the misaligned results are reported as a limitation.

## Exploratory addition (2026-10-09T02:38+11:00, after the round-4 results were seen; not registered)

MiMo's audit of round 4 noted that the archive control keeps 500 rows per expert and more experts than MICE, so its
advantage on the misaligned streams cannot be attributed to merging alone. We add snap1000_500 (storage-matched:
1000 rows per expert, no merging) on the same 12 misaligned streams. This is exploratory; it does not change the
round-4 verdict and will be reported as such.

## Round 2 addition — snapshot control on the 29 real streams (registered 2026-10-09T11:35+11:00, before the run)

Provenance: added in response to the TKDE reviewer's plan check (MICE/logs/tkde_review/round2_reviewer_plan_check.md,
item 1), wording confirmed by the Codex expert (round2_expert_a2.md), approved by the user on 2026-10-09 before
execution. The 29 streams and the MICE results were examined before this registration; this run is a review-added
control, not an independent confirmation. Earlier verdicts (criteria 1 and 2, round 4) and the exploratory labels
stay as they are.

- **Policy:** snap1000_500 (`PoolControl`, mode "snap", MICE/code/run.py): at every closed 500-row segment, store the
  latest min(1000, rows so far) labelled rows as a new stored expert; at most 12 stored experts, oldest evicted (MICE
  evicts its least recently used expert); windows of 100, 300 and 1000 rows; same two-level rule
  `reweight.simulate2(outer='brier', scale=.5, temper=True)`; batch size 100; each batch is predicted before its
  labels arrive; batch 0 is warm-up and excluded, as in the paper. Backbone seed 0. MICE values are the paper's
  existing micev1000_500 caches; no MICE rerun. Failures are retried in a new process from checkpoints written
  every 10 batches.
- **Streams:** the 29 real streams of the paper (MICE/code/noninferiority.py: results_test (5 streams: elec2 and four
  INSECTS), results_heldout, results_heldout2, results_heldout3, results_heldout4).
- **Accuracy:** within a stream, the mean of per-batch accuracies over batches 1..T-1 (all batches have 100 rows, so
  this equals the example-weighted accuracy).
- **Descriptive criterion, fixed now:** the unweighted mean over the 29 streams of the per-stream differences
  MICE - snapshot, in accuracy points, is >= -0.1. It is a descriptive threshold, not an inferential
  non-inferiority verdict.
- **Uncertainty:** per stream, moving-block bootstrap of the batch sequence, resampling the same batch indices for all
  methods jointly; blocks of 20 batches (10 and 50 as sensitivity), 10 000 resamples, generator seed 0; one-sided 95%
  percentile lower bound of the mean difference. If a stream has fewer than 2 x block batches, the block is
  floor(T/2). Bounds are pointwise, conditional on the observed streams and backbone seed 0; they do not cover
  backbone-seed or source variability. The same analysis applied to MICE - archive is retrospective and labelled so.
- **Resources reported, measured and caps kept apart:** active experts per batch (number of experts in the cached
  predictions; mean and maximum); TFM calls per batch (the counter counts every fit and predict, including MICE's
  discrepancy calls at segment closes, which are reported separately where they can be counted); stored rows:
  archive exactly 500 per stored expert, snapshot exactly min(1000, rows so far) per stored expert, MICE at most 1000
  per stored expert and at most 12 000 rows in the pool (per-expert row counts were not recorded for MICE; reported as
  a missing measurement). Wall time only as a description (shared GPU).
