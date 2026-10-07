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

- 2026-10-08T02:32+11:00：进度 20/86。K2 poker_b micev1000_500 完成，K2 仅剩 covertype_b micev（完成后自动运行 K2 分析）。DUO 开发阶段 a3 已完成 h2_poker、h2_weather，a5（anchor=500）开始运行。本窗口无新失败（自 01:20 起累计 4 次）。GPU 利用率均值 99.0%（194 次采样仅 1 次 <90%），显存峰值 10980 MiB（34%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T02:42+11:00：进度 23/86。DUO 开发阶段 seed0 anchor=300（a3）7 条流全部完成；a5 进行中（h2_phishing 已完成）。K2 仅剩 covertype_b micev。本窗口无新失败（累计 4 次）。GPU 利用率均值 99.3%（195 次采样 0 次 <90%），显存峰值 11258 MiB（34%），RAM 可用 ≥22 GB；维持 6 worker。近 30 分钟约 3 任务/10 分钟，剩 63 个任务，粗估约 06:00–06:30 完成（MICE replicate 任务较长，估计偏乐观）。

- 2026-10-08T02:52+11:00：进度 25/86。DUO a5 已完成 elec2、h2_airlines、h2_phishing；duo_replicates 阶段开始（duo_ref_s1_elec2：seed1 下在开发前缀上重算 MICE 参考）。本窗口无失败（累计 4 次）。GPU 利用率均值 99.5%（0 次 <90%），显存峰值 10324 MiB（32%），RAM 可用 ≥22 GB；维持 6 worker。

- 2026-10-08T03:02+11:00：进度 27/86。DUO a5 完成 h2_poker、h2_weather（a5 剩 rialto、spam）；duo_replicates 的 seed1 MICE 参考已启动 elec2、h2_airlines、h2_phishing。本窗口无失败（累计 4 次）。GPU 利用率均值 98.6%（3 次 <90%），显存峰值 9280 MiB（28%），RAM 可用 ≥22 GB；维持 6 worker。

## 2026-10-08T03:06:55+11:00 — duo_dev 完成

全部任务完成后自动核验；原始数据与旧结果保持只读。以下含全部判定，包括不成立项。

```text
DEVELOPMENT ONLY: all pre-specified variants reported; the 22 held-out streams remain untouched.
                        acc  macro_f1      auc     ece  logloss
seed anchor method                                             
0    1      duo     84.5855   78.5438  90.5309  2.0300   0.3866
            fifo    83.6592   77.4918  89.3193  1.9687   0.4220
            sel     82.9293   77.1744  89.0368  4.8421   0.4894
     3      duo     84.4412   78.6801  89.6846  1.8087   0.3937
            fifo    83.6592   77.4918  89.3215  1.9703   0.4218
            safe    84.3416   78.6119  89.6608  1.9345   0.3969
            sel     83.3237   77.5830  89.0814  3.8276   0.4466
     5      duo     83.9692   77.9253  89.4869  1.9476   0.4066
            fifo    83.6592   77.4918  89.3215  1.9703   0.4218
            safe    83.9851   77.9467  89.4828  1.9438   0.4078
            sel     83.0613   77.0910  89.0877  3.5512   0.4398

ADVANCEMENT RULE: mean >= MICE +0.50 points, >=5/7 wins over MICE, every stream >= FIFO -0.30 points.
 seed  anchor method  delta_mice  wins_mice  worst_fifo    go
    0       1    duo    0.020598          3   -0.550000 False
    0       3    duo   -0.123750          2   -0.194444 False
    0       3   safe   -0.223354          3   -0.211111 False
    0       5    duo   -0.595758          2   -0.444816 False
    0       5   safe   -0.579843          2   -0.458194 False
Seed 0 is exploratory. Independent backbone seeds check stability on these same development data.
```
<!-- stage:duo_dev:complete -->

- 2026-10-08T03:09+11:00（duo_dev 解读）：seed0 开发集上，增大强制近期锚点没有带来改进，两种候选都未达预注册晋级标准。anchor=300 的 DUO 比 MICE 低 0.12 个点（2/7 胜），safe 低 0.22 个点；anchor=500 更差（DUO −0.60、safe −0.58，2/7 胜，单流最差比 FIFO 低 0.44–0.46 个点，超出 −0.30 容忍）。原始 anchor=100 的 DUO 仍是最好的 DUO 变体，但也只比 MICE 高 0.02 个点（3/7 胜），同样未达标。趋势是锚点越大越接近 FIFO、选择收益越小。按冻结计划，晋级要求每个 seed 都满足，所以这两个候选已不可能被推荐；seed1/2 复现仍按预注册照常运行并全部报告，不改动队列。仅为开发集结果，22 条 held-out 流未使用。

- 2026-10-08T03:12+11:00：进度 31/86。duo_dev 阶段 14/14 完成并已自动分析发布（解读见上条）。seed1 MICE 参考完成 h2_phishing、h2_airlines，其余 5 条在跑。本窗口无失败（累计 4 次）。GPU 利用率均值 96.6%（19 次 <90%，集中在 03:05–03:08 多任务同时切换），显存峰值 10688 MiB（33%），RAM 可用 ≥21.9 GB；维持 6 worker。

- 2026-10-08T03:22+11:00：进度 33/86。seed1 MICE 参考完成 elec2、h2_weather（剩 poker、rialto、spam）；seed1 DUO anchor=1 复现开始。两次单进程 `launch failure`：03:11 covertype_b micev（该任务第 5 次；检查点已到 840/1000 批，恢复点依次 161→241→401→461→840，净推进正常，03:21 已从 840 恢复），03:21 duo_s1_a1_h2_airlines（首次，退避后从检查点重跑）。自 01:20 起全局 6 次失败，约 1 次/20 分钟，均孤立、无连锁，未达熔断阈值，不降并发。GPU 利用率均值 98.6%（5 次 <90%），显存峰值 9120 MiB（28%），RAM 可用 ≥21.9 GB；维持 6 worker。

- 2026-10-08T03:31+11:00（连接恢复核对）：后台进程持续运行，完成 37/86：K2 15/16、DUO 开发 14/14、复现 8/56；0 个阻塞任务。6 个 worker 均在运行，未重复启动。最近 10 分钟 195 次采样 GPU 平均 98.93%、1 次低于 90%，显存峰值 9962 MiB（约 10.45 GB）。最近一次失败仍为 03:21，保留既有断点重试与熔断机制。恢复前本地 HEAD 与 GitHub main 均为 9f6445c。

- 2026-10-08T03:32+11:00：进度 37/86。seed1 MICE 参考完成 h2_poker、h2_spam（7 条仅剩 rialto）；seed1 DUO anchor=1 完成 elec2、h2_phishing，h2_airlines 已从检查点重跑。本窗口无新失败（累计 6 次）。GPU 利用率均值 99.0%（1 次 <90%），显存峰值 9962 MiB（30%），RAM 可用 ≥21.8 GB；维持 6 worker。

- 2026-10-08T03:42+11:00：进度 40/86。seed1 的 7 条 MICE 参考全部完成；seed1 DUO anchor=1 完成 h2_airlines（重跑后成功）、h2_poker，anchor=3 开始。本窗口无新失败（累计 6 次）。GPU 利用率均值 99.3%（1 次 <90%），显存峰值 10254 MiB（31%），RAM 可用 ≥21.9 GB；维持 6 worker。过去 1 小时完成 17 个任务，剩 46 个，预计约 06:15–06:45 完成。

- 2026-10-08T03:52+11:00：进度 43/86。K2 阶段 16/16 完成并已自动分析（解读见上条）；seed1 DUO anchor=1 完成 h2_weather。03:48 duo_s1_a3_h2_airlines 与 03:49 duo_s1_a1_h2_spam 相隔 1 分钟各失败一次（累计 8 次，近 30 分钟 3 次），调度器自动冷却 3 分钟、目标并发降为 5，期间实际 4 个 worker，GPU 仍为 98%；冷却结束后会按利用率自动回升到 6。两任务检查点均有推进，退避后从检查点重跑。03:41–03:51 GPU 利用率均值 98.5%，显存峰值 9514 MiB（29%），RAM 可用 ≥22 GB。若失败继续成簇出现，将把上限降为 5 worker。

- 2026-10-08T04:02+11:00：进度 46/86。seed1 DUO anchor=1 7/7 完成（h2_spam 重跑后成功）；anchor=3 完成 elec2、h2_phishing。冷却后并发停留在 5：调度器仅在利用率 <94% 时加 worker，而 5 worker 已维持 98.4% 均值（194 次采样仅 3 次 <90%），所以保持 5，同时减少并发失败机会。本窗口无新失败（累计 8 次）。显存峰值 8881 MiB（27%），RAM 可用 ≥23.5 GB。

- 2026-10-08T04:12+11:00：进度 50/86。seed1 DUO anchor=3 完成 h2_airlines（重跑后成功）、h2_poker、h2_weather、h2_rialto（仅剩 h2_spam）；anchor=5 已开始 4 条。本窗口无新失败（累计 8 次）。5 worker 下 GPU 利用率均值 98.6%（4 次 <90%），显存峰值 9869 MiB（30%），RAM 可用 ≥23.5 GB。剩余 36 个任务，按近 1 小时速率预计约 06:15 前后完成。

- 2026-10-08T04:14+11:00（成簇失败）：04:11:36–04:11:57 的 21 秒内 4 个 worker 先后报 `unspecified launch failure`（duo_s1_a5_h2_phishing、a5_elec2、a5_h2_rialto、a3_h2_spam）。此前失败都是孤立的，这次多进程几乎同时失败，更像一次设备级（驱动/WSL）事件，而非各进程独立故障；WSL dmesg 无新记录，失败后 GPU 正常（74°C、203 W、2700 MHz）。调度器逐次冷却，目标并发 6→4→3→2，剩余 2 个 worker 未受影响、继续运行；4 个任务检查点均有推进，冷却后按利用率逐步回升并从检查点重跑。累计失败 12 次；当前 10 分钟窗口内已有 4 次，再有 2 次将触发全局熔断（预期的安全行为）。未读取或改动 Windows 侧事件、TDR 与驱动设置。

- 2026-10-08T04:22+11:00：成簇失败后已恢复。04:12:31 duo_s1_a5_h2_poker 又失败一次（共 5 次集中在 04:11:36–04:12:31，累计 13 次），目标并发一度降到 1；唯一剩余的 worker（a5_h2_airlines）正常推进并于 04:15 完成，说明设备已恢复，属于暂态事件。04:15:30 冷却结束后逐步回升，04:17 恢复到 5 worker；5 个失败任务均已从检查点重跑。期间（04:12–04:16）利用率跌到 18–67%；04:17:30 后均值 99.6%（0 次 <90%），显存峰值 8386 MiB（26%），RAM 可用 ≥23.5 GB。进度 51/86。熔断窗口已过，无需人工处理。

- 2026-10-08T04:32+11:00：进度 55/86。seed1 DUO anchor=3 7/7 完成（h2_spam 重跑后成功）；anchor=5 完成 elec2、h2_phishing、h2_poker（剩 rialto、spam、weather）。seed2 MICE 参考开始（elec2、h2_airlines）。本窗口无新失败（累计 13 次）。5 worker 下 GPU 利用率均值 98.9%（2 次 <90%），显存峰值 11700 MiB（36%），RAM 可用 ≥23.4 GB。剩 31 个任务（seed2 的 7 个 MICE 参考 + 21 个 DUO + 3 个 seed1 a5），预计约 06:30 完成。

- 2026-10-08T04:42+11:00：进度 58/86。seed1 DUO anchor=5 完成 h2_weather、h2_rialto（仅剩 h2_spam）；seed2 MICE 参考完成 h2_phishing，另 5 条在跑。04:41 利用率短暂低于 94%，调度器自动把目标并发从 5 升回 6。本窗口无新失败（累计 13 次）。GPU 利用率均值 97.6%（13 次 <90%，多在任务切换时），显存峰值 7402 MiB（23%），RAM 可用 ≥22 GB。

- 2026-10-08T04:52+11:00：进度 62/86。seed1 DUO 复现（a1/a3/a5 共 21 个）全部完成；seed2 MICE 参考完成 h2_phishing、h2_airlines、h2_weather、elec2（剩 poker、rialto、spam）；seed2 DUO anchor=1 开始。本窗口无新失败（累计 13 次）。6 worker 下 GPU 利用率均值 97.5%（13 次 <90%），显存峰值 10672 MiB（33%），RAM 可用 ≥22 GB。剩 24 个任务，预计约 06:15–06:30 完成。

- 2026-10-08T05:02+11:00：进度 65/86。seed2 MICE 参考完成 h2_poker（剩 rialto、spam）；seed2 DUO anchor=1 完成 elec2、h2_phishing。本窗口无新失败（累计 13 次）。6 worker 下 GPU 利用率均值 99.0%（3 次 <90%），显存峰值 8292 MiB（25%），RAM 可用 ≥22 GB。

- 2026-10-08T05:22+11:00：进度 70/86（含 05:12 未能写入的检查：当时 67/86，GPU 均值 99.2%，显存峰值 11316 MiB）。seed2 的 7 条 MICE 参考全部完成；seed2 DUO anchor=1 完成 h2_weather、h2_poker（剩 rialto、spam），anchor=3 已开始 4 条。05:02 以来无新失败（累计 13 次）。05:11–05:21 GPU 利用率均值 99.3%（0 次 <90%），显存峰值 9424 MiB（29%），RAM 可用 ≥22 GB；维持 6 worker。剩 16 个 DUO 任务，预计约 06:00–06:15 全部完成并自动运行 duo_replicates 分析。

- 2026-10-08T05:32+11:00：进度 74/86。seed2 DUO anchor=1 7/7 完成；anchor=3 完成 elec2、h2_phishing；anchor=5 开始。本窗口无新失败（累计 13 次）。GPU 利用率均值 99.2%（0 次 <90%），显存峰值 9436 MiB（29%），RAM 可用 ≥22 GB；维持 6 worker。剩 12 个任务（6 个在跑、6 个排队）。排队任务用完后并发会自然下降，收尾阶段利用率将低于 90%；按计划不制造额外 GPU 负载。

- 2026-10-08T05:42+11:00：进度 77/86。seed2 DUO anchor=3 完成 h2_airlines、h2_weather、h2_poker（剩 rialto、spam）；anchor=5 已启动 4 条。本窗口无新失败（累计 13 次）。GPU 利用率均值 99.5%（0 次 <90%），显存峰值 10700 MiB（33%），RAM 可用 ≥22 GB；维持 6 worker。仅剩 3 个排队任务。

- 2026-10-08T05:52+11:00：进度 81/86，进入收尾。seed2 DUO anchor=3 7/7 完成；anchor=5 完成 elec2、h2_phishing，最后 5 个任务都在运行、无排队任务，并发将随任务结束逐个下降。本窗口无新失败（累计 13 次）。GPU 利用率均值 99.6%（0 次 <90%），显存峰值 10700 MiB（33%），RAM 可用 ≥22 GB。预计 06:05 前后全部完成，随后自动运行 duo_replicates 分析并发布。

- 2026-10-08T06:02+11:00：进度 84/86。seed2 DUO anchor=5 完成 h2_airlines、h2_poker、h2_weather；最后 2 个任务（a5_h2_rialto、a5_h2_spam）在跑，没有排队任务。本窗口无新失败（累计 13 次）。收尾阶段并发自然降到 2，05:51–06:01 利用率均值 93.1%（32 次 <90%，原因是可跑任务不足，而非资源受限；按计划不制造额外 GPU 负载），当前仍为 100%；显存峰值 7108 MiB（22%），RAM 可用 ≥22 GB。

## 2026-10-08T06:04:39+11:00 — duo_replicates 完成

全部任务完成后自动核验；原始数据与旧结果保持只读。以下含全部判定，包括不成立项。

```text
DEVELOPMENT ONLY: all pre-specified variants reported; the 22 held-out streams remain untouched.
                        acc  macro_f1      auc     ece  logloss
seed anchor method                                             
0    1      duo     84.5855   78.5438  90.5309  2.0300   0.3866
            fifo    83.6592   77.4918  89.3193  1.9687   0.4220
            sel     82.9293   77.1744  89.0368  4.8421   0.4894
     3      duo     84.4412   78.6801  89.6846  1.8087   0.3937
            fifo    83.6592   77.4918  89.3215  1.9703   0.4218
            safe    84.3416   78.6119  89.6608  1.9345   0.3969
            sel     83.3237   77.5830  89.0814  3.8276   0.4466
     5      duo     83.9692   77.9253  89.4869  1.9476   0.4066
            fifo    83.6592   77.4918  89.3215  1.9703   0.4218
            safe    83.9851   77.9467  89.4828  1.9438   0.4078
            sel     83.0613   77.0910  89.0877  3.5512   0.4398
1    1      duo     84.6466   78.8838  90.5952  2.0553   0.3846
            fifo    83.7782   77.7250  89.3993  1.8704   0.4179
            safe    84.5055   78.7553  90.5565  2.3692   0.3883
            sel     83.0404   77.3085  89.1429  4.7801   0.4831
     3      duo     84.6138   79.0302  89.7642  1.8064   0.3904
            fifo    83.7782   77.7250  89.3993  1.8704   0.4179
            safe    84.4979   78.9244  89.7437  2.0194   0.3939
            sel     83.4509   77.8131  89.1932  3.6950   0.4431
     5      duo     84.1737   78.1346  89.5771  1.8961   0.4020
            fifo    83.7782   77.7250  89.3993  1.8704   0.4179
            safe    84.1020   78.0934  89.5721  1.8845   0.4037
            sel     83.2791   77.3143  89.2067  3.3655   0.4347
2    1      duo     84.8491   78.8567  90.6223  1.9748   0.3807
            fifo    83.9139   77.9923  89.4406  1.9333   0.4152
            safe    84.6765   78.9338  90.5788  2.3265   0.3853
            sel     83.0754   77.3531  89.1030  4.6812   0.4797
     3      duo     84.6819   78.9058  89.8179  1.7616   0.3872
            fifo    83.9139   77.9923  89.4406  1.9333   0.4152
            safe    84.5868   78.9209  89.7959  1.9511   0.3911
            sel     83.4744   77.8842  89.2523  3.5814   0.4387
     5      duo     84.1424   78.2404  89.5767  1.9025   0.4024
            fifo    83.9139   77.9923  89.4406  1.9333   0.4152
            safe    84.1119   78.2163  89.5726  1.9080   0.4041
            sel     83.0275   77.2316  89.1624  3.5035   0.4398

ADVANCEMENT RULE: mean >= MICE +0.50 points, >=5/7 wins over MICE, every stream >= FIFO -0.30 points.
 seed  anchor method  delta_mice  wins_mice  worst_fifo    go
    0       1    duo    0.020598          3   -0.550000 False
    0       3    duo   -0.123750          2   -0.194444 False
    0       3   safe   -0.223354          3   -0.211111 False
    0       5    duo   -0.595758          2   -0.444816 False
    0       5   safe   -0.579843          2   -0.458194 False
    1       1    duo    0.104382          4   -0.474916 False
    1       1   safe   -0.036726          2   -0.561873 False
    1       3    duo    0.071576          4   -0.183333 False
    1       3   safe   -0.044306          4   -0.155556 False
    1       5    duo   -0.368541          3   -0.284281 False
    1       5   safe   -0.440159          3   -0.739130 False
    2       1    duo    0.108686          3   -0.577778 False
    2       1   safe   -0.063890          1   -0.688889 False
    2       3    duo   -0.058516          2   -0.155556 False
    2       3   safe   -0.153592          2   -0.222222 False
    2       5    duo   -0.598017          2   -0.555184 False
    2       5   safe   -0.628504          3   -0.799331 False
Seed 0 is exploratory. Independent backbone seeds check stability on these same development data.
Variants meeting all criteria on every seed: []. No held-out evaluation was launched.
```
<!-- stage:duo_replicates:complete -->

- 2026-10-08T06:04:48+11:00: 调度器结束；总完成 86/86，失败阻塞 0。详细事件与资源曲线：`/home/zhwu9808/pfn-runs/night-20261007`。
