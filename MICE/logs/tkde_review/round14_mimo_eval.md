[0m
> auditor · mimo-v2.6-pro
[0m
Auditing the evaluator against the registration and the excerpts. Checking criteria logic, file pairing, purity row bookkeeping, and the logging identification.

## Findings

**F1 — Severity: P1 · Finding status: Confirmed issue**
- **Location:** `analyse_test.py:177` (`rng = np.random.default_rng(0)`), consumed by `report()`/`boot_ci` at `:210-212` before `hier_lb` at `:226`; `hier_lb` `:90-106`.
- **Evidence:** PLAN.md and the module docstring register the C1 hierarchical bound as "10 000 resamples, **seed 0**" (docstring :10-11). The code seeds one `default_rng(0)` at the start of `main` and draws the hierarchical resamples only after five `report()` calls have each consumed 10 000 moving-block resamples per pair. `hier_lb` therefore does not run its registered seed-0 stream; its draws depend on the order and size of all earlier bootstrap calls. The same applies to the block intervals ("seed 0", docstring :22-23).
- **Why it matters:** C1 is the primary criterion and one of its three gates is `lo > 0`. A borderline lower bound can differ between the implemented stream and a literal "seed 0" re-implementation, so the MET/NOT MET verdict is not reproducible from the written rule alone.
- **Recommended correction:** Before any test run, amend to `rng = np.random.default_rng(0)` *inside* `hier_lb` and `boot_ci` (or explicitly document "one `default_rng(0)` stream for the whole analysis, consumed in call order: group block intervals, then C1 bounds" in PLAN.md and the docstring). If the runs have already produced inspected outputs, record the choice as an amendment rather than silently re-seeding.

**F2 — Severity: P1 · Finding status: Suspected issue**
- **Location:** `run_py_logging.diff` `_close` (`MICE/code/run.py`, post-patch ~:282-296): `e = next(e for e in reversed(self.experts) if e.get("last") == t and np.array_equal(e["X"][-1], X[b - 1]))`.
- **Evidence:** The receiving expert is re-derived by feature-value equality after `_merge_or_add`. (i) `np.array_equal` defaults to `equal_nan=False`, so any NaN in the boundary row makes the predicate False for every expert → `StopIteration` aborts the run (with 10-batch checkpoints, partial artefacts). (ii) If two experts touched at the same `t` (the `while` loop can close several segments in one step) hold contexts ending in identical feature rows (possible with discretized/categorical features), `next(reversed(...))` may bind the wrong expert: `src` accumulates on the wrong context and the closes tuple records the wrong uid, corrupting `purity` and hence criterion P. (iii) The predicate assumes every `_merge_or_add` implementation sets `last=now`; an ArchCP override that omits `last` would always fail.
- **Why it matters:** P is a registered criterion; silent mis-attribution would change its value without any visible error, and a crash mid-experiment changes the whole result set.
- **Recommended correction:** Make `_merge_or_add` return the expert it touched (merge target or new expert) and use that reference in `_close`; or stamp the expert with the last row index at creation/merge and match on the index. Never match on feature values.

**F3 — Severity: P2 · Finding status: Confirmed issue**
- **Location:** `analyse_test.py:209` (`g8 = d3.loc[[g for g in GRID8 if g in d3.index]]`), criterion at `:237`; also `:224-225` (no per-regime size check).
- **Evidence:** PLAN.md C3 registers "the 8 streams with 30 or 100 centroids, seeds 20/21". `g8` silently drops any GRID8 member absent from `d3`, so C3 can be evaluated over fewer than 8 streams and still printed as "C3 ... MET". C1's per-regime slice is asserted only globally (`len(d1)==72`, :222), not as 24 per regime. (For C2, a missing file raises, so `d2` is forced to 8.)
- **Why it matters:** A criterion evaluated on a different stream set than registered is a silent change of the frozen protocol.
- **Recommended correction:** `assert set(GRID8) <= set(d3.index)` (or `assert len(g8) == 8`) and `assert len(x) == 24` inside the C1 regime loop.

**F4 — Severity: P2 · Finding status: Confirmed issue**
- **Location:** `analyse_test.py:109-111` (`resources`: `n = [len(st["P"]) for st in c["cache"]]`), used at `:154-158`, `:202`, `:233-234`.
- **Evidence:** `st["P"]` is keyed by uid plus fixed non-expert entries: `Mice.step` stores the online FIFO expert under `-1` (`run_mice_base_excerpt.py:62`), and `reweight.simulate2` reads `st["P"][default=-1000]` (`reweight_simulate2_excerpt.py:21`), so the cache dict must also carry a `-1000` entry. `len(st["P"])` therefore equals stored experts + 1 or 2.
- **Why it matters:** The C5 inequality `cp_experts.mean() <= archcp_experts.mean()` is unaffected (same constant both sides), but the reported "experts per batch" figures used in the paper/tables are inflated and do not equal the stored contexts (kmax 12).
- **Recommended correction:** Count only expert keys, e.g. `sum(u >= 0 for u in st["P"])`, or subtract the fixed keys; confirm the exact key set once at runtime and note it in the log.

**F5 — Severity: P2 · Finding status: Suspected issue**
- **Location:** `analyse_test.py:235` (`pshare = np.concatenate([[d1.cp_pure95_share[s]] * int(d1.cp_closes[s]) ...]).mean()`), per-stream share at `:152-153`.
- **Evidence:** PLAN.md P: "at least 90% of the **stored contexts**, evaluated at every segment close, hold >= 95% rows of one concept". The implementation weights each close equally, i.e. contexts that received many segments count many times; a per-uid unit would give each stored context one vote. The two differ whenever closes per context are unequal (they will be: merge-heavy contexts vs one-shot contexts).
- **Why it matters:** P decides whether the recall theorem is stated as holding or as conditional; the unit of evaluation must match the sentence in the paper.
- **Recommended correction:** Fix the unit explicitly in PLAN.md/paper ("share of (context, close) evaluations with >= 95% purity" as implemented) or recompute per uid (`groupby(uid)` of the close snapshots). Since `analyse_test.py` is itself part of the registration, settle this before the analysis runs and record it.

**F6 — Severity: P2 · Finding status: Confirmed issue (impact limited)**
- **Location:** `analyse_test.py:132-133` (`concept` from `{d_new}/../data/{s}.npz` if present, else `{CTRL}/data/{s}.npz`).
- **Evidence:** PLAN.md states the T2/misaligned data are the control runs' data (`~/pfn-runs/mice-tkde-control-20261009/data`). For `d_new = {R14}/P` the preferred path is `{R14}/data/`, which is not the registered source; a divergent copy there would silently replace the registered concept labels (affecting `segments`, `recurring`, `purity` columns for T2/T3-synthetic).
- **Why it matters:** Wrong concept labels would corrupt the reported detection/purity numbers of the existing-stream groups (no registered criterion is affected: P uses T1 only, whose data path is correct).
- **Recommended correction:** For the non-T1 groups pass the concept directory explicitly (`{CTRL}/data`), or assert `os.path.samefile` / equal arrays when the preferred copy exists.

**F7 — Severity: P2 · Finding status: Suspected issue**
- **Location:** `analyse_test.py:65-67` (`recurring`), used at `:147-149` (`*_rec` columns).
- **Evidence:** PLAN.md registers "first five batches of **recurring** blocks". `recurring` takes every segment start from the 4th segment on (`starts[K:]`, K=3), regardless of whether that concept has appeared before, so first occurrences of new concepts after block 3 are included.
- **Why it matters:** The `*_rec` columns (reported without criterion) would be mislabeled if any stream introduces a new concept after block 3; if the generators guarantee a pure 3-concept cycle, the behaviour coincides with the intended definition.
- **Recommended correction:** Filter to starts whose concept already occurred earlier (`concept[r] in concept[:r]`), or state the implemented definition ("first five batches of every block from the fourth on") in the paper.

**F8 — Severity: P2 · Finding status: Missing information**
- **Location:** `run_py_logging.diff` (`_close` is the only site that extends `e["src"]`); `run_mice_base_excerpt.py:48-50` (base `Mice.step` closes segments via `_merge_or_add` directly).
- **Evidence:** `src` is complete only if every segment that reaches a stored context passes through `_close`. If `CPSegments.step` ever falls through to the base-class closing loop (or any other `_merge_or_add` call site exists in `run.py`/`MiceV1`/ArchCP), those rows are absent from `src`, and `purity`'s `concat(...)[-M:]` would then not equal the context's held rows (`np.r_[...][-M:]`).
- **Why it matters:** Purity (criterion P) would be computed over the wrong row set without any error.
- **Recommended correction:** Grep `run.py` for `_merge_or_add` call sites and confirm that for `micecp1000_500`/`archcp1000_500` it is called only from `_close`; add a cheap invariant (e.g. assert `sum(b-a for a,b in e["src"]) >= len(e["X"])` style check) or compute purity from the actual `e["X"]` row indices if they can be recorded.

## Verified clean within scope
- (a) Thresholds and directions of C1–C5 match PLAN.md and the docstring exactly (`:223-247`): C1 per regime `>= +1.0`, `>= 18/24`, lower bound `> 0` with the registered nested resampling (seeds within centroid count, offsets within drawn seed; `hier_lb:93-105`); C2 `>= +2.0` on the 8 `off_`; C3 `>= -0.3` on the 8 grid streams; C4 `>= -0.1` vs FIFO and `>= -0.2` vs MICE on 29 streams (`assert len(d4)==29`); C5 calls/experts/`>= -0.3`; P reported as a rule with measured purity. Replay rule `simulate2(outer="brier", scale=0.5, temper=True)` matches the registration.
- (b) Method pairing is consistent (T1 all methods from `{TEST}/P`; T2 `micecp`/`archcp` from `{R14}/P` with earlier `micev`/`ddm`/`fifo` from the control directories; real streams take `micev` and `fifo` from the *same* earlier subdir), and every group asserts equal per-batch lengths across methods (`:146`, `:199`); `pool` covers batches 1..T-1 and `plain` returns `acc[1:]`, so batch axes align. The asserts make wrong-length pairing fail loudly rather than shift silently.
- (c) Given the `src` bookkeeping is complete (F8), `purity`'s `concat(arange(x,y) for x,y in src)[-M:]` reproduces `_merge_or_add`'s `np.r_[...][-self.M:]` exactly: chronological (a,b) ranges, truncation to the last 1000 rows on both merge and add, and the closes tuple snapshots `tuple(e["src"])` *after* the append, so historical records stay valid after later merges and LRU evictions. M=1000 matches `micecp1000_500`.
- (d) For `Mice._merge_or_add` as excerpted, identification is correct in both paths: merge and add both set `last=now=t` and leave `X[-1] == X[b-1]` (non-empty segments guaranteed by LMIN/`seg`), and the LRU pop cannot remove the just-added expert (`argmin(last)` removes a strictly older one, ties resolved to the earlier list entry). Residual risks are exactly F2/F8.

## Points that can only be confirmed by running code
1. `simulate2` covers exactly batches 1..T-1 (`pool` assert `:55`) and npz `acc` is indexed by batch 0..T-1 so `plain`'s `a[1:]` aligns (lengths asserted at `:146`, `:199`; misalignment would crash, not silently shift).
2. All expected artefacts exist: 72 T1 streams × {micecp, archcp, micev, ddm, fifo} (+ `.closes.pkl`), 8 `off_` + 12 aligned grid + 12 `mis_` streams with their older runs, 29 real streams × {micecp, micev, fifo} (+ archcp where present).
3. `d3` contains all 8 GRID8 names and 12 aligned streams (F3); `d1` has 24 streams per regime.
4. The cache key set of `st["P"]` (`-1`, `-1000`, uids) to fix `resources` (F4).
5. Features contain no NaNs and no duplicated boundary rows (F2); ArchCP's `_merge_or_add` sets `last` and cannot evict the new expert (F2).
6. `hier_lb`'s `tab` is balanced at 4 seeds × 3 offsets per centroid count per regime (its mean then equals the regime mean).
7. No duplicate stream names across the REAL directories (would double-count in `d4`/`s4`).
8. Streams with zero closes (empty `pur`) do not occur; otherwise `cp_purity_mean` becomes NaN and poisons `d1.cp_purity_mean.mean()` at `:243` (the `pshare` line is safe).

Reviewed scope: `analyse_test.py` (252 lines), `PLAN.md`, `run_py_logging.diff`, `reweight_simulate2_excerpt.py`, `run_mice_base_excerpt.py`. Not covered by evidence: the rest of `MICE/code/run.py` (`CPSegments.step` body, `run()`), `MiceV1`, the ArchCP policy, `tune_detector.py`, the stream manifests and result directories.
