0.1680107
**Defects (7)**

1. **verify_chain.sh:46, 61, 28, 33.** The `cmp/` and `logs/` file names are `$stem.txt` / `$stem.log` with no set name.
   - **Consequence:** `<stream>__<method>` is the same in confirm_cp, r14_confirm, probs_gen and cp_gen (for example `s__ddm1000` and `s__micecp1000_500`). In the later stages line 61 sees the earlier stage's `cmp/<stem>.txt`, skips the task without running it, and the stage reports "done". The log files are also mixed.
   - **Fix:** use `$V/cmp/$name/…` and `$V/logs/$name/…`, or prefix the stem with the set name.

2. **verify_compare.py:38-41.** The loop iterates only over files that exist in the verify dir.
   - **Consequence:** the docstring says a missing file gives exit 1, but only a missing original does. If the replay omits an output the original has (for example `__probs.npz`, or the main npz when only an unrelated filter match exists), the result is still IDENTICAL.
   - **Fix:** iterate over the union of `listdir(vd)` and `listdir(od)` with the same filters, and report "verify missing".

3. **verify_compare.py:39.** `filt not in f` is an unanchored substring match.
   - **Consequence:** `…_m1` also matches `…_m10.npz` and `…_m1.5.npz`. A missing own file can be masked by a neighbour's IDENTICAL file, and extra files get compared. The agrawal_s1 vs agrawal_s10 case is safe because `__` follows the stream name. The left side is still unanchored.
   - **Fix:** match `f == stem + ".npz"` or `f.startswith(stem + ".")` / `f.startswith(stem + "__probs")`.

4. **verify_chain.sh:28, 47, 62.** The first attempt does not clear anything from `$vdir`. `MICE_CKPT_EVERY=10` is set.
   - **Consequence:** after a watcher kill or crash and a chain restart, the task resumes the checkpoint of the killed run. That contradicts "complete replay" in PLAN.md and may carry state from a faulty period. A stale finished `stem.npz` may also be skipped by `run_task.py` and compared without any new run. Only the retry removes ckpts.
   - **Fix:** before the first attempt, run `rm -f $vdir/${stem}.* $vdir/${stem}__*` (ckpt, npz, probs, tmp). Keep the retry removal as well.

5. **verify_chain.sh:58-63.** The task command runs inside `while read … < <(…)`, so it inherits the tasks.txt stream as stdin.
   - **Consequence:** if `run_task.py` or a child process reads stdin, it swallows following task lines and those tasks are silently never replayed.
   - **Fix:** run the task with `< /dev/null`, or read tasks.txt on fd 3 (`read -u3` / `3<`).

6. **verify_chain.sh:56 and 58.**
   - **Line 56:** `$root/data` is a symlink to the original `$orig/data`.
     - **Consequence:** if `run_task.py` or `run.py` writes anything under `<root>/data` (cache, generated streams), it writes into the original run directory.
     - **Fix:** make the link read-only: point at `MICE/data` and chmod it, or copy the data.
   - **Line 58:** `read -r s mm` puts all remaining columns into `mm`.
     - **Consequence:** if tasks.txt has a third column, `[ "$mm" = "$m" ]` never matches and tasks are skipped silently. The "no original" skips also only log a line, and nothing checks the 66/216/60/30 counts.
     - **Fix:** use `read -r s mm _` and assert the number of run and skipped tasks against the PLAN counts at the end of each stage.

7. **verify_compare.py:18-19.** The check is described as "bit identity" but is not one.
   - **Consequence:** `np.array_equal` treats `0.0 == -0.0` as equal, and `equal_nan=True` ignores NaN payloads. `np.float32` NaN scalars fall through to `a == b` and give a false DIFFERENT. Object-dtype arrays can raise on elementwise `==`, which `task()` treats as a mismatch.
   - **Fix:** for numeric arrays compare `a.view(np.uint8).tobytes() == b.view(np.uint8).tobytes()` (contiguous). Handle object arrays element by element with `same()`.

**Missing guard (counts as an eighth item).**
8. **verify_chain.sh:13 (`gate`).** It never checks that fecs_watch is alive.
   - **Consequence:** the watcher exits only after writing GPU_STOP, but it can also crash or never have started. The chain then runs unguarded for hours.
   - **Fix:** in `gate`, `halt` unless `$HOME/pfn-runs/fecs_watch.log.last` was modified within the last 150 s.

**Checks with no defect found**
- **(2) Writes to original dirs:** apart from the symlink in item 6, all writes and `rm` go to `$V`. The canary's reference is only read.
- **(3) Checkpoint resume:** see item 4. Only the retry is a complete replay.
- **(4) dtmoe names:** the stem is consistent with `run_ts.run`. `lr` goes through `float(...):g` and `m` through `:g`, and `$st` is the raw int. Two assumptions I can't confirm from the files: `tasks.txt` has no header (line i+1 is task i), and the queue has at least 39 lines. The `_m1` prefix problem is item 3.
- **(5) fecs_watch.sh:**
  - **CPU jobs:** none of the four patterns matches `tsbase/bin/python run_ts.py` or `stream/bin/python run_trained_probs.py`, so they are not killed. This holds as long as no CPU job also runs a `run_task.py`.
  - **GPU jobs:** `pool_gpu.py`, `run_task.py` (venv), `totgpu/bin/python` and `drtabpfn/bin/python` (canary) are all covered.
  - **Other cases:** a localized "no events" message gives READFAIL and a stop, which fails safe.
- **(6) Output names:**
  - **Filter:** `${s}__${m}` also matches `__probs.npz`, so it is compared.
  - **Checkpoint:** `${stem}*ckpt*` covers `dst[:-4]+".ckpt"` plus its suffix.
  - **Skipped or wrongly compared:** the cross-set `cmp` collision (item 1), a probs file missing from the replay (item 2), and extra columns (item 6).
- **Canary:** `canary_dr.py` writes an input `elec2.npz` into the output dir. The reference dir `drgpu` must contain an identical `elec2.npz`, or the canary fails as "original missing". I can't tell from the files whether it does.
0.1002846
**逐项结论**

1. **cmp/log 名称冲突:已修复。** 日志和比较结果现在按 `$set` 分目录:`logs/$set/$stem.log`、`cmp/$set/$stem.txt`。
2. **compare 漏掉 replay 中缺失的文件:部分修复。**
   - 带 stem 的调用已修好。文件名由"任一目录存在"决定,replay 缺失会报 MISSING,你也测过。
   - 未修好的是不带 stem 的调用。`verify_compare.py:50` 只列 `vd` 的文件,而 `canary()` 正是这样调用的(verify_chain.sh:20-21)。
   - canary 的 `b` 少了 `a` 有的文件会被报成 DIFFERENT,尚可。反过来,`a` 少了 `b` 或参考目录里有的文件,不会被发现。
3. **stem 过滤未锚定:已修复。** 现在用精确的 `stem+ext` 拼名。
4. **首次运行可能续用旧 checkpoint 或旧输出:已修复。** `task()` 在首次运行和重试前都调用 `clean()`。
   - 我无法确认 ckpt 的实际文件名都落在 `$stem.ckpt*` 里,请你对照 run_task 核实一下。
5. **任务继承 tasks.txt 的 stdin:已修复。** 任务命令带 `< /dev/null`。
6. **data 软链、多余列、无计数:已修复。**
   - 现在是 `cp -r` 加 `diff -r -q`。
   - `read -r s mm _` 能处理多余列。
   - 结束时会记录 nrun、nskip 和 tasks.txt 的行数。
7. **不是字节级比较:基本修复。** 数组、标量、float 都按字节比较,dtype 和 shape 也检查。
   - 小缺口:`verify_compare.py:17` 里 `a` 是 dict、`b` 不是时,会抛 `AttributeError` 而不是返回 False。
   - 后果只是崩溃,链会按失败处理并停止,所以是安全的。
8. **没有 watcher 存活检查:已修复。** `gate()` 检查 `.log.last` 的 mtime 小于 150 秒;文件不存在时按过期处理。

**新缺陷**

- **verify_chain.sh:36-37, 49, 68:重跑时会跳过已不一致的任务(最严重)。**
  - 缺陷:DIFFERENT 时也会把 cmp 文件 `mv` 成最终名。
  - 后果:人工处理后删除 CHAIN_STOP 重跑,`[ -e cmp/... ] && continue` 会把这个任务当作"已比较",永远不再重放。链最后还会输出 "chain done"。
  - 修法:只在 IDENTICAL 时才写最终名;或者跳过前先检查文件里没有 DIFFERENT 或 MISSING。
- **verify_chain.sh:60-61:data 拷贝被中断后不再校验。**
  - 缺陷:`cp` 中途被杀会留下残缺的 `$root/data`。
  - 后果:`[ ! -e $root/data ]` 为假,于是跳过拷贝和 diff,用残缺数据继续跑。
  - 修法:每次都执行 diff,或者先拷到临时目录再 `mv`。
- **verify_chain.sh:84:可能静默跑零个任务(推测,取决于文件内容)。**
  - 缺陷:这里的 `awk '{print $2}'` 没有像第 70 行那样 `tr -d '\r'`。
  - 后果:如果 r14 的 tasks.txt 是 CRLF 且方法名在最后一列,order 里的名字会带 `\r`,和第 70 行已去掉 `\r` 的 `$mm` 对不上。结果 `nrun=0`,链只写日志,不会停。
  - 请检查 tasks.txt 是否是 CRLF。
- **verify_chain.sh:57-73:原任务没有被 order 覆盖时不会报错。**
  - 缺陷:`nrun + nskip` 与 tasks.txt 行数不符时,只写进日志,不会停。
  - 后果:order 之外的方法会被静默漏掉。
  - 修法:不符时 `halt`。
- **verify_chain.sh:27:`$2*.tmp*` 通配过宽。**
  - 缺陷:例如 `ltm1000` 会匹配 `ltm1000_75...tmp`。
  - 后果:任务串行执行,目前基本无害,只是不够精确。
- **verify_chain.sh:45-48:队列行缺失时静默跳过。**
  - 缺陷:`tasks.txt` 少于 39 行时,`stem` 为空,`float("")` 报错,然后被记成 "skip (no original)"。
  - 后果:不会停,漏检不容易被发现。
- **verify_chain.sh:13:CHAIN_STOP 残留。**
  - 缺陷:CHAIN_STOP 存在时,重跑会在第一个 `gate` 处不写日志直接退出。
  - 后果:这大概是有意设计,但需要手动清理,也看不到原因。

这次没有读 `canary_dr.py` 和 `run_task.py`。依赖它们行为的地方(ckpt 命名、`$c/$k` 目录是否自动创建、tasks.txt 格式)我只能指出,不能确认。
