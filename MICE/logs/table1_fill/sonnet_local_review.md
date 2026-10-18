0.0748346 27.939
1. **GPU order (dtmoe before DR)**
   - Problem: the order contradicts the earlier user instruction to fill the other cells first and run dtmoe and TOT slowly. DR is one of those other cells. The plan holds all 92 DR streams back by about 1 to 1.5 days.
   - Evidence: "Fill the other cells first, dtmoe and tot slowly" against plan step (c) and (d), which run before (e).
   - Fix: run only the six probes first, because they take about an hour and answer whether strict mode works locally. Then run DR. Run the dtmoe grid and tests after DR. If the user should decide the order, ask them explicitly.

2. **No review step before committing amendment d**
   - Problem: step (a) commits amendment d straight away. The standing rule is that every strategy goes to the expert and then to Sonnet/MiMo review before acting. This plan is itself only the expert's output.
   - Evidence: the "Strategy: Fable then review" memory and the user's instruction today. Amendment b and amendment c both cite Sonnet or MiMo reviews, and the plan has none.
   - Fix: insert "Sonnet/MiMo review of the draft amendment d, then commit" before any probe runs.

3. **Extension rule applied to dtmoe**
   - Problem: the plan classifies this as "notify, do not block". The user approved the one-time full extension (option A) and "freeze even at n_steps 25" for the four CPU baselines only. For dtmoe it adds about a day of GPU time that the user has not accepted.
   - The plan also never says that the dtmoe grid has an n_steps axis, which boundary triggers the extension, or what the extension grid is.
   - Evidence: amendment c items 1 to 3 name only shifts, fsnet, onenet and adaptz. The plan's own risk list says "roughly a day".
   - Fix: either ask the user, or register the dtmoe boundary axes and extension grid explicitly. Move this item to "requires approval".

4. **Bookend probes are new, and their failure rule is missing**
   - Problem: they are extra checks not in amendment b, and they resemble the verification the user has put on hold ("continue experiments, no verification now"). The plan also does not say what happens if a bookend differs from the pre-grid outputs. Possible consequences are discarding the grid, flagging it only, or stopping.
   - Evidence: the plan states only "require bit-identity". Amendment b item 1 says the probes do not certify other grid points.
   - Fix: either drop the bookends, or register them as part of the run and state the consequence of a mismatch. For example, the affected outputs are flagged "unverified" and nothing is selected or frozen from them. Get the user's agreement either way.

5. **Chain script and restart rules for dtmoe are unspecified**
   - Problem: the plan runs the probes, grid and tests "through the same chain script" with a canary. Only `dr_chain.sh` is described as ready. `verify_chain.sh` refuses dtmoe, and amendment b item 4 enforces this. No rule covers what happens when a dtmoe process dies mid-grid: resume, restart, or quarantine. DR restarts from batch 1, but a dtmoe task has no batches in that sense.
   - Evidence: the plan's own note that `verify_chain.sh` refuses dtmoe, and "restart from batch 1" in `dr_chain.sh`.
   - Fix: name the script, which must be a dtmoe-specific chain or a flag on `dr_chain.sh`. State the per-task restart and quarantine rule, and the output path for each task. Do this in amendment d before the probes.

6. **Approval claim for reopening local dtmoe is stated too strongly**
   - Problem: the plan says no approval is needed because the user "moved the device". Amendment b item 1 records that the stage was closed with user approval (option B). The recomputation was placed on the H800 as part of the user's clean-rerun decision, and "do not use the H800 for now" does not clearly say to run it locally. Amendment b also treats the plan's "re-specified selection" as the only fallback.
   - Evidence: amendment b header ("Approved by the user… option B") and item 1.
   - Fix: send the user a one-line notice before the first probe, with an explicit stop option. Frame it as "dtmoe moves to the local GPU under the amendment b protocol", rather than treating "finish the experiments yourself" as sufficient.
