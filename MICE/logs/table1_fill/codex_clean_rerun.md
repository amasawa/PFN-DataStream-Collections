**Decision:** Sound in principle, **not ready for execution**. Register this as an integrity-recovery amendment made after seeing the originals. Recomputing fixed confirmatory evaluations is defensible; it does not create fresh held-out evidence or additional independent samples. Keep MICE’s development selections frozen. Retain genuinely CPU-only results, but recompute CPU analyses dependent on GPU outputs. The proposed reporting rule is appropriate.

**Supporting evidence — required edits:**

1. **Severity:** P1. **Finding status:** Confirmed issue.  
   **Location:** [MANIFEST.md:24](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/MANIFEST.md:24), [paper:1043](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:1043).  
   **Evidence:** Development outputs are excluded, although the paper reports development-derived numerical claims.  
   **Why it matters:** “Every GPU-computed paper result” is not covered.  
   **Recommended correction:** Freeze the complete number-to-source inventory **before execution**. Recompute development outputs needed for reported numbers, without reopening selection. Entire unused tuning grids need not be rerun.

2. **Severity:** P1. **Finding status:** Confirmed issue.  
   **Location:** [analyse_pools.py:75](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_tkde_control/analyse_pools.py:75), [analyse_14b.py:80](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_r14/analyse_14b.py:80).  
   **Evidence:** Benchmark analysis recomputes/writes or checks newly selected k*; benchmark paths still target original roots.  
   **Why it matters:** “Unchanged analysis” does not automatically preserve frozen selections while consuming H800 measurements.  
   **Recommended correction:** Register audited path/reporting adaptations separating measurement from selection. Preserve k*/M* immutably; reassess their budget compliance on H800 without reselection. Do not carry forward “cost-matched” claims automatically.

3. **Severity:** P1. **Finding status:** Confirmed issue.  
   **Location:** [PLAN.md:42](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/PLAN.md:42), [HANDOFF.md:62](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/HANDOFF.md:62).  
   **Evidence:** PLAN permits using a nondeterministic pipeline’s single run; HANDOFF requires stopping it.  
   **Why it matters:** A mismatch does not establish benign nondeterminism.  
   **Recommended correction:** Adopt one rule: pause the affected pipeline, preserve evidence, diagnose, and approve/register its disposition before production. Preserve dtmoe’s existing fallback. Specify numerical comparisons, excluded metadata, probes under production concurrency, and ongoing device-health checks. Passing two runs does not certify every task or GPU.

4. **Severity:** P1. **Finding status:** Confirmed issue.  
   **Location:** [rerun.py:87](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/rerun.py:87), [make_tasks.py:81](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/make_tasks.py:81).  
   **Evidence:** Failed tasks automatically retry with checkpoint resumption; 122 tasks declare no expected outputs and can pass on exit status alone.  
   **Why it matters:** Completion can accept incomplete output or potentially fault-exposed state.  
   **Recommended correction:** Enumerate expected artifacts and validate their structure/counts. Distinguish validated benign preemption from GPU/integrity failures; quarantine affected attempts and restart those tasks from initialization. Record bounded retries and a score-independent acceptance rule.

5. **Severity:** P1. **Finding status:** Missing information.  
   **Location:** [PLAN.md:22](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/PLAN.md:22), [HANDOFF.md:40](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/clean_rerun_mice_h800/HANDOFF.md:40).  
   **Evidence:** Additive code changes are asserted equivalent; the downloaded TabICL checkpoint gets a hash without an explicit original-checkpoint comparison.  
   **Why it matters:** Unchanged computation is not yet established.  
   **Recommended correction:** Freeze and verify original-to-rerun code, data, checkpoint, selection and task identities. Document any unavoidable difference. Register TOT separately before its execution.

**Alternative options:** Keep the fixed-selection correction as primary. Any H800-specific retuning should be a separately registered secondary study.

**Key risks:** Frozen selections may retain consequences of faulty development computations; clean evaluation tests those selections but does not validate their original justification. Extend the appendix to figures/text, uncertainties and missing results. Update abstract and main claims consistently; preserve exploratory versus confirmatory labels. Old/new differences alone cannot identify corruption.

**Remaining uncertainty:** Full dependency coverage, original artifact equivalence and cluster reliability remain unverified. This session’s exact model/effort routing is also unverified.

**Confidence:** High in the methodological decision; conditional on these execution safeguards.

**Requires user approval:** The existing decision already authorizes replacement and reporting changed conclusions. Under the supplied protocol, the finalized amendment still needs MiMo Pro High review, verified Astra Extra High assessment, explicit user approval and commitment before execution.