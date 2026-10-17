# MICE — real-stream confirmation of detected segmentation (pre-registration, committed before any run)

Requested by the user on 2026-10-17 (plan reviewed by Fable on the user's side; amendments by the user the same day:
H1 is an aggregate test; data = CIC-IDS2017 and Bitcoin Heist; Bitcoin Heist handled as proposed below). New data,
chosen by the user. Everything below, the evaluator `analyse.py` and the data builder `make_streams.py` are committed
and pushed before the first task starts. Each method runs once per segment; nothing is changed after a result is seen.

## Why
The method of the paper is now MICE with detected segmentation (`mice_cp`). The real-stream confirmation sets so far
(the fourth held-out set, pre-registration I) were registered for fixed segmentation. This set tests the detector on
real streams no method has loaded, including hypotheses that fail when the detector fails (H1, H5).

## Method (frozen; MICE/code/run.py unchanged since 2026-10-15 15:14)
- `micecp1000_500`: MiceCP, B = 100 rows per batch, labels one batch late, M = 1000 rows, segments of 500 rows when no
  change is detected; detector CPSegments SIG = 300, H = 3, R = 5, RMIN = 2, DELTA_CP = 1e-3, LMIN = 300 (a segment
  closed at a detected change holds at least 300 rows; one closed without a change holds 500), TRIM = 0; pool
  delta = 0.02, kmax = 12; fast level eta = 10; slow level replayed with reweight.simulate2(outer = brier, scale = 0.5,
  temper = True) (discount 0.9, step 1, Brier scale 1/2).
- Backbone TabPFN v2 (four estimators), backbone seed 0, `OMP_NUM_THREADS=1`.
- Comparators (all run): fifo1000, ltm1000_75, ddm1000 (Reset), winens1000 (Window ensemble), micev1000_500 (MICE with
  fixed 500-row segments, the previous method), mice_cp_nopool (replay of the mice_cp cache restricted to its window
  experts, keys < 0; no extra run), ARF and SRP (river, CPU; accuracy only, descriptive).
- Probabilities: mice, mice_cp, mice_cp_nopool, fifo and winens from the expert caches; ddm and ltm recorded per row by
  MICE/code/run_probs.py (through run_task.py). ARF and SRP store no probabilities.

## Data (raw files in ~/pfn-runs/raw-newdata-20261017; sha256 in checksums.txt; manifests cc_manifest*.csv)
Never loaded by any script of this repository before 2026-10-17 (no method, baseline, benchmark, tuning or detector
development). Only label counts and the row layout were inspected before this registration (to choose the segments
as below); no method was run on these rows.
- **Bitcoin Heist** (UCI 526, bitcoinheist.zip, 2,916,697 rows, 1.42% ransomware addresses). Rows sorted by
  (year, day), within a day in a random order (default_rng(0) keys): the file lists all 41,413 ransomware rows first,
  so file order would put each day's ransomware rows at the start of the day (a label-driven pattern every ~10
  batches; found before any run, Fable's check). Binary label (white vs any ransomware family); features length, weight, count, looped,
  neighbors, income. Segments: the first 100,000 rows of each year 2013–2017 (`cc_btc_<year>`). The years were chosen
  from the label counts per year (2011, 2012 and 2018 have < 0.2% ransomware, so every method is near the majority
  rate there). Ransomware share per segment: 0.39%, 4.78%, 0.44%, 3.70%, 2.23% (majority rates 95.2–99.6%).
- **CIC-IDS2017** (MachineLearningCSV.zip, md5 4f83860a… as published; 2,830,743 rows, 8 day files). Days Tue–Fri in
  capture order, rows in file order (Monday is benign only). 15 labels grouped into 9 classes (BENIGN, DoS, DDoS,
  PortScan, Bot, WebAttack, Patator, Infiltration, Heartbleed); 69 features (78 numeric columns minus the duplicate
  "Fwd Header Length.1" and the 8 columns constant over all files); ±inf and NaN set to 0. Segment per day: the aligned
  100,000-row block with the largest min(#BENIGN, #attack) (`cc_cic_<day>`): Tue block 0 (Patator 7.9%), Wed block 0
  (DoS 35.7%), Thu block 0 (WebAttack 2.2%), Fri block 6 (DDoS 51.6%). Every segment is binary after grouping. CIC rows are in genuine capture order (labels alternate in thousands of runs
  per file). The most-mixed rule picks the block most likely to contain an attack onset or end, where a change detector
  should help: on CIC the test is tilted towards detection-based methods (mice_cp, ddm), and the CIC segments are not
  representative of the days. The Bitcoin year rule only excludes years where every method sits at the majority rate.
- Labels are re-indexed per segment to the classes present. n = 9 primary segments, s = 2 sources; ⌈2n/3⌉ = 6.
  All nine primary segments are binary: this set says nothing about the multi-class behaviour of the detector (the
  supplementary PokerHand segments have 8 and 9 classes).
- **Supplementary** (reported, in no hypothesis): PokerHand rows [500k, 600k) and [600k, 700k) of
  MICE/data/external_cdd/poker.csv (`cc_poker_f`, `_g`), after the fourth held-out set's [300k, 500k).
  Airlines and CoverType have fewer than 100,000 unused rows and are not used. No segment is shorter than 50,000 rows.

## Hypotheses (primary segments; "above" = strictly greater; ties do not count)
Accuracy = mean over scored batches (batch 0 is warm-up). Bootstrap = moving blocks of 20 batches, 10 000 resamples,
default_rng(0), one-sided 95% lower bound = 5th percentile (as MICE/code/noninferiority.py).
1. **Not worse than fixed segmentation (aggregate)**: mean over the 9 segments of (mice_cp − mice), every segment
   resampled by moving blocks of its per-batch differences (segments fixed, so the inference is about these nine
   segments, not about a population of segments): lower bound > −0.2 points.
2. **Safe against FIFO**: on every segment the lower bound of the mean per-batch difference mice_cp − fifo > −0.3 points.
3. **Not worse than the better reset/window baseline**: on every segment mice_cp − max(fifo, ddm) ≥ −0.5 points.
4. **Best overall**: within each source the mean accuracy of mice_cp is above the mean of each of fifo, ltm, ddm,
   winens; and mice_cp is above all four on at least 6 of 9 segments.
5. **The pool is used**: mice_cp above mice_cp_nopool on at least 6 of 9 segments.
Descriptive (no decision): the H1 and H2 bounds with blocks of 50 batches, default_rng(1) (attack bursts can be longer than 20
batches); F1, AUC, ECE, half Brier, log-loss of every method with probabilities; mice_cp − mice per
segment; ARF, SRP accuracies; the supplementary segments.

Expected difficulty, stated before the run: on the two Bitcoin Heist segments with < 0.5% ransomware all methods are
close to the majority rate and differences of a few rows decide H4 and H5 there; exact ties count as failures (the
strict rule is kept). CIC Wednesday and Friday (DoS, DDoS) are probably separable by every method (low power).

## Use of the result
- All five met: the paper states that detected segmentation passed every pre-registered test on the new confirmation
  set; the fixed-segmentation held-out sets become supporting evidence.
- Any not met: the paper states which hypothesis failed and that the real-stream confirmation of the detected method
  did not pass it; listed in the limitations.

## Execution
- Root ~/pfn-runs/mice-confirm-cp-20261017 (data/ built by make_streams.py; tasks.txt = this directory's tasks.txt,
  66 GPU tasks, primary segments first). Workers: this directory's worker.sh (copy of experiments/mice_r14/worker.sh),
  2 workers, 3 if stable (env/EXPERIMENT_SCHEDULING.md); `MICE_CKPT_EVERY=10`. ARF/SRP: run_task.py with
  ~/pfn-venvs/stream (CPU), in parallel.
- A GPU fault kills one process; the worker restarts it in a new process. micev/micecp resume from their atomic
  checkpoint; fifo, ltm, ddm and winens have no checkpoint and restart from batch 1 (deterministic; still one run).
- Evaluation only when every task is complete: `python analyse.py ~/pfn-runs/mice-confirm-cp-20261017` →
  MICE/results_paper/confirm_detected/ (acc.csv, metrics.csv, hypotheses.csv, summary.csv; fractions in acc/metrics,
  percent and points in summary). A README with run times, faults and deviations is written afterwards.
- Expected GPU time (from the fourth held-out set: 1.2–2.5 GPU hours per 100,000-row segment for these six runs;
  CIC-IDS2017 has 69 features and may be slower): about 13–30 GPU hours, 7–15 hours with 2 workers.
