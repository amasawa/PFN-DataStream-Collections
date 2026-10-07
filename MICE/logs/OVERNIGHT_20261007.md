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
