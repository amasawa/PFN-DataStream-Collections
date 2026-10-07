# Mechanism test on fresh synthetic streams, 2026-10-08

Frozen before generating the streams or running any model. Follows `PLAN.md`; the development pass of
MICE+sel1 (seeds 1-2) motivates this test but is not evidence for it.

## Question

Does adding DUO's selected-context prediction as a MICE expert (1) never hurt when concepts do not recur, and
(2) help more the more often concepts recur? The development gain sat on one recurring-concept stream
(h2_rialto); this test controls recurrence directly on data never used before.

## Streams (fresh data; MICE used grid seeds 0, 1, 10, 11, 20, 21)

The MICE grid generator (`MICE/code/grid_streams.py::stream`, unchanged): RBF mixture in d=10 with 4 classes;
all concepts share centroids, so P(x) is fixed and only the centroid labels change (pure real drift).
Fifteen blocks of 2000 rows (30000 rows = 300 batches of B=100), varying only how many distinct concepts
there are:

| recurrence | K concepts | cycles | each concept appears |
|---|---|---|---|
| high | 3 | 5 | 5 times |
| medium | 5 | 3 | 3 times |
| none | 15 | 1 | once (never recurs) |

Difficulty: n_centroids in {30, 100}. Data seeds 30, 31, 32. 3 x 2 x 3 = 18 streams.

## Runs (backbone TabPFN v2, 4 estimators, backbone seed 1, unchanged code)

Per stream: MICE `micev1000_500` with its expert cache; DUO with anchor 1 (primary) and anchor 3
(secondary), which also store FIFO. 54 GPU tasks. The overnight supervisor/worker are reused unchanged
except that publication is disabled; logging is done by hand.

## Evaluation (`evaluate_mechanism.py`, written before the runs)

Same construction as `PLAN.md`: insert `P_sel` as one extra expert, apply the frozen MICE rule
`simulate2(outer='brier', scale=.5, temper=True)`. FIFO alignment check as before. Accuracy over batches
1-299; also accuracy in the first 5 batches after each switch to a previously seen concept.

## Pre-registered hypotheses for MICE+sel1 (primary)

- **H1 no harm without recurrence**: on all 6 K=15 streams, accuracy − MICE ≥ −0.30 and accuracy − FIFO
  ≥ −0.30 points.
- **H2 no harm anywhere**: the same two bounds on all 18 streams; mean log-loss ≤ MICE + 0.005.
- **H3 gain grows with recurrence**: mean gain over MICE is ordered K=3 > K=5 > K=15, and at K=3 the
  mean gain is > 0 with ≥ 5 of 6 streams positive.

H1 and H2 are the user's requirement ("no negative effect"); H3 is the mechanism claim for the paper.
Every result, including failures, is reported per stream. MICE+sel3 is reported with the same checks but
is not used to declare success. The 22 held-out streams remain untouched.
