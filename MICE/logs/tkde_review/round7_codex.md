**Overall assessment:** A coherent, potentially publishable contribution, with useful empirical evidence and candidly restricted claims. However, the theoretical justification of the discrepancy contains a confirmed mathematical error.

**Score:** 4 — borderline reject.

**Distance to TKDE acceptance:** Apart from the excluded pending item (2), a focused correction to Proposition 1 and its interpretation is needed. This can be fixed without changing the frozen method.

**Issue (Severity P1; Confirmed issue):** Proposition 1(iii)’s claim that R-divergence vanishes under 0–1 loss is false without an additional tie-breaking assumption.

**Location (section, line):** Section 3.1, `main.tex:230–231`; Appendix, proof of Proposition 1(iii), `main.tex:856–859`. Its connection to the implemented accuracy-based discrepancy appears at `main.tex:390–393`.

**Evidence:** Take identical input distributions, with \(P\) always assigning label 0 and \(Q\) always assigning label 1. Then \(\rho=1\), and Assumption 1 gives the pooled predictor \(h_U=(1/2,1/2)\). Break ties deterministically in favour of label 0—a rule independent of the query’s source. Under 0–1 loss,
\[
\epsilon_P(h_U)=0,\qquad \epsilon_Q(h_U)=1,
\qquad D_R(P\|Q)=1,
\]
contradicting the stated \(D_R=0\).

The proof incorrectly infers equal-probability selection from source-independent tie-breaking. Independence does not imply uniform randomisation.

**Why it is the most severe:** This is a counterexample to a stated proposition supporting a central theoretical contribution, directly in the loss used for the implemented merge statistic. The valid log-loss result does not establish the claimed universal blind spot for accuracy-based R-divergence.

**Required fix:** Explicitly restrict the zero-divergence statement under 0–1 loss to uniform random tie-breaking, with risks averaged over that randomisation, or replace it with a correct tie-dependent statement. Retain the valid \(D_T(Q\mid P)=\rho\) result, which does not need this restriction. Revise the accompanying interpretation so that the log-loss theorem and restricted 0–1 result are distinguished from the empirical accuracy-based comparison. **No method change is required.**

**Confidence:** High. The counterexample satisfies the stated distributional assumptions; it does not imply that the reported empirical results are incorrect.