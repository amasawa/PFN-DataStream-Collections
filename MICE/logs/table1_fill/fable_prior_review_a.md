# Fable 审查前期工作（P1 全路径），2026-10-20 09:26:02–09:32:03，3.05 美元

审核结论（P1 路径端到端 + 整包一致性）：

**1. P0 — 基准 a2 任务在 -h800 根里找不到 kstar.json，首次即失败且不重试**
- 位置：`experiments/mice_tkde_control/bench_pools.py:84`、`experiments/mice_r14/bench_cp.py:96`、`experiments/clean_rerun_mice_h800/make_bundle.sh:17-19`
- 证据：`ks = json.load(open(root / "kstar.json"))`（root = `{RUNS}/mice-r13-bench-h800`）；make_bundle 对 -h800 根只打 `ls -d data*`，注释写 "fresh selections"
- 为何重要：a2 是 tab_poolcap / tab_cpres 的来源；benchmark 只允许 1 次尝试（rerun.py:181），FileNotFoundError 直接 GAVE UP。且 "fresh selections" 与 PLAN.md 第 85-86 行"k* 是冻结输入、永不重算"矛盾。
- 修正：make_bundle.sh 把原根的 `kstar.json`（如有 `m_star.json` 一并）用 `--transform` 复制进 `<root>-h800.tar`，CONTENTS 记录；删除 "fresh selections" 注释；重打 bundle 并重算 SHA256SUMS。

**2. P0 — 三个基准脚本硬编码 TabPFN 缓存路径，覆盖作业环境变量，离线节点上会尝试下载而失败**
- 位置：`bench_pools.py:107`、`bench_cp.py:119`、`bench_resources.py:46`；对照 `HANDOFF.md:43,56`
- 证据：`TABPFN_MODEL_CACHE_DIR=str(Path.home() / "pfn-venvs/cache/tabpfn")`；HANDOFF 把缓存放在 `$WORK/cache/tabpfn`，HOME=`$WORK/home`
- 为何重要：子进程里缓存目录为空 + HF_HUB_OFFLINE=1 + 计算节点可能无外网 → 5 个 exclusive 基准任务全部一次性失败。probe 不含基准任务，发现不了。
- 修正：HANDOFF 步骤 1 改为解压 tabpfn_cache.tar 到 `$WORK/home/pfn-venvs/cache/tabpfn`（或做符号链接），TABPFN_MODEL_CACHE_DIR 指向同一路径；基准前加一行存在性检查。同时让执行方核对 `ext-baselines.tar.files.sha256` 含 `Drift-Resilient_TabPFN/tabpfn/model_cache/tabpfn_dist_model_1.cpkt`（run_drtabpfn.py:27 需要；make_bundle 排除了 `checkpoints`，我无权限读 ~/ext-baselines 验证）。

**3. P1 — ACTIVATION 规定的 dtmoe 10 倍时限参照流程在 HANDOFF 和 rerun.py 中不存在**
- 位置：`ACTIVATION_20261019.md:31-37` vs `HANDOFF.md:64-75`；`rerun.py:149-150`
- 证据：ACTIVATION 要求"TS_DETERMINISTIC unset 的默认模式参照跑进 $WORK/qualify/ref_<n>，严格模式超过 10 倍即停"；HANDOFF 步骤 3 只写 qualify；rerun.py 子环境 = 白名单 + 任务注册变量，无法 unset，也无 timeout。
- 为何重要：HANDOFF 规则 1 禁止执行方跑未注册命令，参照跑无法合法进行；严格模式本地慢 40 倍，probe 可能占 GPU 数天无判定。
- 修正：rerun.py 增加 `qualify --ref`（去掉 TS_DETERMINISTIC/CUBLAS_WORKSPACE_CONFIG，跑一次，只记 wall time）和 `--timeout <s>`；HANDOFF 步骤 3 写明：先 ref，再以 10×ref 为 timeout 跑 strict qualify；三个任意一个超时 → 停 dtmoe 路径并上报用户。

**4. P1 — 没有排除已暂停管线的机制，worker 会按文件顺序领走 dtmoe_dev 和任何 NOT QUALIFIED 集合**
- 位置：`rerun.py:159-166`（仅 `--sets` 白名单）；`HANDOFF.md:78-79`（worker 不带 `--sets`）
- 证据：`if (sets and t["set"] not in sets) ...: continue`；HANDOFF："pause that pipeline (its tasks are not started)" 无执行手段
- 为何重要：180 个 strict dtmoe 任务或失败管线会被自动领取，烧费用并产生不可报告的输出；dtmoe 的生产运行按 ACTIVATION 必须等用户决定。
- 修正：rerun.py 加 `--exclude-sets`；HANDOFF 步骤 4 规定 P1 生产默认 `--exclude-sets dtmoe_dev`，加上任何 NOT QUALIFIED 集合；dtmoe_dev 只在 cap 判定与用户决定后、由协调方新增一条指令时才开。

**5. P1 — 结果回传后在协调方机器上的落位未注册，分析脚本全部硬编码原路径**
- 位置：`HANDOFF.md:89-92`；`experiments/mice_tkde_control/analyse_pools.py:23-25`、`MICE/code/pool_cap_run.py:14-16`、`oracle_recall.py:19-20`；`PLAN.md:86-89`
- 证据：step 5 只写"copy back … to the Windows desktop"；`BENCH = Path.home()/"pfn-runs/mice-r13-bench"`；PLAN 只为基准分析登记路径改造
- 为何重要：H800 输出放进 ~/pfn-runs 或 MICE/results_* 就会覆盖/混入原始结果（违反"原结果不变"）；不放进去则 MANIFEST 那一列分析脚本读不到。"without the input files" 也无定义。
- 修正：现在注册本地布局（例如第二个 HOME `~/h800/` 下的 pfn-runs + 独立 repo checkout 承载 results_*，分析用 HOME= 重定向运行），写进 HANDOFF 步骤 5 和 PLAN "Benchmarks" 段；回传改为整根 rsync（输入已有哈希，排除规则反而易错）。

**6. P1 — Table 1 各 GPU 方法的时间/峰值内存没有可报告的来源**
- 位置：`ACTIVATION_20261019.md:41-43` vs `HANDOFF.md:78-82`
- 证据：ACTIVATION："Timing and peak memory of every Table 1 method are measured on the cluster: GPU methods on an H800"；HANDOFF 生产用 `--gpu shared`，每卡 3-6 进程；exclusive 的只有 5 个基准任务，且不含 drtabpfn / dtmoe。
- 为何重要：共享 GPU 下的 wt / peak_mem 不是干净计时，审稿人可称其不公平；而 DR 与 dtmoe 根本没有独占计时任务。
- 修正：要么在 tasks.jsonl 追加每个 Table 1 GPU 方法在三条真实前缀上的 exclusive 计时任务（注册后再跑），要么在 ACTIVATION 明文：Table 1 计时只来自基准根，DR/dtmoe 计时标注 "shared GPU"。

**7. P2 — 24 h 作业时限与不可续跑的长任务冲突：被 kill 三次即永久放弃**
- 位置：`rerun.py:189-190,183`；`HANDOFF.md:80-81`
- 证据：尝试在运行前就计数；`mice_oracle_r11:all`（4 seed × 6 cell 串行，est 为空）、`drtabpfn:covertype`（1500 批）、基准 a2（3 次重复 × 4 条全长流，仅 1 次尝试）
- 为何重要：任一超过作业时限就会在无故障的情况下 GAVE UP，a2 甚至没有第二次机会。
- 修正：HANDOFF 列出这些任务，单独作业、申请分区最长时限；a2 若被时限 kill，需协调方登记后才可重排，不算入 3 次。

**8. P2 — GPU 作业的 CPU 核数未规定，线程超订**
- 位置：`make_tasks.py:15`（OMP_NUM_THREADS=4）；`HANDOFF.md:78-79`
- 证据：run.py 家族每任务 4 线程 × 每卡 3-6 worker，HANDOFF 未写 `--cpus-per-task`
- 为何重要：集群按卡配核时会严重超订，拖慢并污染 wt；不影响正确性。
- 修正：HANDOFF 步骤 4 规定每 worker 至少 4 核（`--cpus-per-task=4N`），并记入日志。

**总体判定：修复后可交接（第 1、2 项必须先修并重打 bundle；3-6 项须在 probe 前写入 HANDOFF/rerun.py 并提交）。**
