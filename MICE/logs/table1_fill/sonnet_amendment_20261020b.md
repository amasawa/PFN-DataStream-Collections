# Sonnet 核对 AMENDMENT_20261020b

**(a) Statements contradicted by the code**
- Item 3 and the `tot_check.py` docstring say "no accuracy" is computed or written. `run_ts.run` computes `acc` for every batch after the first, stores it in the npz files in the temp directory, and prints `acc=…` to stdout (the log) for each of the 8 timing runs and the 2 gate (b) runs. Those streams are elec2 and insects development data. Either drop the claim ("no accuracy is reported or kept") or suppress that print, for example with redirected stdout.
- Item 3 does not say what the 300 GPU-hour verdict threshold is measured against. Item 1 names "the cost limits (300 GPU-hours)" as a project-wide limit for the A800. `tot_check.py` lets TOT alone use all 300 (dry run: 192), so P1, P3 and P5 could push the total over the limit. Please state whether 300 is per phase or total.

**(b) Bugs in `tot_check.py` that change the verdict**
- None. I checked each of these:
  - The projection arithmetic is right: 4 (L, steps) × 9 × (453 + 2138) matches the 180 tasks, and the in-code assert holds.
  - The CPU reference sums to about 2180 h (25.7 h for elec2 plus 2154 h for INSECTS).
  - The 192 GPU-h dry run gives a speed-up of 11.3.
  - The npz file names match `run_ts.run`'s tag format (`m1e-05`, `m0`).
  - The JSON keys match the task schema.

**(c) Choices left open after results are seen**
- None. The 2-or-3-worker rule is fixed in advance, and so is the verdict rule.

**(d) HANDOFF steps that would run a cancelled or gated set without its gate**
- None. P4 is marked cancelled, and the grid and the qualify are listed after the check's "proceed" verdict. One residual risk: the "Former text" in the cancelled P4 step keeps the full worker command, and `tasks_p4.jsonl` stays in the repository.

## 处置：三点全部采纳。tot_check 丢弃 run_ts.run 的打印并删除临时输出，措辞改为'不报告、不保留准确率'；300 卡时写明是单份清单的上限，总预算按 HANDOFF 规则 5 问用户；HANDOFF 删除 P4 的运行命令。
