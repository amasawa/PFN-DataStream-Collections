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
