# MiceDuo experiment log

本文件只记录 MICE-DUO 的工作。MICE-DUO 是一篇独立于 MICE 的新论文（用户 2026-10-06："我觉得可以做一篇新论文，MICE-DUO"）。其他项目各有自己的日志；需要的代码复制进 `code/`，不跨项目导入。

## 2026-10-06 18:19：来由、与 MICE 的区别、可行性检查的设计与判定规则（运行前写定）
- **来由**：重读 Zhilin 的 WNB（Weighting Non-IID Batches for OOD Detection，Machine Learning 2024）后提出：WNB 的定理 1 说批越小，批与整体分布的差异越大；定理 2 把泛化误差写成含"按批差异加权"的项，并由界推出权重函数。对 in-context 学习器，上下文的大小与"过时的行"之间是同一种权衡，今天的一串负结果（重置、重加权、复制、过滤、减少旧类行都有害，见 ResetEval 日志 10-06 的补充现象一条）都是这个权衡的表现。
- **与 MICE 的区别（必须拉开，否则是增量工作）**：MICE 把过去的片段存成固定的专家，用延迟标签的损失加权混合（理论来自 MOOE 与 R-divergence）。MICE-DUO 每一步都从最近 H 个批里按"与最新一批的模型导向差异"重新挑选批，组成一个**非连续**的相关性上下文，与按时间的 FIFO 上下文并列（DUO = 时间上下文 + 相关性上下文），理论按 WNB 的"差异项 + 上下文大小项"来建。"DUO"的这个含义是 Claude 的理解，名称由用户定。
- **可行性版本的方法**（`code/check_duo.py`，参数全部事先固定）：候选为第 t−H … t−1 批（H = 100）；用只以最新一批 r 为上下文的 TFM 预测所有候选批，按 log-loss 排序；保留 r 和排名最前的 9 个批，共 1000 行。预测：fifo、sel、duo（两者按折扣 log-loss 加权混合，η = 2，γ = 0.5）。协议与 MICE 相同（批 100、标签晚一批、M = 1000、TabPFN v2、4 个 estimator、种子 0），只跑每条流的前 300 批。WNB 的连续权重函数这一版不用（TFM 不接受样本权重，复制行已知有害），先检验"挑选"本身有没有用。
- **开发集与测试集（运行前定下）**：开发集 = elec2 与 6 条 h2 流（airlines、phishing、poker、rialto、spam、weather）；其余 22 条真实流留作 MICE-DUO 的最终测试，在方法定下之前不碰。这些流都在 MICE 里用过，这里的"测试"指没有用于设计 MICE-DUO。
- **对照**：MICE 的最终方法与 FIFO 的逐批准确率从 MICE 的结果导出一次（`results/mice_reference.npz`，用 `MICE/code/reweight.simulate2(outer="brier", scale=0.5, temper=True)`，与 MICE 论文表格的设定相同），在相同的批上比较。调试运行确认本脚本的 fifo 与 MICE 的 fifo 逐批一致（h2_rialto 前 25 批 73.67）。
- **前 300 批的参照**（导出时算出，准确率）：MICE 对 FIFO —— airlines 68.17/68.15，phishing 94.60/94.57，poker 91.27/90.76，rialto 81.13/75.51，spam 94.25/94.49，weather 81.07/81.08，elec2 81.47/81.05。MICE 的收益几乎全来自 rialto。
- **判定规则**：
  - D1：duo 比 fifo 平均高至少 0.5 点，且至少 5/7 条流更好。
  - D2：duo 平均不低于 MICE。
  - D1、D2 都成立 → 立项，进入方法与理论；只有 D1 成立 → 挑选有用但不比 MICE 好，作为新论文不够；D1 不成立 → 放弃这一版的挑选规则（可以再试一个规则，但要在日志里另写判定）。
- **指标**：准确率、macro-F1、ROC AUC、ECE、log-loss；完整概率逐批保存。MICE 的参照只有准确率（它的缓存里有概率，需要时可再导出）。
- **预期**：D1 不确定；D2 在 rialto 上很难（MICE +5.6），我估计 D2 不成立的可能更大。
- **运行**：tmux `duo`，与 ResetEval 的 `re1` 并行（最多两条链）。

## 2026-10-06 21:30：duo 重启（用户："把 duo 也重启了吧"）
- **停下的原因**：18:25:26 一次 CUDA launch failure 后的重试没有留下新输出，`results/duo/` 里没有任何流的结果；WSL 约在 21:00 重新启动，tmux 会话随之消失。
- **重启**：同一条命令（同样的 7 条开发流、重试循环、结束后运行 `analyse_duo.py`），tmux `duo`，与 ResetEval 的 `re1` 并行，共两条 GPU 链。`console.txt` 里加了一行 RESTART 作标记。判定规则不变。
- **21:36 修正后再启动**：重启后 1.5 分钟内又出现一次 CUDA launch failure（RETRY 21:31:54），当时 GPU 显存 32.1/32.8 GB 已满。原因在本脚本：挑选一步用最新一批（100 行）拟合，一次预测约 9900 行候选，`predict_proba` 一次处理全部查询行，显存被占满。改为每次 1000 行分块预测（`check_duo.py` 的 `TFM.predict`）；TabPFN 的测试行互不影响，所以预测与原来相同，判定规则不变。改后显存稳定在约 11 GB（含 re1），4 分钟内无重试。
- **22:03 停掉 duo（用户："你盯着，有问题就停掉 duo"）**：分块后 spam、phishing、weather 三条流跑完（94.49/92.11/94.54、94.57/94.66/94.80、81.09/78.11/80.54，fifo/sel/duo %），之后在 elec2 上连续 4 次 CUDA launch failure（21:50:42、21:53:58 及其后两次），每次都从 elec2 开头重来（结果按整条流写盘）。按事先定的规则（自上一条流跑完后 4 次重试）自动停掉 `duo`，让 ResetEval 的 `re1` 单独跑。此时显存约 1 GB，不是显存问题，触发原因不明；`re1` 在 21:49、21:52 也各有一次重试。剩下 elec2、airlines、poker、rialto 四条，等 re1 结束后单链重跑（已有三条流的结果文件会跳过）。

## 2026-10-06 22:25：duo 的续跑安排（用户："跑完了把 duo 也重启，duo 你也随时监督着，利用率不能低，但是也别跑崩"）
- **改动 1：流内检查点**。`check_duo.py` 每 20 批把状态（P、wsel、chosen、L、上一批的完整概率 prev、t）存到 `results/duo/<stream>.part.pkl`，重试时从检查点接着跑，不再从流的开头重来；流结束后删掉检查点，最终文件先写 `.tmp.npz` 再改名。TFM 在给定上下文时是确定的，L 与 prev 按 float64 原样保存，所以续跑的结果应与不中断时相同（尚未逐位核对，计划在 h2_phishing 上做一次中断续跑与已有结果的比对）。
- **改动 2：按流并行**。剩下的 4 条流（elec2、h2_airlines、h2_poker、h2_rialto）各开一条链（tmux `duo_<stream>`，输出 `results/console_<stream>.txt`），由 `results/launch_duo.sh`（tmux `duo_launch`）在 ResetEval 的 6 条 re1 链全部 CHAIN_DONE 后自动启动；7 条流都有结果后自动运行 `analyse_duo.py`，写 CHECK_DONE。
- **防崩规则**（`results/guard_duo.sh`，tmux `duo_guard_watch`）：最近 10 分钟内 4 条链合计 ≥ 4 次 RETRY 时，暂停重试最多的那条链（至少留 1 条）；有链结束且最近 10 分钟重试 < 2 次时，重新启动一条被暂停的链。暂停与恢复都写进 `console.txt`（THROTTLE / RESUME）。
- 判定规则 D1、D2 不变。
- **22:43 提前启动**：ResetEval 的合成流链陆续结束，GPU 利用率降到 55%，所以没有等 re1 全部结束，提前用 `results/launch_duo_now.sh`（去掉等待的同一脚本）启动了 4 条 duo 链，与 re1 剩下的真实流并行。

## 2026-10-06 23:00：可行性检查的结果——D1 成立，D2 按规则成立但只是持平（CHECK_DONE 23:00:11；22:43 之后 4 条链 0 次重试，检查点没有被用来续跑过；`results/console.txt`）
- **开发集 7 条流，准确率 %（duo / fifo / sel / MICE）**：elec2 81.22/81.04/80.52/81.47；h2_airlines 67.65/68.15/66.76/68.17；h2_phishing 94.80/94.57/94.66/94.60；h2_poker 91.11/90.76/86.51/91.27；h2_rialto 82.24/75.51/81.84/81.13；h2_spam 94.54/94.49/92.11/94.25；h2_weather 80.54/81.09/78.11/81.07。平均 84.59/83.66/82.93/84.56。
- **其他指标（duo / fifo / sel）**：macro-F1 78.54/77.49/77.17；ROC AUC 90.53/89.32/89.04；ECE 2.03/1.97/4.84；log-loss 0.387/0.422/0.489。
- **核对**：本次 fifo 与 MICE 结果里的 fifo 最大绝对差 0.011 点。
- **D1**：duo − fifo 平均 +0.93（需 ≥ +0.50），5/7 条流更好（需 5/7）——**成立**。
- **D2**：duo − MICE 平均 +0.02（需 ≥ 0），3/7 条流更好——**按写定的阈值成立，但实际上与 MICE 持平**；+0.02 远小于流间差异，主要来自 rialto（+1.11），在 airlines、poker、weather 上低于 MICE。
- **解读（Claude 的判断）**：单独的"相关性挑选"（sel）比 fifo 差（−0.73），duo 的收益来自把两种上下文混合；与 MICE 相比没有显示出优势。按规则可以立项，但要成为新论文，方法上需要在 MICE 之外给出明显的收益，这一点目前没有证据。是否继续由用户决定。
- **23:50** 本项目运行中遇到的机器故障（显存占满、CUDA launch failure、WSL 重启）与处理办法汇总在 `env/MACHINE_LOG.md`。
