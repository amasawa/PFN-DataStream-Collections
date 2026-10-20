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
