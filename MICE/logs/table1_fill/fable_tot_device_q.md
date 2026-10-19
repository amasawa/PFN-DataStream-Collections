# Question to Fable: TOT gate (a) cannot run on the CPU (one decision)
Facts:
- REGISTRATION_P6_GATE_A_20261020.md (experiments/clean_rerun_mice_h800/, pushed d3b0ab1) registers gate (a) as the
  released LSTD-TOT code, UNCHANGED, on the CPU (amendment c item 5 moved TOT to the CPU on 2026-10-18 because the local
  GPU had silent-corruption faults; the H800 cluster now exists). Local run = feasibility only; cluster run = binding.
- The local feasibility run (10:3x) stopped after 3 s: main.py calls init_dl_program(args.gpu, ...) with args.gpu an
  int (argparse type=int, default 0); torch.device(0) is cuda:0, and the code asserts torch.cuda.is_available()
  (main.py lines 57-65). With CUDA hidden the released code cannot run; `--gpu cpu` is rejected by argparse. So the
  unchanged code requires a CUDA device. No MSE was produced (no score seen).
- Literal reading of the registration: "skipped (the released code did not finish)". The binding cluster run has not
  happened.
Options:
 A. Gate (a) runs the unchanged code on one H800 (cluster GPU, exclusive). Everything after it (adapter, gate b,
    timing, development grid, stage 2) stays on the CPU, as registered. Amendment before the binding run.
 B. Keep the CPU: TOT "skipped (the released code requires CUDA)".
 C. Minimal device patch so the code runs on the CPU (no longer "unchanged").
Decide. Format: Decision / Supporting evidence / Alternatives / Key risks / Confidence / Requires user approval. At most
12 lines. Answer in Chinese.
