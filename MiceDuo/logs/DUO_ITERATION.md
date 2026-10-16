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
