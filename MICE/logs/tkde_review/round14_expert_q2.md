# Round 14 expert question 2 (Fable 5.1, 2026-10-16 08:56–08:58, $1.93): paper restructuring after the method change

## Prompt
You are the senior expert adviser for the MICE paper (MICE/overleaf/tkde/main.tex; read it with your tools as needed,
especially sections sec:theory, sec:method, sec:exp, sec:rq2, sec:rq3, sec:ablation, the abstract, the conclusion and
app:prereg). Do not write files.

Decision question: how should the paper be restructured now that the method has changed, so that it stays a
self-consistent, theory-driven paper (theory is the spine; the SOTA comparison is secondary)?

Context
- Reviewer (ICML standard, 4/8) P1: recall gain depended on the phase of fixed 500-row segments relative to unknown
  concept boundaries. The user approved a method change. New segmentation (CPSegments): segments start at changes
  detected by a two-sample Hoeffding test on the 300-row window's per-batch errors (H=3 post, up to R=5 pre batches,
  delta_cp=1e-3, min segment 300 rows, periodic close after 500 rows without a change). Merge rule, experts, fast and
  slow level unchanged. MiceCP = MICE with this segmentation; ArchCP = unmerged archive with the same segmentation.
- Registered reporting rule (frozen before runs): "The paper presents MiceCP as the method that implements the
  single-concept premise of the recall theorem; the original fixed segmentation and its boundary failures are reported
  as the motivating evidence. Any criterion not met is stated in the abstract or the conclusion." Purity rule P: strict
  form if >=90% of (context, close) evaluations have >=95% purity; majority form if >=95% have >50%; else conditional.
- Frozen test results (all criteria met):
  T1, 72 fresh streams (seeds 40-43; 30/100 centroids; blocks 500, 2000, variable 500-2500; 3 random row offsets each):
  CP-reset +2.85 [2.35,3.31] (70/72 positive); original MICE-reset +0.69; CP-MICE +2.17; CP-ArchCP +0.11; per regime
  CP-reset b500 +5.17 [4.59,5.72] 24/24, b2000 +1.48 [1.22,1.72] 22/24, bvar +1.91 [1.74,2.07] 24/24 (hierarchical
  bootstrap); original MICE-reset b500 +0.66 [-2.34,3.31], b2000 +0.74, bvar +0.65.
  Shifted grid (old 8 streams, boundaries 200 rows into segments): CP-MICE +6.55 (8/8), CP-reset +3.07, original
  MICE-reset -3.48. Aligned grid 8: CP-MICE +0.04 (CP-reset +3.13 vs MICE-reset +3.09). Misaligned 12: CP-reset +2.21
  (12/12) vs MICE +0.47. Real 29: CP-FIFO +0.58 (24/29), CP-MICE +0.01 (19/29), CP-ArchCP +0.08.
  Resources: 6.26 TFM calls/batch and 2.42 stored experts (ArchCP 10.64 and 7.64).
  Purity: 88.2% of evaluations >=95% pure (strict form missed), 100% >50% -> majority form; mean purity 0.976.
  Detection: 570 of 576 changes found, 1 false cut.
- Drafted theory (MiMo-audited), to add as subsection "Which Rows Form a Concept": Proposition Majority purity (under
  PPD extended to unequal shares, deterministic concepts, P_X=Q_X, 0-1 loss: regret 0 if pi>1/2, rho if pi<1/2);
  Assumption Window error; Proposition Detection (false alarm <= H*delta per batch via Azuma-Hoeffding; detection
  w.p. >=1-delta when gap >= 2 eps); Corollary Segment purity (<=2D foreign rows; majority-pure when 4D < L_S; D<B
  when the declared batch holds the boundary or the next, so segments >=400 rows are majority-pure).
- Problem: all other evidence in the paper was produced with fixed segmentation: learning-curve prediction (rq1,
  Spearman 0.94/0.83 on the aligned grid), 30 generator streams, real-stream confirmatory sets 3 and 4, block
  bootstrap non-inferiority on 28/29, second backbone seed, TabICL backbone, ablations, pool controls (archive,
  snapshot pool k=12 and k=4), timing. MiceCP was run on the 29 real streams and the aligned/shifted/misaligned grid,
  not on the TabICL runs, the second seed, the generator streams, or the ablations.

Alternatives
A. Name MiceCP "MICE" throughout; method section defines CP segmentation; old fixed-segment results relabelled
   "fixed segmentation" where they were produced with it; aligned-grid and real-stream equivalence (C3, C4) is the
   bridge that lets fixed-segment results on aligned grid / real streams stand as evidence for the shared components
   (learning curves, slow level, pool organisation).
B. Keep MICE = fixed segmentation as the main method and present CP segmentation as a module/variant in rq2.
   (Conflicts with the registered reporting rule.)
C. A, but move most fixed-segment-only evidence (TabICL, second seed, generator streams, k=4) to the appendix.

Constraints: theory is the spine; every component framed as implementing a premise of the theory; unfavourable
results kept (original failures as motivating evidence, strict purity missed); no defensive sentences; registration
history in the appendix; numbers only from CSVs.

Requested output (under 600 words): Decision / Supporting evidence / Alternative options / Key risks / Remaining
uncertainty / Confidence / Requires user approval. In the decision give: (1) the section outline with what moves
where; (2) the naming rule for the two segmentations; (3) the 3-4 sentences of the abstract that change; (4) which
existing claims must be weakened or re-scoped because they were made with fixed segmentation.

## Answer
**Decision: Alternative A with one placement rule (A, plus the part of C that the rule forces).** MICE is the method with detected-change segmentation. Fixed-segment evidence stays in the main text only where the registered equivalence covers the same streams and backbone (aligned grid C3, 29 real streams C4). Fixed-only evidence that has no bridge moves to the appendix, labelled.

1. Outline and moves
- Intro: contribution (4) becomes: fixed segments fail by boundary phase (motivating), detected segments repair it (+2.85, 70/72), learning curves still rank gains.
- Theory: insert "Which Rows Form a Concept" as 3.2, after sec:th-disc and before the fast level, so the premise of Theorem 1 is supplied before the theorem states it. Theorem 1's "holds one concept" premise is restated as majority-pure via the new proposition.
- Method: "Experts" paragraph defines segments by detection (H, R, delta_cp, 300-row minimum, 500-row periodic close); one sentence defines "fixed segmentation" as the variant of sec:rq2(a,b). Algorithm line 5, notation table and cost paragraph updated (measured 6.26 calls per batch; the Hoeffding test costs no TFM call).
- sec:rq1: unchanged numbers, one sentence that MICE differs from the fixed variant by +0.04 on these eight streams (C3), so the curve prediction applies to both.
- sec:rq2 retitled "Segment Purity and Boundary Phase": (a) fixed segmentation fails on misaligned and shifted streams (existing tables, relabelled); (b) 72 fresh streams, new primary table with per-regime gains; (c) CP columns added to tab:misaligned and tab:offset; (d) purity and detection statistics, including the missed strict form; (e) archive with the same segmentation (+0.11, 10.64 calls, 7.64 experts).
- sec:rq3: real-stream numbers stay with the C4 sentence (+0.01, 19/29; FIFO +0.58, 24/29). Second seed and TabICL move to app:details as "fixed-segment variant".
- sec:ablation: pool controls at size 12 and the capacity test are fixed-segment results; the shifted-grid clauses are re-scoped (see 4). Size-4 rows move to the appendix. Timing is kept, labelled fixed.
- Conclusion: limitations rewritten around what was not rerun and the missed strict purity.
- app:prereg: round-14 registration, the frozen reporting rule, purity rule outcome, and the order reviewer finding, method change, registration, single test.

2. Naming rule
\method{} = MICE = detected segmentation, everywhere. The old method is "MICE with fixed segmentation" at first use per section, "fixed" in table columns. "Archive" means the unmerged pool with whatever segmentation the row states. "MiceCP", "ArchCP", "CPSegments" do not appear in the paper.

3. Abstract sentences that change
- Replace the "exceeds reset by 8.5 ... restores it" sentence with: "Stored contexts are segments that start at changes detected by a two-sample test on the window's batch errors, so each holds one concept up to a bounded number of boundary rows; with fixed 500-row segments the gain of recall depended on the phase of the segments relative to the concept boundaries."
- Add: "On 72 fresh grid streams with random boundary phases, MICE exceeds reset detection by 2.85 points [2.35, 3.31] (70 of 72; 0.69 with fixed segments), and on the aligned grid and the 29 real streams the two segmentations are within 0.04 and 0.01 points."
- Add: "Segments held one concept in 88% of evaluations at the 95% level, short of the registered 90%, and were majority-pure in all."
- Drop the "level with the snapshot pool on the shifted grid" clause; the capacity sentence is scoped to fixed segmentation.

4. Claims to weaken or re-scope
- "Realigning restores the gain" is motivating evidence for the fixed variant, not a property of MICE.
- "Archive is more robust where segments mix concepts" and "snapshot pool matches MICE on the shifted grid" hold for fixed segmentation; with detection the archive is +0.11 and the snapshot pool was not rerun.
- TabICL, second backbone seed, generator streams ("exactly as many experts as concepts"), capacity timings and set-4 confirmation: all "fixed-segment variant". Set 4 was registered for the fixed method; say so.
- Cost: worst-case call count on a closing batch changes because closes occur at detections; seconds per batch for MICE are unmeasured.
- Limitations: replace "detected change points are future work" with the one false cut, the strict purity miss, and the unrerun sets.

**Supporting evidence.** C3 and C4 equivalences license the bridge; the registered reporting rule mandates MICE as the main method and the failures as motivation; the new theory makes segmentation a premise-implementing component, which only A supports.

**Alternatives.** B violates the registered rule. Pure C hides the real-stream and aligned-grid evidence that the bridge already covers.

**Key risks.** A reviewer reads two methods; the per-section label and the bridge sentence answer this. Robustness to backbone and seed now rests on the fixed variant only.

**Remaining uncertainty.** Snapshot pool, TabICL and timing under detected segmentation.

**Confidence.** High on A and the naming rule; medium on moving TabICL and the seed to the appendix.

**Requires user approval.** The appendix moves, the abstract rewrite, and dropping the shifted-grid snapshot clause.
