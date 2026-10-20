# Sonnet 审 Fable 的去留建议（12:0x）

1. **Quote:** "TOT 无官方代码，纯靠论文复现"
   **Why it's wrong:** FACTS say TOT has official code, the authors' LSTD-TOT code from the NeurIPS 2025 supplementary material. Our adapter imports its official `net` unchanged. Only the OneNet-based reproduction was dropped.
   **Correction:** TOT does have released code. The main argument for dropping it has to be rebuilt on the cost and the unrun gates, not on missing code.

2. **Quote:** "审稿人也能质疑'这不是 TOT'"
   **Why it doesn't follow:** The adapter uses the official network, and the deviation (identification terms active per step, head on the latent) is registered. It is an adaptation of official code, not a reproduction from the paper. The same adaptation caveat applies to dtmoe and the other TS baselines.
   **Correction:** State the deviation and the gate results. Do not frame TOT as an unofficial reimplementation.

3. **Quote:** "登记里本来就写了'未过门槛则报 skipped'，去掉它是执行既定规则，不是新决定"
   **Why it's wrong:** The registered rule says skipped only if gate (a) or (b) fails. A 12 h limit gives "pending". No rule says "gates not executed → not included". Gate (a) has not run, so dropping TOT now is a new protocol decision, not execution of a rule.
   **Correction:** Describe it as a protocol amendment (registered but not run, because of cost). Also, "按登记规则不纳入" would be false.

4. **Quote:** "TOT（NeurIPS 2025）无公开代码，预登记要求先通过复现门槛再改造；门槛未执行，按登记规则不纳入。"
   **Why it's misleading:** The wording is false in three ways. TOT's code is public in the supplement. The registered rule has no "not executed → excluded" clause. And the gate is a precondition for reporting, not a requirement placed before adapting. A reviewer who checks the supplement would read this as hiding a baseline.
   **Correction:** Use wording like: "TOT (NeurIPS 2025) was registered but not run. On 2026-10-20 we amended the protocol to drop it for cost reasons (about X GPU-h), before any TOT or dtmoe score was read."

5. **Quote:** "② 不用 strict deterministic，改固定 seed + 默认 cuDNN，并在附录注明 GPU 非确定性"
   **Why it's an unflagged registration change:** Strict mode exists because the clean rerun must show bit-identical repeated runs (determinism probe, PLAN.md check 1). Dropping it for dtmoe breaks that registered check, and the expert gives no analysis of that. Option ① (drop `drift_k_sigma`) is also a change to the dev grid, which currently has 36 configs and 180 tasks. The expert does say an amendment is needed, but only for the cost-reduction items, not for the determinism exemption.
   **Correction:** Flag that option ② needs an explicit amendment exempting dtmoe from PLAN.md check 1. It should be rated lower than ①, or rejected.

6. **Quote:** "去掉 TOT 省 ~290–490 GPU-h；dtmoe 剩 ~250–450 GPU-h，8 张 A800 约 1.5–2.5 天"
   **Why it doesn't follow:** The numbers are not derived from the FACTS. dtmoe is ≥150 dev + 100–300 tests, which is 250–450. TOT is ~190 dev + 100–300 tests, which is 290–490. Those match. But the 1.5–2.5 day estimate ignores the 7 cores per GPU limit and the fact that the whole rerun already uses ~1250–1650 GPU process-hours. The fixed-segmentation claim "dtmoe ≥40× slower" was only measured locally. The "affordable" conclusion rests on that.
   **Correction:** Give the cluster-wall-time estimate after a cluster throughput check, or mark it as unverified.

## 处置：6 条全部采纳（TOT 有官方代码；去掉 TOT 是协议变更不是执行规则；论文措辞改为'已登记但因成本未运行'；不采用非严格模式；天数以集群实测为准）。

# Sonnet 核对 AMENDMENT_20261020c：none
