# Round 7 — plan (Claude, 2026-10-09)

Judgement: accepted. The counterexample holds: with a deterministic, source-independent tie rule c(x), the risks of
h_U on P and Q split the disagreement mass rho arbitrarily, so D_R = |Pr[c != g_P] - Pr[c != g_Q]| restricted to the
disagreement region can take any value in [0, rho]; the proof wrongly equated source-independence with uniform
randomisation. D_T(Q|P) = rho does not depend on ties.

Change (method unchanged):
1. Proposition 1(iii) restated: in the setting of (ii) with the 0-1 loss, D_T(Q|P) = rho for any tie rule; if ties of
   u_x are broken uniformly at random and risks are averaged over this randomisation, D_R(P||Q) = 0; under a
   deterministic tie rule c, D_R(P||Q) = |E_x 1[g_P != g_Q](1[c != g_P] - 1[c != g_Q])|, which lies in [0, rho] and
   depends on the tie rule rather than on how far the concepts disagree.
2. Proof of (iii) rewritten accordingly (both cases).
3. Interpretation (Remark after the proposition, and the sentence linking to the accuracy-based merge statistic):
   distinguish the log-loss blind spot (ii), which holds without qualification, from the 0-1 case, where D_R is either
   zero (randomised ties) or determined by an arbitrary tie rule, so in neither case does it measure the disagreement
   mass rho; the merge statistic D_T is the directed form and equals rho under 0-1 loss in this setting. The empirical
   comparison on segment pairs (Section RQ5, AUROC 1.00 vs 0.85) is described as an empirical comparison of the
   implemented estimators, not as a consequence of (iii).
