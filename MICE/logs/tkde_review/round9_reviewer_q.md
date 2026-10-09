You are the TKDE reviewer. In this round you raised: "The accuracy-resource tradeoff is not established: no
latency, throughput or peak memory on stated hardware, no comparison with stronger FIFO/window baselines under
comparable memory or time; 'free to store and free to recall' overstates." The paper is in this directory. The
authors propose (wording fix already applied to the closure cost; 'free' will be replaced by 'requires no additional
training'):

# Round 9 — plan (Claude, 2026-10-09)

Judgement: accepted. The paper states a 5-18x time factor but no measured latency, throughput or memory on stated
hardware, and no baseline given a comparable budget; "free to store and free to recall" overstates (only no training
is free). Method frozen.

1. Wording: "free to store and free to recall" -> "requires no additional training"; distinguish the per-context
   limit M = 1000 from total retained data (MICE: windows of 100/300/1000 rows plus at most 12 stored experts of at
   most 1000 rows, i.e. at most 13 400 context rows in total; up to 15 TFM calls per batch plus 3 per segment close).
2. Isolated resource benchmark (new run, registered before it starts; after the running control finishes, GPU
   alone, one process): hardware stated (RTX 5000 Ada 32 GB, WSL2, 20-core CPU), frozen TabPFN v2 with 4 estimators.
   For MICE (micev1000_500), FIFO with M = 1000, 5000, 12 000 and the window ensemble: end-to-end seconds per batch
   (including segment processing), batches per second, peak GPU memory (torch max allocated) and retained context
   rows, on three real streams of different size and dimension (one Airlines, one CoverType, one INSECTS segment),
   the first 300 batches each. Timing from the existing concurrent runs is reported only as descriptive.
3. Budget-matched baselines (new runs, registered): FIFO with M = 5000 and M = 12 000 on the 29 real streams (backbone
   seed 0), i.e. one context with as many rows as MICE may retain in total, and roughly its per-batch inference
   work. Reported per stream and averaged: MICE - FIFO(M) with the RQ3 block-bootstrap lower bounds; accuracy versus
   measured cost (seconds per batch, peak memory) as a table/plot of operating points (FIFO 1000/5000/12 000, window
   ensemble, MICE). Descriptive criterion fixed before the run: none for "MICE wins"; the result is reported either
   way, and if a larger FIFO matches or beats MICE at similar cost the paper says so in the abstract and conclusion.
4. Not done: changing MICE's budget (would change the method).

## Plan v2 (after the expert, round9_expert_a1.md, and a feasibility test), supersedes items 2-3 above
Feasibility (shared GPU, TabPFN v2, CoverType, 100 query rows): context 1000 rows 0.87 s/call (peak allocated 145
MiB, reserved 302), 5000 rows 2.7 s (578/1378 MiB), 13 400 rows 10.2 s (1555/4174 MiB). MICE runs at about 1-1.5 s
per batch. A capacity-matched FIFO is therefore several times slower than MICE, not inference-matched.
Accepted from the expert: capacity ceiling 13 400 context slots (windows 100+300+1000 + 12 x 1000), called
"context-capacity matched"; closure cost corrected in the paper (2 cross-fitted calls + one per stored expert, at
most 29 calls on a closing batch); timing must cover the reported predictor (expert predictions + two-level rule).
A. Isolated benchmark (GPU alone, after the running control), registered: streams h4_airlines_d, h4_covertype_d,
   insects_abrupt_balanced; batches 1-300 (claims restricted to this prefix); policies MICE, FIFO 1000, FIFO M*,
   FIFO 5000, FIFO 13 400, window ensemble; three fresh-process repetitions in rotated order; CUDA-synchronised
   timing of each batch (prediction + update, segment processing included; MICE also its two-level rule), reported as
   mean, median, p95, max, closing vs non-closing batches, and rows per second; peak allocated and reserved GPU memory,
   peak process RAM, retained context rows and pool occupancy. Accuracy on the same prefixes (paired). MICE's expert
   predictions are checked bit for bit against the frozen cache.
B. Time-matched FIFO on all 29 real streams: M* is chosen before any accuracy is seen, by an accuracy-blind rule on
   the benchmark timings of A: the smallest M in {1500, 2000, 3000} whose median seconds per batch is at least MICE's.
   Then FIFO M* runs on the 29 streams (backbone seed 0). Reported: MICE - FIFO M* per stream, mean, two-sided 95% and
   one-sided block-bootstrap bounds (approximate, fixed streams).
C. Definitions fixed now: "matches" = |mean difference| <= 0.1 points; "similar cost" = median seconds per batch within
   a factor 1.25. If FIFO M* is at least as accurate as MICE at similar or lower cost, the abstract and conclusion say
   so. FIFO 5000 and 13 400 are reported only on the benchmark prefixes, as costlier operating points.

Does this plan satisfy your request? Answer: Verdict (Satisfies / Partly satisfies / Does not satisfy); what must be
added or changed before the authors run it (at most 3 items).
