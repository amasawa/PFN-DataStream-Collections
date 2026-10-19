# Phases P3 (extra backbones) and P4 stage 1 (CURE development runs) of the clean MICE rerun (registered 2026-10-20,
before any P3 or P4 run on the cluster)

Binding: ACTIVATION_20261019.md sections "Extra backbones" and "CURE", AMENDMENT_20261020.md, and the decisions below.
Records: draft PLAN_P3_P4_draft.md; Fable MICE/logs/table1_fill/fable_p3p4_a.md and fable_p3p4_a2.md; Sonnet
sonnet_p3p4.md; MiMo audits p3p4_mimo.md.

## User decisions (2026-10-20, verbatim, with the options offered)
1. CURE's tau. Question: CURE's tau has no default for our setting; its authors set it per dataset (TabICL, row-wise
   immediate labels); 7 Table 1 streams (NOAA weather, Rialto, 5 PokerHand) come from those datasets; ACTIVATION said
   "published defaults, no tuning". Options:
   - "开发流选一个": one tau for all 92 streams, selected on the 5 development streams from 0.1-0.4 by mean accuracy,
     ties to 0.3, two-stage registration, the same treatment as the other tuned baselines;
   - "固定 0.3，不调";
   - "7 条用公开值，其余开发流选".

   Answer: "开发流选一个 (Recommended)".
2. Appendix sensitivity runs with the published taus on those 7 streams. Options: "不加" / "加". Answer: "不加 (Recommended)".

Decision 1 replaces the sentence "Hyperparameters: CURE's published defaults; no tuning" of ACTIVATION "CURE" by this
rule: CURE's published defaults, except tau, which has no default for this setting (backbone, batch arrival, our
segmentations). tau is one value for all streams, selected on the five development streams of the Table 1 baselines
by their rule, and registered in two stages: this note fixes the procedure and the tie rule before the development
runs; the frozen value is registered before any test-stream run. The published per-dataset taus are not used. The
paper states that 7 streams come from datasets with a published tau, and why it is not used: it was set with another
backbone and protocol, and possibly on the same data.

## P3: backbones (tasks_p3.jsonl, make_tasks_p3p4.py)
| backbone (P3_BACKBONE) | package, venv | weights (P3_WEIGHTS = {W3}), sha256 | source commit |
|---|---|---|---|
| tabpfn_v2.5 | tabpfn 9.0.0, venv | tabpfn/tabpfn-v2.5-classifier-v2.5_default.ckpt 5d7170e2… | HF Prior-Labs/tabpfn_2_5 6c45f3a |
| tabpfn_v2.6 | tabpfn 9.0.0, venv | tabpfn/tabpfn-v2.6-classifier-v2.6_default.ckpt 0578fa56… | HF Prior-Labs/tabpfn_2_6 2414887 |
| tabpfn_v3 | tabpfn 9.0.0, venv | tabpfn/tabpfn-v3-classifier-v3_default.ckpt d0d865d5… | HF Prior-Labs/tabpfn_3 24a16a8 |
| tabpfn_v3.5 | tabpfn 9.0.0, venv | tabpfn/tabpfn-v3.5-20260909.safetensors ece4d67e… | HF Prior-Labs/tabpfn_3_5 06bf2ba |
| tabdpt | tabdpt 1.3.1, venv-tabdpt (env_lock/tabdpt.txt) | tabdpt/tabdpt1_3.safetensors 97dc3b60… | HF Layer6/TabDPT a5ca6e0 |
| mitra2 | autogluon.tabular 1.6.3, venv-mitra (env_lock/mitra.txt) | mitra-classifier-2/model.safetensors 5ffab0e2… | HF autogluon/mitra-classifier-2 edada0d |
| limix2 | LimiX code 516bf39, venv-limix (env_lock/limix.txt, torch 2.9.1) | limix-2/LimiX-2.ckpt ed01f7a0… | HF stable-ai/LimiX-2 de07b67 |

The full hashes are in the bundle (mice_h800_bundle_p3, p3_weights.tar.files.sha256).

- **Settings** (Fable, before coding):
  - Every backbone has 4 ensemble members, as TabPFN v2 and TabICL in run.py. For the TabPFN versions,
    n_estimators = 4 and not the package's "auto" of v3 and later; v3.5, not v3.5-fast.
  - TabDPT: n_ensembles = 4, full context, compile = False (as ResetEval).
  - Mitra: fine_tune = False, so the backbone stays frozen as MICE requires; its default fine-tunes on every context.
    n_estimators = 4; the four members differ (measured).
  - LimiX-2: the no-retrieval classification config, with 4 of its 32 pipelines (members), evenly spaced over the list
    (0, 8, 16, 24), so the four cover the config's range of preprocessing rather than its first entries (MiMo P3
    finding 1). The member count is the length of the list (LimiXPredictor.n_estimators); the subset takes effect
    (probabilities differ from the first four by up to 0.10, and from all 32 by up to 0.06, on one context).
  - The paper states the package defaults that were not used, and why.
- **Adapter.** MICE/code/run_backbone.py replaces run.TFM, as run_seed.py does. Policies, constants and outputs are
  those of run.py (unchanged since 2026-10-15). Inputs are raw. A one-class context gives a one-hot prediction. The
  non-TabPFN backbones get labels 0..k-1, and their columns are mapped back.
  - Two monkeypatches are applied once per process and change no computation. Mitra's from_pretrained is cached,
    which is safe because the weights do not change: the state-dict hash is the same before and after fit, and the
    model stays in eval mode. LimiX's unused cache directory moves from a hard-coded /mnt/public to one temporary
    directory.
  - Mitra seeding. Mitra's preprocessing draws from the global `random` and `np.random` (feature mirroring and
    permutations), which its interface no longer seeds (AutoGluon >= 1.4). Unseeded, two predictions on the same
    context differed by up to 0.09. Each call therefore seeds `random`, `np.random` and torch with the backbone seed,
    as TabPFN's fixed random_state does per fit, and restores the caller's state afterwards. The four members still
    get different draws within a call.
  - HF_HUB_OFFLINE = 1 is set by the adapter; the weights come only from P3_WEIGHTS.
- **Adapter checks** (local, before registration; no stream accuracy computed):
  - toy separable problem (3 of 6 labels): every backbone is 100 % correct and puts zero mass on absent labels;
  - two fresh processes on the same real context (h3_covertype_b, 1000 rows) give bit-identical probabilities for
    all 7 backbones (Mitra after the seeding above);
  - Mitra's weights are unchanged by fit.
- **Protocol.** That of the TabICL check of P1:
  - segments: h3_airlines_b, h3_covertype_b, h3_insects_b, h3_poker_b, h4_*_d and h4_*_e (10 segments);
  - policies: ddm1000, fifo1000, micev1000_500, winens1000;
  - B = 100, backbone seed 0.

  Per backbone, 40 tasks (280 in all). Each output set is results_heldout3_<tag>, results_heldout4_<tag> or
  results_heldout4_<tag>_e.
- **Hypotheses and analysis.** The four checks of MICE/code/check_heldout4.py (pre-registrations J and M), with its
  method (two-timescale rule, half Brier, step 1/2, tempered), applied to each backbone's three directories; majority
  as in the script (3 of 4, 4 of 6). The only change is the directory mapping, made in a wrapper registered before
  the analysis. Every listed backbone is reported, whatever its result (ACTIVATION).
- **Smoke test and exclusions** (set p3_smoke, exclusive: one process alone on an H800, run first).
  - What is run: 8 backbones (the 7 plus the TabPFN v2 reference) × h3_covertype_b (54 features, 7 classes) and
    h3_poker_b (9 classes). Each run makes 20 calls on FIFO contexts of 1000 rows under a 28 GB cap
    (torch.cuda.set_per_process_memory_fraction).
  - What it writes: time per call, peak memory and the error, if any. No accuracy.
  - When a backbone is excluded, before any of its P3 tasks runs:
    - its smoke run records an error that comes from loading the weights offline, from the class or feature count,
      or from running out of memory under the cap;
    - or, on either segment, its median time per call (calls 2-20) is more than 20 times that of TabPFN v2 on the
      same segment.

    The exclusion and its evidence are logged and pushed. The backbone's sets are then given to `--exclude-sets`.
  - Measured locally (RTX 5000 Ada, h3_covertype_b), as information only: ratios to TabPFN v2 of 1.7 (v2.5, v2.6),
    3.1 (v3), 7.2 (v3.5), 0.9 (TabDPT), 6.7 (Mitra, after the load cache was fixed; 16.5 before) and 3.8 (LimiX-2).
- **Determinism probe.** Before production, one qualify per backbone on `results_heldout4_<tag>:h4_airlines_d__fifo1000`
  (two fresh runs, bit-identical). A NOT QUALIFIED backbone is paused, as in PLAN.md. Its disposition is registered
  with the user, as for P1.

## P4 stage 1: CURE development runs (tasks_p4.jsonl)
- **Adapter.** experiments/mice_table1_fill_20261018/run_cure.py. CURE's CUREMemoryPolicy is imported unchanged from
  its code (commit f7c6b2f), with budget_B = 1000 and short_ratio = 0.75 (its defaults; 1000 = M of Table 1).
  - Backbone: the TabPFN v2 of Table 1 (run.TFM).
  - Protocol: Table 1's (B = 100, labels one batch late, batch 0 warm-up).
  - Signal per row: the probabilities predicted for that row before its label, over the classes of the context
    (CURE's entropy normalisation). Rows are appended in stream order after the batch is scored.
  - Recorded per batch: memory sizes and the counts left / gate / warm (long-bank admission rate).
  - Checkpoint every 25 batches; a resumed run is identical (tested).
- **Tasks.** tau ∈ {0.1, 0.2, 0.3, 0.4} (the published values) × the five development streams of the Table 1
  baselines (elec2 and four INSECTS streams), into {RUNS}/mice-table1-newbase/cure_dev/P. 20 tasks.
- **Selection rule** (fixed now, before any run):
  - Choose the highest mean development accuracy over the five streams (accuracy of a stream = mean over its scored
    batches).
  - Ties (equal means) go to 0.3, then to the smaller tau.
  - No extension of the range: it is the published range.
  - A tau with a missing or given-up stream is not eligible. If none is eligible, the coordinator stops and asks the
    user.
  - The selection reads only the five development outputs. It is committed and pushed, with every mean, before any
    test task exists.
- **Stage 2** (later, its own registration): CURE with the frozen tau on the 92 Table 1 streams (data as the other
  Table 1 baselines). Every cell is reported, and no registered hypothesis names CURE.

## Runner and inputs
- rerun.py has new placeholders PYDPT, PYMITRA, PYLIMIX (venvs) and W3 (weights directory). tasks.jsonl and
  tasks_p2.jsonl are unchanged (sha256 checked).
- The supplement bundle `mice_h800_bundle_p3` on the Windows desktop holds:
  - p3_weights.tar: the weights, urls.txt (pinned commits), SHA256SUMS;
  - ext-baselines-p3.tar: LimiX 516bf39 and CURE f7c6b2f (without its data directory);
  - per-file hashes and COMMITS.txt.
- The venvs are built from env_lock/tabdpt.txt, mitra.txt and limix.txt. LimiX is installed editable from
  $WORK/home/ext-baselines/LimiX.
