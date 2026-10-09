**Decision:** Revise the plan before registration; keep MICE frozen.

- **FIFO-5000 and FIFO-12000 are useful operating points, but neither is established as inference-matched.** Match inference budgets using measured end-to-end time, not context size or call count.
- For the plan’s **13,400 context-slot ceiling**, replace FIFO-12000 with **FIFO-13400**. Call this *context-capacity matched*, not GPU-memory matched. Nested windows share observations; counting their union gives a different ceiling, at most 13,000 rows. Register the accounting convention explicitly.
- Three streams × their first 300 batches supports a **hardware-specific prefix benchmark**, not general steady-state or worst-case resource claims.

**Supporting evidence:**

1. **Severity: P1. Finding status: Confirmed issue.**  
   **Location:** [run.py:133](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/run.py:133), [plan:9](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/logs/tkde_review/round9_plan.md:9).  
   **Evidence:** Segment closure performs two cross-fit predictions **plus one prediction per existing pool expert**. With twelve experts, the upper bound is 29 calls on a closure batch and 17.8 calls/batch averaged over five batches with a full pool—not 15 plus three per closure. Single-class contexts can skip actual backbone execution.  
   **Why it matters:** The proposed inference-budget rationale understates maintenance work; calls also have different context/query sizes.  
   **Recommended correction:** Correct the paper and registration; record actual calls, their sizes, and pool occupancy.

2. **Severity: P1. Finding status: Confirmed issue in the proposed measurement mapping.**  
   **Location:** [main.tex:425](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:425), [run.py:314](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/run.py:314), [reweight.py:151](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/reweight.py:151).  
   **Evidence:** `micev1000_500` emits the single-level mixture; reported MICE accuracy uses `simulate2`. Stored timing excludes replay and checkpoint serialization; replay outputs inherit that timing.  
   **Why it matters:** Those timings alone do not measure the reported predictor end to end.  
   **Recommended correction:** Include the frozen two-level aggregation. Distinguish online prediction/update cost from cache, checkpoint, and evaluation overhead; verify any streaming wrapper against frozen replay predictions.

**Alternative options:** A larger window ensemble is optional, not mandatory for this bounded FIFO tradeoff study. If claiming **equal-time superiority**, preregister a bounded, accuracy-blind timing calibration to select a FIFO capacity near MICE’s measured cost. If none fits, report unmatched operating points. More windows alone does not establish matching; their sizes and aggregation must also be frozen.

**Key risks:** Register these details now:

- **Coverage:** Exact stream IDs and batch indices. Separate startup from later operation; add a fixed later interval with causally accumulated state, or restrict claims to the first 300 batches. Report occupancy rather than assume the pool fills.
- **Timing:** Prefer three fresh-process repetitions with balanced method order. Report mean, median, p95 and maximum batch latency, closure/non-closure latency, and throughput as total rows divided by total elapsed time. Fix startup and I/O inclusion.
- **Memory:** Report peak allocated **and reserved** GPU memory, host-process peak RAM, and logical context storage separately. Full-stream input loading and growing prediction caches make process memory different from bounded learner state. Synchronize CUDA around wall-clock measurements; allocated tensor memory alone is not total GPU usage. [PyTorch documentation](https://docs.pytorch.org/docs/2.14/notes/cuda.html)
- **Scope:** Pair accuracy and cost on the same measured intervals. Do not attach three-prefix costs to the 29-stream accuracy average as though costs were measured across all 29.
- **Reporting:** Freeze configurations, seeds, averaging, failure/retry rules and resource limits. Show every comparator, including infeasible runs. Preserve the RQ3 bootstrap as an approximate, fixed-stream analysis; add two-sided intervals for differences. A nonsignificant difference is not equivalence. Define “matches” and “similar cost” numerically beforehand, or avoid those labels.
- **Adverse outcomes:** If a larger FIFO is at least as accurate and cheaper on a measured operating point, report that dominance prominently. If it is more accurate but costlier, report the tradeoff. Revise abstract/conclusion claims accordingly; do not silently select the best FIFO separately on each stream.

**Remaining uncertainty:** Actual capacity-to-time scaling, pool occupancy, large-context feasibility, and later-stream peaks remain unmeasured. The proposed evidence cannot establish performance across hardware or independent data sources.

**Confidence:** High on the accounting corrections; moderate on benchmark sufficiency after these revisions. Active model variant/effort remain unverified.

**Requires user approval:** Any amendment to existing frozen procedures requires explicit approval under [AGENTS.md](/mnt/c/Users/zhwu9808/Desktop/dataStream/AGENTS.md), including its prescribed reviews. A separate registered supplement should preserve existing runs and criteria. Exclusive timing after the control finishes is explicitly supported by [the scheduling rules](/mnt/c/Users/zhwu9808/Desktop/dataStream/env/EXPERIMENT_SCHEDULING.md). No files or jobs were changed.