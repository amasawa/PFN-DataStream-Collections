> auditor · mimo-v2.6-pro
I'll read the remainder of `main.tex` to reach the appendix (`app:grid`) before checking descriptions against the code and numbers against the CSVs.
→ Read main.tex [offset=745, limit=2000]
The appendix is in view. I'll grep the revised file for leftover wording and key figures before concluding.
✱ Grep "permut|1887|0\.015|18\\%|48\\%|two to four|representative|independent|9\.9|8\.9|0\.94|0\.83" in main.tex · 23 matches
✱ Grep "default_rng|SeedSequence|20_000|20000|permutation" in . · 11 matches
## Audit — grid / learning-curve revision (round 8)
**Numbers checked against `predicted_indep.csv` and the two curve CSVs (all match):** Spearman 0.9429 → 0.94 (registered vs fast, seeds 10–11) and 0.8286 → 0.83 (vs MICE, seeds 20–21); ranks of `indep_registered` are identical, so "rank correlations are unchanged" holds; 9.93→9.9 vs 10.44→10.4 (`indep_registered` vs `registered`) and 8.91→8.9 vs 9.21→9.2 (`indep_visit_specific` vs `visit_specific`), all at (100, 500); max same-form prediction change 0.51 ≤ 0.6; max curve change 0.0137 at (100, n=200) ≤ 0.015; also 1.7/1.9, 9.2/8.6, 0.55/0.53, 3.0/2.6, 10.4/8.6 in RQ1 all match. Code checks match: distributions/parameters (`grid_streams.stream`), 4000-row blocks with rows 1–3000/3001–4000, `default_rng(rep)` seeds 0–2, `TFM(4, seed)`, log-*n* interpolation, average-before-area aggregation, visits 2 and 3 with weight 1/3 each (`for c in (2,3)) / 3`), `(J-1)/J` = 1/J·Σ_{j=1}^{J-1}, observed gain = mean of per-stream `mice1 - ddm` over the two streams, Spearman over six cells. Reviewer items 1–3 are addressed in main.tex (Shared randomness + RQ1 seed-pair distinction + "representative of the concepts"; Learning curves / From curves to predictions; Generator's "not a permutation… no rejection or coverage constraint"). No overclaim of independence or transfer found: seed-10/11 is scoped to already-sampled concepts, seed-20/21 to "two data seeds" transfer.
---
**F1**
- **Severity:** P2
- **Finding status:** Missing information
- **Location:** `main.tex` app:grid, "Generator" (18%–48% agreement weight; two to four classes) and "Shared randomness" (0 to 1887 identical rows)
- **Evidence:** `learning_curve.csv` / `learning_curve_indep.csv` / `predicted_indep.csv` contain only accuracies and predictions (no labels, rows, or class counts). These three figures cannot be checked from the attached CSVs; no counting script/output is attached.
- **Why it matters:** These are the disclosures reviewer item 1/3 turned on; they must be right if the reviewer checks them.
- **Recommended correction:** Attach or cite the script/outputs that computed the agreement weight per concept pair, the class-presence counts, and the row-identity count.
**F2**
- **Severity:** P2
- **Finding status:** Suspected issue
- **Location:** `main.tex` app:grid, "Shared randomness" ("some rows are identical (0 to 1887 per stream)")
- **Evidence:** From the attached code, curve rows (`stream(nc, 4000, seed, cycles=1)`) and stream rows (`stream(nc, L, s)`, `L∈{500,2000}`) share the concept definitions and at most the first `L` centroid draws of the first block (`rng.choice` consumes the same leading uniforms); `x = C_j + N(0,0.15²I)` is then drawn after 4000 vs `L` categorical draws, so bit-identical `X` rows would need bit-identical noise draws from different generator offsets, which this code path does not produce. `learning_curve_indep.no_overlap()` compares `bytes` of float32 `X` rows — the same definition would give 0 matches for the original curves under this mechanism. The count cannot be verified from the CSVs (see F1).
- **Why it matters:** Overstated overlap is conservative for the independence claim, but a reviewer inspecting the released code may find "1887 bit-identical rows" inexplicable and discount the whole disclosure.
- **Recommended correction:** State exactly what counts as identical (float32 bytes of `X`? `(centroid, label)`? rounded rows?) and re-verify the count; if identity is not at the level of full `X` rows, reword "rows are identical".
**F3**
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** `main.tex` app:grid "Shared randomness" ("an independent generator"); `registration_r8.md` line 11; `learning_curve_indep.py` docstring line 5 vs line 24
- **Evidence:** The code draws rows with `np.random.default_rng([20_000 + seed, nc, k])` (entropy list depending on `m` and concept `k`), not `default_rng(20 000 + seed)` as the registration and the script's own docstring state; main.tex says only "an independent generator".
- **Why it matters:** Reviewer item 1 asked for the actual initialisation/substream mechanism to be documented; "an independent generator" plus a wrong seed formula in the registration does not satisfy that and is not reproducible from the prose.
- **Recommended correction:** State the seeding (`default_rng([20000+seed, m, k])`, one stream per `m` and concept, given concept definitions of `default_rng(seed)`) in app:grid or point to `learning_curve_indep.py`, and fix the registration/docstring wording.
**F4**
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** `grid_streams.py` lines 3–4 (docstring) vs line 19 and `main.tex` app:grid line 1029
- **Evidence:** The docstring says labels are "a random permutation per concept", but the code draws `rng.integers(n_classes, size=nc)` i.i.d. per concept; the paper correctly says "it is not a permutation".
- **Why it matters:** Reviewer item 3 asked for the permutation framing to be removed; the released generator still asserts it, contradicting both the code and the manuscript.
- **Recommended correction:** Change the docstring to "an independent uniform class label per centroid and concept (not a permutation)".
All other checked descriptions and figures in the reviewed passages (Section 5 "Streams" sentence, RQ1's two-seed-pair sentences, the introduction sentence, app:grid Generator / `tab:gridparams` / Learning curves / From curves to predictions) match the code and CSVs within the stated tolerances.
