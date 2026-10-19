# Fable 5.1 on the dtmoe CPU protocol (2026-10-19 12:20:54; cost 1.77 USD, 167 s)

## Question
You are the senior methodology adviser (read-only). One bounded decision. Answer with: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence / Requires user approval. No essays. Files you may read: experiments/mice_table1_fill_20261018/AMENDMENT_BASELINES_20261018b.md, AMENDMENT_BASELINES_20261018c.md, AMENDMENT_BASELINES_20261018d.md, tune_ts.sh, tune_ext.sh, select_frozen.py, run_ts.py.

USER DECISION (2026-10-19, final): dtmoe (Table 1 baseline) runs on the CPU, development and test, instead of the local GPU strict deterministic mode (aborted: >= ~40x slower). Amendment b item 1 already says: "if the GPU becomes unusable, every dtmoe run (development and test) is redone on the CPU, never mixed."

FACTS
- Registered dtmoe grid: lr {1e-4,1e-3,1e-2} x n_steps {1,5} x L {16,32} x mech {1,2,3} x 5 dev streams = 180 tasks; selection rule and one-time boundary extension as for the other CPU baselines (amendment c; user said dtmoe gets the same extension rule); then the frozen config on the 92 test streams.
- CPU timings (OMP_NUM_THREADS=1, tsbase env, 2026-10-18 under 8 concurrent CPU procs): elec2 L16 lr1e-4 s1 m1 733 s, m2 821 s, insects_gradual L16 s1 m1 1640 s. n_steps 5 / L32 untimed. My rough estimate: grid 120-200 CPU-h; a n_steps-25 extension could add ~300+ CPU-h; tests ~60 CPU-h.
- Three CPU dtmoe outputs exist in dev/P_cpu_dtmoe (computed 12:04-12:19 on 10-18, the code then = current run_ts.py? unverified; amendment b item 2 says "kept and not used"). Their logs record acc and time.
- CPU currently: 12 lanes (amendment c cap: at most 12 CPU processes) busy with the CPU-baseline extension (onenet/fsnet/adaptz/shifts, 450 tasks, 78 done after 12.3 h, ~59 h left at this rate); after it: freeze + tests of those 4 methods on 92 streams; TOT (CPU, 12 CPU-h gate cap) is also queued. Machine: 20 logical cores, 30 GB RAM (8 GB used), load ~13.4. GPU: one process (Drift-Resilient TabPFN, ~76 h left), must stay alone on the GPU.
- CPU single-thread runs of the other methods have been treated as deterministic; dtmoe CPU run-to-run identity has not been checked.

QUESTION: the concrete operational protocol for dtmoe on CPU, to be registered as amendment e. Specifically decide:
(1) scheduling: wait until the extension frees lanes, or share the 12 lanes now (how many), or raise the CPU cap above 12 (to what, given 20 cores) — the user asked how long until results;
(2) a CPU determinism check before the grid (e.g. one task run twice fresh, bit-identical except wt) and whether to compare against the 3 old P_cpu_dtmoe files; whether those 3 may be reused or must be recomputed;
(3) anything else that must be registered (output directory, provenance flag, extension, tests, device recorded).

## Answer
**Decision**

1. 调度：不等待。向用户申请把 CPU 上限从 12 提到 16(20 逻辑核 = 12 物理核 + HT),新增的 4 条 lane 专属 dtmoe,`nice 19`,单线程。其余 12 条不动。守卫:1 分钟 load > 18、DR 每批时间比其运行中位数慢 > 20%,或 fecs_watch 出现任何 nvlddmkm 事件,立即把 dtmoe 降到 0 lane(kill 其 xargs,未完成任务无输出,重启自动跳过已完成),并记录。扩展跑完后 dtmoe 升到 8 lane,其它方法测试占 8。
2. 决定性检查:网格之前,先跑 amendment d 的同三条 probe(elec2 L16 lr1e-4 s1 m1;elec2 L32 lr1e-4 s1 m1;insects_abrupt L32 lr1e-3 s5 m3),每条两次新进程:run a 直接写入网格目录 `dtmoe_cpu/dev/P`(作为网格产出),run b 写入 `dtmoe_cpu/probe_pre/b`,verify_compare.py 除 wt 外逐数组 bit-identical。任一不同 → dtmoe 路径停,交用户。三条 probe 同时给出 s5 / L32 的首次计时,用来把 120–200 CPU-h 的估计换成实测投影,写进 amendment e 的 deviation record。
3. 旧的 3 个 P_cpu_dtmoe 文件:不复用,重算。只做信息性比对(elec2 m1 / m2、insects_gradual m1 对新 run a):一致则记"代码路径自 10-18 12:04 未变、跨日跨负载决定性";不一致则对 run_ts.py 做 git log 解释,但不阻塞。
4. 必须登记的其它项(见下)。

**Supporting evidence**

- CPU 总剩余量才是瓶颈,顺序只改信息到达时间,不改总完成日。实测扩展 78 任务 / 12.3 h / 12 lane ≈ 1.9 CPU-h/任务,剩余 372 任务 ≈ 700 CPU-h;若 4 方法都冻结在 n_steps 25,92×4 测试再 ≈ 700 CPU-h;dtmoe 网格 135–200 + 扩展 + 测试 60。dtmoe 扩展若触发 n_steps 25:s5 ≈ 5× s1(0.3 h→1.2 h),s25 ≈ 5–6 h/任务 × 90 ≈ 450–550 CPU-h,比你估的 300 更大,是 dtmoe 的主要成本。
- 时间线(从现在起,粗略):

| 方案 | dtmoe 网格冻结 | dtmoe 测试完成 | Table 1 CPU 侧全部完成 |
|---|---|---|---|
| A 16 lane(推荐) | ~2–3 天 | ~6–8 天 | ~6–7 天 |
| B 等待 | ~5 天后才开始 | ~9–10 天 | ~7–8 天 |
| C 共享 12(kill 扩展重启 P=8) | ~3 天 | ~7–9 天 | ~7–8 天 |

- 16 lane 的净吞吐增益只有 ~15–20%(HT 共享拖慢每条 lane),整体省约 1 天;真正的收益是提前 5 天拿到 dtmoe 的决定性结论和 s5/L32 实测预算。
- tune_ts.sh 已对 dtmoe 用 nice 19(`tune_ts.sh:20`),与新 lane 的优先级规则一致。
- 不复用旧文件:amendment b 第 2 项和 d 第 4 项已两次登记"不使用";复用需撤销两条登记,只省 ~0.9 CPU-h。
- 必须用新目录:`dev/P` 里已有同名的旧 GPU dtmoe 输出,run_ts.py 对已存在文件直接跳过(`run_ts.py:399`),写进 dev/P 会静默混合 GPU/CPU 结果,正是 amendment b 禁止的。

**Alternative options**

- B 等待:零 GPU 风险,dtmoe 问题最晚暴露。
- C 共享 12:不加核但 kill 当前 xargs 丢最多 12 个在跑任务(≤ ~20 CPU-h)。变体 C':对 4 个扩展进程 `kill -STOP`,跑完 dtmoe probe 后 `-CONT`,零损失但 wt 失真(wt 已排除在比对和计时之外)。若用户不批 16,选 C'。

**Key risks**

- 16 进程 + GPU 没有实测记录;12 是"观测到安全",不是上限。DR 还有 ~76 h,若驱动事件触发死亡,成本是该流重跑(最多 3 次)。守卫把损失限制在一次事件。
- dtmoe 的扩展预算可能 ≈ 500 CPU-h;用户已定"同样扩展规则",默认继续,但冻结网格时把投影报给用户。
- tune_ext.sh 没有 dtmoe 分支(`tune_ext.sh:13-17`,LS/MS 为空 → 0 任务),且 `-le 12` 检查和单一 flock 与 16 lane 冲突。dtmoe 要用独立脚本、独立任务文件、独立锁、独立目录;登记在 e 里,运行前提交。

**Remaining uncertainty**

- s5、L32 的 CPU 时间未测;probe 之后才知道网格是 135 还是 250+ CPU-h。
- 其它 4 个 CPU 基线"视为决定性"未验证。可选、便宜:每方法冻结配置在一个 dev 流上重跑一次(4 × 1–2 CPU-h),把"视为"变成"已检"。不在本题范围,建议一起登记。

**Amendment e 还需登记的项**

- 目录:`~/pfn-runs/mice-table1-newbase/dtmoe_cpu/{dev/P, probe_pre/b, probe_post_<stage>, logs, quarantine}`;select_frozen.py 的 P 参数指向 `dtmoe_cpu/dev/P`。
- 环境:tsbase,TS_DEVICE 未设(cpu),TS_DETERMINISTIC 未设,OMP/MKL/OPENBLAS=1;冻结时检查每个 npz 的 config.device == "cpu",否则拒选。
- Bookend:网格后、扩展后、测试后各重跑 elec2 L16 lr1e-4 s1 m1 一次,对 probe_pre run a 比对;不同 → 该阶段全部"unverified",不选不冻。
- 进程死亡规则同 amendment d 第 5 项;冻结提交同 c 第 4 项;计时与峰值内存按 c 第 7 项在本机 CPU 上测。
- 出处标记:"CPU"(同其它 CPU 基线)+ probe/bookend 通过状态;Table 1 脚注说明 dtmoe 在 CPU 评估、原因是 b 记录的 CPU/GPU 预测不一致(0.83–0.97 一致率)。
- 旧输出(dev/P 中的 GPU dtmoe、dtmoe_local、P_cpu_dtmoe)继续"不使用"。

**Confidence**:高(目录隔离、重算、probe 设计);中(16 lane 的 GPU 安全性、时间线 ±30%)。

**Requires user approval**:是,仅第 1 项(把登记的 12 进程上限改为 16)。其余为操作性登记,协调者可直接写入 amendment e。
