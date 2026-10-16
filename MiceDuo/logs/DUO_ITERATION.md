# MICE-DUO 审稿迭代记录（v3 流程，ICML 模板）

- 开始：2026-10-17 09:05。用户 2026-10-17："mice 搞定了，你觉得是不是可以迭代mice-duo了"；底座选择（用户 2026-10-17 回答）：**保持旧底座**——DUO 建立在固定分段的 MICE 上，不重跑实验；论文写明这一点，并在局限中说明未在检测分段版本上运行。
- 角色：审稿人 Codex gpt-6-astra high（只看论文的隔离副本）；高级专家 Fable 5.1；快速检查 Sonnet；MiMo auditor。原始回答：MiceDuo/logs/duo_review/。
- 上限 10 轮（全局规则）；方法冻结；需要改方法或新数据时停下交用户。已用过一次的 22 条 held-out 前缀不再作独立确认。

## 第 0 步（2026-10-17 09:05）
- 论文 §2 写明使用固定分段的 MICE（每 500 行关闭一段），并指出 MICE 论文也给出检测分段版本；局限加一句：全部实验用固定分段的 MICE，选择专家未在检测分段下运行。编译通过。
- 2026-10-17 09:08 用户决定 DUO 与 ResetEval 两篇平行迭代，与 MICE 平行投稿。

## 第 1 轮（2026-10-17 09:21）
- **分数**：3（weak reject），离接收差两档（round1_codex.md）。
- **问题（P1，Missing information）**：安全保证继承自 MICE；没有证明相关性排序本身带来信息，而不只是"多加一个上下文专家"。要求：MICE + 保留锚点、均匀随机抽取的上下文专家，同样的混合设置；在可控复现流和 held-out 上做配对的准确率/log-loss 比较，给出不确定性和运行时间。
- **Claude 判断**：成立。论文的所有比较都是对 MICE 本身，缺少"同样大小、同样锚点的随机上下文"这一对照；只改挑选这一步，方法不变，现有数据就能做。依据用户 2026-10-09 的长期授权（审稿引出的对照、已有生成器和数据流）。
- **方案**：experiments/duo_rand_20261017/PLAN.md（副本 round1_plan.md）。专家 Fable（round1_expert_q1.md，1.17 美元）：单次抽取 + K=3 重复、流级配对 t、log-loss 共同主指标、排序只作描述、4 个来源只报来源级、命中率/单独专家/权重/t>10；建议 oracle 需用户批准。**用户 2026-10-17 批准 oracle 对照（"加上"）**。审稿人方案检查（round1_reviewer_plan_check.md）：yes with changes，4 条全部采纳（部署判定规则两个指标都要求；去掉前缀级 t 区间、改为来源级+条件 bootstrap；held-out 也 3 次抽取，分开抽样与骨干变异；同条件重新计时；"no advantage established" 措辞）。
- **实施准备**：worker.py（rand/orc；常驻进程，原子写出）、prepare.py（270 个任务，~/pfn-runs/duo-rand-20261017）、evaluate.py（运行前写定）。流水线检查：用新 worker 重算 sel，两条流 1–30 批的选择与已存 DUO 完全相同，概率最大差 2.4e-4（float16 存储）。评估脚本用零效应夹具（rand/orc = sel）测试：所有 Δ = 0，MICE 与 MICE+sel 的值与冻结结果（mechanism_results.csv、heldout_results.csv）逐项一致。MiMo Pro high 审计 worker 在后台（09:20 开始）。
- **MiMo Pro high 审计 worker**（2026-10-17 09:39 之前，09:20–09:32，12.5 分钟）：1 P1 + 5 P2，全部核实成立并修正：(1) 认领后、记录持有前死亡会留下无人执行的认领 → 改为原子认领（带 owner 文件的临时目录 rename 到认领路径；同 id 重启后续跑自己的认领）；(2) 坏任务无限重试 → worker.sh 同一任务死 3 次标 FAILED、无任务时死 5 次停止（CUDA 错误不在进程内捕获）；(3) 临时文件名加 pid；(4) prepare.py 断言精确的流名集合和数据文件存在（重新生成的任务表与已写的逐字相同）；(5) oracle 每个任务断言每批只有一个概念；(6) oracle 填充规则按读法 (a)：从其余候选中用 rand 第 0 次抽取的种子均匀抽所需数量（代码即如此）。MiMo 关于方差标签的说明采纳：报告中"骨干种子间 SD"称为"跨骨干种子的运行间变异"（rand 的抽取也随种子变）。
- Sonnet 复查修正（round1_fix_sonnet.json）：第一次修正（孤儿接管）有竞态 → 改为上述原子认领；第二次复查（round1_fix2_sonnet.json）：不会两个 worker 跑同一任务；剩两个窄窗口（STOPPED 后遗留认领无输出；第三次尝试写出后死亡被误标 FAILED），由运行后核对 270 个输出和认领目录处理。
- 跨任务确定性测试（~/pfn-runs/duo-rand-verify-20261017）：同一进程先跑另一任务再跑 h3_poker_b，与新进程单独跑的 P 和选择逐位相同。
- 2026-10-17 09:42 运行：09:38 起 3 个常驻 worker（~/pfn-runs/duo-rand-20261017），每任务约 78 s；09:41 加第 4 个，1 分钟内 w3、w4 各一次 CUDA launch failure（GPU 上另有空闲的 ComfyUI 进程）→ 按 PID 停掉 w4，释放其未完成的认领（rand_mech_k15_c100_s31_s1_d2，无输出），保持 3 个。w3 由 worker.sh 自动重启续跑。
