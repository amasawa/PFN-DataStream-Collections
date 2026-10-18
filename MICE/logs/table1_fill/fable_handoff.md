**Decision**
Split and order are right; not yet handoff-ready. Three fixes first, all registration/text and commit state, none in the computation code. Then the third Codex rebuttal, user approval, commit, bundle.

**Supporting evidence**
- The split is correct: everything FECS-exposed goes to the H800 in one registration, so no reported GPU number depends on a choice of what to rerun. The four CPU baselines were never exposed. Keeping DR local was my earlier call under a "no cluster yet" assumption; with the cluster available, a second FECS-exposed 83 h run is strictly worse than one clean run. Local GPU idle or canaries only.
- Codex items 1 and 2 are closed in `rerun.py:136-175` and `valid()`: acceptance = rc 0 of a recorded attempt + structural schema per output, attempts persisted across workers, pre-existing outputs quarantined. `run.py:430` removes the checkpoint on success, so the `.ckpt` check in `complete()` will not reject good tasks.
- dtmoe strict mode is wired (`run_ts.py:26-28`, `TS_DETERMINISTIC=1` + `CUBLAS_WORKSPACE_CONFIG` on all 180 tasks) and the probe list covers L16 and two L32 configs; a "no deterministic implementation" error pauses the pipeline. That matches amendment b.

**What blocks (fix before handoff)**
1. PLAN.md and MANIFEST.md contradict tasks.jsonl. PLAN lines 26-28 and MANIFEST line 25 still say mice-r14-dev and devtrim are not rerun; PLAN says 2664 tasks, the file has 2828; `run_task_trim1.py` cites a PLAN section "Reconstructed runs" that does not exist. The executor is told PLAN is the registration. Codex item 3 is therefore only half-closed. The new section must say: r14-dev is recomputed under one code state (current run_task.py) and devtrim via a TRIM=1 class override on committed code, so both are reconstructions, not replays, and old-new differences there are not read as fault evidence. Also fix stale text in HANDOFF step 4 and the `release()` docstring ("drivers resume from their checkpoints"), which contradicts the fresh-start rule; the code is right, the text is wrong.
2. Commit state. `rerun.py` and `run_drtabpfn.py` are modified and uncommitted; `run_task_trim1.py` and `select_frozen.py` are untracked. The registered commit, the bundle hashes and the executor's clone all key on one commit. Commit these in the registration commit, nothing else.
3. Disposition of the local DR run. If DR moves to the cluster, state in the PLAN what happens to the local run (stop it, or finish as an unverified cross-device comparison, never merged). The cluster output path is fresh, so no collision, but the bundle must not carry local DR outputs (it does not now; keep it so).

**Alternative options**
- Keep DR local and send only the rest. Rejected: same cost, FECS exposure remains, and the paper would mix two GPU provenances in Table 1.
- Skip the third Codex pass and go to user approval. Not recommended: the rebuttal explicitly left items 1 and 4 open, and the reconstruction section is new scope for the reviewer.

**Key risks**
- A Slurm kill mid-attempt leaves no record in `attempts/`, so killed attempts do not count toward the limit of 3. Acceptable, but a task on a flaky node can loop; the executor's status checks catch it.
- Results sets under `MICE/results_*` are gitignored (`*.npz`, `*.pkl`), so the clone is clean; the HANDOFF count check still runs. Good.
- Order of return: dtmoe test tasks depend on the dev-grid freeze. The addendum path is correct, but the freeze must be done by the coordinator without scores being visible to the executor, as HANDOFF rule 3 says.

**Remaining uncertainty**
- Whether `torch.use_deterministic_algorithms(True)` runs for every dtmoe op on Hopper; the probe decides.
- The TabICL checkpoint identity stays unverifiable; already registered as a known limitation.

**Confidence**
High on the split and order. High that the three items above are the only blockers in what I read. Moderate on cluster behaviour, untested.

**Requires user approval**
Yes: the revised PLAN (reconstruction section, DR moved to cluster, local DR disposition) before commit and bundle. No new user decision for the CPU side or the addendum mechanism.