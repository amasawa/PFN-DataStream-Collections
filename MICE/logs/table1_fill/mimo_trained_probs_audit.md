## Findings

### 1. River empty-proba branch: sentinel pred and zero P row poison the metrics
- **Severity:** P2
- **Finding status:** Suspected issue
- **Location:** `run_trained_probs.py:39-41` (`pred[j] = max(p, key=p.get) if p else -1`; `P[j, int(k)] = v` loop) and docstring lines 4-5
- **Evidence:** River's `Classifier.predict_one` returns `None` when `predict_proba_one` is empty (evidence.txt), while this code writes `pred=-1` and leaves `P[j]` all zeros. Accuracy is preserved (both count as wrong), but `compute_metrics` does `P / P.sum(1, keepdims=True)` → 0/0 = NaN row → `roc_auc_score` raises "Input contains NaN" (or NaN ECE/Brier/NLL), so one empty call kills that stream-method in the read-out. The docstring claim "exactly river's Classifier.predict_one" is false in this branch (`None` vs `-1`), and `pred=-1` is not in `0..C-1`.
- **Why it matters:** pred is the source for Table 1 acc/F1 and P for AUC/ECE/Brier/NLL; a single empty call silently corrupts or crashes the read-out of an entire (stream, method) cell.
- **Recommended correction:** in the empty branch write `P[j] = 1.0 / C` (uniform) or fail loudly; keep `-1` only if documented as "abstain", and align the docstring with the actual behaviour.

### 2. MOOE scores must not pass through `compute_metrics.metrics` for AUC
- **Severity:** P1
- **Finding status:** Missing information
- **Location:** `run_trained_probs.py:59,68` (stores raw linear outputs as `S`); consumption side `compute_metrics_excerpt.py:1-4` (`P = np.clip(P, 0, 1); P = P / P.sum(1, keepdims=True)` before `roc_auc_score`)
- **Evidence:** `metrics()` clips to [0, 1] (collapsing all negative scores to 0 and all >1 to 1) and row-normalises (each row divided by a different constant) before the AUC. Both operations change cross-row ranking of each class column, so AUC computed on that output is not the AUC of `S`. The plan says "MOOE scores only for AUC", but the named vehicle (`compute_metrics.metrics`) is rank-destructive for scores.
- **Why it matters:** if the read-out routes `S` through `metrics()` as it does for river/NSE `P`, every MOOE AUC cell of Table 1 is wrong, silently and plausibly (values still look like AUCs).
- **Recommended correction:** compute MOOE AUC on raw scores (`roc_auc_score(y == k, S[:, k])`, macro over classes present) or per-column rank-transform `S` before any shared metric code; never clip/normalise `S`.

### 3. Shared output dir keyed only by stream name: cross-list collision silently reuses the wrong probabilities
- **Severity:** P1
- **Finding status:** Missing information
- **Location:** `run_cpu.sh:9-10` (both lists write into the same `$R/P`), `run_trained_probs.py:24-26` (`dst = f"{out}/{stream}__{method}.npz"`, skip if `os.path.exists(dst)`)
- **Evidence:** main-stream tasks (data `MICE/data`) and confirmation tasks (data `~/pfn-runs/mice-confirm-cp-20261017/data`) share one output namespace. If any name appears in both `streams_main.txt` and `streams_confirm.txt`, the first task writes `P/<name>__<method>.npz` and the second **silently skips**, leaving the other data root's results under that name. No error is raised; the read-out cannot distinguish. (Within-list duplicates are benign: the runs are deterministic — river `seed=0`, NSE `random_state=len(h)`, RFF `seed=0` — and only waste CPU.) The two lists were not included in the package, so disjointness is unverified.
- **Why it matters:** wrong-stream probabilities enter Table 1 without any signal; only ARF/SRP have an accuracy reference to expose it, per PLAN's own reproduction check.
- **Recommended correction:** when building `tasks.txt`, assert the two name sets are disjoint (and each list unique), or tag the output name with the data root (e.g. `conf_<stream>__<method>.npz`).

### 4. CRLF in the stream lists (files under `/mnt/c`) fails every task
- **Severity:** P2
- **Finding status:** Missing information
- **Location:** `run_cpu.sh:9-10` (`while read -r s`)
- **Evidence:** `read -r` with default IFS strips spaces/tabs but not a trailing `\r`; xargs splits fields on blanks only, so `$1` becomes `name\r` and `np.load(f"{data}/name\r.npz")` raises FileNotFoundError. All 736 tasks would FAIL (visible in `progress.txt`/logs — loud, but only after full fan-out).
- **Why it matters:** the lists live on a Windows-mounted path; if they were written with CRLF the whole CPU run dies with no results, costing a day.
- **Recommended correction:** strip `\r` when building tasks (`s=${s%$'\r'}`) or `tr -d '\r' < file` at the top of the script.

### 5. NSE prediction runs every stored tree twice per batch (cost only, correctness neutral)
- **Severity:** P2
- **Finding status:** Confirmed issue
- **Location:** `run_trained_probs.py:62-64` (`pred[r] = m.predict(Z[q])` then `V = m._votes(Z[q], m.w)`)
- **Evidence:** `NSE.predict` is `self._votes(X, self.w).argmax(1)` (run_trained.py:76-77), so `m.predict` followed by `m._votes` executes each `h.predict` twice. `sklearn` tree `predict` is pure, so labels and model state are unaffected (and `pred == V.argmax(1)` always, including the all-zero-vote case where both give class 0) — this is the answer to "side effects of the extra calls": none for NSE (`_votes`), none for MOOE (`_mix` is pure; the assert reuses it), and the river path makes exactly one predict call per row as the original (`predict_one` delegates to `predict_proba_one`).
- **Why it matters:** doubles NSE prediction cost across 92 streams for nothing; trivial to remove.
- **Recommended correction:** `V = m._votes(Z[q], m.w) if m.h else np.zeros((B, C)); pred[r] = V.argmax(1)` (equal to `NSE.predict` in all cases) and drop the separate `m.predict` call (analogous to the MOOE path, which already derives pred from the same quantity).

## Checked and found correct (no finding)
- **Label equivalence:** NSE pred is literally `NSE.predict`; MOOE pred is `argmax(Z@W_mix)` with a runtime assert against `MOOE.predict`; river uses the same `max(p, key=p.get)` expression on the same dict as `Classifier.predict_one` (same tie-breaking), with the empty-dict caveat in finding 1. Smoke test (evidence.txt) reproduces per-batch acc bit-for-bit for all 8 methods on `grid_c5_b500_s20`.
- **Row alignment:** `j = i - B` / `r = slice((t-1)*B, t*B)` over batches 1..T-1 → output row j ↔ stream row j+B; all (T−1)·B rows written exactly once; `acc[t]` compares against `y[t*B:(t+1)*B]`; `acc[0]` NaN. Matches the original loops' semantics.
- **Class indexing:** `C = int(y.max())+1`, columns 0..C-1; river keys come from `learn_one(int(y[i]))`, NSE votes index `h.predict` of trees fit on `y`, MOOE has `C` outputs — all ⊆ 0..C-1.
- **NSE normalisation:** each classifier adds its full positive weight once per row, so row sums are equal; `V/sum` with uniform fallback matches PLAN ("votes / sum (uniform when the sum is 0)"), and argmax is preserved under the per-row scaling.
- **Atomic write:** `dst[:-4] + ".tmp.npz"` ends in `.npz` so `savez_compressed` does not append another suffix; `os.replace` is atomic on the home filesystem; skip-if-exists gives clean resume.
- **Runner wiring:** `bash -c` `$0/$1/$2` = data/stream/method matches the `echo` lines and the `--data/--streams/--methods` flags; `~` expands in the inner shell parse; the backslash-newline inside the quoted script is a line continuation for the inner bash (works); BLAS threads capped; slowest methods scheduled first.

## Points that can only be confirmed by running code
1. Whether any of the 5 river models returns an empty `predict_proba_one` on any of the 92 streams (trigger for finding 1) — after warm-up it should never happen, but that is not provable from the package.
2. Whether `export_table1_fill.py` computes MOOE AUC on raw `S` (finding 2) — that file was not attached.
3. Whether the two stream lists are CRLF-terminated and name-disjoint (findings 3, 4) — the lists were not attached and live paths are outside my scope.
4. Bit-for-bit acc equality beyond the one smoke stream — already covered by PLAN's registered read-out rule (differ > 1e-9 → report and discard that stream's probability metrics).
5. Whether any stream yields exact float64 proba ties where dict-order `max` and `np.argmax` on the float32 row pick different classes (`pred` vs `P.argmax` divergence; ECE inside `metrics()` uses `P.argmax`) — narrow, but observable by comparing `pred` with `P.argmax(1)` in the read-out.
