Task (senior expert and co-author, read-only): help rewrite the paper MICE/overleaf/tkde/main.tex (with its tab_*_rows.tex)
into a theory-driven paper. The method, data and all numbers stay as they are.

The author's framing: the paper proposes a method with an elegant theory, and the experiments support the method and
the theory. It does not need to show that no cheaper or better method exists. The theory already predicts when memory
pays: (a) recall gain = area between the learning curve and the stored context's accuracy (Proposition recall;
Spearman 0.94 / 0.83 on the grid); (b) the theorem assumes a stored context of one concept, so misaligned or shifted
boundaries (mixed segments) remove the gain, as observed; (c) flat learning curves (standard generators, most
slowly drifting real streams) give no gain, and a larger window does as well or better there; (d) the slow level's
regret bound keeps MICE close to the plain window (non-inferiority on real streams). Unfavourable results stay in the
paper but are placed where the theory predicts them or in the limitations; the FIFO-3000 sentence moves from the
abstract to results/limitations (author's decision). Registration/provenance detail moves to one appendix section.

Writing rule from the author: delete every sentence whose only role is to pre-empt criticism rather than advance the
argument. Keep a sentence if it states a result, a condition under which a claim holds, or a definition.

Deliver, concisely:
1. A section-by-section outline of the rewritten paper (titles, the claim each section makes, which existing results
   support it, where each unfavourable result goes).
2. A list of the defensive sentences to delete or move, as: line number(s) | first words | delete or move-to-appendix |
   one-phrase reason. Be exhaustive for the abstract, introduction, Sections 3-5 and the conclusion.
3. Sentences that look defensive but are load-bearing (conditions of a claim) and must stay, with line numbers.
4. A rewritten abstract (at most 220 words) and a rewritten contributions list, using only numbers already in the
   paper.
