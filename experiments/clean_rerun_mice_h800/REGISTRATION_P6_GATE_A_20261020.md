# P6 (TOT), first part: gate (a), its pass rule and the cost limits of P6 (registered 2026-10-20, before any gate run;
# amended the same day, see the end)

Binding:
- AMENDMENT_BASELINES_20261018 item 2: TOT adaptation and gates;
- AMENDMENT_BASELINES_20261018c item 5: CPU; 12 CPU-hours; "pending" and "skipped";
- ACTIVATION_20261019 P6.

Records: PLAN_P5_P6_draft.md; Fable MICE/logs/table1_fill/fable_p5p6_a.md; Sonnet sonnet_p5p6.md.

## Gate (a)
- **Run.** tot_gate_a.sh runs the released code (NeurIPS supplement, LSTD-TOT, unchanged) on ETTh2 with pred_len 1,
  with the configuration line of LSTD_TOT_config.py (d["ETTh2"][1]: mode time, x_dim 3, depth 9, hidden_dim 512, …).
  - Settings: seed 2023, the default of run_LSTD_TOT.py.
  - [Superseded by the amendment below: one H800, CUDA visible.] CPU (CUDA_VISIBLE_DEVICES empty, so main.py sets
    use_gpu False), OMP / MKL / OpenBLAS 1 thread, WANDB_MODE disabled.
  - The code runs from a copy.
  - Environment: env_lock/tot.txt (venv-tot: Python 3.11.17; the supplement's requirements torch 2.3.1 ([superseded:]
    CPU wheel; amended: the cu121 wheel),
    numpy 1.23.5, pandas 1.5.3, einops 0.4.0, tqdm 4.64.1; plus its unpinned imports scipy, scikit-learn, matplotlib,
    numexpr, wandb).
- **Measure.** The final online MSE that main.py prints (`mse:` line; cumulative average over the online test, the
  paper's metric).
- **Target.** LSTD+TOT, ETTh2, horizon 1: mean 0.374 over three seeds, sd 0.0031. Source: arXiv 2510.18281v1,
  Table A14 (p. 37) and Table A16 (p. 38); Table 2 (p. 8) gives 0.374. PDF sha256 af389a0d…7bfa.
  - The paper does not state the mode. The released config, whose ETTh2 horizon-1 line is mode time, is taken as
    the paper's configuration. A failed gate may therefore come from a configuration mismatch as well as from the
    code or the environment; it is reported with that caveat.
- **Rule.** "Within the paper's reported spread" is fixed now as |MSE − 0.374| ≤ 2 × 0.0031 = 0.0062.
  - Pass if within that.
  - Otherwise TOT is "skipped (outside 2 sd)".
  - If the run does not finish, TOT is "skipped (the released code did not finish)".
  - If the 12 h wall-clock limit of the single one-thread process (= 12 CPU-hours, amendment c item 5) is reached,
    TOT is "pending".
  - There is one seed and no buffer band. A different number of seeds would be a change of the amendment, made by
    the user before any run.
  - Fable's estimate: an exact reproduction passes ±2 sd with probability about 0.92 (one seed against a three-seed
    mean).
- **Where.** [Superseded by the amendment below: one H800 run on the cluster only.]
  - First on the local CPU, as a feasibility check: it produces no MICE number, and it decides only whether the
    adapter work goes on now.
  - Then on the cluster CPU (P2 node type): this run is binding.
  - Both use env_lock/tot.txt and tot_gate_a.sh, once each. If they disagree, the cluster verdict holds and the
    disagreement is reported. Neither is repeated. (Superseded by the amendment below: one H800 run only.)

## Environments of the later TOT steps (fixed now)
- **Gate (a):** venv-tot. It certifies the authors' code in the authors' versions.
- **Adapter, gate (b), timing, development grid, extension and tests:** the P2 CPU-baseline environment (tsbase,
  env_lock/tsbase.txt) plus einops 0.4.0, the same as fsnet, onenet, adaptz and shifts. If the released modules do
  not import there, this is recorded, and the environment question goes to the coordinator before gate (b).

## Cost limits (fixed now, before any timing)
- **TOT development grid.** The one-batch timing in the production environment, × the batches of the 180 grid tasks,
  gives a projected cost. If it exceeds 1500 CPU-hours, the grid is not registered; the cost goes to the user.
- **Stage 2 lists** (extension and tests of every tuned baseline, including dtmoe and TOT). A list is generated in
  full and never shortened. If its projected cost exceeds 3000 CPU-hours (CPU) or 300 H800-hours (dtmoe), it goes to
  the user before it runs.

## Amendment, 2026-10-20 (committed and pushed before the binding run)
- **What happened.** The local feasibility run (commit d3b0ab1, 10:2x) stopped after 3 s and produced no MSE. main.py
  calls init_dl_program(args.gpu, ...). args.gpu is an int (argparse type = int, default 0), so torch.device(0) is
  cuda:0, and the code asserts torch.cuda.is_available() (main.py lines 57-65). The unchanged code therefore requires
  a CUDA device. The statement above, "CUDA_VISIBLE_DEVICES empty, so main.py sets use_gpu False", was wrong: use_gpu
  is set, but init_dl_program still asserts CUDA.
- **Expert.** Fable (MICE/logs/table1_fill/fable_tot_device_a.md): option A, gate (a) on one H800. It rejected B (keep
  the CPU, so TOT skipped for a fault of our own registration) and C (a device patch, so the code is no longer
  unchanged).
- **User decision** (2026-10-20, verbatim, with the options). Question: the released code requires CUDA; TOT was moved
  to the CPU on 2026-10-18 because the local GPU corrupted results silently; the H800 exists now. Options:
  - "gate (a) 用 H800 (Recommended)";
  - "保持 CPU，TOT 跳过";
  - "最小补丁后在 CPU 跑".

  Answer: "gate (a) 用 H800 (Recommended)".
- **New rule for gate (a).**
  - It runs once, on the cluster: one H800, exclusive (task p6_gate_a of tasks_p6.jsonl, placeholder {PYTOTA} = the
    venv-tot python). The code is unchanged. It uses its own deterministic settings: init_dl_program sets
    CUBLAS_WORKSPACE_CONFIG = ':16:8' before use_deterministic_algorithms(True) (main.py lines 52-55).
  - Settings: one seed, 1 CPU thread, a 12 h wall-clock limit (the reaching of which means "pending").
  - Pass rule: |MSE − 0.374| ≤ 0.0062, unchanged, with no buffer band.
  - The local feasibility step is cancelled: the local GPU is not used (silent-corruption faults), so the cluster run
    is the only one. This partly reverses amendment c item 5 (the 2026-10-18 decision to move TOT to the CPU), for
    gate (a) only.
- **Environment.** venv-tot is rebuilt with the CUDA wheels torch 2.3.1+cu121 / torchvision 0.18.1+cu121 (sm_90
  included). The other pins are unchanged (env_lock/tot.txt).
- **Unchanged.** Every later TOT step (adapter, gate (b), timing, development grid, stage 2) stays on the CPU in the
  P2 environment. Gate (b) compares λ = 0 with the official λ within the adapter, on the CPU. It never compares with
  gate (a), so the device difference does not enter it.

## P6 development grid (registered 2026-10-20 with AMENDMENT_20261020b, before any TOT run)
- **Adapter.** experiments/mice_table1_fill_20261018/run_ts_tot.py adds METHODS["tot"] to run_ts.py without
  changing it, following AMENDMENT_BASELINES_20261018 item 2:
  - the official net (mode time) with the ETTh2 horizon-1 sizes; activation gelu and lags 1 are main.py's
    defaults, since the configuration line does not set them;
  - the head on z_pred, read at the input of net.regressor;
  - is_training True in learning and False in prediction;
  - loss CE + MSE(x_rec, x) + other_loss;
  - the official AdamW with default hyperparameters (the other run_ts methods use Adam), applied to the net and the
    head;
  - backward, step, store_grad, zero_grad, in that order;
  - λ = zd_kl = zc_kl = sparsity weight.

  This is the registered adaptation, not the authors' online update verbatim, which uses is_training = False and no
  identification terms. The paper describes it as such.
- **Audit.** MiMo Pro high (MICE/logs/table1_fill/p6_tot_mimo.md): no P0 or P1. The P2 findings were resolved as
  logged.
- **Local checks** (no accuracy read):
  - two runs bit-identical;
  - λ = 0 and λ = 1e-5 give different predictions;
  - the hook captures the regressor's first input.
- **Tasks.** tasks_p6.jsonl, made by make_tasks_p6.py:
  - p6_gate_a (1 task);
  - p6_tot_check (1 task);
  - tot_dev (180 tasks): lr {1e-4, 1e-3, 1e-2} × n_steps {1, 5} × L {16, 32} × λ {1e-6, 1e-5, 1e-4} × the 5
    development streams, on the A800 in deterministic mode, venv-tot.
- **Order and gates.** AMENDMENT_20261020b item 3.
- **Selection, extension and tests.** REGISTRATION_STAGE2_20261020, with method tot (A800, dev_a800 / test_a800).
