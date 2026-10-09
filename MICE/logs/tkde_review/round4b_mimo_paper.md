> auditor · mimo-v2.6-pro
I'll recompute every figure from the CSVs and check the text, tables, and registration. First let me read the rest of `main.tex` (Limitations and anything after line 768).
✱ Grep "boundary|boundaries|shift|misalign|archive|Archive|segment" in . · 91 matches
→ Read main.tex [offset=764, limit=120]
All figures in both tables and in the RQ2, abstract, conclusion and Limitations sentences recompute exactly from `misaligned.csv` / `offset.csv` (per-cell values, means, ranges, counts, and the `make_robust_tables.py` rounding all match). Findings below are wording/reporting issues only.
## Findings
### 1. Test (b)'s registered criterion and its failure are never stated in the body
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** main.tex §RQ2, test (b) paragraph (lines 553–572); contrast with test (a) line 542; Limitations line 768
- **Evidence:** `registration_4b.md` registers a criterion in the same form as 4.a: "MICE − DDM on the offset streams positive on ≥ 7 of 8 and mean ≥ +1.0"; `check_offset.py` prints it as MET/NOT MET. Observed: positive on 1 of 8 (`off_d_ddm`: only `100/2000/20` = +0.11), mean −3.67 → NOT MET. Test (a) explicitly writes "The registered criterion … *fails*" (line 542–543); test (b) reports the same facts but never names the criterion or its verdict. Limitations (line 768) asserts "both registered robustness tests failed", which is unsupported for (b) as written in the body.
- **Why it matters:** The workflow requires all registered decision rules and their outcomes to be reported; the reader cannot verify "failed" for (b) from §RQ2 alone.
- **Recommended correction:** In the test (b) paragraph add one sentence: the registered descriptive criterion (above reset on ≥7 of 8 with mean ≥ +1.0) fails (1 of 8, −3.7 points on average).
### 2. Abstract/conclusion compress the two robustness tests into a claim the body contradicts
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** Abstract lines 62–64 ("the large recall gains therefore hold only when concept boundaries coincide with segment boundaries"); contribution (4) line 139–140; Conclusion lines 759–761 ("this advantage disappears")
- **Evidence:** Test (a) has boundaries *inside* segments and yet MICE stays above reset on all six 100-centroid streams (+0.8 to +1.9 overall; +7.1 to +10.9 in the first five batches of recurring blocks) and above the window ensemble on all twelve (lines 544–547). Test (b) recurrence windows also keep sizeable gains on 2 000-row/100-centroid streams (+7.3, +5.7; `off_d_ddm_rec5`), while the whole-stream advantage vanishes (−3.7 mean). "Advantage disappears" and "hold only when" are accurate for the *average* gain and for test (b), not for misaligned hard concepts or for per-recurrence recall.
- **Why it matters:** Overstates the negative result in the two sentences most readers see first; contradicts §RQ2 and can be attacked in review.
- **Recommended correction:** Qualify as "the large *average* gains hold only when boundaries coincide…; when they fall inside segments the average advantage disappears (test (b)) or shrinks below two points (test (a)), although recall right after a recurrence still helps".
### 3. Registered "also reported" contrasts for the offset streams are omitted, asymmetrically with test (a)
- **Severity:** P2
- **Finding status:** Confirmed issue (numbers) / the choice to omit is the issue
- **Location:** main.tex test (b) paragraph (lines 557–562) vs test (a) line 547 ("stays above the window ensemble on all twelve streams"); `registration_4b.md` "Also reported: MICE − FIFO, − window ensemble, − archive (offset and aligned), overall and in recurrence windows"
- **Evidence:** From `offset.csv`: `off_d_winens` = −4.93, −8.55, +0.63, +0.18, −0.91, −1.34, +1.59, +1.84 → MICE is *below* the window ensemble on 4 of 8 shifted streams (all 500-row-block cells, by up to 8.5 points; mean −1.4), and `off_d_winens_rec5` is also negative on the 500-row-block cells. The text only says the baselines themselves are "almost unchanged (within one point)" (true: max |change| 0.95) and compares to reset and the archive.
- **Why it matters:** Test (a) advertises the window-ensemble comparison; test (b) omits the corresponding adverse result, understating the negative outcome of the shift.
- **Recommended correction:** Add "on the shifted streams MICE is below the window ensemble on the four 500-row-block streams (−0.9 to −8.5 points) and above it on the four 2 000-row-block streams" (and optionally the FIFO contrast, which stays largely positive).
### 4. The verbatim 4.a registration is not in the reviewed package
- **Severity:** P2
- **Finding status:** Missing information
- **Location:** main.tex lines 542–543 ("The registered criterion, … at least 10 of the 12 streams with a mean gain of at least one point")
- **Evidence:** Only `registration_4b.md` is attached. Its "same form as 4.a" note (positive on ≥N of N and mean ≥ +1.0) is consistent with the quoted 4.a criterion and with the observed FAIL (8 of 12, +0.47), but the exact registered wording cannot be checked.
- **Why it matters:** The paper's claim that a *registered* criterion failed should be traceable to the registration file.
- **Recommended correction:** No text change needed if `experiments/mice_tkde_control/PLAN.md` (or the 4.a registration) contains this criterion verbatim; otherwise align the quoted criterion with what was registered.
## Verified correct (no issue)
- **tab:misaligned**: all 12 rows and the Mean row (85.0 / 84.5 / 64.4 / 82.0 / 85.8 / +0.47 / +4.6 / −0.89) match `misaligned.csv` under the `make_robust_tables.py` formatting.
- **tab:offset**: all 8 rows and the Mean row (+3.09 / −3.67 / −6.76 / +9.1 / −2.9 / +0.30 / −2.99) match `offset.csv`.
- Test (a) text: 8 of 12 above reset, +0.47 mean; 100 cent. 6/6, +0.8 to +1.9, rec5 +7.1 to +10.9; 30 cent. −0.7 to +0.3, rec5 −2.3 to +2.5; above window ensemble on 12/12; archive above MICE on 12/12 by 0.2 to 1.8 — all correct.
- Test (b) text: Δ mean −6.8 (range −1.0 to −14.4), rec5 Δ −12.0; below reset 7 of 8, mean −3.7, worst −10.8 in 500-row blocks; archive above MICE on 8/8 by 3.0 mean; aligned MICE +0.3 above archive; "within one point" for FIFO/reset/winens under shift; 500-row blocks all below reset; 2 000-row blocks lose 1.0 to 3.0 of their advantage; "7 of the 8 boundaries" for blocks of 700 and 1 300 — all correct.
- Registration 4.b compliance otherwise holds: matched batches with batch t+2 = aligned t (SHIFT=2 in `check_offset.py`), recurrence windows = first five batches of blocks 4–9 with +2 shift, primary contrast Δ reported descriptively, and the pre-stated limit ("sensitivity to this phase shift rather than a pure effect of mixed segments") is carried into the paper (line 563–564). No causal overclaim: "can corrupt that expert" is properly hedged.
