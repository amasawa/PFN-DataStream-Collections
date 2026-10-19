# DRAFT (not registered): P5 (dtmoe tests), P2b (tests of the four CPU baselines) and P6 (TOT)

For expert review (Fable, then Sonnet) before anything is written or run.

## Facts (2026-10-20)
- **Stage 2 is one procedure for five tuned TS baselines.** It applies to dtmoe (P5) and to fsnet, onenet, adaptz,
  shifts (P2b). Amendment c fixes its four steps:
  1. selection on the registered grid (select_frozen.py: mean development accuracy over the 5 development streams;
     ties to the first in sorted order);
  2. if the best lies on a boundary of lr or n_steps, one full extension of every boundary axis;
  3. re-selection (--final; ties to the original grid first; the result is frozen even on a boundary);
  4. a commit of frozen_<m>_final.json, then tests: one run per Table 1 stream (92).

  The development grids run on the cluster: dtmoe_dev in P1 (H800, strict mode), ts_dev in P2 (CPU). Nothing of
  stage 2 can run before those return.
- **TOT (P6)**:
  - Code: the authors' code is in the NeurIPS supplement (LSTD-TOT only). The classification adaptation is registered
    in AMENDMENT_BASELINES_20261018 item 2:
    - the official LSTD-TOT net, mode "time", with the sizes of ETTh2 pred_len 1;
    - a softmax head on the posterior means;
    - loss = CE + MSE(x_rec, x) + other_loss; is_training = True in learning steps and False at prediction;
    - λ = zd_kl = zc_kl = sparsity weight ∈ {1e-6, 1e-5, 1e-4}.
  - Gates (amendment c item 5, CPU):
    - (a) the released code, unchanged, on ETTh2 pred_len 1, one seed, must land "within the paper's reported
      spread". If it takes more than 12 CPU-hours it stops, and TOT stays "pending";
    - (b) λ = 0 and the official λ must give different predictions on a development stream.

    A failed gate means "skipped". Neither gate has run: the only attempt (local GPU, 2026-10-18) produced corrupted
    numbers during the GPU fault period, and gate (a) was then moved to the CPU.
  - The adapter is not implemented (run_ts.py has no "tot").
  - Paper target, arXiv 2510.18281 Tables A14/A16: LSTD+TOT, ETTh2, pred_len 1, MSE mean 0.374, std 0.0031 over three
    seeds (main Table 2: 0.374).
  - Environment: the local totgpu venv (used by dtmoe) has numpy 2.4.6 with pandas 1.5.3, and pandas does not import
    (binary mismatch). dtmoe never imports pandas and runs; TOT's data loader needs it. TOT therefore needs its own
    venv, venv-tot: Python 3.11, torch 2.3.1 CPU, and the supplement's requirements numpy 1.23.5, pandas 1.5.3,
    einops 0.4.0, tqdm 4.64.1.

## Proposal
### Stage 2 for the five tuned baselines (P5 and P2b in one registration, now)
1. Register the procedure now, as code: make_tasks_stage2.py.
   - It reads only the committed selection files: frozen_cluster/frozen_<m>.json, then frozen_<m>_final.json.
   - It writes the extension tasks, and later the test tasks, mechanically. No choice is left to the coordinator.
   - The selection itself runs on the coordinator machine, on the returned outputs (~/h800, AMENDMENT_20261020 item
     5), with select_frozen.py unchanged and new output directories (MICE/results_paper/table1_fill/frozen_cluster/).
   - Each generated list is committed and pushed before it runs: extension list, then test list.
2. Devices:
   - CPU baselines: cluster CPU, the P2 node type, one thread.
   - dtmoe: H800 strict mode. Its cap (ACTIVATION item 2) applies already to the probe. If the probe is TOO SLOW,
     the dtmoe path goes to the user before any stage 2.
3. Tests: the 92 Table 1 streams. Data as for the other Table 1 baselines: MICE/data for 83 streams, the confirmation
   data for 9. Outputs go to {RUNS}/mice-table1-newbase/test_cluster/P (CPU) and test_h800/P (dtmoe).
4. Paper footnote: each method's update steps per batch, and whether the frozen choice sits on a boundary.

### P6, TOT
1. Build venv-tot (the supplement's requirements; torch 2.3.1 CPU wheel).
2. Gate (a) where?
   - Option L: run it now on the local CPU (only a check of the authors' code, which produces no MICE number), so
     that the adapter is written only if the gate passes. The cluster run of gate (a) in P6 is the binding one, and
     the local outcome is logged and never chosen over it.
   - Option C: cluster only, binding (as ACTIVATION P6).

   Proposal: L as feasibility, C binding. If the two disagree, the cluster result holds and the disagreement is
   reported.
3. Gate (a) pass criterion. "Within the paper's reported spread" is ambiguous. Proposal: |MSE − 0.374| ≤ 2 × 0.0031
   (= 0.0062). One seed lands within ±1 std only about 68 % of the time even under perfect reproduction; 2 std is
   about 95 %. Alternative: ±1 std (literal); or the plan's 10 % fallback (|ΔMSE| ≤ 0.0374), meant only for when no
   spread is reported.
4. Implement TOTCls in run_ts.py (amendment item 2).
   - enc_in = the stream's feature count; x_dim = 3 is a latent size (exp_LSTD_TOT.py: x_emb = Linear(320, x_dim)), as registered.
   - Then: MiMo Pro high audit, gate (b) on a development stream (CPU), and a one-batch timing (vmap jacfwd
     sparsity, depth 9, n_steps 5). If one batch takes so long that the grid exceeds X CPU-h, the dev grid is
     registered with that cost and goes to the user.
5. Development grid: lr × n_steps × L × λ = 36 configurations × 5 streams = 180 CPU tasks (cluster CPU). Then stage 2
   as above (make_tasks_stage2.py with method tot).
6. Order: venv-tot and gate (a) (local, background) → adapter, audit, gate (b), timing → register P6 (gate (a)
   cluster task + dev grid) → push → cluster.

## Questions for the expert
Q1 Is registering stage 2 as a committed procedure (generator reading committed selection files) enough, or must each
   generated list get its own reviewed registration?
Q2 Gate (a): local feasibility run plus binding cluster run (L + C), or cluster only?
Q3 Gate (a) criterion: ±2 std, ±1 std, or the 10 % fallback?
Q4 Anything else in P5/P2b/P6 that would make results unreportable or unfair (at most two points).
