> build · mimo-v2.6-pro
## Scope note
Audited only the four attached files: `main.tex` (theory + RQ1), `predicted_visit.csv`, `learning_curve.csv`, `predict_gain_visit.py`. Part (2) numerical checks produced **no findings** (details after the findings). Two minor statement-precision findings on part (1).
---
### Finding 1
- **Severity:** P2
- **Finding status:** Missing information
- **Location:** `main.tex` ~296–306 (`prop:recall` statement), proof ~749–758
- **Evidence:** The theorem assumes `\cref{ass:margin}` “for the better of the stored expert and the window”, then concludes the mixture’s expected accuracy is “the larger of the two values” $a_k(n_c)$, $a_k(\min(jB,M))$. “Better” is never defined in `sec:th-recall`. `ass:margin` only says *one* expert $k^\star$ leads the **last labelled batch**; `lem:margin}(iii)` then only gives that the mixture copies $k^\star$’s class. If “better” is read as the empirical margin leader, $k^\star$ is data-dependent and $\E[\mathrm{acc}(\text{mixture})]=\E[\mathrm{acc}(k^\star)]$ need not equal $\max(a_k(n_c),a_k(\min(jB,M)))$: e.g. $a_k(n_c)=0.9>a_k(jB)=0.8$ but the window wins the margin on the last batch (allowed by `ass:margin` alone) yields 0.8, not 0.9, on the next batch, so the positive part in \eqref{eq:area} is not attained.
- **Why it matters:** `prop:recall` is the recall-versus-relearn formula advertised in the abstract and used for the RQ1 predictions; under the literal reading the identity \eqref{eq:area} can fail.
- **Recommended correction:** Define “better” explicitly as the expert with the larger learning-curve value at its current context size ($a_k(n_c)$ vs $a_k(\min(jB,M))$), i.e. assume *that* expert satisfies `ass:margin` and the top-two gap condition on every labelled batch of the block. One clause; the proof then goes through unchanged.
### Finding 2
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** `main.tex` ~308–314 (`cor:flat` statement), proof ~760–765
- **Evidence:** `cor:flat` states “the area term of \eqref{eq:area} is zero on the first visit”. \eqref{eq:area} is defined for the $c$-th visit with $c\ge2$ and $n_c=\min(M,(c-1)L)$ rows of *previous* visits; for $c=1$ this gives $n_1=0$ and $a_k(0)$ is not defined anywhere in the section. The proof does not evaluate \eqref{eq:area} at $c=1$; it argues the stronger, well-defined fact that the pool holds no expert of the concept, so mixture and relearning use the same rows ($\Delta=0$, not merely the area term).
- **Why it matters:** Minor, but the corollary is cited as the explanation of `obs:relearn`; as written it invokes an undefined quantity.
- **Recommended correction:** Rephrase, e.g. “on the first visit $\Delta_{k,c}(L)=0$ (no stored expert), and the area term is zero whenever $a_k(B)=a_k(M)$”.
---
## Part (2) verification — no findings
Every number in the paragraph from “The registered predictions used a simplification…” matches `predicted_visit.csv`:
| claim in text | CSV / recomputation |
|---|---|
| correlation 0.83 (seeds 20–21) | Spearman(registered, observed_mice) = 1−36/210 = **0.8286** |
| $n_c=\min(M,(c-1)L)$, 500 rows on 2nd visit when $L=500$ | matches `predict_gain_visit.py` |
| 100 cent.: 9.2 instead of 10.4 | visit_specific **9.2135**, registered **10.44** |
| 30 cent.: 1.7 instead of 1.9 | visit_specific **1.7102**, registered **1.91** |
| rank correlations unchanged (0.94, 0.83) | registered and visit_specific have identical rank order across the six cells; Spearman 0.9429 / 0.8286 |
| magnitudes agree more closely (9.2 vs 8.6) | 9.2135 vs observed_fast 8.5795 → 9.2 vs 8.6 |
(Also consistent: earlier sentence 0.55/0.53, 3.0/2.6, 10.4/8.6 vs `observed_fast_s10_11` 0.5335, 2.581, 8.5795.)
**Independent recomputation of visit_specific (100 centroids, L=500)** from `learning_curve.csv` with the method of `predict_gain_visit.py` (mean acc over 2 seeds × 3 concepts × 3 reps per $n$; log-$n$ interpolation; B=100, M=1000; visits c=2,3 with $n_c=\min(M,(c-1)L)$, weight 1/3; positive part; factor $(J-1)/J$):
- means: $a(100)=0.53106$, $a(200)=0.72550$, $a(300)=0.78947$, $a(400)=0.83485$, $a(500)=0.87006$, $a(1000)=0.91589$ (with $a(300),a(400)$ log-interpolated)
- $J=5$; c=2 ($n_c=500$): $\frac15\sum_{j=1}^{4}[a(500)-a(\min(100j,1000))]_+ = 0.11987$
- c=3 ($n_c=1000$): $0.15654$
- total $(0.11987+0.15654)/3 = 0.092135$ → **9.2135 points**, matching `predicted_visit.csv` (9.21352566…) and the text’s “9.2”.
## Part (1) summary
- **$\varepsilon_{k,c}=(A^{\mathrm{mix}}_1-A^{\mathrm{rel}}_1)/J$ with $|\varepsilon_{k,c}|\le1/J$:** correct (both accuracies in $[0,1]$, batch 1 precedes any block label, so it is correctly excluded from the margin argument).
- **Corollary bound $\Delta_{k,c}(L)\le\frac{M}{L}(a_k(M)-a_k(B))+\frac1J$:** correct. Each summand is $\le a_k(M)-a_k(B)$ ($n_c\le M$, $\min(jB,M)\ge B$, $a_k$ non-decreasing); a summand can be non-zero only if $jB<n_c\le M$, so at most $M/B$ of them, and $\frac1J\cdot\frac{M}{B}=\frac{M}{L}$. Flat curve $a_k(B)=a_k(M)$ zeroes every summand. (Proof prose says “the $J=L/B$ terms” where the sum has $J-1$ terms; the bound is unaffected.)
- **Theorem statement:** correct under the reading in Finding 1; otherwise the proof step fails.
