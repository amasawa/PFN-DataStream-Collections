**Decision**

Approve the amendment with three corrections: (a) put the softmax head on the latent representation (posterior means of z, or the penultimate hidden state), not on the 1-step forecast y, whose dimension equals the feature count and would bottleneck classification while being inconsistent with the other baselines' "replace the forecasting head" adaptation; (b) make the mechanism parameter a single identification scale λ applied jointly to zd_kl = zc_kl = sparsity_weight, λ ∈ {1e-6, 1e-5 (official), 1e-4}; (c) keep a reduced gate rather than dropping it.

**Supporting evidence**

- Official online phase uses is_training=False because an offline phase already fit the identification terms. With no prefix, False would make TOT a plain latent autoencoder plus forecaster. True in learning steps and False at prediction is the standard VAE train/eval convention and is the only way the paper's defining terms act.
- Loss CE + MSE(x_rec, x) + other_loss with official weights, tau, L1/L2 is the faithful transfer. Keep store_grad.
- λ captures "how much TOT" in one knob. Beta alone is a generic VAE weight; sparsity alone is the paper-specific term. Scaling both avoids choosing.
- LSTD backbone is the released code; OneNet was a guess made without code. Record as a registered-plan deviation.

**Alternative options**

- Beta-only as mechanism parameter if λ is judged too coarse.
- Official-style False in learning steps, reported explicitly as "TOT without identification", which I do not recommend as the main row.

**Key risks**

- vmap(jacfwd) sparsity per step with depth 9 and n_steps 5 may be slow. Measure one batch before the grid.
- Reconstruction and KL may dominate CE early with no warm-up. Standardize features as for other baselines.
- Head placement and x_dim must adapt to each stream's feature count. Only latent sizes transfer from ETTh2.

**Remaining uncertainty**

Whether official weights tuned for forecasting MSE transfer to CE scale. The λ grid partially covers this.

**Gate (recommended)**

1. Run the released code unchanged on ETTh2 pred_len 1, one seed. Pass if within the paper's reported spread. Verifies code and environment, cheap.
2. Internal check: λ = 0 versus official must produce different predictions. Otherwise the identification path is dead.

**Confidence**

High on (1), (2), head placement. Medium on λ versus beta. 

**Requires user approval**

Yes. Backbone swap and gate replacement alter a registered plan.
