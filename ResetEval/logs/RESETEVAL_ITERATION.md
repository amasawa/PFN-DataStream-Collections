# ResetEval 审稿迭代记录（v3 流程，TMLR）

- 开始：2026-10-17 09:08。用户 2026-10-17：MICE 完成后，DUO 与 ResetEval 两篇平行迭代（"DUO + ResetEval 两篇并行"），与 MICE 平行投稿。
- 角色：审稿人 Codex gpt-6-astra high（只看论文的隔离副本）；高级专家 Fable 5.1；快速检查 Sonnet；MiMo auditor。原始回答：ResetEval/logs/reseteval_review/。
- 上限 10 轮；方法冻结；需要改方法或新数据时停下交用户。

## 第 1 轮（2026-10-17 09:41）
- **分数**：6（weak accept），已在接收一侧（round1_codex.md）。注：这一轮的提示词由 DUO 的提示词改写时误删了第一行（角色与目录说明），审稿人仍按 TMLR 标准作答；复审起提示词完整。
- **问题（P2，Missing information）**：论文说"代码、数据流和全部缓存预测将随论文发布"，但投稿包里没有实现和底层记录，重放一致性和保证检验无法独立核实。
- **Claude 判断**：成立。方案：做一个匿名补充材料包（代码、数据流构造脚本、逐运行结果），能重新生成所有表格、图和定理 (ii) 的检验；缓存预测（约 1.5 GB）随论文发布。
- **实施**：ResetEval/code/build_supplement.py（排除缓存、日志、运维脚本；替换用户名和绝对路径；README 说明目录和命令）；make_tables.py 在没有原始流文件时跳过数据表（仓库中的输出不变）。解包后重新生成：7 张表逐字相同，numbers.txt 只少数据表一行，thm_check.csv 相同（648/648）。包：ResetEval/submission/supplement.tgz（98.2 MB，未入库）。论文贡献一节改为说明补充材料内容。
- **复审**（round1_rebuttal.md）：partly answered（实质问题已解决），**7 分（accept）**；剩余 P2：streams_new.py 的两个路径被去路径规则误替换成 <home>。已修正（只替换本机用户名路径），README 写明原始文件布局；重建后无占位符、无用户名。

## 第 2 轮（2026-10-17 09:42）
- 审稿人（round2_codex.md）：第 1 轮问题已完全回答；**7 分（accept），接收无需进一步修改**；没有剩余必改问题。
- **迭代结束**：审稿人判定可接收。投稿包：ResetEval/overleaf/tmlr（main.tex/pdf）+ ResetEval/submission/supplement.tgz（98.2 MB）。投稿去向由用户决定（建议 TMLR）。
