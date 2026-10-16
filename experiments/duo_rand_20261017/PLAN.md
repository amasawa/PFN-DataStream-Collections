# MICE-DUO round 1: random-selection control (registered when committed, before any run)

Reviewer (MiceDuo/logs/duo_review/round1_codex.md, score 3, P1): the safeguard is inherited from MICE, so the
paper must show that relevance ranking adds information beyond adding one more context expert. Requested control:
MICE plus an anchor-preserving, uniformly sampled context expert with identical mixing settings; paired accuracy and
log-loss on the controlled-recurrence and held-out streams, with uncertainty and runtime.

Under the user's standing authorisation of 2026-10-09 (review-induced control, existing generator and streams,
method unchanged). Base: MICE with fixed segmentation (user 2026-10-17).

## Control expert `rand` (only the ranking step differs from DUO's `sel`)
At batch t (anchor a, candidate horizon H = 100 batches, budget M = 1000 rows, B = 100):
recent = batches max(0, t-a) .. t-1; candidates = batches max(0, t-H) .. max(0, t-a)-1; slots = M/B - |recent|.
If |candidates| <= slots: context = candidates + recent (identical to sel). Otherwise `slots` candidates drawn
uniformly without replacement, rng = numpy default_rng([backbone seed, t, crc32(stream name)]) (fixed, causal,
independent of labels). Prediction: one TFM call on the 10 selected batches for the query batch, with the same
TFM wrapper, backbone seed and chunking as DUO. Inserted into the existing MICE expert cache exactly as `sel`
(extra expert key, simulate2(outer='brier', scale=.5, temper=True)). MICE caches and DUO `sel` outputs are the
existing ones (not rerun).

## Oracle expert `orc` (user approval 2026-10-17: "加上")
Analysis-only upper reference on the 18 mechanism streams (uses the generator's concept labels, unavailable to any
online method): same anchor, candidates and slots as sel; the slots are filled with the most recent candidate batches
whose concept equals the concept of the query batch t; remaining slots (fewer such batches) are filled by the uniform
draw 0 of rand from the other candidates. Mechanism blocks are 20 batches, so every batch has one concept.

## Streams
(i) Mechanism: the 18 synthetic streams of PLAN_mechanism.md (K in {3,5,15} concepts, 30/100 centroids, data
seeds 30-32), backbone seed 1, anchor 1 (the primary DUO variant); rand with three draws (d = 0, 1, 2); orc once.
(ii) Held-out: the 22 real-stream prefixes (4 sources: INSECTS 9, CoverType 5, Airlines 4, Poker 4) x backbone
seeds 0, 1, 2 of experiments/duo_heldout_20261008, anchor 1, rand with three draws per prefix and backbone seed. These
were evaluated once for DUO; here they serve a comparison between two experts, not a new confirmation of DUO's
held-out criterion, whose verdict stands.
Total: 54 + 18 + 198 = 270 accuracy tasks (one TFM call of a 1000-row context per batch, 300 batches), run by
long-lived workers (no timing). rng for draw d: numpy default_rng([backbone seed, d, t, crc32(stream name)]).
Selected batches are passed to the TFM in chronological order, as for sel. TFM wrapper, backbone, memory cap and
thread settings are those of the frozen held-out source (~/pfn-runs/duo-heldout-20261008/source/MICE/run.py, the same
file as the mechanism run's). Pipeline check before the runs: recomputing sel with this worker reproduces the stored
P_sel of two streams (max abs difference < 2e-3, the float16 storage tolerance).

## Timing benchmark (matched boundaries)
Three held-out prefixes (one each of INSECTS, CoverType, Airlines; backbone seed 0), one process per run alone on the
GPU (no other process above 5% utilisation; any idle resident process is recorded), two repetitions, rotated order:
MICE (micev1000_500, online step per batch as recorded by run.py), sel expert (ranking call + context prediction, wall
clock per batch), rand expert (context prediction per batch); the replay of the two-level mixture with and without the
extra expert is timed per batch and added. Reported: seconds per batch of MICE, MICE+sel, MICE+rand.

## Analysis (no further model calls; evaluate.py, committed before the runs)
Two comparisons, each with accuracy and log-loss (co-primary; Delta oriented so that positive = sel better); rand
effects are the mean over its three draws:
- Ranking (expert alone): sel vs rand (and orc on mechanism), single predictors over batches 1-299.
- Deployed (inside MICE): MICE+sel vs MICE+rand (and MICE+orc), frozen simulate2 rule; both also against MICE.
Diagnostics (zero cost): hit rate on mechanism streams (share of non-anchor selected batches whose concept is that
of the query batch), sel vs rand vs orc per K; mean fast-level weight of the extra expert (recomputed with the frozen
rule's formula); Deltas restricted to batches t > 10.
- Mechanism: per K level, the 6 per-stream mean Deltas: mean, paired t 95% interval over the 6 streams (streams are
  independent draws of the generator), and the number of positive streams. Selector variability: SD over the 3 draws
  of the per-stream Delta.
- Held-out: per prefix, mean over draws and backbone seeds; per-source mean Delta and its sign over the 4 sources.
  Conditional uncertainty on these fixed prefixes: moving-block bootstrap over batches (blocks of 17) within every
  prefix, pooled mean over the 22 prefixes, 95% interval; it does not generalise beyond these prefixes, and four
  sources do not support a population interval. Selector variability (SD over draws, backbone fixed) and backbone
  variability (SD over seeds, draw-averaged) reported separately.

## Pre-specified reading (descriptive; no pass/fail on the method, DUO's earlier verdicts stand)
- R1 (ranking, mechanism K = 3): an expert-level advantage of ranking is established if the paired-t 95% intervals
  of both Delta_acc and Delta_ll (sel - rand, expert alone) are above 0.
- R2 (deployed, mechanism K = 3): a deployed advantage on controlled recurrence is established if the same holds
  for MICE+sel - MICE+rand.
- R3 (deployed, real): a deployed advantage on the held-out prefixes is established if the conditional intervals of
  both Delta_acc and Delta_ll are above 0 and Delta_acc is positive on at least 3 of the 4 sources.
- Otherwise the paper says "no advantage established" for that comparison (not "not better"). If R2 and R3 are not
  established, the abstract and conclusion say that the gain over MICE is not shown to come from relevance ranking
  rather than from an extra context expert, and the contribution is narrowed accordingly. If R1 holds but R2/R3 do
  not, they say that ranking finds better contexts but MICE's mixture does not turn this into an established gain over
  a random extra expert.
- A recency context of the last 10 batches is MICE's own 1000-row FIFO expert.
Expert check: MiceDuo/logs/duo_review/round1_expert_q1.md (Fable 5.1): adopted (K=3 replicates, stream-level paired t,
log-loss co-primary, ordering descriptive, source-level reporting with 4 sources, hit rate, expert-alone, weights,
t > 10); oracle approved by the user. Reviewer plan check (round1_reviewer_plan_check.md): yes with changes; all four
adopted (deployed decision rule with both co-primary metrics; no prefix-level t interval, source-level effects plus
conditional bootstrap; three draws on held-out with selector and backbone variability separated; matched timing
benchmark and "no advantage established" wording).
