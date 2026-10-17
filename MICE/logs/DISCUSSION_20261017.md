# 2026-10-17 与用户的讨论：MICE 的投稿与 arXiv

时间取自会话记录（AEDT）；09:10–09:50 之间的几条消息没有精确时间，标为区间。只记用户的问题、我的建议和用户的决定；
建议不是决定，未决事项单列。

## 投稿去向（约 09:10–10:02）
- 用户："我现在这三篇感觉都能成文，但是下半年没有合适的会议和期刊了，是投 TMLR、WWW 还是统一明年 1 月的 ICML"；
  "MICE 投稿 TMLR 是不是可惜了"；"你是用的谁给你的分数怎么都是接受呢"。
- 我的建议：
  - MICE 是理论 + 方法的论文，投 TMLR 可惜，首选 ICML（约 2027-01-22），备选 KDD 2027 第二轮（约 2 月）或 TKDE。
  - 分数来自 Codex 审稿人按 ICML 标准自评，只是内部参考，不是同行评审；MICE 的 tkde_review 里也有 3–5 分的轮次。
- 用户问"下半年还有啥比较好的会议""ijcnn 几页"，用于学生的 DUO（见 MiceDuo/logs/DISCUSSION_20261017.md）。

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
- 我的建议：
  - 防被抢先靠 arXiv 时间戳，不靠会议；应尽快挂 arXiv（周一美东 14:00 前提交，悉尼周二上午公开）。
  - WWW 中了是好事（CCF A；早出结果；37 页完整版可再扩展投 TKDE）。代价：读者群不完全对口；故事要带 Web 动机；ICML 不能再投。
  - 主要风险是 Web 相关性被直接拒稿（我估计约一半；注意：已有记忆记录 WWW 2026 录用过不用 Web 数据的概念漂移论文，
    doi 10.1145/3774904.3792379，风险可能低于估计）。被拒也不耽误 1 月的 ICML。
  - 方案：先挂 arXiv → 明晚前交 WWW 摘要 → 一周内压成 8 页 → 中了就扩展投 TKDE，被拒就改投 ICML。
- **未决（等用户）**：是否投 WWW；投稿方向（建议 Web Mining and Content Analysis）；所有作者的 OpenReview 账号。
