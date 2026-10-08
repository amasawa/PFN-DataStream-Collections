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

## Second pass (Claude Code, 2026-10-08, from a Codex reviewer audit)

1. **Zero effects were misclassified by floating-point residue.** `reset_effects.effects` summed float batch accuracies,
   so effects that are exactly zero left residues of about 1e-17 and counted as non-zero. Effects are now summed as
   integer counts of correctly predicted rows (`test_reset_effects.py` has an exact-zero case). Changes: TabICL real
   harm 88.3 -> **88.4%**, TabPFN synthetic 15.5 -> **15.4%**, TabICL synthetic 11.6 -> **11.5%**, M=500 80.4 -> **80.5%**,
   and M=2000 back to **88.1%**: the first pass's 88.1 -> 88.0 change was itself this artefact.
2. **The pooled harmful share is event-weighted.** It pools all resets of all streams and detectors, so sources with
   many alarms weigh more. Now reported alongside: source-weighted 69.5/72.9/68.8% (TabPFN/TabICL/TabDPT), majority
   harmful on 15/19 sources for every backbone, per-detector 81.6-90.7%, and the counts (TabPFN 25 699 losses, 3 460
   gains, 1 057 zero). Abstract, Observation 1 and Section 5.1 revised; the claim "most resets that change the outcome
   are net losses" stands at source level.
3. Tails table caption: removed the obsolete "TabDPT was run on real streams only"; states that the harm column pools
   all resets. Figure 1 caption: its detector-averaged worst source (covertype -23.1) differs from the worst-source
   statistic (-26.2, detector-wise minima averaged).
4. **Claims tightened (reviewer items 2, 3, 4, 5, 7, 12, 14).** Per-reset Δ_j is described as an exact allocation of the
   realised difference to FIFO, not a counterfactual effect; the finite-memory bound is presented as an explanation
   consistent with the results (it is symmetric in gains and losses and alarms are not known to be correct);
   "removes the tail/losses" and "safe" replaced by "substantially reduces"; the guarantee is attached to η<=1,
   γ=1 and the batch-mean log-loss (row-summed allowance BNln2/η); the unsupported "followed within a few batches"
   removed; significance phrased as the Holm-corrected signed-rank null, with test details (two-sided, zeros dropped,
   10 000 percentile bootstrap resamples, pointwise); hedge sensitivity described as one-factor-at-a-time on TabPFN.
5. **Data selection disclosed as sequential.** The ten added sources came in two batches after the first analyses
   (EXPERIMENT_LOG 2026-10-06 23:09-23:30); the paper now says so, reports the batches separately (first batch: full
   reset -1.8 to -2.5, 4-5/5 sources negative; second: helps on 3/5), and states that the hedge fails H4 on the
   first batch (-0.4 to -0.9), which the pre-registration table had omitted.
6. **Grid description corrected.** The grid streams have three concepts on RBF mixtures with 5/30/100 centroids, not
   "5, 30 or 100 concepts". Proposition 1 proof: the equivalence keeps the max with 0 (warm-up), as a necessary condition.
7. **Reproducibility appendix (items 9-11)** added as `overleaf/tmlr/repro.tex`, written from the code (each fact cites its file in a comment): real-stream construction and sources (UCI ids), synthetic generators and seeds, package versions, zero probability for absent classes, float16 cache, dropped incomplete batch, detector lifecycle. Drafted without Codex to save quota.
