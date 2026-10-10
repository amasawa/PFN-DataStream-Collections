[0m
> auditor · mimo-v2.6-pro
[0m
I'll finish reading the three provided files (they were truncated) before auditing.
[0m→ [0mRead main_old.tex[90m [offset=729, limit=700][0m
[0m→ [0mRead main_new.tex[90m [offset=755, limit=700][0m
[0m→ [0mRead rewrite.diff[90m [offset=576, limit=700][0m
Now I'll verify a few deletion claims with targeted searches in the same three files (the long appendix line was truncated in the tool output).
[0m✱ [0mGrep "replay|simulate2|single-level mixture|tuned on a real|none was tuned|frozen on 2026|exceed the archive|not equivalence|backbone seed|inconclusive|in response to review"[90m in . · 2 matches[0m
[0m✱ [0mGrep "varepsilon|\\\\zeta"[90m in . · 0 matches[0m
Audit complete. I compared every changed region of `main_new.tex` against `main_old.tex` and `rewrite.diff`, and used whole-file pattern searches on `main_new.tex` only to confirm absences (the appendix paragraph is one 2000+ char line, so line-level display is truncated, but pattern search covers the full line).

## Findings

**1. Severity P1 · Confirmed issue · Location: `main_new.tex:421` (end of the Timing paragraph; nothing in the appendix)**
- Evidence — old (`main_old.tex:434–438`): "All reported numbers for \method{} come from such replays: the method above with $\eta_2=\tfrac12$ (\texttt{simulate2(outer='brier', scale=0.5, temper=True)} in the released code, frozen on 2026-10-05) ... The runs that produced the cache emitted a different, single-level mixture, which we do not report." New: the paragraph ends at "with the log-loss or with the registered step $\eta_2=10$." Pattern search of `main_new.tex` finds no "replay", "simulate2", or "single-level mixture".
- Why it matters: this is a load-bearing provenance/scope condition — it states what computation produced the reported numbers and that the runs that generated the prediction cache emitted a different rule. Deleting it (rather than moving it to the provenance appendix, as the rewrite brief required) removes the reproducibility statement of the main results.
- Recommended correction: restore it in `app:prereg` ("Development and provenance"), e.g. "All reported numbers for MICE are replays of the cached predictions (`simulate2(outer='brier', scale=0.5, temper=True)`, frozen 2026-10-05); the runs that produced the cache emitted a different, single-level mixture, which we do not report."

**2. Severity P1 · Confirmed issue · Location: `main_new.tex:425` (cost sentence; nothing in the appendix)**
- Evidence — old (`main_old.tex:442–443`): "so at most 29 calls on a closing batch. All constants were set on synthetic development streams; none was tuned on a real stream." New: "so at most 29 calls on a closing batch." Pattern search of `main_new.tex` finds no "none was tuned" / "tuned on a real".
- Why it matters: "no constant was tuned on a real stream" is the condition under which the real-stream numbers are confirmatory; dropping it leaves the reader unable to tell that the 29 real streams were not used for model selection.
- Recommended correction: restore the sentence in `app:prereg`, e.g. "All constants were set on synthetic development streams; none was tuned on a real stream."

**3. Severity P1 · Confirmed issue · Location: `main_new.tex:916–917` (conclusion)**
- Evidence — old (`main_old.tex:69` + `main_old.tex:703`): "its one-sided 95\% block-bootstrap lower bound on the difference to the window is above $-0.3$ points on 28 of the 29 streams"; body: "The lower bound is above $-0.3$ points on 28 of the 29 streams." New conclusion: "\method{} stays within 0.3 points of the plain window on 28 of the 29 real streams". The numbers 0.3 and 28/29 belong to the bootstrap lower bound, not to the accuracy difference; the body states the accuracy difference is "at most 0.25 points" below FIFO on any stream and *above* FIFO on 24 streams ($+0.57$ on average, $+4.7$ on Rialto, `main_new.tex:684–686`).
- Why it matters: the claim as written is either contradicted by a reported result (Rialto $+4.7$, so not "within 0.3 points") or misstates the count (point estimates are within 0.25 below on all 29, not 28). It silently converts a statistical lower bound into an accuracy-closeness statement.
- Recommended correction: "…\method{} is never more than 0.25 points below the plain window, and its one-sided 95\% block-bootstrap lower bound is above $-0.3$ points on 28 of the 29 streams."

**4. Severity P2 · Confirmed issue · Location: `main_new.tex:61–62` (abstract) and `main_new.tex:139–140` (contributions)**
- Evidence — new abstract: "shifting the concept boundaries inside the stored segments removes this advantage, as the single-concept premise implies"; new contribution (4): "mixed segments remove the gain". Body: "on average the advantage remains small and positive in test (a) and disappears in test (b)" (`main_new.tex:633`), and "agreement in magnitude is approximate and the first-batch term $\zeta_{k,c}$ is not predicted" (`main_new.tex:533–535`).
- Why it matters: `prop:recall` is silent outside its premises; it does not *imply* that mixing segments removes the gain, and test (a) retains a $+0.47$-point average advantage. This attributes deductive status to an empirical finding and states a stronger result than the body.
- Recommended correction: "…removes this advantage, as expected when the single-concept premise fails"; contribution (4): "mixed segments largely remove the gain (it disappears in the shifted-boundary test)."

**5. Severity P2 · Confirmed issue · Location: `main_new.tex:914` (conclusion)**
- Evidence — old conclusion (`main_old.tex:948`): "The evidence supports keeping past contexts within this two-level system; it does not establish merging by discrepancy as the source of the gain". New: "The experiments confirm both regimes of the theory." Body scope: "the observed comparison is against DDM, whose detection delay, and the slow level of \method{}, lie outside the theorem, so agreement in magnitude is approximate" (`main_new.tex:532–535`).
- Why it matters: "confirm both regimes of the theory" is a stronger epistemic claim than the paper's own stated idealisations support (margin assumption, idealised relearning, unexplained first-batch term).
- Recommended correction: "The experiments are consistent with both regimes of the theory" (or "support both regimes").

**6. Severity P2 · Confirmed issue · Location: `main_new.tex:766–768` (pool controls)**
- Evidence — old (`main_old.tex:799–800, 807–808`): "These thresholds are descriptive; passing them is not equivalence, and individual streams lose up to 0.52 points" and "at the upper cap it can exceed the archive on single streams." New: only "single streams differ by up to 0.52 points"; pattern search finds no "not equivalence" and no "exceed the archive" anywhere in `main_new.tex`.
- Why it matters: both are unfavourable qualifications (MICE's storage can exceed the archive per stream; passing the descriptive thresholds is not equivalence). They were deleted, not moved to the appendix, so the pool-control result now reads cleaner than the evidence.
- Recommended correction: restore both qualifications in the pool-controls paragraph (or in `app:prereg`), e.g. "…passing these thresholds is not equivalence; at the upper cap MICE's storage can exceed the archive on single streams."

**7. Severity P2 · Confirmed issue · Location: `main_new.tex:472` (notation table, `$K$` row)**
- Evidence — table: "$K$ & number of experts of a meta expert". Text: `def:recur` uses $K$ for the number of past intervals ("$\min_{k\le K}\Div_T(P_{K+1}\,|\,P_k)$", `main_new.tex:155–156`), and the grid generator uses $K=3$ concepts (`main_new.tex:1140`).
- Why it matters: (e) requires the notation table to match the definitions in the text; as written the table assigns a single meaning to a symbol used with three meanings.
- Recommended correction: "$K$: number of experts of a meta expert; also the number of past intervals in \cref{def:recur} and of concepts in the grid generator" (or rename one of the uses).

**8. Severity P2 · Confirmed issue · Location: `main_new.tex:57–58` and `main_new.tex:62–63` (abstract)**
- Evidence — old abstract: "a discounted regret of at most $\ln K/\eta$ against the plain window at any time, with no assumption on the stream" and "…above $-0.3$ points on 28 of the 29 streams (backbone seed 0), the remaining one being too short to decide". New: "the slow level bounds the discounted half-Brier regret against the plain window by $2\ln2\approx1.39$ at every time, for any stream" and "…above $-0.3$ points on 28" (no seed scope). `cor:outer` (`main_new.tex:364–368`) requires $\gamma=0.9$ and is stated "against a discounted horizon of $1/(1-\gamma)=10$ batches"; the bounds "concern backbone seed~0 on fixed streams" (`main_new.tex:709–710`).
- Why it matters: (d) forbids deleting load-bearing scope conditions. The constant $1.39$ is only valid for the stated discount/horizon, and the bootstrap bound was computed for backbone seed 0 only; the abstract now states both unconditionally.
- Recommended correction: "…bounds the discounted ($\gamma=0.9$, horizon 10 batches) half-Brier regret against the plain window by $2\ln2\approx1.39$ at every time, for any stream" and "…is above $-0.3$ points on 28 of the 29 streams (backbone seed 0)."

## Checks passed
(a) All retained numbers in changed lines match the old quantities (abstract, contributions, RQ1–RQ3, pool controls, cost, metrics, appendix); the only omitted number is the redundant "30 centroids: 1.7 instead of 1.9" prediction recomputation. (b) The main unfavourable results survive: both failed registered robustness criteria (now "short of the registered criterion" with the numbers intact), the failed pool criterion ($+0.30$ vs $+0.5$), archive above MICE on all misaligned/shifted streams, 3000-row window ahead on 21/29 and cheaper, LTM's AUC advantage, the log-loss collapse 86.4→74.9, retrospective/post-hoc registration status (moved to `app:prereg`), and the shared-randomness disclosure (kept in `app:grid`). The $\varepsilon_{k,c}\to\zeta_{k,c}$ rename is complete (no `varepsilon` remains in `main_new.tex`) and the theorem statements, `ass:ppd`, `ass:margin`, and the "covers the method as run, but not the variants" condition are unchanged. (c) Only the two claim-strength issues in findings 4–5. (e) All other notation-table entries match the text definitions.
