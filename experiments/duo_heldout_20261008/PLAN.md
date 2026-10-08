# Frozen DUO held-out confirmation, 2026-10-08

Authorization: after the log review recommended a frozen real-stream evaluation and cost accounting,
the user instructed “按照你说的迭代”. This authorizes this evaluation; no further method search is included.
This plan, evaluator, controller and task/data manifests are hashed before any held-out GPU task starts.

## Scope and fixed method

The 22 real streams below were not used to develop DUO, but were used in MICE. They are not wholly
new benchmarks. Use the first min(30000, floor(n/100)*100) rows, preserving order and preprocessing.
This matches the development and mechanism evaluation length; conclusions concern these prefixes,
not full-stream performance. Batch 0 warms up; score every remaining complete batch.

Sources and streams (all INSECTS variants/segments grouped conservatively as one source):
- covertype: covertype, h3_covertype_b, h3_covertype_c, h4_covertype_d, h4_covertype_e
- airlines: h3_airlines_b, h3_airlines_c, h4_airlines_d, h4_airlines_e
- poker: h3_poker_b, h3_poker_c, h4_poker_d, h4_poker_e
- insects: insects_abrupt_balanced, insects_abrupt_imbalanced, insects_gradual_balanced,
  insects_gradual_imbalanced, insects_incremental_abrupt_balanced, insects_incremental_balanced,
  insects_incremental_reoccurring_balanced, h3_insects_b, h3_insects_c

TabPFN v2, 4 estimators, backbone seeds 0, 1, 2; B=100, M=1000, H=100, anchor=1 batch.
Primary method: add P_sel as exactly one expert to micev1000_500, then simulate2(outer='brier',
scale=.5, temper=True), all other defaults unchanged. Comparators: same-run MICE and its FIFO-1000.
Generate fresh matched caches for each seed. No alternate anchors, nested mixtures or tuning.
22 streams x 3 seeds x (MICE, DUO selection) = 132 GPU tasks.

## Validation and decision (fixed before results)

Require all 132 tasks, exact labels/batch indices, finite probabilities, causal selected indices, and
FIFO probability maximum difference <0.002 (float16 storage). No partial-result verdicts.
Per seed, apply the existing safe-gain criteria on all 22 streams:
1. every stream: accuracy(method)-accuracy(MICE) >= -0.30 percentage points;
2. every stream: accuracy(method)-accuracy(FIFO) >= -0.30 points;
3. mean stream gain over MICE >= 0;
4. mean stream log-loss(method)-log-loss(MICE) <= 0.005.
Overall pass requires all four on every seed. Report exact negative counts, minima and ties, even on
pass. These are empirical tolerance criteria, not statistical non-inferiority or accuracy guarantees.

Report each seed/stream and each source; average streams within source, then give sources equal weight.
Also report the equal-stream summaries used by the frozen decision. Backbone seeds are repeated model
randomness, not independent datasets. There are only four source groups here; report descriptive
variation, not a significance claim based on 22 or 66 independent replicates. Do not select a seed.
Accuracy and log-loss are decision metrics; macro-F1, macro one-vs-rest AUC, ECE (15 bins), Brier are
descriptive. AUC averages classes having both positive and negative examples; report class coverage.

## Cost and execution

Record MICE's batch times/call count and separate selection+selected-context batch times and logical
calls (excluding duplicate FIFO validation). Also count fit/predict_proba calls, since ranking splits
queries into 1000-row chunks. The sum of MICE time and selection time is a component-cost estimate,
not measured end-to-end deployed latency; concurrent contention, warm-up and replay overhead are
reported explicitly. Preserve per-batch timings, successful-attempt peak allocated GPU memory and
whole-device memory samples. Failed/retried work is visible in events/attempt records, not hidden
inside the successful-batch timings. Model initialization is outside batch timing.

Start with one GPU worker (matching the documented safe default), stop on its first failure and retain
checkpoints. No automatic circuit-breaker reset or unapproved concurrency escalation. 24-hour maximum
per invocation; a timeout/incomplete run is not a scientific failure or license to discard streams.
Use the existing resource guard; never change host settings. Automatic analysis only when all tasks
are done; no automatic git push. Frozen snapshots run on Linux storage. On completion write reports
to the run directory; import them into the paper only after validation.

If criteria fail, report failure and preserve this test as used data. Do not retune and re-label it
held-out. Publication value is judged jointly with cost, without an invented post-result cutoff.
