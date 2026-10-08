# ResetEval paper audit, 2026-10-08

Scope: user requested iteration following the log review; CPU-only audit of existing results and
paper revisions while DUO frozen confirmation runs separately. No ResetEval GPU experiment added.

## Corrections

1. `make_tables.py` used a hard-coded ten-batch reset attribution window for every context budget.
   For FIFO TFMs the exact width is ceil(M/B)-1: 4, 9 and 19 batches at M=500/1000/2000.
   `reset_effects.py` now supplies that width and asserts that the per-reset differences sum to the
   full-stream accuracy difference. `analyse_backbone.py` uses the same implementation.
   Regenerated all manuscript tables from stored results: M2000 harmful share changes **88.1% to
   88.0%**; the other generated numeric entries are unchanged. Full output: TABLE_AUDIT_20261008.txt.
   Historical experiment logs are preserved; their old M2000 88.1% value is superseded by this audit.
2. Trained learners have no finite FIFO horizon. Their previously registered ten-batch statistic is
   retained but now labelled as a local-window descriptive comparison, not exact full-reset
   attribution. The 69.9%/48.8% values do not change. They should not be presented as directly
   interchangeable with the TFM's full per-reset effects.
3. The cumulative log-loss guarantee requires eta<=1 and gamma=1. It is now explicit in the abstract
   and conclusion; no inference from that bound to an accuracy-tail guarantee is made. The bound
   grows with alarm count. Clipped loss updates / normalized float16 cache mixtures are distinguished
   from the positive, normalized probabilities assumed by the theorem. The empirical 648-case
   check is not a proof of arbitrary-stream safety for these numerical modifications.
4. Removed the unsupported claim that tuned detectors necessarily fire less often, corrected the
   main-backbone best-source range from 5--8 to approximately 5--6, replaced absolute tail-removal
   wording in the results/conclusion, and clarified the additional-context prediction cost.

## Validation

- `test_reset_effects.py`: exact accounting at M=500/1000/2000 and a non-multiple budget; catches
  effects incorrectly truncated after batch ten; preserves explicitly local trained-learner stats.
- Full manuscript table regeneration passes exact-accounting assertions on all loaded TFM streams.
- `thm_check.py` now rejects missing files, incomplete arrays and non-finite values instead of
  silently skipping them. Re-run: **648/648**, maximum allowance fraction **0.683**, **424** cases
  with lower cumulative log-loss than FIFO. No change to these manuscript numbers.
- Revised TMLR PDF compiles successfully with Tectonic. No undefined citations/references or
  overfull boxes in the final log; remaining warnings concern underfull boxes, PDF bookmark text,
  and a float-placement adjustment.

## Primary-source reference checks

- TabICL author list matches [PMLR 267, Qu et al.](https://proceedings.mlr.press/v267/qu25d.html).
- TabDPT 2024 citation matches [the version-1 arXiv record](https://arxiv.org/abs/2410.18164v1).
  Kept this explicitly versioned citation; the later NeurIPS record has a different author list,
  so metadata from different versions was not combined.
- Drift-Resilient TabPFN authors/title match the
  [NeurIPS 2024 record](https://proceedings.neurips.cc/paper_files/paper/2024/hash/b2e2774c8e76afe191b5bf518f5cb727-Abstract-Conference.html).

## Remaining before submission

This is a targeted technical audit, not a claim of completed submission review. Remaining work:
full bibliography/source verification beyond the entries above, final editorial review of the
causal/mechanistic language and pooled reset statistics, and review of the compiled manuscript.
The manuscript and anonymized artifacts must be reviewed before an external submission. No paper
was submitted or pushed by this iteration.
