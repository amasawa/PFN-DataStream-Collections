Decision question (research methodology; you are the senior expert / decision maker, read-only).

Context: paper MICE/overleaf/tkde/main.tex (IEEE TKDE submission in revision). The method is frozen. A reviewer
asked whether MICE's concept-organised recall (excess-risk discrepancy test + merging of segments into concept
experts) adds value over a plain pool of past contexts. Pre-registered controls (experiments/mice_tkde_control/PLAN.md)
gave the evidence in MICE/logs/tkde_review/round2_plan.md (read it). In short: merging adds only +0.3 points over an
unmerged archive on aligned recurring concepts (registered threshold +0.5 not met), costs nothing on 29 real streams
(+0.07), and an unmerged archive is more accurate when concept boundaries are misaligned.

Alternatives:
(A) The plan in round2_plan.md: credit the gain to the pool of in-context experts under the two-level rule; keep the
    discrepancy as a theoretical contribution and merging as one way to organise the pool, with its measured effect.
(B) Additionally present fewer expert calls as the value of merging (only partly supported: fewer calls on some
    streams, not on Rialto/Poker; not registered).
(C) Recommend the archive as the default variant in the paper (this would change the method; excluded unless you
    see no honest alternative).

Constraints: method frozen; no new data; honest reporting of failed registered criteria; length is not a concern.

Answer concisely with: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty /
Confidence / Requires user approval. In the decision, also say (i) whether the excess-risk discrepancy can still be
listed as a contribution and in what words, (ii) which claims in the abstract and contributions must change, and
(iii) whether anything here would require changing the method or new data (then it goes to the user).
