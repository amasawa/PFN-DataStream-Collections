[0m
> auditor · mimo-v2.6-pro
[0m
Audit complete. The core mathematics (Azuma–Hoeffding constants, union bound, inequality directions, corollary condition, and the three numerical claims) checks out; the findings below are precision and claim-scope issues.

## Findings

**F1. π = 1/2 case omitted from prop:purity**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:16–21` (the two-case display)
- Evidence: The display gives 0 for π > 1/2 and ρ for π < 1/2 only. At π = 1/2 the mixture conditional ties on the disagreement region, so the regret is tie-rule dependent — exactly the situation prop:blind(iii) treats carefully for `h_U` under 0-1 loss.
- Why it matters: The statement reads as exhaustive; a reader at equal shares (e.g. a segment with equal counts of two concepts) gets no defined value.
- Recommended correction: Add the π = 1/2 case by reference to the tie rule of prop:blind(iii) (regret 0 or ρ·(tie mass) depending on the rule), or state "π ≠ 1/2" in the proposition.

**F2. Finite-context remark: "behaves at best like πn rows" is false as stated**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:27–29` ("a context of n rows with share π of concept k behaves at best like πn rows of it, so … contamination moves a_k(n_c) towards a_k(π n_c)")
- Evidence: (a) With ρ < 1 the minority rows are correct labels for g_k on the agreement region (mass 1−ρ), so the effective sample can exceed πn; at ρ = 0 the mixed context is n clean rows and a_k(n), not a_k(πn), is achievable. (b) For π < 1/2, prop:purity says the context recalls the other concept (regret ρ on k), which is not on the path from a_k(n_c) to a_k(π n_c) at all. (c) Nothing in prop:purity (population limit, 0-1, deterministic, P_X = Q_X) implies a finite-n interpolation; under label noise the relevant inflation is governed by the signal attenuation (2π−1), not by πn.
- Why it matters: The remark is the bridge from prop:purity to prop:recall's learning curve and to the trimming trade-off; as written it suggests a ceiling that the theory does not give.
- Recommended correction: Restrict to π > 1/2 and phrase as a heuristic bound under a stated reading (e.g. "if the minority rows are treated as noise, the usable rows of concept k are at most πn; on the agreement region they also contribute, so the effective sample lies between πn and n"); note that π < 1/2 is the recall-failure case of prop:purity. The trimming sentence ("which effect dominates depends on the slope") should say direction depends on whether the effective sample rises or falls, the slope on the magnitude.

**F3. "A boundary inside a batch is located to that batch or the next, so D<B" does not follow from prop:cp**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:72–73`; related: `prop:cp(ii)` at lines 55–56
- Evidence: (ii) proves only that the excess **at the true b** is positive at t = b + n2/B; the detector declares at the argmax candidate, and (ii) does not show the argmax equals b. At t = b+2 the candidates are {b−1, b, b+1}; if b−1 wins, the cut is at (b−1)B and the distance to a boundary inside batch b is up to almost 2B, so D < B fails. Expected excesses (ρ on b,b+1 vs 0 before) favour b, but no bound on the argmax error is proved. cor:cp correctly conditions on localization; the remark states it as established.
- Why it matters: D < B is what yields "a segment of at least 400 rows is majority-pure" and the sentence "Segmentation … implements the premise of prop:recall … wherever the boundaries fall".
- Recommended correction: Either state the localization as an additional condition ("when the largest excess occurs at the true batch, the named batch is b or b+1 and D < B") or cite the empirical localization rate from exp-seg instead of asserting it. Also fix Δ's scope in (ii): ass:err(b) should say "the mean rate on the batches b…t−1 exceeds that on the batches of the pre-window", and (ii) should fix the evaluation time t (n1, n2 depend on it).

**F4. Text statistic ≠ code statistic (pre-window restrictions omitted)**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:36–42` (eq:cp and preceding sentence) vs `cpsegments_excerpt.py:18–30`
- Evidence: The text compares post = b…t−1 with pre = b−R…b−1. The code forms `pre = [k for k in range(max(ref0, b-R), b) if k in self.err]`, requires `len(pre) ≥ RMIN` (=2), skips candidates with `b*B < closed`, and sets `ref0 = b+1` after each detection (pre never crosses the previous **detected** change). It also sets n1 = len(pre)·B, n2 = len(post)·B, i.e. every batch is counted as exactly B rows. The margin and the argmax-positive rule match the text exactly (`sqrt((1/n1+1/n2)/2 · ln(1/δ_cp))`, `ex > 0`, largest wins).
- Why it matters: Prop:cp remains valid for the implemented windows (the restrictions shrink n1 and the candidate set), but the paper as written describes a different statistic than the one analysed in the code comments and used in the experiments.
- Recommended correction: Add one sentence: "pre-batches are those after the batch following the previous detected change, at least RMIN of them; n1, n2 are the rows of the compared batches (each of size B)".

**F5. Scope of the false-alarm statement**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:53–54` (prop:cp(i)); proof sketch comment lines 80–84
- Evidence: "E ≤ 0 without a change" uses (a) across each candidate's full compared span (b−R through t−1). If a true change lies inside a candidate's pre-window, (a) does not apply and the per-candidate bound need fail; the code's `ref0` only guarantees this relative to detected changes, not missed ones. The statement "Without a change, … at most Hδ_cp" is right only if read as "no change in any compared batch at that time".
- Why it matters: As literally read ("no change occurs") a single past change inside a pre-window invalidates the bound; the intended reading should be explicit.
- Recommended correction: Replace with: "If no change occurs in the batches compared at a given time (from b−R through t−1 for the candidates b), the probability of a declaration is at most Hδ_cp."

**F6. "The recall theorem needs majority purity, not purity" overstates**
- Severity: P2 · Status: Confirmed issue
- Location: `r14_theory_draft.tex:26–27`
- Evidence: prop:recall is stated for a stored expert holding n_c rows of concept k (pure); its accuracy formula uses a_k(n_c) of a pure sample. Prop:purity gives zero **population** regret under 0-1 loss, deterministic concepts, and P_X = Q_X — a narrower setting than prop:recall (general accuracy curves) — and the very next sentence concedes finite contexts still lose accuracy. So majority purity is what the **identification** (which concept is recalled) needs; the recall theorem's accuracy statement still needs the pure-context premise plus the contamination correction.
- Why it matters: The sentence reads as an extension of prop:recall's assumptions that the draft does not establish.
- Recommended correction: "In the population limit a stored context recalls the concept holding the majority of its rows; identification therefore needs majority purity, while \cref{prop:recall} applies to the majority concept with the finite-context correction below."

## Points confirmable only by running code
1. Whether the 300-row window's realised post-change error is ρ on exactly batches b and b+1 (finite window vs the population reading of ass:ppd), and the empirical rate at which the argmax candidate is the true batch (the D < B premise of F3) — needs the synthetic-stream runs of exp-seg.
2. Whether n1 is ever below 5B in the experiments (stream start, immediately after a detection because of `ref0`/`RMIN`), which changes ε and the "2ε = 0.31" example.
3. Whether batches are always exactly B rows; the code counts n1, n2 as len·B, so a partial final batch would bias the rates.

## Checked and found correct
- Margin constant: ε = sqrt(½(1/n1+1/n2)·ln(1/δ_cp)) with n1=500, n2=200, δ=10⁻³ gives ε ≈ 0.1555, **2ε ≈ 0.311** ✓ ("0.31"), matching the code expression exactly.
- Azuma–Hoeffding: increments have range lengths 1/n2 (post) and 1/n1 (pre), Σ r² = 1/n1+1/n2, so P(stat − M ≥ λ) ≤ exp(−2λ²/(1/n1+1/n2)) = δ at λ = ε ✓; sketch's (ii) direction and the condition Δ − ε ≥ ε ⟺ Δ ≥ 2ε ✓.
- Union bound over ≤ H candidates gives **Hδ_cp = 0.003** ✓.
- cor:cp: ≤ D foreign rows per end, ≤ 2D total, majority-pure iff 2D < L_S/2 ⟺ **4D < L_S** ✓; with D < B = 100 (integer rows D ≤ 99), **4D ≤ 396 < 400**, so "at least 400 rows" ✓.
- "Disagree on more than about a third": Δ = ρ ≈ mean post rate minus 0 pre rate, Δ ≥ 2ε ≈ 0.31 ✓; 1 − δ = 0.999 ✓.
- prop:purity: mixture conditional π·1[y=g_P] + (1−π)·1[y=g_Q], argmax = g_P iff π > 1/2 on the disagreement region, regret on P = (π < 1/2)·ρ, ε_P(h_P) = 0 ✓ (modulo F1); notation Div_T(evaluated | source) matches eq:transfer ✓.
- Text-code agreement: post = b…t−1, pre = up to R batches before b, candidates b ∈ [t−H, t−1], largest positive excess, δ_cp = 10⁻³, H = 3, R = 5, SIG = 300 ✓ (modulo F4).
