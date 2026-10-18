# Amendment c to PLAN_BASELINES.md, 2026-10-18 (committed before any extension run, test run or TOT run it covers)

Expert decisions (Fable 5.1: MICE/logs/table1_fill/fable_continue.md, fable_extension.md, fable_handoff.md) reviewed by
Sonnet (sonnet_continue_review.md, sonnet_extension_review.md); user decisions of 2026-10-18 evening: full grid
extension (option A), a re-selected configuration is frozen even with n_steps 25, all GPU work to the H800 cluster.

1. **Development selection** (select_frozen.py; no test stream is read). On the registered grid (lr {1e-4, 1e-3,
   1e-2} x n_steps {1, 5} x L x mech, 5 development streams, mean over each stream's scored batches, then over the
   streams) the best of all four CPU baselines lies on a boundary: n_steps = 5 for shifts, fsnet, onenet; lr = 1e-4 and
   n_steps = 5 for adaptz (frozen/frozen_<method>.json in MICE/results_paper/table1_fill).
2. **Extension, once, full (user option A)**: the new value of each boundary axis crossed with every value of all the
   other axes. shifts, fsnet, onenet: n_steps 25 x lr {1e-4, 1e-3, 1e-2} x L x mech (18 configurations x 5 streams);
   adaptz: n_steps 25 x lr {1e-4, 1e-3, 1e-2} x L x mech and lr 1e-5 x n_steps {1, 5, 25} x L x mech (36 x 5),
   the corner lr 1e-5 x n_steps 25 included. 450 runs, about 255 CPU-h. CPU, single-thread processes, at most 12 at
   once (14:30-18:37 today 12 CPU processes ran next to one GPU process with no driver event).
3. **Re-selection** (select_frozen.py --final): over the original 36 and the added configurations, same streams and
   score; ties to the original grid first, then the added configurations, each in ascending (L, lr, n_steps, mech).
   The re-selected configuration is frozen even if it lies on a boundary again (no second extension; reported in a
   footnote of Table 1), including n_steps 25, whose test runs cost about five times those of n_steps 5. Table 1
   states the number of update steps per batch of every method.
4. **Freezing before tests**: per method, one commit with frozen_<method>_final.json (scores of every configuration,
   the choice, the boundary status), before that method's first test stream. Tests: one run per test stream (92),
   then the grid and generator streams, CPU, within the 12-process limit.
5. **TOT on the CPU** (replaces the cuda note of AMENDMENT_BASELINES_20261018.md item 2; gates unchanged): gate (a)
   runs the released code unchanged on ETTh2 pred_len 1 on the CPU; gate (b) (lambda = 0 vs the official lambda give
   different predictions on a development stream) runs on the CPU after the adapter is implemented and audited (MiMo),
   before the tot development grid; development grid and tests on the CPU, never mixed with another device. If gate (a)
   exceeds 12 CPU-hours, it is stopped and tot stays "pending" (not skipped); a failed gate means "skipped" as
   registered.
6. **GPU work moves to the H800** (experiments/clean_rerun_mice_h800): Drift-Resilient TabPFN (92 streams) and the
   dtmoe development grid (strict deterministic mode; gpu_verify AMENDMENT_20261018b) run there and not on the local
   GPU; dtmoe test tasks are added there after its grid is frozen. This supersedes the local Drift-Resilient TabPFN
   run of tonight's plan (never started; no local output).
7. **Timing and peak memory** (PLAN_BASELINES "Execution"): measured after the test runs, for the CPU methods on the
   local CPU and for the GPU methods on the H800, on the three real prefixes of the MICE resource benchmark.
8. **Readout flags** (export_table1_fill.py, coverage.csv, README): every cell carries its provenance: CPU; GPU H800;
   or GPU local with "unverified" (mice_cp generator 30/30 computed during the pre-reboot fault storm; ddm/ltm generator
   probabilities, whose accuracy reproduced bit for bit but whose probabilities were not checked) until the user's
   verification or the H800 results replace them. Nothing is replaced in place.
