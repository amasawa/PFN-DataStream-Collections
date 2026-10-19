# Sonnet 审 P5/P6 方案与 Fable 答复（10:2x）

1. **Gate (a) buffer band contradicts the binding gate rules and leaves a choice open until after the result.**
   - Quote: "(2σ, 3σ] … tot 置为 pending,带记录交用户决定是否补两粒种子".
   - Why: Amendment c item 5 and TOT item 2 register "one seed" and allow only two outcomes. "Pending" applies only when gate (a) exceeds 12 CPU-hours, and any other failed gate means "skipped". Adding seeds after seeing a near-miss is a post-result choice.
   - Correction: Register a single pass threshold before any run, local or cluster, and make anything above it "skipped". If a buffer or extra seeds are wanted, the user must change the amendment first. The threshold must also be committed before the local run (option L), so the local result can't influence it.

2. **The stage 2 generator is not mechanical for every boundary case.**
   - Quote: "one full extension of every boundary axis" and "reads only the committed selection files".
   - Why: Amendment c item 2 gives new values only for the observed cases: n_steps 25 for the upper edge, and lr 1e-5 for adaptz at the lower edge. The following are unspecified:
     - the lr upper edge (1e-2);
     - the n_steps lower edge (1);
     - dtmoe's grid, which the amendment doesn't cover. The draft only asserts that the amendment "applies to dtmoe".
   - Correction: Before the generator is committed, register a table of the new value for each axis and edge. Register dtmoe's grid and edges explicitly, or state that the user approved applying amendment c to dtmoe. Add a fixture for each edge.

3. **The gate (a) environment differs from the environment that produces the tot numbers.**
   - Quote: "venv-tot … numpy 1.23.5 / torch 2.3.1" for gate (a), versus "P2 lock + einops" for the development grid and tests (the expert's suggestion).
   - Why: Gate (a) then certifies the authors' code in an environment that is never used for any reported number. Gate (b) and the timing must run in the production environment, and the draft doesn't say where.
   - Correction: State which environment each of gate (a), gate (b), the timing, the grid and the tests uses. If the P2 lock can't import the released code, record that explicitly. The local and cluster runs of gate (a) must use the same lock file.

4. **Unfixed cost threshold X, and a "12 CPU-hours" definition that was not yet registered.**
   - Quote: "exceeds X CPU-h … goes to the user".
   - Why: X is a placeholder that would be set after the timing is seen, which makes it a post-hoc choice.
   - Correction: Commit X and the exact "12 CPU-hours" definition (single process, fixed OMP threads, wall clock) before the first gate run. Also commit the rule for tot when stage 2 picks n_steps 25, which costs about five times as much.

5. **The paper target is unverified and has no citation.**
   - Quote: "MSE mean 0.374, std 0.0031 over three seeds".
   - Why: The whole gate rests on this number and nobody could check it. Neither the draft nor the expert shows that the table's configuration is the same as the released code's mode "time", pred_len 1.
   - Correction: Add the page and table reference, plus a confirmation of the configuration, to the P6 registration. If σ changes, the 2σ rule stays and only the number changes.

## 处置
1 采纳：不设缓冲带，单一阈值 2σ，否则 skipped。2 采纳：阶段 2 登记写出各轴各边界的新取值表（PLAN_BASELINES：lr ×10 / ÷10，n_steps 25；n_steps 下界 1 为最小值不扩展），dtmoe 显式列入，生成器夹具覆盖各边界。3 采纳：登记写明各步环境。4 采纳：12 CPU 小时 = 单线程 12 小时墙钟；TOT 网格 1500 CPU-h、阶段 2 清单 3000 CPU-h / 300 H800-h 上限，超过交用户。5 采纳：写明页码表号与 PDF 哈希；论文未写 mode，失败时注明可能来自配置不符（gate (a) 登记第二轮 Sonnet 核对后补）。
