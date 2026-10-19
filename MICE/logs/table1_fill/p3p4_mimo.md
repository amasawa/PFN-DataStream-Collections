# MiMo 审计 P3/P4 适配器（2026-10-20）

## P3：run_backbone.py，MiMo v2.6 Pro high，09:42:53–09:51:41

## Audit: `run_backbone.py` backbone adapter (P3)

**1. P1 — Suspected issue — LimiX `pipelines[:4]` of 32 may bias the comparison**
- Location: `run_backbone.py:65` (`cfg["pipelines"] = cfg["pipelines"][:LIMIX_MEMBERS]`); evidence.txt line 7 ("open point").
- Evidence: the no-retrieval config ships 32 preprocessing pipelines (the ensemble's designed diversity); the adapter takes a *prefix*, not a sample. The pipeline list itself is not in the package, so whether the first 4 are a representative slice cannot be checked here.
- Why it matters: if the 32 pipelines are ordered by family (e.g. all quantile variants first), the first 4 under-represent LimiX's designed preprocessing diversity and the robustness comparison ("does the phenomenon hold for another frozen backbone") is run against a weakened or unrepresentative LimiX, not against LimiX as designed. Equal member count is a fair compute choice; an unexamined prefix is not a fair content choice.
- Recommended correction: inspect `cls_default_noretrieval_v2.json`; pick 4 spread across the list (e.g. indices 0, 8, 16, 24 or one per family) or run a subset-sensitivity check (2–3 different 4-subsets on 1–2 streams) and report the spread; state the selection rule in the paper/appendix.

**2. P1 — Missing information — call semantics of TabDPT and LimiX are unverified; current evidence cannot detect a mis-call**
- Location: `run_backbone.py:82-89` (`TabDPTClassifier.fit` + `ensemble_predict_proba`; `LimiXPredictor.predict(Xc, yr, Xq, task_type=...)`); no TabDPT/LimiX `predict`/`fit` signatures in `library_excerpts.txt`.
- Evidence: the smoke test asserts only `Pq.sum(1) ≈ 1` and output shape (`run_backbone.py:111`, `run_backbone.py:91`). Row-normalized garbage (swapped train/test argument order, context subsampled, logits post-softmaxed twice) passes both checks. Mitra is covered by the sklearn-interface excerpt; the other two are not.
- Why it matters: a wrong call would silently produce invalid probabilities for two of the seven backbones while all current evidence looks clean.
- Recommended correction: attach the `fit`/`predict`/`ensemble_predict_proba` signatures; run a toy sanity check per backbone (separable 2-class problem, context 50 rows, expect accuracy ≥ 0.99 and near-one-hot probabilities) before the full run and record the output.

**3. P1 — Suspected issue — Mitra "frozen" and "patch changes no computation" are asserted, not shown; the shared instance amplifies any violation**
- Location: `run_backbone.py:47-52` (cache monkeypatch), `run_backbone.py:51` (`fine_tune=False`); library excerpt `_train_ensemble` always calls `trainer.train(...)` even when `fine_tune=False`.
- Evidence: code comment and evidence.txt claim "weights never change", but `_train_ensemble` runs a train loop per member regardless; nothing in the evidence compares weights or predictions before/after `fit`. Worse, the monkeypatch makes **all** trainers of **all** fits share one model instance, so any in-place state change (optimizer step, dropout/BatchNorm train-mode buffers, `n_classes` rewrite) would compound across members, batches and method runs — results would depend on run order.
- Why it matters: if freezing does not hold exactly, this backbone is neither frozen nor order-invariant, and the robustness check is invalid for Mitra.
- Recommended correction: verify at runtime (see list below): state-dict hash before/after `fit`, and identical probabilities for two consecutive `predict` calls on the same context; if either fails, drop the instance cache (load per member, as stock) and/or find the flag that truly disables updates.

**4. P2 — Confirmed issue — Mitra cache monkeypatch reloads the checkpoint on every call (comment claims "one load per process")**
- Location: `run_backbone.py:49-50`: `cache.setdefault((path, str(device)), _load.__func__(cls, path, device=device))`.
- Evidence: Python evaluates arguments before the call, so `_load.__func__(...)` runs on every `from_pretrained` even on a cache hit; the fresh load is discarded and the first model returned. The comment at `run_backbone.py:47-48` ("the loaded model is kept (one load per process)") is wrong about the load count — it is one *kept* model but N loads.
- Why it matters: no prediction change by itself (same object returned), but the stated intent is not achieved (per-call disk load; consistent with the high 3.74 s/call), and the pattern hides finding 3.
- Recommended correction: `m = cache.get((path, str(device))); if m is None: m = cache[key] = _load.__func__(cls, path, device=device); return m`.

**5. P2 — Confirmed issue — both monkeypatches are re-applied on every `TFM.__init__`, nesting wrappers**
- Location: `run_backbone.py:46-52` and `run_backbone.py:60-62`, both inside `__init__`; `run.run` constructs `TFM(K)` per stream×method (run_py_excerpts.py:40), so a multi-stream/multi-method process re-wraps each time.
- Evidence: the second pass binds `_load` to the *already patched* classmethod and wraps again; each nested LimiX `__init__` calls `tempfile.mkdtemp` before delegating to the inner patched `__init__`, which creates another one — empty temp directories accumulate per construction.
- Why it matters: computation is unaffected (LimiX cache unused with `use_data_cache=False`; Mitra returns the first model), but memory/leaks grow and the wrappers make findings 3–4 harder to reason about.
- Recommended correction: apply each patch once at module import (or guard with a flag); give the LimiX cache a single temp dir (or `atexit` cleanup).

**6. P2 — Missing information — `calls` counter semantics on the single-class early return**
- Location: `run_backbone.py:74-76` (returns without `self.calls += 1`, which is at line 93); `run.py` predict body is truncated in `run_py_excerpts.py:19-26`.
- Evidence: cannot see whether `run.TFM.predict` increments `calls` unconditionally or only after a backbone invocation. The docstring claims semantics are "as in run.TFM".
- Why it matters: only affects any cost/call accounting built on `calls`, not accuracy; diverging counts would misreport backbone-call statistics between TabPFN v2 and P3 backbones.
- Recommended correction: show `run.TFM.predict`'s increment location and match it (increment before the early return if run.py does it unconditionally).

**7. P2 — Suspected issue — offline use and run-to-run determinism are not enforced in code**
- Location: `run_backbone.py:36-38, 42, 52, 66` (paths under `P3_WEIGHTS`); `run_backbone.py:56-57` (`MASTER_PORT=29500`); LimiX `__init__` defaults `deterministic=False`, `preprocess_num_jobs=16` (library excerpt lines 195-199), not overridden at `run_backbone.py:66-67`.
- Evidence: `evidence.txt` says `HF_HUB_OFFLINE=1` was set in the smoke test and sha256 recorded, but nothing in `run_backbone.py` sets it or verifies weights; `deterministic=False` leaves RNG pinning off; parallel preprocess may vary float results across runs; a hard-coded port collides if two LimiX processes start concurrently, and `setdefault` silently adopts a pre-existing `RANK`/`MASTER_PORT` from the environment.
- Why it matters: a silent download of a different revision, or nondeterministic re-runs, would break the pinned comparison and reproducibility claims without any error.
- Recommended correction: set `HF_HUB_OFFLINE=1` (and verify sha256) in the full-run script; set LimiX `deterministic=True` or demonstrate two identical runs match; allow `P3_MASTER_PORT` override or use a free port.

**8. P2 — Confirmed (interpretation note) — two settings differ from each backbone's native usage and should be stated in the paper**
- Location: `run_backbone.py:51` (`fine_tune=False` for Mitra); `run_backbone.py:66-67` (LimiX library default `softmax_temperature=0.9` kept).
- Evidence: Mitra's interface is built around fine-tuning on the support set; freezing it tests a weaker, non-native variant. LimiX applies its native temperature calibration while TabPFN versions do not — part of each library's default pipeline.
- Why it matters: neither is a code error (both were decided before coding), but they bound the claim: "the phenomenon holds for other frozen backbones" is accurate; "holds for Mitra/LimiX as used in their papers" would not be.
- Recommended correction: one sentence per backbone in the appendix on which native settings were kept/overridden and why (frozen-backbone policy).

### Points only confirmable by running code
1. Mitra freezing: hash `state_dict` before/after `fit`; two consecutive `predict` on the same context must be bit-identical; compare probabilities with vs without the instance cache on one fixed batch.
2. Mitra trainer side effects with `fine_tune=False`: whether `TrainerFinetune.train` runs optimizer steps or leaves the model in train mode (dropout/BN).
3. TabDPT: does `fit` keep the full 1000-row context or subsample; what `seed` in `ensemble_predict_proba` controls; two identical runs must match.
4. LimiX: argument order/meaning of `predict` via a toy sanity check; two-run identity with `deterministic=False`; accuracy under 2–3 different 4-of-32 pipeline subsets (finding 1).
5. Toy separable sanity check for **all** backbones (shape + row-sum checks cannot detect a semantically wrong call).
6. `calls` counter vs `run.TFM` on a stream containing a single-class batch (finding 6).
7. Full-run path has no row-sum assert (only `--max-batches` does, `run_backbone.py:111`): one batch from the real run output should be checked to sum to 1.

### 处置（Claude 核实）
1. LimiX 前 4 个成员 — 采纳：改为等间隔 0、8、16、24；实测子集生效（与前 4 个差 ≤0.10，与全部 32 个差 ≤0.06）。
2. TabDPT、LimiX 调用语义 — 采纳：7 个骨干在玩具可分问题上全部 100% 正确、缺席标签概率为 0。
3. Mitra 是否冻结 — 核实：fit 前后 state_dict 哈希相同、eval 模式；但发现原生 Mitra 不确定（全局 random/np.random 未设种子，AutoGluon ≥1.4 移除了 set_seed）：同一上下文两次预测差 ≤0.09。修正：每次调用以骨干种子设定全局 RNG 并在结束后恢复；修正后同进程重复预测、跨进程均逐位相同。
4. Mitra 缓存每次都重新加载 — 成立（setdefault 先求值参数），已修；每次调用 3.7 秒 → 1.5 秒。
5. 补丁重复套用 — 采纳：每个进程只打一次。
6. 调用计数 — 不成立：run.TFM.predict 在单类分支直接返回、不计数，与适配器相同。
7. 离线、确定性 — 采纳：适配器设 HF_HUB_OFFLINE=1；7 个骨干跨进程逐位相同；predict 中加入概率和为 1 的断言。LimiX 的 MASTER_PORT 仅在 DDP 时使用（inference_with_DDP=False），不改。
8. 论文需说明未用的原生设置 — 采纳（登记中已写）。

## P4：run_cure.py
第一次 Pro high 审计（09:42:53–09:47:25）输出作废：MiMo 回答的是无关内容（另一个项目的"主实验 033"），没有审计 run_cure.py。在新的隔离目录重新审计。

## P4 重新审计：run_cure.py，MiMo v2.6 Pro high，09:52:12–10:04:17
## Findings

**1. P2 · Suspected issue · `run_cure.py:81-83` (also `:65`) — checkpoint handle is never closed before the atomic replace.**
Evidence: `pickle.dump(dict(...), open(ck + ".tmp", "wb"))` is immediately followed by `os.replace(ck + ".tmp", ck)`; the file object is only closed by CPython refcount finalisation after the statement. `pickle.load(open(ck, "rb"))` at line 65 has the same pattern.
Why it matters: if the dump is not flushed before the rename, a "successfully written" checkpoint is truncated and the next resume dies in `pickle.load` (blast radius is a crash, not silent corruption). The executor's kill-at-batch-25/resume test shows it behaves on this platform, so this is robustness, not a current defect.
Recommended correction: `with open(ck + ".tmp", "wb") as fh: pickle.dump(..., fh)` before `os.replace`; same for the load.

**2. P2 · Suspected issue · `run_cure.py:44,47` — `gate`/`warm`/`bypass` re-derive undocumented policy internals instead of reading explicit fields.**
Evidence: `g = len(ev.evicted_timestamps) - len(ev.evicted_indices)` is correct only because in `cure_memory.py` a gate-drop extends `evicted_ts` alone (line 177) while a long-drop extends both lists (lines 188-190); hence `g` = gate-drops and `out - g` = promotions, with `out = s0 + 1 - short_size()` counting loop-1 exits only (loop 2 never touches short rows, and at most one loop-1 iteration occurs per append since `short_size ≤ 750` is an invariant). `bypass` at line 44 duplicates `warm_fill_target` (`cure_memory.py:167,174`) and coincides with the policy's flag only because the appended row is short and does not change `long_size`. Smoke totals close: 3072 + 250 + 1928 = 5250 = 6000 − 750.
Why it matters: any change in `EvictionEvent` semantics (e.g. gate-drops recorded in `evicted_indices`, or >1 timestamp per drop) makes `left/gate/warm` and the printed `admitted_by_gate` silently misreport the mechanism, with no test to catch it.
Recommended correction: state the invariant (gate-drop = +1 timestamp/0 indices; long-drop = +1/+1) next to line 47, or read a dedicated `details["gate_dropped"]` counter from the policy; same for the warm-fill threshold.

**3. P2 · Confirmed issue (documentation) · `run_cure.py:14-18` vs `:86-89` — output keys `calls` and `tau` are written but not documented.**
Evidence: the docstring lists `acc, pred, P, C, B, wt, te, peak_mem, mem, short, long, left, gate, warm`; `np.savez_compressed` also writes `calls=f.calls` and `tau=tau`.
Why it matters: downstream aggregation cannot rely on a documented schema.
Recommended correction: add both keys to the docstring's output list.

**4. P2 · Suspected issue · `run_cure.py:53,63,66,81,102` — checkpoint/output identity omits `B`.**
Evidence: `tag = f"cure_tau{tau:g}"` covers tau (a different tau gets its own ckpt/npz) but not `--B`; the checkpoint dict (`mem, t, P, acc, wt, te, stats, calls`) stores neither `B` nor `tau`, and on resume `P[:len(c["P"])] = c["P"]` is shape-checked only by accident.
Why it matters: resuming with a different `--B` either raises on a shape mismatch or (if `len(c["P"]) < len(P)`) silently misaligns prediction rows with batch indices. The registered protocol fixes B = 100, so there is no current impact.
Recommended correction: store `B` (and `tau`) in the checkpoint dict and assert equality on load, or put `B` in the tag.

## Verified by reading (no issue within scope)

- **Faithfulness (1):** `record_prediction_signal` for row *i* is called with `Pb[i, labs]` where `labs` is fixed at batch start — exactly the support of the prediction made before any label of the batch arrives — then renormalised; entropy is therefore divided by `log(#context classes)` as in CURE's TabICL path. Order is signal → `append_then_evict` per row, matching the official runner (`context.txt:197,210`). Batch 0 is appended with `probs=None` (entropy 0), matching CURE's `warmup_steps` rows. A one-class context yields `p=[1]`, `entropy 0`, `margin 0` — gate-equivalent to CURE's `probs=None` (the `y_pred` difference is dead data: `_CUREMeta.pred` is never read). `budget_B=1000, short_ratio=0.75` → 750/250, and the memory is capped at 1000 rows (loop 1 leaves `short ≤ 750`, loop 2 leaves `long ≤ 250`).
- **Protocol (2):** at iteration *t* the memory holds only batches `0..t-1`; `P[r] = f.predict(Xm, ym, X[q])` is scored against `y[q]` and only then appended (`run_cure.py:74-77`). `y_true` is discarded in the policy, so the gate depends only on pre-label probabilities: no label leakage. `P` rows `(t-1)B .. tB` map to batch *t*; `acc[0] = NaN`; context is capped at M = 1000.
- **Counters (3):** derivation checked line-by-line against `cure_memory.py:157-207`; see finding 2 for the fragility, the arithmetic itself is correct, including `admitted = left − gate − warm` over batches 1.. (`run_cure.py:93`).
- **Checkpoint (4):** save point `t % 25 == 0 and t < T−1` stores `t+1` as the next batch and `P[:t*B]`; resume continues `r` at `t*B` with a rebuilt, seed-0 `TFM` and restored `f.calls`; write is tmp + `os.replace`, and the final npz write uses the same pattern; a stale `.ckpt.pkl` can only remain if the process dies between line 90 and line 92 (harmless: the npz short-circuits the run).
- **Outputs (5):** key set and shapes match the docstring apart from finding 3; `pred = P.argmax(1)` over batches 1..T−1 is consistent with `acc`. `C = int(y.max())+1` peeks at the whole stream but is used only to size `P`/`TFM.K`; the model's support is restricted to context classes, so predictions and scores are unaffected.

## Can only be confirmed by running code

1. Resume determinism on any stream other than the smoke run: the checkpoint holds no RNG or model state (`run_cure.py:81-82`) and `TFM` is reconstructed at line 59; identical results rely on `random_state=0` refits being pure functions of the data. Smoke evidence covers one kill/resume at batch 25 of 60 only.
2. The one-class-context path (`run_cure.py:41-42` + `TFM.predict` early return) was not exercised: the smoke stream has 2 classes and a growing memory, so `len(labs) == 1` never occurs after batch 0.
3. Counter identities on Table 1 streams (`sum(left) = appended − final short`, `gate + warm + admitted = left`); the smoke arithmetic is consistent (5250 = 6000 − 750 = 3072 + 250 + 1928).
4. `P` rows summing to 1 and `calls = T−1` outside the smoke stream (both hold there: 59 = 60 − 1).

No P0/P1 within the reviewed scope.

### 处置（Claude 核实）
1. 断点文件未关闭即替换 — 采纳：改用 with。
2. 计数依赖策略内部约定 — 采纳：在代码中写明不变式（门丢弃 = 1 个时间戳、0 个索引；长库淘汰 = 1/1；每次追加至多一行离开短期记忆）。
3. calls、tau 未写入文档 — 采纳。
4. 断点不含 B — 采纳：断点存 B、tau，恢复时断言一致。
运行才能确认的点：单类上下文路径已实测（前 1500 行改为单类的合成流：calls 44 = 59 − 15，计数恒等式成立，概率和为 1）；修改后原冒烟流输出与修改前逐位相同。
