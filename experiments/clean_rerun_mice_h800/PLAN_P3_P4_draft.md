# DRAFT (not registered): phases P3 (extra backbones) and P4 (CURE) of the clean MICE rerun

Status: a draft for expert review (Fable, then Sonnet) before any adapter is written. ACTIVATION_20261019.md already
fixes the scope and the reporting rules of P3 and P4. This draft fixes the open settings. After the review, the
adapters are written, audited by MiMo Pro high and smoke-tested, and then P3 and P4 are registered.

## Facts checked 2026-10-20
- **TabPFN.** tabpfn 9.0.0 (main venv) has ModelVersion v2, v2.5, v2.6, v3, v3.5 and v3.5-fast. The weights are on
  Hugging Face, not gated (HTTP 206 on a range request; licence "other", non-commercial):
  | version | repository | file |
  |---|---|---|
  | v2.5 | Prior-Labs/tabpfn_2_5 | tabpfn-v2.5-classifier-v2.5_default.ckpt |
  | v2.6 | Prior-Labs/tabpfn_2_6 | tabpfn-v2.6-classifier-v2.6_default.ckpt |
  | v3 | Prior-Labs/tabpfn_3 | tabpfn-v3-classifier-v3_default.ckpt |
  | v3.5 | Prior-Labs/tabpfn_3_5 | tabpfn-v3.5-20260909.safetensors |

  `create_default_for_version` sets n_estimators = "auto" for v3 and later.
- **TabDPT.** tabdpt 1.3.1 is installed in ~/pfn-venvs/venv-tabdpt (torch 2.14.0+cu126). The weights are
  Layer6/TabDPT tabdpt1_3.safetensors (Apache-2.0). ResetEval already has a wrapper (ResetEval/code/reset_eval.py:55-76):
  compile = False, labels remapped to 0..k-1, ensemble_predict_proba(n_ensembles = 4, seed).
- **Mitra-v2.** The model is autogluon/mitra-classifier-2 (Hugging Face, 2026-09-07, Apache-2.0), used through
  autogluon.tabular 1.6.3 (MitraClassifier, sklearn interface). Its defaults are fine_tune = True (50 steps of
  fine-tuning in every fit), n_estimators = 1, max_samples_support 8192, and at most 10 classes.
- **LimiX.** The code is limix-ldm-ai/LimiX (latest commit 516bf39, 2026-09-18), with the entry point LimiXPredictor.
  It needs Python 3.12 and torch 2.9.1; flash-attn is optional. There are three checkpoints:
  | checkpoint | parameters | released |
  |---|---|---|
  | LimiX-2 | 400M | 2026-09-16 |
  | LimiX-16M | 16M | 2025-08 |
  | LimiX-2M | 2M | 2025-11 |

  The weights are on Hugging Face under stable-ai/ (non-commercial licence). The README uses the config
  cls_default_noretrieval_v2.json; a retrieval config also exists.
- **CURE.** Code at morcellinus/CURE-ICML-FMSD, commit f7c6b2f (2026-06-04, 1426 lines). Read in full; the main facts:
  - Backbone: TabICL v2 (tabicl 2.0.3, checkpoint tabicl-classifier-v2-20260212), with n_estimators = 1.
  - Updates are row by row with immediate labels: predict one row, then append it.
  - Memory: budget_B = 1000 split into a short FIFO of 750 rows (short_ratio 0.75) and a long bank of 250.
  - When a row leaves the short memory, it enters the long bank if the long bank is still below capacity (warm-fill),
    or if the normalised entropy of the prediction made for that row is at least tau. Otherwise it is dropped.
  - Long-bank eviction: in the majority class of the long bank, take the nearest pair of rows (on jointly
    standardised features). Of the two, drop the one farther from the class centroid of the short memory.
  - tau is set per dataset in config/expected_main_taus.json: noaa 0.4, meter 0.1, rialto 0.1, posture 0.2,
    nomao 0.3, poker 0.3, agr_a 0.4. The paper and code define no tau for other data.
  - CURE is the dual memory of Lourenco et al. (LTM, our ltm1000_75: short 750, long 250) with an entropy gate on
    admission and redundancy-aware eviction instead of class-balanced eviction.
- **Protocol to reuse.**
  - The P3 protocol is the TabICL check: the held-out sets 3 (4 segments) and 4 (6 segments); the policies ddm1000,
    fifo1000, micev1000_500 and winens1000; run.py with MICE_BACKBONE; 4 policies x 10 segments = 40 tasks per
    backbone, 280 in all. On the local GPU the TabICL check took about 12 h for its 40 tasks.
  - The P4 protocol is Table 1: 92 streams (83 main and 9 confirmation segments), B = 100, labels one batch late,
    batch 0 as warm-up, TabPFN v2 with 4 estimators, backbone seed 0, and probabilities per row (as
    run_drtabpfn.py).

## Proposed settings (each one a question for review)
### P3
1. **TabPFN v2.5, v2.6, v3, v3.5.** `create_default_for_version(V, n_estimators = 4, ignore_pretraining_limits =
   True, random_state = seed)`. This uses the same estimator count as TabPFN v2 and TabICL in MICE. The alternative
   is the package default "auto" for v3 and later. Use v3.5, not v3.5-fast.
2. **TabDPT 1.3.1.** The ResetEval wrapper: full context, n_ensembles = 4, seed = backbone seed, compile = False,
   tabdpt1_3 weights. It runs in venv-tabdpt.
3. **Mitra-v2.** fine_tune = False, so the backbone stays frozen, as MICE's definition requires (every policy uses
   the same frozen backbone). n_estimators = 4, hf_model = the local copy of mitra-classifier-2. The package default
   (fine-tuning in every fit) would make the backbone a learner trained on each context. It runs in its own venv
   (autogluon.tabular[mitra] 1.6.3).
4. **LimiX.** LimiX-2 (400M, the current release, as v3.5 for TabPFN), with the README classification config
   cls_default_noretrieval_v2.json. Retrieval would make the context query-dependent; TabDPT already covers that
   axis. It runs in its own venv (torch 2.9.1, no flash-attn, for determinism and simpler installation).
5. **Shared rules.**
   - Inputs are passed raw, as for TabPFN v2.
   - A single-class context gives a one-hot prediction (TFM.predict), as now.
   - The class columns are mapped back to the global label set, as in TFM.predict.
   - The backbone is selected by MICE_BACKBONE in run.py (TFM.__init__ and predict only). No policy code or constant
     changes.
   - Outputs go to results_heldout{3,4,4_e}_<backbone>.
6. **Smoke test.** First a local functional check: one segment, a few batches, outputs discarded; it confirms the
   adapter runs and the probabilities sum to 1. Then the H800 smoke test of ACTIVATION, which measures time per batch
   and peak memory under the 28 GB cap and stores no accuracy. Exclusions follow ACTIVATION.

### P4 (CURE)
7. **Adapter.** A new driver, run_cure.py, in the style of run_drtabpfn.py. It imports CUREMemoryPolicy from the
   clone (commit f7c6b2f), unchanged.
   - Batch t >= 1 is predicted from `memory.arrays()` (at most 1000 rows) with the Table 1 TabPFN v2 (4 estimators,
     seed 0), in one call per batch.
   - When the labels of batch t arrive, its rows are added in stream order. For each row, record_prediction_signal
     gets the probabilities predicted for that row, then append_then_evict runs.
   - The rows of batch 0 are not predicted and get no signal (entropy 0), as CURE's own warm-up rows. The warm-fill
     bypass applies to them in the same way.

   This is the only change from CURE's protocol: labels arrive per batch instead of per row. The admission signal is
   still the entropy of the prediction made for that row before its label was known.
8. **tau (no published default).** This is the main question. The options:
   - (a) the median of the published values, tau = 0.3;
   - (b) select tau from the published set {0.1, 0.2, 0.3, 0.4} on the five development streams of the Table 1
     baselines, with their selection rule (mean accuracy), then freeze it before any test stream. This is tuning,
     which ACTIVATION says CURE does not get, but it is the same treatment as the other tuned baselines;
   - (c) run all four values on every stream and report all four rows, with no choice;
   - (d) a value derived from the entropy distribution, which needs a rule of our own.

   Proposal: (a), recorded as "undefined default; median of the published per-dataset values; no tuning", with the
   reason written in the P4 registration (as ACTIVATION requires). The cost is about one Table 1 policy (about
   ltm1000_75).
9. **Backbone.** TabPFN v2, as registered (the main table's backbone). CURE was tuned with TabICL, and the entropy
   scale differs between backbones. That is a limit of any fixed tau, and it is stated with the result.
10. **Outputs.** Per-batch acc, P (float32), pred, wt, te, peak_mem, plus the memory sizes per batch. A checkpoint
    every 25 batches (atomic). Tasks go into tasks_p4.jsonl for the H800 (gpu "shared").

## Order of work
1. Download the weights here, with sha256: the TabPFN v2.5, v2.6, v3, v3.5 checkpoints, tabdpt1_3, mitra-classifier-2
   and LimiX-2.
2. Create the venvs for Mitra and LimiX; write env_lock files.
3. Write the adapters and run_cure.py.
4. Run the local functional checks, one GPU process at a time.
5. MiMo Pro high audits: one for the P3 adapters, one for run_cure.py, in parallel.
6. Register P3 and P4 (task lists tasks_p3.jsonl and tasks_p4.jsonl, HANDOFF sections). Bundle the weights to the
   desktop and push.
7. The H800 smoke test (time and memory) runs first on the cluster; exclusions are logged; then production.
