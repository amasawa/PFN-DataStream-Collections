Access to the clones under `/home/zhwu9808/ext-baselines` was denied, so the points below rest on the papers and the plan text, not on the code. Items marked **verify** need one look at the source.

**Decision.** The plan is registrable after four corrections: (1) all seven learners train online from batch 0, ADAPT-Z included, with the departure from its frozen base documented; (2) TOT is reproduced on OneNet with a native-task sanity check, else skipped; (3) L = 1 is removed for the four window methods and each method's one mechanism-critical hyper-parameter joins the dev grid; (4) Drift-Resilient TabPFN uses relative domain indices.

**Supporting evidence.**

(a) A pre-training prefix would give these seven methods labelled data the context strategies and MOOE never saw, breaking the Table 1 protocol. Training the base on the 100 warm-up rows and freezing it is a strawman. The faithful online analogue is: base, head and adapter all updated per batch, the adapter as in the official pseudo-code (delta in z-space from stored historical gradients). The paper's mechanism is the gradient-driven feature adjustment, not the frozen base, which is an artefact of its train/test split. For dtmoe and shifts the per-batch updates replace the epoch loop. The expert add/prune and MMD check run in the learning phase after labels, never at prediction. Footnote both as "offline forecasters run online".

(b) TOT: reproduce as a plug-in on OneNet, using only values stated in the paper. Before adapting to classification, run the reproduction once on one dataset and horizon from the paper's OneNet rows and require it to land within the paper's reported spread. If it does not, or a required hyper-parameter is missing from the paper, report skipped. Label the row "reproduced from paper, no official code".

(c) Corrections to the shared grid:
- L = 1 makes dtmoe's patching, shifts' positional mask, and fsnet/onenet's dilated convolutions degenerate. Offer L = 1 only for adaptz's MLP base. For the others use L in {16, 32}, and dtmoe's L must be at least its patch length (**verify** the default).
- n_steps in {1, 5} per 100-row batch is far less gradient signal than the official per-sample updates of fsnet, onenet and adaptz. Keep {1, 5} for parity with MOOE, but apply the boundary extension to 25 rather than stopping at 5.
- Each method's drift mechanism has one threshold calibrated for forecasting windows that may be inert on standardised tabular rows: dtmoe's MMD drift threshold, fsnet's adapter trigger tau, adaptz's gradient-history length, shifts' mask sparsity weight. Add that single parameter at three values around the official default, and log fire counts on the dev streams. A mechanism that never triggers is not a kept mechanism.
- RevIN in dtmoe and shifts subtracts the mean of the last L rows per feature. On tabular streams where the class depends on absolute feature values this removes the signal. Keep it, since it is the temporal-shift mechanism, but report it as a known handicap in the README.

(d) The official prior samples a handful of consecutive domain indices and tests on the next one. Absolute batch indices in the hundreds are likely outside that range. Use relative indices: context batches 0 to 9 oldest to newest, test rows 10. **Verify** whether the encoder normalises `dist_shift_domain` per call. If it does, absolute and relative coincide. One model via the official best-model selector matches the paper's main table. Ensembling the three is a reasonable sensitivity check but not the default.

**Alternative options.** An "adaptz-frozen" variant (base trained on batch 0 only) on the dev streams would document why the frozen setup is unusable. Per-row updates within each batch would match the official online regime exactly, at 100 times the cost.

**Key risks.** RevIN damaging class signal. Drift detectors silent on tabular rows. TOT reproduction failing silently and being reported as a weak method rather than a failed reproduction. Context padding for the first rows of batch 0: repeat the first row and say so.

**Remaining uncertainty.** Domain normalisation in Drift-Resilient TabPFN. Whether dtmoe's patch length and shifts' mask dimension fit L = 16. The exact stated hyper-parameters in the TOT paper.

**Confidence.** High on (a), (b), (c). Medium on (d) pending the normalisation check.

**Requires user approval.** Adding the mechanism-critical hyper-parameter axis beyond the MOOE grid. ADAPT-Z base updated online. The TOT native-task sanity check as a gate. Relative domain indices.
