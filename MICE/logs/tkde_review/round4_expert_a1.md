**Decision:** 4.b is justified **as an additional experiment, with revisions before registration**. 4.a answered whether its tested schedules met the robustness criterion; it failed. It could not isolate alignment from block length and seed changes. Preserve that verdict regardless of 4.b.

**Supporting evidence:**

- **Severity:** P1. **Finding status:** Confirmed issue. **Location:** [4.b design](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/logs/tkde_review/round4_plan_b.md:16), [evaluation loop](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/run.py:266). **Evidence:** With 100-row batches, a 250-row extension moves switches into batch interiors as well as segment interiors. The runner also drops the final 50 rows. **Why it matters:** This changes prediction/update timing and evaluation coverage alongside segment purity. **Recommended correction:** Use **200 rows as the primary offset** to preserve batch alignment. Retain 250 only as a separately labelled combined segment-and-batch misalignment test.
- **Severity:** P1. **Finding status:** Confirmed issue. **Location:** [pairing assertion](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/logs/tkde_review/round4_plan_b.md:19), [generator](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_tkde_control/make_misaligned.py:22). **Evidence:** Each block draws centroid indices before Gaussian noise; enlarging the first block changes its noise draws too. Zero-offset reproduction does not establish sample matching at nonzero offset. **Why it matters:** Same-seed pairing preserves latent concepts, but does not hold observations fixed. **Recommended correction:** Preserve the aligned observations and prepend independently generated first-concept observations using a registered auxiliary RNG, or explicitly describe the weaker pairing and sampling variability.
- **Severity:** P1. **Finding status:** Missing information. **Location:** [criterion and reporting](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/logs/tkde_review/round4_plan_b.md:23). **Evidence:** The pass rule uses offset performance alone; recurrence-window indexing and evaluation weighting are unspecified. **Why it matters:** Positive offset gains do not establish preservation of aligned gains. **Recommended correction:** Register the paired change and exact scoring rules below.

**Alternative options:** Under the frozen-method constraint, fixed recurring block lengths with a **200-row offset** are a practical improvement. A preregistered 300-row sensitivity tests the complementary 60/40 mixture and timing direction; it is useful, not mandatory for a claim limited to 200 rows. Neither is a universal worst case. Additional offsets are unnecessary unless claiming robustness across offsets.

**Key risks:** Extending the first block still adds initial learning history. Preserving observations and scoring corresponding recurrence windows reduces ambiguity, but does not remove that history difference. Describe the result as sensitivity to the registered phase-shift construction, rather than a pure causal effect of segment impurity.

Keep **7/8 positive and mean ≥1 percentage point** only as a descriptive criterion for advantage over DDM on that offset grid. For the alignment question, make
\[
\Delta_i=(A_{\mathrm{MICE}}-A_{\mathrm{DDM}})_{\mathrm{offset},i}
-(A_{\mathrm{MICE}}-A_{\mathrm{DDM}})_{\mathrm{aligned},i}
\]
the primary contrast. Report all eight values, their unweighted mean, and breakdowns by block length, centroid count and seed. A preservation/noninferiority claim additionally needs a justified loss margin fixed beforehand.

Register exact schedules, RNG coupling, warm-up/tail handling, six recurring switches, window boundaries, aggregation weights, frozen configuration and aligned-cache provenance. Report full-stream accuracy separately from matched recurrence windows. Two seed values and one backbone seed support limited generalization; eight configurations are not eight independent replications.

**Remaining uncertainty:** The proposed offset implementation and claimed reproduction check were not supplied. Active model identifier/effort remain unverified.

**Confidence:** High on the redesign justification and identified confounds; moderate on the revised design’s ability to quantify alignment sensitivity.

**Requires user approval:** Yes, before execution. [Project instructions](/mnt/c/Users/zhwu9808/Desktop/dataStream/AGENTS.md:14) require “explicit user approval” and a recorded, committed amendment, alongside the specified MiMo Pro High and verified Codex Extra High assessment. Preserve 4.a and its complete reporting. Claude should schedule 4.b after the running 29-task control, respecting existing resource safeguards.