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

## Round 4, attempt 4.b — boundary alignment at fixed block length (registered 2026-10-09T12:54+11:00, before the run)

Provenance: the reviewer's rebuttal review (MICE/logs/tkde_review/round4_rebuttal.md, item 1) found that 4.a changes
block length and alignment together and so cannot isolate alignment; design corrected by the Codex expert
(round4_expert_a1.md); approved by the user on 2026-10-09 before execution. The 4.a verdict (FAIL) stands unchanged.

- **Streams** (`make_offset.py`): the 8 aligned confirmatory grid streams of the paper (data seeds 20, 21; 30 and 100
  centroids; blocks of 500 and 2000 rows; K=3; three cycles) with their observations unchanged, preceded by 200 rows of
  the first concept drawn with default_rng(10 000 + seed) from the same centroids, weights and labels. Every concept
  boundary then lies 200 rows into a 500-row segment and on a 100-row batch boundary; recurring blocks keep their
  length. Verified before the run: rows 200.. equal the aligned stream bit for bit.
- **Policies:** micev1000_500 (MICE), arch1000_500, ddm1000, fifo1000, winens1000; backbone seed 0; method, rule and
  constants frozen. Aligned values: the existing seed-20/21 results (MICE replayed from MICE/results_grid_test3; the
  archive from this control run).
- **Matched batches:** offset batch t+2 holds exactly the rows of aligned batch t. Accuracies are averaged over the
  matched batches t = 1..T_aligned-1 (offset batches 3..T_aligned+1); full-stream accuracy is reported separately.
  Recurrence windows: the first five batches of each of the six recurring blocks (blocks 4-9), indexed in aligned
  batches and shifted by +2 in the offset stream. Unweighted means over streams; all batches have 100 rows.
- **Primary contrast:** Delta_i = (MICE - DDM)_offset,i - (MICE - DDM)_aligned,i on matched batches, for the 8 streams:
  all values, the unweighted mean, and breakdowns by block length, centroid count and seed. Descriptive; no
  preservation or non-inferiority claim (no margin was fixed).
- **Descriptive criterion (same form as 4.a):** MICE - DDM on the offset streams positive on >= 7 of 8 and mean >= +1.0.
- **Also reported:** MICE - FIFO, - window ensemble, - archive (offset and aligned), overall and in recurrence windows.
- **Limits stated in advance:** the extra 200 rows add initial history; two data seeds and one backbone seed; the 8
  configurations are not independent replications; the result is sensitivity to this phase shift, not a pure causal
  effect of segment impurity.

## Round 8 addition — learning curves from independent rows (registered 2026-10-09T15:41+11:00, before the run)

Provenance: while documenting the grid for the TKDE reviewer (round 8), we found that the registered learning curves
(MICE/code/learning_curve.py, data seeds 10 and 11) re-initialise the same NumPy generator as the evaluated seed-10/11
grid streams: the first block's centroid draws coincide (labels 100% equal) and some rows are bit-identical (0 to
1887 per stream). The seed-20/21 evaluation shares no rows with the curves. This addition is a sensitivity analysis
under the standing authorisation of 2026-10-09; the registered predictions and their verdicts stay as they are.

- **Curves:** same protocol as learning_curve.py (one block of 4000 rows per concept; rows 1-3000 context pool, rows
  3001-4000 test; n in {50, 100, 200, 500, 1000, 2000}; three contexts per n with generator seeds 0, 1, 2; TabPFN v2,
  4 estimators, random state = data seed), but the rows are drawn from default_rng(20 000 + seed) given the concept
  definitions (centroids, weights, labels) of default_rng(seed). Verified before the run: no row of the new curve data
  equals a row of any evaluated grid stream of seeds 10, 11, 20, 21.
- **Predictions:** registered form (M rows on every recurrence) and theorem form (n_c = min(M, (c-1)L)), aggregated
  exactly as before (curve averaged over 2 seeds x 3 concepts x 3 repetitions, interpolated in log n; visits 2 and 3
  with weight 1/3; per cell the mean of the two streams; Spearman over the six cells).
- **Reported:** Spearman with the observed fast-level gains (seeds 10, 11) and with the full method (seeds 20, 21),
  for the original and the independent curves, side by side. No criterion; descriptive sensitivity.

**Correction (2026-10-09T16:08+11:00, wording only, after the run):** the rows of the round-8 sensitivity curves were drawn from `default_rng([20000 + seed, m, k])` (one generator per seed, centroid count and concept), as implemented in `learning_curve_indep.py` before the run; the text above wrote `default_rng(20 000 + seed)`. Found by the MiMo audit; the analysis is unchanged.

## Round 9 addition — accuracy-resource tradeoff (registered 2026-10-09T16:20+11:00, before any run)

Provenance: TKDE reviewer round 9 (MICE/logs/tkde_review/round9_codex.md), plan v2 with the expert's corrections
(round9_expert_a1.md) and the reviewer's plan check (round9_reviewer_plan_check.md); standing user authorisation of
2026-10-09. Method frozen; existing results and criteria unchanged.

**A. Isolated benchmark** (GPU alone, one process at a time, after the snapshot control finishes):
- Streams h4_airlines_d, h4_covertype_d, insects_abrupt_balanced, batches 1-300 (data truncated to 301 batches; the
  policies are causal, so these batches are identical to the full-stream runs). Claims about cost are restricted to
  these prefixes.
- Policies: micev1000_500 (MICE), fifo1000, fifo1500, fifo2000, fifo3000, fifo5000, fifo13400, winens1000; backbone
  seed 0; three fresh-process repetitions, policy order rotated per repetition.
- Per batch: wall time of prediction and update as recorded by run.py (segment processing included; checkpointing
  disabled), synchronised by the transfer of predictions to the host. MICE adds its two-level rule: the replay time
  of simulate2 over the prefix, amortised per batch. Reported: amortised mean, median, p95, max seconds per batch,
  closing versus non-closing batches for MICE, rows per second; peak allocated and reserved GPU memory and peak process
  RAM; retained context rows and pool occupancy. Accuracy on the same prefixes, paired. MICE's cached expert
  predictions are compared bit for bit with the frozen cache.
- Aggregation: per policy, the mean over the three streams of the per-stream mean over repetitions.

**B. Time-matched FIFO** on the 29 real streams: M* is fixed from A before any accuracy is examined: among
{1500, 2000, 3000}, the M whose amortised mean seconds per batch is within a factor 1.25 of MICE's (closest if
several); if none is, M* is the closest one and the comparison is reported as bracketing, not matched. FIFO M* then
runs on the 29 streams (backbone seed 0). Reported: MICE - FIFO M* per stream and mean, two-sided 95% intervals and
one-sided block-bootstrap bounds (approximate, fixed streams). Described as "accuracy at a benchmark-calibrated FIFO
capacity"; cost comparability on the 29 full streams is not claimed.

**C. Definitions fixed now:** "matches" = absolute mean difference at most 0.1 points; "similar cost" = amortised
mean seconds per batch within a factor 1.25. If on the benchmark prefixes a FIFO is at least as accurate as MICE at
similar or lower cost, the abstract and conclusion say so. FIFO 5000 and 13 400 are costlier operating points on the
prefixes only. Every configuration, including any that fails or exceeds limits, is reported.
