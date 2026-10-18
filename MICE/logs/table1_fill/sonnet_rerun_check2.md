0.0640686 24.602
**三项发现的判定**

1. 尝试在运行前持久化:**fixed**。`rerun.py` 现在先 append 一条 `end=None` 的记录并原子写盘,再 `run_once`,之后原地更新。你的测试也确认了 start 先于 end。有一个前提我在 diff 里看不到:`attempt` 和重试上限必须来自重启时重新读取的 `hist_f`。如果它们取自内存计数,跨重启的计数仍然是漏的。

2. 隔离 `.ckpt.npz`:**fixed**。`stem` 去掉 `.npz` 后,`stem + ".ckpt.npz"` 和 `stem + ".ckpt.tmp.npz"` 正好是 `run_drtabpfn.py` 写的路径。`complete()` 也把 `.ckpt.npz` 的残留当作未完成。

3. null schema:**fixed(仅限代码层面)**。为 DR 和 dtmoe 生成了按规格推导的 schema。`valid()` 在 schema 为空时一律返回 False,空 npz 因此被拒绝。你用真实的 DR 和 dtmoe 输出做的验证支持这一点。

**新缺陷**

- `tasks.jsonl`(整个文件):diff 里没有它的重新生成。它仍是旧版本,schema 全是 null。因为 `valid()` 现在对 null schema 一律拒绝,**这 272 个任务(92 个 DR 加 180 个 dtmoe)全部永远无法被接受**。后果是每个任务被重试到上限后放弃。必须重新运行 `make_tasks.py` 并提交。
- `rerun.py:76-96`(`valid` 中所有 `bool(sch) and ...` 分支):对其他集合是整体收紧。`schema()` 在原始输出不存在或类型不识别时返回 None,这类任务现在一律不可接受,此前它们按"非空"或"n>0"放行。你只验证了三个集合的原始输出。其余集合如果有 None schema 的任务,会被全部拒绝。需要统计 `tasks.jsonl` 里 `schema` 为 null 且输出是 npz、pkl、csv、jsonl 或 json 的任务数,应为 0。
- `rerun.py:105`(`complete`):`.ckpt.npz` 现在是"未完成"的判据。如果 `run_drtabpfn.py` 成功结束后不删除 checkpoint,每个 DR 任务都会被判为未完成。你的 12 批测试只验证了输出结构,没有说明成功后 checkpoint 是否被清理。需要确认它在成功时会删除 checkpoint,或在 `complete` 里排除这种情况。
- `rerun.py:166-167`(新增的 `end=None` 记录):任何读取 `hist[*]["end"]` 的代码,例如汇总或 done 记录,遇到被中断的记录会得到 None。diff 里没有展示这些读取点,需要确认它们能处理 None。
- 次要问题:`make_tasks.py` 里 `spec_schema` 写死 `B=100`,dtmoe 测试运行(冻结配置后追加)若使用其他 B,schema 会错。后续追加任务时要带上对应的 schema。

结论:代码层面三项都已修复,但有新缺陷。第一项(`tasks.jsonl` 未重新生成)必须先处理,其他三项需要先核实。
