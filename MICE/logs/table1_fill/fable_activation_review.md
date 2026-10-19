# Activation note: Fable review (2026-10-19 23:55-23:57, ~1.10 USD)

You are the senior expert (read-only). Review the registration note experiments/clean_rerun_mice_h800/ACTIVATION_20261019.md (uncommitted) against PLAN.md, HANDOFF.md in the same directory, experiments/mice_table1_fill_20261018/AMENDMENT_BASELINES_20261018{c,d,e}.md, experiments/gpu_verify_20261018/AMENDMENT_20261018b.md, and your earlier advice MICE/logs/table1_fill/fable_h800_activation_a.md and fable_backbones.md. The user's decisions quoted in the note are final; do not reopen them.
Answer: Decision (register as is / register with changes) / required changes (at most 6, each with exact replacement text) / Key risks / Confidence. <= 450 words. Focus: integrity holes (post-hoc choice between local and cluster runs, reporting rules fixed before results, thresholds that could be tuned after the fact), contradictions with PLAN.md / amendments, and anything the cluster executor could misread.

## Answer
**Decision:** register with changes (six below). The structure is sound; the holes are all "a choice made after a result exists."

**Required changes**

1. **Item 4, last sentence** (post-hoc local-vs-cluster choice). Replace "If the cluster cannot run a set for a reason unrelated to results, the user decides what is reported." with: "If a cluster set cannot run, the reason is logged before any cluster score of that set exists; that set is then reported from the local CPU outputs with the flag 'CPU local', without choice. No local extension, selection (select_frozen.py --final) or test score of the four CPU baselines or of dtmoe_cpu is read before the P2 selection is committed from cluster outputs; frozen_<method>.json stays a record, not a P2 input."

2. **Item 2, time cap** (undefined reference run). Append: "The default-mode reference is one run per probe task on the same H800 with TS_DETERMINISTIC unset, into $WORK/qualify/ref_<n>; its wall time is the only value read and its outputs are never used. Each of the three probe tasks must finish within the cap; one 'too slow' stops the dtmoe path."

3. **Item 3** (timing contradiction). Append: "Amendment d item 8 (GPU timing on the local GPU), amendment e item 6 (CPU footnote, CPU timing) and amendment c item 7's 'local CPU' no longer apply: timing and peak memory of every Table 1 method are measured on the cluster, GPU methods on an H800, CPU methods on one cluster CPU node type, registered with P2."

4. **P3 exclusion rule.** Replace "out of memory under 28 GB; time per batch above 20 times that of TabPFN v2 measured in a result-blind smoke test" with "out of memory with a 28 GB per-process cap enforced on the H800 (torch.cuda.set_per_process_memory_fraction); time per batch above 20 times that of TabPFN v2, both measured in the same smoke test on an H800. The smoke test writes no accuracy array (predictions discarded)." Also replace "every backbone that is started" with "every backbone listed in the P3 registration".

5. **CURE tuning branch** (result-contingent). Replace the sentence from "If CURE needs tuning" to the end of the bullet with: "No tuning. If a default is undefined for this setting (no value in code or paper), the value and reason are fixed in the P4 registration before any run. CURE uses the main table's streams, seeds, batch size and backbone; no registered hypothesis names CURE; every CURE cell is reported whatever its value; MICE's constants and claims are unchanged."

6. **P6 and PLAN.md header.** Replace "P6: TOT." with "P6: TOT, gates and device (CPU) as amendment c item 5, registered separately." Change PLAN.md line 1 in the same commit to "Registered by ACTIVATION_20261019.md; this note holds on conflict", since HANDOFF tells the executor to read PLAN.md first and it still says DRAFT.

**Key risks**
- Cluster CPU nodes differ from the local CPU: P2 may not be bit-identical to local runs. Say now that differences are reported, not chosen between (same rule as PLAN "What changes").
- The 10x cap is below the local 40x slowdown; expect "too slow", and have the fallback registered before the probe runs rather than after.
- Public repo: grep the note and bundle manifest for the account name and any absolute Mac paths before pushing.
- The TabICL protocol wording matches main.tex line 1523, so P3 is consistent with the paper.

**Confidence:** high on changes 1, 2, 5 (direct integrity holes); medium on 3 and 4 (depend on cluster CPU node availability and whether a per-process memory cap is enforceable under Slurm gres).

## Disposition: all six changes accepted and applied.

# Sonnet check of the applied diff (23:57-23:58)
1. **Change 3 (timing) is only partly implemented and leaves a contradiction.** Item 3 reverses the old timing amendments, but item 2 still has the "too slow" cap measured against a default-mode reference on the H800. Item 4 also still refers to "the CPU dtmoe", which item 2 cancels. Fix: delete "or of the CPU dtmoe" in item 4, or write "the (cancelled) CPU dtmoe".

2. **Change 1 is changed in meaning.** The expert said a set that cannot run is reported "from the local CPU outputs with the flag 'CPU local', without choice". The diff keeps that, but the trigger, "the reason is logged before any cluster score of that set exists", is weaker than the expert's. Also, "Local CPU runs that are still going may finish but are not used for reporting" contradicts the "CPU local" fallback. Fix: write "not used for reporting except under the 'CPU local' rule of this item".

3. **Change 6 is only partly implemented.** P6 now reads "gates and device (CPU) as amendment c item 5", but the expert's "registered separately" is placed differently and the sentence is ambiguous: it could mean TOT is registered separately or the gates are. Fix: write "P6: TOT, with gates and device (CPU) as amendment c item 5; its task list is registered separately before it runs."

4. **"Key risks" are not covered.** The expert asked for a stated rule that cluster-versus-local CPU differences are reported, not chosen between. Item 4 has this. But the "too slow" fallback is not registered before the probe runs: item 2 sends the path to the user afterwards. Fix: name the fallback options and the decision rule now, or state that the user's choice is made before any dtmoe production run and is not conditioned on any score.

5. **The executor can read item 2 two ways.** "Within 10 times the default-mode time of the same task" could mean one reference run or the average over the probe tasks. The new sentence says each task, but "one 'too slow' stops the dtmoe path" conflicts with "goes to the user". Fix: write "stops the dtmoe path and goes to the user as above".

6. **Transport leaks (the expert's public-repo risk).** The diff puts `C:\Users\zhwu9808\Desktop\...` and the account name in a public repo, and the expert asked to grep for the account name and absolute paths. Fix: replace them with "the bundle directory on the Windows machine" and run the grep before pushing.

## Disposition
- 1-5 accepted and applied (wording).
- 6 rejected: the account name and /mnt/c/Users/zhwu9808 paths already appear in 106 committed files of the public repository; the desktop path is needed by the executor; no secret is involved.
