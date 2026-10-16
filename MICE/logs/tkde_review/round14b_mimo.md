## Findings

**F1 — A2 does not run the capacity-matched snapshot (snap kmax 12)**
- Severity: P1
- Finding status: Confirmed issue
- Location: `bench_cp.py:95-97` (`plan`, else-branch), echoed in the docstring `bench_cp.py:11-12`; consequence in `analyse_14b.py:119-133` (`a2`)
- Evidence: PLAN_14B.md:33 registers "micecp, archcp kmax 12, snap k\* and snap kmax 12; 3 repetitions" for A2. `plan(root, "a2")` returns only three policies: `("micecp1000_500", 0, 3), ("archcp1000_500", 12, 3), ("snap1000_500", ks["snap"], 3)`. Since rule B restricts k\* to {2, 4}, snap kmax 12 is never timed on any A2 stream. (Round 13's driver, from which this was copied, had `[(m, 12, 1) ...]` in a2; the copy dropped it.)
- Why it matters: rule E (PLAN_14B.md:60) requires the capacity-matched snapshot's cost to be stated "where measured (A1 prefixes, A2 streams), with the measured ratio of s/batch to MICE on those streams". With no A2 measurement, that ratio cannot be produced for the A2 streams, and the registered A2 design is not what runs. `a2()` in the analysis can only compare snap k\* to MICE.
- Recommended correction: add `("snap1000_500", 12, 3)` to the a2 policy list (3 repetitions, as registered), and have `a2()` also report `snap12` vs MICE mean s/batch per stream; or, if 3 repetitions were a registration error, amend PLAN_14B.md before running.

**F2 — Infeasible / exhausted configurations are not persisted in the analysis outputs**
- Severity: P2
- Finding status: Confirmed issue (whether they vanish from the paper is downstream)
- Location: `analyse_14b.py:46-49` (`runs` returns `bad`), `analyse_14b.py:84`, `analyse_14b.py:123` (print only); CSVs written at `analyse_14b.py:98-100`, `131-133` contain successful runs only
- Evidence: rule E (PLAN_14B.md:61) states "All configurations are reported, including infeasible ones." `bad` is printed to stdout and survives only in the raw `<stage>.jsonl` in the bench root; `r14b_a1_*.csv` / `r14b_a2_*.csv` contain no infeasible row.
- Why it matters: if the paper tables are assembled from `results_paper/r14b_*.csv`, infeasible configurations drop out of the reported set, violating the registered reporting rule; the stdout print is easy to lose.
- Recommended correction: write `bad` (stream, policy, kmax, rep, reason) to `r14b_*_infeasible.csv`, or add a status column to the policy/stream tables.

**F3 — k\* fallback label conflates "over budget" with "not measured"**
- Severity: P2
- Finding status: Suspected issue (edge case, only on failure/infeasibility)
- Location: `analyse_14b.py:86-93`
- Evidence: rule B (PLAN_14B.md:44-45): "the largest whose amortised mean s/batch <= micecp's on all three prefixes; if none, k\* = 2 labelled 'over-budget fallback'". The code drops a candidate entirely if any of its runs is in `bad` or a stream is missing (`len(x) == 3` and the `bad` filter), so `under` can be empty because nothing was measured; the label written to `kstar.json` is still `"over-budget fallback"`.
- Why it matters: `kstar.json` is the pre-registered record of how k\* was fixed; a wrong status string misstates the selection reason in the paper's budget line.
- Recommended correction: if no candidate has complete measurements, write status `"no complete measurement; k*=2 by rule B fallback"` and keep `"over-budget fallback"` for the case where measured means exceed MICE's.

**F4 — Primary (k\*) vs sensitivity candidate is not marked in the analysis outputs**
- Severity: P2
- Finding status: Suspected issue
- Location: `analyse_14b.py:157-183` (`c` writes one table with `control` in {snap2, snap4, snap12}, no role column); only the two prints select k\* and snap12
- Evidence: PLAN_14B.md:67-68: "Only the k\* and kmax 12 outputs enter the analysis; the other candidate is reported as a sensitivity row." `r14b_c_groups.csv` gives all three candidates identical treatment; nothing in the file records which rows are primary (k\* from `kstar.json`, snap12) and which is the sensitivity row.
- Why it matters: downstream writing can present the non-selected candidate as the primary comparison without any signal in the artifact; the distinction is pre-registered (k\* fixed before part-C accuracy was read) and should travel with the table.
- Recommended correction: add a `role` column (`primary_kstar`, `capacity_matched`, `sensitivity`) derived from `kstar.json` when writing `r14b_c_groups.csv` and `r14b_c_streams.csv`.

**F5 — Pairing of the existing MICE runs and the part-C data staging is not verifiable from these files**
- Severity: P2 (validity of the comparison depends on it)
- Finding status: Missing information
- Location: `analyse_14b.py:144-148` (`mdir` = `CONF/P` for confirm, `R14/P` for shifted and misaligned; `ACC/P_k{k}` for snapshots); `run_task.py:14` (`run.DATA = f"{root}/data"`)
- Evidence: `R14` resolves to `~/pfn-runs/mice-r14-exist` and `CONF` to `~/pfn-runs/mice-r14-confirm` (analyse_test excerpt). The reviewed files do not show that `mice-r14-exist/P` holds `off_*__micecp1000_500.pkl` and `mis_*__micecp1000_500.pkl` from the registered round-14 code (TRIM=0, same constants), that `mice-r14-confirm/P` holds the 72 `c_*` runs, or that the task root used by `run_task.py` has `data/` staged with all 92 streams copied from the same sources bench_cp uses (`mice-r14-confirm/data` for `c_*`, `mice-tkde-control-20261009/data` for `off_*`/`mis_*`).
- Why it matters: PLAN_14B.md:49-50 requires the MICE side of Delta to be the existing round-14 runs ("same streams, same code"). Wrong directory contents would fail loudly at `pool()` open, but stale or differently-produced runs under the same filenames would silently change Delta.
- Recommended correction: before part C runs, list those directories and record file names, sizes and the producing commit/run id in the log; stage `ACC/data` from the same npz sources `bench_cp.py` uses (`SRC_C` for `c_*`, `SRC`/`CTRL` for `off_*`/`mis_*`).

## Scope items checked without issue
- Occupancy hook: one entry per batch for all three policies, statically. `MiceCP`/`ArchCP` resolve `step` to `CPSegments.step` (run_excerpt 167-195 does not call `super().step`), so only the `CPSegments.step` wrapper fires; `snap` is `PoolControl.step` → `MiceV1.step` (run_excerpt 92-94), so only the `MiceV1.step` wrapper fires. The child's `assert len(occ) == T - 1` (bench_cp.py:55) is a runtime backstop against double or missing entries.
- kmax patch: `run.PoolControl.__init__` patch reaches both `snap1000_500` and `ArchCP` (ArchCP's `super().__init__(tfm, M, "arch", **kw)` walks the MRO to `PoolControl.__init__`); `micecp` runs unpatched at the MICE default kmax 12, matching "archcp … kmax 12" being capacity-matched to MICE.
- k\* rule B quantities: `mean_s = wt.mean() + replay per batch` is the amortised mean s/batch; the largest of {2,4} under MICE on all three prefixes; `kstar.json` written once (assert not exists) from a1 timings only, and `a1acc`/`a2`/`c` all require it before reading accuracy; `c()` is the only reader of part-C outputs and loads `kstar.json` first.
- Statistics: confirm = hierarchical (`hier_lb`, keys `[c<nc>, s<seed>, o<k>]` parsed correctly from `c_<regime>_c<nc>_s<seed>_o<k>`) for all and per regime; shifted/misaligned = `boot_ci(..., 10)` (moving blocks of 10); Delta = MICE − snapshot; rule E flag `mean <= +0.1` at snap k\*; A1 streams, A2 streams, 301×100 prefixes, rotated policy order, quiet-GPU wait, 28 GB cap and the reported resource columns match the registration.

## Points that can only be confirmed by running code
1. The occupancy hook actually yields exactly T−1 entries per policy in a live run (the child asserts it; verify the first run of micecp, archcp and snap).
2. The kmax patch takes effect (occ.json expert counts never exceed K for snap k∈{2,4,12}, and archcp caps at 12).
3. That `pol.step`'s wall clock includes the GPU work (TFM `predict` returning host memory, synchronising) — the validity of the timed quantity under WSL2.
4. `gpu_busy()`'s quiet-GPU test under WSL2 (empty compute-apps listing; utilisation/memory are the primary signals) — whether runs are ever launched onto a busy GPU or wait spuriously.
5. Stability of the amortised second-level number (`reweight.simulate2` time / batch) across repetitions, since it is added as a constant to every batch of a run.

Or: no other verified issues within the reviewed scope.
end 12:32:45
