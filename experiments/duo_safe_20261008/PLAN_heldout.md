# Frozen held-out evaluation of MICE-DUO, 2026-10-08

**Not executed (2026-10-08 14:40).** The same evaluation (same method, seeds 0-2) was already running from
`experiments/duo_heldout_20261008/`; that run is authoritative. See MiceDuo/logs/DUO_SAFE_20261008.md.

Approved by the user ("按照你的想法迭代吧", in reply to the request to run item 1, the held-out evaluation).
Frozen and pushed before any held-out stream is touched. The method is fixed by `PLAN.md` and was tested in
`PLAN_mechanism.md` (H1-H3 held). Nothing below may change after the first run starts; every result is reported.

## Streams (never used to design MICE-DUO)

MICE's 29 real streams minus the 7 MICE-DUO development streams (elec2 and the six h2 streams) = 22:
insects_{abrupt,gradual,incremental,incremental_reoccurring}_balanced; covertype,
insects_{abrupt,gradual}_imbalanced, insects_incremental_abrupt_balanced; h3_{airlines,covertype,insects,poker}_{b,c};
h4_{airlines,covertype,poker}_{d,e}. MICE's own runs used these streams; "held-out" means unused for MICE-DUO.
Protocol as on the development streams: the first 300 batches (B=100) of each stream, i.e. its first 30000 rows
(insects_gradual_balanced has 24150 rows, 241 batches, used in full). The truncated copies are the inputs of both
methods, so both see the same rows and the same label set.

## Runs

TabPFN v2, 4 estimators, M=1000, labels one batch late. Backbone seeds 1 and 2. Per stream and seed: MICE
`micev1000_500` with its expert cache, and DUO with anchor 1 (stores P_sel and P_fifo). 88 GPU tasks, the code
of the overnight and mechanism runs, unchanged.

## Method (frozen)

MICE-DUO = MICE with DUO's anchor-1 selected context inserted as one extra expert in every cached step, combined by
the unchanged MICE rule `simulate2(outer='brier', scale=.5, temper=True)`. No other variant is evaluated.

## Criterion: no negative effect (as in PLAN.md), on each seed separately

1. every stream: accuracy(MICE-DUO) − accuracy(MICE) ≥ −0.30 points;
2. every stream: accuracy(MICE-DUO) − accuracy(FIFO) ≥ −0.30 points;
3. mean over the 22 streams: accuracy(MICE-DUO) − accuracy(MICE) ≥ 0;
4. mean log-loss(MICE-DUO) ≤ mean log-loss(MICE) + 0.005.

**Confirmed** if all four hold on both seeds. Otherwise the claim fails on held-out data and is reported as such;
the failing criteria and streams are named. Reported in addition, without decision role: mean gain, wins, per-stream
gains, gains by stream family, macro-F1 and log-loss, and the task wall-clock time of MICE and DUO.

## Alignment check

MICE's cached 1000-row FIFO expert must equal DUO's `P_fifo` on every batch (tolerance 2e-3, float16 storage).
