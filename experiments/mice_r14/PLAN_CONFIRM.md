# MICE round 14 — confirmation set on fresh seeds (registered 2026-10-16, before any run)

## Why
The round-14 registration (PLAN.md) describes data seeds 40-43 as "never used; independent concept draws". An auditor
(MiMo, 2026-10-16) found that seeds 40 and 41 had been used on 2026-10-14 by the registered oracle test of the recall
theorem (MICE/code/oracle_recall.py): same generator, so the same concept draws; the 500- and 2000-row-block streams are
row-identical to the oracle streams after the prepended offset rows. That test used oracle boundaries, involved no
change detector and tuned nothing; the detector constants come from development seeds 0 and 1. PLAN.md and its results
are kept unchanged (see CORRECTION_20261016.md). Codex gpt-6-astra (xhigh) judged the misstatement P1, required a
disclosed correction, and recommended (optional) this separate confirmation on previously unused seeds. Run under the
user's standing authorisation of 2026-10-09 (additional controls on existing generators, method unchanged).

## Design (frozen)
- Method: MiceCP exactly as frozen in PLAN.md (MICE/code/run.py class CPSegments, SIG=300, H=3, R=5, RMIN=2,
  DELTA_CP=0.001, LMIN=300, TRIM=0; `micecp1000_500`). Comparators: fixed segmentation (`micev1000_500`) and reset
  (`ddm1000`), as in PLAN.md.
- Streams: `make_streams.py confirm` — data seeds 50, 51, 52, 53 (checked unused in the repository and in ~/pfn-runs on
  2026-10-16), otherwise identical to the test set: 30 or 100 centroids; regimes b500, b2000, bvar (nine blocks drawn
  uniformly from 500..2500 rows once per seed and centroid count); three offsets per (seed, centroids, regime), 1..499
  rows (1..1999 for b2000), drawn by default_rng(8000 + 10 * seed + centroids). 72 streams, 216 tasks.
- Root: ~/pfn-runs/mice-r14-confirm (new). Workers: experiments/mice_r14/worker.sh, checkpoints every 10 batches.

## Criterion (identical to C1 of PLAN.md)
Within each length regime (24 streams): mean(CP - reset) >= +1.0 points, CP above reset on >= 18 of 24, and the
hierarchical-bootstrap 95% lower bound (seeds within centroid count, offsets within seed; analyse_test.hier_lb) > 0.
Met if all three regimes meet it. Evaluator: experiments/mice_r14/analyse_confirm.py.

## Reported without criterion
CP - fixed segmentation, first five batches of recurring blocks, purity (shares >= 95% and > 50%), detection.

## Reporting
The confirmation is reported separately from the registered test, whatever its outcome; the registered verdicts of
PLAN.md stand as computed, with the disclosed seed reuse. A failure is stated in the abstract or the conclusion.
