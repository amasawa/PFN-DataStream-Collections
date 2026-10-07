# WJD02YF4 WSL 实验稳定性手册

记录时间：2026-10-08 00:57 Australia/Sydney。此页区分已观察事实和待验证假设；不是根因已经解决的声明。

## 当前可继续使用的配置

- Python 环境与 requirements 保持不变：驱动 573.44、torch 2.14.0+cu126、tabpfn 9.0.0。
- 当前 supervisor 单 worker，CUDA_LAUNCH_BLOCKING=1，CPU 数学库线程限制为 1。
- 不设置 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True。
- 保留现有分块预测、原子结果落盘与批次断点恢复。错误进程退出后才能恢复，不能在发生 CUDA 错误的进程内继续预测。
- 显存采样 22000 MiB 暂停、23200 MiB 紧急停止，保留低于用户 25 GB 限制的余量；采样不能保证捕获全部瞬态峰值。
- 当前单 worker 首次失败全局停止属于排查期策略，不代表最终重试策略。受控多进程恢复尚未验证。

## 实测证据

- 单进程无 NVML 采样：120 次预测通过。
- 单进程每 3 秒 NVML 采样：360 次预测通过；前 120 次概率与上一组完全一致。
- 双进程同样采样：22.10 秒后 illegal memory access，峰值 2669 MiB。只能说明该次配置失败，不能证明多进程必然失败。
- 单进程长测：1080 次预测通过，套件 478.53 秒，峰值 1791 MiB。
- 实际队列从 00:11:57 恢复至 00:57:37，事件日志未出现新失败；airlines_b 的 micev1000_500 在 00:53:19 完成，随后开始 covertype_b。总完成 3/86。
- 这段实际运行有 885 次资源采样，显存峰值 1805 MiB，GPU 利用率采样均值 26.64%，未实现持续 90% 目标。
- 00:56 左右宿主 WSL 进程检查未见其他 CPU 密集任务；主要 CPU 消耗是实验 worker 自身（约一个 CPU 核）。这不证明先前失败时没有 CPU 竞争，也看不到 Windows 进程。

原始证据位于 `~/pfn-runs/night-20261007/` 的 events.log、gpu.csv、status.json 和 diagnostics/。

## 新发现：内核警告的时间界限

读取真实 WSL 宿主 dmesg，而不是仅依赖沙箱进程视图或 journal：

```text
2026-10-07T22:30:39+11:00 memcpy: detected field-spanning write (size 4) of single field "current_pos" at drivers/hv/dxgkrnl/dxgvmbus.c:3095 (size 0)
WARNING: CPU: 0 PID: 3017 ... dxgvmb_send_wait_sync_object_gpu+0x271/0x290
Comm: python ... 6.18.33.2-microsoft-standard-WSL2
Call Trace: dxgkio_submit_wait_to_hwqueue ... dxgk_ioctl
```

另外，`dxgkio_query_adapter_info: Ioctl failed: -2/-22` 出现在 21:21 的 WSL 启动阶段。
这些记录早于 23:16 后的夜间队列失败和 00:00 的双进程对照，不能当作这些失败的同步证据。
它们说明存在可追踪的 dxg 内核警告；尚不能证明 TDR、驱动故障、CPU 竞争或 Cortex XDR 是根因。
之前仅凭 journal 未见记录得出的“无内核证据”需要以上述 dmesg 记录补充。

## 后续受控排查与恢复顺序

1. 保留正在推进的单进程队列，不旁路调度器启动竞争 GPU 的诊断。等安全检查点/独占诊断窗口后再测试。
2. 对照前后记录宿主 CPU 进程、线程数、GPU 使用、准确时间与 dmesg。用户报告其他实验中 CPU 基线/Chromium 可诱发故障；本轮尚未验证此因果关系。
3. 在无额外 CPU 密集任务的窗口重做双进程 TabPFN 对照；随后独立做双进程纯 Torch 矩阵乘对照。矩阵乘通过不能排除其他算子触发的平台问题。
4. 只有对照通过后才逐级恢复并发。孤立失败可采用有上限的进程重启加断点恢复；密集失败必须熔断，不能无限重试追求利用率。
5. 记录每个配置的持续时间、预测数、失败数、资源峰值与概率一致性。不要将稳定性测试当成论文结果。
6. 只用 WSL/Linux。Windows 事件 4101、TDR 注册表及驱动操作需要另行说明，不能自动执行。

本页为侧对话补充记录；未修改运行中的 supervisor、停止其他任务或启动额外 GPU 负载。

## 01:04–01:20 独占窗口对照（接管后）

暂停 supervisor（优雅停止，MICE 从 20 批检查点恢复）后在独占 GPU 上测试：

| 配置 | 调用数 | 失败 | GPU 利用率 | 显存峰值 |
|---|---|---|---|---|
| 1 进程 1 线程，blocking=0 | 120 | 0 | 22% | 1765 MiB |
| 1 进程 4 线程（共享 context） | 720 | 0 | 21%（吞吐 4.4 vs 3.8 调用/秒） | 2105 MiB |
| 纯 torch 2 进程 LayerNorm+SDPA 60 s | ~24k 迭代 | 0 | 99% | 2839 MiB |
| TabPFN 2 进程，无 allocator cap，blocking=0 | 360 | 0 | ~55% | 2647 MiB |
| TabPFN 2 进程，cap 1792，blocking=0 | 360 | 0 | — | — |
| TabPFN 4 进程 4 条流，无 cap | 1440 | 0 | 均值 70% | 3540 MiB |
| TabPFN 6 进程，无 cap | 2160 | 1（unspecified launch failure，其余 5 进程不受影响） | 满载期 ~95% | 5032 MiB |

结论（仍是经验观察，不是根因证明）：
- 单进程瓶颈是 CPU/GIL：每次调用 ~350 ms，其中每次 fit 重建模型 ~60 ms、sklearn 预处理 ~60 ms、前向 ~90 ms（大量小 kernel 启动）。线程无法提高吞吐，只有多进程能逼近 90%。
- 多 CUDA context 本身在本机 WSL 上可稳定满载（纯 torch 99%）。TabPFN 多进程失败是间歇性的、单进程局部的，不会传染给其他进程。
- 4 进程 blocking=0 与单进程 blocking=1 的概率逐元素完全一致（最大差 0.0），blocking 与 allocator cap 不改变数值结果。
- 因此策略从“首次失败全局熔断”改为：6 worker、CUDA_LAUNCH_BLOCKING=0、allocator cap 4096 MiB/worker、失败进程从检查点重启，10 分钟内 6 次失败才全局熔断（`--breaker`）。显存远低于 90%（6 worker ≈ 6.2 GB / 32 GB）。

01:20:43 以 6 worker 恢复正式队列，启动 1 分钟后 GPU 99%、6164 MiB。
