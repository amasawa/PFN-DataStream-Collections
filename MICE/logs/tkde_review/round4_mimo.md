> build · mimo-v2.6-pro
Verified against `misaligned.csv` first: `pos = 8`, `mean d_ddm = +0.4665` → `+0.47`, so `check_misaligned.py` applies the PLAN criterion (`pos >= 10 and mean >= 1.0`) exactly and the FAIL verdict is right. Criterion application and the numeric claims in the Misaligned-boundaries paragraph, abstract, conclusion and Limitations check out (ranges 0.75–1.87 → "+0.8 to +1.9"; rec5 7.07–10.93 → "+7.1 to +10.9"; c30 −0.74…+0.29 → "−0.7 to +0.3"; d_winens all > 0, mean 2.99 → "+3.0"; |d_arch| 0.17–1.84, mean 0.89; |d_arch_rec5| 0.63–4.30, mean 2.59; archive better on 12/12). Three findings:
**F1**
- Severity: P2
- Finding status: Confirmed issue
- Location: `main.tex`, RQ2 "Misaligned boundaries" — "whose blocks are 700 rows, 1 300 rows, or drawn from 500 to 2 500 rows, so that most segments straddle a boundary"
- Evidence: from `make_misaligned.py` and the 500-row closing rule: for 700-row blocks only about 7 of ~12–13 segments contain a switch in their interior; for 1300-row blocks (9×1300 = 11 700 rows ≈ 23 segments) only 6–7 of 8 switches fall strictly inside a segment, so under a third of segments straddle; for `bvar` (9 blocks averaging ~1 500 rows, ~27 segments) at most 8 segments straddle. Only in the 700-row condition is "most" roughly defensible.
- Why it matters: as written the test sounds harsher than it is — in two of three conditions most closed segments are pure within one concept — which distorts how a reader weights the failed robustness criterion and the archive comparison.
- Recommended correction: replace with the true design fact, e.g. "so that concept boundaries fall inside the 500-row segments rather than on their edges" (7 of 8 boundaries for both 700 and 1300 rows).
**F2**
- Severity: P2
- Finding status: Suspected issue
- Location: `main.tex` same paragraph — "merging segments by discrepancy can thus combine rows of different concepts, and keeping the segments apart recalls better"; `run_excerpt.py` `PoolControl._merge_or_add`; `PLAN.md` controls
- Evidence: `arch` experts hold one closed segment (`Xs[-self.M:]` with `|Xs| = 500`), while MICE stored experts keep the last `M = 1000` rows after merges (`main.tex` "A stored expert keeps its last M rows"); the pool therefore differs in per-expert context size (500 vs up to 1000) and in expert count (up to 9 single-segment experts vs ~3 merged), which changes K in the fast-level weighting (Lemma 1 / Proposition 2). `PLAN.md` itself defines the storage-matched control `snap1000_500` for exactly this confound, but the round-4 method list runs only `arch1000_500`, and snap is never reported. No purity diagnostic of the merged pool is shown.
- Why it matters: the causal sentence attributes the 0.2–1.8 point archive advantage solely to cross-concept merging; the evidence supports "an unmerged archive was more accurate under these constants", not that mechanism specifically.
- Recommended correction: run/report snap on the misaligned streams, or weaken to an associational statement and note the context-size and expert-count differences between arch and MICE.
**F3**
- Severity: P2
- Finding status: Missing information
- Location: `check_misaligned.py:24–28` (`reweight.simulate2(c, outer="brier", scale=0.5, temper=True)`); compare `main.tex` §4 constants (η = 10, γ = 0.9, η₂ = ½, half Brier)
- Evidence: `reweight.py` is not in the reviewed scope, so the replay cannot be checked against the registered rule. `temper=True` has no counterpart in the paper's equations (`w_k ∝ exp(-η ℓ_k)`), γ is not passed (default unknown), and `t` comes from `simulate2` keys used to index `["acc"][t]` with an unverified 0-/1-based convention (batch counts 62/116/134 are consistent with 0-based keys and one unscored batch, but not proof). Baselines are aligned to the same `t`, so internal comparisons remain consistent either way.
- Why it matters: if the replay weights or batch indexing deviate from the frozen two-level rule, the reported MICE numbers are not the registered method, and the FAIL verdict would stand on unregistered numbers.
- Recommended correction: document that `simulate2` with these arguments reproduces Section 4 exactly (temper meaning, γ, η, batch-key base) in the paper appendix or the script docstring.
No label leakage found in `PoolControl`: segments close only from rows with arrived labels (`closed + seg ≤ t·B`), losses use batch `t−1` labels one batch late as in the protocol, and `snap` (unused here) also slices only past rows. `recurring_batches` is correct for this generator (block lengths are multiples of 100, so `r // B` is exact; `starts[3:]` is exactly the six blocks whose concepts appeared in the first cycle; `b0…b0+4` are the first five batches of the recurring block).
