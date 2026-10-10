Make **the value of recall** the organising claim: the learning curve determines the opportunity, identification makes that opportunity accessible, and the slow level controls discounted loss when recall is unhelpful.

Two distinctions must remain explicit. Mixed contexts remove the recall theorem’s guarantee; the theorem does not itself predict the observed losses under shifted boundaries. Similarly, the slow-level theorem bounds **discounted half-Brier regret**; accuracy non-inferiority is supporting experimental evidence. The manuscript does not report learning curves for most real streams, so their behaviour is *consistent with* the proposed explanation, not direct verification of flat curves.

All line references below refer to [main.tex](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex). No files were changed.

**1. Proposed section-by-section outline**

| Section title | Claim and supporting material | Placement of unfavourable results |
|---|---|---|
| **1. Introduction: Recall or Relearn?** | Contexts provide training-free memory. Its value depends on how much relearning a recurrence requires. Compress the three observations into the motivation, then introduce the area formula and two-level method. | Mention the two operating regimes—valuable recall and little recall opportunity—without rehearsing every comparison. |
| **2. Recurring Concepts and Context Policies** | Define the stream, delayed labels, context budget, recurrence and reference policies. Retain current Section 2. | State the comparison budgets precisely: 1000 rows **per context**, with multiple contexts for MICE. |
| **3. Theory: The Value and Cost of Recall** | Lead with the learning curve and area formula. Present fast identification as the condition enabling recall, then the slow safeguard. Put discrepancy analysis last as the basis for organising contexts. Proofs remain in Appendix A. | Keep all theorem assumptions. A flat curve eliminates the area term; mixed contexts fall outside the single-concept premise; the safeguard concerns Brier loss. |
| **4. MICE: Memory with Two Time Scales** | Explain windows, stored contexts, directed recall-regret merging, fast weights, slow weights and causal timing. Retain the algorithm. | Explain fixed segmentation and computational cost directly. Move replay implementation history and freeze chronology to the provenance appendix. |
| **5.1 Experimental Design** | Briefly define datasets, baselines, metrics, budgets and uncertainty estimation. | Identify development versus confirmatory evidence in one sentence and refer to the provenance appendix. |
| **5.2 Learning Curves Predict Recall Gains** | Combine current RQ1 and the aligned-grid part of RQ2. Correlations 0.94/0.83; hardest-cell gain 8.5 points; `tab_grid_rows.tex`; standard-generator results. | Place near-zero generator gains here as the low-area regime. Explain the ideal boundary reset versus experimental DDM comparison. Retain the distinction between original and corrected curve predictions. |
| **5.3 Concept-Pure Memory and Boundary Sensitivity** | Test the premise that stored rows represent one concept. Use `tab_misaligned_rows.tex` and `tab_offset_rows.tex`. | Keep the +0.47-point misaligned mean, shifted mean −3.7, losses on 7/8 shifted streams, and archive superiority prominently here. Preserve the block-length confound and added-prefix-history qualification. |
| **5.4 The Slow Safeguard on Real Streams** | Connect small expert margins to the role of the slow level. Use `tab_real_summary_rows.tex`, `tab_real_rows.tex`, slow-level ablations, regret checks, second backbone and second seed. | Keep Spam’s inconclusive non-inferiority, the missed second-seed ranking criterion, the trained-learner exception, fast-only losses and the log-loss failure here. Explain the 0.4-point aligned-grid cost of the slow level. |
| **5.5 Pool Organisation, Probability Quality and Resources** | Separate the benefits of retaining contexts from the properties of particular pool policies. Use `tab_pool_grid_rows.tex`, `tab_pool_real_rows.tex`, `tab_metrics_rows.tex`, `tab_cost_rows.tex` and `tab_fifo3000_rows.tex`. | Retain +0.30 versus the archive, the unmet +0.5 criterion, +0.07/−0.08 real-stream differences, and fewer experts/calls. Keep LTM’s AUC advantage and MICE’s calibration trade-off. Put FIFO-3000’s 21/29 wins, MICE’s +0.31 mean, and prefix-only cost measurements here. |
| **6. Related Work** | Position context-based recall, discrepancy analysis and discounted aggregation against existing approaches. | Describe the implemented merging rule as **directed recall regret**; the excess-risk discrepancy is a related theoretical object. |
| **7. Discussion and Limitations** | Explain when the results support using memory: costly relearning, usable stored contexts and substantial change. | Consolidate fixed-segment fragility, small real-stream gains, larger-window advantages, probability-quality costs, limited independent sources/seeds and hardware scope. Change-point segmentation remains future work. |
| **8. Conclusion** | Return to the central result: learning curves quantify recall opportunity; two time scales combine recall with a default window. | One sentence summarises the scope: gains depend on usable memory, while real-stream evidence supports empirical non-inferiority to the default window. Avoid repeating the full limitations inventory. |
| **Appendices** | **A:** Proofs. **B:** Registration, Development History and Result Provenance. **C:** Experimental Specifications and Full Results. | Appendix B consolidates existing registration history, failed criteria, replay provenance, curve-data overlap and sensitivity checks. Appendix C retains detailed tables and definitions. |

Keep every `tab_*_rows.tex` unchanged. Reorganise their surrounding discussion and table placement.

**2. Defensive sentences to delete or move**

“Delete” below means delete that occurrence or the explicitly identified clause. It never means suppress the underlying result. Mixed sentences require splitting.

| Lines | First words / targeted span | Action | Reason |
|---|---|---|---|
| 143 | “this is a result about the discrepancy, not evidence…” | delete | Interrupts the contributions with a rebuttal; distinguish theoretical and empirical contributions affirmatively. |
| 254 | “without further conditions” | delete | Redundant aside after a conditional proposition. |
| 432–438 | “The cache holds every expert’s prediction…” through “which we do not report” | move-to-appendix | Replay implementation and result provenance; retain causal timing in Section 4. |
| 442–443 | “All constants were set…” | move-to-appendix | Parameter-selection provenance. |
| 502–508 | “Hypotheses, data and decision rules…” | move-to-appendix | Consolidate development and registration chronology. |
| 514–515 | “We measured the learning curves… and only then…” | move-to-appendix | Chronology; start the results with the prediction and observation. |
| 519–524 | “The registered predictions used a simplification…” | move-to-appendix | Preserve original/corrected predictions together; retain the table’s \(M\)-row assumption and appendix reference. |
| 527–528 | “The two seed pairs answer different questions.” | delete | Metatext; state the two evidence scopes directly. |
| 528–533 | “The curves were measured on the concepts…” | move-to-appendix | Detailed sampling/overlap provenance; retain a concise main-text scope statement and sensitivity result. |
| 535–536 | “Recurring-concept memory cannot be evaluated…” | delete | Dismisses the useful near-zero-gain evidence instead of interpreting it. |
| 567–568 | “Every stage was run once…” | move-to-appendix | Registration history in a results caption. |
| 596–597 | “In response to review…” | delete | Review chronology; retain the test design and unchanged constants. |
| 602–604 | “The registered criterion…” | move-to-appendix | Move criterion specification; retain 8/12, +0.47 and a brief statement that the criterion was unmet. |
| 621–622 | “so the registered descriptive criterion…” | move-to-appendix | Move threshold specification; retain the observed failures and criterion outcome. |
| 634 | “the average advantage fails both registered robustness criteria” | delete | Repeated verdict after both tests have already reported their outcomes. |
| 689–692 | “On the fourth held-out set all four registered hypotheses hold…” | move-to-appendix | Move hypothesis enumeration; retain the six-segment results in the main text. |
| 699 | “The statements above compare observed differences with fixed margins.” | delete | Metatext before the actual uncertainty analysis. |
| 711–712 | “We therefore claim non-inferiority…” | delete | Repeats the supported count, margin and Spam exception already stated. |
| 714–715 | “under the same registered hypotheses” | move-to-appendix | Replication registration detail. |
| 775–776 | “Removing the pool shows… it does not show…” | delete | Replace defensive setup with the direct purpose: comparing pool policies. |
| 776–777 | “In response to review…” / “added in response to review” | delete | Duplicate review history. |
| 784–788 | “the registered criterion…” and “below the required +0.5” | move-to-appendix | Consolidate exact rule; keep +0.30, its interval and the unmet criterion in results. |
| 790 | “the grid snapshot pool was registered…” | move-to-appendix | Secondary-control registration status. |
| 790–792 | “The archive runs, the grid criterion above…” | move-to-appendix | Repeated registration chronology. |
| 792–796 | “the registered criterion for the archive…” / “the snapshot pool and this threshold were registered later…” | move-to-appendix | Consolidate thresholds and chronology; retain numerical comparisons and label the snapshot analysis exploratory. |
| 797–798 | “the bounds against the archive are retrospective, not registered” | move-to-appendix | Detailed provenance; retain a compact retrospective-analysis label or appendix reference. |
| 815–817 | “archive registered with a criterion, snapshot pool…” | move-to-appendix | Caption-level registration inventory. |
| 836–837 | “archive comparison and criterion registered…” | move-to-appendix | Caption-level chronology; retain interval definitions. |
| 854 | “registered before it was run” | move-to-appendix | Benchmark registration chronology. |
| 860–861 | “its expert predictions… are bit-identical…” | move-to-appendix | Benchmark/replay provenance. |
| 862–864 | “To compare at similar cost, we fixed beforehand…” | move-to-appendix | Comparator-selection procedure; retain actual costs and unequal-cost status. |
| 873 | “whether the same holds for other streams and hardware was not tested” | delete | Generic disclaimer duplicates the explicit benchmark scope. |
| 948–949 | “it does not establish merging by discrepancy…” | delete | Repeated rebuttal; retain pool-control findings in results and limitations. |

Also remove repetitive **“registered/pre-registered” modifiers** from the abstract, contributions and captions at 58, 147–151, 643, 660 and 877. Their factual registration status belongs in Appendix B.

The following are **results, not defensive sentences**. Their removal from the abstract or conclusion is a placement edit:

| Lines | Opening | Destination |
|---|---|---|
| 61–64 | “These grid concepts are aligned…” | Compress to one abstract sentence; full results in §5.3. Replace “hold only when” with the narrower demonstrated scope. |
| 65–68 | “Against pools that keep past contexts…” | §5.5, with the complete comparison retained. |
| 70–74 | “These comparisons use contexts…” / “A plain window of 3000 rows…” | §5.5 and §7, as requested. |
| 943–945 | “although it costs storage…” | Resource discussion; retain “without retraining” in the conclusion. |
| 949–956 | “When concepts recur…” through the FIFO-3000 comparison | Preserve a short scope statement in the conclusion; detailed outcomes already belong in §§5–7. |

I would not delete any theorem, definition, algorithmic condition or additional result sentence in Sections 3–5 merely because it sounds cautious.

**3. Conditions that must stay**

These may be shortened or relocated beside their claim, but their content is essential.

| Lines | Content to retain | Why it is load-bearing |
|---|---|---|
| 141–142; 205–211; 227–247 | Posterior-predictive assumption, log-loss setting, equal marginals and tie-breaking conditions | Defines when the discrepancy identities hold. |
| 255–263 | Loss-dependent behaviour and the distinction between excess-risk discrepancy and directed recall regret | Keeps the theory consistent with the implemented merging rule. |
| 282–294; 299–304 | Expert margin, clipping and prediction-gap conditions | Conditions the identification guarantee. |
| 315–329 | One-concept stored context, visit-dependent \(n_c\), boundary reset, margin/top-two gap and first-batch remainder | Defines the recall formula’s actual scope. |
| 334–337 | Flat curve eliminates the **area term**, with a first-batch allowance | Prevents “flat curve means exactly zero observed gain.” |
| 357–378; 386–388 | Half-Brier loss, discount, \(\eta_2\le 1/2\), fixed-expert comparison | Defines the safeguard; it is not an accuracy guarantee. |
| 410–412; 422–431 | Cross-fitting and scoring predictions before incorporating labels | Defines valid estimation and online timing. |
| 431–432 | Log-loss and step-10 variants are outside this theorem | Prevents attributing the guarantee to uncovered variants. |
| 524–527 | Ideal reset versus DDM, slow-level effects and unpredicted first batch | Explains why magnitude agreement is approximate. |
| 528–533 | Same-concept versus fresh-concept evidence; overlap and independent-row sensitivity | Preserve a concise main-text distinction even after moving provenance details. |
| 595–596; 609–611; 627–628 | Alignment, changed block lengths and added initial history | Limits causal interpretation of boundary tests. |
| 630–637 | Residual gains in some settings and failure in others | Prevents claiming that every misalignment eliminates recall. |
| 699–710 | Bootstrap construction, approximate coverage under drift, seed-0 scope and Spam’s uncertainty | Defines empirical non-inferiority. |
| 710–711; 965–966 | Backbone seeds differ from data seeds; segments share sources | Defines the amount of independent evidence. |
| 780–784 | Pool controls compare complete policies with different stored-row budgets | Prevents interpreting them as an isolated merging intervention. |
| 799–800 | Descriptive thresholds do not establish equivalence; individual losses remain | Prevents turning small means into universal parity. |
| 802–808 | Storage bounds versus measurements; reconstructed call overhead | Defines what resource quantities actually represent. |
| 854–857; 864; 870; 971 | Hardware/prefix scope and unequal measured costs | Keeps the FIFO-3000 comparison accurate. |
| 903–906 | Finite-context estimator evidence versus population discrepancy theory | Distinguishes empirical support from a theorem consequence. |
| 966–968 | Brier versus accuracy, calibration cost and theoretical assumptions | Retain once in the limitations rather than repeatedly throughout the paper. |

**4. Rewritten abstract — 204 words**

> Tabular foundation models can recall a past concept by reusing its labelled context without retraining. We characterise when this memory improves prediction under recurring concept drift. Under concept-pure stored contexts and identification margins, the gain over relearning is the area between the stored context’s accuracy and the learning curve, up to a first-batch term. This characterisation predicts substantial gains for concepts that require many examples and little gain for rapidly learned concepts.
>
> We propose MICE, a mixture of window and stored-context experts with two aggregation time scales. A fast level identifies a recurring concept within one batch under a margin; a slow level bounds discounted half-Brier regret against the plain window by 1.39 at every time, for arbitrary streams. Model-oriented discrepancies guide the organisation of stored contexts.
>
> On a controlled grid, predicted and observed recall gains have Spearman correlations of 0.94 and 0.83, and MICE exceeds reset detection by 8.5 percentage points on the hardest aligned cell. Shifted boundaries remove the average advantage, exposing the importance of concept-pure memory. On 29 real streams, MICE outperforms all four in-context baselines on 23; approximate one-sided bootstrap bounds support accuracy non-inferiority to the 1000-row window at a 0.3-point margin on 28 streams, conditional on backbone seed 0.

**Rewritten contributions**

1. **A characterisation of recall value.** We express the gain from recalling a concept rather than relearning it through the backbone’s learning curve, under single-concept contexts and identification conditions. The resulting area formula explains when memory offers substantial benefit and when the opportunity vanishes.

2. **Theory for identifying and combining contexts.** We establish identification within one batch under a margin, characterise a blind spot of R-divergence and its excess-risk repair under posterior-predictive assumptions, and derive an any-time discounted half-Brier regret bound for the slow aggregation level.

3. **A training-free streaming method.** MICE combines window and stored-context experts through fast and slow aggregation, using directed recall regret to organise a bounded pool of past contexts.

4. **Evidence across recall and weak-gain regimes.** Controlled experiments link predicted and observed gains with Spearman correlations of 0.94 and 0.83 and expose sensitivity to mixed segments. Real-stream experiments support accuracy non-inferiority to the default window on 28 of 29 streams at a 0.3-point margin. Pool controls, ablations and resource comparisons quantify the effects of aggregation, context organisation and larger windows.

**Decision:** Adopt this theory-led structure.  
**Supporting evidence:** The existing theory, grid results, boundary tests and real-stream safeguard evidence form a coherent argument.  
**Alternative options:** Retain the current RQ ordering, with substantially more repetition.  
**Key risks:** Presenting assumption failure as a quantitative prediction, or Brier regret as guaranteed accuracy non-inferiority.  
**Remaining uncertainty:** This is a manuscript-and-table consultation, not independent verification of experiments or proofs.  
**Confidence:** High in the editorial recommendation.  
**Requires user approval:** No additional approval for this proposal; no protocol or numerical changes are proposed.

Runtime provenance: the sandbox is read-only. The local catalog lists Astra and High effort; the active session’s exact model/effort was not independently verified.