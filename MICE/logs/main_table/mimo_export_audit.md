[0m
> auditor · mimo-v2.6-pro
[0m
Audit complete. All material was provided in the prompt (script + `compute_metrics`, `simulate2`, `load_acc` excerpts + `summary_head.csv`); no project files were modified. Findings below target numbers that would be wrong in `main_table/` outputs.

## Findings

### F1 — Duplicate streams are double-counted in every aggregate; stream-name index breaks worst-vs-FIFO
- **Severity**: P1 · **Status**: Confirmed issue (mechanism; manifestation depends on which names repeat)
- **Location**: `export_main_table.py:53-54` (melt), `:66` (merge), `:75-76` (pivot), `:78-86` (summary + worst_vs_fifo), `:88-90` (coverage)
- **Evidence**: Nothing in the script deduplicates. `make_paper_tables.collect`/`compute_metrics.one` remap fam-dir streams without `_s`+1–2 chars to group `realD` (excerpts), so `all.csv`/`metrics.csv` can carry the same `(group, stream)` twice, and the stated data shape (a stream in two groups) adds cross-group repeats. Consequences: (a) `acc.merge(m, on=["group","stream","method"])` cartesian-multiplies when either side has duplicate keys (2 left × 2 right = 4 rows); (b) summary means use `v = d[k].dropna(); 100*v.mean()` over rows while `streams=d.stream.nunique()` — duplicates get double weight and `n_acc` ≠ `streams`; (c) `pivot_table` silently averages duplicates; (d) `coverage` compares row counts `d[k].notna().sum()` against unique-stream `n[st]`, so gaps can be hidden (`have` inflated); (e) `f = …fifo….set_index("stream")` and `d.set_index("stream")` use stream alone as the key — for a repeated name the subtraction either raises `cannot reindex on an axis with duplicate labels` (different row patterns) or silently pairs a stream with FIFO of the other group.
- **Why it matters**: Per-set means, `n_*` counts, per-set pivots and `worst_vs_fifo` in the paper's main table can be wrong for every duplicated stream.
- **Correction**: Key everything by `(group, stream)` (merge FIFO via `merge on ["group","stream"]`, pivot keyed by both as now, assert `long` unique on `(group,stream,method)` after an explicit resolution of duplicates); compute `worst_vs_fifo` on that key; make `have` count unique `(group,stream)` and assert `n_acc == streams` in `summary.csv`.

### F2 — mice_cp cache lookup is by stream name only → a name collision attributes another stream's cache
- **Severity**: P1 · **Status**: Suspected issue (needs name-overlap check)
- **Location**: `export_main_table.py:29-41`, especially `:32`; input at `:57` (`a[a.group != "fam"]` includes `grid20`)
- **Evidence**: `f = next(f"{d}/{s}__micecp1000_500.pkl" for d in CP if exists)` ignores `g`. `CP` holds only `mice-r14-exist` and `mice-main-cp-grid10`. A `grid20` (or second-group) stream whose name equals a real/grid10 stream name will be replayed from the *other* stream's expert cache, and `cp_rows` will emit those metrics under its own `(group, stream)`. The same applies to two groups sharing a name: the same pkl is replayed twice under two groups (feeds F1), and the first matching dir wins if both dirs contain the name.
- **Why it matters**: Wrong `mice_cp` accuracy/F1/… rows in the main table, undetectable downstream (the r14 check only covers streams that exist in the r14 tables).
- **Correction**: Give each group its own cache directory (or a `(group, stream) → path` map), and `assert` that the found file's directory matches the stream's group; at minimum record `source_file` per row and reject name reuse across groups.

### F3 — Check of the replay merges on `stream` alone → row inflation and wrong pairing against the r14 tables
- **Severity**: P2 · **Status**: Confirmed issue (mechanism given duplicated names)
- **Location**: `export_main_table.py:39` (chk rows lack `group`), `:58-62`
- **Evidence**: `chk` gets one row per `(g, s)` input row with only `stream` as identity; `r14 = concat(r14_real_streams, r14_aligned_streams)` keeps both tables' rows for a shared name; `chk.merge(r14, on="stream", how="left")` then produces a cartesian product per duplicated name, pairing each replay with **both** tables' `cp`. If the two tables disagree for one name, `assert chk["diff"].max() < 1e-9` fails spuriously (crash) or, if equal, `check_cp_replay.csv` and the printed "over N streams" overcount. Also `chk` has no `group`, so duplicates are indistinguishable.
- **Why it matters**: The only integrity check of the replayed `mice_cp` numbers can be mispaired or can block the export; the check file is misleading evidence.
- **Correction**: Put `group` in `chk`, deduplicate `r14` per table with a `source` column (or assert stream names are disjoint across the two r14 files), and assert `chk.stream` is unique before merging.

### F4 — Methods with no surviving rows vanish silently (docstring promises coverage lists them)
- **Severity**: P2 · **Status**: Confirmed issue
- **Location**: `export_main_table.py:53-54` (`dropna(subset=["acc"])`), `:89-90` (coverage built from `long.groupby`)
- **Evidence**: A method with all-NaN `all.csv` accuracy and no `metrics.csv` entry (e.g., a trained learner with no runs on a set) is erased by the melt drop and never appears in `long`, so `groupby(["set","method"])` has no such group: absent from `summary.csv` **and** from `coverage.csv`. Same for `mice_cp` on the generator set (`cp_rows` skips `fam` at `:57`). `coverage` only lists metrics *within* methods that already have ≥1 row.
- **Why it matters**: The main table's missing entries are undocumented; a reader (or the paper's completeness claim) cannot distinguish "not run" from "not applicable".
- **Correction**: Build coverage over the full expected `set × method` grid (the method list is known: `["mice","mice10","fast","fifo","ltm","ddm","winens","oracle"] + TRAINED + ["mice_cp"]`) against `n[st]`, emitting rows even when `have == 0`.

### F5 — Assertions fail spuriously on empty selections
- **Severity**: P2 · **Status**: Suspected issue
- **Location**: `export_main_table.py:69-70`, similarly `:60`
- **Evidence**: `dd[both & ~rerun].max() < 1e-9 and dd[both & rerun].max() < 1e-3` — `.max()` of an empty selection is `NaN`, and `NaN < tol` is `False`. If `metrics.csv` contains no `ddm`/`ltm` rows at all (docstring: they are added only when `run_probs.py` stored probabilities), `both & rerun` is empty and the assert aborts although nothing disagrees; symmetrically for `both & ~rerun`. Same pattern for `chk["diff"].max()` when `chk` is empty (no caches found).
- **Why it matters**: The export crashes on valid configurations; the obvious workaround (weakening the assert) would weaken a real check.
- **Correction**: `dd[sel].le(tol).all()` (vacuously true on empty) or guard with `if sel.any()`.

### F6 — `ddm`/`ltm` rows mix metrics from two different runs
- **Severity**: P2 · **Status**: Suspected issue (documented trade-off, but it does put non-coherent numbers in one table row)
- **Location**: `export_main_table.py:66-71`; comment at `:68`
- **Evidence**: `acc` is filled from `all.csv` first, `f1/auc/ece/brier/nll` come from `metrics.csv` (the `run_probs.py` replay); the assert allows the two accuracies to differ by up to `1e-3` (0.1 points; comment claims ≤0.05 points). The row's accuracy is therefore not the accuracy of the predictions behind its F1/AUC/calibration numbers.
- **Why it matters**: A main-table row is not attributable to a single run; per-method comparisons across columns are not strictly apples-to-apples.
- **Correction**: For `ddm`/`ltm`, take **all** metrics from the `metrics.csv` run (i.e., prefer `acc_m` for `rerun` rows), or split the row/footnote the provenance.

**Units** (explicitly checked): `summary.csv` is percent (`100 * v.mean()`), per-stream outputs (`streams_long.csv`, `acc_*.csv`) are fractions, `worst_vs_fifo = 100 * dd.min()` is percentage points — internally consistent with the docstring. One caveat: `nll` is also multiplied by 100 under the label "values in percent" (`:81-82`); log-loss has no percentage meaning — fine if the paper labels the column `×100`, wrong if it says `%`.

## Points that can only be confirmed by running code
1. Which stream names occur in more than one row of `all.csv` (same or different groups), and whether those groups map to the same set — determines whether F1 double-weights means or crashes `worst_vs_fifo`, and whether `acc.merge(m)` cartesian-multiplies (compare `len(long)` vs `long.drop_duplicates(["group","stream","method"]).len()`).
2. Whether any name exists in both `r14_real_streams.csv` and `r14_aligned_streams.csv`, and whether their `cp` values agree — determines whether F3's assert passes, fails, or silently double-counts; also confirms `cp` is on the percent scale of `100 * acc` (the `1e-9` assert assumes bit-level agreement between `metrics(P, yy)["acc"]` and the r14 aggregation).
3. Whether stream names collide across the cache groups (grid20/grid10/real/fam-dir realD copies) so the name-only lookup at `:32` finds a pkl belonging to a different stream (F2). Check: for each `(g,s)` row, whether `dirname(found_pkl)` matches the stream's group's expected run directory.
4. Whether `metrics.csv` contains `ddm`/`ltm` rows at all (F5), and whether the `_file`-suffixed methods filtered at `:56` are baselines that belong in the main table (missing information — deliberate or accidental drop).
5. Whether any fam-dir stream name fails the `_s`+1–2 trailing chars test in the `make_paper_tables`/`compute_metrics` remap (e.g. bare `_s` or `_s100`): such a generator stream would be grouped `realD` and land in the "real" set of the main table.
6. Whether the grid20 `.npz` accuracy arrays can be all-NaN (`np.nanmean` then writes `NaN` with only a warning) and whether `all.csv` already has non-NaN grid20 trained values (the `assert pd.isna` at `:52` would then abort).
