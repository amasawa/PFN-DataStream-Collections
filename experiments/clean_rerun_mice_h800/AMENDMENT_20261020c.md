# Amendment c of the clean MICE rerun, 2026-10-20: TOT removed, dtmoe at its default drift threshold (committed and
# pushed before any TOT run and before any dtmoe development run; no TOT or dtmoe score has been read)

## User decisions (2026-10-20, verbatim, with the options)
1. User request: "好，问 Fable 评估去掉 dtmoe 和 TOT".
   - Fable (MICE/logs/table1_fill/fable_drop_dtmoe_tot_a.md) recommended removing TOT and keeping dtmoe. dtmoe is the
     Table 1 baseline closest to MICE's mechanism (expert addition and pruning, temporal memory routing, drift
     detection, official code); removing it alone would read as hiding a baseline.
   - Sonnet (sonnet_drop_dtmoe_tot.md) corrected Fable's facts:
     - TOT has official code (the NeurIPS supplement; our adapter uses its net);
     - no registered rule excludes a method whose gates were not run, so removing TOT is a protocol change, not the
       execution of a rule.
2. Question: "Fable 建议去掉 TOT、保留 dtmoe……怎么定？" Options:
   - "去掉 TOT (Recommended)";
   - "保留 TOT";
   - "dtmoe 和 TOT 都去掉".

   Answer: "去掉 TOT (Recommended)".
3. Question: "dtmoe 的开发网格怎么跑？" Options:
   - "完整网格 (Recommended)";
   - "只用默认漂移阈值".

   Answer: "只用默认漂移阈值".

## 1. TOT is removed
- **Reason.** Cost: on the A800, about 290-490 GPU-hours for development and tests, the most expensive baseline. Also,
  its registered adaptation departs the most from the authors' use: identification terms active in every step, and
  the classifier on the latent.
- **Status.** TOT was registered (AMENDMENT_BASELINES_20261018 item 2, REGISTRATION_P6_GATE_A_20261020,
  AMENDMENT_20261020b item 3) but never run. Nothing of tasks_p6.jsonl runs: gate (a), the check, the 180-task grid.
  TOT has no stage 2. The adapter (run_ts_tot.py), tot_check.py and the gate script stay in the repository, unused.
- **Paper.** One sentence (appendix and the Table 1 note): "TOT (NeurIPS 2025) was registered as a baseline but not
  run: an amendment of 2026-10-20 removed it for its cost (about 300-500 GPU-hours), before any TOT or dtmoe score was
  read."

## 2. dtmoe: development grid at the default drift threshold only
- **Grid.** drift_k_sigma = 2 (the model default) only. This gives lr {1e-4, 1e-3, 1e-2} × n_steps {1, 5} × L
  {16, 32} = 12 configurations × 5 development streams = 60 tasks.
  - They are the 60 tasks of set dtmoe_dev of the frozen tasks.jsonl with "--mech 2", copied unchanged into
    tasks_dtmoe.jsonl (make_tasks_dtmoe.py). tasks.jsonl is unchanged (sha256 checked).
  - P1 production keeps `--exclude-sets dtmoe_dev`. dtmoe development runs only from tasks_dtmoe.jsonl, after its
    probe cap verdict and the user's decision (ACTIVATION item 2).
- **Unequal tuning.** The other four TS baselines tune their mechanism parameter over 3 values and dtmoe does not.
  This is a stated difference of treatment, chosen by the user for cost. The paper states it with dtmoe's row: "dtmoe
  at its default drift threshold".
- **Probe.** The determinism probe and the 10× cap (HANDOFF step 3) use the m2 counterparts of the registered probe
  ids, so that the probe measures configurations that run:
  - `dtmoe_dev:elec2__dtmoe_L16_lr0.0001_s1_m2`;
  - `dtmoe_dev:elec2__dtmoe_L32_lr0.0001_s1_m2`;
  - `dtmoe_dev:insects_abrupt_balanced__dtmoe_L32_lr0.001_s5_m2`.

  These ids are in tasks.jsonl, so qualify and ref find them without --tasks.
- **Selection.** select_frozen.py keeps only drift_k_sigma = 2 for dtmoe and expects 12 configurations (the extended
  grid: the boundary rule of amendment c with 2 configurations per (lr, n_steps)). Other methods are unchanged: 36
  configurations; tested on synthetic outputs.
- **Extension and tests.** make_tasks_stage2.py generates dtmoe's extension with mech 2 only (self-test updated).
  Everything else of REGISTRATION_STAGE2_20261020 holds.

## Resources after this amendment
- About 960-1160 GPU process-hours remain, against about 1250-1650 before. On 8 A800 with 7 cores per GPU, that is
  about 2-2.5 days of computation, to be corrected by the first 30 minutes of cluster throughput.
