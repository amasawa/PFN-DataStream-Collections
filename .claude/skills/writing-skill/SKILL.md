---
name: writing-skill
description: 用户的科研写作与 LaTeX 规范（符号、函数表示、公式标点、专有名词与引用、交叉引用、参考文献、URL）。只要往论文里写东西或修改论文，就必须使用本 skill，并同时使用 anti-defensive-writing。
---

请对整篇 LaTeX 论文进行一次系统性的格式、符号和学术写作规范检查与修改。不要改变论文的技术内容、实验结果和核心论点，并确保修改后能够正常编译。

# 1. Notation 与数学符号规范

- **Notation table**：放在实验部分前后的合适位置，统一说明重要的随机变量、函数、操作、模块，以及变量和张量的维度与含义。
- **符号风格**：vector 用 `\mathbf{}`，matrix 按项目已有规范用 `\mathcal{}`；公式中的普通名称、模块名、操作名用 `\texttt{}` 或 `\mathrm{}`，否则会被 LaTeX 排成斜体变量。
- **复用已有定义**：项目存在 `math.tex` 时优先 `\input{math.tex}` 使用其中的命令，不要重复造 notation。
- **一个概念一个符号**：检查全文同一概念是否出现多种写法并统一。

# 2. 函数与操作的表示

- **普通函数**：统一写成 `f(\cdot)`。
- **含可学习参数**：函数、模型或操作写成参数化形式 `f_\theta(\cdot)`。
- **输入输出**：所有函数、操作、模块的输入输出含义必须清楚，不清楚就补充定义。
- **命名不混用**：函数名、变量名、模型名分开，否则读者无法区分对象与映射。

# 3. 公式与标点

- **公式即句子**：公式是句子的一部分，所以必须按正常英文语法处理标点。
- **前后标点**：检查所有 display equation，公式前该用 comma、colon 时是否遗漏，公式后该有 comma、period 时是否缺失。
- **语句完整**：句子不能被公式生硬切断，公式前后应读成完整、自然的英文。

# 4. 专有名词、方法名与引用

- **引用**：已有方法、算法、模型、数据集首次出现必须有正确 citation，否则会被误读为本文贡献。
- **缩写**：首次出现写 “Full Name (ABBR.)”，之后统一使用缩写。

# 5. Table / Figure / Equation 引用

- **引用命令**：尽量使用 `\Cref{}` / `\cref{}`，避免手写 “Table~\ref{}” 造成写法不一致。
- **Label**：必须唯一、命名清楚，且没有 unresolved reference。

# 6. Bibliography 整理

- **会议论文**：按 `/Users/usydwzk/SynologyDrive/Skills/学术写作_Bib会议/BibConference.md` 处理。
- **期刊论文**：暂无专用规则，在 DBLP 查找后保留期刊名称、年份、卷号和页码；title 格式同会议。
- **清理**：删除重复、格式错误或字段不一致的 entry。

# 7. Dataset / Metric / Software URL

- **只需地址**：dataset、metric 或 software 只需提供官网、GitHub 或下载地址时，优先使用 `\footnote{\url{...}}`。
- **对应论文**：如果它本身对应正式论文，仍然正常 citation。

# 8. 执行方式

1. 扫描整个项目，找到主 `.tex`、所有 section `.tex`、`math.tex` 和 `.bib` 文件。
2. 逐项修改上述问题，而不是只改单个 section。
3. 尽量复用项目已有的 macro 和 notation。
4. 不要擅自修改实验数值、模型结构、方法贡献或结论。
5. 修改后运行 LaTeX 编译，检查 undefined reference、citation、duplicate label 和 bibliography error。
6. 给出简短 summary，按 1–7 说明具体修改内容，以及仍需人工确认的问题。

# 附注（安装时添加，2026-10-10）

- 本 skill 的正文是用户桌面 `writingSkill.md` 的原文，未改动。
- 第 6 节引用的会议参考文献规则 `/Users/usydwzk/SynologyDrive/Skills/学术写作_Bib会议/BibConference.md` 是另一台
  Mac 上的路径，这台机器上没有；处理会议论文的 bib 时先向用户要这份文件，在拿到之前按"期刊论文"一条的做法
  （DBLP 核对、保留关键字段、title 格式统一）处理并标明待确认。
- 写入论文时与 `anti-defensive-writing` 一起使用：本 skill 管格式与规范，那个 skill 管论证（删除只为防止被质疑的句子）。
