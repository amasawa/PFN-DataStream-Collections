# FeatEvo experiment log

本文件只记录"特征空间演化的流上的表格基础模型（TFM）"这个方向的工作。其他项目各有自己的日志；需要的代码复制进 `code/`，不跨项目导入。

## 2026-10-06：方向的来由（用户："结合实验，重新阅读yangxiaoyu zhilin 论文看看能做啥"；对三个候选的回答："2 3 可以 我更喜欢3"，并说明现象型的文章就是 ResetEval，方法为主）
- **重读的范围**：Yang 的三篇（ICLR 2025、arXiv 2505.13081、ICML 2026）的引言、Observations 与问题定义；Zhilin 的 WNB（Machine Learning 2024，方法与定理 1、2 的陈述）、I-Div 与 R-divergence 的摘要、AIJ（TC，Regaining Lost Clues）与 TMLR（DRL）的摘要。证明没有读。
- **今天实验的共同教训**（Claude 的总结）：对 TFM，上下文就是模型；重置、重加权、复制、按自身预测过滤、为新类减少旧类行，都伤害它（见 ResetEval、GrayContext、Emergence 各自的日志）。无标签信号在真实流上没用，延迟标签的信号有用。
- **这个方向的设想（尚无证据）**：Yang 式的"自己定义流"——流的特征空间本身在变：一部分特征消失（传感器下线），一部分新特征出现（新传感器上线），另一部分一直都在。TFM 天然接受任意特征集，是传统流学习模型没有的能力；但它的上下文在切换后混着两种特征空间的行。对应 Zhilin 的 TC/DRL：强特征消失时，模型必须用到之前被忽略的弱特征，即"找回丢失的线索"在时间上的版本。传统文献中这一设定称为特征演化流（例如 Hou、Zhang、Zhou 的 FESL，NeurIPS 2017），引用细节待核实。

## 2026-10-06：可行性检查（设计与判定规则，运行前写定）
- **流的构造**：源流前 20000 行，保持原顺序；去掉常数特征后，特征分成三组：A（切换前才有）、B（一直有）、C（切换后才有）。切换点 S = min(10000, n/2)。批 100 行，标签晚一批，上下文预算 1000，TabPFN v2、4 个 estimator、种子 0。真实数据集里没有天然的特征演化，所以这是受控的构造（该领域的标准做法），论文里要写明。
- **分组方式**：每个源 4 种——3 个随机三等分（种子 0–2），以及 strong：A 为切换前互信息最大的三分之一特征（"强特征消失"），B、C 从其余随机分。
- **数据源**：covertype、insects_abrupt_balanced、h2_poker、h2_rialto、elec2、h2_weather、h2_phishing、h2_airlines，共 32 条流。
- **策略**（切换后）：union（最近 1000 行，A+B+C 全部特征，未观测处为 NaN，交给 TabPFN 的缺失值处理）；shared（最近 1000 行，只用 B）；new（只用切换后的行，B+C）；settled（参照：最近 1000 行、B+C 且旧行的 C 值完整——好像新特征空间一直就在，用到切换前本应看不到的 C 值）；oracle（参照：没有演化，A+B+C 全部完整）。只预测切换前 10 批到切换后 60 批。每批的完整概率都保存。
- **为什么参照是 settled 而不是 oracle**：A 消失之后任何方法都拿不回，oracle 与 settled 的差是不可恢复的信息损失；settled 与可行策略的差才是方法能争取的空间。
- **判定规则（运行前写定）**：
  - F1（问题存在且有空间）：切换后前 10 批，settled 比三个可行策略中最好的一个平均高至少 3 点，且至少 2/3 的流上 ≥ 3 点。
  - F2（问题不是"选一个固定策略"就能解决）：前 10 批最好的可行策略与第 31–60 批最好的不同，至少 1/3 的流如此。
  - F1、F2 都成立 → 立项，方法的目标是过渡期（例如利用 B 把旧行的 C、新行的 A 补出来，或在策略间按延迟标签加权）；只有 F1 成立 → 问题存在，但方法可能就是"固定选一个"，需要再想；F1 不成立 → 放弃。
- **另外报告**：union 相对 shared、new 的差（TabPFN 对整块缺失的处理是否有效）；strong 与随机分组的差；oracle − settled（不可恢复的部分）。指标按 Drift-Resilient TabPFN：准确率、macro-F1、ROC AUC、ECE，另加 log-loss。
- **预期**：F1 成立（elec2 strong 的调试运行里，前 10 批 union 63.0、shared 53.7、new 58.8，oracle 81.4；settled 当时尚未加入）；F2 不确定——我猜早期 union 或 shared 最好、后期 new 最好。
- **脚本**：`code/check_featevo.py` → `results/featevo/`；`code/analyse_featevo.py` → `results/featevo_metrics.csv`。运行：tmux `fe`，与 ResetEval 的 `re1` 并行。

## 2026-10-06 18:07：可行性检查的结果——F1 不成立，不立项（CHECK_DONE 18:06:34；两次 CUDA launch failure 后自动续跑，17:31:43、18:03:54，结果按文件续跑，不受影响；`results/featevo_metrics.csv`、`results/console.txt`）
- **切换后前 10 批，32 条流平均（%），准确率 / macro-F1 / ROC AUC / ECE**：union 71.72 / 66.48 / 84.87 / 7.28；shared 68.48 / 61.91 / 80.96 / 7.20；new 73.62 / 68.77 / 85.89 / 6.38；settled 75.97 / 71.35 / 87.43 / 5.41；oracle 81.04 / 78.24 / 91.34 / 4.40。
- **第 31–60 批**：union 75.82，shared 67.22，new 75.90，settled 75.90，oracle 82.18。后期 new 与 settled 完全相同（上下文已全是切换后的行）。
- **F1 不成立**：settled 比每条流上最好的可行策略平均只高 1.00 点（需要 3），≥ 3 点的只有 4/32 条流（h2_poker 平均 3.5，其余源 −0.3 到 1.8）。即使与平均最好的单一策略 new 比，也只差 2.35 点。
- **F2 成立**：早期与后期最好的可行策略不同的流 19/32（早期 new 15、shared 12、union 5；后期 new 17、union 12、shared 3）。
- **判定**：只有 F2 成立。按规则，方法能争取的空间（settled − 可行策略）在过渡期平均只有 1–2.4 点，并且只持续约 10 批（之后 new 就等于 settled）。**不立项。**
- **另外看到的**：
  - 损失的大头是不可恢复的：oracle − settled 在后期仍有 6.27 点，来自永久消失的特征 A，任何方法都拿不回。
  - strong 分组（强特征消失）的可争取空间反而最小（0.09 点）：强特征一消失，settled 自己也掉下来，过渡期没有额外损失。这与"TFM 找回弱线索"的设想相反：没有看到 TFM 在过渡期被旧强特征拖累。
  - union（NaN 填充）比 shared 高 3.24、比 new 低 1.90：TabPFN 对整块缺失的处理有用，但不如直接只用新行。
- **与预期对照**：F1 预期成立——不成立（调试时只看了 oracle，没有 settled 时差距看起来很大，这正是加 settled 的原因）。F2 不确定——成立。
- **GPU**：两条链并行时出现了两次 CUDA launch failure（ResetEval 的 `re1` 同时在跑）；之前只在三到四条链并行时出现过。以后并行最多两条，失败重试的逻辑保留。
