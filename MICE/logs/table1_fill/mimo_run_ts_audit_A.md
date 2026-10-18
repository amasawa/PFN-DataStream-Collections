
> auditor · mimo-v2.6-pro

Audit complete. Scope reviewed: `run()` / `windows()` / `Method`, `FSNetCls`, `OneNetCls`, `_count_triggers`, against PLAN_BASELINES.md and the attached official excerpts. Five findings; one is a method–code mismatch in a kept mechanism.

## Findings

### 1. OneNet: combination-weight update does not match the official update rule (gradient accumulation dropped)
- **Severity**: P1
- **Finding status**: Confirmed issue
- **Location**: `run_ts.py:162-176` (`OneNetCls.learn`) vs `official_onenet_excerpt.py:197-218` (`_ol_one_batch`, `individual = 0`)
- **Evidence**: In the official code `self.weight` is a plain leaf tensor with `requires_grad = True` and is **not** in `opt_bias`. The sequence is: `loss_bias.backward()` (whose graph reaches `weight` twice: through `inputs_decision = cat([sigmoid(w) * y1_w, ...])` and through `sigmoid(w + bias)`) → `opt_bias.step(); opt_bias.zero_grad()` (which does not clear `weight.grad`) → `loss_w.backward()` (accumulates onto the same `weight.grad`) → `opt_w.step(); opt_w.zero_grad()`. So the official weight step uses `∂loss_bias + ∂loss_w`. The adaptation detaches `weight` everywhere in the bias step (`g = torch.sigmoid(self.weight).detach()`, `torch.sigmoid(self.weight.detach() + b)`) and calls `self.opt_w.zero_grad()` **before** `loss_w.backward()`, so `weight` is trained with `∂loss_w` only. The decision inputs are likewise detached (`g = torch.sigmoid(self.weight).detach()`), whereas the official `F.sigmoid(self.weight)` is not.
- **Why it matters**: The kept mechanism of OneNet is exactly the `sigmoid(w)` + decision-bias combination and its online update; this is a silent change to that update rule, not a disclosed adaptation. It changes the trajectory of `w` and hence every prediction `g * p1 + (1 - g) * p2`.
- **Recommended correction**: Either replicate the official accumulation (drop the detaches in the bias step, move `opt_w.zero_grad()` to after `opt_w.step()` as in the official code), or keep the cleaner split and document it in the class docstring and the README change list as a deliberate deviation ("official `opt_w.zero_grad()` runs after `step()`, so `loss_bias` gradients accumulate into `w`; we isolate the two losses").

### 2. Official time-mark features dropped from both encoders' input (undisclosed in the class docstrings)
- **Severity**: P2
- **Finding status**: Confirmed issue
- **Location**: `run_ts.py:62` (`FSNetCls`: `TSEncoder(input_dims=d, ...)`), `run_ts.py:134-137` (`OneNetCls` branch 2), `run_ts.py:70` (`self.enc(x, ...)`); official `official_fsnet_exp_excerpt.py:15` (`input_dims=args.enc_in + 7`) and `official_onenet_excerpt.py:17,33` (`x = torch.cat([x, x_mark], dim=-1)`)
- **Evidence**: Both official nets concatenate 7 calendar-mark channels to the raw features before the encoder; the adaptation feeds the d features only. PLAN_BASELINES.md discloses this only implicitly ("Row context: features (never labels) ... L x d"); `FSNetCls`'s docstring says "over the L x d window" without naming the dropped marks, and `OneNetCls`'s does not mention them at all (PLAN states "No timestamps" explicitly only for dtmoe).
- **Why it matters**: Every deviation must be one the docstring states. This one is real (less input information than the official method) and a reader of the class docstrings cannot tell it was made.
- **Recommended correction**: Add one sentence to both docstrings and the README change list: "no calendar marks; the official encoder takes `enc_in + 7` channels (`x_mark` concatenated), here `input_dims = d`".

### 3. Model output dimension `C` is computed from the labels of the whole stream
- **Severity**: P2
- **Finding status**: Suspected issue
- **Location**: `run_ts.py:370` (`C, T = int(y.max()) + 1, len(y) // B`), used at `run_ts.py:373` (head size) and in the shape of `P`
- **Evidence**: `y.max()` reads labels of all batches, including those not yet revealed when batch 1 is predicted. If a class first appears in batch 50, the model predicting batch 1 already has a softmax unit for it.
- **Why it matters**: The protocol states "batch t is predicted with the state after learning batches < t". The architecture (head width, `P` columns) is part of that state and here depends on future labels. For these benchmarks the class set is plausibly a known dataset property, which is why this is only Suspected — but as written the code derives it from future labels.
- **Recommended correction**: Pass `C` as a dataset property (each stream's registered class count), or compute it from the warm-up batch and assert `C == int(y.max()) + 1`, failing loudly otherwise.

### 4. Global `model.eval()` for the entire run: official online mode unverified; OneNet decision-MLP dropout silently disabled
- **Severity**: P2
- **Finding status**: Missing information
- **Location**: `run_ts.py:374` (`model.eval()`), interacting with `official_fsnet_padconv.py:24` (`if not self.training:` in `store_grad`) and `run_ts.py:97-98` (`_MLP.forward` dropout gated on `train=True`, but the `nn.Dropout` submodule is in eval mode because the whole module is)
- **Evidence**: `FSNetCls`'s docstring claims the memory trigger is checked in eval mode "as in the official online phase" — the attached excerpts show the trigger gate but not the train/eval mode of the official online loop, so that claim is not verifiable from the material in scope. Concrete consequence of the unconditional `eval()`: OneNet's decision MLP dropout (official `mlp_dropout = 0.1`) is always an identity, and if the official `TSEncoder` contains BatchNorm its running statistics stay at initialisation for the whole stream. Note the trigger gate `if not self.training` makes eval mode necessary for the FSNet/OneNet memory to fire at all — supporting evidence for the docstring's claim, but not proof of what the official loop does.
- **Why it matters**: If the official online phase runs in train mode (dropout active in the decision MLP), this is an undisclosed behavioural deviation in OneNet's kept combination mechanism; if it runs in eval, everything is consistent and only the docstring claim needs a source.
- **Recommended correction**: Read the official `Exp_TS2VecSupervised` train/test loop mode during `_ol_one_batch` (not in the attached excerpts) and record it in the docstring; if the official loop is in train mode, either call `train()` during `learn()` (and keep `eval()` for `predict`) or state explicitly that dropout/BN are disabled.

### 5. `_count_triggers` patches a different import path than the one the encoders are built from
- **Severity**: P2
- **Finding status**: Missing information
- **Location**: `run_ts.py:80-90` (`from models.ts2vec import fsnet_; fsnet_.SamePadConv.store_grad = ...`) vs `run_ts.py:61` and `run_ts.py:133` (`from models.ts2vec.fsnet import TSEncoder`)
- **Evidence**: The counter only increments if the `SamePadConv` class object used by the patched module is the same class the encoder instantiates. If `models.ts2vec.fsnet` and `models.ts2vec.fsnet_` defined separate classes, `fires` would be identically 0 with no error. The smoke tests report 110 triggers on elec2, which strongly suggests the class is shared (e.g. re-export), but the code contains no guard. Also, only `SamePadConv.store_grad` is wrapped; any other `PadConv`-named class with its own `store_grad` would be counted as 0 silently.
- **Why it matters**: `fires` is a reported Table 1 quantity; a silent 0 would look like "mechanism never fired" and would be reported per PLAN ("A mechanism that never fires on the development streams at the frozen setting is reported").
- **Recommended correction**: At patch time assert `fsnet.SamePadConv is fsnet_.SamePadConv` (import the module actually used to build the encoder) and assert the encoder's `convs` are instances of the patched class; or patch `type(model.convs[0]).store_grad` instead of a hard-coded class path.

## Points that can only be confirmed by running code
1. **`fsnet` / `fsnet_` class identity** (Finding 5): the non-zero smoke-test trigger counts (110 on elec2) indicate the patched class is live; a one-line `assert` at startup settles it.
2. **Trigger set-events = memory reads**: the counter increments when `store_grad` raises `trigger` 0→1; the memory read/write in `fw_chunks` executes at the *next* forward (often the next batch's `predict`). Under the harness's one-forward-per-learn-step schedule every set event is consumed exactly once, so counts should coincide with reads — equal `fires.sum()` and a read counter (a second patch inside `fw_chunks`) would confirm.
3. **Probability rows sum to 1 in the saved `P`** for both methods (`softmax` for FSNet; convex combination `g*p1+(1-g)*p2` for OneNet) — checkable on the written `.npz` (`np.abs(P.sum(1) - 1).max()`).
4. **`P` alignment against `acc`**: recompute `acc` from `P` and `y[B:T*B]` and compare with the stored `acc[1:]` (should match exactly).
5. **BatchNorm presence and running-stat behaviour in the official `TSEncoder`** under permanent `eval()` (Finding 4) — confirmable by instantiating the encoder and listing its submodules' types at runtime.

## Checked and found correct within scope
- Prequential order in `run()`: `predict` precedes `learn` for every batch t ≥ 1; batch 0 is learned and never scored (`acc[0] = nan`); `P[(t-1)*B : t*B]` filled for t = 1..T-1 covers exactly stream rows B..T*B-1 of `P`, matching the docstring and `P.shape[0] = (T-1)*B`.
- No label leakage into features or into prediction: `windows()` reads only `Xs`; labels enter only `acc` (after `predict`) and `learn`. The only label-derived prediction-side state is OneNet's `bias`/`weight`, which come from already-learned batches (Finding 3 covers the `C` issue).
- `windows()` context order (oldest → newest, current row last, pre-stream rows padded with row 0) matches the registered protocol; `enc(... )[:, -1]` and `forward_time` usage match the official call sites (`official_fsnet_exp_excerpt.py:9`, `official_onenet_excerpt.py:29`).
- FSNet mechanism kept intact: official `TSEncoder` 320/64/10, linear head 320→C, `after_step` → `store_grad` in the same order as the official `_ol_one_batch` (`step` → `store_grad` → `zero_grad`), `mech = tau` set on the convs (official default 0.75). Per-batch `fires` measures sets of the memory trigger; OneNet's `fires` covers both encoders' convs, matching `official_onenet_excerpt.py:50-58`.
- Optimiser groups (`FSNetCls`: one Adam over all parameters; `OneNetCls`: `opt` excludes `decision.*` and the top-level `weight` only — `head.weight`/`head_time.weight` correctly stay in `opt`), softmax outputs for FSNet, convex combination of two softmaxes for OneNet, and state carried across batches (EMAs, `W`, `q_ema`, `w`, `bias`) are all consistent with the docstrings.
