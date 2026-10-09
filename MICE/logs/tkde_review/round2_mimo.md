> auditor · mimo-v2.6-pro
I'll read the remainder of `main.tex` (ablation, conclusion, limitations) before checking numbers against the CSVs.
→ Read main.tex [offset=733, limit=400]
I checked the pool-control paragraph, both tables, the abstract/contributions/conclusion/Limitations wording, the registration file, and the analysis code against the two CSVs. Table rows and the paragraph’s counts match the data (details below); the issues are in derived claims and labelling.
**Verified against the CSVs (no finding):** grid rows and the 30/100 summary (`+0.30`, `+3.25`, `6.3/10.0` calls) match `pool_control_grid.csv` and `make_pool_tables.py`; real-stream rows match `pool_control_real_full.csv` (spot-checked Electricity, Spam, Mean row: 83.82, `+0.07`, `−0.08`, 8.4/14.2, 9.7/14.0). Counts: archive positive 18/29, snapshot positive 11/29, LB ≥ −0.3 on 17 (snap) and 23 (arch), fewer calls 25/29 — all correct. Criteria are applied as registered (criterion 1 correctly reported FAIL at `+0.30` vs `+0.5`, 7/8; criterion 2 PASS at `+0.07 ≥ −0.1`; snapshot threshold PASS at `−0.08 ≥ −0.1`). The bootstrap in `pool_control_real.py` is correct now: `n = len(next(iter(d.values())))` (batch count), one `idx` per (stream, block) applied to both difference series (joint, paired), `b_ = b if n >= 2*b else n//2`, non-circular blocks, 10 000 resamples, 5th percentile — matching the registration and the text.
## Findings
**F1 · P2 · Confirmed issue**
- **Location:** `main.tex` abstract, lines 65–67 (“on real streams the three pools are within 0.1 points on average”).
- **Evidence:** From the CSVs, mean MICE − arch = `+0.074`, mean MICE − snap = `−0.078`, hence mean snap − arch = `+0.152` (means 83.82 / 83.75 / 83.90). The three pools are *not* within 0.1 points of each other on average; only MICE is within 0.1 of each control. (The average of the three pairwise gaps is 0.10, which may be the source of the sentence, but that is not what it says.)
- **Why it matters:** The abstract states a false pairwise closeness claim about the main controls.
- **Recommended correction:** “on real streams MICE is within 0.1 points of each control on average (`+0.07` vs the archive, `−0.08` vs the snapshot)”.
**F2 · P2 · Confirmed issue**
- **Location:** `main.tex` lines 782–783 (“the bounds against the archive were computed after its registration”); table caption lines 812–814 (“archive bounds computed after registration”).
- **Evidence:** `registrations_round2.md` requires: “The same analysis applied to MICE − archive is retrospective and labelled so.” The paper never uses “retrospective”; “computed after its registration” reads as if the bound analysis had been registered and only executed later.
- **Why it matters:** Misstates the registration status of an analysis — exactly the registered-vs-retrospective distinction the revision promised.
- **Recommended correction:** “the bounds against the archive are retrospective (not registered; computed after the run)”.
**F3 · P2 · Confirmed issue**
- **Location:** `main.tex` line 772 (“(registered before the runs)”); abstract line 65 (“In response to review…” framing).
- **Evidence:** `registrations_round2.md` (“Round 2 addition”) registers the snapshot control and records its provenance: “The 29 streams and the MICE results were examined before this registration; this run is a review-added control, not an independent confirmation.” `round2_expert_a2.md` required this label. The paper says only “In response to review” and omits the examined-data caveat.
- **Why it matters:** A reader can take the snapshot comparison as independent confirmation on untouched streams.
- **Recommended correction:** Add “review-added; the 29 streams and the MICE results had been examined before this registration; not an independent confirmation.”
**F4 · P2 · Missing information**
- **Location:** `main.tex` line 772 (“two pools … (registered before the runs)”), caption line 795 (“registered”).
- **Evidence:** The attached registrations cover the archive (criteria 1–2) and the snapshot **on the 29 real streams** only. The grid snapshot (`snap` columns of `pool_control_grid.csv`) appears only as “Also reported: snap” in `check_pool_control.py`, whose docstring cites a `PLAN.md` that is not attached. So pre-registration of the *grid* snapshot comparison cannot be verified from the reviewed files.
- **Why it matters:** `tab:poolgrid` is captioned “(registered)” for a comparison whose registration is not in evidence.
- **Recommended correction:** Either cite the plan entry that registered the grid snapshot, or label the grid snapshot column “reported (no registered criterion)” — its `+3.3` figure is already used descriptively, which is fine.
**F5 · P2 · Suspected issue**
- **Location:** `main.tex` line 785 (“MICE uses fewer resources than both controls”); abstract lines 66–67 (“fewer experts and less storage”).
- **Evidence:** Experts (8.4 vs 14.2) and calls (9.7 vs 14.0, fewer on 25/29) are measured and correctly qualified in the body. Storage is *not* measured: per-expert rows were not recorded; the stated 2 700–5 400 range is 500–1000 rows × the mean pool size. Per stream the upper end exceeds the archive (CoverType 11 731 vs 5 874; h3_covertype_b 10 385 vs 5 811; h2_poker 9 409 vs 5 811; h2_rialto 10 687 vs 5 770). The mean upper bound (5 361 → “5 400”) is just below the archive’s 5 591, so “less storage” holds only on average and only as a cap bound. `round2_expert_a2.md` warned against exactly this (“claims of actual storage … would require additional evidence”).
- **Why it matters:** Blanket resource claim rests partly on unrecorded quantities and is false per stream under the upper cap.
- **Recommended correction:** “on average, MICE uses fewer active experts (8.4 vs 14.2) and fewer calls (9.7 vs 14.0; fewer on 25 of 29); stored rows are between 2 700 and 5 400 on average from the 500/1000 per-expert caps, against 5 600 (archive) and 11 100 (snapshot); per-stream storage can exceed the archive at the upper cap.” Qualify the abstract the same way (“fewer experts and less storage on average, bounded from the caps”).
**F6 · P2 · Confirmed issue**
- **Location:** `main.tex` lines 784–785 (“individual streams lose up to 0.5 points”).
- **Evidence:** Worst observed loss is `d_snap = −0.52` (INSECTS abrupt imbalanced); worst `d_arch = −0.32`. “Up to 0.5” understates the worst loss.
- **Recommended correction:** “up to 0.52 points” or “up to 0.6 points”.
**F7 · P2 · Confirmed issue**
- **Location:** `main.tex` abstract line 65 (“Against pools that keep past segments without merging them”).
- **Evidence:** The archive keeps past segments; the snapshot pool stores `min(1000, rows so far)` at each close (`run_poolcontrol_excerpt.py`), i.e. rolling snapshots that span up to two segments, not past segments. The body and `tab:poolreal` describe it correctly; only the abstract bundles both under “keep past segments”.
- **Recommended correction:** “Against pools that keep past contexts without merging them (an unmerged archive of segments and a snapshot pool)”.
No other mismatches found: contribution (2)’s “not evidence that merging improves streaming accuracy”, contribution (4)’s “did not meet its improvement criterion over an unmerged archive”, the conclusion’s “it does not establish merging by discrepancy as the source of the gain”, and the Limitations sentence are mutually consistent and match the registered narrowing plan; “passing them is not equivalence” is stated explicitly; `+0.3`/`+0.5`, `+0.30`, `+3.3`, 7/8, 18, 11, 17, 23, 25/29, 8.4/14.2, 9.7/14.0 all match the CSVs.
## Confirmable only by running code
1. That `pool_control_real_full.csv` (including all LB columns) was produced by the current fixed `lower_bounds` — re-run `pool_control_real.py` on the run root and diff. The attached code is correct; the reported CSV’s provenance is not verifiable from the attachments.
2. That `reweight.simulate2(outer='brier', scale=0.5, temper=True)` replays the `mice`/`arch`/`snap` accuracies in the CSVs from the pickled caches (caches not attached).
3. That the `calls` counters in the `.npz` files include MICE’s discrepancy calls at segment closes (claimed in the registration; counter semantics not verifiable from the attached excerpts).
4. That `make_pool_tables.py` regenerates `tab_pool_*_rows.tex` byte-identically from the attached CSVs (I verified the arithmetic of every grid row and of the real rows I sampled; a full run would close this).
