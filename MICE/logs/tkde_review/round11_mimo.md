## Findings

**F1 · P1 · Confirmed issue · `oracle_recall.py` `summary()` (lines 62–87)**
- Evidence: `summary()` concatenates whatever `*.csv` exists in `RUN`, then `per_seed = per_block.groupby([..., "seed"]).mean()` and `per_seed[per_seed.seed.isin(seeds)].groupby(["n_centroids","block"]).mean()` — no check that all 24 streams (4 seeds × 6 cells) exist or that each cell has both seeds of the pair.
- Why it matters: with one stream missing, H1/H2 are computed on a mean over one seed and on a subset of blocks, which is not the registered estimator ("mean over all 9 blocks of a stream, then over the two seeds of a cell"), while the printed verdict still reads `H1 ... -> HOLDS`. A missing cell would also silently shrink the "/6 cells" denominator (`merge` is inner).
- Correction: before computing, assert the expected set `{c{nc}_b{L}_s{seed}.csv}` for all 4 seeds × 6 cells (and 9 blocks per stream) and refuse `--summary` otherwise; at minimum print per-cell file/seed counts and refuse if any count ≠ 2.

**F2 · P1 · Suspected issue · `run_TFM_excerpt.py` `TFM.__init__` (lines 33–40), called from `oracle_recall.py:101`**
- Evidence: `TFM(NCLS, 0)` honors `os.environ.get("MICE_BACKBONE", "tabpfn") == "tabicl"` and would construct `TabICLClassifier` instead of the registered TabPFN v2. The registration commits to "Backbone TabPFN v2, seed 0, four estimators".
- Why it matters: if `MICE_BACKBONE=tabicl` is exported in the launching shell (plausible after earlier backbone-ablation work), the whole round-11 run silently uses a different backbone and none of area/zeta/H1/H2 is comparable to `predicted_indep.csv`.
- Correction: in `oracle_recall.py` assert `os.environ.get("MICE_BACKBONE", "tabpfn") == "tabpfn"` before constructing TFM (or unset the variable explicitly in the run command). Status is "suspected" only because firing depends on the runtime environment; the missing guard is certain.

**F3 · P2 · Confirmed issue · `learning_curve_indep.py:47` vs `oracle_recall.py:101`**
- Evidence: the frozen `predicted` column was measured with `f = TFM(NCLS, seed)` for `seed in (10, 11)`; this run uses `TFM(NCLS, 0)`. All three paths use `n_estimators=4`, so the backbone RNG (the 4 estimator seeds) differs between the curves and the measured run.
- Why it matters: part of any H1 residual is backbone-seed noise, not magnitude-model error; with 4 estimators this is not guaranteed to be negligible.
- Correction: do **not** recompute the column (it is frozen by the registration). Document the seed mismatch as a limitation of the comparison in the report/PLAN.

**F4 · P2 · Suspected issue · `learning_curve_indep.py:66–68` vs `registration.md` H1/H2**
- Evidence: `indep_visit_specific` is built from `max(0.0, acc(n_c) - acc(min(j*B, M)))`, i.e. the per-batch better-expert (oracle identification) gain — exactly the estimand of `ideal_obs`. H1/H2 test it against `area_obs`, the realized exponential-weights mixture X.
- Why it matters: any identification loss (registered as descriptive `ideal_obs - area_obs`) drives `area_obs` below `predicted` and can fail H1 even when the learning-curve magnitude model is right; a failed H1 is then ambiguous between "wrong magnitude" and "weighting failed to identify".
- Correction: keep the registered criteria unchanged, but report `|ideal_obs - predicted|` (and its Spearman) next to H1/H2 in the summary output so a failure can be attributed. Both columns are already computed.

**F5 · P2 · Missing information · `oracle_recall.py:88–92`, `predicted_indep.csv` column `observed_mice_s20_21`**
- Evidence: the decomposition computes `remainder = observed_mice_s20_21 - area - zeta` and labels `observed_mice_s20_21` as "deployed MICE - DDM". Nothing in the attached files establishes that this column is the MICE−**DDM** gap (rather than MICE−FIFO or raw MICE) or that it is averaged as points over the same batch set and seeds. Note also `run.py` excludes the warm-up batch 0 ("batch 0 is the warm-up and is not scored"), whereas `oracle_recall.py` scores every batch (the stream's first batch contributes 0 to area+zeta by construction, since X=R there).
- Why it matters: if the baseline, unit, or averaging differs, the decomposition "oracle + remainder" is arithmetic on incommensurable quantities and the remainder's interpretation (detection delay, identification, slow level) does not hold.
- Correction: trace `observed_mice_s20_21` to its generating script before reporting; state the baseline (DDM), the unit (points), and the batch set (and note the warm-up-batch difference). If the batch sets differ, report the decomposition on the common batch set.

## Consistency checks you asked for (verified, no finding)

1. **Policies match the registration.** R: `j=1` → `[max(0,start-M), start)` (FIFO over the last M labelled rows, none of the block yet); `j≥2` → `[start+max(0,(j-1)B-M), start+(j-1)B)` = last `min((j-1)B, M)` rows of the block. S: `[-min(M,(visit-1)L):]` over earlier visits of concept k = `n_c = min(M,(c-1)L)`, most recent rows, `None` on first visits. X: `PX=PR` when `S_ctx is None` (c=1) or `prev_R is None` (stream's first batch), else `w ∝ exp(-η l)` with η=10 and `logloss` clipping at 1e-6 exactly as `reweight.simulate2` (`-log(clip(P[y],1e-6,1)).mean()`); first batch of a block uses the previous block's last batch (`prev_R`), later batches use the preceding batch. No context contains any row of the query batch or later (R ends at `q[0]`; S is strictly earlier blocks); weights use `y[q_prev]` only, so no current-batch label leakage. `TFM(NCLS, 0)` gives seed 0 / 4 estimators, B=100, M=1000, NCLS=4 consistent with `grid_streams` defaults.
2. **Quantities: same scale and averaging as `predicted`.** Per block the script computes `100/J · Σ_{j≥2}(accX−accR)`, `100/J · (accX₁−accR₁)`, `100/J · Σ_{j≥2}(max(accS,accR)−accR)`, then means over 9 blocks and over the two seeds — "points" on both sides (`predictions` returns `100 * vis`). Batch-index shift is consistent: the theorem's "jB rows before batch j+1" corresponds to the script's batch `t = j+1` with `min((t-1)B, M)` relearn rows; `predictions` loops `j = 1..J−1` over `min(j*B, M)`, i.e. the same size set `{B,2B,…,(J−1)B}`. The `(J−1)/J` factor in `predictions` turns the mean over the J−1 interior batches into `Σ/J`, matching the script's `1/J` sum. Visit averaging matches: `predictions` returns `(h(2)+h(3))/3`, which equals the mean over the 9 blocks of a stream (3 first-visit blocks contribute 0 because X=R there), exactly as `per_seed` averages over `b`.
3. **H1/H2 are evaluated as registered**: `|area−predicted| ≤ 1.0` on ≥ 5 of 6 primary cells, MAE ≤ 0.5, and Spearman(area, predicted) ≥ 0.8 over the six cells, all on `primary_s40_41` only, verdicts printed unconditionally.
4. **`ideal_obs` is as registered** (`fmax` so first visits fall back to R, `j≥2` only); `zeta_obs` as registered.
5. **Crash safety is adequate per stream**: full-stream DataFrame, `to_csv(out+".tmp")` then `os.replace`, and `os.path.exists` skip (a `.csv.tmp` is not picked up by `summary`). The gap is F1 (no completeness validation at summary time).

## Only confirmable by running code

- Whether `MICE_BACKBONE` is exported in the launching shell (F2) and whether pandas ≥ 2.2 supports `include_groups=False` in `summary()`.
- Wall time / GPU memory for ~2–3 TFM calls per batch over 24 streams (~6.5k fits on up to 1000-row contexts), and that `from run import TFM` resolves in the run venv.
- The realized values of `area_obs`, `zeta_obs`, `ideal_obs − area_obs` (i.e. whether F4's identification loss is material against the 1.0/0.5 point H1 tolerances) and the H1/H2 verdicts themselves.
- Provenance of `observed_mice_s20_21` (F5) needs the generating results script, which is outside the attached scope.

No verified issue in the policy definitions, the leakage constraints, or the scale/averaging of `area_obs`/`zeta_obs`/`ideal_obs` against `indep_visit_specific`; the batch-index shift between the theorem and both scripts is consistent.

