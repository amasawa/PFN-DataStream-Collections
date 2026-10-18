# Amendment b to PLAN_BASELINES.md, 2026-10-18 (operational: device of dtmoe)

Written at 12:54 after the Windows reboot. It records a change made at 12:40 (EXPERIMENT_LOG.md, "GPU 故障加重") that
was logged but not registered; it is committed before any further dtmoe run is started. No test-stream run of dtmoe
exists and no development score was used for selection when it was written.

1. **dtmoe development grid on the GPU** (replaces "development grid on the CPU" of AMENDMENT_BASELINES_20261018.md
   item 1). Reason: one grid stream takes about 50 s on the GPU and 232 s on the CPU; and the CPU and GPU runs of the
   same configuration differ (three development runs, CPU vs GPU: prediction agreement 0.83 / 0.96 / 0.97, mean
   accuracy difference <= 0.003, drift firings 21 vs 19, 40 vs 40, 29 vs 28), so development and test must use the
   same device for the frozen configuration to be the one evaluated. Development and test of dtmoe both run on the
   GPU; if the GPU becomes unusable, every dtmoe run (development and test) is redone on the CPU, never mixed.
2. The three development results computed on the CPU before 12:40 are kept in ~/pfn-runs/mice-table1-newbase/dev/
   P_cpu_dtmoe and are not used.
3. GPU processes: at most 2 at once (PLAN_BASELINES.md, unchanged). Between 12:49 and 12:53 a third worker ran by
   mistake; it was stopped and its task released. GPU outputs are deterministic across processes: after the reboot
   the GPU rerun of elec2 dtmoe L16 lr1e-4 s1 m1 equalled the pre-reboot result bit for bit (P, acc, pred, firings,
   added, pruned).
4. Device recorded per stream (GPU for every dtmoe output in dev/P).
