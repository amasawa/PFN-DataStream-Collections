# Fable 追问答复（09:22:20–09:23:14，0.49 美元）

**Decision:(A)。** 全部 92 条流用同一个 tau,从 {0.1, 0.2, 0.3, 0.4} 在 5 条开发流(elec2 + 4 条 INSECTS)上按 Table 1 基线的规则(平均准确率)选出;两阶段注册:先注册并推送选择程序 + 平局规则(平局取 0.3),再跑开发流,再在任何测试流运行前注册冻结值。7 条有公开 tau 的流不用公开值。

**Supporting evidence:** (1) 公开的 tau 是作者在 TabICL(n_estimators = 1)、逐行即时标签、CURE 自己的分段上调出的;我们的设置是 TabPFN v2、4 个估计器、整批延迟标签、自己的分段。归一化熵的尺度随骨干和信号陈旧度变化,所以这些值不是"本设置的默认值",ACTIVATION 第 96–97 行的"undefined for this setting"分支适用于全部 92 条,不只是 85 条。(2) h2_weather 和 5 条 poker 流用的就是 CURE 调参所用的数据,公开值很可能是在测试数据上调的;(B) 会让 7 条流的 CURE 带着测试集调出的 tau,其余 85 条带开发流的 tau,审稿人要么指泄漏,要么指不一致。(3) 开发流与那 7 条流不重叠,(A) 对 CURE 和其他可调基线一视同仁,这是最站得住的说法。

**Alternatives:** (C) 0.3 不跑开发流,是用户不批准改句子时的回退,结果旁写"未调参,中位数";(B) 不建议,理由见上;可选附录:用公开值在那 7 条流各跑一次(7 个任务)作为敏感性行,预先堵住"忽略了公开值"的质疑,是否加由用户定。

**Key risks:** 5 条开发流上四个 tau 可能几乎无差别,平局规则必须事先写死;开发流只有 2 类和 6 类,tau 对多类流的迁移未经检验;批到达使信号陈旧最多一批,入库率要按流记录并在论文说明;论文须明说那 7 条流存在公开 tau 而未使用及原因。

**Confidence:** 中高。

**Requires user approval:** 是。ACTIVATION 第 96–97 行改为:"CURE's published defaults; no tuning, except tau, which has no default for this setting (backbone, batch arrival, our segmentations): one value for all streams, selected on the five development streams of the Table 1 baselines by their rule, registered in two stages (procedure and tie rule before the development runs; the frozen value before any test-stream run)."
