**Decision:** Treat this as a **P0 integrity incident**, with confirmed silent corruption in the demonstrated DR batch. Past FECS-exposed results are **suspected affected, not individually proven wrong**. Preserve them and suspend their use for new scientific conclusions pending verification.

**Yes, one GPU process may continue provisionally tonight**, prioritizing verification over new development, TOT and the 83-hour DR run. Four event-free hours support this restriction; they do not certify the GPU.

**Supporting evidence:**

- **Severity:** P0.
- **Finding status:** Confirmed issue for the demonstrated silent output failure; Suspected issue for historical FECS-exposed outputs.
- **Location:** Supplied DR GPU run 2, batch 11, finishing at 14:17:18; listed exposed run directories.
- **Evidence:** Same-device deterministic replay changed probabilities by 0.868 and accuracy from 0.76 to 0.32 without an exception, coincident with FECS. Conversely, 60 runs reproduced per-batch accuracy, establishing substantial successful computation during FECS.
- **Why it matters:** Successful completion cannot establish correctness. Equal batch accuracy can conceal different predictions and probabilities; corrupted state can affect subsequent batches and checkpoints.
- **Recommended correction:** Independent, isolated replay with unchanged inputs, code, environment and seeds; compare saved numerical outputs before accepting downstream claims.

The confirmation log records 66 successful GPU tasks and closely separated methods ([log](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/logs/EXPERIMENT_LOG.md:1084)). These deserve priority.

**Alternative options — recommended verification order:**

Each “task” below means its **complete original stream**, starting from clean initialization. Preserve original artifacts; write verification outputs separately.

| Priority | Verification job | Number and order |
|---|---|---|
| 0 | Qualify tonight’s execution | **Two independent 12-batch DR GPU canaries**, sequential fresh processes, plus **one complete dtmoe task** against the known matching 12:48 reference. Require exact GPU-to-GPU numerical agreement. Use the existing CPU DR output as an additional diagnostic; CPU/GPU bit identity is not required. |
| 1 | Remove uncertainty from dtmoe selection | **All 32 task IDs 6–37**, including fresh completion of missing outputs. Also rerun **task 38** from initialization if continued from an exposed checkpoint; include any additional task whose execution/state actually overlaps the window. Compare probabilities, predictions, accuracy and recorded mechanism state. Complete this before configuration selection. |
| 2 | `mice-confirm-cp-20261017` | **All 54 primary tasks:** first mice_cp/mice pairs across nine segments (**18**), then FIFO/DDM (**18**), then remaining methods (**18**). Follow with **12 supplementary tasks: 66 total**. Verify derived cache/replay results from these inputs. |
| 3 | `mice-r14-confirm` | **All 216 tasks**, the count recorded in the scheduling file. Spread early checks across methods, datasets and execution times; finish the census before clearing this frozen confirmation set. |
| 4 | Remaining Table 1 GPU sources | `mice-table1-probs-gen`: **all 60 tasks**, comparing full probabilities and predictions. Then `mice-table1-cp-gen`: **all 30 tasks**. Then `mice-main-cp-grid10`: **every task in its manifest**; its count is not supplied. |
| 5 | Other exposed runs | `mice-r14-exist`, `mice-r14b-acc`, `duo-rand-20261017`, `duo-rand-verify`: initially **min(12, N) complete tasks per directory**, stratified by execution time and method/data configuration, chosen without looking at scores. Then verify **all tasks feeding reported claims or model selection**. Agreement between two FECS-exposed runs does not independently clear them. |
| 6 | Earlier results without retained events | **12 complete tasks initially**, spanning dates, model families and consequential claims. Include earlier sources of current tables. Expand any affected lineage after a discrepancy. A passing sample supports only the checked tasks. |

**Stopping rule:** Any new FECS/Event 153, GPU exception, disagreement between clean replicas, failed canary, or loss of event monitoring → Claude stops GPU execution and preserves the evidence. Do not automatically resume potentially contaminated checkpoints.

For an **old-versus-new mismatch**, stop clearing that result family and perform **one additional independent replay** of that task. If the two new runs disagree, stop GPU verification. If they agree against the original, record confirmed non-reproduction and expand to the entire affected dependency lineage; retain all versions. Never retry until a preferred answer appears.

Compare full per-example predictions/probabilities and available state, not merely aggregate accuracy. Preserve frozen analyses and avoid interpreting partial confirmation scores.

**Key risks:** Probability corruption invisible to accuracy checks; propagation through checkpoints; corrupted development scores changing model selection; timestamp uncertainty. File mtimes are screening evidence, not precise exposure boundaries. Startup canaries alone cannot protect an 83-hour run: repeat between streams and monitor events throughout.

**Remaining uncertainty:** Historical corruption prevalence, exact onset, and reliability of continued single-process operation. Neither 14,400 correlated calls nor missing older event records establishes a population-wide error bound. A passing sample cannot clear unsampled results.

**Confidence:** High in the integrity incident and verification priority; moderate in guarded single-process continuation; low in estimating historical damage.

**Requires user approval:** **No** for the authorized isolated verification and existing single-process workload restriction ([instruction](/mnt/c/Users/zhwu9808/Desktop/dataStream/env/EXPERIMENT_SCHEDULING.md:104)). **Yes** before replacing reported results, changing frozen scientific procedures or criteria, or adopting revised conclusions. The existing authorization for 92 DR streams remains; I recommend putting the verification queue first tonight.