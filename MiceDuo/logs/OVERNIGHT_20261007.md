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
