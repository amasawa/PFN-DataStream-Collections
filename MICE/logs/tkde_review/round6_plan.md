# Round 6 — plan (Claude, 2026-10-09)

Judgement: accepted. The issue is a documentation omission; I checked the frozen implementation (MICE/code/run.py
MiceV1.step and MICE/code/reweight.py simulate2, the replay that produces every reported number):
- Every expert's prediction for batch t is computed and cached when batch t is issued, before its labels arrive.
- Fast level for batch t: w_k proportional to exp(-eta * l_k), where l_k is the log-loss of expert k's cached
  prediction for batch t-1, scored when the labels of t-1 arrive (last batch only, no accumulation).
- Slow level: L_k <- gamma L_k + half Brier score of the default (1000-row window) and of the fast mixture as actually
  issued for batch t-1; v_k proportional to exp(-eta_2 gamma L_{t-1,k}). These are the losses Theorem 2 assumes.
- New stored expert (created when a segment closes): it issued no prediction for t-1, so its l_k is the median of the
  l of the experts that did. A merged expert keeps its identity and its cached prediction history.
- Order within a step: (1) score cached predictions of t-1; (2) add t-1 to the windows, close a segment and merge or
  add; (3) predict batch t with every expert, cache, mix.

Change (method unchanged): rewrite Algorithm 1 in this order with the caching, scoring and initialisation rules;
add a short "Timing" paragraph in Section 4 linking the slow-level losses to the issued predictions and stating that
Theorem 2 applies to them; note that every reported number is computed this way from the cached predictions.
