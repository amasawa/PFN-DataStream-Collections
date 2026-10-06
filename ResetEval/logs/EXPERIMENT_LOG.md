# ResetEval experiment log

本文件只记录"按错误率重置在表格基础模型（TFM）上不安全"这篇评测型文章的工作。目标期刊 TMLR（用户 2026-10-06 决定）。其他项目各有自己的日志；本项目需要的代码从其他项目复制进 `code/`，不跨项目导入。

## 2026-10-06：立项与现有材料（用户："那就TMLR吧"）
- **来由**：DriftTriage 方法线终止时给出的三个去向之一（"误差驱动的重置在 TFM 上不安全"的评测型文章，见 `DriftTriage/logs/EXPERIMENT_LOG.md` 10-06 02:27 一条）。之后在"值得做的方向"排序里列第 4。用户选 TMLR：没有截止日期，只审结论是否正确和有用，不要求方法新颖。
- **现有材料**（都在 MICE 里，尚未复制）：
  - 29 条真实流（13 个数据源）上 ddm 相对 fifo 平均 −1.80 点、最差 −9.57 点（`MICE/logs/EXPERIMENT_LOG.md` 789 行附近；结果在 `MICE/results_*/<流>__ddm1000.npz`、`__fifo1000.npz`）。
  - 同一批流上 ddm 的概率指标：ECE 2.59（fifo 1.73），log-loss 52.39（fifo 42.81）（同一日志 946 行附近）。
  - DriftTriage 的 lref 检测器：重置次数约为 DDM 的一半，合成流上不差，poker 上比 fifo 低 3 点。
  - 与主张相反方向的证据，必须写进去：概念按块突变的合成流上重置有大幅收益（GrayContext 流实验，grid_c30_b2000_s0 clean：ddm 93.75，fifo 82.10）。
- **与 MICE 的重叠**：ddm 对 fifo 的数字已写进 MICE 初稿。本文不能只是复述，要在 MICE 之外给出新的东西（更多检测器、更多 backbone、机理分析、替代做法）；MICE 里那一句保留，引用关系等两篇的状态再定。
- **初步的研究问题（Claude 拟定，待用户确认）**：
  - RQ1 现象：多种误差驱动检测器（DDM、EDDM、ADWIN、HDDM、Page-Hinkley、KSWIN）在 TFM 上相对"不重置"的得失，真实流与合成流分开报；
  - RQ2 普遍性：换 backbone（TabPFN v2、TabICL；TabDPT 视情况）与上下文长度，现象是否保持；与训练式模型（Hoeffding 树等）对照——对它们重置是否仍有利；
  - RQ3 机理：重置后的恢复时间、误报率、重置前后上下文的有用性；为什么 TFM 的"模型就是上下文"使得误报的代价更高；
  - RQ4 替代做法：部分替换上下文而非清空、按检测器置信度缩短窗口、lref 式少重置，哪种在两类流上都不吃亏。
- **状态**：只立项，没有运行任何东西。GPU 目前被 GrayContext/Emergence 的两个收尾检查占用（tmux `next`）。

## 2026-10-06 13:37：阶段 1——RQ1 现象、RQ3 机理与 RQ4 的两个替代做法（设计与假设，运行前写定；用户："好的，就按这四个研究问题做"）
- **脚本**：`code/reset_eval.py`（TFM 包装与 DDM 从 `MICE/code/run.py` 复制）。协议同 MICE：批 100 行，标签晚一批，上下文预算 M = 1000，TabPFN v2、4 个 estimator，种子 0。
- **关键实现**：上下文总是一个连续窗口 [lo, tB)，所以每次预测由 (lo, t) 唯一确定；预测按这个键缓存（`results/cache_tabpfn/`，float16），所有策略共用。TFM 在给定上下文时是确定的，缓存的预测就是该策略本来会得到的预测。
- **一个可以写进论文的结构性事实**：FIFO 预算为 M、批大小为 B 时，一次重置只影响此后 ⌈M/B⌉ = 10 批，之后上下文与 FIFO 完全相同。因此每次重置的得失可以逐次精确计算（重置后 10 批的准确率减去同批 FIFO 的准确率），这是 RQ3 的主要量。
- **核对（10-06 已做）**：在开发流 sea_s0 上，none 与 MICE 的 fifo1000、ddmM 与 MICE 的 ddm1000 逐批准确率完全相同（0 批不同）。
- **策略**：none（FIFO）；ddmM（MICE 的 DDM 副本）；river 0.26.1 的 8 个检测器，默认参数，输入为策略自身预测的逐行 0/1 错误：DDM、EDDM、FHDDM、HDDM_A、HDDM_W、ADWIN、Page-Hinkley、KSWIN；每个检测器三种动作：完全重置、保留最近 M/2 行（+half）、重置上下文与 FIFO 上下文按折扣 log-loss 加权混合（+hedge，η = 2，γ = 0.5，与 MICE 的窗口集成相同）。参数全部事先固定，不调。
- **流**：29 条真实流（MICE 论文的全部真实流）；合成流 42 条：6 个生成器族的测试种子 10–14（30 条）与网格流的测试种子 10、11（12 条）。先跑真实流。
- **假设（运行前写定）**：
  - H1：在 29 条真实流上，8 个检测器中至少 6 个的完全重置平均低于 none。
  - H2：在合成流上，至少 6 个检测器的完全重置平均高于 none（突变、可辨认的漂移上重置有利；这是反面证据，必须报告）。
  - H3（机理）：真实流上的单次重置，多数（> 50%）在其后 10 批里净亏于 FIFO；合成流上多数净赚。
  - H4（替代做法）：+hedge 在真实流上对 none 的平均差不低于 −0.2 点，同时在合成流上保留完全重置收益的至少一半；+half 介于两者之间。
- **预期**：H1、H2 成立；H3 成立；H4 不确定（hedge 每批调用两次 TFM，混合权重需要几批才能跟上）。
- **运行**：tmux `re1`，与 GrayContext/Emergence 的收尾检查（tmux `next`）并行，共两条链在 GPU 上；按文件续跑，失败重试。

## 2026-10-06 17:47：并入本文的补充现象（只是记录，没有运行任何东西；用户确认现象型的文章只有本文这一篇，"不是的话没必要做，还是方法为主"）
- 本文的主线仍是"按错误率重置在 TFM 上有害"。以下同一主题（传统流学习的做法在 in-context 学习器上失灵）的现象作为补充证据并入，数据都在各自项目的结果里，写作时再定放正文还是附录：
  - EM 先验校正：在所有流设定下准确率 −6 到 −8 点，ECE 从约 3.5 升到约 15（`Emergence/logs/EXPERIMENT_LOG.md`，10-06 流上 Observation 与稀有新类两条）。
  - 复制上下文行：每行复制 4 份，对称 20% 噪声下比不处理低 7.1 点（`GrayContext/logs/EXPERIMENT_LOG.md`，修复探查的 rep4）。
  - 按模型自身预测过滤或改标：静态下标记精度 0.80，流上只有 0.23–0.40，干净流上也大幅变差（GrayContext，流上 Observation 与阈值收尾检查）。
  - 为新类减少旧类行：新类排序 AUROC 反而下降，准确率 −5 到 −12 点（Emergence，抢救实验）。
- 这些现象来自不同的协议，并入时要分别说明协议，不能混成一张表。

## 2026-10-06 21:13：re1 重启（用户："那先重启 re1 接着跑"）
- **停下的原因**：日志最后一行写于 19:02（h4_covertype_d hddma+half），之后没有 RETRY 或 CHAIN_DONE；WSL 约在 21:00 重新启动（系统进程都从 21:00 开始），tmux 会话随之消失。停下时 29 条真实流完成 20 条，h4_covertype_d 完成 13/26 个策略，合成流还没开始。
- **重启**：同一条命令（同样的流顺序、环境变量与重试循环），tmux `re1`，按文件续跑，已有的 540 个结果文件跳过。`re1.log` 里加了一行 RESTART 作标记。
- **损失**：预测缓存在每条流结束时才写盘，所以 h4_covertype_d 已算过的 TFM 预测要重算一遍（结果不变，因为 TFM 在给定上下文时是确定的），只是多花时间。
- **预计**：剩约 8 条真实流 + 42 条合成流，单链 4–7 小时。
- **22:43 加链**：合成流跑完后 GPU 利用率降到 55%，加一条 `re1f` 跑 insects_abrupt_balanced（与 re1 的清单末尾重叠，碰到时只重复计算，结果相同）。
- **23:00 阶段 1 运行完毕**：71 条流（29 真实 + 42 合成）× 26 个策略全部有结果（`results/tabpfn_M1000/`，另有开发流 sea_s0 的 7 个）。22:07 起 6 条链并行（后加 re1f），之后共 4 次重试（22:09:13、22:16:02、22:16:22、22:42:42），22:43 以后没有重试。假设 H1–H4 的分析尚未运行。

## 2026-10-06 23:06：阶段 1 的分析——H1–H4 全部成立，但真实流上的损失集中在 poker 与 covertype 两个来源（用户："跑 ResetEval 的 H1–H4 分析"；`code/analyse_stage1.py` → `results/stage1_summary.csv`、`results/stage1_resets.csv`、`results/console_stage1.txt`）
- **口径**：每条流的准确率为逐批平均，流之间等权；差值都相对 none（FIFO），单位为百分点。单次重置的得失 = 重置后第 t 到 t+9 批（遇到下一次重置就截断）与 none 同批准确率之差的总和（单位：点·批）。
- **与 MICE 的一致性**：ddmM（MICE 的 DDM 副本）在 29 条真实流上平均 −1.80、最差 −9.57，与 MICE 初稿中的数字相同。river 的 DDM（ddm）是另一种实现，平均 −1.75，与 ddmM 在单条流上最多差 1.27 点，这不是错误。
- **H1 成立（8/8）**：真实流上完全重置平均低于 none：ddm −1.75，eddm −5.34，fhddm −5.47，hddma −6.65，hddmw −6.37，adwin −6.73，ph −5.38，kswin −5.66。
- **H2 成立（8/8）**：合成流上完全重置平均高于 none：fhddm +1.69，其余 7 个在 +9.96 到 +11.75 之间，42 条流中 30–42 条更好。
- **H3 成立**：真实流上 28534 次单次重置，87.6% 净亏、10.4% 净赚，每个检测器的净亏比例都在 80.6%–89.8%；合成流上 3346 次，82.7% 净赚（fhddm 只有 58.3%，eddm 69.8%）。
- **H4 成立（8/8 个检测器、两部分都满足）**：+hedge 在真实流上为 −0.05 到 +0.19（平均 +0.09，要求 ≥ −0.2），合成流上 +10.14 到 +11.38，保留了完全重置几乎全部的收益（平均 9.83，要求 ≥ 4.97）；+half 在真实流上介于两者之间（−0.19 到 −1.14），但合成流上只拿到 +0.7 到 +4.2。
- **必须同时报告的限定（Claude 核对后加的）**：
  - 真实流上的平均损失主要来自两个来源：covertype 的四段（h3_covertype_b/c、h4_covertype_d/e，大多数检测器 −25 到 −48 点）和 poker 的四段（−4 到 −13 点）。完全重置的中位数只有 −0.04 到 −1.13，胜出的流为 4–9/29。去掉含 poker、covertype 的流后，8 个检测器的平均在 −0.46 到 +0.24 之间，基本持平。
  - 这些段来自同一个源数据集，不是相互独立的样本，统计检验要按来源聚类。所以论文里"重置有害"的准确说法应该是：在少数来源上有严重害处，在其余来源上大体无害也无益；而不是"普遍有害"。
- **解读（Claude 的判断）**：+hedge（把重置后的上下文和 FIFO 上下文按近期损失加权混合）在两类流上同时接近最优，是本文 RQ4 的主要正面结果。它和 MICE 的窗口集成是同一个混合规则，写作时要说明两者的关系。

## 2026-10-06 23:07：按来源聚类的统计检验（用户："按来源聚类做统计检验"；事后分析，不是事先登记的检验；`code/cluster_tests.py` → `results/stage1_cluster_tests.csv`、`results/console_cluster_tests.txt`）
- **聚类**：真实流 9 个来源（covertype 5 段、poker 5、airlines 5、insects 9 条，以及 elec2、phishing、rialto、spam、weather 各 1）；合成流 7 个生成器族（grid 12 条，其余各 5 条）。每个来源内先对流求平均，来源之间等权。检验方法：来源层面的 Wilcoxon 符号秩检验（双侧）、正负计数、95% 来源 bootstrap 区间（10^4 次，种子 0），8 个检测器内做 Holm 校正。
- **功效上限**：9 个来源时 Wilcoxon 能达到的最小 p 为 0.0039，7 个来源时为 0.0156；Holm 校正后合成流最小只能到 0.125。只有几个来源的 bootstrap 区间偏窄（偏乐观）。
- **真实流，完全重置**：来源加权的平均差 −1.25（ddm）到 −4.55（adwin）；9 个来源里只有 2 个为正（insects、rialto），5–7 个为负。未校正 p：eddm 0.039，其余 0.08–0.30；**Holm 校正后 8 个检测器全部不显著**（0.31–0.78）。bootstrap 区间对 eddm、fhddm、hddmw、adwin 不含 0。
- **按来源看**：covertype −2.4 到 −32，poker −5 到 −11，elec2 −0.6 到 −2.1，spam −0.3 到 −2.0，weather 0 到 −4.9，airlines −0.1 到 −1.7；insects +0.0 到 +0.8，rialto +0.2 到 +1.2；phishing 约 0（几乎不触发重置）。
- **去掉 covertype、poker 后（7 个来源）**：完全重置为 −0.05 到 −1.17，全部不显著，区间都含 0。
- **合成流，完全重置**：+0.93（fhddm）到 +9.43；7 个族中 5–7 个为正、0–2 个为负；未校正 p 为 0.016–0.11；Holm 后全部为 0.125（达到这个样本量的下限）。
- **+hedge**：真实流 −0.02 到 +0.16，所有 p ≥ 0.74；区间下限 −0.11 到 −0.42，所以"不低于 −0.2"的非劣性只在 ph（−0.11）、fhddm（−0.18）上由区间支持，其余检测器区间下限低于 −0.2，**非劣性没有得到统计支持**。合成流 +1.16 到 +9.17，方向与完全重置一致。
- **结论（Claude 的判断）**：方向在两组上都清楚而且一致（真实流 8/8 个检测器、多数来源为负；合成流 8/8 为正），但按来源聚类后，真实流上的损害没有一项能通过多重比较校正，原因是只有 9 个来源，并且损失集中在 covertype、poker。写论文时不能说"显著有害"，只能报告来源层面的效应大小、符号计数和区间；要做出显著性结论需要更多独立来源（例如加入更多真实流数据集，而不是同一数据集的更多段）。

## 2026-10-06 23:09：加入独立的真实流（用户："加入更多独立的真实流数据集"；选择规则与预处理在下载和运行前写定）
- **目的**：来源聚类后只有 9 个真实来源，检验功效不够（见 23:07）。加的是新的独立来源，不是已有数据集的更多段。
- **选择规则**：公开可下载、按时间排列、文档里写明有时间漂移或按时间采集的分类数据集；至少 5000 行、至多 10 类（TabPFN v2 的上限）；此前没有用过。候选（全部列出，能下载的都用）：
  1. Gas Sensor Array Drift（UCI 224）：13910 行、128 特征、6 类，按 batch 1→10（36 个月）排列。
  2. Occupancy Detection（UCI 357）：三个文件合并后按时间戳排序，5 个特征，2 类。
  3. Room Occupancy Estimation（UCI 864）：按日期和时间排序，16 个特征，标签为房间人数（0–3，4 类）。
  4. Bank Marketing（UCI 222，bank-additional-full）：文件本身按日期排列（2008-05 到 2010-11）；按 UCI 的说明去掉 duration（通话时长只有事后才知道）。
  5. KDD Cup 99（10% 子集，经 sklearn 的镜像下载）：23 个标签按标准方式归为 5 类（normal、dos、probe、r2l、u2r）。
- **统一预处理**：取前 100000 行（同 h2 的 CAP）；类别型列转为整数编码；时间列只用于排序，不作为特征；标签按出现的取值排序编号。
- **事先写定的排除规则**：多数类比例 ≥ 0.98 的流排除（几乎全是同一类，不能区分策略）；另外照 h2 的做法记录滑动随机森林与多数类的准确率，只作描述，不用于排除。
- **运行**：同阶段 1 的 26 个策略、同参数，输出与原流放在一起（`results/tabpfn_M1000/`），数据放在 `ResetEval/data/`（不写进 MICE 的目录）；`reset_eval.py` 加环境变量 RESET_DATA 指定数据目录，默认不变。
- **分析**：来源从 9 个增加到最多 14 个；按 23:07 同样的方法（来源层面 Wilcoxon、bootstrap 区间、8 个检测器内 Holm）重新检验，并单独报告新来源上的结果（这是唯一一组没有被看过的数据）。
- **23:12 数据构建结果**（`code/streams_new.py` → `data/*.npz`、`results/console_streams_new.txt`）：五个都通过排除规则，都使用。
  - gas：13910 × 128，6 类，多数类 0.216；滑动 RF 0.834，滑动多数类 0.178。
  - occupancy：20560 × 5，2 类，多数类 0.769；RF 0.958，多数类 0.591。
  - room：10129 × 16，4 类，多数类 0.812；RF 0.950，多数类 0.841。
  - bank：41188 × 19，2 类，多数类 0.887；RF 0.877，多数类 0.871（几乎没有可学的信号，只作描述，不排除）。
  - kdd：前 100000 行 × 41，5 类（计数 41844/56237/1808/102/9），多数类 0.562；RF 0.995，多数类 0.936。
  - 运行：tmux `rn_<name>`，每个数据集一条链，`RESET_DATA=../data`，日志 `results/rn_<name>.log`。原始文件在 `data/_raw/`，已加进 `.gitignore`。

## 2026-10-06 23:23：新来源的结果与 14 个来源的聚类检验（`code/analyse_new_sources.py` → `results/new_sources_summary.csv`、`results/new_sources_cluster_tests.csv`、`results/console_new_sources.txt`；5 条链 0 次重试）
- **新的 5 个来源（此前没有看过）上的完全重置**：8 个检测器在 gas（−5.0 到 −7.4）、occupancy（−1.0 到 −2.7）、room（−2.2 到 −3.0）上都为负；bank（−0.21 到 +0.10）和 kdd（−0.30 到 +0.03）接近 0（none 的准确率分别为 89.9、98.9）。来源加权平均 −1.78 到 −2.47，4–5/5 个来源为负。5 个来源时 Wilcoxon 能达到的最小 p 是 0.0625，所以这一组单独不可能显著；bootstrap 区间都不含 0。
- **新来源上的单次重置**：912 次，净亏 45.9%，净赚 14.5%，其余约 40% 恰好为 0（kdd、bank 上很多重置不改变预测）。去掉为 0 的部分，净亏与净赚约为 3:1。
- **14 个来源（9 + 5）的聚类检验，完全重置**：8 个检测器的平均差在 −1.67 到 −3.67 之间，9–12/14 个来源为负，未校正 p 为 0.002–0.034（全部 < 0.05）。**Holm 校正后 eddm 显著（0.019），其余 7 个在 0.061–0.095 之间**；bootstrap 区间全部不含 0。与 9 个来源时（Holm 后 0.31–0.78）相比，结论明显变强，但除 eddm 外仍没有达到校正后的 0.05。
- **H4 在新来源上不成立（必须报告的反面结果）**：+hedge 在新来源上为 −0.37 到 −0.93（room −0.4 到 −1.9，gas −0.9 到 −2.1，occupancy −0.4 到 −1.6），8 个检测器全部低于 −0.2 的界限；bootstrap 区间都在 0 以下。14 个来源合起来为 −0.03 到 −0.35，区间下限 −0.30 到 −0.80。原来 29 条流上的"+hedge 几乎没有代价"只在原来的 9 个来源上成立。+half 在新来源上为 −0.06 到 −0.59，在 room 上为正（+0.34 到 +0.36）。
- **解读（Claude 的判断）**："完全重置在真实流上有害"在新的、此前未看过的来源上得到了重复（方向 8/8，幅度 2 点左右，小于 covertype、poker），14 个来源时证据接近校正后的显著水平。"混合（+hedge）可以避开代价"这一正面结论没有在新来源上重复。一个未经检验的猜测：在较小的数据集（room 1 万行、gas 1.4 万行）上，混合权重还没来得及调整，重置分支就已经造成了损失。论文里 RQ4 的结论要改成"混合减小了损失，但不能消除"，并报告新来源上的这组数字。

## 2026-10-06 23:25：第二批独立真实流（用户再次："加入更多独立的真实流数据集"；选择、预处理在下载和运行前写定）
- **规则不变**（同 23:09）：公开可下载、按时间记录、至少 5000 行、至多 10 类、此前没用过；先取前 100000 行；多数类比例 ≥ 0.98 排除。另外不用其他项目已经用过的数据集（例如 AgDR 的 N-BaIoT），以免项目之间混用。
- **候选（全部列出，能下载、能按规则构建的都用）**：
  1. EEG Eye State（UCI 264）：14980 行，连续 117 秒的脑电记录，2 类（睁眼/闭眼），文件顺序即时间顺序。
  2. Online News Popularity（UCI 332）：39644 篇文章，按发表时间排序（timedelta 从大到小，即从早到晚）；去掉 url、timedelta；标签为 shares ≥ 1400（原论文 Fernandes et al. 的二分类定义）。
  3. Gas sensors for home activity monitoring（UCI 362）：按记录编号和时间排序，特征为 8 个电阻值加温度、湿度，标签为该次记录的刺激（background/wine/banana，3 类）；时间列只用于排序。
  4. Wall-Following Robot Navigation（UCI 194）：5456 行，24 个超声波传感器，4 类，文件顺序即记录顺序。
  5. Activity Recognition from Single Chest-Mounted Accelerometer（UCI 287）：按受试者编号 1→15、文件内顺序拼接，去掉标签为 0 的行，7 类，前 100000 行（大约只覆盖第一个受试者）。
- **分析**：同 23:23 的方法，单独报告这 5 个来源，并与前面 14 个合成 19 个来源重新做检验。
- **23:27 第二批数据构建**（`code/streams_new.py 2` → `results/console_streams_new2.txt`）：五个都通过排除规则。
  - eeg：14980 × 14，2 类，多数类 0.551；滑动 RF 0.689，滑动多数类 0.565。
  - news：39644 × 58，2 类，多数类 0.534；RF 0.654，多数类 0.544。
  - home：前 100000 行 × 10，3 类，多数类 0.689；RF 0.965，多数类 0.878。
  - wall：5456 × 24，4 类，多数类 0.404；RF 0.951，多数类 0.349。
  - chest：前 100000 行 × 3，7 类，多数类 0.337；RF 0.952，多数类 0.950（标签成段出现）。
- **与 23:25 写定内容的两处偏差**：
  - (a) home 的标签：写定的是"整次记录的刺激"，但每次记录包含刺激前后的时段（time < 0 或 time > dt，此时没有刺激）。构建时把这些时段标为 background，只有刺激期间用该次记录的类。这是在看结果之前、为了让标签与数据说明一致做的修正。
  - (b) chest 的 UCI 新地址返回 404，改用旧镜像 `ml/machine-learning-databases/00287/`。
- **运行**：tmux `rn_<name>`，5 条链。
- **关于"继续加来源"的说明**：加第二批的决定是在看到第一批之后做出的（逐步加入，直到效应清楚为止），这属于序贯决策。所以最终的 p 值不能当作单次事先设计的检验来解读；论文里要报告每一批的结果，而不只报合并后的结果。
- 23:30 `analyse_new_sources.py` 改为按批次运行（参数为批次号）；第一批的输出改名为 `results/new_sources1_*.csv`（内容不变）。

## 2026-10-06 23:35：阶段 2——换 backbone 为 TabICL 的重复（用户："自己迭代几轮，gpu利用率别低"；设计与判定在运行前写定）
- **动机**：立项时写明本文要比 MICE 多出"更多 backbone"；同时让 GPU 在第二批新来源跑完后不空着。
- **设置**：`RESET_BACKBONE=tabicl`（TabICL 2.2.0，4 个 estimator，种子 0，与 MICE 的 TabICL 设置相同），其余与阶段 1 完全相同（26 个策略、参数不调）。流：全部 39 条真实流（原 29 条 + 两批新加的 10 条）与 42 条合成流。输出 `results/tabicl_M1000/`，缓存 `results/cache_tabicl/`。
- **运行**：`code/run_queue.sh`，共享队列 `results/queue_tabicl.txt`（真实流按长度从长到短，之后是合成流），每条流用 mkdir 加锁，多条链不会撞在同一条流上。开 7 条链（tmux `icl1`–`icl7`，日志 `results/icl<k>.log`），GPU 利用率低于 70% 时再加链，频繁重试时减链。
- **判定（同阶段 1 的阈值，来源层面）**：
  - H1'：19 个真实来源上，8 个检测器中至少 6 个的完全重置来源加权平均低于 none；
  - H2'：合成流（7 个族）上至少 6 个高于 none；
  - H3'：真实流上 > 50% 的单次重置净亏（不计恰好为 0 的），合成流上 > 50% 净赚；
  - H4'：+hedge 在真实来源上的来源加权平均 ≥ −0.2，同时在合成流上保留完全重置收益的至少一半。
- **预期**：H1'、H2'、H3' 与 TabPFN 一致；H4' 不确定（TabPFN 在新来源上已经不成立）。
- **23:36 队列锁的修正**：第一次启动时锁目录放在 /mnt/c 上，那里的 mkdir 不是原子操作，7 条链里有 4 条抢到了同一条流（约 30 秒后发现）。已全部停掉，删除这 30 秒里产生的输出（`tabicl_M1000`、`cache_tabicl` 都还是空的），锁目录改到 Linux 文件系统（`~/.reset_locks/`），各链间隔 2 秒启动；重启后 7 条链各占一条不同的流。

## 2026-10-06 23:38：第二批新来源的结果——与第一批方向相反；19 个来源合起来不再显著（`code/analyse_new_sources.py 2`、`... 1 2` → `results/new_sources2_*.csv`、`results/new_sources1_2_*.csv`、`results/console_new_sources2.txt`、`results/console_new_sources1_2.txt`）
- **第二批 5 个来源上的完全重置**：eeg 为 +3.3 到 +7.4（8/8 为正），home 为 +0.9 到 +1.5，chest 为 +0.7 到 +2.1，即三个来源上重置**有益**；wall 为 −2.2 到 −33.8（eddm、hddma 约 −33），news 为 0 到 −1.3。来源加权平均从 +1.56（ddm）到 −4.66（hddma），5 个来源中 3 个为正、1–2 个为负，所有 p ≥ 0.63。
- **单次重置**：770 次，净亏 40.6%，净赚 48.6%（wall 上 97% 净亏，chest 上 0%）。
- **19 个来源（9 + 5 + 5）**：完全重置的来源加权平均为 −0.82 到 −3.93，5–6 个来源为正、11–14 个为负；未校正 p 为 0.045–0.21，**Holm 校正后全部不显著（0.36–0.62）**，有 5 个检测器的 bootstrap 区间含 0。14 个来源时接近显著的结论（Holm 后 eddm 为 0.019）没有在第二批上重复。
- **+hedge 在 19 个来源上**：+0.13 到 +0.46，区间下限 −0.10 到 −0.55，p ≥ 0.50。
- **按来源看的尾部（8 个检测器平均，19 个来源，Claude 补算的描述）**：

  | | 完全重置 | +half | +hedge |
  |---|---|---|---|
  | 最差来源 | −26.2 | −4.3 | −1.6 |
  | 次差来源 | −17.6 | −2.6 | −1.4 |
  | 最好来源 | +6.3 | +0.7 | +6.0 |
  | 损失 > 1 点的来源数 | 7.5 | 3.0 | 2.6 |
  | 收益 > 1 点的来源数 | 3.1 | 0.0 | 3.8 |

- **解读（Claude 的判断）**：
  - "错误驱动的重置在真实流上普遍有害"不成立。效应强烈依赖来源：covertype、poker、wall、gas 上损失很大，eeg、chest、home、rialto、insects 上有收益，其余大多接近 0。19 个来源下，平均损失由少数来源的大损失驱动，不显著。
  - 更站得住的结论是关于风险的：完全重置的结果分布有很重的左尾（最差来源平均 −26 点）；+hedge 把最差来源的损失压到约 −1.6 点，同时保留了几乎全部收益（最好来源 +6.0，对比完全重置的 +6.3）。所以本文的主张可以从"重置不安全"改为"重置的风险是尾部的、依赖来源的，而对 FIFO 的对冲几乎不付代价就能去掉这个尾部"。
  - 这个尾部指标是看过数据之后才提出的，后面要在 TabICL 的结果上当作事先写定的检验来确认。
- **对 TabICL 阶段的补充判定（写于 TabICL 结果出来之前）**：
  - T1：19 个真实来源上，8 个检测器平均的"最差来源"，+hedge 比完全重置至少好 10 点；
  - T2：+hedge 的"最好来源"不低于完全重置最好来源的一半。
- **23:48 加链与收尾安排**：TabICL 每个策略平均比 TabPFN 慢 1.74 倍（34 个共有的策略对比），7 条链预计 3–4 小时；为赶在 05:00 机器重启前结束，加到 9 条链（`icl8`、`icl9`）。`code/finish_stage2.sh`（tmux `finish2`）在 9 条链都 CHAIN_DONE 后自动运行 `analyse_backbone.py tabicl`，并在本日志末尾追加判定结果（标明为自动写入）。`analyse_backbone.py tabpfn` 已在 TabPFN 结果上核对过：H1'–H4'、T1、T2 都成立，尾部数字与 23:38 的表相同（−26.23/6.32、−1.64/5.98）。
- **如果 05:00 重启时还没跑完**：所有结果按策略写盘、缓存每 200 次调用写盘，重启后用同样的命令重开 9 条链即可接着跑（先删 `~/.reset_locks/queue_tabicl`，已完成的文件会自动跳过），再运行 `finish_stage2.sh`。
- **23:50 记录安排**（用户："跑完记录到log里面，不光要记录做了什么实验得到什么结论还要记录这个机器的故障，我们怎么解决的，怎么监督利用率"）：机器故障、处理办法和利用率的监督方法写在 `env/MACHINE_LOG.md`（所有项目共用）；tmux `gpu_sampler` 每分钟记一行 GPU 利用率、显存和进程数到 `results/gpu_util_stage2.csv`；`finish_stage2.sh` 跑完后自动在本日志和 `env/MACHINE_LOG.md` 末尾追加判定结果、平均利用率、低于 70% 的分钟数和重试次数。
- **23:58 进度与截止**：开跑 21 分钟后，按 TabPFN 的逐策略耗时折算，完成约 5.7%（不计正在跑的流），整体可能要 3–6 小时，可能赶不上 05:00 重启。`finish_stage2.sh` 改为：9 条链都结束，或到 04:45，二者先到就运行分析；`analyse_backbone.py` 只用 26 个策略都齐的流，缺的流列为 PARTIAL，此时日志标题写明"部分结果，判定不作数"，并写出重启后续跑的步骤。队列是真实流在前，所以没跑完时缺的主要是合成流。
- **00:16** 已 commit 并 push（817752d）；`finish_stage2.sh` 结束时会把 ResetEval 的日志、结果表、代码和 `env/MACHINE_LOG.md` 自动 commit 并 push 到 main。

## 2026-10-07 00:55：阶段 3——TabPFN 换种子的重复（用户："那跑完还继续继续安排2小时的任务，反正你别让利用率掉下来，直到5点自动关机"；设计与判定在运行前写定）
- **动机**：阶段 1 每条流只跑了一次（种子 0）；本阶段检验结论是否依赖 backbone 的随机性。同时在 TabICL 结束后到 05:00 重启前让 GPU 不空闲。
- **代码**：`reset_eval.py` 加环境变量 RESET_SEED（TabPFN 的 random_state，默认 0 时路径不变；s > 0 时写到 `tabpfn_s<s>_M1000/`、`cache_tabpfn_s<s>/`）。队列脚本另存为 `run_queue2.sh`（队列行多一列种子）；正在跑的 `run_queue.sh` 没有改动（bash 边读边执行，改运行中的脚本可能出错；已从 git 恢复原样，逐字节一致）。
- **队列** `results/queue_seeds.txt`：种子 1 的 39 条真实流（从长到短）→ 种子 2 的真实流 → 两个种子的合成流。
- **接力**（`code/relay_seeds.sh`，tmux `relay`）：每有一条 TabICL 链结束，就启动一条种子链，保持约 9 个 GPU 进程；04:35 之后不再启动新链；04:40（或全部种子链结束）时运行 `seed_compare.py 1 2` 和 `analyse_backbone.py tabpfn_s1/s2`，结果追加到本日志，并 commit、push。利用率由 tmux `gpu_sampler3` 每分钟记录到 `results/gpu_util_stage3.csv`。
- **判定**（只用两个种子都跑完 26 个策略的流）：
  - S1：完全重置的逐流差值（8 个检测器合并）在种子 s 与种子 0 之间的 Pearson r ≥ 0.9（真实流）。
  - S2：在同一批真实流上，完全重置和 +hedge 的来源加权平均，8 个检测器中至少 7 个与种子 0 同号；T1（+hedge 在最差来源上比完全重置好 ≥ 10 点）和 T2 在两个种子上都成立。
- **预期**：时间只够种子 1 的大部分真实流，可能加上种子 2 的一部分；没跑完的部分会列为 PARTIAL。
- **01:35:57 中断与 01:38 重开**：WSL 虚拟机在 01:35:57 正常关机（journal 里是 systemd 完整的 poweroff 流程，不是 OOM 或进程崩溃；关机指令来自 Windows 一侧，原因未知）。关机前 GPU 利用率 99–100%，9 条链 0 次重试。01:38 删除 `~/.reset_locks/queue_tabicl`，用同一队列重开 9 条 TabICL 链（`icl1`–`icl9` 日志里有 RESTART 行），同时重开 `gpu_sampler`、`finish2`、`relay`（含 `gpu_sampler3`）。已完成的策略文件自动跳过；关机时正在跑的策略从头重跑。04:35/04:40/04:45 的截止时间不变。
- **01:44 保持利用率**（用户："如果5点前跑完任务你就放一点任务去跑，保持利用率90以上"）：新增 `code/keep_busy.sh`（tmux `keep_busy`）。它每 5 分钟算一次 GPU 平均利用率，低于 90% 就多开一条 `run_queue2.sh` 链。这些链先消化 `queue_seeds.txt`（和 relay 共用锁）；该队列的每一行都被领走之后，改用 `results/queue_seeds3.txt`（TabPFN 种子 3，81 条流，作备用）。最多加 6 条，显存超过 26 GB 时不加，04:35 之后不加。每次判断都记到 `results/keep_busy.txt`，日志写到 `results/extra*.log`。relay 04:40 的自动 commit 会一并带上这些结果。

## 2026-10-07 02:15：阶段 2（TabICL）运行完毕，分析已自动运行（自动写入，未经人工核对）
- 队列链 9/9 条 CHAIN_DONE；重试 0 次。判定结果（原样摘自 `results/console_stage2_tabicl.txt`）：
  - H1' full below none on real: 8/8 (need >= 6) -> holds
  - H2' full above none on synthetic: 8/8 (need >= 6) -> holds
  - H3' real: 88.3% of 30217 non-zero resets are losses; synthetic: 86.8% of 3172 resets are wins (need > 50% each) -> holds
  - H4' per detector 8/8; detector average: real +hedge 0.22 (need >= -0.2), synthetic +hedge 8.26 vs half of full 4.19 -> holds
  - tail over 19 real sources, detector-averaged (worst, best): {'full': (np.float64(-26.46), np.float64(4.78)), '+half': (np.float64(-5.37), np.float64(0.87)), '+hedge': (np.float64(-1.74), np.float64(4.57))}
  - T1 worst source: +hedge - full = 24.71 (need >= 10) -> holds
  - T2 best source: +hedge 4.57 vs half of full 2.39 -> holds
- 运行期间的 GPU：145 samples (one per minute), mean utilisation 92.4%, minutes below 70%: 16, mean memory 6529 MiB（`results/gpu_util_stage2.csv`）；CUDA 重试 0 次。机器方面的记录见 `env/MACHINE_LOG.md`。

## 2026-10-07 06:08：阶段 3（TabPFN 种子 1）结果——04:14 提前关机，分析在重启后手动运行
- **中断**：WSL 在 04:14:40 正常关机（journal 是完整 systemd poweroff，与 01:35 那次相同，来自 Windows 一侧），早于 04:40 的自动分析和 commit；06:06 重启后手动运行 `seed_compare.py 1 2` 和 `analyse_backbone.py tabpfn_s1`（输出 `results/console_stage3_seeds.txt`、`console_stage3_tabpfn_s1.txt`）。
- **完成度**：种子 1 真实流 36/39 完整（缺 gas、h2_rialto、h2_spam，关机时在跑）；种子 2 只有 3 个策略文件；合成流两个种子都没开始。种子 3 备用队列未用到。
- **判定（只针对种子 1 真实流，PARTIAL）**：
  - S1：完全重置逐流差值与种子 0 的 Pearson r = 0.975（≥ 0.9）→ 成立；平均绝对差 0.57 点。
  - S2：来源加权平均的符号，完全重置 8/8、+hedge 8/8 与种子 0 一致；T1（最差来源 +hedge − full）种子 0 24.76、种子 1 24.37；T2 两个种子都成立 → 成立。
  - H1'（真实流 full 低于 none）8/8 成立；真实流上 89.7% 的 28174 次非零重置是损失；+hedge 真实流平均 +0.34。H2'/H3'/H4' 的合成部分无数据，不作判定。
- **GPU**：196 个样本（每分钟一个，00:55–04:13），平均利用率 95.8%，低于 70% 的分钟 8 个（`results/gpu_util_stage3.csv`）。
- **结论**：真实流上的结论对 TabPFN 随机种子稳健；种子 2 和合成流未跑，需要的话用 `run_queue2.sh` 接着跑（已完成的文件会自动跳过）。

## 2026-10-07 06:11：阶段 3 续跑（用户："接着跑种子2和合成流"）
- 删掉 `~/.reset_locks/queue_seeds`，用同一队列 `results/queue_seeds.txt` 重开 9 条 `run_queue2.sh` 链（tmux `seedR1`–`seedR9`，日志 `results/seedR*.log`）；已完成的策略文件自动跳过。剩下的是：种子 1 的 gas、h2_rialto、h2_spam，种子 2 的 39 条真实流，以及两个种子各 42 条合成流。
- tmux `gpu_sampler3` 接着往 `results/gpu_util_stage3.csv` 记录；`code/finish_stage3.sh`（tmux `finish3`）在 9 条链都 CHAIN_DONE 后运行 `seed_compare.py 1 2` 和 `analyse_backbone.py tabpfn_s1/s2`，把结果追加到本日志，再 commit 并 push。吸取 04:14 的教训，运行期间每小时把日志 commit 一次。判定标准不变（S1、S2，以及每个种子的 H1'–H4'、T1、T2）。
- 开跑 1 分钟后：GPU 99%，显存 13.2 GB。

## 2026-10-07 06:22：无人值守运行的安排与事先写定的判定（用户："你自己迭代吧，保持 util 利用率不低 90 吧，然后内存不超过 20G，就行了，结束一个任务你就帮我自己迭代加任务上去"）
- **约束的执行**：`code/supervisor.sh`（tmux `supervisor`，决定记到 `results/supervisor.txt`）。"内存不超过 20G"对 GPU 显存和系统内存都执行。规则如下：
  - 每分钟采样一次。显存连续两次 > 19.5 GB，就停掉最新的一条 GPU 链，把它正在跑的那条流放回队列，GPU 链的上限减一；内存 > 19.5 GB，先停 CPU 链。
  - 每 5 分钟判断一次。平均利用率 < 90%、显存 < 16.5 GB、内存 < 17 GB，并且 GPU 队列还有没领走的行，就加一条 GPU 链（< 70% 时加两条）。
  - CPU 链最多保持 5 条。
  - 某个队列全部完成时，`code/stage_done.sh` 运行这个队列对应的分析，把判定追加到本日志，再 commit 并 push。
  - 每小时 commit 一次日志。
  - 原来阶段 3 的 `finish3` 已停掉，由 supervisor 接管（队列 `queue_seeds` 完成时运行 `seed_compare.py 1 2` 和 `analyse_backbone.py tabpfn_s1/s2`，判定 S1、S2 不变）。
- **新的链脚本** `code/run_queue3.sh`：按顺序处理多个队列。行格式为"流 数据目录 种子 M 策略集 类型"。完成的行写 done 标记；被停掉的行解锁后，会在下一遍被重新领走。
- **代码改动**（旧策略的输出不变）：
  - `reset_eval.py` 加了 `RESET_POLSET=hsens`（策略名 `<det>+hedge@e<η>g<γ>`）。核对：在 bank 上，`ddm+hedge@e2g0.5`、`adwin+hedge@e2.0g0.5` 与原来的 `+hedge` 逐批准确率、重置位置完全相同。
  - 缓存写盘时与磁盘上的文件合并，因为现在会有多个进程共用 seed 0 的缓存。
  - `analyse_backbone.py` 可以接受 `tabpfn_M500` 这样的目录名。
- **GPU 队列（按顺序）**：
  1. `queue_seeds`（阶段 3 剩余部分）；
  2. `queue_M500`、`queue_M2000`：TabPFN 种子 0，上下文预算 M = 500、2000，81 条流 × 26 个策略。属于 RQ2，判定沿用 H1'–H4'、T1、T2；
  3. `queue_seeds3b`：种子 3，作备用。
- **CPU 队列（nice 19）**：
  1. `queue_hsens`：+hedge 的超参数敏感性。TabPFN 种子 0，M = 1000，7 个变体（γ = 0.5 时 η ∈ {0.5, 1, 4, 8}；η = 2 时 γ ∈ {0.25, 0.75, 0.9}），8 个检测器，大部分预测走缓存。
  2. `queue_trained_ht`、`queue_trained_nb`：训练式学习器对照（RQ2 后半）。`code/trained_eval.py`，river 0.26.1 的 HoeffdingTree 和 GaussianNB，默认参数，协议与 TFM 相同（批 100、标签晚一批、每批最多一次检测）。策略为 none、8 个检测器的完全重置（换一个新模型），以及 +hedge（不重置的模型与重置后的模型按同一规则混合）。
- **判定（运行前写定，`code/analyse_variants.py`）**：
  - +hedge 敏感性，对每个变体：HS1 真实流检测器平均 ≥ −0.2；HS2 最差来源上比完全重置好 ≥ 10 点；HS3 合成流保留完全重置收益的至少一半。7 个变体都满足三条，才算"对超参数稳健"。
  - 训练式对照，与同一批流上的 TabPFN 比较：TR1 完全重置的真实流平均（检测器平均）比 TabPFN 高 ≥ 2 点；TR2 最差来源比 TabPFN 好 ≥ 10 点；TR3 真实流上非零单次重置的净亏比例 < 70%（TabPFN 约 88%）。
  - 预期：HS 大体成立，η 很小（0.5）时混合跟不上，HS3 可能不成立；TR1–TR3 成立。如果 TR 不成立，"TFM 特有"的说法要撤回，改成"错误驱动的重置普遍有风险"。
- **07:40 检查**：近 1 小时 5 分钟平均利用率 94–99%，显存 ≤ 13.0 GB，内存 17.2–18.5 GB。06:52 内存到 19.8 GB，supervisor 按规则停掉 1 条 CPU 链，上限改为 4 条，之后没有再超。种子 2 的两条 covertype 段各有 1 次 cudaErrorLaunchFailure（MACHINE_LOG 中已知的问题），自动重试后继续。进度：queue_seeds 52/162，hsens 18/81；GPU 队列还剩 344 行未领，不需要加任务。

## 2026-10-07 起的无人值守运行：queue_hsens 全部完成，10-07 08:14 自动分析（自动写入，未经人工核对）
- full reset: real mean -2.84, worst source -26.23, synthetic 8.02
- HS variants passing HS1-HS3: 7/7 -> robust; HS1 7/7, HS2 7/7, HS3 7/7
- 完整输出：`results/console_queue_hsens.txt`。
- **08:40 人工核对（hsens）**：81 条流都齐（没有 PARTIAL）。默认 +hedge 一行（最差来源 −1.64）、完全重置一行（最差来源 −26.23）与 10-06 23:38 的表相同，所以敏感性实验和原实验口径一致。7 个变体之间：真实流平均在 +0.24 到 +0.29 之间，最差来源在 −1.58 到 −1.73 之间，合成流在 +7.86 到 +7.93 之间，即 η 在 0.5–8、γ 在 0.25–0.9 的范围内结果几乎不变。事先的预期"η = 0.5 时 HS3 可能不成立"没有发生。结论：+hedge 的效果不依赖这两个超参数，可以写进论文。
- **同一检查，资源**：07:59 和 08:01 显存两次连续超过 19.5 GB（19.8 GB、19.6 GB，当时有几条 covertype 段在跑），supervisor 各停掉 1 条种子链（seedR9、seedR8），把它们的流放回队列，GPU 链上限降到 7。之后显存 ≤ 17.4 GB，利用率 86–98%（08:09、08:14 两次低于 90%）。显存上限优先于利用率，所以不再加链。

## 2026-10-07 起的无人值守运行：queue_seeds 全部完成，10-07 09:17 自动分析（自动写入，未经人工核对）
- == seed 1 vs seed 0, real: 39/39 streams complete in both; Pearson r of per-stream d (full resets) 0.975; mean |diff| 0.56 points
- S1 r >= 0.9 -> holds; S2 sign kept: full 8/8, +hedge 8/8; T1 (+hedge - full, worst source) {'seed0': np.float64(24.59), 'seed1': np.float64(24.29)}; T2 {'seed0': np.True_, 'seed1': np.True_} -> holds
- == seed 2 vs seed 0, real: 39/39 streams complete in both; Pearson r of per-stream d (full resets) 0.973; mean |diff| 0.64 points
- S1 r >= 0.9 -> holds; S2 sign kept: full 8/8, +hedge 8/8; T1 (+hedge - full, worst source) {'seed0': np.float64(24.59), 'seed2': np.float64(23.99)}; T2 {'seed0': np.True_, 'seed2': np.True_} -> holds
- == seed 1 vs seed 0, syn: 42/42 streams complete in both; Pearson r of per-stream d (full resets) 0.999; mean |diff| 0.22 points
- == seed 2 vs seed 0, syn: 42/42 streams complete in both; Pearson r of per-stream d (full resets) 0.999; mean |diff| 0.21 points
- H1' full below none on real: 8/8 (need >= 6) -> holds
- H2' full above none on synthetic: 8/8 (need >= 6) -> holds
- H3' real: 87.8% of 29516 non-zero resets are losses; synthetic: 84.0% of 3283 resets are wins (need > 50% each) -> holds
- H4' per detector 8/8; detector average: real +hedge 0.28 (need >= -0.2), synthetic +hedge 7.93 vs half of full 4.03 -> holds
- tail over 19 real sources, detector-averaged (worst, best): {'full': (np.float64(-25.9), np.float64(6.18)), '+half': (np.float64(-4.02), np.float64(0.71)), '+hedge': (np.float64(-1.62), np.float64(5.98))}
- T1 worst source: +hedge - full = 24.29 (need >= 10) -> holds
- T2 best source: +hedge 5.98 vs half of full 3.09 -> holds
- H1' full below none on real: 8/8 (need >= 6) -> holds
- H2' full above none on synthetic: 8/8 (need >= 6) -> holds
- H3' real: 88.0% of 29641 non-zero resets are losses; synthetic: 84.6% of 3284 resets are wins (need > 50% each) -> holds
- H4' per detector 8/8; detector average: real +hedge 0.26 (need >= -0.2), synthetic +hedge 7.91 vs half of full 4.02 -> holds
- tail over 19 real sources, detector-averaged (worst, best): {'full': (np.float64(-26.0), np.float64(6.94)), '+half': (np.float64(-3.76), np.float64(1.27)), '+hedge': (np.float64(-2.01), np.float64(6.6))}
- T1 worst source: +hedge - full = 23.99 (need >= 10) -> holds
- T2 best source: +hedge 6.60 vs half of full 3.47 -> holds
- 完整输出：`results/console_queue_seeds.txt`。

## 2026-10-07 起的无人值守运行：queue_trained_ht 全部完成，10-07 09:33 自动分析（自动写入，未经人工核对）
- 81 common streams; detector-averaged (real mean, worst real source, synthetic mean):
- full reset: ht [  1.83 -17.47  12.46], TabPFN [ -2.84 -26.23   8.02]
- +hedge:     ht [ 3.55 -7.77 13.67], TabPFN [ 0.27 -1.64  7.91]
- TR1 full-reset real mean: ht - TabPFN = 4.67 (need >= 2) -> holds
- TR2 worst real source: ht - TabPFN = 8.76 (need >= 10) -> fails
- TR3 real: 69.9% of 33127 non-zero resets are losses for ht (TabPFN 88.1% of 29211; need < 70%) -> holds
- 完整输出：`results/console_queue_trained_ht.txt`。
