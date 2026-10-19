# Activation of the clean MICE rerun on the H800 cluster, 2026-10-19 (committed and pushed before any cluster run)

PLAN.md (commit 959aae3, a draft until now) becomes the registration of the clean rerun, with the changes below. Where
this note and PLAN.md / HANDOFF.md disagree, this note holds.

## User decisions (2026-10-19, verbatim, with the options they answered)
1. "我准备把mice 单独到8块H800跑，但是H800在同济 集群里面，我用我家里macmini连上了集群……你帮我办法怎么搞". Options
   offered: A, GitHub as relay and a Claude Code session on the Mac mini operating the cluster; B, Tailscale network
   with SSH ProxyJump through the Mac mini. Answer: "选A 整个mice 重新跑，数据和权重都要在macmini下好".
2. The repository is public (anonymous HTTP 200), so data and weights cannot go through GitHub. Options: OneDrive share
   link; a new private GitHub repository; the Mac mini downloads from the original sources (identity not guaranteed).
   Answer: OneDrive; then "我用macmini rdp 登录上了这个服务器，可以直接从桌面拉文件，不用onedrive了".
3. dtmoe device, options "H800, strict deterministic mode" / "stay on the local CPU (amendment e)": "H800，严格确定性模式".
4. Local Drift-Resilient TabPFN, options "stop now" / "stop when the H800 DR starts": "现在就停".
5. Scope, options "only the GPU-computed results (2828 tasks); CPU results stay local" / "move the CPU results to the
   cluster as well": "CPU 的也搬到集群重跑".
6. Extra backbones (robustness check, the role of the existing TabICL check): "7 个全测" (TabPFN v2.5, v2.6, 3, 3.5,
   TabDPT, Mitra-v2, LimiX), after Fable's advice that only TabPFN-3.5 and TabDPT are necessary
   (MICE/logs/table1_fill/fable_backbones.md).
7. CURE (arXiv 2606.18677, concurrent work, public code), options "cite and add as a main-table baseline" / "cite only":
   "引用，并加为主表基线".

## Changes to PLAN.md
1. **Drift-Resilient TabPFN (DR).** PLAN.md says that DR "is not run on the local GPU (no local output exists)". This is
   no longer true: under amendment d, 13 of the 92 streams finished on the local GPU
   (~/pfn-runs/mice-table1-newbase/drtabpfn), and a partial checkpoint of h3_insects_c remains. The local run was
   stopped on 2026-10-19 at 23:39 (user decision 4). These outputs are kept and are never merged into or substituted for
   H800 outputs. The reported DR results are the H800 results.
2. **dtmoe.** H800, strict deterministic mode, as in PLAN.md and gpu_verify AMENDMENT_20261018b. The CPU dtmoe of
   amendment e is cancelled; its grid never started, and its probe outputs are kept. On the local GPU, strict mode was
   at least about 40 times slower than the default mode (amendment d, deviation record). The H800 probe therefore
   follows amendment d item 4. If the strict probe does not finish within 10 times the default-mode time of the same
   task on the H800, it is stopped as "too slow" with no determinism verdict. The dtmoe path (a fallback, CPU, or no
   dtmoe) then goes to the user, before any dtmoe production run; that choice is not conditioned on any dtmoe score. The default-mode reference is one run per probe task
   on the same H800 with TS_DETERMINISTIC unset, into $WORK/qualify/ref_<n>. Its wall time is the only value read, and
   its outputs are never used. Each of the three probe tasks must finish within the cap; one "too slow" stops the
   dtmoe path, which then goes to the user as above.
3. **Supersessions reversed.** Amendment d item 1 (H800 replaced by the local GPU) and amendment e item 1 (dtmoe on the
   local CPU) no longer apply to DR and dtmoe. Every other item of amendments c, d and e stands where it applies
   (selection, extension, freezing, bookends, provenance flags). Amendment d item 8 (GPU timing on the local GPU),
   amendment e item 6 (CPU footnote, CPU timing) and the "local CPU" of amendment c item 7 no longer apply. Timing and
   peak memory of every Table 1 method are measured on the cluster: GPU methods on an H800, CPU methods on one cluster
   CPU node type, registered with P2.
4. **Scope (user decision 5).** The CPU-computed MICE results are also rerun on the cluster: the river and trained
   learners, the four CPU baselines of Table 1 (fsnet, onenet, adaptz, shifts: registered grid, one-time extension,
   selection, freezing, tests as in amendment c), and arf / srp of the confirmation sets. They form a later phase
   (below), with their own task list registered before it runs. Local CPU runs that are still going (the
   extension grid of the four baselines) may finish but are not used for reporting, except under the "CPU local" rule of this item. If a cluster set cannot run, the
   reason is logged before any cluster score of that set exists. That set is then reported from the local CPU outputs
   with the flag "CPU local", without choice. No local extension, selection (select_frozen.py --final) or test score
   of the four CPU baselines or of the (cancelled) CPU dtmoe is read before the P2 selection is committed from cluster outputs;
   the original-grid selections already made under amendment c stay records, not P2 inputs. Differences between
   cluster and local CPU outputs are reported, not chosen between.
5. **Transport (user decisions 1, 2).**
   - Code: the public repository at the registering commit (git clone on the Mac mini, then rsync to the cluster).
   - Inputs: the bundle written by make_bundle.sh to C:\Users\zhwu9808\Desktop\mice_h800_bundle (data, run inputs,
     ext-baselines with the Drift-Resilient TabPFN model_cache, the TabPFN v2 cache, SHA256SUMS). The user copies it
     to the Mac mini over RDP; it then goes to the cluster by rsync. SHA256SUMS and the per-file hashes are checked on
     the cluster, as in HANDOFF step 1.
   - Downloaded on the Mac mini, with sha256 recorded in the cluster log: the TabICL checkpoint, and the Python wheels
     of env_lock/ (only if the cluster has no package mirror).
6. **Phases.** Each later phase is registered (task list, criteria, committed and pushed) before it runs:
   - P1: tasks.jsonl as frozen (2828 GPU tasks).
   - P2: the CPU sets of item 4.
   - P3: the extra backbones.
   - P4: CURE.
   - P5: the dtmoe test tasks, after its freeze.
   - P6: TOT, with the gates and device (CPU) of amendment c item 5; its task list is registered separately before it
     runs.

   Within P1, the order of tasks.jsonl holds. The cluster may run P2 on CPU nodes alongside P1.

## Extra backbones (P3; rules fixed now, before any run or result)
- Backbones: TabPFN v2.5, v2.6, 3, 3.5 (tabpfn 9.0.0, ModelVersion), TabDPT, Mitra-v2, LimiX. Exact versions,
  checkpoints and hashes are fixed in the P3 registration.
- Protocol: that of the TabICL check (paper: "Second backbone and second seed").
  - Segments: the four segments of the third held-out set and the six segments of the fourth.
  - Settings: fixed segmentation, the same policies, no constant changed, the same four hypotheses ("at least three of
    four").
- Reporting:
  - every backbone listed in the P3 registration is reported in the paper, in the robustness paragraph and the pre-registration
    appendix, whatever its result;
  - a backbone is excluded only for reasons fixed before any accuracy is read: weights unavailable offline; an error
    for the class or feature counts; out of memory with a 28 GB per-process cap enforced on the H800
    (torch.cuda.set_per_process_memory_fraction); time per batch above 20 times that of TabPFN v2. Both are measured
    in the same smoke test on an H800, which writes no accuracy array (predictions discarded);
  - an exclusion is logged with its evidence before any accuracy of that backbone is read.
- Each adapter (TabDPT, Mitra-v2, LimiX) is first audited by MiMo Pro high, then smoke-tested inside MICE for time
  and memory only, before P3 is registered.

## CURE (P4; main-table baseline)
- CURE is cited as concurrent work.
- It runs as a baseline policy of the main table with the TabPFN v2 backbone and the memory budget of every policy
  (M = 1000 rows), from its public code (github.com/morcellinus/CURE-ICML-FMSD, commit fixed in the P4
  registration).
- Hyperparameters: CURE's published defaults; no tuning. If a default is undefined for this setting (no value in its
  code or paper), the value and the reason are fixed in the P4 registration before any run.
- CURE uses the main table's streams, seeds, batch size and backbone.
- No registered hypothesis names CURE, and every CURE cell is reported whatever its value. MICE's constants and claims
  are unchanged.
- The adapter is first audited by MiMo Pro high, then registered before any run.
