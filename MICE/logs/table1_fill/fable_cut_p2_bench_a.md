**Decision**
- **Q1: keep P2 on the cluster** as registered. Dropping it saves nothing that matters.
- **Q2: keep the 5 benchmarks on the cluster.** They are not timing-only, so the fault reaches them directly.

**Supporting evidence**
- **P2 integrity is not the issue, but hardware and provenance are.** ACTIVATION item 3 fixes Table 1 timing and peak memory for CPU methods on one cluster node type. Dropping P2 puts four Table 1 rows on an Intel desktop and the rest on A800 nodes. The original CPU outputs also come from a venv whose versions were never recorded. The cluster run under env_lock repairs that.
- **P2 costs no GPU-hours and no calendar time.** It runs on the ~444 non-GPU cores alongside P1. P2b's round trip coincides with the dtmoe stage 2 round trip, which happens anyway.
- **Local P2 outputs are already partly unusable for timing.** Four extension processes have invalid wall-time arrays after the SIGSTOP/SIGCONT deviation.
- **The benchmarks carry accuracy, not only time.** bench_accuracy_runs.csv feeds tab_cost_rows.tex. Those predictions were made on the faulty GPU. The local timings also come from the faulty machine, with 3 crashed runs in r13 a1.
- **PLAN.md already commits to cluster numbers.** Cost-matching claims are "re-evaluated on the H800 [A800] numbers, not carried over". Keeping local numbers contradicts the registration.
- **Savings are small.** About 19 exclusive GPU-hours out of 760-960, about 2-2.5 percent. Scheduled into the GPU-idle gap of the select/extend/test round trip, the calendar cost is zero.

**Alternative options**
- Reduced P2: cluster-run only the four CPU baselines (ts_dev, extension, selection, tests, timing); report river/trained/arf/srp as "CPU local" with the flag. Saves CPU core-hours only, which are not the bottleneck. Not recommended.
- Reduced benchmarks: drop r13 a1 and r14b a1 (timing sweeps, ~11 GPU-h), keep a2 and the tkde bench. But budget compliance of k* on the A800 needs the a1 timing curve. Not recommended.

**Key risks**
- Benchmarks get one attempt; a failed one leaves a hole in the cost table. Mitigate by running them exclusively (no MPS sharing, no co-tenant on that GPU) and only after GPU health is checked.
- The "runs alongside P1" assumption for P2 depends on CPU nodes actually being free under the 500-core account cap.
- The analyse_bench/analyse_pools/analyse_14b path adaptations must be audited before the A800 analysis; this is a coordination item, not a compute item.

**Remaining uncertainty**
- Whether the cluster CPU node type gives timings comparable in spirit to what the paper discusses; the paper reports whatever it measures, so this is a wording question.
- Whether 5 exclusive GPUs are free in the round-trip gap; if not, the benchmarks cost about 6 h wall at the end.

**Confidence**: Q1 high (~85%). Q2 high (~90%).

**Requires user approval**: none for keeping both, which is the registered status quo. Dropping P2 reverses user decision 5 and ACTIVATION items 3-4; dropping the benchmarks changes the PLAN benchmark section and the hardware rule of item 3. Either needs an amendment before any score is read.
