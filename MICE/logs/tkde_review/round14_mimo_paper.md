[0m
> auditor · mimo-v2.6-pro
[0m
I'll finish reading the diff and the rest of main.tex, then check the dropped-result and attribution questions against the evaluator output.
[0m→ [0mRead main.tex[90m [offset=755][0m
[0m→ [0mRead r14_paper.diff[90m [offset=607][0m
[0m✱ [0mGrep "window ensemble|Win\. ens|winens"[90m in main.tex · 9 matches[0m
[0m→ [0mRead main.tex[90m [offset=1436][0m
The oracle-test seeds and the T1 independence claim look inconsistent — I'll verify exactly what the diff touches and what the text says about seeds 40–43.
[0m✱ [0mGrep "oracle|40 and 41|40 to 43|never used|not used before|unused"[90m in r14_paper.diff · 5 matches[0m
[0m✱ [0mGrep "oracle|40 and 41|40 to 43|never used|not used before|unused|Data seeds"[90m in main.tex · 13 matches[0m
[0m✱ [0mGrep "-0\.9|-8\.5|1\.0 to 3\.0|below the window ensemble|below the Win"[90m in main.tex · 0 matches[0m
[0m✱ [0mGrep "gridparams|segment.*500|100, 500, 1000"[90m in main.tex · 7 matches[0m
All checks are done. Six findings, ordered by severity.

---

## Audit: MICE round-14 revision (change-point segmentation)

### Finding 1
- **Severity:** P1
- **Finding status:** Confirmed issue (textual contradiction); whether it compromises C1's independence depends on run dates I cannot see
- **Location:** main.tex:791 “four data seeds (40 to 43) that were not used before”; vs. main.tex:653 (unchanged by the diff) “On the unused seeds 40 and 41 the measured area term lies within 0.7 points…” with tab:oracle on “Seeds 40, 41”; PLAN.md:51 “data seeds 40-43 (never used; independent concept draws)”
- **Evidence:** The oracle-test passage (main.tex:650–667, tab:oracle) does not appear in r14_paper.diff (only mention of “oracle” in the diff is line 245, the new Segmentation paragraph), so its results on seeds 40/41 existed before this round. The new T1 text then claims seeds 40–43 “were not used before”, and the registration claims “never used”. Seeds 40/41 = 36 of the 72 T1 streams; the oracle test already examined recall gains on those concept draws.
- **Why it matters:** The primary criterion C1 is registered as being on never-used, independent streams. The paper’s own prior results falsify that premise for half of them, and the registration repeats it.
- **Recommended correction:** Establish the run timeline from the logs. If the oracle runs preceded the T1 registration, state it honestly (e.g. “seeds 40 and 41 were used beforehand only for the oracle-boundary test of \cref{prop:recall}, which does not involve the detector; seeds 42–43 were unused”), correct PLAN.md’s claim in the record, and note the partial overlap in app:prereg. If the oracle runs came after T1, fix the “unused” wording at main.tex:653 instead.

### Finding 2
- **Severity:** P1
- **Finding status:** Confirmed issue
- **Location:** r14_paper.diff removes: “On the four shifted streams with 500-row blocks \method{} is also below the window ensemble ($-0.9$ to $-8.5$ points); on the four with 2\,000-row blocks it stays above it ($+0.2$ to $+1.8$)” and “with 2\,000-row blocks one segment in four is mixed and it loses 1.0 to 3.0 points of its advantage”
- **Evidence:** Neither quantity appears anywhere in main.tex (searched for “-0.9”, “-8.5”, “1.0 to 3.0”, “below the window ensemble”: no hits). tab:offset has only $-$Reset and $-$Archive columns, so the comparison is unrecoverable from tables. The rest of test (b)’s failures are retained (below reset on 7 of 8, $-3.7$/$-10.8$, short of the registered criterion).
- **Why it matters:** PLAN.md Reporting is binding: “All results are reported whether criteria are met or not; the results of the original method … stay in the paper as results of the original method.” The rewrite of RQ2 drops one unfavourable comparison of the original method while keeping the favourable ones (e.g. “the shift leaves … the window ensemble almost unchanged”).
- **Recommended correction:** Restore both sentences in test (b), attributed to fixed segmentation, e.g. “with 500-row blocks fixed segmentation is also below the window ensemble ($-0.9$ to $-8.5$ points), with 2\,000-row blocks above it ($+0.2$ to $+1.8$); with 2\,000-row blocks it loses 1.0 to 3.0 points of its advantage.”

### Finding 3
- **Severity:** P1
- **Finding status:** Confirmed issue
- **Location:** main.tex:1195–1196 (Conclusion) “Recall needs the recalled concept to hold the majority of the stored rows, and segments that start at detected changes provide this wherever the concept boundaries fall”; also main.tex:55–57 (abstract) “which bounds the rows of other concepts in each segment” and “Identification needs only that the concept holds the majority of the stored rows”
- **Evidence:** cor:cp gives majority purity only “If every declared change lies within $\nu$ rows of a concept boundary and no boundary is missed” and $4\nu<|S|$; prop:cp needs \cref{ass:err}; the text’s own remark (main.tex:343–344) says “changes between closer concepts may be missed, and a segment then holds both”; Limitations (1208–1210) say ass:err need not hold on real streams. prop:purity additionally needs \cref{ass:ppd}, $P_X=Q_X$, deterministic concepts and 0-1 loss — all dropped in the abstract sentence.
- **Why it matters:** The conclusion states as an unconditional property of the method what the new theory only yields under assumptions the paper itself says can fail; this is exactly using the new propositions beyond their assumptions.
- **Recommended correction:** Qualify: e.g. “segments that start at detected changes supply this wherever the boundaries fall, up to the mixing bounded by \cref{cor:cp} and as long as boundaries are detected” and in the abstract “which, when changes are detected, bounds the rows of other concepts in each segment.”

### Finding 4
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** main.tex:1509 (tab:gridparams, app:grid) “Batch size, segment, $M$ & 100, 500, 1000 rows”
- **Evidence:** The method’s segments are now 300–700 rows (notation table, main.tex:576 “a closed segment (300 to 700 rows)”; method text 497–500). “Segment = 500” is only true of fixed segmentation. The same appendix also omits the T1 construction (seeds 40–43, row-level offsets, variable blocks; main.tex:1491–1493 lists only seeds 0/1, 10/11, 20/21, 30/31).
- **Why it matters:** A reader of the grid specification still gets the pre-round-14 protocol; this is the stale fixed-segment description the revision was meant to remove.
- **Recommended correction:** Change the row to “Batch size, $M$ & 100, 1000 rows” (drop “segment”, or mark it “500 under fixed segmentation”), and add the T1 seeds/offset/variable-block construction to the seed list.

### Finding 5
- **Severity:** P2
- **Finding status:** Suspected issue
- **Location:** main.tex:296–299 (remark after prop:purity) “a context of $n$ rows with share $\pi>\tfrac12$ is worth between $\pi n$ and $n$ rows of the majority concept”
- **Evidence:** prop:purity (proof, main.tex:1275–1278) only computes the population 0-1 risk of the mixture’s mode; prop:recall defines $a_k(n)$ for a context of rows of concept $k$ only. The minority rows are wrong labels on the disagreement region; a context with label noise can have accuracy below $a_k(\pi n)$, so the interval claim does not follow from either result, and no argument is given.
- **Why it matters:** The remark is the only bridge from majority purity to the area formula of \cref{prop:recall} for mixed contexts; the “between $\pi n$ and $n$” bound is the kind of statement later sections lean on when they say prop:recall applies to detected segments.
- **Recommended correction:** Either drop the interval claim and say the effective sample size is not identified for mixed contexts (identification only follows from prop:purity), or add the argument/conditions under which it holds.

### Finding 6
- **Severity:** P2
- **Finding status:** Missing information
- **Location:** main.tex:800 “the gain over reset is $+10.1$ points against $+5.3$”; 813–814 “(69\% at the 95\% level, against 92\% and 88\% …)”; 816 “between 0 and 180 changes per stream (median 9)”; 822–823 “(6.56 calls with fixed segmentation)”, “10.0 calls per batch on average (4.6 to 17.3)”
- **Evidence:** None of these values appear in evaluator_output.txt (which covers C1–C5, group means/intervals, purity aggregate, detection totals). All other round-14 numbers I checked match the evaluator exactly (2.85/0.685, per-regime means and intervals, +6.55/+3.07/+3.13/+1.74/+0.04/+0.01 with its interval and range, 88%/97.6%, 570/576 and 1 false cut, archive/resources, +0.23/0.58; “0.68” is correct rounding of 0.685 in binary floating point).
- **Why it matters:** These are registered “reported without criterion” items; with the provided evidence package they are unverifiable (not contradicted).
- **Recommended correction:** Attach the per-regime purity and first-five-batch outputs and the real-stream detector/call summaries to the evidence package, or cite the exact table/run file that backs each.

---

**Checked and clean:** purity rule P outcome is reported exactly as registered (majority form, 88% vs 90% stated in abstract, RQ2, Limitations, app:prereg); all C1–C5 outcomes match evaluator_output.txt; no criterion is unmet so the reporting rule is satisfied apart from Finding 2; attribution between fixed and detected segmentation is careful everywhere I looked (RQ3 “The rest of this section uses fixed segmentation”, the protocol Segmentation paragraph, table captions, and the “Detected segments remove this case” sentence at main.tex:1064); no remaining text describes the default method as fixed 500-row segments except Finding 4’s appendix table.
