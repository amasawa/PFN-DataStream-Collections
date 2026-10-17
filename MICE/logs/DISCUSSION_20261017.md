# 2026-10-17 与用户的讨论：MICE 的投稿与 arXiv

时间取自会话记录（AEDT）；09:10–09:50 之间的几条消息没有精确时间，标为区间。只记用户的问题、我的建议和用户的决定；
建议不是决定，未决事项单列。

## 投稿去向（约 09:10–10:02；我的回答 09:48–10:00）
- 用户："我现在这三篇感觉都能成文，但是下半年没有合适的会议和期刊了，是投 TMLR、WWW 还是统一明年 1 月的 ICML"；
  "MICE 投稿 TMLR 是不是可惜了"；"你是用的谁给你的分数怎么都是接受呢"；
  09:55 "所以不如 mice 投 TMLR，然后 mice-duo 学生做，B/C 我后面自己做投稿 ICML 对不对，那 MICE 发表是不是不太好"；
  10:00 "下半年还有啥比较好的会议"。
- 分数（09:48）：审稿人是 Codex gpt-6-astra（high），只看隔离的论文副本；分数是"它再找不出必须改的问题"，是内部质控，
  不是接收概率（MICE 起点 4，DUO 3，ResetEval 按 TMLR 标准起点 6）。
- 两个方案（09:55）：
  - 方案 1（用户提出）：MICE 投 TMLR、学生做 DUO 投 IJCNN、用户自己做 B/C 投 ICML——确定性高，但最强的一篇放在 CCF 不认的
    TMLR，B/C 在 ICML 会被看成"对 TMLR 论文的推广"，次序是反的。
  - 方案 2（我倾向）：MICE 挂 arXiv 后投 ICML、DUO 投 IJCNN、B/C 投 NeurIPS 2027（约 5 月）；ICML 5 月初出结果正好在 NeurIPS 前。
- 会议表（10:00）：WWW 2027（A，摘要 10-18/全文 10-25，当时我判断"契合度低、时间来不及"）、ICDE 2027 第二轮（11-11）、
  IJCAI（约 1-15）、ICML（约 1-22）、KDD 2027 第二轮（约 2 月，**契合度最高**：数据流和漂移是 KDD 核心主题）、IJCNN、PAKDD；
  期刊 TKDE / DMKD / TMLR。综合建议：MICE 投 KDD 第二轮或 ICML，先挂 arXiv。
- 用户当时没有最终选定。

## arXiv 版（10:19–13:52）
- 用户："好的，准备一个 arxiv 的版本"；版式选"单栏中性预印本"；作者先留占位，随后给出
  "xu zhang zhihong cui kaize shi"，"我是一作"。作者顺序：Zhangkai Wu, Xu Zhang, Zhihong Cui, Kaize Shi。
- 已做：`MICE/code/make_arxiv.py` 从 TKDE 源生成 `MICE/overleaf/arxiv/`（37 页），去注释，把"added in response to review"
  改为"added later"（内部 AI 审稿不是同行评审），把"released code"改为"the code"（代码尚未公开）；摘要精简到 1919 字符
  （arXiv 上限 1920），见 `MICE/overleaf/arxiv_metadata.txt`。提交 a3bd5b0。
- 13:42 用户："把 arxiv 版本 zip 一个桌面"；13:45："bib 是不是有问题"——确有问题：
  - Tectonic 自带的 BibTeX 展开 @string 时丢了空格（"ACMComput.Surv."），refs.bib 本身没错；arXiv 版改为把 @string 写成字面量；
  - 修正 Schlimmer & Granger, Jr. 的作者解析，ICDM/IDA/两个期刊名统一为缩写；提交 207bd8e。
  - 13:47 用户："不是直接准备个版本我要放到 overleaf"——已改为 Overleaf 工程包 `Desktop/MICE_arxiv_overleaf.zip`
    （23 个文件，含 refs.bib，pdfLaTeX 编译）；删除了之前的 MICE_arxiv.zip。
- 未决：作者单位与邮箱（AFFILIATIONS / EMAIL 占位）；Gama & Kosina (KAIS 2014) 页码未核实，仍留空。

## WWW 2027（13:52–14:01）
- 用户："mice 你觉得可以整理整理投稿 WWW 吗"；"还有三个月真怕被别人做了"；"www 中了是不是也不是好事"。
- 查到的事实（www2027.thewebconf.org 征稿）：摘要 10-18 AoE（悉尼约 10-19 23:00），全文 10-25 AoE；ACM 双栏，正文 8 页 +
  参考文献/附录共 12 页；双盲，允许已挂 arXiv 的论文匿名投稿（不引用自己的 arXiv）；必须说明与 Web 的相关性，
  "只是用了 Web 数据"会被直接拒稿；作者有审稿义务；结果 12-15，最终通知 2027-01-04。
- 我的建议（更正了 10:00 时"WWW 来不及"的判断：一周压缩到 8 页可行）：
  - 防被抢先靠 arXiv 时间戳，不靠会议；应尽快挂 arXiv（周一美东 14:00 前提交，悉尼周二上午公开）。
  - WWW 中了是好事（CCF A；早出结果；37 页完整版可再扩展投 TKDE）。代价：读者群不完全对口；故事要带 Web 动机；ICML 不能再投。
  - 主要风险是 Web 相关性被直接拒稿（我估计约一半；注意：已有记忆记录 WWW 2026 录用过不用 Web 数据的概念漂移论文，
    doi 10.1145/3774904.3792379，风险可能低于估计）。被拒也不耽误 1 月的 ICML。
  - 方案：先挂 arXiv → 明晚前交 WWW 摘要 → 一周内压成 8 页 → 中了就扩展投 TKDE，被拒就改投 ICML。
- **未决（等用户）**：是否投 WWW；投稿方向（建议 Web Mining and Content Analysis）；所有作者的 OpenReview 账号。

## 晚间（21:2x–22:52）：主表补数据与检测分段确认实验
- **21:2x 用户**："这是mice表1 我们还跑了什么数据能够支持主表的内容"（贴了表 1 的结构和想要的数据清单）。
  我盘点：8 个训练式学习器有逐流准确率（真实 29 条、grid10）；检测分段 MICE 有 29 条真实流和 grid20；生成器流 30 条有准确率；
  TabICL 14 条；SAM-kNN/蓄水池/ADWIN 窗口从没跑过；检索式上下文属于 DUO。
- **用户**（贴来的建议）：主表补训练式学习器逐行、检测分段 MICE 一行（主推）、补齐网格口径、生成器准确率一列；oracle 行删去；
  TabICL 与种子 1 放附录。"主表内容可以先导出到桌面，然后等 gpu 空了继续跑"。
  - 做了：`export_main_table.py` → 桌面 `MICE_main_table/`；补跑训练式学习器 grid20（CPU）与检测分段 grid10（GPU，等 GPU 空出后自动启动），
    两者都做了复现检查（逐位一致）；MiMo 审计导出脚本（6 条，数字不受影响，加了断言）。commit c29f343、af65b49、fca4dd3。
- **用户**："跑完了告诉我"、"还有多久啊"——22:11 全部完成，桌面已更新。
- **用户**贴来"检测分段 MICE 的真实流确认实验方案（Fable 审核后修订版）"，问"这个实验你觉得能跑吗"。
  我的判断：能跑（代码现成，去掉专家池的变体可从缓存回放）；要先定新数据；原第 1 条"每段 ≥ −0.2"在已有 29 条上就有 3 条不满足，
  新数据 8 段时偶然失败概率约 57%；方案里"段长 300–700"与代码不符（检测到变化时至少 300 行，否则 500 行）。
- **用户决定**："第 1 条改成整体检验，数据用 CIC-IDS2017 和 Bitcoin Heist"；随后"Bitcoin Heist 按你的建议"
  （二分类、6 个特征、2013–2017 每年前 10 万行）。CIC-IDS2017 官方下载要填个人信息表，用户本人下载了 MachineLearningCSV.zip（md5 与官方一致）。
- 预注册 `experiments/mice_confirm_cp_20261017/PLAN.md`。Fable 审核（1.78 美元）：评估脚本 H2 误把补充的 Poker 段算进去（已修）；
  Bitcoin 原文件把勒索行排在最前，日内顺序会泄漏标签（核实属实，改为日内随机顺序后重建）；补充披露（CIC 选段偏向检测类方法、
  9 段全是二分类、H1 只对这 9 段成立）；加 50 批块的敏感性（描述性）。平局计为失败的严格规则保留（Fable 也建议保留）。
- **用户 22:52**："今天的对话记录到 log 然后有大结果记得 push，我睡觉了"。之后按预注册自主执行：MiMo 审计 → 提交推送预注册 → 开跑 → 评估 → 推送。
