[0m
> auditor · mimo-v2.6-pro
[0m
I'll audit the three scripts against PLAN.md and the attached library excerpts. First, let me check the repository layout and the remaining library code so path and API claims can be verified.
[0m→ [0mRead .
[0m✱ [0mGlob "**/*"[90m in . · 11 matches[0m
The scratchpad holds only the attached materials. Let me re-check a few exact lines in `analyse.py` (env-hook unpacking, H1/H2 value strings) before writing findings.
[0m→ [0mRead analyse.py[90m [offset=26, limit=95][0m
I have enough to report: the H1–H5 implementation is otherwise faithful (thresholds, strictness, units, primary-only for H1/H3/H4/H5, bootstrap settings), and the two decision-rule deviations I found are in H1/H2 handling of the supplementary segments. Findings below.

## Findings

**1. H2 is decided on 11 segments including the two supplementary ones, not on the 9 primary segments**
- Severity: P1
- Finding status: Confirmed issue
- Location: `analyse.py:73-78` (loop fills `LB_fifo` for `STREAMS + SUPP`) and `analyse.py:94` (`met=all(v > -0.3 for v in LB_fifo.values())`), vs PLAN.md "## Hypotheses (primary segments; ...)" and "Supplementary (reported, in no hypothesis)"
- Evidence: PLAN.md registers H2 as "on every segment the lower bound ... > −0.3 points" under the header restricting hypotheses to primary segments, and states the two PokerHand segments are "reported, in no hypothesis". The code computes `LB_fifo` for `STREAMS + SUPP` (11 entries) and the `met` flag iterates `LB_fifo.values()`, i.e. `cc_poker_f`/`cc_poker_g` also have to clear −0.3. H1 (`for s in STREAMS`, line 88) and H3–H5 (on `a`, filtered to primary at line 84) correctly exclude them; H2 alone does not.
- Why it matters: the pre-registered decision rule is changed after registration. A supplementary segment below −0.3 would flip H2 to NOT MET and the paper would report a failure of a test the protocol never specified; the recorded rule string in `hypotheses.csv` says "every segment" without saying that supplementary segments were included.
- Recommended correction: decide on primary segments only — `met=all(LB_fifo[s] > -0.3 for s in STREAMS)` — and report the supplementary lower bounds separately (e.g. in the `value` string labelled as supplementary, or in the summary), consistent with H1/H3–H5.

**2. The H1 point estimate recorded in `hypotheses.csv` averages over 11 segments while its lower bound is over 9**
- Severity: P2
- Finding status: Confirmed issue
- Location: `analyse.py:91` (`np.mean([d.mean() for d in D_cp_mice.values()])`) vs `analyse.py:88` (`for s in STREAMS`)
- Evidence: `D_cp_mice` is filled for `STREAMS + SUPP` (lines 73–77), so `.values()` includes `cc_poker_f`/`cc_poker_g`. The bootstrap lower bound and the `met` flag correctly use only the 9 primary segments; only the reported mean mixes in the supplementary segments. The H2 `value` string (line 94) likewise lists the supplementary segments under a rule that says "every segment".
- Why it matters: `hypotheses.csv` is the permanent record of the pre-registered numbers. A mean over 11 segments next to a lower bound over 9 cannot be reconciled later from the table alone.
- Recommended correction: use `D_cp_mice[s] for s in STREAMS` in the H1 value string, and mark or omit the supplementary entries in the H2 value string.

**3. `../../MICE/...` root resolution is only correct if the scripts sit exactly two levels below the workspace root**
- Severity: P1
- Finding status: Suspected issue (repository layout not in the reviewed scope)
- Location: `analyse.py:21` and `analyse.py:32`, `run_task.py:10`, `make_streams.py:75` (`os.path.join(os.path.dirname(...), "..", "..", "MICE", "code"|"results_paper"|"data")`)
- Evidence: the joins resolve to `MICE/code`, `MICE/results_paper/...`, `MICE/data/external_cdd/poker.csv` only when the script directory is `<workspace>/<x>/<y>`. If these files are committed at `MICE/experiments/<dir>/` (where the previous pre-registration's scripts were committed, and which PLAN.md's "copy of `experiments/mice_r14/worker.sh`" suggests), the paths resolve to `MICE/MICE/code`, `MICE/MICE/results_paper/confirm_detected` and `MICE/MICE/data/...`. PLAN.md itself names the destinations as `MICE/results_paper/confirm_detected/`, which is the workspace-level path the code produces only under the two-level layout.
- Why it matters: if the layout is the deeper one, every worker dies at `import run` on the first task and `analyse.py` dies at `import reweight`; the failure is loud, but it costs a launch and, for `analyse.py`/`make_streams.py` poker, can create stray `MICE/MICE/...` directories. Nothing can be evaluated until it is fixed, and a fix after the first run would deviate from the committed evaluator.
- Recommended correction: before the first task, run `python -c "import run_task"` / `python analyse.py --help`-style smoke checks from the experiment directory, or anchor the root explicitly (walk up for `MICE/code/run.py`, or take the root from an environment variable) in all three scripts and re-commit.

## Points that can only be confirmed by running code (listed separately, no conclusion drawn)

1. **Batch-0 exclusion and key alignment**: whether `simulate2`'s cache dicts have keys exactly `1..T-1` (batch 0 absent), so the assert at `analyse.py:60` passes and batch 0 is not scored. If a cache ever contains `t=0`, evaluation aborts (loud); if an `npz` ever had a finite `acc[0]`, warm-up would silently enter the means.
2. **arf/srp output layout**: that `run_river.run` writes `acc` with the same length `T`, NaN at index 0 and finite values at `1..T-1`, so their keys match the replayed dicts at `analyse.py:58-60`. `run_river.py` was not attached.
3. **ddm/ltm probability alignment**: that each of `ddm1000`, `ltm1000_75` makes exactly one TFM call per scored batch in batch order, so `z["n_calls"] == T-1`, `len(z["P"]) == (T-1)*B`, and `y[B:B+len(z["P"])]` at `analyse.py:57` lines up with batches 1..T-1. Check on the first produced `__probs.npz`.
4. **FIFO identity across the two sources of numbers**: `acc["fifo"]` (hypotheses) comes from the `fifo1000` run file while `pred["fifo"]` (metrics.csv) is the `-1000` expert of the `micev1000_500` cache (`analyse.py:48`). Confirm once on one stream that the per-batch accuracy of the cached expert equals the run file; both are registered this way in PLAN.md, so a mismatch would be a data issue, not a code issue.
5. **Unattached established modules**: the full body of `noninferiority.block_means` (only the first lines were attached; `analyse.py:65` assumes it returns `(nboot,)` bootstrap means), the signature of `reweight.simulate` (`analyse.py:49` calls `simulate(c, 2.0, 0.5, subset=..., collect=...)`), `run_river.run`'s output keys, and that every cache entry contains expert key `-1000`. All are used exactly as the established modules document, but only excerpts were in scope.

No other verified issues within the reviewed scope: H1/H3/H4/H5 match PLAN.md on segments, thresholds (−0.2, −0.5, strict "above", `⌈2n/3⌉=6`), strictness and units (per-batch fractions ×100 against points thresholds); the moving-block bootstrap (block 20, 10 000 resamples, `default_rng(0)`, 5th percentile) matches PLAN.md and `noninferiority.py`; `run_task.py`'s `run_probs` patching (`run.TFM = RecTFM` before `run.run`), `DATA` assignment, and the skip/redo logic for the two-file ddm/ltm outputs match PLAN.md and `run_probs.py`; `make_streams.py` keeps labels and identity columns out of the features (Bitcoin Heist drops address/year/day, CIC drops `Label` and the duplicated `Fwd Header Length.1`), sorts Bitcoin Heist stably by (year, day), groups CIC labels as registered, and replaces ±inf/NaN with 0 with a float32 range assert; the label-informed CIC block choice is the pre-registered selection rule, not leakage into features.
