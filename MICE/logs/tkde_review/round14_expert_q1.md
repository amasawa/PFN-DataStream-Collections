You are the senior methodology expert for the MICE paper (repository: current directory; paper MICE/overleaf/tkde/main.tex,
method in MICE/code/run.py classes MiceV1 and PoolControl, two-level replay rule in MICE/code/reweight.py simulate2).
Answer with: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence /
Requires user approval. No essay; at most ~600 words. Read files only if needed (sections sec:method and sec:rq2 of main.tex).

CONTEXT. The user approved (2026-10-15) a method change to fix the reviewer's P1 issue (ICML-standard reviewer, score 4/8):
"MICE's recall gain depends on the phase of fixed 500-row segments relative to unknown concept boundaries. Fix: develop
and freeze a boundary-robust segmentation or memory-update rule, evaluate it on fresh concept draws with several
independently chosen boundary offsets and variable block lengths, compare against reset and the unmerged archive under
stated resource budgets, preserving the current failures as results of the original method." Reviewer estimate: 4 -> 5.
Evidence so far: shifting boundaries by 200 rows (500-row blocks) turns MICE's +3.09 gain over DDM-reset into -3.67;
realigning the segment origin with the known phase restores +3.01; the unmerged archive is more robust (merging a mixed
segment contaminates an existing concept expert, since an expert keeps its last M=1000 rows). On real streams MICE is
only slightly above the plain window and must stay safe (slow level).

PROPOSED CHANGE (MiceCP; everything else unchanged: windows 100/300/1000, merge rule with delta=0.02, kmax 12,
fast level eta=10, slow level simulate2 brier 0.5 tempered):
- Segments start at detected changes. A change detector on a per-batch error signal (labels arrive one batch late):
  a change at batch boundary b is declared at time t when the error rate on batches b..t-1 (1 to H=3 batches) exceeds the
  error on the R batches before b (after the previous detected change) by more than a Hoeffding margin at level delta_cp;
  the b with the largest excess is taken. The open segment then ends at b: closed through the usual merge-or-add test
  if it holds >= lmin=300 rows, otherwise its rows join no segment (they stay in the windows). The next segment starts at b.
- Without a change, a segment closes after 500 rows as now, but only once H further batches are labelled, so that a
  change inside it would have been seen.
- Candidate error signals: (i) the M-row window's errors (independent of the pool; relearns slowly, so with 500-row blocks
  its error stays high and changes may be masked), (ii) the fast mixture's errors (spikes at every change, recovers fast
  when recall works; depends on the pool), (iii) the 300-row window.
- No extra TFM calls except merge tests of the extra (shorter) segments.
Alternatives I considered: (A) multi-phase segmentation (5 staggered segmenters, store only segments passing a purity
test) - 5x closing cost; (B) per-batch purity gate: refuse merging a segment whose two halves disagree; mixed segments
become their own experts (archive-like) - prevents contamination but stores mixed experts; (C) offline cut search inside
each closed segment via TFM cross-prediction of candidate splits - ~8 extra calls per close.

PLANNED PROCEDURE. Development on fresh dev streams of the same generator (seeds 0,1: aligned and shifted 500/2000-row
blocks, variable blocks with an offset; already generated, baselines running). Tune the detector signal and
(delta_cp, R, H, lmin) there only, partly offline from the cached expert predictions of the original method. Then
register and freeze the rule, and test once on fresh seeds (e.g. 40-43) with randomly drawn offsets (at row
granularity, not batch) and variable blocks, plus the existing aligned grid (seeds 20/21), shifted grid, misaligned
schedules (seeds 30/31) and all 29 real streams for safety; compare with original MICE, DDM-reset, archive (k=12 and the
timing-matched k=2) and FIFO; report resources.

QUESTIONS (one decision): (1) Is change-point segmentation the right remedy versus A/B/C (or a combination such as
change-point segmentation + purity gate B as a fallback)? (2) Which error signal? (3) What registered success criteria
for the frozen test are appropriate (e.g. MICE-CP above reset on >= x of N fresh misaligned streams with mean gain >= y;
no loss vs original MICE on aligned streams beyond z; real-stream safety bound vs FIFO), so that the reviewer's concern is
answered without overfitting? (4) Does the theory section need a new statement (e.g. a purity bound in terms of detection
delay), or is a remark linking detection to the single-concept premise of the recall theorem enough?

---
## Answer (Claude Fable 5.1, 2026-10-15 11:47-11:49, $1.36)
**Decision.** Adopt change-point (CP) segmentation as the single frozen remedy. Do not add gate B or cut search C now. Use a pool-independent error signal, the 300-row window, and give the archive baseline the same segmentation so the merge-versus-archive comparison is clean.

**Supporting evidence.**
- CP segmentation targets the diagnosed cause directly. The paper locates the loss in segment phase (realignment restores 3.01 of 3.09 points, main.tex:671-679). A detector that starts segments at changes is phase-free by construction, and it is the remedy a reviewer of this literature expects. A and C still close on a grid or add 5x or 8 calls per close. B stops contamination but stores mixed experts, which the archive already shows is only a partial fix.
- CP changes storage only, not recall latency. The fast level still recalls an existing expert on the first labelled batch after a recurrence. Detection delay affects which rows a stored expert holds, not when it is used. That keeps the recall theorem's mechanism intact.
- Signal (iii) is the right one. The windows do not depend on the pool, so the detector is a fixed function of the stream and backbone. Two consequences follow. First, you can tune the detector offline from the cached window predictions of the original runs on the dev streams with zero TFM calls. Second, the same segmentation can be handed to the archive (archive-CP), which isolates the merge rule as the only difference. Signal (ii) is circular: its spikes depend on the pool that CP itself builds, and its one-batch recovery leaves nothing for H=3 to see. Signal (i) is masked on 500-row blocks as you note. The 300-row window stays elevated for about three batches after a change, which is what H=3 was designed to catch. If the dev streams show missed changes on 30-centroid concepts, fall back to the original 500-row close, which is the existing method, and report the miss rate. Note the Hoeffding margin at n=100 rows is roughly 0.12 at delta 0.05, so hard-concept changes will sometimes be missed; this is a documented degradation, not a failure mode.

**Registered criteria (keep to four, mark primary).**
1. Primary, fresh misaligned (seeds 40-43, row-granularity offsets, variable blocks): MICE-CP above reset on at least 3 of 4 streams per cell and mean gain at least +1.0 point overall, at least +2.0 on 500-row-block cells.
2. Primary, existing shifted grid: MICE-CP minus original MICE at least +2.0 points mean, with the realigned run reported as the ceiling.
3. Aligned grid: MICE-CP minus original MICE no worse than -0.3 mean, since detected and fixed boundaries should coincide there.
4. Safety: on the 29 real streams, MICE-CP minus FIFO mean at least -0.1, and minus original MICE at least -0.2.

Report, do not register, MICE-CP against archive-CP (k=12) and the timing-matched k=2 archive, detector delay, false alarms per 1000 rows, and stored-segment purity on synthetic streams. Keep the P1 results of the original method as they are.

**Alternative options.** If dev shows frequent misses, add B as a second stage at close rather than retuning the detector. C remains the only option that uses the TFM to find the cut, but it needs multiple-testing control and the cost is hard to justify in the method's budget.

**Key risks.**
- Real streams: false alarms produce short segments that fall under lmin, the pool fills slower, and MICE-CP drifts toward the window ensemble. Safe, but the small real gains may shrink. The slow level covers this.
- Batches straddling a boundary are mixed by up to 100 rows. State the rule for where the new segment starts and leave it fixed.
- Reviewer may call CP a new tuned component. The dev-only tuning, frozen constants and one-shot fresh seeds are the answer; put the dev tuning curve in the appendix.

**Theory.** A remark in the main text is enough for the recall link: detection makes each stored segment single-concept up to D*B rows, which restores the premise of the recall theorem. Add a short appendix proposition with the two standard guarantees: false-alarm probability per test at most delta_cp by Hoeffding, and detection within H batches when the error jump exceeds twice the margin. Do not state a purity bound in terms of accuracy; that needs a graceful-degradation assumption on contaminated contexts that the framework does not have. Measure purity instead.

**Remaining uncertainty.** I did not inspect the detector code or the dev stream manifests. Whether the 300-row window's excess is detectable on 30-centroid changes is an empirical dev question.

**Confidence.** High on the choice of CP and signal (iii). Medium on the numeric thresholds, which should be set after seeing dev baselines but before the frozen commit.

**Requires user approval.** No for development. Yes for the registration commit that fixes the four criteria and the constants, since it determines what the paper reports.
