# MICE 集群重跑日志（执行者：Mac mini 上的 Claude Code）

时间为 Mac 本地时间（AEDT，UTC+11）；集群时间为 CST（UTC+8），两者差 3 小时。

## 2026-10-20 16:40 AEDT 准备

- 用户把 `mice_cluster_all.tar` 解包到 `~/Desktop/mice_cluster_all/`。三个数据包在 Mac 上 `shasum -a 256 -c SHA256SUMS`
  均 OK：mice_h800_bundle（1.2G）、mice_h800_bundle_p2（4.8M）、mice_h800_bundle_p3（3.1G）。
- 仓库从 GitHub 克隆到 `~/Desktop/mice_cluster_all/repo`，HEAD = a7405e0（含 ACTIVATION 与修正 a–d）。未用 repo.bundle。

## 2026-10-20 16:49 AEDT Step 0 访问

- 登录：`ssh tj`（~/.ssh/config 别名：logini.tongji.edu.cn，端口 10022，用户 u2105445，公钥，ControlMaster 8h），
  免密，由另一 Claude 会话（h800run-c9）事先配置。需要同济 MotionPro VPN 在线。登录节点 logini04。
- 账号：`sacctmgr show assoc` 显示 account p_p2105445 / qos cpu-500_core-a800-8_card（另有 u2105445、d_000313，qos normal）。
  qos 的 GrpTRES / MaxTRESPU 字段对普通用户显示为空，MaxWall = 7-00:00:00。上限按 qos 名与用户核实：8 张 A800、500 核。
- `sinfo -o "%P %G %D %t %l"`（13:49 CST）：
  - A800：gres `gpu:a800:8`，19 个节点（11 mix、5 alloc、3 drng），时限 infinite（作业实际受 qos 7 天限制）。
  - L40 / L40-ubunut / L40-fbb：gpu:l40:8（本账号 L40 额度 0，不用）。
  - CPU 分区：intel（默认）、amd、fata。
- 存储：`/ssdfs/datahome/u2105445`，文件系统 HPCSSD_NVME 513G，已用 14K。WORK = `/ssdfs/datahome/u2105445/mice_rerun`（新建，之前不存在）。
- 登录节点网络：pypi.org 200、download.pytorch.org/whl/cu126 200、pypi.tuna 200、mirrors.aliyun 200、hf-mirror.com 200；
  huggingface.co 不通（TabICL 权重走 HF_ENDPOINT=https://hf-mirror.com）。
- 软件：module 有 anaconda3/24.1.2、miniconda3/24.1.2、cuda 11.1–13.0。CUDA 驱动版本待 Step 2 的 GPU 作业里 `nvidia-smi` 记录。
- 已知约束（h800run-c9 实测）：GPU 必须写 `--gres=gpu:a800:N`；每卡最多 7 核（超出提交即拒）；内存约 1.8GB/核；
  共享环境 pytorch_nvidia_2.7.1 的 torchrun 缺 importlib_metadata（本重跑不用该环境）；MPS 可由普通用户在作业内启动。

## 2026-10-20 16:50 AEDT Step 1 输入：开始上传

- `rsync -a --partial` 三个数据包到 `$WORK/bundle/`、`$WORK/bundle_p2/`、`$WORK/bundle_p3/`。
- 实测上行约 366 KB/s（VPN 上行瓶颈），4.3G 预计 3 小时以上。用户决定照原流程传（不改为集群直接下载权重）。
- 17:26 AEDT VPN 断开（`Could not resolve hostname logini.tongji.edu.cn`），mice_h800_bundle 的 rsync 报
  `unexpected end of file` 中断；已停止上传，`--partial` 已保留部分文件，VPN 恢复后续传。
- 环境脚本 `cluster/setup_envs.sh` 已写好（conda 基础 Python 3.12.15 / 3.11.17 + venv，`pip install --no-deps -r` lock，
  freeze 与 lock 逐行比对），尚未在集群上运行。

## 2026-10-20 17:40–19:00 AEDT Step 1 续传、Step 2 环境

- 17:40 VPN 恢复后续传（失败自动重试）。18:14 清理集群上断线遗留的 4 个 rsync server 进程。18:29 又断一次，自动重连。
- 18:40 用户同意并行传：p3_weights.tar 在 Mac 上 `split -b 420m` 成 8 块（各块 sha256 记在 PARTS.sha256），
  每个文件一路 rsync，8 路并行。实测总速度约 216 KB/s，并行没有提速（VPN 总带宽受限；家宽上行实测 55 Mbps）。
  集群上拼回后用 bundle_p3/SHA256SUMS 校验整个 tar。
- 环境（登录节点 tmux，`cluster/setup_envs.sh`；conda 基础 Python 来自清华 pkgs/main；pip 源 pypi.tuna + download.pytorch.org）：
  venv（3.12.15，109 包）、totgpu（3.11.17，46 包）、stream（3.12.15，11 包）、tsbase（3.12.15，34 包）、tabdpt（3.12.15，94 包）。
  `pip freeze --all` 写入 `cluster/env_freeze_<env>.txt`。初次逐字比对时 totgpu、tabdpt 报差异，全部是包名写法
  （Jinja2/jinja2、typing_extensions/typing-extensions、PyYAML/pyyaml 等），版本相同；脚本改为按 PEP 503 规范名比对后，
  5 个环境全部与 env_lock 一致（pip/setuptools 也与 lock 一致）。drtabpfn 等 ext-baselines 解包后再建。
- TabICL 权重 `tabicl-classifier-v2-20260212.ckpt`：在登录节点经 HF_ENDPOINT=https://hf-mirror.com 下载到 HF_HOME=$WORK/hf，sha256 待记录。
- TabICL 权重 sha256 = bdc7dbd5e4ff21f8f0456fcf90c6b7cdf72dbea960f2d05b19bec19f9b3d4ed0
  （hf/hub/models--jingang--TabICL/snapshots/4dcd344ece2c00be9e831fdd35bed57b5ad83e19/）。

## 2026-10-20 20:44–21:51 AEDT 上传中断、P3 权重改由集群下载（待协调者登记）、P1 输入就绪

- 20:44 左右 Mac 上的并行上传进程到达执行时限被终止（Claude Code 后台任务上限 2 小时）。此时 P1 只差
  runs/mice-tkde-control-20261009.tar，P2 已传完，P3 的 8 块只传了约 350 MB。21:47 单独补传完 P1 最后一个文件。
- **P3 权重运输方式变更（用户同意；请协调者登记）。** 修正 d 后 P3 只用 TabPFN-3.5 和 TabDPT。
  p3_weights.tar 的 3.1G 里，需要的只有 tabpfn-v3.5-20260909.safetensors（876 MB）、tabdpt1_3.safetensors（252 MB）
  和 tabdpt/config.json；其余（LimiX-2 1.6G、Mitra、v2.5/v2.6/v3）已取消。按包内 urls.txt 的固定 commit，
  在登录节点经 hf-mirror.com 下载到 `$WORK/p3_download/`，用 p3_weights.tar.files.sha256 中的值逐个核对：3 个文件全部 OK。
  这是运输方式的变更（文件按哈希完全相同），未改任何任务。正式放到 `$W3`（= $WORK/home/mice-p3-weights）前，
  等协调者登记；P3 包其余小文件（SHA256SUMS、ext-baselines-p3.tar 等）已在集群。
- 21:48 `cluster/unpack_inputs.sh p1`：bundle SHA256SUMS OK；MICE_data.tar → $WORK/repo/MICE，18 个 runs/*.tar →
  $WORK/home/pfn-runs/<root>，ext-baselines.tar → $WORK/home/ext-baselines（DR model_cache 列在 files.sha256 中），
  tabpfn_cache.tar → $WORK/home/pfn-venvs/cache（含 tabpfn-v2-classifier-finetuned-zk73skhh.ckpt）；每个 tar 解包后
  `sha256sum -c <tar>.files.sha256` 全部 OK。
- 探针前检查：`find $WORK/repo/MICE -path "*results_*" \( -name "*.npz" -o -name "*.pkl" \) | wc -l` = 0。
- 作业脚本（cluster/）：env.sh（作业环境变量、MPS 启停）、gpu_check.sbatch、probe_main.sbatch、probe_dtmoe.sbatch。
  探针在生产配置下运行（修正 b 第 2 条）：1 张 A800、7 核、MPS、卡上 3 个进程（3 条 lane，每条 lane 内按顺序）。
  dtmoe 三个 id 各一条 lane：先 `rerun.py ref`，再 `qualify --timeout ceil(10 R)`。

## 2026-10-20 22:08 AEDT Step 2 GPU 检查、Step 3 探针提交、Fable 咨询（KumoRFM）

- drtabpfn（3.11.17）freeze 与 lock 一致（-e 行为 git+…Drift-Resilient_TabPFN@a6e75afb）。
- sbatch 用 `-c 7` 单独写被集群拒绝（"必须为每个 GPU 设置不超过 7 个 CPU 核心"），改为 `--ntasks-per-node=1 -c 7` 后通过。
- GPU 检查作业 3048466（gpu8011，24 s）：NVIDIA A800-SXM4-80GB，驱动 550.54.14，compute mode Default；
  venv 2.14.0+cu126、drtabpfn 2.1.2+cu121、totgpu 2.3.1+cu121、tabdpt 2.14.0+cu126 的 arch list 均含 sm_80，matmul 正常；
  作业内 MPS 启动、接管、停止正常。
- 探针：3048479（probe_main，gpu8011）、3048480（probe_dtmoe，gpu8012），19:08:31 CST 同时开始。
- 用户问"要不要比较 TabDPT、Kumo、TabICL，Fable 给个意见"。Fable 5.1 咨询（21 s，0.92 美元；问题文件见本次会话 scratchpad）：
  (1) 不把 KumoRFM 加为 P3 第三个骨干：它是多表关系模型，只有 SaaS/SDK/NIM，未找到离线权重，违反离线和逐位一致要求，
  且属于登记中已有的排除理由（权重无法离线获得）；(2) 不做骨干之间的比较，只按登记的四个假设报告；附录可放一张描述性表，
  不做排名。可选：相关工作中引用 KumoRFM（改论文需用户同意）。执行者接受，未改任何登记。

## 2026-10-20 19:25 CST（22:25 AEDT）探针：results_heldout_tabicl NOT QUALIFIED

- [5] mice-r14-test:t_b2000_c100_s40_o0__micecp1000_500：QUALIFIED（bit-identical），19:16:37 CST。
- dtmoe 参考时间：[9] elec2 L16 R = 123.0 s，[10] elec2 L32 R = 123.0 s（gpu8012，rc 0）；严格模式 qualify 上限 1231 s，19:10:35 开始。
- **[3] results_heldout_tabicl:covertype__ddm1000：NOT QUALIFIED**（19:25:22 CST；a 492 s，b 519 s，两次 rc 0）。
  rerun.py 报告的不同项：covertype__ddm1000.npz 的 `ll`。逐数组比较（qualify/3/a/out 对 b/out，`logs/npzdiff.py`）：
  - 相同：acc、B、concept（150000）、calls、n_experts、cuts、closes。
  - `ll`（1500，float64）：1 个 NaN，位置相同；其余 1499 个有限值中 1317 个不同，max abs diff 7.2e-08，
    相对差中位数 7.6e-08，最大 2.1e-05。即浮点舍入量级的差异，acc（预测）逐位相同。
  - `wt`（每批墙钟时间）不同，属于计时，rerun.py 按设计不比较。
  - 任务：MICE_BACKBONE=tabicl，TabICLClassifier(device="cuda", random_state=seed, n_estimators=4)，OMP_NUM_THREADS=4，
    MPS 下卡上 3 个进程。初步判断：TabICL 在 A800 上的 GPU 计算不是逐位确定的（推测为非确定性 kernel），
    只影响概率的末几位，不影响预测；但按登记这仍是 NOT QUALIFIED，由协调者诊断。
- **处置（HANDOFF step 3）：** 暂停 TabICL 骨干的全部 4 组（同一骨干、同一调用）：results_heldout_tabicl（16）、
  results_heldout3_tabicl（16）、results_heldout4_tabicl（12）、results_heldout4_tabicl_e（12），共 56 个任务（估计 22 GPU 小时）；
  生产 worker 加入 `--exclude-sets`。证据保留在 `$WORK/qualify/3/`（a、b 两次完整输出与日志）。等协调者诊断并登记处置。
  其余探针继续。

## 2026-10-20 19:31 CST（22:31 AEDT）dtmoe 探针：TOO SLOW，dtmoe 路径停止，交用户决定

- [9] dtmoe_dev:elec2__dtmoe_L16_lr0.0001_s1_m2：默认模式 R = 123.0 s；严格模式（TS_DETERMINISTIC=1，
  CUBLAS_WORKSPACE_CONFIG=:4096:8）第一次运行在 1231 s（10 R）被终止：**TOO SLOW**，无确定性结论。
- [10] dtmoe_dev:elec2__dtmoe_L32_lr0.0001_s1_m2：R = 123.0 s；严格模式 1231 s 被终止：**TOO SLOW**。
- [11] dtmoe_dev:insects_abrupt_balanced__dtmoe_L32_lr0.001_s5_m2：R = 1385.7 s（rc 0）；严格模式 19:31:37 开始（上限 13858 s）。
  按 ACTIVATION 第 2 条（"one TOO SLOW stops the dtmoe path"），dtmoe 路径已停止，[11] 的结论不再影响决定，
  继续运行要占 1 张 A800 约 7.7 小时；执行 `scancel 3048480`，作业于 19:32:11 CST 取消（运行 23:40）。[11] 记为“未完成，已取消”。
- 三个参考运行均在 gpu8012、MPS、卡上 3 个进程下运行（与生产配置一致）。证据：$WORK/qualify/ref_9..11、9.out、10.out、11/a。
- **待用户决定 dtmoe 路径**（ACTIVATION 第 2 条：退路方案、CPU 或不跑 dtmoe；决定不依赖任何 dtmoe 分数）。
  dtmoe_dev 继续不启动（生产 `--exclude-sets dtmoe_dev`）。
- 22:34 AEDT 用户要求问 Fable dtmoe 怎么处理。Fable 5.1（60 s，1.16 美元）建议 **A：dtmoe 全部在集群 CPU 节点单线程跑**
  （探针 run-twice 先行；固定一种 CPU 节点型号，建议与 P2 相同的 EPYC 9654；新目录、不混设备；网格、扩展、测试后各做 bookend；
  论文 dtmoe 行标 "CPU" 并加脚注）。不选 B（默认模式 GPU，MPS 下 MoE 路由几乎必然不逐位一致，需为一个方法改完整性规则）、
  C（严格模式估计 ≥600 GPU-h）、D（隐藏最接近的基线，只作 CPU 探针失败后的兜底）。成本粗估 350–800 CPU-h，墙钟 1–2 天（±50%）。
  需用户批准，并由协调者写成 amendment 提交后执行。执行者补充：现登记的 dtmoe 任务行带 TS_DEVICE=cuda、TS_DETERMINISTIC=1、
  {PYTOT}（totgpu，torch 2.3.1+cu121），CPU 方案需要新的任务清单（协调者生成并登记），执行者不改任务。

## 2026-10-20 19:40 CST（22:40 AEDT）MPS 实际未生效；用户决定先不开 MPS 跑 30 分钟

- 在探针作业 3048479 内（`srun --jobid --overlap`）查看：卡上 3 个任务进程的类型均为 `C`，不是 MPS 客户端的 `M+C`；
  MPS 控制进程在 /tmp/mps_pipe_3048479 正常运行。原因：rerun.py 的子进程环境白名单 KEEP 不含
  CUDA_MPS_PIPE_DIRECTORY / CUDA_MPS_LOG_DIRECTORY，任务进程找不到本作业的 MPS，退回普通 CUDA 上下文。
  因此到目前为止的探针都在“无 MPS、卡上 3 个进程”的配置下运行。
  同时观测：3 个进程合计显存 2.9 GB / 80 GB，GPU 利用率 87%（单次采样）。
- 不把 MPS 放到默认 /tmp/nvidia-mps：节点与其他用户共用，可能影响他人作业。
- **请协调者：** 若要 MPS 生效，最小改动是把 CUDA_MPS_PIPE_DIRECTORY、CUDA_MPS_LOG_DIRECTORY 加入 rerun.py 的 KEEP；
  改后 MPS 配置需重做探针（修正 b 第 2 条：探针与生产同配置）。
- **用户决定（22:41 AEDT，选项 1）：“选1，先不开MPS跑30分钟”**。生产先在与探针相同的配置下运行（无 MPS，作业不启动 MPS 守护进程），
  头 30 分钟比较每卡 3 个与 2 个 worker 的吞吐，并记录 8 张卡的显存、GPU 利用率和内存。

## 2026-10-20 22:59 AEDT 用户决定 dtmoe 路径：CPU

- 选项（执行者转述 Fable 建议后提出）：A 集群 CPU 单线程（推荐）/ B GPU 默认模式 / C GPU 严格模式加预算 / D 不跑 dtmoe。
  用户原话："cpu 跑呗"。决定时没有任何 dtmoe 分数（集群上没有 dtmoe 输出被读取；参考运行只读墙钟时间）。
- **请协调者：** 按 Fable 协议写成 dated amendment 并生成 CPU 任务清单（单线程、TS_DEVICE 不设、TS_DETERMINISTIC 不设、
  CPU 版 torch 环境、新输出目录、固定 CPU 节点型号，run-twice 探针先行），提交后执行者再运行。dtmoe_dev 在此之前不启动。

## 2026-10-20 20:01–20:06 CST（23:01–23:06 AEDT）探针收尾；生产首次提交传参错误，已取消并重交

- [2] results_test:agrawal_s10__fifo1000 QUALIFIED（19:58:37）；[1] results_heldout3:h3_airlines_b__micev1000_500 QUALIFIED（19:56:50）；
  [6] mice-r14b-acc:…snap1000_500.k2 QUALIFIED（19:47:51）；[4] results_probs:covertype__ddm1000 QUALIFIED（19:41:12）；
  [7] mice-tkde-control-20261009:mis_micev_mis_b700_c30_s30 QUALIFIED（20:01:30）。[8] drtabpfn:elec2 仍在运行（drtabpfn 组本就不进共享生产）。
  汇总：6 QUALIFIED（[1][2][4][5][6][7]），1 NOT QUALIFIED（[3] TabICL），dtmoe 3 个 TOO SLOW/取消，[8] 待定。
- 20:02 提交 3048761（NW=3，4 卡）、3048762（NW=2，3 卡）；第 8 张卡仍被探针占用。
- **错误：** `sbatch --export=ALL,NW=..,EXCL=a,b,c` 中逗号被当作变量分隔符，EXCL 只剩 `dtmoe_dev`。3048762 在 gpu8012 上运行 39 s
  （20:04:39–20:05:18）后由执行者 scancel；3048761 未开始即取消。期间 worker 按文件顺序只领取了 6 个 results_grid_test 任务
  （grid_c100_b2000_s10 的 ddm1000、fifo1000、micev1000_500、oracle1000、winens1000，s11 的 ddm1000），没有任何暂停组的任务启动。
  这 6 个任务各记 1 次被杀的尝试（attempt 0，rc 未写入），`rerun.py release` 释放 6 个 claim；下次运行前其部分输出由 rerun.py 自动隔离。
- 20:05 改为先 `export EXCL=…` 再 `sbatch --export=ALL` 重交：3048786（NW=3，4 卡）、3048787（NW=2，3 卡），排队中。

## 2026-10-20 20:07–20:12 CST（23:07–23:12 AEDT）生产停止：run.py 家族输出多出 cuts / closes，结构检查失败

- 3048787（NW=2，gpu8012，20:06:09 起；排除列表完整）运行约 2 分钟，20:07:50–52 四个任务 GAVE UP：results_grid_test 的
  grid_c100_b2000_s10__ddm1000 / __fifo1000 / __oracle1000、grid_c100_b2000_s11__ddm1000（各 2 次尝试 rc 0，加上 20:04 被杀的
  1 次，3 次用完）。执行者 20:08:19 scancel 3048787，3048786 未开始即取消。done=0，gaveup=4，claims=10（未释放，见下）。
- **原因：** rerun.py `valid()` 要求 npz 的键与 tasks.jsonl 的 schema（取自原始输出）完全一致（只忽略 wt、te、peak_mem）。
  当前 MICE/code/run.py 的 `np.savez_compressed` 多写两个键：`cuts`（(0,2) int64）和 `closes`（(0,4) int64），
  由 e62ebce（2026-10-15 14:15，round 14 "stored-context provenance"）加入；原始 results_* 输出早于此，schema 中没有这两个键。
  任务本身每次 rc 0、写出完整 npz（acc、ll、wt、B、concept、calls、n_experts 结构都与 schema 一致），只是被判为不完整。
- **影响范围：** run.py 家族的全部 results_* 组：生产中 843 个任务（不含已暂停的 TabICL 4 组），估计 60 GPU 进程小时。
  用探针输出核对 schema：[1] heldout3、[2] results_test、[4] results_probs 的主 npz 均 schema-invalid（同一原因）；
  其他驱动的 [5] mice-r14-test、[6] mice-r14b-acc、[7] mice-tkde-control 的全部输出 schema-valid。
  不受影响的共享生产任务：1646 个，估计 209 GPU 进程小时。
- **请协调者（HANDOFF 规则 1，执行者不改代码）：**
  1. 判断当前 run.py 与原始 results_* 运行的计算是否相同（e62ebce 只加了记录，还是也改了计算），并登记处置；
     最小的操作性修正是 `valid()` 的忽略键加上 cuts、closes（与 wt 同类的记录键），或按当前输出更新 schema。
  2. 提交 4 个 GAVE UP 任务的尝试记录重置（它们的 3 次尝试中 1 次被执行者传参错误时 scancel，2 次被本问题判失败）。
  3. 10 个 claim 未释放、4 个 gaveup 记录和 MICE/results_grid_test 下现有输出（含 1 个 .ckpt）保持原样，等处置。
- 23:10 AEDT 用户决定："好，先跑那1646个"。提交 3048856（NW=3，4 卡）、3048857（NW=2，3 卡），`--exclude-sets` 共 21 组：
  dtmoe_dev、drtabpfn、mice_oracle_r11、results_delay_dev 和全部 results_*（含 TabICL 4 组），排队中。

## 2026-10-20 20:15–20:50 CST（23:15–23:45 AEDT）生产开始（1646 任务子集）；头 30 分钟吞吐

- 4 卡/3 卡作业排队预计要到 22:49 和次日 14:26，20:15 改为 7 个单卡作业（每个 1×A800、7 核，SLURM_MEM_PER_CPU=18400 MB）：
  NW=3：3048892/3/4（gpu8017，20:15:11）、3048895（gpu8011，20:19:12）；NW=2：3048896/7（gpu8011，20:26:42）、3048898（gpu8012，20:37:17）。
  [8] drtabpfn:elec2 **QUALIFIED**（20:19:08），探针作业 3048479 结束。探针最终：7 QUALIFIED、1 NOT QUALIFIED（[3]）、dtmoe 停止。
- 20:44 CST 统计（res.csv 每分钟采样；ok = 通过结构检查的任务；当前全部为 mice-r14-test，每个约 40 s）：

  | 作业 | NW | 运行 | ok | GAVE UP | GPU 利用率均值 | 显存峰值 |
  |---|---|---|---|---|---|---|
  | 3048892 | 3 | 29 min | 21 | 0 | 62% | 2882 MiB |
  | 3048893 | 3 | 29 min | 26 | 0 | 66% | 2886 MiB |
  | 3048894 | 3 | 29 min | 24 | 0 | 65% | 2810 MiB |
  | 3048895 | 3 | 25 min | 26 | 0 | 66% | 2949 MiB |
  | 3048896 | 2 | 17 min | 11 | 0 | 38% | 1782 MiB |
  | 3048897 | 2 | 17 min | 13 | 0 | 40% | 1938 MiB |
  | 3048898 | 2 | 7 min | 6 | 0 | 32% | 1782 MiB |

  每卡每小时完成：NW=3 约 43–62（均值约 52），NW=2 约 38–45。驻留内存（ps 统计的是本用户在该节点上所有进程之和，
  含同节点其他作业）最高 15.4 GB，单个作业分配 7×18.4 GB ≈ 129 GB，远低于 80%。显存最多 2.9 GB / 80 GB。
  **按修正 b 第 2 条取 NW=3**（每小时完成更多，内存远未到 80%）。
- 20:44 用 `srun --jobid --overlap` 给 3 个 NW=2 作业各加第 3 个 worker（不重启作业、不杀任务）。核查发现这 3 个 worker 都在 srun
  步骤结束时被 Slurm 回收（3048895 的 w3 是作业自己的）；它们各已领取 1 个任务并开始运行，任务进程也一并结束。
  受影响的 claim 约 3 个（20:44:20–30 领取的 mice-r14-test t_b500_c100_s42_o0__ddm1000 等），在 claims 中保持“已领取”，
  作业结束后 `rerun.py release` 再跑（各记 1 次被杀的尝试）。此法不再使用；NW=2 作业继续以 2 个 worker 运行。
- 20:45 提交 3049189（NW=3）用第 8 张卡，排队中。
- 生产状态：mice-r14-test done=127（20:44），其余 1646 子集任务按文件顺序待跑。

## 2026-10-20 23:49 AEDT 用户决定：单线程组每卡 5 个 worker（请协调者登记）

- 证据（20:5x CST，gpu8017 上 3 个 NW=3 作业，共 21 核）：本用户进程 CPU 合计约 870–890%（约 9 核，43%），
  9 个任务进程各 100%（mice-r14-test，OMP_NUM_THREADS=1，每个 worker 只占 1 核）；GPU 利用率 NW=3 约 65%，显存 ≤ 2.9 GB。
  即 CPU 和显存都有余量，GPU 未饱和。
- 线程数按组完全分开：当前运行的 1646 任务子集（mice-r14-*、mice-r13-acc、mice-tkde-control-20261009、mice-*-cp-*、
  mice-table1-probs-gen、mice_seg_origin_r12）全部 OMP_NUM_THREADS=1；results_* 各组全部 OMP_NUM_THREADS=4。
- 用户说"那看利用率每张卡5个worker比较合适"；执行者说明修正 b 只允许 2 或 3、探针须与生产同配置后，用户："好，按这个办"。
- **请协调者登记（修正 b 第 2 条的变更）：** OMP_NUM_THREADS=1 的组每卡 5 个 worker（7 核/卡不变）；OMP_NUM_THREADS=4 的组
  （results_*）保持每卡 3 个。登记后执行者先在每卡 5 个进程下重跑 OMP=1 组的探针（[5] mice-r14-test、[6] mice-r14b-acc、
  [7] mice-tkde-control 各 qualify 一次，5 个进程同卡并发），全部 QUALIFIED 再把生产换成 NW=5；30 分钟后与 NW=3 比较吞吐并记录。
  在此之前生产保持 NW=3。

## 2026-10-21 00:07 AEDT（21:07 CST）按用户指示改为每卡 5 个 worker（未等协调者登记）

- 21:06 CST 最近 10 分钟 GPU 利用率：NW=3 的 5 张卡 55–67%，NW=2 的 3 张卡 38–46%；显存 1.5–2.6 GB / 80 GB。
- 用户："我都说了workder 要5个呀"。执行者此前把"好，按这个办"理解为"登记后再改"，是理解错误；按用户指示立即执行，
  修正 b 第 2 条（2 或 3 个 worker）的变更仍请协调者补登记。
- 做法（不杀任何正在运行的任务）：在登录节点 tmux 中对每个作业 `srun --jobid=<j> --overlap -n1` 以前台方式运行追加的
  `rerun.py worker <j>_g0_w<k>`（步骤随 srun 存活；20:44 的后台方式会被回收，已弃用）：
  NW=3 作业（3048892/3/4、3048895、3049189）各加 w4、w5；NW=2 作业（3048896/7/8）各加 w3、w4、w5。
  核查：抽查 4 个作业，每张卡 5 个 GPU 进程、5 个 worker。追加的 worker 共用作业原有的 7 核。
- 确定性：当前运行的组全部 OMP_NUM_THREADS=1。按 HANDOFF step 4 的 recheck，在 5 worker 负载下（3048892 内再加 1 个进程）
  `rerun.py recheck mice-r14-test:t_b2000_c100_s40_o0__ddm1000 $WORK/recheck/mice-r14-test`（该任务的生产输出产生于 NW=3），
  比较两者逐字节一致性；结果出来后记录。
- recheck（5 worker 负载下）mice-r14-test:t_b2000_c100_s40_o0__ddm1000：**QUALIFIED (bit-identical)**，与其 NW=3 下的生产输出逐字节一致。
  追加的 19 个 worker 会话全部存活。

## 2026-10-21 00:21 AEDT（21:21 CST）每卡 6 个 worker（用户指示）

- 21:10–21:20 CST NW=5 下 GPU 利用率 79–97%（均值约 90%），显存 5.7–17 GB / 80 GB（当前为 mice-r14-exist，任务比 r14-test 重）。
- 用户："那应该6个workder"。8 个作业各追加 w6（同样 `srun --overlap` 前台、tmux），抽查每卡 6 个 GPU 进程；追加会话共 27 个。
  仍是 OMP_NUM_THREADS=1 的组、每卡 7 核。请协调者在补登记中写为 NW=6。

## 2026-10-21 00:40 AEDT（21:40 CST）用户：自己就是协调者；P2 开始；drtabpfn 暂缓

- 用户："好，先跑drtabpfn和P2 不用等协调者了，我就是协调者"；随后："drtabpfn 暂时不用了吧，等跑完吧"。
  因此 drtabpfn 等 P1 生产跑完再提交（cluster/dr.sbatch 已写好：1×A800、7 天、NW=6、`--sets drtabpfn`，未提交）。
  账号 8 卡上限已被 P1 的 8 个作业占满，drtabpfn 本来也要等卡。
- P2 输入：`unpack_inputs.sh p2`：bundle_p2 SHA256SUMS OK；ext-baselines-p2.tar → $WORK/home/ext-baselines，files.sha256 OK。
  环境 stream、tsbase 已于 20 日建好并与 env_lock 一致。
- P2 CPU 节点型号：AMD EPYC 9654（partition amd，192 核、772 GB/节点），全部 P2 任务都用该型号；首个作业里用 lscpu 记录实际型号。
- P2 探针：3049609（probe_p2.sbatch，amd，14 核，7 个 qualify 并行，`--tasks tasks_p2.jsonl`，输出 $WORK/qualify_p2/1..7），排队中。
  任务清单 tasks_p2.jsonl：2358 个 CPU 任务，估计 132 CPU 小时（ts_dev 720 个 64 h，mice-table1-trained-probs 736 个 37 h）。
- 21:40–21:45 CST P2 探针 3049609（cpua228，lscpu：AMD EPYC 9654 96-Core Processor）：7 个全部 **QUALIFIED (bit-identical)**：
  results_river:elec2__hat、results_trained_dev:elec2__mooe_lin_50_0.1_0.01、mice-main-trained-grid20:grid_c5_b500_s20__nse、
  mice-table1-trained-probs:h2_phishing__levbag、mice-confirm-cp-20261017-cpu:cc_btc_2013__arf、ts_dev:elec2__adaptz_L1_lr0.001_s1_m0.001、
  results_heldout34_trained:h3_poker_b__mooe_rff2000_100_2_0.01。另核对 7 个探针输出均符合 tasks_p2.jsonl 的 schema（P1 的 cuts/closes 问题不出现在 P2）。
- 21:47 CST P2 生产：8 个作业 3049649–3049656（amd，各 48 核、24 个 worker、每 worker 2 核，共 384 核；`--gpu cpu --tasks tasks_p2.jsonl`），
  节点 cpua258、cpua016、cpua037、cpua279、cpua068，全部立即开始。核数合计 384 + P1 56 = 440 ≤ 500。

## 2026-10-20 22:17 CST（2026-10-21 01:17 AEDT）进度

- P1（8×A800，每卡 6 worker）与 P2（384 核）均无 GAVE UP、无报错。`rerun.py status`（只列有进展的组）：
```
P1
results_grid_test                  done=0 claimed=6 gaveup=4 left=50
mice-r14-test                      done=357 claimed=3 gaveup=0 left=0
mice-r14-exist                     done=86 claimed=36 gaveup=0 left=0
mice-r14b-acc                      done=73 claimed=12 gaveup=0 left=191
P2
results_river                      done=51 claimed=0 gaveup=0 left=0
results_heldout                    done=12 claimed=0 gaveup=0 left=0
results_trained_dev                done=435 claimed=0 gaveup=0 left=0
results_trained                    done=125 claimed=1 gaveup=0 left=0
results_heldout2                   done=48 claimed=0 gaveup=0 left=0
results_heldout34_trained          done=112 claimed=0 gaveup=0 left=0
mice-main-trained-grid20           done=96 claimed=0 gaveup=0 left=0
mice-table1-trained-probs          done=730 claimed=6 gaveup=0 left=0
mice-confirm-cp-20261017-cpu       done=22 claimed=0 gaveup=0 left=0
ts_dev                             done=320 claimed=185 gaveup=0 left=215
```
- results_grid_test 的 6 claimed / 4 gaveup 是 20:04–20:08 两次取消留下的（见上），等处置。mice-r14-test 的 3 claimed 是 20:44 被回收的 worker 留下的。

## 2026-10-21 01:29 AEDT 用户（协调者）决定：6 项全部按执行者推荐

用户原话："全部按推荐"。执行者的推荐（同一条消息中逐项列出）：
1. **P2b**：ts_dev 720 done、0 gaveup 后，由执行者在集群上按 REGISTRATION_STAGE2_20261020 的流程执行
   （select_frozen.py → 提交 frozen_cluster/frozen_<m>.json → make_tasks_stage2.py ext → 提交并运行 → --final 重选并提交 →
   make_tasks_stage2.py test → 提交并运行）。与登记的唯一差别：选择在集群上读同一批开发输出，而不是返回 Windows 的 ~/h800 后再读。
   任何 GAVE UP 都停止该方法并等用户。
2. **run.py 的 cuts / closes**：e62ebce 只把 _merge_or_add 包进 _close 以记录每个存储上下文的行来源（注释："no effect on
   predictions"），并多写 closes 数组和 .closes.pkl。决定：rerun.py valid() 把 cuts、closes 与 wt、te、peak_mem 一样排除在结构
   比较之外；results_* 各组恢复运行；4 个 GAVE UP 任务（results_grid_test）重置尝试记录（旧记录移入 _rerun/reset_20261021/，不删除）。
3. **TabICL**（[3] 只有 ll 有约 1e-7 相对差，acc/预测逐位一致）：照常运行 4 个 TabICL 组，论文如实写明“预测逐位一致，概率有浮点级差异”。
4. **dtmoe 改 CPU**：执行者生成 CPU 任务清单（去掉 TS_DEVICE、TS_DETERMINISTIC、CUBLAS_WORKSPACE_CONFIG，tsbase 环境，新输出目录，
   AMD 9654 节点），先 qualify 三个 m2 探针 id，全部逐位一致后再跑 60 个开发任务；随后按第 1 项流程做 dtmoe 的阶段 2。
5. **确认既成事实**：每卡 6 worker（OMP=1 组）；不用 MPS（6 worker 下 GPU 约 95%）；P3 权重由集群经 hf-mirror 下载并按 sha256 核对。
6. **P1 子集结束后**：release 被打断的 claim 并重跑；随后 drtabpfn（dr.sbatch）和 P3。

## 2026-10-21 01:33 AEDT 执行用户决定（第 2、4 项）

- **第 2 项**：rerun.py valid() 在 schema 不含 cuts / closes 时不比较这两个键（commit 83960cd；集群上 sha256 1e6fa9f6…，与 git 一致）。
  用全部探针输出复核：P1 的 7 个 qualify 输出全部 schema-valid（其中 [5][6] 的 schema 本来含 cuts，仍逐键比较）；
  先前被判失败的 results_grid_test:grid_c100_b2000_s10__ddm1000 现有输出 complete() = True。正在运行的 worker 仍用旧代码（它们不跑 results_*）。
- results_grid_test 的 10 个任务（4 GAVE UP、6 被两次 scancel 打断，尝试数 1–3）的 attempts / gaveup 记录移入 _rerun/reset_20261021/，
  claim 释放；其现有输出在下次尝试前由 rerun.py 自动隔离。原因都是执行者的传参错误和 cuts/closes 误判，不是任务本身。
- **第 4 项**：cluster/make_tasks_dtmoe_cpu.py 由 tasks_dtmoe.jsonl 生成 tasks_dtmoe_cpu.jsonl（60 个；set dtmoe_cpu_dev；gpu cpu；
  {PYTOT}→{PYTS}；去掉 TS_DEVICE/TS_DETERMINISTIC/CUBLAS_WORKSPACE_CONFIG；CUDA_VISIBLE_DEVICES=""；输出 mice-table1-newbase/dtmoe_cpu/dev/P），
  commit a404635。探针 3050085（probe_dtmoe_cpu.sbatch，amd，6 核）：三个 m2 id 各 qualify 一次，已开始。
- P2 ts_dev 695/720（25 在跑，0 GAVE UP）；P2b 在 720 done 后开始。prod_p2.sbatch 增加 TASKS 变量（默认 tasks_p2.jsonl），供 P2b 和 dtmoe CPU 清单使用。

## 2026-10-21 01:43 AEDT P1 GAVE UP：mice-r14-exist:h4_covertype_d__micecp1000_500（等用户处置）

- 3 次尝试都在 gpu8011（slot 3048895_g0_w2），21:12:55–22:40:37 CST，rc 均为 0，墙钟 1815 / 1764 / 1643 s；三次都写出 .npz、.pkl、.closes.pkl。
- 判失败的原因：npz 的 `cuts` 为 (164, 2)，tasks.jsonl 的 schema（取自原始输出）为 (163, 2)；其余键（acc、ll、B、concept、calls、
  n_experts、closes (209,4)）与 schema 一致，.pkl 与 .closes.pkl（list 209）也一致。三次尝试的结构相同（运行是确定的）。
- 含义：在 A800 上重算时，这条流的 micecp 比原始运行多一个切点（cuts 行数取决于计算结果）。这是重算与原始输出之间的一处真实差异，
  不是运行器或节点故障。按 HANDOFF，执行者不手动重试、不改判定。三次输出在 _rerun/quarantine/mice-r14-exist__h4_covertype_d__micecp1000_500/{0,1,2}。
- **请用户（协调者）决定：** 执行者建议 valid() 对 cuts / closes 只比较列数和 dtype（行数取决于数据，类似数值），把行数与原始不同的任务
  单独列表报告；改后对此任务登记一次尝试重置。其他已完成的 r14 任务行数都与原始一致（否则也会失败）。
- 22:44:02 CST 第二个 GAVE UP：mice-r14-exist:h3_covertype_c__micecp1000_500，原因相同：三次 rc 0，cuts (181,2) 对 schema (180,2)，
  closes (212,4) 对 (211,4)，其余键一致，三次结构相同。并入上一条，等用户决定。

## 2026-10-20 22:44–22:50 CST（2026-10-21 01:44–01:50 AEDT）P2 完成；P2b 选择与扩展清单

- P2 全部完成：`rerun.py status --tasks tasks_p2.jsonl` 10 组共 2358 done、0 gaveup（ts_dev 720/720，22:44:45）。
- 重复开发对（REGISTRATION_P2 "Duplicate development pairs"）：results_trained 与 results_trained_dev 中同命令的 15 对输出，除 wt 外逐数组一致：15/15。
- P2b 第 1 步（用户第 1 项决定）：在集群上 `select_frozen.py $RUNS/mice-table1-newbase/dev_cluster/P <m> MICE/results_paper/table1_fill/frozen_cluster`，
  4 个方法各 36/36 个配置可选。最优配置及所需扩展：fsnet L32 lr1e-3 s5 m0.9 → steps 25；onenet L32 lr1e-3 s5 m0.75 → steps 25；
  adaptz L1 lr1e-4 s5 m0.01 → lr 1e-5、steps 25；shifts L16 lr1e-3 s5 m0.5 → steps 25。选择文件 commit 4ef2307（扩展任务存在之前）。
- `make_tasks_stage2.py ext <m>`：fsnet 90、onenet 90、adaptz 180、shifts 90（各 manifest 的 expected = tasks），共 450 个，输出到 dev_cluster/P。
- 22:48:58 CST 第三个同类 GAVE UP：mice-r14-exist:elec2__archcp1000_500（gpu8017，三次 rc 0，约 1823 s/次）：cuts (43,2) 对 schema (44,2)，
  closes (90,4) 与 schema 一致，.pkl / .closes.pkl 一致，三次结构相同。即重算比原始少一个切点。至此 3 个 r14-exist 任务属这一类，等用户决定。
  注：每个这类任务会用满 3 次尝试（约 3×30 min GPU）才被放弃；用户决定前执行者不改判定。
- 01:46 AEDT P2b 扩展 9 个作业（3050172–3050180：adaptz 3、fsnet 2、onenet 2、shifts 2，各 48 核/24 worker）开始运行。
- 22:50:17 CST 第四个同类 GAVE UP：mice-r14-exist:elec2__micecp1000_500：cuts (43,2) 对 (44,2)，其余一致。
- 22:51 CST dtmoe CPU 探针：[10] elec2 L32 **QUALIFIED**、[9] elec2 L16 **QUALIFIED**（bit-identical）；[11] insects 仍在运行。
- P2b shifts：扩展 90/90 done、0 gaveup。`select_frozen.py … shifts … --final`：54/54 个配置可选，最终配置不变
  L16 lr1e-3 s5 m0.5（扩展的 steps 25 没有更好）。frozen_shifts_final.json 在任何 shifts 测试任务之前提交。

## 2026-10-21 02:04 AEDT 进度与估计

- GPU（22:58 CST，最近 15 分钟）：8 卡利用率 95–99%，显存 5–8 GB / 80 GB。
- 22:58 CST 登录节点 logini04 上的 tmux 服务已不在（会话全部消失，原因不明）；但 27 个追加 worker 的 Slurm 作业步骤仍在运行
  （squeue -s 可见，抽查 3048892/3/4 的 18 个 worker 全在）。此后用作业步骤数而不是 tmux 会话数检查它们。
- P1 子集：690/1646 done（r14-test 357+3 待重跑、r14-exist 101 done + 4 个 cuts 行数类 GAVE UP、r14b-acc 232/276）。
  按最近 60–120 分钟的完成量（26–37 个估计秒/秒），子集剩余约 142 估计小时，约 4–5.5 小时；之后 results_*（约 82 估计小时）、drtabpfn、P3。
- P2b：shifts 已冻结、测试 2 个作业运行中；fsnet、onenet、adaptz 扩展约 250/450。dtmoe CPU 探针 2/3 QUALIFIED。
- 22:54–22:55 CST shifts 测试（3050236/7，各约 50 s）：stage2_test_shifts 92/92 done、0 gaveup（shifts 很快，例：agrawal_s10 4 s），
  输出 mice-table1-newbase/test_cluster/P。**shifts 的 P2b 完成**（选择 → 扩展 90 → --final → 测试 92）。

## 2026-10-21 02:28 AEDT 预先提交 GPU 后续作业（防 VPN 断开时卡空闲）

- 用户担心夜间 VPN 断开。Slurm 作业不依赖 VPN；但执行者断线时无法提交后续作业。因此按已批准的计划（决定第 2、3、6 项）预先提交：
  - results_* 全部 17 组（含 TabICL 4 组；不含 results_delay_dev），每卡 NW=3（OMP_NUM_THREADS=4），8 个单卡作业，
    各自 `--dependency=afterany` 于一个 P1 作业：3048892→3050502、3048893→3050503、3048894→3050504、3048895→3050505、
    3049189→3050506、3048896→3050507、3048897→3050508、3048898→3050509；`--exclude-sets` 为其余 20 组。新作业使用已打补丁的 rerun.py。
  - drtabpfn：dr.sbatch（NW=6，7 天）作业 3050510，afterany 于 3050502。
- 已知副作用：P1 作业的批处理脚本只等待 w1–w3；作业结束时，用 srun --overlap 追加的 w4–w6 若仍在跑最后一个任务会被一起结束
  （每卡最多 3 个；记 1 次尝试，claim 保留）。待所有 worker 都停时用 `rerun.py release` 释放后重跑（连同 mice-r14-test 的 3 个）。
- P2b（选择/冻结需先 git 提交）与 dtmoe CPU 网格（需 [11] 的探针结论）仍需执行者在线处理。
- 23:32 CST 同类 GAVE UP 第 5、6 个：mice-r14-confirm:c_bvar_c100_s52_o2__micecp1000_500 与 …_o0__micecp1000_500（三次 rc 0）：
  这次是 closes (27,4) 对 schema (28,4)，.closes.pkl 长度相应少 1；cuts 与 .pkl 一致。共 6 个任务（全是 micecp / archcp 的
  cuts/closes 行数差一行），等用户决定。
- 注：监控里 results_grid_test 的 4 条 GAVE UP 是 20:07 的旧日志行，那 4 个任务已按用户第 2 项决定重置（见上文“执行用户决定”一节）。
- P2b adaptz：扩展 180/180 done、0 gaveup。`--final`：72/72 个配置可选，最终配置 L1 lr1e-4 **s25** m0.001（来自扩展；
  按登记即使在边界上也冻结）。frozen_adaptz_final.json 在任何 adaptz 测试任务之前提交。

## 2026-10-21 03:01 AEDT mice-r14-dev 被旧代码 worker 判失败（cuts/closes，已批准的第 2 项同类）

- 23:58–23:59 CST 起 mice-r14-dev 的 ddm1000 任务接连 GAVE UP（每次约 50 s，三次 rc 0，acc 三次相同）。原因：mice-r14-dev 的 schema 不含
  cuts/closes，输出含 closes（部分也含 cuts）；当前 8 个 P1 作业的 worker 在 rerun.py 打补丁（83960cd）之前启动，内存中仍是旧的 valid()。
  用补丁后的 rerun.py 检查已放弃任务的隔离输出：9/9 有效（多出的键只有 cuts/closes）。schema 不含 cuts 的还有 mice-r13-acc、mice_seg_origin_r12、
  mice-tkde-control-20261009（后者用自己的代码快照，探针输出有效）。
- 执行者想取消 8 个 P1 作业和预先提交的 results_*/drtabpfn 链，换成新代码的作业（P1 子集每卡直接起 6 个 worker），
  但该操作被 Claude Code 的自动权限检查拒绝。按规则不绕过，等用户决定。作业保持原样。
- 后果：旧 worker 会把 mice-r14-dev（144）、mice-r14-devtrim（20）以及可能的同类组每个任务跑 3 次后放弃（估计浪费约 30 卡时）；
  输出本身有效，结果不丢。P1 作业结束后需要：重置这些任务的尝试记录（同 results_grid_test 的做法），并用新代码的 worker 补跑。
  注意：不能用 `rerun.py release`（它会释放所有任务清单的 claim，包括 P2b 正在运行的 CPU 任务），只释放 P1 任务的 claim。

## 2026-10-21 03:34 AEDT 进度；cuts/closes 行数差一行的任务增至 9 个

- 00:34 CST 新增同类 GAVE UP（三次 rc 0、三次结构相同）：mice-r14-exist 的 insects_incremental_abrupt_balanced__micecp1000_500 与 __archcp1000_500
  （cuts 16 对 17）、h2_rialto__archcp1000_500（cuts 65 对 66）。至此：r14-exist 7 个、r14-confirm 2 个，共 9 个，都是 micecp/archcp，
  cuts 或 closes 与原始差一行，其余结构一致。等用户决定。
- P1：r14b-acc 276、table1-cp-gen 30、main-cp-grid10 13、table1-probs-gen 60 完成；confirm-cp-20261017 62/66；r14-exist 104 done、11 在跑；
  mice-r14-dev 2 done、83 GAVE UP（旧代码 worker，见上一节）、33 在跑、26 待跑。
- P2b：fsnet 扩展 87/90，onenet 42/90，adaptz 测试 81/92；dtmoe CPU 探针 [11]（insects）自 22:32 CST 运行中。
- P2b fsnet：扩展 90/90 done、0 gaveup。`--final`：54/54，最终配置不变 L32 lr1e-3 s5 m0.9（steps 25 没有更好）。在 fsnet 测试任务之前提交。
  另：cp1000（cuts/closes 行数）类 GAVE UP 增至 10 个。
- 04:05 AEDT 全部 P1 GAVE UP 按原因分类（用补丁后的 valid() 检查各任务最后一次隔离输出）：
  - 103 个 mice-r14-dev：补丁后有效（旧代码 worker 误判，cuts/closes 不在 schema 中）。
  - 15 个行数类（全是 micecp1000_500 / archcp1000_500）：mice-r14-exist 11（8 个只 cuts 差一行；h3_covertype_c、h2_poker 的 micecp 与 archcp
    三项 cuts/closes/.closes.pkl 都差）、mice-r14-confirm 2（closes 与 .closes.pkl）、mice-r14-devtrim 2（d_b500_o250_c100_s0 的 micecp/archcp，closes 与 .closes.pkl）。
  没有其他原因的 GAVE UP。
- 04:15 AEDT fsnet 测试 stage2_test_fsnet 92/92 done、0 gaveup：**fsnet 的 P2b 完成**。
- 04:30 AEDT adaptz 测试 stage2_test_adaptz 92/92 done、0 gaveup：**adaptz 的 P2b 完成**。剩 onenet（扩展中）。

## 2026-10-21 05:05 AEDT（02:05 CST）进度

```
mice-r14-exist                     done=104 claimed=4 gaveup=14 left=0
mice-r14b-acc                      done=276 claimed=0 gaveup=0 left=0
mice-r14-confirm                   done=214 claimed=0 gaveup=2 left=0
mice-table1-cp-gen                 done=30 claimed=0 gaveup=0 left=0
mice-main-cp-grid10                done=13 claimed=0 gaveup=0 left=0
mice-confirm-cp-20261017           done=66 claimed=0 gaveup=0 left=0
mice-table1-probs-gen              done=60 claimed=0 gaveup=0 left=0
mice-r14-dev                       done=40 claimed=0 gaveup=104 left=0
mice-r14-devtrim                   done=18 claimed=0 gaveup=2 left=0
mice-tkde-control-20261009         done=157 claimed=44 gaveup=0 left=22
stage2_ext_onenet                  done=83 claimed=7 gaveup=0 left=0
```
- r14-exist GAVE UP 增至 14（新增 3 个待分类，预计同属行数类）；mice-r14-dev 104 GAVE UP（旧代码误判，40 个不写 cuts/closes 的方法正常 done）。
- 接下来 P1 子集还剩 tkde-control 66、mice-r13-acc 100、mice_seg_origin_r12 16；GPU 利用率抽查 76–86%（tkde-control 阶段）。
- P2b：shifts、fsnet、adaptz 完成；onenet 扩展 83/90。dtmoe CPU 探针 [11] 仍在运行（自 22:32 CST）。

## 2026-10-21 05:32 AEDT 新类型 GAVE UP：tkde-control 显存上限漏登记（等用户决定）

- 02:29:13 CST mice-tkde-control-20261009:fifoM_h2_spam GAVE UP（gpu8017，三次 rc 1，约 1 min/次）：
  `TabPFNCUDAOutOfMemoryError … 1,400 train / 100 test samples, 499 features … 1.75 GiB allowed`（卡上 70.7 GiB 空闲）。
- 原因：tkde-control 的 controller/worker.py:116 用 `torch.cuda.set_per_process_memory_fraction(MICE_ALLOC_MIB …)`，默认 1792 MiB；
  原始运行由 controller/supervisor.py:97 设 `MICE_ALLOC_MIB='4096'`。tasks.jsonl 中该组任务的 env 没有 MICE_ALLOC_MIB
  （rerun.py 的白名单也不传它），所以重算用的是 1792 MiB 上限。这是任务登记时漏掉的原始运行参数，不是节点故障。
- **请用户决定：** (a) 给 mice-tkde-control-20261009 的任务 env 加 MICE_ALLOC_MIB=4096（与原始一致），重置该任务的尝试后重跑；
  (b) 已在 1792 MiB 下完成的该组任务（02:05 CST 时 157 个）是否重跑——若 TabPFN 的分批与可用显存有关，数值可能与原始设置不同；
  执行者未核实 TabPFN 是否如此。执行者不改任务；同组后续大特征数任务可能同样 OOM。
- 05:41 AEDT mice-r13-acc 自 02:37 CST 起 GAVE UP（k2_18–k2_22 等，三次 rc 0，约 1 min/次）：用补丁后的 valid() 检查隔离输出均有效，与 mice-r14-dev 同属旧代码 worker 误判（schema 不含 cuts/closes）。预计 mice_seg_origin_r12 同样。P1 结束后与 r14-dev 一并重置、用新代码补跑。
- P2b onenet：扩展 90/90 done、0 gaveup。`--final`：54/54，最终配置不变 L32 lr1e-3 s5 m0.75。在 onenet 测试任务之前提交。

## 2026-10-21 06:37 AEDT P1 子集收尾；results_* 开始

- 03:32:45 CST 3048898（gpu8012）的批处理 worker 用完任务后作业结束，追加的 srun 步骤 3048898.3/.4/.5/.7 随之 CANCELLED（预期的副作用）。
  依赖作业 3050509（results_*，NW=3，新代码）03:32:46 开始：results_grid_test 前几个任务（含已重置的 s10 ddm/fifo/oracle/winens、s11 ddm）
  全部 ok，cuts/closes 补丁生效。
- 03:37 CST P1 子集：r14-test 357（3 claimed 待释放）、r14-exist 104 done / 17 GAVE UP（行数类，待复核新增 3 个）、r14b-acc 276、r14-confirm 214+2、
  table1-cp-gen 30、main-cp-grid10 13、confirm-cp 66、table1-probs-gen 60、r14-dev 40 done / 104 旧代码误判、devtrim 18+2、
  tkde-control 219 done / 3 在跑 / 1 OOM、r13-acc 0 done / 79 误判 / 21 在跑、seg_origin 0 done / 8 误判 / 8 在跑。
- P2b：onenet 测试运行中；shifts、fsnet、adaptz 完成。
- 07:17 AEDT onenet 测试 stage2_test_onenet 92/92 done、0 gaveup。**P2b 全部完成**：4 个方法的最终配置（frozen_cluster/frozen_<m>_final.json）
  shifts L16 lr1e-3 s5 m0.5、fsnet L32 lr1e-3 s5 m0.9、onenet L32 lr1e-3 s5 m0.75、adaptz L1 lr1e-4 s25 m0.001；各 92 条测试流输出在
  mice-table1-newbase/test_cluster/P。每一步的选择文件、任务清单都在运行前提交（4ef2307、5c3f553、4d7766d、841781f、f490b27、06d426c、b49c81d、63620b0、c4c766f、99641db）。

## 2026-10-21 07:27 AEDT dtmoe CPU 探针全部 QUALIFIED；开发网格开始

- 3050085（AMD 9654）：[10] elec2 L32 lr1e-4 s1 m2、[9] elec2 L16 lr1e-4 s1 m2（22:51 CST）、[11] insects_abrupt_balanced L32 lr1e-3 s5 m2
  （04:24:47 CST，两次共约 5.9 h）均 **QUALIFIED (bit-identical)**。按用户第 4 项决定运行 tasks_dtmoe_cpu.jsonl（60 个，输出 dtmoe_cpu/dev/P）：
  3 个 prod_p2 作业（TASKS=tasks_dtmoe_cpu.jsonl，各 48 核、24 worker、每 worker 2 核）。

## 2026-10-21 07:48 AEDT P1 旧代码作业全部结束；误判任务重置；补跑作业排队

- 8 个 P1 作业（3048892–8、3049189）已全部结束，8 张卡都在跑 results_*（3050502–9，新代码）。此时没有任何旧代码 worker。
- 重置（与 results_grid_test 同法，记录移入 _rerun/reset_20261021b/）：逐个用补丁后的 valid() 检查最后一次隔离输出，**仅对有效者**重置：
  mice-r14-dev 104、mice-r13-acc 91、mice_seg_origin_r12 15（共 210，均为旧代码 worker 的 cuts/closes 误判）。
  未重置（其他原因，等用户）：mice-r14-exist 18、mice-r14-confirm 2、mice-r14-devtrim 2（行数类）、mice-tkde-control 1（显存上限）。
- 释放 P1 子集中被作业结束打断的 claim（只限 mice-* 组，不用 `rerun.py release`）：mice-r13-acc 9、mice-r14-test 3、mice_seg_origin_r12 1。
- 待跑：mice-r14-test 3、mice-r14-dev 104、mice-r13-acc 100、mice_seg_origin_r12 16。补跑作业 3053914–3053920（NW=6，新代码），
  各 afterany 于 results_* 作业 3050503–3050509；drtabpfn 3050510 afterany 于 3050502。

### 2026-10-21 09:55 AEDT (06:52 CST) progress
VPN back at 09:51 AEDT; all jobs kept running. results_* (3050502-509, running 2:09-3:19): 445 done, 24 claimed, 427 left, 0 gave up. dtmoe_cpu_dev (3053868-870): 42/60 done, 18 claimed, 0 gave up. Pending: drtabpfn 3050510, P1 rest 3053914-920 (afterany on results_*).

### 2026-10-21 10:15 AEDT P3 inputs and smoke job
P3 weights copied from $WORK/p3_download/{tabpfn,tabdpt} to $W3=$WORK/home/mice-p3-weights (layout as run_backbone.py
expects); sha256 -c OK for tabpfn-v3.5-20260909.safetensors, tabdpt1_3.safetensors, config.json. ext-baselines-p3
(LimiX, CURE) not unpacked: unused after AMENDMENT_20261020d. Smoke job 3054183 (cluster/p3_smoke.sbatch, p3_smoke,
--gpu exclusive, tasks_p3b.jsonl) submitted; pending on the 8-GPU QOS limit. GPU use, mean of the last 30 samples per
results_* job: util 37-78%, memory 2.3-5.1 GB of 80 GB. Cluster cannot reach github.com:22; scripts are copied by scp.

### 2026-10-21 11:50 AEDT (08:46 CST) progress
results_* jobs 3050503, 3050507, 3050509 COMPLETED (exit 0, 4:04-5:10); P1 rest 3053914, 3053918, 3053920 started on
gpu8001. results_*: all done except 6 claimed (heldout_tabicl 1, heldout4_seed1 1, probs 4) and results_delay_dev 5
left. P1 rest: mice-r14-dev 50 done, 18 claimed, 76 left; r13-acc, seg_origin, oracle and the benchmarks not started.
dtmoe_cpu_dev 54/60 done, 6 claimed. Gave up: 23, unchanged (the 22 rows-class tasks and tkde fifoM_h2_spam, awaiting
the user). Smoke 3054183 and drtabpfn 3050510 pending.

### 2026-10-21 12:00 AEDT reset_20261021c (stale pre-patch attempts)
Three mice-r13-acc tasks (k2_0, k2_2, k2_5) GAVE UP at once when P1 rest started: their 3 attempts were all from the
old-code P1 workers on gpu8012 before the valid() patch (rc 0 not accepted, then the third interrupted when the job
ended); reset_20261021b had missed tasks that were in flight at that time. Same class, same handling as reset_20261021b
(user decision items 2 and 6): attempts records of the 10 unfinished tasks whose attempts all predate reset_20261021b
moved to _rerun/reset_20261021c/ (r13-acc k2_0 k2_2 k2_5 k4_4 k4_7 k4_9 k4_11 k4_17 k4_46, seg_origin_r12 11; and the 3
gaveup records). None was claimed. Gave up is back to 23 (the 22 rows-class tasks and tkde fifoM_h2_spam).

### 2026-10-21 12:25 AEDT (09:25 CST) progress
All results_* jobs COMPLETED (3050504 last, 4:47). P1 rest 3053915 and 3053916 COMPLETED (no task left for them);
mice-r14-dev all done; mice-r13-acc 88 done, 12 claimed (the 10 of reset_20261021c rerunning). Left in P1: the untimed
results_delay_dev (5) and mice_oracle_r11:all (1), submitted as their own job 3054319 (cluster/untimed.sbatch, 7-day
limit, --sets, NW 3); the 5 benchmarks will run last, one exclusive job each (cluster/bench.sbatch). P3 smoke 3054183
running on gpu8015; drtabpfn 3050510 running (6 claimed, 0 done after 31 min).

### 2026-10-21 12:35 AEDT P3 smoke test and exclusion rule
Job 3054183 (gpu8015, alone, --gpu exclusive, 1:58): 6/6 ok, $RUNS/mice-p3-smoke/*.json. Registered rule
(REGISTRATION_P3_P4_20261020, smoke test and exclusions): excluded if an error is recorded, or if on either segment the
median time per call (calls 2-20) is more than 20 times TabPFN v2's.

| backbone | segment | error | median s/call | TabPFN v2 | ratio | peak GB |
|---|---|---|---|---|---|---|
| tabpfn_v3.5 | h3_covertype_b | none | 1.5845 | 0.2307 | 6.87 | 1.64 |
| tabpfn_v3.5 | h3_poker_b | none | 1.5458 | 0.1834 | 8.43 | 1.64 |
| tabdpt | h3_covertype_b | none | 0.1092 | 0.2307 | 0.47 | 0.47 |
| tabdpt | h3_poker_b | none | 0.1080 | 0.1834 | 0.59 | 0.47 |

Neither backbone is excluded. Next: the determinism probe of each, then production.

### 2026-10-21 12:50 AEDT (09:50 CST) P1 shared sets finished; benchmarks; P3 probe
P1 rest jobs 3053914-920 all COMPLETED (32-53 min, exit 0). mice-r13-acc 97/100: k2_0, k2_2, k2_5 kept their claim
directories from the 08:53 GAVE UP (reset_20261021c moved only attempts and gaveup), so no worker took them: the 3
empty claim directories removed (as rerun.py release does, for these 3 only) and job 3054353 (untimed.sbatch,
SETS=mice-r13-acc, NW 3, 24 h) submitted. Benchmarks (last P1 sets; one exclusive worker per job, one attempt):
3054354 tkde-bench, 3054355 + 3054357 r13-bench (a1, a2), 3054356 + 3054358 r14b-bench (a1, a2). Untimed job 3054319:
results_delay_dev 3 claimed. drtabpfn: 2 done, 6 claimed after 54 min. P3 probe 3054337: tabdpt QUALIFIED
(bit-identical, 4:45); tabpfn35 still running.

### 2026-10-21 12:55 AEDT benchmark a2 GAVE UP (executor's scheduling error)
mice-r13-bench-h800:a2 (job 3054357) and mice-r14b-bench-h800:a2 (job 3054358) GAVE UP after 10 s, rc 1:
FileNotFoundError on $RUNS/mice-r1{3,4b}-bench-h800/kstar.json, which stage a1 of the same benchmark writes. The
executor gave a2 its own job so that each task had one job; a2 depends on a1 and must run after it (file order, one
worker). Nothing was computed (attempt 0.3 s, no output). Benchmarks get one attempt, so the two tasks stay GAVE UP
until the user decides. Proposed: when a1 is done, move the two a2 attempts/gaveup records and claim directories to
_rerun/reset_20261021d/ and run a2 in a new exclusive job, alone on its GPU. a1 jobs 3054355 and 3054356 continue.

### 2026-10-21 13:05 AEDT dtmoe (cluster CPU) grid done; stage 2 step 1 and extension
dtmoe_cpu_dev 60/60 done, 0 gave up (jobs 3053868-870 COMPLETED, 4:53-5:26). `select_frozen.py
$RUNS/mice-table1-newbase/dtmoe_cpu/dev/P dtmoe frozen_cluster` (12/12 eligible): best L32 lr1e-4 s5 m2 -> extension
lr 1e-5, steps 25. frozen_dtmoe.json (sha256 2e91658e...) committed f6173a8 before any extension task.
`make_tasks_stage2.py ext dtmoe` 60/60 (manifest expected = tasks), CPU copy by cluster/make_tasks_dtmoe_cpu.py
(set stage2_ext_dtmoe_cpu, outputs to dtmoe_cpu/dev/P), committed 053ebc5. Jobs 3054397-399 (prod_p2.sbatch,
TASKS=tasks_stage2_dtmoe_ext_cpu.jsonl, 48 cores, 24 workers each, 3-day limit since steps 25 runs longer).

### 2026-10-21 13:32 AEDT P3 probe and production
Probe 3054337 (gpu8001): tabdpt QUALIFIED (bit-identical, 09:29:45-09:34:30 CST), tabpfn35 QUALIFIED (bit-identical,
09:29:45-10:29:37 CST). No backbone paused. Production: 3 jobs of cluster/prod_p3.sbatch (1 A800 each, NW 3,
--tasks tasks_p3b.jsonl, --exclude-sets p3_smoke) on the GPUs left free by drtabpfn, the untimed job and the 3
benchmarks. mice-r13-acc 100/100 and mice_seg_origin_r12 16/16 done (3054353 COMPLETED, 21:41).

### 2026-10-21 14:50 AEDT (11:50 CST) progress
Untimed job 3054319 COMPLETED (2:23:36): results_delay_dev 5/5 and mice_oracle_r11 1/1 done. Benchmarks: a1 of tkde,
r13, r14b running (2:05). drtabpfn: 6 done (1268-9064 s each), 6 claimed, 80 left after 3 h on one GPU; a second
drtabpfn job 3055420 (dr.sbatch, NW 6) submitted on the free eighth GPU. P3: results_heldout3_tabpfn35 7 done, 9
claimed; 0 gave up. dtmoe extension: 14/60 done, 46 claimed, 0 gave up.

### 2026-10-21 19:50 AEDT (16:50 CST) after the VPN outage (about 15:50-19:45 AEDT)
Jobs kept running. Benchmark jobs 3054354-356 COMPLETED (4:17, 6:25, 5:51). mice-r14b-bench-h800:a1 done.
mice-tkde-bench-20261009-h800:bench and mice-r13-bench-h800:a1 GAVE UP with rc 0: the output jsonl has 73 lines
against the schema's 75 (tkde: 72 records, all ok at attempt 0, plus the done line) and 52 against 55 (r13 a1: 51
records ok at attempt 0, plus done). Reading: the records carry an attempt field, so the original runs very probably
logged extra retry records that this run did not need; the line count depends on the run, like the rows-class tasks.
Not retried (benchmarks get one attempt); waiting for the user. r13 a2 needs r13 a1 (kstar.json is absent) and r14b a2
waits for the user's decision on its reset. drtabpfn 25 done, 12 claimed, 55 left: 3 more drtabpfn jobs on the 3 GPUs
the benchmarks freed. P3: tabpfn35 28 done, 9 claimed, 3 left; tabdpt 40 left. dtmoe extension 30/60. Gave up: 27.

### 2026-10-21 20:05 AEDT user decision "全部按推荐" (benchmarks and row counts); two actions blocked
The user answered "全部按推荐" to the executor's message of 19:50 AEDT: (1) cuts / closes of the rows-class tasks and the
benchmark jsonl records compared on format only (columns and dtype; parse and final "done" record), the row / line
differences listed and reported; (2) the two a2 benchmarks reset and rerun after their a1. Found while preparing (2):
the a2 failure has a second cause. The bundle tars put kstar.json one level down, at
$RUNS/<root>/<root>/kstar.json (AMENDMENT_20261020 item 1 expects $RUNS/<root>/kstar.json), so a2 would fail even
after a1. Both actions were refused by the session's permission classifier ("Modify Shared Resources"): the
rerun.py valid() edit and the copy of kstar.json to the benchmark root. Nothing was changed; waiting for the user.
Not covered by the decision (no recommendation was given): tkde MICE_ALLOC_MIB=4096, scancel permission.
GPU, last 5 min: drtabpfn 99% and 4 GB; P3 (tabpfn35, OMP 4 x 3 per GPU) 9-25% and 7 GB.

### 2026-10-21 20:25 AEDT executing the user's decision (user: "允许改 rerun.py 和复制 kstar.json")
- rerun.py valid() (a4ec53e, d7b9354; cluster sha256 4398e984..., same as git): cuts / closes compared on columns and
  dtype; .closes.pkl on its type; a benchmark jsonl is accepted when it ends with its "done" record. Workers already
  running (drtabpfn, P3) keep the old code; they run none of these sets.
- Check of the 24 GAVE UP outputs under the new rule (outputs in place or last quarantined attempt): 24/24 valid.
  Row / line differences, rerun against original:

| task | difference |
|---|---|
| r14-confirm c_bvar_c100_s52_o0 / o2 micecp | closes 27 vs 28 |
| r14-devtrim d_b500_o250_c100_s0 archcp / micecp | closes 7 vs 8 |
| r14-exist covertype archcp / micecp | cuts 81 vs 83, closes 300 vs 301 |
| r14-exist elec2 archcp / micecp | cuts 43 vs 44 |
| r14-exist h2_poker archcp / micecp | cuts 127 vs 128, closes 209 vs 210 |
| r14-exist h2_rialto archcp / micecp | cuts 65 vs 66 |
| r14-exist h3_covertype_b archcp / micecp | cuts 47 vs 48 |
| r14-exist h3_covertype_c archcp / micecp | cuts 181 vs 180, closes 212 vs 211 |
| r14-exist h4_covertype_d archcp / micecp | cuts 164 vs 163 |
| r14-exist h4_poker_e archcp / micecp | cuts 137 vs 138 |
| r14-exist insects_incremental_abrupt_balanced archcp / micecp | cuts 16 vs 17 |
| tkde-bench bench | 73 vs 75 lines (72 runs ok at attempt 0 + done) |
| r13-bench a1 | 52 vs 55 lines (51 runs ok at attempt 0 + done) |

  The benchmark drivers retry a run up to 5 times after an OOM and write one record per attempt (bench_pools.py), so
  the original's extra lines are retry records.
- Reset (reset_20261021d/): attempts and gaveup records of the 22 rows-class tasks, tkde-bench:bench, r13-bench a1 and
  a2, r14b-bench a2; their claims released. The drivers skip a run whose .occ.json exists, so the benchmark run
  directories $RUNS/mice-r13-bench-h800/a1 and $RUNS/mice-tkde-bench-20261009-h800/rep{0,1,2} moved to
  reset_20261021d/bench_dirs/ (task outputs are quarantined by rerun.py itself). kstar.json copied from
  $RUNS/<root>/<root>/ to $RUNS/<root>/ for r13 and r14b (sha256 a3709bf2..., 4c6f22ba..., identical to the bundled copy).
- Jobs: 3059720 rows-class (untimed.sbatch, SETS r14-exist,r14-confirm,r14-devtrim, NW 6); benchmarks, one exclusive
  worker each: 3059721 r13 (a1 then a2, file order), 3059722 r14b (a2), 3059723 tkde. All pending (Priority), with
  drtabpfn 3059665-667. Gave up now: 1 (tkde-control fifoM_h2_spam, MICE_ALLOC_MIB question open).

### 2026-10-21 20:35 AEDT tkde-control memory cap (user: "按推荐")
Decision: only mice-tkde-control-20261009:fifoM_h2_spam (GAVE UP, out of memory under 1792 MiB) reruns, with
MICE_ALLOC_MIB=4096 as the original controller/supervisor.py:97 set it; the set's other tasks stay as run, under the
1792 MiB default of worker.py, which the paper / return notes state. tasks.jsonl unchanged: the task with the added
variable is the one line of tasks_tkde_alloc.jsonl (5b3b80e). Its attempts and gaveup records moved to
_rerun/reset_20261021e/, claim released; job 3059748 (untimed.sbatch, TASKS=tasks_tkde_alloc.jsonl, NW 1). Gave up: 0.

### 2026-10-21 22:10 AEDT (19:10 CST) drtabpfn complete; tkde fifoM_h2_spam still out of memory under 4096 MiB
- drtabpfn 92/92 done, 0 gave up (jobs 3050510, 3055420, 3059665-667 all COMPLETED, exit 0).
- Job 3059748 (MICE_ALLOC_MIB=4096, tasks_tkde_alloc.jsonl): 3 attempts on gpu8003, 19:03-19:07 CST, each rc 1 after
  about 75 s: TabPFNCUDAOutOfMemoryError, "Tried to allocate 1.26 GiB ... this process has 3.30 GiB memory in use.
  4.00 GiB allowed" (2,300 train / 100 test rows, 499 features). So the variable reached the task and the original cap
  is not enough on this run. Why the original run passed under the same cap is not known from the cluster copy
  (controller/supervisor.py sets 4096 for every worker; its event log is not in the bundle). GAVE UP again; waiting
  for the user.
- Rerun jobs running: 3059720 rows-class (r14-exist 107 done, 6 claimed, 9 left; confirm and devtrim 2 left each),
  benchmarks 3059721 (r13 a1), 3059722 (r14b a2), 3059723 (tkde). P3 3 jobs; dtmoe extension 3 jobs.

### 2026-10-21 22:50 AEDT dtmoe test layout (user: "好，就这么加速")
When the extension is done and frozen_dtmoe_final.json is committed, the 92 test tasks run in 4 jobs of prod_p2.sbatch
(48 cores, 24 workers each; 96 workers, 192 cores, under the 500-core limit), so that all start at once. Threads
stay at 1 (registered).

### 2026-10-21 23:00 AEDT tkde fifoM_h2_spam at 8192 MiB (user: "tkde 按推荐，提到 8192 重跑")
tasks_tkde_alloc.jsonl now sets MICE_ALLOC_MIB=8192 (3ae04d6); the 4096 attempts moved to _rerun/reset_20261021f/;
job 3061674 (untimed.sbatch, NW 1). The paper and the return notes state that this one task ran with a cap of 8192 MiB
(original 4096, other tasks of the set 1792). Also checked: on the dtmoe CPU nodes (192 cores) each of our processes
has 1 thread at 100 %; the node load of 103-145 includes other users' jobs.

### 2026-10-21 23:46 AEDT (20:46 CST) progress
mice-tkde-control-20261009 223/223: fifoM_h2_spam done at MICE_ALLOC_MIB=8192 (job 3061674, 5:23). r14b-bench a2 done
(3059722, 2:36): mice-r14b-bench-h800 2/2. Rows-class reruns: r14-exist 116 done + 6 claimed, r14-confirm and
r14-devtrim 2 left each. Running: tkde-bench, r13-bench a1, P3 last job (tabpfn35 2 tasks), dtmoe extension 24.
Gave up: 0. Sent the per-set status and paper-table mapping (MANIFEST.md) to the session mice-6e, without scores.

### 2026-10-22 00:51 AEDT (21:51 CST) progress
Rows-class reruns done (job 3059720, COMPLETED 3:53:00): mice-r14-exist 122/122, mice-r14-confirm 216/216,
mice-r14-devtrim 20/20. Running: tkde-bench (3059723), r13-bench (3059721), P3 last job 3054553
(results_heldout4_tabpfn35_e 11/12), dtmoe extension 3054397-399 (stage2_ext_dtmoe_cpu 36/60). Gave up: 0.

### 2026-10-22 01:25 AEDT (22:25 CST) benchmarks cancelled (user decision)
User decision 2026-10-22: the r13 and tkde benchmarks are not rerun on the cluster ("运行时间和内存不同服务器都不同"); the
cost tables keep the original-machine values. Cancelled job 3059721 (mice-r13-bench-h800, a1 at 4:18) and 3059723
(mice-tkde-bench-20261009-h800, at 3:47); their partial outputs stay in place, not used. mice-r14b-bench-h800 2/2 kept.
Return to the Mac (user decision): result files only (task outputs, _rerun attempts/done/gaveup/logs, env freezes), no
inputs; list $WORK/return_list.txt (26108 files, about 16 GB), checksums $WORK/return_SHA256SUMS. After P3 finishes,
only the CPU dtmoe jobs remain.

### 2026-10-22 09:55 AEDT (06:55 CST) progress
The Mac lost the cluster from about 01:50 to 09:50 AEDT (campus VPN down: logini.tongji.edu.cn did not resolve); the
jobs ran on. P3 complete: results_heldout4_tabpfn35_e 12/12, job 3054553 ended, no GPU job remains. dtmoe extension
stage2_ext_dtmoe_cpu 52/60 (3054397-399, CPU only). Gave up: 0. Return rsync resumed (772 MB of about 16 GB before
the outage).
