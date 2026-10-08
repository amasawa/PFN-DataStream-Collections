**Decision:** Choose **A**, with two refinements: describe “no cost” as passing the registered **mean-accuracy criterion**, and restrict the established large recall gains to the tested conditions with sufficiently pure stored segments. Retain the frozen method.

(i) **The excess-risk discrepancy can remain a contribution**, phrased as:

> “We identify a blind spot of R-divergence under conflicting concepts and derive an excess-risk discrepancy that resolves it under the stated posterior-predictive assumptions, with supporting evidence on controlled segment pairs.”

Separate this theoretical result from the practical directed recall-regret statistic used for merging. Neither the theorem nor segment-pair discrimination establishes that merging improves streaming accuracy over an archive.

(ii) Change these claims:

- **Abstract:** retain the theoretical and baseline results, but explicitly add that discrepancy-based pool organisation **did not meet the registered improvement criterion over an unmerged archive**, even on aligned concepts. Retain the existing misalignment limitation. Describe the fast-level result as concentrating weight on a leading expert under the margin conditions; avoid implying that it validates discrepancy-based concept identification. Keep “all four in-context baselines” explicitly scoped to the original four, excluding the archive.
- **Contributions:** retain the qualified discrepancy theory in contribution (2). Replace contribution (3)’s “every component corresponds to one of these results” with a concrete description: “a training-free mixture of window and stored-context experts under a two-level aggregation rule, with discrepancy-based pool organisation.” Contribution (4) must include the failed archive-improvement and misalignment criteria, and scope its superiority claims to the named comparators and tested conditions. See [current claims](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:117).
- Apply the same distinction throughout: evidence supports retaining past contexts **within the tested two-level system**; it does not establish merging as the source of that benefit.

(iii) These are reporting and interpretation changes. **They require neither a method change nor new data.**

**Supporting evidence:** I independently recomputed the summaries from the saved result tables:

- Aligned primary comparison: **+0.295 percentage points, positive on 7/8**; fails the registered ≥+0.5 requirement.
- Real streams: **+0.074 points, positive on 18/29**; passes the registered mean ≥−0.1 criterion, without establishing equivalence or absence of individual losses.
- Misaligned streams: archive wins **12/12**, averaging **0.892 points**; MICE versus reset also fails its registered criterion.
- Aligned snapshot comparison: **+3.251 points, positive on 5/8**. This supports an advantage over that particular snapshot design, but cannot replace the failed primary comparison.

These verdicts directly trigger the narrowing prescribed in the [registered plan](/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_tkde_control/PLAN.md:20).

**Alternative options:** Use **B only as secondary descriptive evidence**. The saved tables show fewer calls on all eight primary aligned streams and 25/29 real streams, but fewer calls do not uniformly imply lower runtime. Crucially, calls and wall time were **registered reporting measures**; interpreting them afterward as the principal value of merging was not a registered success criterion. Report the exceptions and avoid using efficiency to rescue the failed accuracy claim. **C is unnecessary**: an honest paper can retain MICE while acknowledging where a simpler archive performs better.

**Key risks:** Substituting a secondary success for the failed primary criterion; equating pair discrimination with downstream utility; treating the archive comparison as isolating merging despite differences in context sizes and expert counts; presenting 29 streams/segments as 29 independent sources.

**Remaining uncertainty:** Generalisation beyond these conditions, the causal reason for the misalignment losses, and the accuracy–resource tradeoff remain unresolved. I checked saved summaries and relevant manuscript statements, not raw prediction caches or full proofs. Active model/effort remains unverified.

**Confidence:** High in this reporting decision; limited in any stronger causal or universal claim about merging.

**Requires user approval:** No additional approval for this recommendation to narrow claims while preserving the method and registered verdicts. Changing the default method, amending frozen criteria, or collecting new data would require explicit user approval. None is necessary here.