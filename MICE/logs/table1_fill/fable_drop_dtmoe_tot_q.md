# Question to Fable (decision maker): drop dtmoe and TOT from Table 1 of MICE? (one decision)
User request (2026-10-20, verbatim): "好，问 Fable 评估去掉 dtmoe 和 TOT" after the executor suggested it.
Context:
- MICE = mixture of in-context experts over a frozen tabular foundation model (TabPFN v2) for drifting streams; claim:
  recall the context of a recurring concept. Theory-driven paper (user rule: "self-consistent, theory-driven,
  phenomenon-guaranteed first, SOTA second; universal advantage over all baselines is point-chasing").
- Table 1 (92 streams) already has the context policies FIFO, LTM (Lourenco et al. KDD 2026), DDM reset, window
  ensemble, MICE variants; trained stream learners (ARF, SRP, HAT, LevBag, AdwinBag, NSE, MOOE); and new baselines
  registered on 2026-10-18 (experiments/mice_table1_fill_20261018/PLAN_BASELINES.md, user request "表 1 补齐数据需求"):
  Drift-Resilient TabPFN (NeurIPS 2024), and six online time-series forecasting methods adapted to streaming
  classification (fsnet ICLR 2023, onenet NeurIPS 2023, adaptz ICLR 2026, shifts ICLR 2026, dtmoe ICML 2026, TOT
  NeurIPS 2025): head replaced by a classifier, online per-batch updates, tuned on 5 development streams.
- fsnet/onenet/adaptz/shifts run on CPU (cheap; were never on the faulty GPU). dtmoe needs the A800 in strict
  deterministic mode (locally >= 40x slower than default; dev grid >= 150 GPU-h + tests 100-300). TOT needs gate (a)
  (paper reproduction), gate (b), a cost check, then dev (~190 GPU-h) + tests (100-300); its adaptation is a
  registered deviation (identification terms active per step, head on the latent). Together ~550-950 of ~1250-1650
  GPU process-hours of the whole rerun.
- No dtmoe or TOT score exists or was read (dtmoe: only determinism probes, scores not read; TOT: nothing run).
- Cluster: 8 A800, 7 cores per GPU.
Options:
 A. Drop both (registered but not run: "not related to the claim; cost"), keep DR-TabPFN and the 4 CPU TS baselines.
 B. Keep both as registered.
 C. Drop one (which?).
 D. Drop all six TS forecasting baselines (keep only DR-TabPFN as a new baseline).
Questions: which option, and how the paper should state it so a reviewer does not read it as hiding baselines.
Format: Decision / Supporting evidence / Alternatives / Key risks / Confidence / Requires user approval. At most 15
lines. Answer in Chinese.
