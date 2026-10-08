> build · mimo-v2.6-pro
Verification of the four attached files only. The quoted figures against `noninferiority.csv` / `noninferiority_sources.csv` and the procedure against `noninferiority.py` are consistent except as noted; findings follow.
---
**1.**
- Severity: P2
- Finding status: Confirmed issue
- Location: `main.tex`, RQ3 “Uncertainty.” paragraph: parenthetical “blocks of 20 batches, 10\,000 resamples; blocks of 10 and 50 give the same counts”, with the following sentence’s two counts (“28 of the 29”, “all six segments”).
- Evidence: For `lb95_b50`, `h4_covertype_e` is `-0.0300303` (= -30/999), i.e. **not** above `-0.03`; so the six-segment count under blocks of 50 is 5/6, not 6/6. Under `lb95_b10` (`-0.0270`) and `lb95_b20` (`-0.0290`) it is 6/6, and the 28/29 count holds for all three block lengths. The plural “counts” sits before both counts and therefore asserts robustness of both.
- Why it matters: A robustness claim that fails for one of the two stated counts at a threshold the paper treats as decisive (the held-out confirmation) is an overstatement of stability.
- Recommended correction: Either restrict the clause to the stream count (“blocks of 10 and 50 give the same count of streams above $-0.3$”) and state the six-segment claim for the primary block length, or replace “above $-0.03$” by a threshold that holds for all three block lengths (e.g. “above $-0.04$”), or report `h4_covertype_e` as $-0.029$ (b=20) / $-0.030$ (b=50).
**2.**
- Severity: P2
- Finding status: Suspected issue
- Location: `main.tex`, “Uncertainty.” paragraph: “above $-0.03$ on all six segments of the fourth held-out set” and “above $-0.14$ points for eight sources”.
- Evidence: Both statements are true for the primary block length but sit at the resolution of the reported data: `h4_covertype_e` `lb95_b20 = -0.02903` (0.001 points of slack) and `weather` source `lb95 = -0.13889` (0.001 points of slack). `h4_covertype_e` flips at b=50 (finding 1). Values are discrete multiples of `1/999` and `1/180`, so the claims rest on a single grid step.
- Why it matters: Categorical threshold claims with ~0.001-point slack are not verifiable from rounded prose and read as stronger evidence than the bootstrap resolution supports.
- Recommended correction: Quote the actual bounds (e.g. “the worst bound is $-0.029$ points on `h4_covertype_e`”; “the worst source bound is $-0.139$ for Weather”) or loosen the thresholds to the next robust value.
**3.**
- Severity: P2
- Finding status: Suspected issue
- Location: `main.tex`, last sentence of the abstract (“with one-sided 95\% block-bootstrap bounds it is non-inferior to the window at a 0.3-point margin on 28 of the 29 streams”) versus the paragraph’s own caveats.
- Evidence: The paragraph restricts the claim (“These bounds concern backbone seed~0 on fixed streams; the second seed varies the model, not the data, and segments of one source are not independent evidence”), and the bounds are 28 separate pointwise one-sided 5% bounds (no multiplicity adjustment). The abstract states non-inferiority as established, without those conditions.
- Why it matters: The abstract is the part most read; as written it supports a general non-inferiority claim that the analysis does not provide (conditional on backbone seed 0 and the realized streams; not a simultaneous guarantee).
- Recommended correction: Align the abstract with the paragraph, e.g. “non-inferior … on 28 of the 29 streams (one-sided 95% block-bootstrap bounds, seed 0)”, or drop “non-inferior” in favour of “its one-sided 95% lower bound is above $-0.3$ points on 28 of the 29 streams”. The paragraph’s formulation (“claim non-inferiority … for the streams where the bound supports it”) is appropriately scoped and needs no change.
**4.**
- Severity: P2
- Finding status: Suspected issue
- Location: `main.tex`, “Uncertainty.” paragraph (method description); `noninferiority.py` `block_means` / `np.percentile(bm, 5)`.
- Evidence: The implementation is as described (moving-block bootstrap over batches, blocks 10/20/50, 10\,000 resamples, one-sided lower bound = 5th percentile, per-source mean with each stream resampled independently). But a moving-block bootstrap of the per-batch differences assumes local stationarity of that difference; the streams are drifting by design, and the percentile bound is neither studentized nor basic.
- Why it matters: The sentence presents the bounds as accounting for “sampling variability and dependence between consecutive batches”, which invites reading the 95% as nominal coverage; under drift that coverage is approximate, so “non-inferior” inherits that approximation.
- Recommended correction: Add one clause that the bootstrap treats the per-batch differences as locally stationary (or use a stationary bootstrap / subsampling and say so), and that the bound is a percentile approximation.
**5.**
- Severity: P2
- Finding status: Missing information
- Location: `main.tex`, last sentence of the abstract (“more accurate than all four in-context baselines on 23”, “a pre-registered test on six held-out segments confirms both”); `noninferiority.py` `series()` (`reweight.simulate2`).
- Evidence: The attached CSVs contain only the difference to FIFO (mean and three bounds), so “23 of 29 versus four baselines” and the registered hypotheses cannot be checked here. The per-batch MICE series is produced by `reweight.simulate2(c, outer="brier", scale=0.5, temper=True)` on cached predictions; that module is not among the attached files, so the replay is not verified to be the registered two-level rule.
- Why it matters: These are the two claims in the abstract that the reviewed artefacts do not support either way.
- Recommended correction: None required in the text; for verification, point the audit at `reweight.py` and the per-stream baseline table (or state the 23/29 count and the registered-test outcome in a table that can be checked).
---
No P0/P1 findings. All other numbers in the two passages check out against the CSVs: 28/29 with `lb95` above $-0.3$ for b=10/20/50; all six `realI` segments above $-0.03$ for b=10 and b=20; `h2_spam` 61 batches, `mean = -0.2459` ($-0.25$), `lb95_b20 = -0.8525` ($-0.85$); nine sources, eight with `lb95` above $-0.14$ (worst non-Spam is Weather $-0.1389$), Spam $-0.8525$; abstract “never more than 0.25 points below the plain window” matches the worst stream mean ($-0.2459$). `noninferiority.py` matches the described procedure on every listed point (MBB over batches, 5th percentile as the one-sided 95% lower bound, blocks 10/20/50 with 20 primary, 10\,000 resamples, source level = unweighted mean over streams with independent per-stream resampling and a 5th percentile). Note that the source-level bound is computed only for the primary block length and is an unweighted mean over streams of unequal length (Covertype 1499/999, Insects 240–798); the sentence “Averaged within each of the nine sources” would be clearer if it said “unweighted mean over the streams of the source”.
