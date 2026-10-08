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
