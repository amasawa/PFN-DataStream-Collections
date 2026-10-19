# Fable 5.1 after the dtmoe guard trip (2026-10-19 12:46:54; 1.67 USD, 151 s)

## Question
Senior methodology adviser, read-only, one bounded decision. Answer: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence / Requires user approval. Short.

Context: your previous decision (MICE/logs/table1_fill/fable_dtmoe_cpu.md) and AMENDMENT_BASELINES_20261018e.md (committed b86f1c2): dtmoe on CPU, 4 extra lanes (16 total, user approved "提到 16，附守卫"), nice 19, guard trips if DR batch time > 20% slower.
What happened: probe started 12:35:47 (4 dtmoe procs). Guard tripped 12:41:59: DR stream h3_airlines_b median batch time 7.35 s over 659 batches before dtmoe started (last 50: 7.69 s) vs 10.60 s over 31 batches after -> +44%. 1-min load rose 13.4 -> 16.7. Guard wrote STOP, killed the 4 dtmoe procs; partials quarantined as "stop"; dev/P empty. The script then logged "probe pre FAILED" because outputs were missing - this is a stop artifact, NOT a determinism verdict. probe_pre/ dir exists and the script refuses to rerun while it exists.
So nice 19 does not protect DR: the DR process (drtabpfn, one GPU process, CPU-bound parts) shares the cores; 12 CPU lanes + DR gave 7.35 s/batch; 16 gave 10.6. DR has ~74 h left; a 44% slowdown would add ~30 h.
Options I see: (A) keep total CPU <= 12 + DR: SIGSTOP 4 of the 12 extension processes (their wt is excluded from comparisons; wt is used for timing? timing/peak mem is measured separately after tests per amendment c item 7) while the dtmoe probe and grid run in those 4 slots, i.e. extension 8 + dtmoe 4; (B) dtmoe waits until the extension finishes, then shares 12 lanes with the other tests; (C) accept the DR slowdown (16 lanes, raise guard threshold); (D) 13-14 total lanes, test whether DR stays within 20%.
Question: which option, and the exact operational record (how to handle the stale "probe pre FAILED" line and the probe_pre/ directory: rename to probe_pre_stopped_<ts>? and the deviation record text for amendment e).

## Answer
**Decision**

选 **A**:对扩展的 4 个 run_ts.py 进程 `kill -STOP`,CPU 可运行进程回到 12 + DR;dtmoe 在腾出的 4 个槽里跑 probe 和网格(扩展 8 运行 + 4 挂起,dtmoe 4)。守卫原样保留,阈值不改。这就是我上次决定里登记的备选 C'。probe 重启前先登记 deviation 并提交。

**Supporting evidence**

- 慢的根源是物理核数,不是优先级:12 物理核上已有 13 个可运行进程(12 lane + DR),再加 4 个就有 5 对超线程对共享,DR 无论 nice 都被配对拖慢。nice 只在就绪队列超过逻辑核时起作用,17 < 20,所以 nice 19 对 DR 零保护。
- 16 lane 的总吞吐增益本来就只有 ~8–15%,而 DR 慢 44%(+30 h)。A 把总可运行数恢复到实测安全的 13,总 CPU 吞吐不变,dtmoe 提前 2.5 天得到决定性结论和 s5/L32 实测预算。
- SIGSTOP 零损失:被挂起任务不退出,xargs 不会补位,内存只占 8/30 GB;它们的 wt 失真但 select_frozen.py 完全不读 wt,计时按 c 第 7 项另测。
- A 自带证伪:若挂起 4 个后守卫再次因 DR 触发,说明原因不是进程数(例如 dtmoe 的内存带宽),此时转 B(等待),最多再损失一轮 quarantine。
- D(13–14 lane)每试一次要一个 trip/quarantine 周期,增益 ≤ 5%,不值。C 改守卫阈值等于改用户批准的条件。

**Operational record(按顺序)**

1. 守卫已 STOP、已 kill,不要动 progress.txt 的旧行(只追加)。追加一行:`note: the 12:4x "probe pre FAILED" line is a stop artifact (guard trip 12:41:59, outputs missing), not a determinism verdict`。
2. `mv dtmoe_cpu/probe_pre dtmoe_cpu/probe_pre_stopped_20261019_1241`;把 3 个 `probe_pre.<tag>.txt` 比对输出也移进去。不删除。确认 `PROBE_PRE_PASSED` 不存在、`deaths/` 为空(若有 ≥12:41:59 的 probe 任务 death 记录,按时间线判为守卫 stop,删除并在 deviation 里写明)。
3. dtmoe_cpu.sh 小修并提交:probe 分支 xargs 结束后 `[ -e $D/STOP ] && { say "probe pre STOPPED (guard)"; exit 2; }`,再做比对,避免再出现误导行。
4. 选扩展里 **启动时间最晚** 的 4 个 run_ts.py(`ps -eo pid,etimes,args`,只停 python 进程),`kill -STOP`;把 pid、任务 tag、挂起时刻写进 `dev/suspended_20261019.txt`,并注明这 4 个任务的 wt 无效。
5. 确认 1 分钟 load 回到 ~13、DR 最近批次回到 ~7.4 s(距 12:42 已超过 25 批,守卫窗口已干净),然后删 STOP,`dtmoe_cpu.sh probe pre 4`。
6. `kill -CONT` 时机:dtmoe 路径结束或被停,或扩展的 8 条运行 lane 队列排空,二者先到者;之后 lane 分配回到 e 第 1 项(dtmoe 8,其它测试 8)。

**Deviation record(写入 amendment e 末尾,英文)**

> Deviation 1 (2026-10-19). The probe under item 1 started 12:35:47 with 16 running CPU processes. The guard tripped at 12:41:59 as registered: Drift-Resilient TabPFN stream h3_airlines_b, median batch time 7.35 s over 659 batches before dtmoe (last 50: 7.69 s) against 10.60 s over 31 batches after, +44%; 1-minute load 13.4 to 16.7. The four dtmoe processes were killed, partial outputs quarantined as stop, no deaths. The "probe pre FAILED" line of dtmoe_cpu.sh is an artifact of the missing outputs, not a determinism result; probe_pre/ was renamed probe_pre_stopped_20261019_1241 and nothing of it is used. Cause: the machine has 12 physical cores; 16 CPU processes plus the GPU process pair on hyperthreads and nice 19 does not shield the GPU process. From now on at most 12 running CPU processes plus the GPU process: four of the extension's processes are suspended with SIGSTOP (listed in dev/suspended_20261019.txt; their wall-time arrays are invalid and are not used anywhere, select_frozen.py does not read them, timing is measured under amendment c item 7); the extension continues on 8 lanes, dtmoe runs on 4. They are resumed when the dtmoe path ends or stops, or when the extension's queue is empty, whichever comes first; lanes then follow item 1. The guard is unchanged. A second trip on the DR criterion with 12 running processes means the cause is not the process count; dtmoe then waits for the end of the extension (option B).

**Key risks**

- 挂起数天的进程遇到重启/OOM 即丢失(与其它任务一样,重跑即可,扩展跳过已有输出)。
- 守卫的"earlier"参考中位数现在含 31 个慢批,影响 <5%,可忽略。
- 若 DR 变慢另有原因(内存带宽),A 会再 trip 一次,浪费 ~1 h。

**Remaining uncertainty**:SIGSTOP 后 DR 是否精确回到 7.35 s 未实测,第 5 步会给出答案。

**Confidence**:高(机制解释、A 的安全性);中(dtmoe 4 lane 的网格 ~1.5–2 天到冻结,±30%)。

**Requires user approval**:否。A 严格在用户已批准的范围内(≤16 个进程、守卫不变、可运行数回到 c 的 12),且是用户批准 16 时的既定回退;在下一条进度日志里报告即可。只有选 C(改阈值)才需用户批准。

## Sonnet 5.5 review of the plan (29 s)
**Concrete problems in the plan (4 found):**

1. **Unchecked watchdogs in the extension (medium).** The plan assumes a SIGSTOPped task just sits there for days. It never checks whether the run_ts.py wrapper (`bash -c`, xargs) or any other supervisor has a per-task timeout, a stale-progress or heartbeat check, a wall-clock budget, or an auto-retry. Any of these could kill or restart a frozen task, or abort the run on SIGCONT. Because the progress line is only written when a process ends, a frozen task looks identical to a hung one. Check this before stopping anything. Also confirm the stopped tasks hold no GPU memory, since that would conflict with the GPU util ≥90% rule.

2. **Invalid `wt` is only recorded in a side file (medium).** The four stopped tasks will later write valid-looking outputs whose `wt` includes days of suspension. Today `select_frozen.py` ignores `wt`, but a later table, timing report or anyone reading the outputs can pick it up. `dev/suspended_20261019.txt` is not attached to the outputs themselves. Mark those four output files, or the task tags in the extension manifest, as `wt invalid`. Alternatively, add an assertion that no reporting path reads `wt` for those tags.

3. **Evidence is deleted, and the deviation text can be false (low to medium).**
   - Step 2 says to delete a death record from the stop window. Move it to `probe_pre_stopped_*` instead of deleting it.
   - The deviation text says "no deaths" unconditionally, but step 2 allows that deaths may exist. State the actual finding after checking.
   - The `dtmoe_cpu.sh` STOP-check edit is a script change after the amendment was committed. The deviation text does not mention it, so add it (commit hash) to the deviation.

4. **Step 5 has no check that the fix works before the guard acts (low to medium).** It verifies load and DR batch time before dtmoe starts. That does not test the claim that 12 running processes plus DR is safe once dtmoe is running. The only protection is the guard tripping again, which costs another quarantine and probe cycle. Add a manual check of DR batch time at 10 to 15 minutes after the start, and treat the 44% mechanism claim (physical cores, hyperthread pairing) as a hypothesis, not a measurement. The deviation text states it as fact ("the machine has 12 physical cores…nice 19 does not shield"). Soften the wording, or cite the measurement behind it.

**Not a problem:** the claim that no user approval is needed holds, because the change is strictly more conservative than what the user approved.

**Severity overall:** no integrity-breaking flaw. Items 1 and 2 are worth fixing before the SIGSTOP step.

## Disposition: all 4 Sonnet findings accepted (extension has no watchdog: tune_ext.sh xargs without timeout, CPU only; wt invalid recorded in the deviation and dev/suspended_20261019.txt; evidence moved, not deleted; no deaths existed; cause stated as hypothesis; DR checked manually ~15 min after restart). Lanes after resume scaled to the 12 limit (dtmoe 6, other tests 6).
