0.15093070000000003
**逐条结论**

1. **fixed(`qualify` 的空输出守卫仍缺,见下方新缺陷 A)。** `make_tasks.py` 现在给 r13-acc(:101)、seg-origin(:108)、oracle(:110)和各 bench(:115、118、120)都填了输出列表。`complete()` 对空列表返回 False,任务因此不会被记为 done。`make_tasks.py` 没有拒绝输出为空的任务,所以原始文件缺失时输出仍会是 `[]`。
2. **fixed。** `qualify` 现在设 `HOME=<d>/<k>`、`RUNS=<d>/<k>/pfn-runs`,并只链接输入(`INPUTS`)。硬编码 `~/pfn-runs` 的驱动经 `expanduser` 落到沙箱里。
3. **fixed。** 每次尝试前 `quarantine` 会把输出文件本身和 `.ckpt` 一起移走。`run.run` 因此不会遇到已有输出而直接返回,重试会真正重算。
4. **fixed。** `GPU_METHOD` 已加入 `mice\d{3,}`。未匹配的方法会记入 `FILTERED`,并在 :152 打印出来供核对。
5. **fixed。** results_*(:47)和 tkde(:85)的输出现在都包含 `.closes.pkl`。
6. **not fixed:** `rerun.py:135` 的 `complete()` 对已有输出的任务写 `note` 后直接标 done,而且既不事先断言 `{REPO}/MICE/results_*` 为空,也不在汇总里单独统计。已提交的 clone 里若带有 results_* 文件(很可能,因为这些结果在仓库里),整个 results_* 家族(几十到上百个任务)会不经计算就被记为 done。results_probs 和 delay_dev 同理。
7. **fixed。** `run_once` 现在用白名单 `KEEP` 加 `SLURM_*`,再叠加任务自己登记的环境变量。
8. **fixed。** `make_tasks.py:143` 的 `float(lr):g` 加整数 `L`、`st`、`float(mech):g`,与 `run_ts.py` 的命名一致。例如 1e-4 得到 `lr0.0001`,steps 为 `s1`。

**新缺陷**

- **A. `rerun.py:190` 和 `:211`:** 两组输出列表都为空时,`len` 相等、循环空转,且 rc 均为 0,于是打印 `QUALIFIED (bit-identical)`,而实际什么都没比较。后果是 qualify 和 recheck 会错误通过。修复是在 `qualify` 里要求输出非空且文件都存在。
- **B. `rerun.py:148`:** `ok = complete(t, env)` 不看返回码。最后一次尝试 rc≠0 但输出文件已存在且可读时(例如驱动写完 npz 后在收尾阶段崩溃),任务会被记为 done。后果是失败的运行被当成成功。修复是用 `ok = rec["rc"][-1] == 0 and complete(...)`,"启动前已完整"的分支除外。
- **C. `rerun.py:84-86` 和 `:93`(与 A、B 同源):** 输出列表为空的任务既不会被验证,也不会被隔离旧文件。`make_tasks.py` 没有为空列表报错,这会让 A 的问题重新出现。修复是 `make_tasks.py` 在写 `tasks.jsonl` 前,对输出为空的任务直接报错。

除上述之外,我没有发现会让任务执行与登记不同的命令或环境的缺陷。
