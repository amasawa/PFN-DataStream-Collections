# MiMo Pro high 审计 run_ts_tot.py（TOT 适配器），10:58:13–11:11:08

## Findings

**F1 — Optimiser hyper-parameters and parameter scope are unverified and only recorded as an executor note**
- Severity: P2 | Status: Missing information
- Location: `run_ts_tot.py:50` (also `run_ts_tot.py:65`); `intent_evidence.txt:10-12` vs `intent_evidence.txt:25`
- Evidence: `torch.optim.AdamW(self.parameters(), lr=lr)` uses library defaults (weight_decay 0.01, betas 0.9/0.999). The authors' optimiser construction is not in `official_excerpts.py` (only `self.opt.step()` at line 381); `AMENDMENT_BASELINES_20261018.md` item 2 (`intent_evidence.txt:3-17`) names no optimiser — only the executor note (line 25) says "AdamW (official) instead of run_ts's Adam". `self.parameters()` also includes the added head, which the official optimiser cannot cover.
- Why it matters: Adam vs AdamW, weight decay and parameter scope change the update dynamics relative both to the official method and to the other run_ts baselines (plain Adam, no weight decay); this is a Table 1 comparability issue.
- Recommended correction: read the official `self.opt = ...` construction; match its hyper-parameters exactly (including weight decay and any scheduler); record the optimiser and its scope (net+head) in the registered amendment; state in the paper appendix that run_ts methods use Adam except tot with the official AdamW.

**F2 — Gate (a) of the registration has no evidence in the attached material**
- Severity: P2 | Status: Missing information
- Location: `intent_evidence.txt:15-17` (gate) vs `intent_evidence.txt:18-24` (evidence)
- Evidence: the gate requires (a) the released code, unchanged, on ETTh2 pred_len 1 (one seed) to land within the paper's reported spread for LSTD+TOT, and (b) lambda 0 vs official lambda to differ. The evidence log records only smoke-stream runs and gate (b) ("lambda 0 vs 1e-5: P differs"); no ETTh2 result appears.
- Why it matters: the registration states that if (a) or (b) fails, tot is reported as skipped with the reason. Publishing tot's Table 1 numbers without gate (a) violates the frozen gate.
- Recommended correction: run the released code on ETTh2 pred_len 1 and record the comparison with the paper's reported spread before Table 1 is assembled; if the result is not produced, report tot as skipped.

**F3 — `activation="gelu"` is not part of the registered size list and cannot be checked from the excerpts**
- Severity: P2 | Status: Missing information
- Location: `run_ts_tot.py:6-7,36-38`; `intent_evidence.txt:6-8`
- Evidence: the registered list is depth 9, hidden_dim 512, hidden_layers 1, tau 0.75, x_dim 3, L1/L2 1e-3, lags 1, dropout 0. `activation="gelu"` is set in the adapter and claimed in the docstring as coming from `LSTD_TOT_config.py` (ETTh2, pred_len 1), which is not among the audited files.
- Why it matters: activation enters `Base_Net` (regressor, zd_rec); a wrong value would silently change the function class while appearing registered.
- Recommended correction: verify `activation` (and tau/x_dim/L1/L2) against `LSTD_TOT_config.py` and add the value to the registered list.

**F4 — The learning step is the registered adaptation, not the authors' online update; wording risk**
- Severity: P2 | Status: Suspected issue
- Location: `run_ts_tot.py:61-65` vs `official_excerpts.py:372-383`
- Evidence: the authors' online step calls `self.model(x, False)` even in its learning branch (`official_excerpts.py:377`), so the official online update uses posterior means and `other_loss = L1 + L2` only (`official_excerpts.py:267`); the adapter uses `is_training=True` (`run_ts_tot.py:63`) so the KL and Jacobian-sparsity terms act, exactly as registered (`intent_evidence.txt:10-12`). Loss composition (CE + MSE(x_rec, x) + official `other_loss`) also matches the registration and drops the official forecast loss deliberately.
- Why it matters: the behaviour is faithful to the registration, but it is not the authors' online update; any text claiming Table 1 runs "the official TOT online algorithm" verbatim would be inaccurate, and the per-step cost (vmap(jacfwd)) is not the official online cost.
- Recommended correction: keep the behaviour (registered); make the paper/appendix wording match the registered adaptation (identification terms active per step, head on the latent, forecast loss replaced by cross-entropy). Changing the behaviour would require a user-approved amendment.

**F5 — `SamePadConv.store_grad` body after `if not self.training:` is not in the excerpts; eval-mode effect on triggers/memory unknown**
- Severity: P2 | Status: Missing information
- Location: `official_excerpts.py:445-451` (truncated), `run_ts_excerpts.py:60-70,84`, `run_ts_tot.py:44-47,67-68`
- Evidence: the counting wrapper counts `trigger` transitions 0→1 inside `store_grad`; the rest of `store_grad` (starting `if not self.training:`) and `fw_chunks` are not attached, and the module train/eval mode of the official loop is not shown. The harness keeps the whole model in `eval()` (`run_ts_excerpts.py:84`) and never calls `train()`.
- Why it matters: if trigger setting or memory reads branch on `self.training`, `fires` and the encoder's forward differ from the authors' setting; internally tot is at least consistent with fsnet/oneten under the same convention, so the Table 1 `fires` column stays comparable within the harness.
- Recommended correction: read the full `store_grad` and `fw_chunks`; if mode-dependent, either match the official loop's mode or document the eval() convention for all methods; re-check that tot's and fsnet/oneten's `fires` are counted under the same condition.

## Points that can only be confirmed by running code

1. Hook capture identity: the assert at `run_ts_tot.py:55` checks shape only, and a functorch wrapper of the same shape would pass it. Confirm in a smoke run that `self._z` is the plain `z_pred` object the net passed to `regressor` (id/type check), and that `head` receives exactly `z_pred.flatten(1)`. (Indirect evidence: the smoke runs completed and two runs were bit-identical; a batched tensor escaping vmap would normally raise.)
2. Regressor call pattern per learning forward: exactly one direct call (captured) followed by the vmap(jacfwd) trace calls (guarded). Confirm with a counter hook; also confirm that with lambda = 0 the regressor is called once (sparsity block skipped).
3. `fires` per batch for tot increments under the same eval()/device convention as fsnet/oneten, and the `_count_triggers` patch is active in the real entry point (asserted at `run_ts_tot.py:47`).
4. Equality of the constructed `args` with `LSTD_TOT_config.py` ETTh2 pred_len 1 (activation, tau, x_dim, L1/L2, depth, hidden_dim, hidden_layers, lags, dropout) — needs the config file.
5. The official optimiser construction (hyper-parameters, parameter scope, scheduler) and therefore whether `AdamW(self.parameters(), lr)` matches it — needs the authors' Exp code.
6. Gate (a): the released code on ETTh2 pred_len 1 versus the paper's reported spread.
7. Hook behaviour inside `vmap(jacfwd)` is torch-version dependent (verified on torch 2.14.1+cpu by the executor's smoke run); re-verify in the environment actually used for the P6 rerun if it differs (e.g. `TS_DEVICE=cuda`).

## 处置（Claude 核实）
- F1 优化器：官方 _select_optimizer 为 optim.AdamW(self.model.parameters(), lr)（exp_LSTD_TOT.py 第 611–613 行，默认超参）；在线阶段无调度器（adjust_learning_rate 只在离线训练轮次，第 685 行）。适配器与之一致；参数范围含分类头（官方无此头）。写入 P6 登记：TOT 用官方 AdamW，其余 run_ts 方法用 Adam。
- F2 gate (a)：已登记（REGISTRATION_P6_GATE_A_20261020，集群 H800），不在本审计范围。
- F3 activation：配置行未设，main.py 默认 gelu（第 138 行）；lags 默认 1（第 103 行）；其余由配置行给定。写入登记。
- F4 措辞：采纳；论文写"登记的改编（每步启用识别项，分类头接在潜变量上，预测损失换成交叉熵）"，不称官方在线算法原样。
- F5 store_grad：已读全文，只在 eval 模式（not self.training）判断触发；官方在线阶段同为 model.eval()；harness 全程 eval，与 fsnet/onenet 计数条件相同。
- 运行确认：钩子捕获——λ=1e-5 时一次学习前向调用 regressor 两次（直接 + vmap 内），捕获的是第一次的普通张量（形状 (B,3,d)，requires_grad）；λ=0 时调用一次。两次运行逐位相同；λ=0 与 1e-5 的预测不同。
