"""TOT (Li et al., Online Time Series Forecasting with Theoretical Guarantees, NeurIPS 2025) as a Table 1 baseline:
run_ts.py with one more method, without touching run_ts.py (the harness, protocol, outputs and CLI are those of
run_ts.py). Registered adaptation: AMENDMENT_BASELINES_20261018.md item 2; P6 of the clean rerun.
- Official net: class `net` of exp/exp_LSTD_TOT.py in the authors' code (NeurIPS supplement, LSTD-TOT, read-only in
  ~/ext-baselines/TOT_neurips_supp/source_code/LSTD-TOT), mode "time", with the sizes of the ETTh2 pred_len-1
  configuration of LSTD_TOT_config.py: depth 9, hidden_dim 512, hidden_layers 1, tau 0.75, x_dim 3, L1_weight 1e-3,
  L2_weight 1e-3, lags 1, dropout 0, activation gelu; pred_len 1; enc_in = d (the stream's features); seq_len = L.
- Classification head: a linear layer on the latent representation that feeds the official forecaster, z_pred =
  [zs_pred, x_emb_pred, zd_pred] (pred_len 1: 3 x d values), taken at the input of net.regressor (a forward pre-hook,
  no change to the net). Learning steps use is_training = True (reparametrised samples, so the KL and Jacobian-sparsity
  identification terms act: there is no offline phase); prediction uses is_training = False (posterior means).
- Loss of a learning step: cross-entropy + MSE(x_rec, x) + the official other_loss (KL terms, L1, L2, sparsity), then
  AdamW (the official optimiser) step and net.store_grad() (the official online order: backward, step, store_grad).
- mech = lambda = zd_kl_weight = zc_kl_weight = sparsity_weight (official 1e-5).
- fires: memory triggers of the encoder's SamePadConv layers (as fsnet / onenet in run_ts.py).
Usage: as run_ts.py, with --method tot."""
import argparse, os, sys
from types import SimpleNamespace
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_ts                                                     # noqa: E402

TOT_DIR = f"{run_ts.EXT}/TOT_neurips_supp/source_code/LSTD-TOT"


class TOTCls(run_ts.Method):
    REPO = "TOT_neurips_supp/source_code/LSTD-TOT"

    def __init__(self, d, C, L, mech=None):
        super().__init__()
        from exp.exp_LSTD_TOT import net
        lam = 1e-5 if mech is None else float(mech)
        self.args = SimpleNamespace(hidden_dim=512, hidden_layers=1, dropout=0.0, depth=9, activation="gelu", lags=1,
                                    data="stream", enc_in=d, mode="time", seq_len=L, pred_len=1, x_dim=3, tau=0.75,
                                    zc_kl_weight=lam, zd_kl_weight=lam, sparsity_weight=lam, L1_weight=1e-3, L2_weight=1e-3)
        self.net = net(self.args, device=run_ts.DEV)
        self.head = nn.Linear(3 * d, C)
        self._z = None
        # the first regressor call of a forward is y = regressor(z_pred); the sparsity term calls it again inside
        # vmap(jacfwd(...)), which must not overwrite the captured z_pred
        self.net.regressor.register_forward_pre_hook(lambda mod, inp: None if self._z is not None else setattr(self, "_z", inp[0]))
        self.convs = [m for m in self.net.encoder.modules() if "PadConv" in type(m).__name__]
        from models.ts2vec import fsnet_
        assert self.convs and all(type(m) is fsnet_.SamePadConv for m in self.convs) and fsnet_.SamePadConv._counted

    def setup(self, lr):
        self.opt = torch.optim.AdamW(self.parameters(), lr=lr)

    def parts(self, x, is_training):
        self._z = None
        x_rec, _, other = self.net(x, is_training)
        assert self._z is not None and self._z.shape[1:] == (3, self.args.enc_in), self._z
        return self.head(self._z.flatten(1)), x_rec, other

    def forward(self, x):
        return self.parts(x, False)[0]

    def learn(self, x, y, steps):
        for _ in range(steps):
            logit, x_rec, other = self.parts(x, True)
            loss = F.cross_entropy(logit, y) + F.mse_loss(x_rec.float(), x.float()) + other
            loss.backward(); self.opt.step(); self.net.store_grad(); self.opt.zero_grad()

    def fires(self):
        return int(sum(getattr(m, "_n_trig", 0) for m in self.convs))


run_ts.METHODS["tot"] = TOTCls

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True); ap.add_argument("--out", required=True); ap.add_argument("--streams", nargs="+")
    ap.add_argument("--method", required=True, choices=["tot"]); ap.add_argument("--L", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3); ap.add_argument("--steps", type=int, default=1)
    ap.add_argument("--mech", type=float, default=None)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    torch.set_num_threads(1)
    sys.path.insert(0, TOT_DIR)
    run_ts._count_triggers()
    for s in a.streams:
        run_ts.run(a.data, a.out, s, a.method, a.L, a.lr, a.steps, a.mech)
