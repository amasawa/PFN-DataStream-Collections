> auditor · mimo-v2.6-pro
I'll audit the round-9 revision against the attached CSVs, scripts and registration. First I need the parts of `main.tex` beyond line 729 (the cost paragraph, tables, conclusion, Limitations).
✱ Grep "Cost and a larger window|tab:cost|tab:fifo3000|Limitation|Conclusion|14\.6|five times|8 of the 29|0\.31" in . · 15 matches
→ Read main.tex [offset=730, limit=400]
I have the body text and data files. Now I'll read the appendix table environment and double-check the per-source averages against the CSV.
✱ Grep "fifo3000|FIFO 3000|larger window|cost-matched|2\.5|five times|14\.6|0\.31|21 of the 29|8 of the 29" in main.tex · 20 matches
→ Read main.tex [offset=1130, limit=141]
All attached files reviewed against each other: `main.tex` (abstract, §RQ4 cost paragraph, `tab:cost`, `tab:fifo3000`, conclusion, Limitations), `tab_cost_rows.tex` / `tab_fifo3000_rows.tex`, `bench_cost_policy.csv`, `bench_cost_runs.csv`, `bench_accuracy_runs.csv`, `m_star.json`, `fifo3000_real*.csv`, `registration_r9.md`, `bench_resources.py`, `analyse_bench.py`, `fifo_m_real.py`, `make_cost_tables.py`.
## Verified as matching (no finding)
- **tab:cost** (all 8 rows × 12 columns) matches `bench_cost_policy.csv` + `bench_accuracy_runs.csv` under `make_cost_tables.py`’s formatting, including memory as `*_mib/1024`: MICE 1.07 / 0.95 / 2.12 / 2.66 / 99 / 0.2 / 1.0 / 1.8 / 65.3 / 95.4 / 78.1 down to Window ens. 0.53 / 0.50 / 0.65 / 1.80 / 192.
- Closing vs non-closing: `closing_mean_s` 1.6855 → 1.69, `nonclosing_mean_s` 0.9119 → 0.91; weighted check (60 closing / 240 non-closing batches) reproduces the 1.0667 amortised mean.
- Text: 1.07 s (MICE), 0.22 (FIFO 1000), 0.42 (FIFO 3000), 1.91 (FIFO 13 400) ✓; **2.5×** (1.0667/0.4231 = 2.52) ✓; **about five times** (1.0667/0.2178 = 4.90) ✓; **14.6 points** (78.07 − 63.50 = 14.57, the 13 400-row window on INSECTS) ✓.
- MICE most accurate on the INSECTS prefix (78.07 vs 77.66 window ens.) ✓; FIFO 3000 ahead of MICE on the Airlines and CoverType prefixes at lower cost ✓.
- **8 of 29** streams with positive MICE−FIFO3000 point estimate ✓; **14** two-sided intervals wholly below zero, **6** wholly above ✓; **+0.31 [+0.09, +0.49]** matches `fifo3000_real_aggregate.csv` (0.3077, 0.0850, 0.4947) and the `tab:fifo3000` mean row (83.82 / 83.51) ✓; **21 of 29** in abstract, conclusion and Limitations ✓; “four INSECTS +3.3 to +5.5” (3.34, 4.91, 5.17, 5.49) and “Rialto +6.9” (6.94) ✓; Airlines source mean −1.095 → −1.1 ✓; Weather −0.539 → −0.5 ✓.
- **Rule B for M\***: none of {1500, 2000, 3000} within a factor 1.25 of 1.067 (ratios 0.25–0.40), so M\* = 3000 as closest, reported as not cost-matched (“about 2.5 times cheaper”) — matches `m_star.json` and the registration note ✓.
- **Bootstrap in `fifo_m_real.py`**: correct. Differences formed per batch and then resampled (paired indices); block length 20, with `n//2` only when `n < 40` (all 29 streams have `n ≥ 61`, so all use 20); `ceil(n/b)` blocks drawn uniformly from starts `0..n-b`, concatenated and truncated to `n`; 10 000 resamples, `default_rng(0)`; percentile two-sided 95% and one-sided 5% bound; aggregate = mean over independently resampled streams. No issue.
- Wording is consistent across abstract, conclusion and Limitations and does not understate the unfavourable result (21 of 29, “only because of … INSECTS and Rialto”, “value … lies in sharply drifting or recurring streams, not in general”).
## Findings
**1. P2 · Confirmed issue · Location: `main.tex` line 867 (source means in the cost paragraph)**  
Evidence: `fifo3000_real.csv` gives Phishing `d = −1.4495` (→ −1.4 at 1 dp) and PokerHand mean `d = (−2.6957 + 0.0841 − 2.1371 − 1.0000 − 1.9930)/5 = −1.5483` (→ −1.5). The text states −1.5 and −1.6. Both match only via double rounding of the 2-dp table entries (−1.45→−1.5, −1.55→−1.6 with half-up). Airlines (−1.095→−1.1) and Weather (−0.539→−0.5) are correct either way.  
Why it matters: both errors are in the direction of overstating the larger window’s advantage; a reviewer recomputing from `tab:fifo3000` or the CSV gets a different number.  
Recommended correction: use the once-rounded exact means (Phishing −1.4, PokerHand −1.5), or state explicitly that source averages are taken from the rounded per-stream values.
**2. P2 · Suspected issue · Location: `main.tex` abstract (lines 70–73) and conclusion (lines 953–955) vs `registration_r9.md` part C**  
Evidence: part C requires that “if on the benchmark prefixes a FIFO is at least as accurate as MICE at similar or lower cost, the abstract and conclusion say so.” Per prefix this occurs: FIFO 3000 beats MICE on the Airlines prefix (66.59 vs 65.33) and the CoverType prefix (95.72 vs 95.43) at 0.42 vs 1.07 s/batch. The body reports this split (lines 869–871), but the abstract and conclusion report only the 29-stream result (21 of 29) plus the cost ratio. On the mean over the three prefixes MICE is still ahead (79.61 vs 78.56), so under an aggregate reading the trigger does not fire.  
Why it matters: the registration’s reporting rule is not met under the per-prefix reading; the unfavourable result is prominent either way, so this is letter vs spirit.  
Recommended correction: if the per-prefix reading was intended, add one clause to the abstract and conclusion (e.g. “and on the Airlines and CoverType benchmark prefixes a larger window is more accurate at lower cost”); otherwise record in the registration log that the trigger was evaluated on the mean over the three prefixes and did not fire.
No other verified issues within the reviewed scope.
## Points that can only be confirmed by running code
1. Chronology: that `m_star.json` was written before any accuracy was examined (`analyse_bench.py` only asserts the file exists at the accuracy stage, not when it was written).
2. Batch alignment in `analyse_bench.py accuracy()`: MICE averages over `sorted(simulate2)` keys, FIFO over `acc[1:]`; unlike `fifo_m_real.py` (which pairs via `t = sorted(a)`), the prefix accuracy columns are not explicitly paired. If `simulate2`’s key set is not exactly `{1,…,300}`, the paired prefix accuracies cover slightly different batches.
3. Reproduction of the bootstrap intervals (per-stream and the aggregate `[+0.09,+0.49]`) from the caches and `fifoM/*.npz`.
4. `records()` discarded-run filtering against the actual `bench.jsonl` (the `disc` set is built from entries with a `"discarded"` key).
5. Whether the closing-batch mask `((t*100) % 500 == 0)` in `analyse_bench.py` matches `run.py`’s actual segment-close timing (the weighted 60/240 check is internally consistent, but not a check against `run.py`).
6. That `identical_to_frozen=True` is a complete bit-identity check of every cached expert prediction (`np.array_equal` over cache entries) for all three repetitions.
7. That the benchmark was actually isolated (GPU idle, one process at a time) as registered — not derivable from the analysis artefacts.
