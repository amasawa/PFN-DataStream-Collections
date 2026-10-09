Decision question (senior expert, read-only). Read MICE/logs/tkde_review/round9_codex.md (reviewer's round-9 issue)
and MICE/logs/tkde_review/round9_plan.md (my plan). Context: MICE/code/run.py (fifo{M} baseline, MiceV1), the
paper MICE/overleaf/tkde/main.tex. The GPU is busy for several more hours with a registered control run; new runs
would follow it. Machine rules: env/EXPERIMENT_SCHEDULING.md.

Confirm or correct before I register and run: (1) Are FIFO with M = 5000 and 12 000 the right budget-matched
baselines (memory-matched vs inference-matched), or is another configuration needed (e.g. window ensemble with more
windows, or MICE's per-batch call count)? (2) Is the isolated benchmark design (3 streams x 300 batches, metrics)
adequate for latency/throughput/peak-memory claims? (3) Anything to register now so the result cannot be spun (e.g.
how a larger FIFO beating MICE must be reported)? Constraints: method frozen, no new data.
Answer concisely: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty /
Confidence / Requires user approval.
