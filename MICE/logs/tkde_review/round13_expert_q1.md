# Round 13 expert question 1 (Claude Fable 5.1, 04:20–04:21, $0.88)

## Prompt

You are the senior expert adviser for a machine-learning paper (MICE: mixture of in-context experts with TabPFN v2 for recurring concept drift). Do not edit anything. Answer in this format: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence / Requires user approval. Be brief (<= 350 words).

Context. The ICML-standard reviewer asked (round 13): MICE beats an unmerged archive by only 0.30 pts (aligned grid) / 0.07 (29 real streams) and trails a snapshot pool by 0.08 on real streams, all at pool cap 12; its organisational benefit (fewer experts/calls) was never timed against these controls. Requested: bounded accuracy-latency-memory comparison against archive and snapshot, including smaller capacities selected by timings alone, on aligned, shifted and representative real streams. "Superiority everywhere is unnecessary."

Registered design (before runs): capacity k* in {2,4} = largest whose amortised s/batch <= MICE's on three 300-batch real prefixes (isolated GPU). Reporting rule E: if any group has mean Delta (MICE - control) <= +0.1, abstract and conclusion must say so, naming the group.

Results.
Timing (s/batch, real prefixes; experts; TFM calls/batch; stored rows k): MICE 1.11 (1.8; 5.5; 1.76). Archive k2 0.93, k4 1.27, k12 2.49 (10.7 experts; 13.6 calls). Snapshot k2 0.98, k4 1.38, k12 2.84. So k* = 2 for both. Grid timings (A2) pending.
Accuracy at k*=2, Delta = MICE - control, group mean [95% block-bootstrap CI], streams positive:
 aligned grid (8): archive +6.72 [5.42, 8.69] 8/8; snapshot +7.49 [6.18, 9.51] 8/8
 shifted grid (8, boundaries inside segments; MICE known to be phase-sensitive): archive +1.45 [1.03, 2.06] 7/8; snapshot +0.00 [-0.64, 0.47] 4/8  -> rule E triggered
 real subset (9): archive +0.35 [0.26, 0.44] 7/9; snapshot +0.27 [0.16, 0.36] 6/9
At k=12 (prior results): MICE within ~0.3 of both on accuracy, but 2.2-2.6x cheaper per batch on the prefixes.

Question: What is the single claim the paper should now make about the discrepancy-based organisation, and how should the abstract sentence (one sentence, including the rule-E statement) read? Should the Limitations sentence "Merging by discrepancy did not improve accuracy over an unmerged archive by the registered margin; its measured benefit is a smaller pool" be replaced, and with what? Keep claims to measured prefixes/streams.

## Answer

**Decision**
把论断从"准确率"改为"效率"：Discrepancy-based merging 是一个**在匹配延迟下保持准确率**的机制，不是提升准确率的机制。唯一主张：在三条真实流前缀上，MICE 以约 2 个专家、1.11 s/batch 的成本达到容量 12 的 archive/snapshot 的准确率（差距 ≤0.3），而在同等延迟（容量 2）下控制组在 aligned grid 和真实流上落后，shifted grid 上 snapshot 与 MICE 持平。

**Abstract 句（含 rule E）**
"Against unmerged archive and snapshot pools whose capacity was fixed by timing alone (two experts, the largest matching MICE's per-batch latency on three real-stream prefixes), MICE is more accurate on the aligned grid (+6.7/+7.5 points) and on nine real streams (+0.35/+0.27), but on the shifted grid it only matches the snapshot pool (mean difference 0.00, four of eight streams); at capacity 12 both controls reach MICE's accuracy within 0.3 points at 2.2–2.6× its per-batch cost."

**Limitations 替换为**
"Merging by discrepancy does not raise accuracy above an unmerged archive of equal capacity (12) by the registered margin. Its measured benefit is cost: a pool averaging 1.8 experts and 5.5 TFM calls per batch reaches that accuracy at 2.2–2.6× lower per-batch cost on three real prefixes. At matched latency (capacity 2) the controls lose 0.3–7.5 points, except on the shifted grid, where the snapshot pool matches MICE. Timings come from three real prefixes on an isolated GPU; grid timings are pending."

**Supporting evidence**
k*=2 由计时独立选出；aligned 8/8、real 7/9 与 6/9，CI 均不含 0；shifted-vs-snapshot CI 跨 0 → rule E 必须点名该组；k=12 时 MICE 落后 snapshot 0.08、领先 archive 0.07，只能写"within 0.3"。

**Alternative options**
(a) 声称 Pareto 优势——不成立，snapshot k12 在真实流上略高。(b) 等 A2 grid 计时再定稿——若 grid 上 k*=4，aligned/shifted 数字需重算。(c) 保留原 Limitations 句只加延迟数字——比替换弱，未说明 shifted 失败。

**Key risks**
k* 在真实前缀选出却用于 grid；真实流 +0.35 增益小，审稿人可能视为噪声（CI 紧但仅 9 条流）；shifted grid 暴露相位敏感性，与"大池准确率、小池成本"的主张直接冲突，必须在正文承认。

**Remaining uncertainty**
A2 grid 计时结果；3 条前缀是否代表 29 条真实流的延迟分布。

**Confidence** 0.75

**Requires user approval**
无新方法/新数据，可在自治循环内写入；但摘要主张从准确率改为效率是框架变化，本轮 push 时需向用户明示。
