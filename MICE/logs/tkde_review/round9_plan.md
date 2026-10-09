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
