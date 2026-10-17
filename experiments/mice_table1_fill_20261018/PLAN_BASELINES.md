# New baselines for Table 1 (registered when committed, before any development or test run)

Request: user, 2026-10-18 (merged request, section 3). Expert review: Fable 5.1, 2026-10-18 10:47-10:49
(MICE/logs/table1_fill/fable_baselines_question.txt, fable_baselines_review.md); its four corrections are adopted
below. The user asked on 2026-10-18 for "plan -> Fable review -> run -> Sonnet check, iterate" and is away; the
choices Fable marked "requires user approval" (ADAPT-Z base trained online, the mechanism axis of the grid, the TOT
gate, relative domain indices) are taken on that instruction and listed for the user in the README.
All results are descriptive Table 1 entries; no registered hypothesis is re-decided.

## Sources (checked 2026-10-18; shallow clones in ~/ext-baselines, read-only)
| name | paper, venue | code |
|---|---|---|
| drtabpfn | Helli et al., Drift-Resilient TabPFN, NeurIPS 2024 | automl/Drift-Resilient_TabPFN a6e75af, weights in the repo |
| dtmoe | Dynamic TMoE, ICML 2026 (arXiv 2605.20678) | andone-07/Dynamic-TMoE 3e41235 |
| adaptz | Online time series prediction using feature adjustment (ADAPT-Z), ICLR 2026 | xiannanhuang/ADAPT-Z f5b70e1 |
| tot | Online Time Series Forecasting with Theoretical Guarantees, NeurIPS 2025 (arXiv 2510.18281) | none found (paper, arXiv html and NeurIPS page searched): reproduced from the paper, gated (below) |
| onenet | OneNet, NeurIPS 2023 | yfzhang114/OneNet 65eed9d |
| fsnet | Learning Fast and Slow for Online TS Forecasting, ICLR 2023 | salesforce/fsnet c776afc |
| shifts | Tackling TS Forecasting Generalization via Mitigating Concept Drift, ICLR 2026 | AdityaLab/ShifTS 0589ecb |

## Protocol (as every method of Table 1)
Prequential, B = 100 rows; batch t is predicted with the state after learning batches < t, then its labels are
revealed and learned; batch 0 is warm-up (learned, not scored); seed 0. No method gets a pre-training prefix: every
model starts from its initialisation at batch 0. Probabilities per row are stored; metrics as for the other methods.

## drtabpfn (no training, no tuning)
Official package in its own venv (torch 2.1, scikit-learn < 1.6), model tabpfn_dist_model_1 through the official
get_best_tabpfn(task_type = "dist_shift_multiclass", model_type = "best_dist"), its default inference settings. Batch t:
context = the 1000 most recent labelled rows (rows of batches t-10..t-1), dist_shift_domain = batch index relative to
the oldest context batch (0..9; test rows 10). The model min-max scales the domain per call
(scripts/model_builder.py, MinMaxScalingEncoderStep, normalize_on_train_only), so relative and absolute indices give
the same input. One call per batch. Limits (utils.default_task_settings: 10 classes, 500 features, 10000 samples): every
stream is inside. Inputs passed raw (the package preprocesses them).

## Time-series methods: shared adaptation
- Row context: features (never labels) of the L most recent rows up to and including the row predicted, stream
  order, L x d; the first rows of batch 0 are padded by repeating the first row. Inputs standardised with the warm-up
  batch mean / std, clipped to [-10, 10] (as MOOE).
- Head: the method's output representation -> linear -> C logits; softmax + cross-entropy replaces the forecasting
  loss everywhere (including the losses that drive the method's own online mechanisms).
- Learning: after each revealed batch, n_steps Adam steps on its 100 rows (per-batch, since labels arrive per batch).
- Offline forecasters (dtmoe, shifts) and ADAPT-Z run online: per-batch updates replace the epoch loop; ADAPT-Z's
  base, head and adapter are all updated (its official frozen base is an artefact of its train / test split; a frozen
  base trained on 100 rows would be a strawman); dtmoe's MMD check and expert add / prune run in the learning phase,
  never at prediction; its router is not updated at prediction.
- Official modules imported from the clones; every change is listed in the README.

## Per method: kept mechanism, mechanism parameter
- fsnet: TSEncoder with per-layer adapters (fast) and associative memory triggered by gradient disagreement
  (cos < -tau), backbone (slow). Mechanism parameter tau in {0.5, 0.75 (official), 0.9}.
- onenet: two fsnet branches (time: L x d; cross-variable: d x L); combination weight sigmoid(w) updated by the
  combination loss plus the decision-MLP bias (exp_onenet_fsnet.py); probabilities combined. Mechanism parameter: the
  branches' tau in {0.5, 0.75, 0.9}.
- dtmoe: TemporalDynamicMoELayer (RevIN, patches over the window per feature, MMD drift detector, expert add / prune,
  temporal memory router with anomaly repository). patch_len and stride scaled to L with the official ratios
  (seq_len 96, patch_len 48, stride 12 -> L/2, L/8). Drift-expert pre-training: one pass over its ref / cur data.
  Mechanism parameter drift_k_sigma in {1, 2 (model default), 3}.
- shifts: RevIN over the window (temporal shift first), then the Soft Attention Mask over the window positions per
  feature (parameter-free threshold at the mean), the current row being the observed "horizon"; backbone MLP -> C.
  The official loss is forecast loss + SAM selection loss with an implicit weight 1 (exp_causal_forecasting.py);
  mechanism parameter: the SAM-loss weight in {0.5, 1 (official), 2}. (Fable named a "mask sparsity weight"; the
  official code has none.)
- adaptz: base encoder + adapter producing a delta in z-space from the current representation and the previous
  batch's gradient with respect to z (official pseudo-code). L = 1 allowed (MLP base on the current row). The official
  code uses the previous batch's gradient (no history length, which Fable named); mechanism parameter: adapter_lr in
  {1e-4, 1e-3 (official), 1e-2}.
- tot: plug-in on onenet as the paper's OneNet rows, values only from the paper. Gate: before the classification
  adaptation, the reproduction runs once on one dataset and horizon of the paper's OneNet+TOT rows; it must land within
  the paper's reported spread (or within 10% of its MSE if no spread is reported). If it fails, or a required
  hyper-parameter is not in the paper, tot is reported as skipped ("no official code, reproduction did not match").
- Known handicap (README): RevIN (dtmoe, shifts) removes the window mean per feature, which can remove class signal on
  tabular rows; kept, being the method's temporal-shift mechanism.
- Fire counts of every drift mechanism (memory triggers, MMD detections, experts added / pruned) are logged.

## Tuning (development streams of MOOE: elec2, insects abrupt / gradual / incremental / reoccurring balanced, which
## are also among the 29 real streams, as for MOOE)
Grid: lr in {1e-4, 1e-3, 1e-2} x n_steps in {1, 5} x L in {16, 32} (adaptz: L in {1, 16}) x the mechanism parameter
(3 values where listed). Highest mean development accuracy frozen (ties: first in sorted order); if the best lies on
the boundary of lr or n_steps, the grid is extended once (lr x 10 or / 10; n_steps 25) and re-selected. Then one run
per test stream and set. A mechanism that never fires on the development streams at the frozen setting is reported.

## Execution, order, timing
Order: drtabpfn; dtmoe, adaptz, tot; onenet, fsnet, shifts; per method real and confirm first, then grid and
generator. CPU processes for the neural methods (the GPU shows fault storms under shared load); drtabpfn on the GPU
(at most 2 GPU processes in total). Timing: seconds per batch and peak GPU memory on the three real prefixes of the
MICE resource benchmark. Outputs: ~/pfn-runs/mice-table1-newbase/<method>/; read-out into
MICE/results_paper/table1_full/ and ~/Desktop/MICE_table1_full/.
