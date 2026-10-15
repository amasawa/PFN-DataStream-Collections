# MICE round 14: change-point segmentation (method change) — registration

Status: DRAFT until committed and pushed before any test run (the commit id of this file is the registration).
Approval: the user approved a method change on 2026-10-15 ("A，改方法，继续迭代"; option A: a boundary-robust memory
construction with a new frozen evaluation) and delegated the iteration ("你自己迭代吧"). Expert advice: Claude Fable 5.1
(MICE/logs/tkde_review/round14_expert_q1.md). Code audit: MiMo Pro high (round14_mimo_code.md), findings fixed.

## Question
The reviewer's P1 issue (round 13): the recall gain of MICE depends on the phase of its fixed 500-row segments
relative to unknown concept boundaries (shifted grid: gain over reset +3.09 -> -3.67; realigned with the known phase:
+3.01). The recall theorem assumes stored contexts that hold one concept. Does starting segments at detected changes
restore the gain without knowledge of the phase, on fresh concept draws with arbitrary offsets and block lengths,
without losing accuracy where boundaries are aligned and without harming the real streams?

## Method (frozen at the registration commit)
MiceCP = MICE (MiceV1: windows 100/300/1000, merge rule delta=0.02, kmax 12 with least-recently-used eviction,
two-level rule `reweight.simulate2(outer="brier", scale=0.5, temper=True)`) whose segments start at detected changes:
`MICE/code/run.py` class `CPSegments` with SIG=300, H=3, R=5, RMIN=2, DELTA_CP=0.001, LMIN=300, TRIM=0 (method name
`micecp1000_500`). ArchCP = the archive (every closed segment its own expert, no merging, oldest evicted beyond 12)
with the same segmentation (`archcp1000_500`).
Causal segment construction (as implemented): at step t the labels of batches < t are known. (1) The 300-row window's
prediction for batch t-1, issued at t-1 before its labels, is scored: err[t-1] = number of errors. (2) Detection: for
b in max(1, t-3)..t-1, compare the error rate on batches b..t-1 with that on up to 5 batches before b that lie at or
after ref0 (the batch after the previous detected change; at least 2 of them); a change is declared at the b with the
largest excess over the Hoeffding margin sqrt((1/n1 + 1/n2)/2 ln 1000). (3) On a change, the open segment (rows
closed..b*B-1) is closed if it holds >= 300 rows, otherwise its rows enter no stored context; the next segment starts
at row b*B; ref0 = b+1. (4) Without a change, the open segment's first 500 rows are closed once 300 further rows are
labelled. (5) A closed segment goes through the unchanged merge-or-add rule; a stored context keeps its last 1000
rows. Detection delay: a change in batch b is seen at t >= b+1; segments are cut at batch boundaries, so a boundary
inside a batch leaves fewer than B=100 rows of the adjacent concept in one of the two segments. No true boundary,
concept label or future label enters any online decision; the concept labels are used only to measure purity.
Budgets: at most 12 stored experts of at most 1000 rows each (MiceCP and ArchCP alike; reset and FIFO hold 1000 rows);
TFM calls per batch: one per window and stored expert, plus MICE's merge tests when a segment closes (ArchCP none);
the detector adds no TFM call (it reuses the window's issued prediction) and O(H R) arithmetic per batch.
The constants were set on development streams only (data seeds 0 and 1 of the generator:
experiments/mice_r14/make_streams.py dev/dev2; offline tuning with tune_detector.py; dev accuracies with
analyse_dev.py, ~/pfn-runs/mice-r14-dev). Development result (20 streams, before registration): MiceCP - reset
+2.66 points on average, above reset on 20/20; original MICE -0.01; MiceCP - MICE +2.67; MiceCP - ArchCP +0.31;
152/152 changes detected, 0 false cuts, all fixed-phase dev segments pure. Row-granularity development offsets (dev2):
230/232 changes found (cut at the batch holding the change or up to 3 batches later), 0 false cuts; a boundary inside
a batch leaves < 100 rows of the adjacent concept in a segment (500-row blocks: segment purity down to 0.83).
Leaving out one batch on each side of a detected change (TRIM=1) made the segments pure but lowered accuracy on
500-row blocks (MiceCP - reset, 30 centroids, offset 250: +1.76/+2.09 with TRIM=0, -0.50/-1.24 with TRIM=1; 100
centroids +6.96/+9.22 vs +6.65/+8.24), so TRIM=0 is frozen (~/pfn-runs/mice-r14-devtrim).
Reviewer check of the draft (Codex astra high, round14_reviewer_plan.md): three required changes adopted (several
offsets per concept draw with a per-regime criterion and hierarchical uncertainty; an operational resource criterion;
causal construction stated and purity measured, the theorem claim conditional on purity).

## Test sets and runs (backbone TabPFN v2, seed 0; B=100, M=1000; outputs never inspected before all runs finish)
- T1 (primary, fresh): `make_streams.py test` -> ~/pfn-runs/mice-r14-test/data, 72 streams: data seeds 40-43 (never
  used; independent concept draws), 30 or 100 centroids, three length regimes (500-row blocks; 2000-row blocks; nine
  blocks drawn from 500..2500 rows once per seed and centroid count), each with three independently drawn offsets at
  row granularity (1..499 rows; 1..1999 for 2000-row blocks), drawn by default_rng(7000 + 10 seed + nc) and listed
  in data/manifest.txt. Methods: micecp1000_500, archcp1000_500, micev1000_500, ddm1000 (reset), fifo1000.
- T2 (existing synthetic, ~/pfn-runs/mice-r14-exist, data from ~/pfn-runs/mice-tkde-control-20261009/data): micecp
  and archcp on the 8 shifted grid streams (off_), the 12 aligned grid streams (seeds 20/21; criterion on the 8 with
  30 or 100 centroids) and the 12 misaligned schedules (mis_); the other methods from the earlier runs.
- T3 (real): micecp on the 29 real streams (then archcp, reported without criterion); MICE and FIFO from the earlier
  runs (MICE/results_test, results_heldout, results_heldout2/3/4).
Order: T1, T2, T3 micecp, T3 archcp (experiments/mice_r14/launch_test.sh; 4 workers at the user's request, reduced if
CUDA failures storm), checkpoints every 10 batches.

## Registered criteria (experiments/mice_r14/analyse_test.py, committed with this plan)
Accuracy of a stream = mean over batches 1..T-1; differences in points.
- C1 (primary, T1): within each length regime (24 streams): mean(MiceCP - reset) >= +1.0, MiceCP above reset on
  >= 18 of 24, and the 95% hierarchical-bootstrap lower bound of the regime mean > 0 (seeds resampled within each
  centroid count, offsets within each drawn seed; 10 000 resamples, its own default_rng(0)). Recurring blocks: blocks
  from the fourth on (the generators cycle three concepts in order).
- C2 (shifted grid): mean(MiceCP - MICE) >= +2.0 over the 8 streams.
- C3 (aligned grid): mean(MiceCP - MICE) >= -0.3 over the 8 streams with 30 or 100 centroids.
- C4 (real): mean(MiceCP - FIFO) >= -0.1 and mean(MiceCP - MICE) >= -0.2 over the 29 streams.
- C5 (resources, T1): MiceCP uses no more TFM calls and no more stored experts per batch than ArchCP (means over the
  72 streams), with mean(MiceCP - ArchCP) >= -0.3.
- P (purity rule, T1), on the (stored context, segment close) evaluations (the context that received a segment, right
  after receiving it, over all closes of the 72 streams): the paper says that MiceCP's stored contexts meet the
  single-concept premise if >= 90% of them hold >= 95% rows of one concept; else that they meet its majority form
  (under the posterior-predictive assumption, a context whose majority concept holds more than half of its rows
  predicts that concept's class where two deterministic concepts disagree) if >= 95% of them hold > 50%; otherwise the
  recall theorem is presented as conditional on purity. The measured purity is reported in every case.

Reported without criterion: per-cell means; misaligned schedules; the archive (k=12) on the existing streams; first
five batches of recurring blocks; 95% moving-block bootstrap intervals of group means; detection (found / false
cuts); experts, TFM calls and seconds per batch (wall time of the runs, not an isolated benchmark). All results are
reported whether criteria are met or not; the results of the original method (including the failed boundary tests of
rounds 4 and 12) stay in the paper as results of the original method.

## Reporting
The paper presents MiceCP as the method that implements the single-concept premise of the recall theorem; the
original fixed segmentation and its boundary failures are reported as the motivating evidence. Any criterion not met
is stated in the abstract or the conclusion.
