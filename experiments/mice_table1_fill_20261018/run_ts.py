"""Time-series drift methods adapted to streaming classification (PLAN_BASELINES.md). One harness, one class per method;
official modules are imported from the read-only clones in ~/ext-baselines.

Protocol: B = 100 rows per batch; batch t is predicted (softmax of the classification head, no gradient) with the state
after learning batches < t; then its labels are revealed and the model takes n_steps Adam steps on its 100 rows; batch 0
is warm-up (learned, not scored). Inputs: standardised with the warm-up batch mean / std, clipped to [-10, 10]. Row
context: the features of the L most recent rows up to and including the row (stream order; rows before the first are
the first row repeated). Seed 0. CPU (torch.set_num_threads(1)); the official modules call .cuda() on buffers, which
is mapped to the CPU here (Tensor.cuda -> identity) without changing their arithmetic.
Output <out>/<stream>__<method>_L<L>_lr<lr>_s<steps>[_m<mech>].npz: acc, pred, P (float32, rows of batches 1..T-1),
C, B, wt, fires (per batch: memory triggers for fsnet / onenet, drifts handled for dtmoe), added / pruned (dtmoe: experts
enabled / disabled per batch), config. C = the number of classes of the stream (labels are re-indexed per stream when the
streams are built; a property of the data set, as for every method of Table 1). No calendar marks: the official
encoders take enc_in + 7 channels (x_mark concatenated); here only the d features.
Usage: python run_ts.py --data <dir> --out <dir> --streams s1 .. --method fsnet --L 16 --lr 1e-3 --steps 1 [--mech v]"""
import argparse, json, os, sys, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

EXT = os.path.expanduser("~/ext-baselines")
torch.Tensor.cuda = lambda self, *a, **k: self          # official modules hard-code .cuda() on buffers


def windows(Xs, idx, L):
    """L x d context of every row in idx (rows before 0 are row 0)."""
    j = idx[:, None] - np.arange(L - 1, -1, -1)[None, :]
    return Xs[np.maximum(j, 0)]


class Method(nn.Module):
    """Default online step: predict = softmax(forward); learn = steps x (cross-entropy, backward, Adam step,
    after_step hook). Subclasses with their own online rules override predict / learn."""
    def setup(self, lr):
        self.opt = torch.optim.Adam(self.parameters(), lr=lr)

    def predict(self, x):
        with torch.no_grad():
            return F.softmax(self(x), -1)

    def learn(self, x, y, steps):
        for _ in range(steps):
            self.opt.zero_grad(); F.cross_entropy(self(x), y).backward(); self.opt.step(); self.after_step()

    def after_step(self):
        pass

    def fires(self):
        return 0


# ---------------------------------------------------------------------------------------------------------- fsnet
class FSNetCls(Method):
    """FSNet (Pham et al., ICLR 2023): official TSEncoder (dilated conv layers with per-layer adapters and associative
    memory, models/ts2vec/fsnet.py) over the L x d window; representation of the last step -> linear -> C logits
    (the official regressor is nn.Linear(320, c_out * pred_len)). Official sizes: output_dims 320, hidden 64, depth 10.
    The memory trigger (cos(f_grads, grads) < -tau) is checked in eval mode, as in the official online phase, so the
    module stays in eval mode throughout (the whole stream is the online phase). mech = tau."""
    REPO = "fsnet"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        from models.ts2vec.fsnet import TSEncoder
        self.enc = TSEncoder(input_dims=d, output_dims=320, hidden_dims=64, depth=10)
        self.head = nn.Linear(320, C)
        self.convs = [m for m in self.enc.modules() if "PadConv" in type(m).__name__]
        from models.ts2vec import fsnet_
        assert self.convs and all(type(m) is fsnet_.SamePadConv for m in self.convs) and fsnet_.SamePadConv._counted
        if mech is not None:
            for m in self.convs:
                m.tau = float(mech)

    def forward(self, x):
        return self.head(self.enc(x, mask="all_true")[:, -1])

    def after_step(self):
        for m in self.convs:
            m.store_grad()

    def fires(self):
        return int(sum(getattr(m, "_n_trig", 0) for m in self.convs))


def _count_triggers():
    """Count the memory reads of the official SamePadConv (trigger set to 1 then consumed in fw_chunks)."""
    from models.ts2vec import fsnet_
    orig = fsnet_.SamePadConv.store_grad

    def store_grad(self):
        before = self.trigger; orig(self)
        if self.trigger == 1 and before == 0:
            self._n_trig = getattr(self, "_n_trig", 0) + 1
    fsnet_.SamePadConv.store_grad = store_grad
    fsnet_.SamePadConv._counted = True


# --------------------------------------------------------------------------------------------------------- onenet
class _MLP(nn.Module):
    """exp_onenet_fsnet.MLP (copied: importing the exp module pulls in its data loaders)."""
    def __init__(self, n_inputs, n_outputs, mlp_width, mlp_depth, mlp_dropout, act):
        super().__init__()
        self.input = nn.Linear(n_inputs, mlp_width); self.dropout = nn.Dropout(mlp_dropout)
        self.hiddens = nn.ModuleList([nn.Linear(mlp_width, mlp_width) for _ in range(mlp_depth - 2)])
        self.output = nn.Linear(mlp_width, n_outputs); self.act = act

    def forward(self, x, train=True):
        x = self.input(x)
        if train:
            x = self.dropout(x)
        x = self.act(x)
        for h in self.hiddens:
            x = h(x)
            if train:
                x = self.dropout(x)
            x = self.act(x)
        return self.output(x)


class OneNetCls(Method):
    """OneNet (Zhang et al., NeurIPS 2023), exp_onenet_fsnet.py with individual = 0 (one output, the label):
    branch 1 = TSEncoder over the variables (forward_time on the d x L transpose, input_dims = L), its per-variable
    representations flattened -> linear -> C (the official head maps each variable to pred_len); branch 2 = TSEncoder
    over time (input_dims = d), last step -> linear -> C. Online step per revealed batch, as the official _ol_one_batch:
    (i) both branches by l1 + l2 (cross-entropy each) with the model optimiser, store_grad; (ii) decision MLP on
    [g p1, (1-g) p2, onehot(y)] gives the bias, g = sigmoid(w + bias), loss_bias = NLL of g p1 + (1-g) p2 (opt_bias);
    (iii) loss_w = NLL of sigmoid(w) p1 + (1 - sigmoid(w)) p2 (opt_w). As the official code, w is not detached in (ii)
    and opt_w.zero_grad() runs only after opt_w.step(), so the step of w uses the gradients of loss_bias and loss_w; the
    decision MLP is not part of the official model, so it stays in train mode (dropout 0.1 active) while the encoders are
    in eval mode (official online phase: model.eval()). Prediction: g = sigmoid(w + bias) with the bias
    of the last learned batch (its mean over the batch; the official online batch has one row). Probabilities replace
    the forecasts in every combination. lr_w = lr_bias = 1e-3 (official defaults). mech = tau of both encoders."""
    REPO = "OneNet"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        from models.ts2vec import fsnet_
        for cls in (fsnet_.SamePadConv, fsnet_.ConvBlock, fsnet_.DilatedConvEncoder):   # their device defaults to cuda:0
            if not getattr(cls, "_cpu", False):
                cls.__init__ = (lambda f: lambda self, *a, device=None, **k: f(self, *a, device=torch.device("cpu"), **k))(cls.__init__)
                cls._cpu = True
        from models.ts2vec.fsnet import TSEncoder
        self.enc_time = TSEncoder(input_dims=L, output_dims=320, hidden_dims=64, depth=10)
        self.head_time = nn.Linear(320 * d, C)
        self.enc = TSEncoder(input_dims=d, output_dims=320, hidden_dims=64, depth=10)
        self.head = nn.Linear(320, C)
        self.decision = _MLP(3 * C, 1, 32, 3, 0.1, nn.Tanh())
        self.weight = nn.Parameter(torch.zeros(1)); self.C = C
        self.register_buffer("bias", torch.zeros(1))
        self.convs = [m for m in self.modules() if "PadConv" in type(m).__name__]
        assert self.convs and all(type(m) is fsnet_.SamePadConv for m in self.convs) and fsnet_.SamePadConv._counted
        if mech is not None:
            for m in self.convs:
                m.tau = float(mech)

    def branches(self, x):
        p1 = F.softmax(self.head_time(self.enc_time.forward_time(x).flatten(1)), -1)
        p2 = F.softmax(self.head(self.enc(x, mask="all_true")[:, -1]), -1)
        return p1, p2

    def setup(self, lr):
        model_params = [p for n, p in self.named_parameters() if not n.startswith(("decision", "weight"))]
        self.opt = torch.optim.Adam(model_params, lr=lr)
        self.opt_w = torch.optim.Adam([self.weight], lr=1e-3)
        self.opt_bias = torch.optim.Adam(self.decision.parameters(), lr=1e-3)

    def predict(self, x):
        with torch.no_grad():
            p1, p2 = self.branches(x); g = torch.sigmoid(self.weight + self.bias)
            return g * p1 + (1 - g) * p2

    def learn(self, x, y, steps):
        nll = lambda p: F.nll_loss(torch.log(p.clamp_min(1e-8)), y)
        Y = F.one_hot(y, self.C).float()
        self.decision.train()
        for _ in range(steps):
            p1, p2 = self.branches(x)
            loss = F.nll_loss(torch.log(p1.clamp_min(1e-8)), y) + F.nll_loss(torch.log(p2.clamp_min(1e-8)), y)
            self.opt.zero_grad(); loss.backward(); self.opt.step(); self.after_step(); self.opt.zero_grad()
            p1w, p2w = p1.detach(), p2.detach()
            g = torch.sigmoid(self.weight)
            b = self.decision(torch.cat([g * p1w, (1 - g) * p2w, Y], 1))
            g = torch.sigmoid(self.weight + b)
            nll(g * p1w + (1 - g) * p2w).backward(); self.opt_bias.step(); self.opt_bias.zero_grad()
            self.bias = b.detach().mean().view(1)
            g = torch.sigmoid(self.weight)
            nll(g * p1w + (1 - g) * p2w).backward(); self.opt_w.step(); self.opt_w.zero_grad()

    def after_step(self):
        for m in self.convs:
            m.store_grad()

    def fires(self):
        return int(sum(getattr(m, "_n_trig", 0) for m in self.convs))


# ---------------------------------------------------------------------------------------------------------- dtmoe
class DTMoECls(Method):
    """Dynamic TMoE (ICML 2026): the official Model (models/Dynamic_TMoE/model.py) built with its defaults (d_model 128,
    2 temporal MoE layers, 4 base + 3 drift experts, top_k 2, 2 RNN router layers, dropout 0.1, RevIN affine,
    channel independence; drift detector window 576, history 20, k_sigma 2.0 = the model's getattr defaults) and its
    forecast() up to the flattened encoder output [B, N, P*D]; head = linear(N*P*D -> C) instead of the per-channel
    linear(P*D -> pred_len) (the label is one output for the whole row). patch_len = L/2, stride = L/8 (the official
    96 / 48 / 12 ratios). No timestamps: patch_cycle_indices = 0 (the official fallback when x_mark is None). Learning
    phase in train mode: before each step, if the layer-0 detector is full, model.check_and_handle_drift(train_mode =
    True) (MMD test, drift expert added and pre-trained, redundant experts pruned), exactly as the official train loop;
    drift-expert pre-training: one pass over its ref / cur data, as registered (official default train_epochs 10).
    The drift handling runs under torch.no_grad(), as the official train loop. Prediction in eval mode (router not updated).
    mech = drift_k_sigma. fires = drifts handled (sum over layers)."""
    REPO = "Dynamic-TMoE"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        from types import SimpleNamespace
        from models.Dynamic_TMoE.model import Model
        cfg = SimpleNamespace(task_name="long_term_forecast", seq_len=L, pred_len=1, patch_len=L // 2, stride=max(1, L // 8),
                              d_model=128, dropout=0.1, enc_in=d, cycle_length=24, train_epochs=1)
        self.m = Model(cfg)
        if mech is not None:
            self.m.drift_k_sigma = float(mech)
        self.m.enable_drift_detection(window_size=self.m.drift_window_size, history_size=self.m.drift_history_size,
                                      k_sigma=self.m.drift_k_sigma)
        self.head = nn.Linear(d * self.m.head_input_dim, C)
        self.added = self.pruned = 0

    def forward(self, x):
        m = self.m; B, S, N = x.shape
        x_norm, _, _ = m.revin_layer.normalize(x)
        enc_out, _ = m.patch_embedding(x_norm.permute(0, 2, 1))
        pci = torch.zeros(B, dtype=torch.long)
        start = m.global_patch_counter.item(); BN, P = enc_out.shape[:2]
        for layer in m.temporal_moe_layers:
            enc_out, _ = layer(enc_out, hidden_state=None, batch_start_patch_idx=start, patch_cycle_indices=pci)
        if m.training:
            m.global_patch_counter += BN * P
        return self.head(enc_out.reshape(B, -1))

    def learn(self, x, y, steps):
        self.train()
        for _ in range(steps):
            det = self.m.temporal_moe_layers[0].drift_detector
            if det is not None and det.should_check_drift():
                e0 = self.enabled()
                with torch.no_grad():                            # (the expert pre-training re-enables grad inside)
                    self.m.check_and_handle_drift(train_mode=True)
                e1 = self.enabled()
                self.added += sum(len(n - o) for o, n in zip(e0, e1)); self.pruned += sum(len(o - n) for o, n in zip(e0, e1))
                self.opt = _extend_adam(self.opt, self)          # parameters of newly enabled experts
            self.opt.zero_grad(); F.cross_entropy(self(x), y).backward(); self.opt.step()
        self.eval()

    def fires(self):
        return int(sum(int(l.drift_handled_count) for l in self.m.temporal_moe_layers))

    def enabled(self):
        return [set(int(i) for i in l.expert_pool.get_enabled_expert_indices()) for l in self.m.temporal_moe_layers]


def _extend_adam(opt, model):
    """Add parameters that are not yet in the optimiser (experts created at a drift) with the same settings."""
    have = {id(p) for g in opt.param_groups for p in g["params"]}
    new = [p for p in model.parameters() if id(p) not in have]
    if new:
        opt.add_param_group(dict(params=new))
    return opt


# --------------------------------------------------------------------------------------------------------- adaptz
class _Adapter(nn.Module):
    """adapt_z.py bulid_adapter.Adapter, copied (it is defined inside a method of the official class)."""
    def __init__(self, n, E):
        super().__init__()
        self.linear = nn.Linear(E, 64); self.linear_ = nn.Linear(E, 64)
        self.linear2 = nn.Linear(64, 64); self.linear3 = nn.Linear(64, E)
        self.lr = nn.Parameter(torch.ones(n, E))

    def forward(self, x, his_grad):
        his_grad = self.linear_((his_grad * self.lr).unsqueeze(0).repeat(x.size(0), 1, 1))
        x = torch.relu(self.linear(x) + his_grad)
        return self.linear3(torch.relu(self.linear2(x)))


class AdaptZCls(Method):
    """ADAPT-Z (ICLR 2026), adapt_z.py online(): base = the official iTransformer_z (configs/model/iTransformer.yaml,
    ETTh sizes: e_layers 2, d_model 128, d_ff 128, n_heads 8, dropout 0, factor 1, gelu; z added after encoder layer
    z_loc = e_layers - 1 as the official iTransformer setting); variates = the d features, series = the L-row window
    (the same iTransformer for every L, also L = 1);
    use_norm false (official true): with use_norm the official forecast() also de-normalises the output by each
    variate's window mean and std, which has no meaning for class scores, and for L = 1 it makes the series 0; the
    inputs are already standardised (warm-up batch statistics).
    projector: d_model -> C per variate, logits = mean over variates. Prediction: feature = model(x, z = 0)['feature'],
    z = adapter(feature, his_grad), logits = model(x, z). After the labels: (a) his_grad = mean over the z batch dimension
    of z.grad, where z is a zeros parameter and, as in the official online(), z.grad is never cleared (it accumulates
    over batches); (b) n_steps steps on the loss of model(x,
    adapter(stored feature, his_grad used at prediction)), updating the adapter (Adam, adapter_lr = mech; the official
    online phase uses adp_online_lr = 3e-4 for iTransformer, adapter_lr = 1e-3 in its pre-training)
    and the base (Adam, lr): the official online phase updates only the projector of a pre-trained base; here the base
    is trained online (no pre-training split, PLAN_BASELINES.md)."""
    REPO = "ADAPT-Z"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        from types import SimpleNamespace
        import importlib
        for m in ("", ".masking"):            # the repository's folder is "uitls" while its modules import "utils"
            sys.modules["utils" + m] = importlib.import_module("uitls" + m)
        from models.iTransformer_z import Model
        cfg = SimpleNamespace(pred_len=C, output_attention=False, use_norm=False, d_model=128, e_layers=2, embed="timeF",
                              freq="h", dropout=0.0, class_strategy="projection", factor=1, n_heads=8, d_ff=128,
                              activation="gelu", norm_style="none")
        self.m = Model(cfg, L); self.z_loc = 1; self.d = d
        self.adapter = _Adapter(d, 128)
        self.zp = nn.Parameter(torch.zeros(100, d, 128))
        self.his = torch.zeros(d, 128); self.adapter_lr = 1e-3 if mech is None else float(mech)

    def logits(self, out):
        return out["pred"].mean(-1)                                   # [B, C, N] -> [B, C]

    def setup(self, lr):
        self.opt = torch.optim.Adam(self.m.parameters(), lr=lr)
        self.opt_a = torch.optim.Adam(self.adapter.parameters(), lr=self.adapter_lr)

    def predict(self, x):
        with torch.no_grad():
            feat = self.m(x, z=torch.zeros(x.shape[0], self.d, 128), z_loc=self.z_loc)["feature"]
            self._feat, self._his = feat.detach(), self.his.clone()
            return F.softmax(self.logits(self.m(x, z=self.adapter(feat, self.his), z_loc=self.z_loc)), -1)

    def learn(self, x, y, steps):
        if not hasattr(self, "_feat") or self._feat.shape[0] != x.shape[0]:   # batch 0: nothing predicted yet
            self.predict(x)
        feat, his_used = self._feat, self._his
        F.cross_entropy(self.logits(self.m(x, z=self.zp[:x.shape[0]], z_loc=self.z_loc)), y).backward()
        self.his = self.zp.grad.mean(0).detach().clone()
        for _ in range(steps):
            self.opt.zero_grad(); self.opt_a.zero_grad()
            F.cross_entropy(self.logits(self.m(x, z=self.adapter(feat, his_used), z_loc=self.z_loc)), y).backward()
            self.opt.step(); self.opt_a.step()


# --------------------------------------------------------------------------------------------------------- shifts
class ShifTSCls(Method):
    """ShifTS (ICLR 2026), exp/exp_causal_forecasting.py Warpper.foward_causal, adapted: (1) temporal shift first:
    the official RevIN (revin1, affine) normalises the L x d window; the backbone (an MLP on the flattened normalised
    window, 2 x 256, as registered) forecasts the d exogenous features of the current position, de-normalised by
    revin1 -> h; (2) concept drift: the official Soft Attention Mask, a learnable (L x d) score softmax-ed over the window
    positions, kept where above its per-feature mean and renormalised, gives s = sum_positions mask * window (the
    invariant pattern; in forecasting the window spans lookback + horizon, here the window ends at the observed current
    row); loss = cross-entropy(head(h_norm), y) + mech * MSE(s, h) (official: forecast loss + MSE(x_pred_sel, x_out of the
    exogenous features), weight 1); head = the official target head Linear(d, 512) - ReLU - Linear(512, C) applied to the
    normalised forecast h_norm (h = revin1 de-normalisation of h_norm), as official. Differences forced by the task: the
    label is not an input channel, so the official mask's fixed one-hot column for the target, the target-column
    exclusion and the residual "+ target forecast" of the head have no counterpart; mask (L x d) over the d features."""
    REPO = "ShifTS"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        sys.path.insert(0, f"{EXT}/ShifTS")
        import importlib.util
        spec = importlib.util.spec_from_file_location("shifts_exp", f"{EXT}/ShifTS/exp/exp_causal_forecasting.py")
        src = open(spec.origin).read(); i = src.index("class RevIN"); j = src.index("warnings.filterwarnings")
        ns = {"torch": torch, "nn": nn}; exec(compile(src[i:j], spec.origin, "exec"), ns)   # the RevIN class only
        self.revin = ns["RevIN"](num_features=d)
        self.mask = nn.Parameter(torch.rand(L, d))
        self.backbone = nn.Sequential(nn.Flatten(), nn.Linear(L * d, 256), nn.ReLU(), nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, d))
        self.head = nn.Sequential(nn.Linear(d, 512), nn.ReLU(), nn.Linear(512, C))
        self.lam = 1.0 if mech is None else float(mech)

    def parts(self, x):
        m = torch.softmax(self.mask, 0)
        m = m * ((m - m.mean(0)) > 0); m = m / m.sum(0)
        s = (x * m).sum(1)
        hn = self.backbone(self.revin(x, "norm")).unsqueeze(1)
        h = self.revin(hn, "denorm")[:, 0]
        return self.head(hn[:, 0]), s, h

    def forward(self, x):
        return self.parts(x)[0]

    def learn(self, x, y, steps):
        for _ in range(steps):
            logit, s, h = self.parts(x)
            self.opt.zero_grad(); (F.cross_entropy(logit, y) + self.lam * F.mse_loss(s, h)).backward(); self.opt.step()


METHODS = {"fsnet": FSNetCls, "onenet": OneNetCls, "dtmoe": DTMoECls, "adaptz": AdaptZCls, "shifts": ShifTSCls}


def run(data, out, stream, method, L, lr, steps, mech, B=100):
    tag = f"{method}_L{L}_lr{lr:g}_s{steps}" + ("" if mech is None else f"_m{mech:g}")
    dst = f"{out}/{stream}__{tag}.npz"
    if os.path.exists(dst):
        return
    torch.manual_seed(0); np.random.seed(0)
    z = np.load(f"{data}/{stream}.npz"); X, y = z["X"].astype(np.float64), z["y"].astype(int)
    C, T = int(y.max()) + 1, len(y) // B
    mu, sd = X[:B].mean(0), X[:B].std(0) + 1e-6
    Xs = np.clip((X[:T * B] - mu) / sd, -10, 10).astype(np.float32)
    model = METHODS[method](X.shape[1], C, L, mech)
    model.eval()                                     # see FSNetCls: the stream is the online phase
    model.setup(lr)
    acc, wt, fires = np.full(T, np.nan), np.zeros(T), np.zeros(T, int)
    added, pruned = np.zeros(T, int), np.zeros(T, int)
    P = np.zeros(((T - 1) * B, C), np.float32)
    for t in range(T):
        ts = time.time(); idx = np.arange(t * B, (t + 1) * B)
        xw = torch.from_numpy(windows(Xs, idx, L)); yt = torch.from_numpy(y[idx])
        if t > 0:
            p = model.predict(xw).numpy()
            P[(t - 1) * B:t * B] = p; acc[t] = (p.argmax(1) == y[idx]).mean()
        f0, a0, p0 = model.fires(), getattr(model, "added", 0), getattr(model, "pruned", 0)
        model.learn(xw, yt, steps)
        fires[t] = model.fires() - f0; wt[t] = time.time() - ts
        added[t], pruned[t] = getattr(model, "added", 0) - a0, getattr(model, "pruned", 0) - p0
    tmp = dst[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, acc=acc, pred=P.argmax(1), P=P, C=C, B=B, wt=wt, fires=fires, added=added, pruned=pruned,
                        config=json.dumps(dict(method=method, L=L, lr=lr, steps=steps, mech=mech)))
    os.replace(tmp, dst)
    print(stream, tag, f"acc={np.nanmean(acc):.4f}", f"time={wt.sum():.0f}s", f"fires={fires.sum()}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--streams", nargs="+")
    ap.add_argument("--method", required=True); ap.add_argument("--L", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3); ap.add_argument("--steps", type=int, default=1)
    ap.add_argument("--mech", type=float, default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    torch.set_num_threads(1)
    sys.path.insert(0, f"{EXT}/{METHODS[a.method].REPO}")       # one method (one repository) per process
    if a.method in ("fsnet", "onenet"):
        _count_triggers()
    for s in a.streams:
        run(a.data, a.out, s, a.method, a.L, a.lr, a.steps, a.mech)
