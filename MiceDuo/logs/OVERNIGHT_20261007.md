# MICE-DUO overnight development — 2026-10-07

User authorized overnight experiments, GPU utilization target >=90%, GPU memory <25 GB, findings
logged and substantive results/changes pushed. Main experiment history is in `EXPERIMENT_LOG.md`.

## Registration before execution

Question: does ranking history from only the latest 100 labelled rows make relevance selection
unstable? Compare anchors of 300/500 rows, always retaining the anchor, adding the best older batches
from H=100 to reach M=1000. Both ranking reference and mandatory recent data change together;
this experiment does not separate their individual contributions.

Only the seven original development streams are used: elec2, h2_airlines, h2_phishing, h2_poker,
h2_rialto, h2_spam, h2_weather. First 300 batches, B=100, labels one batch late; frozen TabPFN v2,
four estimators. The 22 held-out streams remain unused for selection.

For each candidate report selection alone, original DUO weighting, and a conservative half-Brier
mixture (scale=.5, discount=.9, tempered weights). Use seed 0 for exploratory comparison; repeat
all fixed variants, original anchor=1 and MICE references on seeds 1 and 2. No adaptive threshold search.

Advancement requires all of: mean >= MICE +0.50 points; above MICE on >=5/7 streams; every stream
>= FIFO -0.30 points. Report all candidates and all seeds, including failures. A candidate must pass
on all three seeds before recommending a separate frozen held-out test. No held-out test starts tonight.
Report accuracy, macro-F1, macro OvR AUC, ECE, log-loss. This is development evidence, not a final test.

Raw outputs/checkpoints: `~/pfn-runs/night-20261007/`. Small summary tables will be placed in
`MiceDuo/results/night_20261007/`. Full execution design: `experiments/night_20261007/README.md`.

## 启动前验证

原 DUO 配置与新执行器通过确定性预测器的一致性检查；三种 anchor 均通过逐数组精确的
中断续跑对照，并核对了候选选择不使用未来标签。检查中发现 float64→float32→float16 的
二次舍入会引入一个量化差异，已改为与原实现相同的直接 float16 存储；更新混合权重使用的
上一批预测仍保留原精度，随后全部检查通过。

夜间队列的 MICE 阶段在 23:17 遇到 3 次 CUDA launch failure，总显存不到 4 GB。
调度器已自动降并发、冷却并保留断点，详见 MICE 的同名日志。此时 DUO 尚未产生新结果。

23:29：MICE 阶段仍有零星 CUDA launch failure。增加了基线断点和按断点进展计算的重试额度，
并尝试 CUDA_LAUNCH_BLOCKING=1；这些属于执行稳定性调整，DUO 开发方案与阈值保持不变。

- 2026-10-07T23:29:47+11:00: 调度器结束；总完成 2/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。
