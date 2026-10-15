[0m
> auditor · mimo-v2.6-pro
[0m
## Audit: `CPSegments` / `MiceCP` / `ArchCP` (round 14 change-point segmentation)

Scope reviewed: `run_py.diff`, `run_classes_excerpt.py`, `run_driver_excerpt.py`, `tune_detector.py`, `tune_output.txt`. Intended behaviour checked point by point: causality, unchanged legacy kinds, checkpoint resume, tune ↔ online reproduction.

**Verified as correct (no finding):** causality holds (`err[t-1]` from labels of batch t−1 only; cuts at rows ≤ (t−1)·B; closed segments use labelled rows only); detector formula matches the docstring exactly (`run_classes_excerpt.py:85-86`); Hoeffding margin `sqrt((1/n1+1/n2)/2·ln(1/δ))` is the correct one-sided bound; ordering inside `_segment` (change cut before periodic close) correctly prioritises detections, and the `H·B` periodic delay guarantees any change in a segment body is tested before that segment closes; drop path (`< LMIN`) and `ref0 = b+1` match the docstring; `MiceCP`/`ArchCP` MRO is right (CP `step` wins; `_merge_or_add` resolves to `Mice`’s for `MiceCP`, `PoolControl`’s for `ArchCP`; `Xall/yall` set inside CP `step` so `PoolControl.step` is not needed); legacy classes are untouched (pure additions + driver else-branches); `getattr(pol, "cuts", [])` is safe for `pol=None` and legacy kinds; checkpointed state (`err`, `ref0`, `cuts`, `closed`, `pending`) round-trips and resumes on the same trajectory (err[t] filled from restored `pending`, then `_segment` — identical to the uninterrupted order).

### Findings

**1. P1 · Confirmed issue · `run_driver_excerpt.py:16-17` (`run_py.diff:98-99`)**
- Evidence: `MiceCP(f, M, seg=int(m.group(3))) if kind == "micecp"` / `ArchCP(f, M, seg=int(m.group(3)))`. With `method = "micecp1000"` or `"archcp1000"` the regex `([a-z]+)(\d+)(?:_(\d+))?` gives `group(3) is None`, and `int(None)` raises `TypeError`. Every other kind guards this: `seg=int(m.group(3)) if m.group(3) else 1000` (micev, arch, snap).
- Why it matters: suffix-less names are the documented, working convention for the classes these replace (“MiceV1 whose segments start at detected changes”); the new kinds crash at construction for them.
- Recommended correction: use `seg=int(m.group(3)) if m.group(3) else 1000` in both branches.

**2. P2 · Confirmed issue · `tune_detector.py:58` vs `run_classes_excerpt.py:75`**
- Evidence: script default setting `[(300, 3, 5, 2, 0.01, 300)]` (DELTA_CP = 0.01); shipped class `DELTA_CP = 0.001`; `tune_output.txt:1` shows the reported results used 0.001.
- Why it matters: `python tune_detector.py <root>` with no settings evaluates a detector different from the deployed one (a looser margin → more cuts), so a re-run “to check the numbers” silently disagrees with both the class and the logged output.
- Recommended correction: default the settings to `run.CPSegments` class constants (SIG, H, R, RMIN, DELTA_CP, LMIN) instead of a duplicated literal.

**3. P2 · Confirmed issue · `tune_detector.py:30` (cf. `run_classes_excerpt.py:119`)**
- Evidence: `P = {st["t"]: st["P"][-prm[0]] for st in c["cache"]}` — `prm[0]` (SIG) is advertised as tunable in the usage line, but cached predictions exist only for window keys −100, −300, −1000; any other SIG raises `KeyError`. The online class has the same coupling (`self.pending[-self.SIG]`).
- Why it matters: the script’s stated parameter sweep over SIG is not actually supported; a tuning attempt with SIG=200 fails (or, if windows change, the online class raises mid-run).
- Recommended correction: assert `prm[0]` is among the cached window sizes (and document SIG ∈ window sizes in the class docstring).

**4. P2 · Confirmed issue · `tune_detector.py:44-46`**
- Evidence: `mixed_rows = rows[pur < 0.95].sum() / rows.sum()` (row-weighted) vs `fixed_mixed = (fpur < 0.95).mean()` (unweighted share of fixed segments).
- Why it matters: the two are printed side by side as if comparable (e.g. `mixed_rows=0.00` vs `fixed_mixed=0.89` on `d_b500_o200_*`), overstating the gain of change-point segmentation against the fixed grid.
- Recommended correction: compute both as row-weighted shares (or both as segment shares).

**5. P2 · Confirmed issue · `tune_detector.py:27-29, 32, 59`**
- Evidence: `evaluate(f, prm, B=100, seg=500)` hardcodes B and seg while the pickle already stores `B` (`c["B"]` is never read) and the glob is fixed to `*__micev1000_500.pkl`; `T = len(c["y"]) // B`, error counts and the segment grid all use the hardcoded B.
- Why it matters: any cache produced with a different B (or a different seg) is evaluated on the wrong batch grid and the reproduction claim (“exactly those an online run would close”) fails silently.
- Recommended correction: read `B` (and the seg encoded in the filename or stored) from the cache; assert consistency.

**6. P2 · Missing information · `run_py.diff:103` (unchanged driver line)**
- Evidence: `CK = int(os.environ.get("MICE_CKPT_EVERY", 100))` — default 100 batches; the stated intended behaviour says checkpoints are written every 10 batches. The mechanism (`pol.__dict__` minus `f/Xall/yall`, restored by `__dict__.update`) matches the code.
- Why it matters: if 10 is the intended cadence, the default is wrong (a crash loses up to 100 batches of a multi-hour run); if the launcher sets `MICE_CKPT_EVERY=10`, this is only a documentation gap.
- Recommended correction: confirm the launcher env; otherwise change the default or the documented cadence.

**7. P2 · Missing information · reproduction claim (`tune_detector.py` vs `Mice` base class)**
- Evidence: `Sim.__init__` fixes `self.closed = 0` (`tune_detector.py:21`), but the online initial value comes from `Mice.__init__`, and `Mice._merge_or_add` (used by `MiceCP`) is not in the reviewed files. Fidelity of `tune_detector` to an online `MiceCP` run requires: `closed` starts at 0, and `_merge_or_add` never touches `closed`/`ref0`/`err`/`cuts`.
- Why it matters: if either fails, the offline segments diverge from the online ones even though everything else matches.
- Recommended correction: verify `Mice.__init__` / `_merge_or_add` against these two points (statically — reading the base class is enough).

**8. P2 · Confirmed issue · `run_py.diff:127-131`**
- Evidence: `np.savez_compressed(..., cuts=np.array(getattr(pol, "cuts", []), dtype=int).reshape(-1, 2))` runs for every kind, so legacy methods (fifo/ltm/ddm/mice/micev/arch/snap) now emit an extra `cuts` key (empty for them); algorithm behaviour is unchanged.
- Why it matters: output-schema change for all existing result files; any consumer with strict key checks or byte-identical reproducibility expectations will see a difference between old and re-run results.
- Recommended correction: none required for correctness; note the schema change in the results documentation.

### Points that can only be confirmed by running code
1. End-to-end reproduction: an online `micecp*` run’s `cuts` equal `tune_detector`’s `sim.cuts` on the same stream/parameters (the core claim of the offline tuner).
2. Checkpoint round-trip: a run killed and resumed from `.ckpt` yields identical `acc`/`ll`/`cuts` to an uninterrupted run (pickle of `err`/`ref0`/`cuts`/`closed`/`pending`).
3. Regression: `micev`/`arch`/`snap` runs before vs after the diff produce identical `acc`/`ll` (only the npz gains `cuts`).
4. Re-running `tune_detector.py` with `(300,3,5,2,0.001,300)` reproduces `tune_output.txt` (120/120 found, 0 false).
5. `python tune_detector.py <root> 300,3,5,2,0.001,200` etc. raises `KeyError` for SIG ∉ {100,300,1000} (finding 3; statically certain, trivially runnable).
6. `run(stream, "micecp1000", 100, out)` raises `TypeError: int() argument must be a string...` (finding 1; statically certain).

No P0/P1 scientific issues found: the detector is causal, legacy method behaviour is untouched, and the offline tuner reproduces the online segmentation logic line for line (modulo finding 7’s base-class assumptions).
