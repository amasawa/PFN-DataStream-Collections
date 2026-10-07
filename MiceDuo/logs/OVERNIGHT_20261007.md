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

- 2026-10-07T23:33:03+11:00: 调度器结束；总完成 2/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。

23:33 用户报告崩溃后，整轮已停止排查。DUO 的 70 个任务尚未开始，没有新实验结论。
MICE 阶段共 14 次 CUDA 失败，315 次资源采样显存峰值约 7.5 GB、可用内存最低约 20.8 GiB，
未见 WSL 重启或 OOM 证据。根因未确定，详见 MICE 同名日志。调度器已加入连续故障全局停机，
本轮不会自动恢复 GPU 负载；计划、旧结果和新断点均保留。

2026-10-08：继续迭代前完成稳定性对照。单进程 120/360 次预测通过，两进程 22.10 秒内
发生 illegal memory access（峰值显存 2669 MiB）。详见 MICE 同名日志。
调度器改为默认单进程、首次任务失败即全局停止。DUO 方案/阈值保持原注册设置；暂无新科学结论。

- 2026-10-08T01:03:30+11:00: 调度器结束；总完成 3/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。

- 2026-10-08T01:35+11:00（接管，并发调整）：独占窗口对照显示单进程受 CPU/GIL 限制（GPU 约 22%），多线程无效；TabPFN 多进程失败为间歇、单进程局部（6 进程 2160 次调用 1 次 launch failure，其余进程不受影响）；并发与单进程概率逐元素一致（最大差 0.0）。01:20:43 起以 6 worker、CUDA_LAUNCH_BLOCKING=0、allocator 4096 MiB/worker、失败进程从检查点重启、10 分钟 6 次失败熔断恢复队列。01:23 起 GPU 利用率均值 97%，显存峰值约 7.3 GB/32 GB。进度 4/86（新完成 airlines_b ddm1000）；insects_b micev 01:21 失败一次已从检查点恢复。详见 `experiments/night_20261007/STABILITY_MANUAL.md`。预计 6–10 小时，DUO 任务开始后再校准。

- 2026-10-08T01:42+11:00：进度 9/86（新完成 covertype_b fifo1000/ddm1000、insects_b fifo1000/ddm1000、poker_b ddm1000；winens1000 基线开始）。01:31–01:41 GPU 利用率均值 96.4%（196 次采样中 14 次 <90%，多在任务切换间隙），显存峰值 7068 MiB/32760（22%），RAM 可用 ≥22 GB。01:41:34 covertype_b micev1000_500 再次出现 `unspecified launch failure`（自 01:20 起第 2 次，约 1 次/20 分钟），检查点仍在推进，按退避从检查点重试；远低于 6 次/10 分钟熔断阈值，维持 6 worker。

- 2026-10-08T01:52+11:00：进度 10/86（airlines_b winens1000 完成；covertype_b micev1000_500 已从检查点恢复运行）。01:42–01:51 无新失败，GPU 利用率均值 95.5%，显存峰值 6760 MiB（21%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:02+11:00：进度 11/86（covertype_b winens1000 完成）。首个 DUO 任务 duo_s0_a3_elec2 于 01:51:59 启动，约 9.5 分钟完成 200/300 批，即 6 并发下约 14 分钟/DUO 任务；据此粗估剩余约 4–5 小时（约 06:30 前后），在调度器 8 小时上限（约 09:20）之内。01:51:59 poker_b winens1000 出现一次 `unspecified launch failure`（自 01:20 起第 3 次，约 1 次/13 分钟），已从检查点重跑。01:52–02:01 GPU 利用率均值 97.1%，显存峰值 7362 MiB（22%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:12+11:00：进度 15/86。K2 的 fifo/ddm/winens 基线全部完成（12/12），K2 仅剩 covertype_b、insects_b、poker_b 三个 micev1000_500 在跑。DUO 开发阶段已完成 elec2（a3，约 16 分钟）与 h2_phishing（a3，约 8 分钟）。02:02 covertype_b micev 再次 launch failure（该任务累计第 4 次，检查点均有推进，02:08 已恢复）；自 01:20 起全局 4 次失败，约 1 次/12 分钟，未达熔断阈值。02:02–02:11 GPU 利用率均值 98.0%，显存峰值 6382 MiB（19%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:22+11:00：进度 17/86。K2 insects_b micev1000_500 完成（K2 剩 covertype_b、poker_b 两个 micev）；DUO 开发阶段 h2_airlines（a3）完成。本窗口无新失败。GPU 利用率均值 98.9%（195 次采样仅 2 次 <90%），显存峰值升至 9956 MiB（30%，h2_spam/weather 等 DUO 任务占用较大），RAM 可用 ≥22 GB；均在 90% 以下，维持 6 worker。02:12 的日志推送因 GitHub 端 `remote rejected (failure)` 暂未推送，本次一并推送。
