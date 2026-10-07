# Overnight experiments, 2026-10-07

Authorized by the user: run experiments overnight, target GPU utilization >=90%, GPU memory <25 GB;
record findings in project logs and push substantial changes/findings to GitHub. Use WSL/Linux only.

## Frozen plan

1. MICE K2: the existing registration, unchanged. Seed 2 on h3_airlines_b, h3_covertype_b,
   h3_insects_b, h3_poker_b; fifo1000, ddm1000, winens1000, micev1000_500. Evaluate the final
   two-level rule using half Brier, scale=.5, temper=True, with the original checker.
2. DUO development: only the original seven development streams, first 300 batches, B=100,
   M=1000, history H=100, TabPFN v2 with four estimators. Compare mandatory recent anchors of
   300 and 500 rows against the original 100 rows. Rank only older batches outside the anchor
   using its predictive log-loss; append the best older batches to reach 1000 rows. This is
   a joint change of the ranking reference and the amount of mandatory recent data, so an
   improvement would not isolate which mechanism caused it.
3. For every selection, store FIFO, selection alone, original DUO (eta=2, gamma=.5), and
   conservative mixture (half-Brier scale=.5, gamma=.9, tempered weights) without new model calls.
   The conservative rule is an ablation, not a claim that MICE's full theorem automatically applies.
4. Seed 0 is exploratory; seeds 1 and 2 repeat every fixed candidate and original anchor=1.
   Recompute MICE's reference on the same seven development prefixes for each additional seed.
   Original seed-0 DUO and MICE references are read from their archived outputs.
5. Advancement criterion, fixed before runs: a candidate must exceed MICE by >=0.50 percentage
   points on average and on >=5/7 streams, and never fall >0.30 points below FIFO. Report every
   candidate, per seed, regardless of success. A candidate must meet all three criteria on every
   seed before being recommended for a separate frozen held-out evaluation. No held-out run is
   launched automatically; the 22 held-out streams are not used for candidate selection.
6. Report accuracy, macro-F1, macro OvR AUC, ECE and log-loss. Seeds change backbone randomness,
   not data; do not describe them as independent data sources or claim confirmatory significance.

## Execution and limits

Run `bash experiments/night_20261007/launch.sh` from WSL. Environments are in `~/pfn-venvs/`.
Raw results, snapshots, locks and checkpoints are in `~/pfn-runs/night-20261007/` on Linux storage.
Existing repository experiment files are only read. Small new reports and per-project overnight
logs are versioned; raw probabilities/checkpoints are not committed.

The controller starts four workers, grows to at most ten when utilization is below target, and
samples every three seconds. Each worker's PyTorch allocator is limited to 1792 MiB. The controller
pauses workers at 22000 MiB total device use (about 23.1 GB), with emergency termination at 23200 MiB
(about 24.3 GB), leaving headroom below 25 GB. These are observed-resource controls; they cannot
guarantee instantaneous device-wide use if external jobs allocate between samples. RAM admission
requires >6500 MiB available; <4096 MiB triggers a pause. Two successive failed jobs lower concurrency;
Four failures without checkpoint progress (or twenty total failures) block a task and retain its
logs. Productive checkpoint recovery does not exhaust the four-failure allowance. No expandable_segments setting is used.
After recurring launch failures during startup, CUDA_LAUNCH_BLOCKING=1 is enabled as a Linux-side
diagnostic/mitigation attempt. It changes synchronization, not the experiment's prediction rules;
its effect on stability is measured in the resource/event logs rather than assumed.

MICE stores its original checkpoints every 20 batches; FIFO/DDM/window baselines use an equivalent
loop with the same checkpoint interval. DUO checkpoints every 10 batches, including
all losses and predictions needed for exact restart. Completed task markers are written only after
validation. The supervisor has a Linux flock, so duplicate launches cannot execute duplicate queues.
The run stops after eight hours or when all tasks finish/block, whichever comes first. It does not
manufacture GPU work after the scientific queue is exhausted.
`restart.sh` gracefully stops only this run's verified supervisor PID, waits for its workers to
exit, then refreshes controller code and resumes checkpoints. It does not kill unrelated processes.

Completed stages run their analyses automatically. Results including failed hypotheses are appended
to the appropriate `logs/OVERNIGHT_20261007.md` and committed/pushed with an explicit path allowlist.
The publisher refuses to consume someone else's staged work, never force-pushes, and records push
failures rather than auto-merging concurrent changes. There is no message-sending integration.

WSL shutdown kills tmux and GPU jobs. This launcher resumes the queue and checkpoints on a later
manual launch; it does not start Windows programs or change university restart/RDP policy.

## Validation

`python experiments/night_20261007/test_worker.py` checks exact resumed/uninterrupted equality for
all three anchors, original DUO equivalence with a deterministic test predictor, and causal selection.
Before launching, TabPFN v2 was loaded on the actual GPU and predicted a real-data batch successfully.
