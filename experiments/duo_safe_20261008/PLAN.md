# DUO as a MICE expert (safe-gain), 2026-10-08

Frozen before computing any result of this variant. Written after the overnight DUO results and the
post-hoc per-stream decomposition, so the development result below is exploratory by construction.

## Question

The user's new goal for DUO: **no negative effect; gains are not required everywhere.** The overnight runs
showed that DUO's selection helps strongly on a recurring-concept stream (h2_rialto) and hurts on others
(h2_airlines, h2_weather). Hypothesis: if DUO's selected-context prediction enters MICE as one additional
expert, MICE's two-level rule (inner loss-weighted mixture + outer guard against the 1000-row FIFO expert)
keeps the harm bounded while retaining part of the rialto gain.

## Method (no new model calls)

- Inputs: the overnight caches `duo_mice_s{1,2}/<stream>__micev1000_500.pkl` (every MICE expert's
  probabilities per batch) and `duo/s{1,2}_a1/<stream>.npz` (`P_sel`: TabPFN on DUO's selected 1000 rows).
  Both are causal: batch t uses only labels of batches < t.
- Primary variant **MICE+sel1**: insert `P_sel` (anchor=1, the original DUO selection) as one extra expert key
  in every cached step, then apply the frozen MICE rule `simulate2(outer='brier', scale=.5, temper=True)`,
  unchanged.
- Secondary, report only: MICE+sel3, MICE+sel5 (anchor 300/500 selections) and MICE+duo1 (DUO's mixture as
  the expert). No parameter of the MICE rule is tuned.
- Sanity check before reporting: MICE's cached FIFO expert (key -1000) must equal DUO's `P_fifo` on every
  batch (same backbone seed, same 1000 rows).
- Streams: the 7 development streams, first 300 batches, B=100. Seeds 1 and 2 (seed 0 has no cache).

## Criterion "no negative effect" (fixed now)

For each seed separately, a variant passes if all hold:

1. every stream: accuracy(variant) − accuracy(MICE) ≥ −0.30 points;
2. every stream: accuracy(variant) − accuracy(FIFO) ≥ −0.30 points;
3. mean over the 7 streams: accuracy(variant) − accuracy(MICE) ≥ 0;
4. mean log-loss(variant) ≤ mean log-loss(MICE) + 0.005.

Gains are reported (mean, wins, per stream) but not required. All variants and seeds are reported.

## What a pass licenses

Only a frozen confirmation on data not used here: first new synthetic streams with controlled recurring
vs. non-recurring drift (fresh development data), then the 22 held-out streams only after explicit user
approval. A development pass alone is not a result for the paper. A failure is reported as such.
