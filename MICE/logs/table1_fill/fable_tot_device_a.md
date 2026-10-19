# Fable：TOT gate (a) 设备（10:25:45–10:26:34，0.31 美元）

**决定**：选 A。gate (a) 用未改动的发布代码在集群一张 H800 上独占运行；其余（adapter、gate b、timing、development grid、stage 2）按注册留在 CPU。在绑定运行前先写修订。
**支持证据**：注册第 14 行"CUDA_VISIBLE_DEVICES 为空则 main.py 置 use_gpu False"是注册自身的事实性错误，不是代码没跑完；第 30 行"did not finish"针对的是运行失败，不是我们的前提写错。论文数字本来就是 GPU 跑出来的，H800 比 CPU 更接近论文环境，也避免了 12 CPU 小时单线程（depth 9、hidden 512）跑不完而变成"pending"的风险。本地跑只是可行性检查、非绑定，所以修订不违反"Neither is repeated"。
**替代方案**：B 是把注册写错转嫁成"代码的锅"，TOT 被无故删掉，审稿人一看就知道可以避免，且 gate 变得不可证伪，拒绝。C 破坏"unchanged"这一 gate (a) 的全部意义，CPU 数值差异还会混入 pass/fail，拒绝；若 A 被用户否决，再退到 C 并明示补丁 diff。
**关键风险**：(1) 本地 GPU 有静默损坏故障，所以本地可行性步骤取消，集群运行成为唯一一次，需在修订中写明；(2) 后续 gate (b) 若拿 adapter（CPU）对比 gate (a)（GPU）的数字，容差须明确容纳 GPU/CPU 数值差，否则 gate (b) 可能因设备而非 adapter 失败；(3) 12 CPU 小时上限要换成 12 h 单卡 H800 墙钟上限，一次、一个 seed、不加缓冲带，其余规则不动；(4) 需要集群 GPU 预算。
**置信度**：0.85（A 优于 B/C 高置信；gate (b) 容差细节需在修订中定）。
**需要用户批准**：是。A 部分撤销 amendment c 第 5 条（用户 2026-10-18 把 TOT 移到 CPU 的决定）并占用 H800 时数；属于注册变更，按规则运行前必须由用户批准。建议同时把 tot_gate_a.sh 第 3 行和注册第 14 行的错误说明一并改正。

## 用户决定
"gate (a) 用 H800 (Recommended)"（选项：gate (a) 用 H800 / 保持 CPU，TOT 跳过 / 最小补丁后在 CPU 跑）。
