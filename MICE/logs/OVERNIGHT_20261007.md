# MICE overnight replication — 2026-10-07

User authorized overnight experiments, GPU utilization target >=90%, GPU memory <25 GB, findings
logged and substantive results/changes pushed. Main experiment history is in `EXPERIMENT_LOG.md`.

## Registration before execution

Complete previously paused K2 without changing its thresholds: TabPFN v2 seed 2; four third-set b
segments (airlines, covertype, insects, poker); FIFO, DDM, window ensemble, and cached MICE experts.
The final paper rule is evaluated with outer="brier", scale=0.5, temper=True.

- K1: MICE >= max(FIFO, DDM) -0.5 points on every segment.
- K2a: MICE strictly above FIFO, DDM, window ensemble on at least 3/4 segments; K2b: highest mean.
- K3: MICE >= FIFO -0.3 points on every segment.
- K4: MICE above windows-only on at least 3/4 segments.

No old results are overwritten. New raw outputs: `~/pfn-runs/night-20261007/results_heldout3_seed2/`.
The original checker is copied unchanged, and the seed 0/1/2 comparison reports means/ranges on
identical data segments, not independent data replications. Negative verdicts will also be recorded.
The controller plan and checks are in `experiments/night_20261007/README.md`.

## 23:17 启动观察：CUDA 故障与自动恢复

TabPFN v2 真实数据冒烟通过。队列 23:16:41 启动，23:17:31–23:17:44 在四路并发阶段，
insects/covertype/airlines 的 micev 各遇到一次 `CUDA unspecified launch failure`。
同期总显存低于 4 GB，故本次不是显存占满；Linux kernel journal 未给出对应条目，原因尚未确定。
调度器按规则降到两路并冷却三分钟，保留每 20 批的 MICE 断点；存活任务的调用计数继续增长。
没有因此改变 K2 的方法、种子或判定规则。资源限制优先于利用率目标，不将重试日志当作实验结果。

## 23:29 故障恢复改进（不改变实验定义）

23:22–23:23 的采样曾达到 95–99% GPU 利用率、约 6–7 GB 显存，但后续又有零星 CUDA
launch failure，故不能称为稳定达标。已完成 airlines/poker 的 FIFO 两项，其余结果仍待运行。
为避免基线因中断从头重跑，新增 FIFO/DDM/window ensemble 的每 20 批原子断点。
用确定性预测器逐数组核对：原实现与人为中断后续跑的准确率、log-loss、调用次数完全一致。
MICE 原来的每 20 批断点保留。调度器改为四次“无断点进展”的失败才阻塞，另设总计 20 次上限。
同时尝试 `CUDA_LAUNCH_BLOCKING=1`，只改变 CUDA 同步方式；是否改善稳定性以新日志为准，
不预先宣称问题已解决。不调用 Windows 程序、不修改驱动或学校安全策略。

- 2026-10-07T23:29:47+11:00: 调度器结束；总完成 2/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。

- 2026-10-07T23:33:03+11:00: 调度器结束；总完成 2/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。

## 23:33 用户报告“刚才崩溃”：停止并取证

- 已安全停止本轮调度器和所有 GPU 子任务；未调用任何 Windows 程序。
- WSL 从 21:21:37 持续运行，未重启；kernel journal 在实验时段无记录，未见 OOM 证据。
- 315 次采样（23:16:41–23:33:02）：GPU 显存峰值 7164 MiB（约 7.5 GB）；
  MemAvailable 最低 21259 MiB（约 20.8 GiB），均远离资源上限。采样不能排除瞬态事件。
- 共 14 次任务失败：12 次 `CUDA unspecified launch failure`、2 次 `illegal memory access`。
  同步模式下也失败，落点包括 TabPFN 的 GPU 预处理和目标嵌入；尚不能据此确定根因。
- 降并发/冷却后自动回升未能稳定运行。这轮未实现持续 >=90% 的目标，不能只凭短窗口 95–99% 宣称达标。
- 2 项 FIFO 结果已完成（airlines_b、poker_b），四项 micev 有断点；K2 尚不完整，DUO 未开始。
- 修正调度器：10 分钟内 4 次任务失败即全局停机，不再自动回升；STOP 需要明确 --resume。
  停止状态现在明确写入 status.json，避免残留的运行 PID 造成误读。
- Windows GPU 超时恢复（TDR）只是待核实假设；Microsoft 文档说明这类恢复会记入 Windows
  Event Viewer。没有读取 Windows 事件、没有修改 TDR/驱动/安全软件，不能归因给 Cortex XDR。
  文档：https://learn.microsoft.com/en-us/windows-hardware/drivers/display/timeout-detection-and-recovery

## 2026-10-08 单进程/并发对照与恢复策略

用户要求继续迭代后，在同一环境、同一 TabPFN v2 模型、seed=2、insects_b batch 140 起，
每批依次预测 100/300/1000 行上下文。各测试均 CUDA_LAUNCH_BLOCKING=1；未修改依赖、精度或模型。

- `single_current_2354`：单进程，不采样 NVML，120 次预测通过，61.56 秒。
- `single_nvml3`：单进程，每 3 秒采样 NVML，360 次预测通过，172.81 秒（套件总时间）；
  显存峰值 1791 MiB，采样平均 GPU 利用率约 17.4%。前 120 次概率与上一组逐元素完全一致。
- `two_nvml3`：两进程，其余设置相同，22.10 秒内失败，峰值 2669 MiB；worker1 第 6 次预测
  在 layer_norm 报 CUDA illegal memory access。套件立即终止另一进程。
- 这些证据支持优先排查并发相关问题，不能证明驱动/TDR/Cortex XDR 中哪一个是根因，
  也不能由短测证明单进程长期稳定。更长单进程测试正在进行。
- 调度器默认硬上限改为 1 个 worker；此模式首次失败即写 STOP 并停机。旧的按低利用率
  自动增加并发现在也受此上限约束。暂时不满足 >=90% 利用率目标，优先取得可靠实验结果。
- 原 DUO 等价性、3 个 anchor 断点恢复/无未来标签选择，以及 FIFO/DDM/window 中断恢复测试全部通过。
- 诊断原始日志和概率：`~/pfn-runs/night-20261007/diagnostics/`；这些不是新的论文结果。

长测 `single_long` 全部通过：1080 次预测，套件用时 478.53 秒，显存峰值 1791 MiB，采样平均利用率 19.0%。即将以默认单进程从原断点恢复；这仍不能保证长期无故障。

- 2026-10-08T01:03:30+11:00: 调度器结束；总完成 3/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。

- 2026-10-08T01:35+11:00（接管，并发调整）：独占窗口对照显示单进程受 CPU/GIL 限制（GPU 约 22%），多线程无效；TabPFN 多进程失败为间歇、单进程局部（6 进程 2160 次调用 1 次 launch failure，其余进程不受影响）；并发与单进程概率逐元素一致（最大差 0.0）。01:20:43 起以 6 worker、CUDA_LAUNCH_BLOCKING=0、allocator 4096 MiB/worker、失败进程从检查点重启、10 分钟 6 次失败熔断恢复队列。01:23 起 GPU 利用率均值 97%，显存峰值约 7.3 GB/32 GB。进度 4/86（新完成 airlines_b ddm1000）；insects_b micev 01:21 失败一次已从检查点恢复。详见 `experiments/night_20261007/STABILITY_MANUAL.md`。预计 6–10 小时，DUO 任务开始后再校准。

- 2026-10-08T01:42+11:00：进度 9/86（新完成 covertype_b fifo1000/ddm1000、insects_b fifo1000/ddm1000、poker_b ddm1000；winens1000 基线开始）。01:31–01:41 GPU 利用率均值 96.4%（196 次采样中 14 次 <90%，多在任务切换间隙），显存峰值 7068 MiB/32760（22%），RAM 可用 ≥22 GB。01:41:34 covertype_b micev1000_500 再次出现 `unspecified launch failure`（自 01:20 起第 2 次，约 1 次/20 分钟），检查点仍在推进，按退避从检查点重试；远低于 6 次/10 分钟熔断阈值，维持 6 worker。

- 2026-10-08T01:52+11:00：进度 10/86（airlines_b winens1000 完成；covertype_b micev1000_500 已从检查点恢复运行）。01:42–01:51 无新失败，GPU 利用率均值 95.5%，显存峰值 6760 MiB（21%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:02+11:00：进度 11/86（covertype_b winens1000 完成）。首个 DUO 任务 duo_s0_a3_elec2 于 01:51:59 启动，约 9.5 分钟完成 200/300 批，即 6 并发下约 14 分钟/DUO 任务；据此粗估剩余约 4–5 小时（约 06:30 前后），在调度器 8 小时上限（约 09:20）之内。01:51:59 poker_b winens1000 出现一次 `unspecified launch failure`（自 01:20 起第 3 次，约 1 次/13 分钟），已从检查点重跑。01:52–02:01 GPU 利用率均值 97.1%，显存峰值 7362 MiB（22%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:12+11:00：进度 15/86。K2 的 fifo/ddm/winens 基线全部完成（12/12），K2 仅剩 covertype_b、insects_b、poker_b 三个 micev1000_500 在跑。DUO 开发阶段已完成 elec2（a3，约 16 分钟）与 h2_phishing（a3，约 8 分钟）。02:02 covertype_b micev 再次 launch failure（该任务累计第 4 次，检查点均有推进，02:08 已恢复）；自 01:20 起全局 4 次失败，约 1 次/12 分钟，未达熔断阈值。02:02–02:11 GPU 利用率均值 98.0%，显存峰值 6382 MiB（19%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:22+11:00：进度 17/86。K2 insects_b micev1000_500 完成（K2 剩 covertype_b、poker_b 两个 micev）；DUO 开发阶段 h2_airlines（a3）完成。本窗口无新失败。GPU 利用率均值 98.9%（195 次采样仅 2 次 <90%），显存峰值升至 9956 MiB（30%，h2_spam/weather 等 DUO 任务占用较大），RAM 可用 ≥22 GB；均在 90% 以下，维持 6 worker。02:12 的日志推送因 GitHub 端 `remote rejected (failure)` 暂未推送，本次一并推送。

- 2026-10-08T02:32+11:00：进度 20/86。K2 poker_b micev1000_500 完成，K2 仅剩 covertype_b micev（完成后自动运行 K2 分析）。DUO 开发阶段 a3 已完成 h2_poker、h2_weather，a5（anchor=500）开始运行。本窗口无新失败（自 01:20 起累计 4 次）。GPU 利用率均值 99.0%（194 次采样仅 1 次 <90%），显存峰值 10980 MiB（34%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:42+11:00：进度 23/86。DUO 开发阶段 seed0 anchor=300（a3）7 条流全部完成；a5 进行中（h2_phishing 已完成）。K2 仅剩 covertype_b micev。本窗口无新失败（累计 4 次）。GPU 利用率均值 99.3%（195 次采样 0 次 <90%），显存峰值 11258 MiB（34%），RAM 可用 ≥22 GB；维持 6 worker。近 30 分钟约 3 任务/10 分钟，剩 63 个任务，粗估约 06:00–06:30 完成（MICE replicate 任务较长，估计偏乐观）。
