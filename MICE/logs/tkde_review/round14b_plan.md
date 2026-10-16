# Round 14.b plan (registered 2026-10-16, before any run)

Reviewer verdict on round 14 (round14_rebuttal.md): partly answered, score 4. Two remaining required changes, neither
changes the method:
1. Theory wording: keep the recall theorem conditional on pure contexts; present majority purity as a restricted
   population identification result and the detected-segment gains as empirical evidence of contamination tolerance;
   separate detection, boundary localisation and stored-context purity.
2. Resources and snapshot control for the detected method: end-to-end latency, retained rows and peak memory against
   the archive with identical detected segments; the snapshot control on the unknown-phase and irregular schedules,
   with stated storage and timing budgets. Existing results kept separately.

## Part 1 (text only)
Rewrite of sec:th-seg remark, RQ2 "Purity and detection", abstract/intro/conclusion sentences that say detected
segments "supply the premise", the contributions list, the RQ2 heading and the appendix purity verdict ("the registered
90% rule failed"); "majority form" and "near-pure" removed everywhere: theorem conditional on purity (the registered strict rule failed: 88% and 87% < 90%);
prop:purity = population identification under deterministic concepts, P_X = Q_X, 0-1 loss; the measured gains = evidence
that the recall gain survives the measured contamination; three separate measured quantities: detection (575/576),
localisation (declared batch), purity of stored contexts (share at close).

## Part 2 (experiment; method, constants and all earlier results unchanged)
Policies: micecp1000_500 (MICE), archcp1000_500 (archive with the same detected segments, kmax 12), snap1000_500
(snapshot pool as defined in round 2: every 500 rows stores the latest 1000 rows; needs no boundary information).
The snapshot keeps fixed 500-row closing because its stored context is the latest window, not a segment; it uses no
detector, so its budget excludes the detector's cost (stated in the budget line). A detected-segment snapshot is not
added (it would be MICE's stored segment without the recall organisation, confounded with the archive).

**A. Isolated benchmark** (protocol of round 13 A1/A2, bench_pools.py: GPU alone, 28 GB cap, fresh process per run,
checkpointing off, rotated order; the occupancy hook extended to CPSegments.step, which replaces MiceV1.step).
- A1: real prefixes h4_airlines_d, h4_covertype_d, insects_abrupt_balanced (batches 1-300); micecp, archcp kmax 12,
  snap kmax 2 and 4; 3 repetitions each; snap kmax 12 one repetition (timing budget of the capacity-matched
  snapshot of part C).
- A2: full grid streams: confirmation streams c_b500_c100_s50_o0, c_b2000_c100_s50_o0 and c_bvar_c100_s50_o0, shifted off_c100_b500_s20;
  micecp, archcp kmax 12, snap k* and snap kmax 12; 3 repetitions.
- What is timed (end to end, the procedure whose accuracy is reported): the online step of each batch, i.e. the change
  detector, the discrepancy tests, segment closure, pool maintenance, all TFM predictions and the first-level weights
  (wall clock around pol.step; TFM outputs are copied to host memory, which synchronises the GPU), plus the slow level
  (second-level mixture) timed per batch by replaying the run's prediction cache and added to each batch (amortised).
- Retained rows (counting convention): rows of all stored contexts in the pool after each batch, recorded per batch;
  every policy also keeps the latest 1000 stream rows for its windows (identical, stated once); the detector keeps one
  error count per labelled batch (no rows); peak process RSS reported as measured (process peak, not data volume).
- Reported: amortised mean s/batch, median, p95 and max of the online step, peak allocated/reserved GPU memory, peak
  RSS, TFM calls, mean occupancy, logical stored context rows per batch (retained rows), accuracy on the measured run.

**B. Snapshot k*** (prefix-budget-selected) from A1 timings only, before any accuracy of part C is read: among kmax in {2, 4}, the largest whose
amortised mean s/batch <= micecp's on all three prefixes; if none, k* = 2 labelled "over-budget fallback".

**C. Accuracy** (backbone seed 0, two-level replay, parallel workers, not timed): snapshot at k* and at kmax 12 (the
pool capacity of MICE) on (i) the 72 confirmation streams (seeds 50-53, random boundary phase; regimes 500, 2000 and
500-2500-row blocks), (ii) the 8 shifted grid streams, (iii) the 12 misaligned schedules. MICE outputs are the existing
round-14 runs (same streams, same code).

**D. Statistics:** Delta = MICE - snapshot per stream. (i) per regime and overall, hierarchical bootstrap as in
PLAN.md (seeds within centroid count, offsets within seed); (ii), (iii) group mean with moving-block bootstrap
(blocks of 10 batches). Delta >= -0.1 is "within the descriptive tolerance or better".

**E. Reporting rule:** resource results are stated for the measured prefixes and streams only. If in any group the
snapshot at k* has mean Delta <= +0.1, the abstract and conclusion say so, naming the group. All configurations are
reported, including infeasible ones. The detected-segmentation resource results form a separate table, never merged
with the fixed-segmentation tables. The snapshot at kmax 12 is described as capacity-matched (same maximum number of stored
contexts); its cost is stated only where measured (A1 prefixes, A2 streams), with the measured ratio of s/batch to
MICE on those streams, and called higher or lower only where that ratio says so. k* is called prefix-budget-selected;
time matching is claimed only where measured.

Order (user 2026-10-16: do not leave the GPU idle): C is run first for all candidate capacities kmax in {2, 4, 12}
(92 streams x 3 = 276 tasks, 4 workers, reduced on a failure burst), as in the round-13 amendment; no output of C
(npz, pkl, accuracies) is read until kstar.json is written by stage a1. Then A1 -> B -> A2, each alone on the GPU
(bench_cp.py waits for a quiet GPU before every run). Only the k* and kmax 12 outputs enter the analysis; the other
candidate is reported as a sensitivity row.
Expert check: round14b_expert_q1.md (Fable 5.1), changes (a)-(d) adopted. Reviewer plan check:
round14b_reviewer_plan_check.md (sufficient with changes), changes 1 and 2 adopted. Estimated GPU time: A1 about 4-5 h alone; C 276 tasks about 3 h with 4 workers.
