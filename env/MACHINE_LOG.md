# Machine log (university WSL machine, RTX 5000 Ada 32 GB)

Faults of this machine, how each was handled, and how GPU use is monitored. Applies to all projects; each project's
own `logs/EXPERIMENT_LOG.md` records the experiments and points here for machine issues. Times are taken from `date` or
file modification times.

## Machine and policies
- WSL2 (kernel 6.18, `dxgkrnl` GPU paravirtualisation) on a university Windows workstation with Cortex XDR; 20 cores,
  30 GB RAM, one RTX 5000 Ada 32 GB that also drives the display (`Disp.A On`, Xwayland). Python envs in `~/pfn-venvs/`.
- RDP policy (checked 2026-09-30): idle 15 min, disconnected 5 min, `fResetBroken=1` → the session is ended and WSL,
  tmux and every job die. Keep the RDP window open with `rdp-keepalive.ps1`; locking the screen is fine, disconnecting
  or closing the window is not.
- No scheduled restart. The 04:00–05:00 server update announced on 2026-10-06 was cancelled (user, 2026-10-08);
  runs no longer need to finish or pause before 05:00. Long runs still checkpoint and resume, because the WSL VM has
  been powered off from the Windows side without notice (see the table below).

## Faults and fixes

### 1. CUDA "unspecified launch failure" / "illegal memory access" (recurring since 2026-10-05)
- **Open hypothesis (2026-10-08, not yet tested)**: failures cluster after process start. Time from LAUNCH to failure:
  6/25 within 60 s on 2026-10-08 and 8/27 on 2026-10-07 (median 170 s and 220 s), against about 10% expected for tasks
  of about 10 minutes if the hazard were constant. A staggered or serialised start (one process initialising at a time)
  is the candidate mitigation; it has not been tried. Single-process reruns of failed tasks pass.
- **Symptom**: a TabPFN/TabICL process dies inside `torch.cuda.synchronize`; nothing points at our code.
- **Known triggers** (on/off tests, MICE log 2026-10-05): CPU-heavy jobs running beside GPU chains (River / trained
  stream baselines: 6–7 failures in 6 min with them on, 0 with them off, also at 2 workers with `nice 19`); headless
  Chromium (Excalidraw renderer): one failure per render, 3 of 3.
- **2026-10-06 21:35, a second cause — GPU memory full**: MiceDuo's `check_duo.py` predicted ~9,900 query rows in one
  `predict_proba` call; GPU memory reached 32.1/32.8 GB and the kernel log showed
  `dxgkio_make_resident: Ioctl failed: -12` (out of memory). Fix: query rows in chunks of 1,000 (identical
  predictions; TabPFN test rows are independent). Memory then stayed at ~11 GB.
- **2026-10-06 21:49–22:03, failures with only ~1 GB in use**: 4 failures in duo (all on elec2) and 3 in ResetEval's
  `re1`. Cause not identified. Leading hypothesis (not verified): Windows TDR (GPU timeout detection and recovery) on a
  GPU that also drives the display. Check in Windows Event Viewer → System, source "Display", event 4101 at those
  times (needs the Windows side, so it was not run from WSL). If confirmed, the fix is a larger `TdrDelay` in the
  registry (admin rights).
- **Mitigation in every GPU script**: a retry loop in the tmux command (`until python ...; do echo RETRY; sleep 45;
  done`) and resume-from-files: ResetEval writes one file per (stream, policy) and its prediction cache every 200
  calls; duo now checkpoints every 20 batches (`results/duo/<stream>.part.pkl`) instead of restarting the stream.
- **Guard for chains that keep failing**: `MiceDuo/results/guard_duo.sh` pauses the chain with the most retries when
  the chains together have ≥ 4 RETRY in 10 min and resumes it later; an earlier rule stopped duo after 4 retries
  without a finished stream (it fired at 22:02:57).

### 2. WSL restart around 21:00 on 2026-10-06
- All tmux sessions vanished (`re1` stopped at 19:02 without an error line, `duo` after a retry at 18:25). System
  processes all started at 21:00 (`ps`, `uptime`).
- Fix: both chains restarted with the original commands (recovered from the previous session's transcript); results
  resume per file. Lost work: only predictions computed but not yet cached.

### 3. Work-queue lock not atomic on /mnt/c (2026-10-06 23:35)
- `mkdir` on the Windows drive (drvfs) is not atomic: 4 of 7 queue chains claimed the same stream within 30 s.
- Fix: lock directory moved to the Linux filesystem (`~/.reset_locks/`), chains started 2 s apart
  (`ResetEval/code/run_queue.sh`). Outputs of those 30 s were deleted (nothing had been written).
- Rule: locks, sockets and anything that needs atomic file operations go on the Linux filesystem, not /mnt/c.

### 4. Other pitfalls already known
- `pkill -f <pattern>` kills the calling shell if the pattern occurs in its own command line; use `pkill -f 'run_[r]iver.py'`.
- Never `git checkout` another branch while jobs run (files are deleted and recreated; running jobs write to the
  deleted ones).

## Monitoring GPU utilisation
- **Why utilisation is low with one process**: TabPFN/TabICL calls here are small (context ≤ 1,000 rows, 100 queries);
  each process is bound by one CPU core (~115% CPU: preprocessing, Python, the detectors' per-row loops), so one
  process gives ~20% GPU. GPU memory is not the bottleneck (5–9 GB for 6–9 processes).
- **Rule of thumb**: run 6–9 GPU processes. Measured 2026-10-06: 1 process 11–24%, 3 processes ~20–60%,
  6 processes 75–99%, 9 processes (TabICL) ~95–100%.
- **How**: independent units of work (streams) are spread over many chains. For ResetEval a shared queue
  (`run_queue.sh`, longest streams first, one lock per stream) lets any number of chains run; chains are added when
  utilisation falls below ~70% (e.g. when short streams finish) and removed when retries become frequent.
- **Watching**: a Claude Code Monitor reports every RETRY / STREAM_DONE / CHAIN_DONE line and samples
  `nvidia-smi` every 5 min; for unattended runs `tmux gpu_sampler` writes one line per minute
  (`date, util %, memory MiB, python process count`) to `ResetEval/results/gpu_util_stage2.csv`.
- **Unattended finish**: a tmux "finisher" waits for all `CHAIN_DONE` lines and runs the analysis itself
  (`ResetEval/code/finish_stage2.sh`), so results do not depend on an open Claude session.

## Timeline 2026-10-06 (evening)
| time | event | action |
|---|---|---|
| 18:25 | duo CUDA failure, then no output | — |
| 19:02 | `re1` stops (no error line) | — |
| ~21:00 | WSL restarted, tmux sessions gone | 21:13 `re1` and 21:30 duo restarted |
| 21:31–21:35 | duo fills GPU memory (32 GB), failure | query chunking, restart 21:35 |
| 21:49–22:03 | failures with low memory (cause unknown) | duo stopped by rule 22:02:57; `re1` kept going |
| 22:04–22:07 | utilisation 11–24% with 1–3 processes | 6 chains → 75–99% |
| 22:43 | utilisation 55% as short streams finished | duo started early as 4 parallel chains, extra `re1f` |
| 23:00 | ResetEval stage 1 and duo done (4 retries after 22:07, none after 22:43) | analyses |
| 23:10–23:37 | 10 new real streams (2 rounds × 5 chains), 0 retries | — |
| 23:35–23:36 | TabICL queue: lock race on /mnt/c | locks moved to Linux fs |
| 23:48 | 9 TabICL chains, finisher and per-minute sampler started | unattended until done |
| 01:35:57 | WSL VM clean poweroff (systemd shutdown in journal, not OOM/crash; triggered from Windows side, cause unknown); all tmux jobs lost | 01:38 cleared queue lock, restarted 9 TabICL chains + sampler, finisher, relay; per-policy outputs resume |

## 2026-10-07 02:15 ResetEval stage 2 (TabICL), unattended run finished (auto-written)
- 9 queue chains; CUDA retries: 0; GPU: 145 samples (one per minute), mean utilisation 92.4%, minutes below 70%: 16, mean memory 6529 MiB.

## 2026-10-07 04:14:40 第二次 WSL 关机
- 与 01:35:57 相同：journal 中是完整的 systemd poweroff，来自 Windows 一侧，原因未知（早于预计的 05:00 重启约 45 分钟）。关机前 GPU 利用率 99–100%。
- 后果：relay 04:40 的自动分析/commit 没有执行；06:08 重启后手动补跑并 commit。教训：自动收尾不要排在离预计重启时间太近的地方，或每完成一条流就增量 commit。

## 2026-10-07 06:44 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` breaks CUDA under WSL
- Symptom: every new TabPFN process started with this setting failed at model load with `RuntimeError: CUDA driver error: unknown error` (ResetEval c1–c5 logs). Processes without it ran normally on the same GPU at the same time.
- Fix: removed the setting from `ResetEval/code/run_queue3.sh` and restarted the chains. Do not use expandable segments on this machine.
- Also: the supervisor's first version died after 5 min (`(( ) / 0`): `${a[@]: -5}` on an array shorter than 5 elements is empty. Fixed 06:38.

## 2026-10-07 18:34 repository split (local only, nothing pushed)
- `Desktop/pfn-split/ood` (AgDR, GOR) and `Desktop/pfn-split/dataStream` (MICE, DriftTriage, GrayContext, ResetEval, MiceDuo, FeatEvo, Emergence, InterTFM), each with its own history via `git filter-repo` (tool in `~/pfn-venvs/tools`); `pdfs/`, `env/`, `skills/`, `SETUP.md` in both. Untracked data copied with rsync (12 min for 10 GB). No remote set yet. `Desktop/pfn` and `oodpfn` unchanged.
- Checked: file counts match the joint repo (2328 / 500); `git status` clean after the copy; ResetEval's analyses reproduce in the new location (TabDPT T1 = 29.01).
- 2026-10-07 21:13 pushed: `pfn-split/ood` -> github.com/amasawa/PFN-OOD-Collections, `pfn-split/dataStream` -> github.com/amasawa/PFN-DataStream-Collections, each over its own write-enabled deploy key (`~/.ssh/id_ed25519_ood`, `id_ed25519_datastream`; host aliases `github-ood`, `github-datastream` in `~/.ssh/config`). The old key `id_ed25519_oodpfn` is a deploy key of `oodpfn` only.
