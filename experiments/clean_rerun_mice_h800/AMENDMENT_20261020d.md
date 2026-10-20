# Amendment d of the clean MICE rerun, 2026-10-20: P3 limited to TabPFN-3.5 and TabDPT (committed and pushed
# before any P3 run; no P3 output exists)

## User decision (2026-10-20, verbatim, with the options)
The user wrote "骨干没必要跑那么多吧". The executor recalled Fable's advice of 2026-10-19
(MICE/logs/table1_fill/fable_backbones.md): two backbones are enough.
- TabPFN-3.5, the newest TabPFN. v2.5, v2.6 and v3 are intermediate versions of the same family.
- TabDPT, the only one with a different mechanism: retrieval inside the model makes the context query-dependent, and
  its real-data pretraining lets the theory predict a smaller gain, which is a falsifiable prediction.

Mitra and LimiX are synthetic-prior full-context transformers, the class that the TabICL check already covers.

Question: "P3 骨干减到几个？" Options:
- "TabPFN-3.5 + TabDPT (Recommended)";
- "只跑 TabPFN-3.5";
- "保留 7 个".

Answer: "TabPFN-3.5 + TabDPT (Recommended)". This replaces ACTIVATION user decision 6 ("7 个全测").

## What changes
- **Task list.** P3 runs from tasks_p3b.jsonl (make_tasks_p3b.py). It holds the lines of tasks_p3.jsonl, copied
  unchanged:
  - the 80 production tasks of tabpfn_v3.5 and tabdpt: sets results_heldout{3,4,4_e}_{tabpfn35,tabdpt};
  - their smoke tasks;
  - the TabPFN v2 reference smoke tasks.

  tasks_p3.jsonl is unchanged (sha256 checked) and is not run.
- **Every other rule of REGISTRATION_P3_P4_20261020 holds:** the settings, the smoke test and its exclusion rule, the
  probe, and the check_heldout4 hypotheses. Both remaining backbones are reported whatever their result.
- **Environments.** Only venv (TabPFN-3.5) and venv-tabdpt are needed for P3. venv-mitra and venv-limix are not built
  on the cluster. The P3 bundle's extra weights and the LimiX code stay unused.
- **Paper.** The robustness paragraph names the two backbones. The appendix states that seven were first
  registered and five were removed before any run, for redundancy with the TabICL check and for cost, by amendment of
  2026-10-20.

## Resources
P3 goes from about 300 to about 100 GPU process-hours. The whole rerun needs about 760-960 GPU process-hours, about
1.5-2 days of computation on 8 A800 (to be corrected by the first 30 minutes of cluster throughput).
