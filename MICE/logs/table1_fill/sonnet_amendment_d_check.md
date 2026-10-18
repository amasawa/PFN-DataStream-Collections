0.11114860000000001 55.082
1. **dtmoe_local.sh:22-29 (third classification run missing).**
   - Defect: amendment item 4 says a mismatching probe is run a third time for classification only. The script only writes "DIFFERENT" and exits 3. A probe that crashed or raised exits 2 with no classification either.
   - Consequence: the mismatch cannot be classified, so the fallback decision for the user is missing the evidence the amendment promises.
   - Fix: on mismatch, run that probe once more into `probe_pre/c` and compare it against both `a` and `b`. Write the result to `progress.txt`.

2. **dtmoe_local.sh:27-29 and gpu_local.sh:14 (bookend mismatch does not flag anything).**
   - Defect: amendment item 7 says a mismatch flags every output of the stage "unverified" and that nothing is selected or frozen from flagged outputs. The script only returns exit 3 and a progress line. No marker is written, and `select_frozen.py` does not look for one.
   - Consequence: the coordinator could select or freeze from flagged outputs without noticing.
   - Fix: when `probe post_*` fails, write `$D/dev/P/UNVERIFIED` (or `$D/UNVERIFIED_<stage>`). Make `select_frozen.py` refuse to run when that file exists.

3. **dtmoe_local.sh:34-37 and :31 (resume skips a partial npz).**
   - Defect: a task counts as done if `$o/$t.npz` exists. The `GPU_STOP` exit on line 37 happens before the partial outputs are quarantined on line 38. A script restart also reuses `dev/P` without any check that it is fresh.
   - Consequence: if `run_ts.py` writes the npz non-atomically, or an earlier partial output is left behind, a half-written task counts as complete. It would then be selected on.
   - Fix: quarantine the partial outputs before the `GPU_STOP` exit. Skip a task only when its npz is complete, for example by checking a completion marker or loading the file. Alternatively, refuse a non-empty `dev/P` unless resuming explicitly.

4. **gpu_local.sh (whole file) and dtmoe_local.sh:2-10 (fecs_watch not checked, no log kept beside outputs).**
   - Defect: amendment item 2 requires `fecs_watch.sh` to be active throughout and its log kept beside every GPU output. Item 8 makes this the criterion for the "guarded" flag. Nothing starts or checks `fecs_watch`, and nothing copies its log.
   - Consequence: the chain can run unguarded, and the provenance flag cannot be justified afterwards.
   - Fix: at the top of `gpu_local.sh` and before each `one`, exit if `fecs_watch` is not running. Record its log path and offset at the start and end of each stage.

5. **dr_chain.sh:28 (false "GAVE UP" message).**
   - Defect: `[ n -lt 3 ] && rmdir claims/$i || say GAVE UP` also prints "GAVE UP" when `rmdir` fails, for example when the claim directory is missing.
   - Consequence: a stream can be reported as given up although it was only on its first or second death. Whether it is actually retried depends on `pool_gpu.py`'s claim logic.
   - Fix: use `if [ "$n" -lt 3 ]; then rmdir ... || say "claim missing"; else say GAVE UP; fi`.

6. **dr_chain.sh:20 and gpu_local.sh:10 (given-up DR stream still gives exit 0).**
   - Defect: once the other streams are done, the pool exits 0 even though a task was given up, and the chain says "finished". `gpu_local.sh` then goes on to the dtmoe grid.
   - Consequence: the chain does not exit 1 for a given-up stream, but proceeds as if all 92 were done. This does not break the amendment's stop rule, but the incomplete DR result is easy to miss.
   - Fix: after the pool exits 0, check that every task has an output. If any is missing, `say` which ones and exit 0 with a `DR_INCOMPLETE` marker.

7. **select_frozen.py:31-35 (expected count is fragile).**
   - Defect: `want` assumes the extension adds exactly one value per extended axis. `n_cfg` is derived from `acc`, the configurations present.
   - Consequence: if an `lr` extension adds values on both sides, `want` is too small and a legitimate complete grid is refused. If a whole L×mech combination is missing, `n_cfg` shrinks with it and the check passes wrongly.
   - Fix: take `n_cfg` from the registered grid (`len(L) * len(mech)`). Take the counts of added values per axis from `frozen_{method}.json`, for example the length of the extension lists, not from `"lr" in e`.

I found no other mismatches. The tag and file names match `run_ts.py`. The grid is 3 lr × 2 steps × 2 L × 3 mech × 5 streams = 180. The three probe cells match the amendment. The order is probes, then DR, then the grid, then the bookend. The DR canaries run in fresh processes and are compared to each other and to the reference. A `GPU_STOP` or a canary failure stops everything, and nothing runs after a DR failure.
0.11368260000000001 59.987
**逐项结论**

1. **已修复。** `dtmoe_local.sh:37-41`:pre 探针的 a/b 不一致时,会跑第三次 c,并分别与 a、b 比较,结果只写入 progress,不参与选择。
2. **已修复,但有一个缺口(见 D1)。** `dtmoe_local.sh:43` 写 `$D/UNVERIFIED_<stage>`。`select_frozen.py:17` 会 glob `P/../..`,即 `$D/UNVERIFIED*`,所以 `P=$D/dev/P` 时能匹配到,并在第 19 行拒绝选择。
3. **已修复,但有一个缺口(见 D2)。**
   - 第 50 行只在 npz 存在且能加载时才跳过任务。
   - 第 52 行在每次尝试前隔离残留文件。
   - 第 54 行先隔离部分输出,第 55 行才检查 GPU_STOP 并退出,顺序正确。
   - `guard` 在进程启动前退出,所以不会留下部分输出。
4. **部分修复。**
   - 每个 GPU 任务前都会调用 `guard`(第 18 行),它检查心跳(小于 150 秒)和 GPU_STOP,这一点没问题。
   - 但 fecs_watch 日志只在阶段正常走完时才保存:探针在第 35 行,grid 在第 59 行。
   - 提前退出时(guard 退出、崩溃 exit 2、grid 第 55 行的 GPU_STOP 退出)都不保存日志,而这些正是最需要日志的时候。
   - 第三次分类运行 c 也没有被任何一份日志覆盖。
5. **已修复。** `dr_chain.sh:34`:只有 `n<3` 时才 `rmdir` 认领目录,`GAVE UP` 只在 `n>=3` 时才写。`rmdir` 失败只写 "claim missing",不会再误报 GAVE UP。
6. **已修复,但有一个缺口(见 D6)。** `dr_chain.sh:22-24` 按 `tasks.txt` 里不存在 npz 的流写出 `DR_INCOMPLETE`。
7. **部分修复。** `select_frozen.py:34-40` 在 `--final` 下,按 lr 数 × steps 数 × 6 计算期望数量,并要求 `eligible == rows == want`。但非 final 路径没有这个检查(见 D3)。

**新缺陷**

- **D1** `dtmoe_local.sh:28`、`:27`,以及 guard 的退出路径:收尾探针(bookend)崩溃、被拒绝或被 GPU_STOP 中断时(exit 1 或 2),不会写 `UNVERIFIED_*`。后果:阶段末尾没有完成验证,`select_frozen` 仍会照常选择。建议所有非 `PASSED` 的退出都写标记,或者让 select 要求存在 `PASSED` 标记。
- **D2** `dtmoe_local.sh:53`:任务成功且 npz 能加载,就记 ok 并 break,不再检查运行期间是否出现过 GPU_STOP。后果:在 fecs 报警窗口内跑完的结果会被接受,只能靠事后的收尾探针发现。建议成功后再检查一次 GPU_STOP,有则隔离。
- **D3** `select_frozen.py:33`、`:34`:非 final 模式下完整度检查只靠"缺流的配置不合格"。后果:grid 里有被放弃的任务时,会在不足 36 个配置的情况下直接选出最优,且不报错。建议非 final 也要求 `len(eligible)==36`。`n_cfg=6` 是写死的,没有从注册网格推导;`mech=None` 的方法会因数量不符而安全退出。
- **D4** `dtmoe_local.sh:20`:日志名用 `basename $(dirname $1)`,所以 probe_pre 的 a、b、c 共用同一个日志,post 的 a 也一样。后果:各次运行的日志混在一起,难以分开审计。
- **D5** `dr_chain.sh:32-34`:因 GPU 事故(GPU_STOP)导致的进程死亡也会计入该流的 3 次上限。后果:一个流可能因为硬件故障期间的死亡而被放弃,并在 DR_INCOMPLETE 里列出。建议在 GPU_STOP 存在时不计数。
- **D6** `dr_chain.sh:24-25`:正常完成时不会删除旧的 `DR_INCOMPLETE`。后果:重启后全部完成,过期标记仍在,会造成误判。另外 `miss` 只看 npz 是否存在,不检查能否加载。
