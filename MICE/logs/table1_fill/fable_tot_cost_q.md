# Question to Fable: TOT development grid exceeds the registered cost limit (one decision)
Registered (REGISTRATION_P6_GATE_A_20261020.md, "Cost limits"): if the projected TOT dev grid exceeds 1500 CPU-hours,
the grid is not registered and the cost goes to the user. Stage 2 lists over 3000 CPU-h also go to the user.
Measured (local WSL CPU, one thread, tsbase env, run_ts_tot.py; MiMo audit done, no P0/P1), seconds per batch:
  elec2 (d=8, 453 batches): L16 s1 1.1, L32 s1 3.2, L16 s5 4.3, L32 s5 14.1
  INSECTS (d=33; 4 streams, 2138 batches): L16 s1 25, L32 s1 57, L16 s5 113, L32 s5 ~250 (extrapolated; run ongoing)
  The vmap(jacfwd(regressor)) sparsity term dominates (lambda 0: 10x faster); cost grows roughly with d^2.
Projection: dev grid (lr 3 x steps 2 x L 2 x lambda 3 x 5 streams = 180 tasks) ~ 2400 CPU-h; longest task ~55 h.
Tests (92 streams, frozen config) include covertype (d=54, 1500 batches): one task could take 3-12 days at L32 s5,
beyond the 7-day job limit. Cluster: account limit 8 A800 (not H800) + 500 CPU cores total; A800 nodes 56 cores.
GPU budget elsewhere: ~600-1200 GPU-h for P1/P3/P4/P5.
Options for the user:
 A. Run the dev grid on the cluster CPU as is (2400 CPU-h ~ 2.5 days wall on ~180 cores); tests later, with the
    7-day limit risk handled by the stage-2 cost rule.
 B. Move the TOT dev grid and tests to A800 GPUs (deterministic mode; qualify first); jacfwd on GPU likely >10x faster;
    competes with the GPU budget.
 C. Do not run TOT; report "not run, for its cost" (gate (a) still runs).
Recommend one. Format: Decision / Supporting evidence / Alternatives / Key risks / Confidence / Requires user
approval. At most 12 lines, Chinese.
