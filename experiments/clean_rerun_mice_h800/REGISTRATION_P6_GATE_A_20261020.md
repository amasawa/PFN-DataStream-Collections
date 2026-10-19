# P6 (TOT), first part: gate (a), its pass rule and the cost limits of P6 (registered 2026-10-20, before any gate run)

Binding:
- AMENDMENT_BASELINES_20261018 item 2: TOT adaptation and gates;
- AMENDMENT_BASELINES_20261018c item 5: CPU; 12 CPU-hours; "pending" and "skipped";
- ACTIVATION_20261019 P6.

Records: PLAN_P5_P6_draft.md; Fable MICE/logs/table1_fill/fable_p5p6_a.md; Sonnet sonnet_p5p6.md.

## Gate (a)
- **Run.** tot_gate_a.sh runs the released code (NeurIPS supplement, LSTD-TOT, unchanged) on ETTh2 with pred_len 1,
  with the configuration line of LSTD_TOT_config.py (d["ETTh2"][1]: mode time, x_dim 3, depth 9, hidden_dim 512, …).
  - Settings: seed 2023, the default of run_LSTD_TOT.py.
  - CPU (CUDA_VISIBLE_DEVICES empty, so main.py sets use_gpu False), OMP / MKL / OpenBLAS 1 thread, WANDB_MODE
    disabled.
  - The code runs from a copy.
  - Environment: env_lock/tot.txt (venv-tot: Python 3.11.17; the supplement's requirements torch 2.3.1 (CPU wheel),
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
- **Where.**
  - First on the local CPU, as a feasibility check: it produces no MICE number, and it decides only whether the
    adapter work goes on now.
  - Then on the cluster CPU (P2 node type): this run is binding.
  - Both use env_lock/tot.txt and tot_gate_a.sh, once each. If they disagree, the cluster verdict holds and the
    disagreement is reported. Neither is repeated.

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
