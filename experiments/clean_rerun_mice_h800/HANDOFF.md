# Handoff: clean MICE rerun on the Tongji H800 cluster

You are Claude Code on the user's Mac mini, the **executor on the cluster**. The Claude Code session on the user's
Windows machine (the coordinator) wrote this file; it keeps the registration, the audits (MiMo, Codex, Sonnet) and the
analysis. Communication: git (this repository) and the user. Reply to the user in Chinese; code, commits in English.

Read first, in this order: `ACTIVATION_20261019.md` and `AMENDMENT_20261020.md` (they hold where they differ from
PLAN.md or this file; the phases
P2-P6 come with their own registrations later), `bundle/claude_rules/global_CLAUDE.md` (the user's team rules; they apply to you, except
that MiMo and Codex run on the Windows side: ask the coordinator for audits), this file, `PLAN.md` (the registration:
what is rerun and what must stay the same), `MANIFEST.md`, `tasks.jsonl`, `rerun.py`.

## Rules for you
1. You run the registered tasks and nothing else. Never edit a task, a driver or any computation code. If a task
   cannot run as it is (a path, a missing directory, a package), stop, write the exact error into the log, and propose
   the smallest operational fix (paths only); the coordinator registers and audits it before you use it.
2. Write only: `experiments/clean_rerun_mice_h800/cluster/` (your scripts: Slurm jobs, setup), and
   `MICE/logs/CLUSTER_RERUN_LOG.md` (your log). `git pull --rebase` before each commit; commit explicit paths only;
   push after each stage (setup, probe, each finished set, return of results).
3. Never delete or overwrite an output; never look at scores to decide anything; never select among repeated runs.
4. Log in Chinese with times from `date`, about every 10 minutes while jobs run; record every failure and its handling.
5. Costs: the cluster bills by use. Ask the user before requesting more than the 8 H800 or more than 24 h of 8 GPUs.

## Step 0. Access
- SSH from the Mac: `ssh -p 10022 <account>@logini.tongji.edu.cn` (or logina; campus network or VPN). Set up an SSH
  key or a ControlMaster connection so that later commands need no password (ask the user to type it once).
- Record in the log: `sinfo -o "%P %G %D %t %l"` (find the H800 partition and the gres name, e.g. gpu:h800:8), the
  account limits (`sacctmgr show assoc user=$USER format=...` if allowed), the storage (`/ssdfs/datahome/$USER`, 500 G),
  whether the login node reaches pypi / pytorch / huggingface mirrors, and the CUDA driver version (`nvidia-smi` in a
  short GPU job).

## Step 1. Inputs
- The bundle is on the Windows machine's desktop, `C:\Users\zhwu9808\Desktop\mice_h800_bundle\` (SHA256SUMS
  inside). The user copies it to the Mac mini over RDP (for example to `~/mice_h800_bundle/`). On the Mac, check
  `shasum -a 256 -c SHA256SUMS` first, then copy it to the cluster:
  `rsync -az -e "ssh -p 10022" ~/mice_h800_bundle/ <account>@<login>:/ssdfs/datahome/<account>/mice_rerun/bundle/`
  and check `sha256sum -c SHA256SUMS` on the cluster; after untarring, check every `<tar>.files.sha256` (per-file
  hashes of the inputs) in the directory where that tar was extracted. Any mismatch stops the set it belongs to.
- Layout (WORK = /ssdfs/datahome/<account>/mice_rerun; HOME of every job = $WORK/home, because drivers use ~/pfn-runs
  and ~/ext-baselines):
  - `$WORK/repo`: the repository at the registered commit (git clone on the Mac, then rsync; or `git bundle`).
    Put the MICE data at `$WORK/repo/MICE/data` (tar MICE_data.tar).
  - `$WORK/home/pfn-runs/<root>/`: untar every `runs/<root>.tar` (inputs only; outputs are created by the runs).
  - `$WORK/home/ext-baselines/`: untar ext-baselines.tar. Check that its files.sha256 lists
    `Drift-Resilient_TabPFN/tabpfn/model_cache/tabpfn_dist_model_1.cpkt`.
  - `$WORK/home/pfn-venvs/cache/tabpfn`: untar tabpfn_cache.tar into `$WORK/home/pfn-venvs/cache/` (the benchmark
    scripts set this path themselves; AMENDMENT_20261020 item 2). Check that the TabPFN v2 checkpoint is there.
- TabICL checkpoint `tabicl-classifier-v2-20260212.ckpt` (Hugging Face repo jingang/TabICL, used by tabicl 2.2.0) is
  not in the bundle: download it once (on the Mac, or on the login node with HF_ENDPOINT=https://hf-mirror.com) into
  the HF cache that the jobs use (HF_HOME=$WORK/hf), then run with HF_HUB_OFFLINE=1. Record its sha256.

## Step 2. Environments (exact versions: env_lock/)
- `venv` (Python 3.12): `pip install -r env_lock/venv.txt` (torch 2.14.0+cu126: from the PyTorch index or a mirror).
- `drtabpfn` (Python 3.11): `env_lock/drtabpfn.txt`, with the `-e file:///...Drift-Resilient_TabPFN` line replaced by
  `-e $WORK/home/ext-baselines/Drift-Resilient_TabPFN` (torch 2.1.2+cu121).
- `totgpu` (Python 3.11): `env_lock/totgpu.txt` (torch 2.3.1+cu121).
- Check in a GPU job: `torch.cuda.get_arch_list()` contains sm_90 and a small matmul runs. Record `pip freeze` of each
  environment on the cluster into `cluster/env_freeze_*.txt`; any version that differs from env_lock is a stop.
- Job environment: REPO, RUNS=$WORK/home/pfn-runs, PY, PYDR, PYTOT (paths of the three pythons), HOME=$WORK/home,
  TABPFN_MODEL_CACHE_DIR=$WORK/home/pfn-venvs/cache/tabpfn, HF_HOME=$WORK/hf, HF_HUB_OFFLINE=1, TABPFN_DISABLE_TELEMETRY=1.
  rerun.py passes only a whitelist of these (plus SLURM_*, PATH, CUDA_VISIBLE_DEVICES, ...) and each task's
  registered variables to the task, so nothing else from the job leaks in. If a driver needs another variable
  (e.g. a library path), report it: it is added to the whitelist by the coordinator.

Before the probe: `find $WORK/repo/MICE -path "*results_*" \( -name "*.npz" -o -name "*.pkl" \) | wc -l` must be 0
(the clone holds no result file; the run.py-family tasks write their outputs there, as the original commands did).

## Step 3. Determinism probe (PLAN.md, checks 1) - before any production job
Always run rerun.py with `$PY` (the MICE venv; written `python rerun.py` below), never with the system python.
Run in one GPU job, sequentially, `$PY rerun.py qualify "<task id>" $WORK/qualify/<n>` for these task ids:
`results_heldout3:h3_airlines_b__micev1000_500`, `results_test:agrawal_s10__fifo1000`,
`results_heldout_tabicl:covertype__ddm1000`, `results_probs:covertype__ddm1000`,
`mice-r14-test:t_b2000_c100_s40_o0__micecp1000_500`, `mice-r14b-acc:c_b2000_c100_s50_o0__snap1000_500.k2`,
`mice-tkde-control-20261009:mis_micev_mis_b700_c30_s30`, `drtabpfn:elec2`,
`dtmoe_dev:elec2__dtmoe_L16_lr0.0001_s1_m1`, `dtmoe_dev:elec2__dtmoe_L32_lr0.0001_s1_m1`,
`dtmoe_dev:insects_abrupt_balanced__dtmoe_L32_lr0.001_s5_m3`.
Report each QUALIFIED / NOT QUALIFIED in the log and push. Any NOT QUALIFIED (or a dtmoe error "does not have a
deterministic implementation"): pause that pipeline (its tasks are not started), keep the evidence, report the
differing arrays, and wait: the coordinator diagnoses and registers its disposition with the arbiter and the user.
The other pipelines may go on. (The probe outputs are not results; keep them.)
- **dtmoe probe with its cap (ACTIVATION item 2, AMENDMENT_20261020 item 3).** For each of the three dtmoe ids,
  first `python rerun.py ref "<id>" $WORK/qualify/ref_<n>` (default mode; prints and writes only the wall time
  R), then `python rerun.py qualify "<id>" $WORK/qualify/<n> --timeout <10 R in seconds>`. One TOO SLOW stops the
  dtmoe path: log it with the times, push, and wait for the coordinator (the user decides the dtmoe path).

## Step 4. Production
- Slurm: one job per GPU (or one 8-GPU job), each running N workers
  `python rerun.py worker <slot> --gpu shared --exclude-sets dtmoe_dev,drtabpfn,mice_oracle_r11,results_delay_dev[,<every NOT QUALIFIED set>]`
  (dtmoe_dev starts only on a committed instruction of the coordinator; AMENDMENT_20261020 item 4). Request at least
  4 CPU cores per worker (`--cpus-per-task` >= 4N; item 8) and log it.
  in parallel (start with N = 3; raise to 4-6 if 30 min pass without any failure and the GPU is not saturated). The
  workers take tasks in file order (the paper-critical sets come first). Time limit per job <= 24 h; after a job ends
  with tasks left: `python rerun.py release`, then resubmit (the released tasks start again from initialisation; a
  kill counts as an attempt; a released benchmark is given up, see below).
- Tasks without a time estimate (the 5 benchmarks, mice_oracle_r11:all, results_delay_dev, drtabpfn, dtmoe_dev) run
  in their own jobs with the partition's maximum time limit (use `--sets`). A task killed by the time limit: report
  it, `release`, and wait for the coordinator's commit on its attempt counter before it runs again (item 7).
- Exclusive tasks (benchmarks: timing) last: one job per task, one worker, `--gpu exclusive`, nothing else on that GPU.
  Before the first one, check in that job that `$WORK/home/pfn-venvs/cache/tabpfn` holds the TabPFN v2 checkpoint.
- `python rerun.py status` every ~10 min; log progress and failures; GAVE UP tasks: read their log, report, do not
  retry by hand without telling the coordinator. Quarantined partial outputs stay in $RUNS/_rerun/quarantine.
- Once per set, when its first tasks are done and while the other workers run: `python rerun.py recheck <a done task
  of that set> $WORK/recheck/<set>`; it must print QUALIFIED. Otherwise pause that set, as for the probe.
- Benchmarks are never retried (rerun.py makes one attempt): a failed benchmark is reported.

## Step 5. Return
- Where the results go on the Windows machine is fixed by AMENDMENT_20261020 item 5 (`~/h800/`, never ~/pfn-runs or
  the working repository); the coordinator places them.
- Copy back (rsync to the Mac; the user then copies `mice_h800_results/` over RDP to the Windows desktop): the whole
  `$WORK/home/pfn-runs/` (inputs included; AMENDMENT_20261020 item 5), `$WORK/repo/MICE/results_*` (new outputs), `$WORK/home/pfn-runs/_rerun/` (records and logs), the env freezes;
  write SHA256SUMS. Log the totals (tasks, GPU hours, failures) and push.
- dtmoe: after its development grid is back, the coordinator freezes the configuration and adds its test tasks
  (a second handoff note); TOT likewise once implemented and gated.

## Phase P2: CPU results (REGISTRATION_P2_20261020.md; may run on CPU nodes alongside P1)
- **Inputs.** Copy the supplement bundle `C:\Users\zhwu9808\Desktop\mice_h800_bundle_p2\` over RDP, as for P1. Check
  SHA256SUMS on the Mac, then untar `ext-baselines-p2.tar` into `$WORK/home/ext-baselines/` and check
  `ext-baselines-p2.tar.files.sha256` there.
- **Environments.** Create two more Python 3.12 venvs from `env_lock/stream.txt` (river; set PYST to its python) and
  `env_lock/tsbase.txt` (torch 2.14.1+cpu; set PYTS). Record `pip freeze` into `cluster/env_freeze_stream.txt` and
  `cluster/env_freeze_tsbase.txt`; any difference from env_lock stops P2.
- **Node type.** Choose one CPU node type for all of P2 and record it (model, cores, memory) in the log before the
  first job. Give every worker a fixed core count (e.g. `--cpus-per-task=2`) and record it.
- **Probe first.** In one CPU job, run `python rerun.py qualify "<id>" $WORK/qualify_p2/<n> --tasks tasks_p2.jsonl`
  for the seven task ids listed in the registration ("Local evidence"). Report QUALIFIED / NOT QUALIFIED.
- **Production.** `python rerun.py worker <slot> --gpu cpu --tasks tasks_p2.jsonl`, many workers per node (the tasks
  are single-threaded or 2-threaded). Check progress with `python rerun.py status --tasks tasks_p2.jsonl`. Record time
  and memory per job.
- **Stop point.** The other P2 sets run until `status` shows none left. When ts_dev shows 720 done and 0 given up,
  push. If any ts_dev task is given up, push and report it; the coordinator registers its disposition before any
  selection. The coordinator registers P2b (selection,
  extension and tests of fsnet, onenet, adaptz and shifts) from those outputs. Do not select anything yourself.
