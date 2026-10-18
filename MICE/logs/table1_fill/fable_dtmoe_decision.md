**Decision**
Keep the full registered grid and official sizes for dtmoe. Do not reduce (B) or shrink (C). Run the dev grid on CPU now, 10 single-thread processes in parallel, and run the 92 test streams on the GPU once it has been fault-free for several hours, after adding per-stream checkpointing. If the GPU is still unstable when dev finishes, run test on CPU too. Record the device per stream.

**Supporting evidence**
- 300 core-hours over 10 free cores is ~30 wall-hours for dev. Test at 150–200 core-hours is another 15–20 wall-hours. About two days total, no protocol change.
- Channel independence turns a 100×54 batch into 5,400 short sequences through two MoE layers. That is a GPU-shaped workload. A 20–50× speedup over one CPU thread is plausible, so GPU test runs should finish in hours.
- The dev grid cost is dominated by the 18 configs with n_steps = 5. Those are exactly the configs a reduced grid would drop, and exactly what a reviewer would ask about.
- Runs are deterministic, so checkpointing costs nothing in validity and removes the restart-from-zero penalty during fault storms.

**Alternative options**
- (B) is unfair to dtmoe. Fixing n_steps = 1 and L = 16 while other baselines may select n_steps = 5 under-tunes the one new strong baseline. "Compute restriction" disclosures invite the under-tuned-baseline critique directly.
- (C) confounds the comparison. A smaller-than-official model with the full grid makes any dtmoe loss attributable to size.
- (D) inherits B's problem and produces two sets of dtmoe numbers to reconcile.
- If compute truly forces reduction later, the least-bad cut is dropping L = 32 only, applied after checking that L has no effect on the other four baselines' dev selections. Register before running.

**Key risks**
- CPU contention with other baseline runs during the two days. Check existing run directories and locks before launching ([[parallel-agents]]).
- CPU–GPU numeric drift if dev selects on CPU and test runs on GPU. Mitigate with a one-stream CPU-vs-GPU agreement check and a logged device column.
- The fault storm correlates with two concurrent TabPFN processes. Run dtmoe alone on the GPU, and read env/EXPERIMENT_SCHEDULING.md first for the 28 GB limit.
- The 6.17 s/batch figure may hide an inefficiency such as a per-sample Python loop. Profile one batch before committing 300 core-hours.

**Remaining uncertainty**
Actual GPU speedup and whether the fault storm is hardware rather than contention. Neither changes the decision, only the timeline.

**Confidence**
High that A/E is the fair choice. Medium on the two-day wall-time estimate.

**Requires user approval**
No for the recommended path. It spends compute but changes nothing registered. Yes for B or C, since either alters the registered protocol for one baseline.
