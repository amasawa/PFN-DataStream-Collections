
> auditor · mimo-v2.6-pro

MiMo 审计进行中。趁等待，我核对审计提示词里写的冒烟数字是否与实际运行一致。
Audit of `run_ts.py` (DTMoECls, AdaptZCls, ShifTSCls and `run()`), against the attached official excerpts. 6 findings, all P2; the protocol in `run()` itself I could verify as clean (predict-then-learn order, batch 0 not scored, features-only windows, `P[(t-1)*B:t*B]` aligned with stream rows `B..T*B-1`, softmax probabilities, label used only in `learn()` and scoring).

---

**F1 · Severity P2 · Confirmed issue · ShifTSCls (docstring 321-328, `parts` 344-349)**
Evidence: the official mask is `nn.Parameter(torch.rand(lb_win+1, feature_dim-1))` with a fixed one-hot column appended (`last_dim[0] = 1`, official_shifts.py 59, 81-83), and both the selection and the forecast side of the SAM loss drop the target column (`x_pred_sel[:,:,:-1]`, `x_out[:,:,:-1]`, 85, 93). The official target head is applied to the **normalised** forecast and residual-added to the target's own forecast before de-normalisation (`x_pred_last = self.linear(x_pred[:,:,:-1]) + x_pred[:,:,-1:]`, then `revin1(..., "denorm")`, 88-93). run_ts instead uses an (L, d) mask over all features with no fixed column, and applies `head(h)` to the **de-normalised** forecast with no residual.
Why it matters: the class docstring presents the (L, d) mask as "the official Soft Attention Mask" and only notes "official output 1, the target"; three structural changes are therefore undisclosed deviations from the registered "kept mechanism".
Recommended correction: state all three in the docstring (mask column, target-column exclusion, head placement / missing residual), or restore the residual analogue.

**F2 · Severity P2 · Suspected issue · DTMoECls.learn 228-231**
Evidence: the official train loop wraps the whole drift handling in `torch.no_grad()` (official_dtmoe_layer_train.py 140-146: `with torch.no_grad(): ... model.check_and_handle_drift(train_mode=True)`). run_ts calls `self.m.check_and_handle_drift(train_mode=True)` with gradients enabled.
Why it matters: if `expert_pool.enable_drift_expert` re-enables autograd internally the two are equivalent; if not, either the expert pre-training behaves differently from the official run or `analyze_drift_pattern` builds graphs on the gating network. Cannot be settled from the attached excerpt.
Recommended correction: wrap the call in `torch.no_grad()` to match the official, or read `enable_drift_expert` and record the verified reason for leaving it out.

**F3 · Severity P2 · Confirmed issue · AdaptZCls docstring (275, 291)**
Evidence: the docstring says "L = 1 allowed (MLP base on the current row)", but the code builds the same `iTransformer_z` Model for every L (285-288); there is no MLP base. The same docstring and the plan call `adapter_lr = 1e-3` "official"; the attached official code initialises the adapter optimiser at `lr=0.0003` (official_adaptz.py 4) and `online()` replaces it with `settings[model][data]['adp_online_lr']` (55), a table that is not attached.
Why it matters: two fidelity claims in the docstring are wrong or unsupported; the registered grid values themselves are fine.
Recommended correction: replace "(MLP base on the current row)" with what is actually built at L = 1, and either attach the settings table or state the adapter lr as the registered value without the "official 1e-3" claim.

**F4 · Severity P2 · Missing information · AdaptZCls.learn 306-316 vs official_adaptz.py 98-105**
Evidence: the official update is `loss.backward(retain_graph=True); his_grad2 = self.z.grad; his_grad = torch.mean(his_grad2, dim=0)` on an MSE loss; no zeroing of `self.z.grad` is visible in the excerpt (so `z.grad` may accumulate across iterations), and the mean divides by `z_shape[0] = max(batch_size, batch_size2)`, not by the number of rows used. run_ts sets `self.zp.grad = None` each batch and averages over `x.shape[0]`, with cross-entropy (the CE substitution is registered).
Why it matters: the docstring says "as the official update"; if the official `z.grad` is never cleared, `his` differs materially (cumulative vs per-batch gradient).
Recommended correction: check the full official `online()` for `self.z.grad` zeroing and for the settings table; adjust "as the official update" to the verified statement.

**F5 · Severity P2 · Confirmed issue · DTMoECls docstring 196 and cfg 204**
Evidence: "drift-expert pre-training epochs = 1 (official train_epochs)" — the official `Model.train_epochs` default is 10 (`getattr(configs, 'train_epochs', 10)`, official_dtmoe_model.py 40) and the experiment passes its own `args.train_epochs`. The value 1 comes from the registration (PLAN_BASELINES "one pass over its ref / cur data") and is implemented via `cfg.train_epochs = 1`, which also becomes `finetune_epochs` in `check_and_handle_drift`.
Why it matters: the docstring attributes a registered deviation to the official code.
Recommended correction: reword to "one pass over ref / cur data, as registered (official default 10)".

**F6 · Severity P2 · Confirmed issue · run() 10-11, 388-391, fires() 235-236**
Evidence: PLAN_BASELINES line 73 registers "Fire counts of every drift mechanism (memory triggers, MMD detections, experts added / pruned) are logged"; the npz stores only `fires = Δ drift_handled_count`, so experts added / pruned are not logged. The run() header also claims the output is `<out>/<stream>__<method>.npz`, while the file is `<out>/<stream>__<method>_L<L>_lr<lr>_s<steps>[_m<mech>].npz`.
Why it matters: a registered logging promise is unfulfilled, and the header does not describe the artefact name.
Recommended correction: record expert add / prune counts (extra npz fields) or amend the registration line, and fix the header string.

---

Can only be confirmed by running code (not concluded here):
1. Saved `P` rows sum to 1 and correspond to stream rows `B..T*B-1` in the produced npz files.
2. The quoted smoke numbers (`fsnet` elec2 acc 0.7835 with 110 triggers; `dtmoe` 4 drifts in 45 batches) against the actual npz / logs.
3. `_extend_adam` really picks up the parameters of a newly created drift expert and the optimiser continues (needs a stream where a drift fires).
4. `AdaptZCls.his` is finite and changes across batches (`zp.grad` mean over the batch rows).
5. Numerical equivalence of learning in eval mode for ShifTS / AdaptZ (expected, given dropout 0 and no normalisation layers).
6. AdaptZ at L = 1 (`Model(cfg, 1)`) actually runs and learns.
