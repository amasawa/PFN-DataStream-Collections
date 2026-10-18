# Amendment to PLAN_BASELINES.md, 2026-10-18 (committed before any dev or test run of the methods it changes)

Decisions of the expert adviser (Fable 5.1), taken on the user's instructions of 2026-10-18 ("方案先让 Fable 审，再跑";
"dtmoe 让 fable 决定，继续跑"). Fable marked the tot items "requires user approval" because they change this
registration; they are executed on those instructions and listed for the user in the README.

1. **dtmoe compute** (MICE/logs/table1_fill/fable_dtmoe_decision.md): the registered grid and official sizes are kept.
   Development grid on the CPU (5 single-thread processes, limited by memory: 1.9 GB each); test streams on the GPU,
   alone, once it has run without faults for several hours, with per-stream checkpointing; otherwise on the CPU.
   Device recorded per stream; CPU and GPU results compared on one stream first.
2. **tot** (MICE/logs/table1_fill/fable_tot_decision.md): the authors' code exists in the NeurIPS supplementary material
   (Supplemental-Conference.zip, sha256 a20ff1547d17f43f363e7f84b24ba6c0d21639f3304d0c830195c27978afa8a2; LSTD-TOT
   only), so tot uses it instead of a reproduction on OneNet:
   - official net of exp/exp_LSTD_TOT.py, mode "time" (used for pred_len 1 on every dataset of LSTD_TOT_config.py),
     sizes of the ETTh2 pred_len-1 configuration (depth 9, hidden_dim 512, hidden_layers 1, tau 0.75, x_dim 3,
     L1_weight 1e-3, L2_weight 1e-3, lags 1, dropout 0), pred_len 1, enc_in = d;
   - softmax head on the latent representation (the posterior means feeding the forecaster), not on the 1-step
     forecast y (whose width is the feature count);
   - loss = cross-entropy + MSE(x_rec, x) + the official other_loss; learning steps with is_training = True (so the
     KL and Jacobian-sparsity identification terms act: there is no offline phase), prediction with is_training =
     False (posterior means), store_grad after each step;
   - mechanism parameter: one identification scale lambda = zd_kl_weight = zc_kl_weight = sparsity_weight in
     {1e-6, 1e-5 (official), 1e-4}; the rest of the grid as for the other methods;
   - gate (replaces the native-task gate): (a) the released code, unchanged, on ETTh2 pred_len 1, one seed, must land
     within the paper's reported spread for LSTD+TOT; (b) lambda = 0 and the official lambda must give different
     predictions on a development stream. If (a) or (b) fails, tot is reported as skipped with the reason.
