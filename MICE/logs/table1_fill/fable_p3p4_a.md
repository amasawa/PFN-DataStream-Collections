# Fable 答复（2026-10-20 09:18:42–09:20:49，0.74 美元）

**Q1. TabPFN v2.5/v2.6/v3/v3.5 的 n_estimators 与 v3.5 变体**

- Decision:全部用 n_estimators = 4,用 v3.5(非 fast)。
- Supporting evidence:P3 的规则是"TabICL check 的协议,不改任何常数"(ACTIVATION 第 76–79 行);run.py 第 35、40 行把 4 固定为协议常数。"auto" 会让集成规模随版本、甚至随每批上下文大小变化,把"骨干版本"和"集成规模"两个因素混在一起,也让 20 倍时间排除规则失去可比基准。
- Alternative options:对 v3.5 用 "auto" 作为单段敏感性检查;预注册"v3.5 若触发时间/显存规则则以 v3.5-fast 替补"。两者都不建议:前者扩大范围,后者等于加第 8 个骨干。
- Key risks:v3+ 的包默认行为与我们不同,论文须写一句"所有骨干 4 个估计器;v3 以后的包默认是 auto"。
- Remaining uncertainty:"auto" 在 tabpfn 9.0.0 中的具体规则(草案未查)。不影响决定。
- Confidence:高。
- Requires user approval:否。

**Q2. Mitra-v2 的 fine_tune**

- Decision:fine_tune = False;n_estimators = 4。
- Supporting evidence:MICE 的定义是"所有策略共用同一冻结骨干"。默认每次 fit 做 50 步微调,骨干就变成一个在每个记忆上训练的学习器,比较对象从"记忆策略"变成"记忆策略 + 微调";每批多次调用时成本和不确定性也不可控。
- Alternative options:默认微调模式,作为附录的单独一行。不建议,它不在 P3 的问题之内。
- Key risks:10 类上限会使部分段按"类数错误"规则排除;须在注册时写明这是能力限制,预计会发生。n_estimators 对 Mitra 的含义(排列集成)与 TabPFN 不完全相同,注册时注明。
- Remaining uncertainty:fine_tune = False 下 Mitra 的 in-context 质量未知;这正是要报告的。
- Confidence:高。
- Requires user approval:否。

**Q3. LimiX 检查点与检索**

- Decision:LimiX-2(400M),cls_default_noretrieval_v2.json。
- Supporting evidence:与 TabPFN 选 v3.5 的逻辑一致,选当前旗舰版本;审稿人会问为何不用最新。检索配置会让骨干自己从记忆中再选上下文,与策略的职责重叠,混淆"记忆策略"的归因。
- Alternative options:LimiX-16M 作为时间规则触发后的替补。不建议,理由同 Q1。
- Key risks:上下文 ≤1000 行、查询 100 行,400M 应在 28 GB 与 20 倍时间之内,但须由 smoke test 证实;无 flash-attn 时速度更慢,时间规则按同样条件测量即可。
- Remaining uncertainty:无 flash-attn 路径是否完全等价(数值上)。注册时记录。
- Confidence:中高。
- Requires user approval:否。

**Q4. CURE 的 tau**

- Decision:(b)。在 Table 1 基线所用的 5 条开发流上,从 {0.1, 0.2, 0.3, 0.4} 中按同一选择规则(平均准确率)选一个 tau,在任何测试流运行前冻结并写入 P4 注册。
- Supporting evidence:三点。第一,CURE 作者自己是按数据集调 tau 的,给它一个未调的中位数等于运行一个比作者弱的版本,审稿人会说"其他基线调了,CURE 没调"。第二,tau 作用在归一化熵上,熵的尺度随骨干变化(草案第 9 条已承认);TabICL 上的值移到 TabPFN v2 上没有依据,在真实骨干上用开发流选值正好解决这一点。第三,这不是新流程,就是 Table 1 其他可调基线已有的流程,"同等对待"比"零调参"更站得住。成本约 4 × 5 条开发流加 1 × 92 条,低于 (c)。
- Alternative options:(a) 中位数 0.3,作为用户不批准 (b) 时的回退,并在结果旁写明熵尺度限制。(c) 四行全报,成本约 4 个策略,主表放不下,只适合附录。(d) 需要自创规则,不要。
- Key risks:(b) 与 ACTIVATION 第 96 行"no tuning"字面冲突,必须由用户改为"除 Table 1 可调基线共有的开发流选择外不调参"。若用户坚持原文,则用 (a)。
- Remaining uncertainty:5 条开发流上四个 tau 可能几乎无差别,此时取中位数 0.3 作为预先写明的平局规则。
- Confidence:中高(技术上),决定权在用户。
- Requires user approval:**是**(修改 ACTIVATION 的一句)。

**Q5. CURE 的批到达映射**

- Decision:草案第 7 条的映射是忠实的,保留。补三条约束。
- Supporting evidence:CURE 的核心是"用预测该行时的熵决定是否进入长库";批映射保留了这一点(信号来自该行标签未知时的预测)。"预测时记忆不含同批前几行"是批协议对所有策略一视同仁的约束,不是对 CURE 的额外惩罚。
- 三条约束:
  1. 标签插入时刻必须与其他策略(如 ltm1000_75 在 run_drtabpfn.py 中的时序)完全一致,不要按 CURE 自己的时序;否则 CURE 的记忆会比其他策略早或晚一批。
  2. 归一化熵的分母:CURE 代码用的是 TabICL classes_ 的类数(上下文中的类),MICE 的 P 是全局标签集(缺失类为 0)。H 不变,但 log K 的 K 会变,阈值的含义随之变。按 CURE 的定义计算(用上下文类数),这是给 MiMo 审计的具体检查点。
  3. 单类上下文的 one-hot 预测熵为 0,这些行只能靠 warm-fill 进入长库;与 CURE 自身行为一致,无需改。
- Alternative options:插入时用当时记忆重新预测该行以取信号。不是 CURE,成本翻倍,不要。
- Key risks:上面第 2 点若做错,tau 的选择失效。
- Remaining uncertainty:CURE 代码对 warm-up 行的信号是否确为 0(草案这样说,按草案)。
- Confidence:高。
- Requires user approval:否。

**Q6. 审稿人可能指为不公平或误导的点**

- P3:新骨干没有按各自包的默认配置运行(4 个估计器而非 auto;Mitra 冻结而非微调)。这是对的,但论文必须用一句话明说,否则知道 v3.5 默认行为的审稿人会说"新骨干被降配"。类数排除(Mitra 10 类)要写成能力限制并给出受影响段数。
- P4:tau 是唯一的真实风险,见 Q4。其余(TabPFN v2 而非 TabICL、M = 1000)由"所有策略同骨干同预算"覆盖,写明即可。论文里描述 CURE 时用"LTM 式双记忆加熵门与冗余感知淘汰",不要用"我们的 ltm1000_75 加……"的口吻。

**待用户批准的事项**:只有 Q4 的 (b),需把 ACTIVATION 第 96 行改为"除 Table 1 可调基线共有的开发流选择外不调参"。其余按草案执行。
