Role: senior research expert (read-only). One bounded decision before registration.
Question: Is the plan below a sound and sufficient answer to the reviewer's issue, with the method frozen? Specifically:
(1) Is selecting archive/snapshot capacity by timing on three prefixes the right matching rule, or should memory/rows
also be matched? (2) Is the real-stream subset (one stream per source, fixed rule) acceptable, or must all 29 be run?
(3) Any confound in timing pool policies whose call counts depend on pool occupancy? (4) Is the reporting rule right?
Files you may read: experiments/mice_tkde_control/PLAN.md (Round 9 section), experiments/mice_tkde_control/bench_resources.py,
MICE/code/run.py (PoolControl, MiceV1), MICE/logs/tkde_review/round12_rebuttal.md.
Plan:
# Round 13 plan v1 (resource comparison against the closest pool controls; method frozen)

Reviewer issue (round12_rebuttal.md, next issue, P1): MICE exceeds the archive by 0.30 points (aligned grid) and 0.07
(real) and trails the snapshot pool by 0.08 (real); its organisational benefit is fewer experts and calls (9.7 vs 14.0
per batch), but the latency benchmark excludes these two competitors, and calls with different context lengths need not
cost the same. Fix: keep MICE frozen; bounded accuracy-latency-memory comparison against archive and snapshot pools,
including smaller pool capacities selected using timings alone; aligned and shifted streams plus representative real
streams; establish where MICE offers a useful tradeoff.

A. Isolated benchmark (protocol of round 9 A, experiments/mice_tkde_control/bench_resources.py): same three prefixes
   (h4_airlines_d, h4_covertype_d, insects_abrupt_balanced, batches 1-300), three fresh-process repetitions with rotated
   order, GPU alone, 28 GB cap, checkpointing off. Policies: micev1000_500 (rerun, same session), arch1000_500 and
   snap1000_500 with pool capacity kmax in {12 (deployed), 8, 6, 4} (PoolControl kmax set after construction, nothing
   else changed). Two-level replay time amortised per batch for every pool policy, as for MICE in round 9.
   Reported: mean/median/p95/max s per batch, peak allocated/reserved GPU memory, peak RSS, TFM calls per batch,
   stored context rows per batch (exact for archive/snapshot; MICE: per-expert counts now recorded), accuracy.
B. Capacity from timings only, before any accuracy is examined: for archive and snapshot separately, k* = largest kmax
   whose amortised mean s/batch <= MICE's (same session); if even kmax=4 costs more, k* = 4 and reported as bracketing.
C. Accuracy (backbone seed 0, two-level replay), MICE vs archive k* and snapshot k* (kmax=12 results exist): 8 aligned
   grid streams (seeds 20/21, 30/100 centroids, 500/2000 blocks), 8 shifted streams (4.b), and one real stream per
   source (9): h4_airlines_d, h4_covertype_d, h4_poker_d, insects_abrupt_balanced, h2_rialto, elec2, h2_weather,
   h2_phishing, h2_spam (the benchmark segments where they exist, otherwise the only/first segment).
D. Definitions (round 9): "matches" = |mean difference| <= 0.1 points; "similar cost" = within a factor 1.25 in
   amortised mean s/batch. Reporting rule fixed now: if on any of the three stream groups an archive or snapshot pool
   at similar or lower cost is at least as accurate as MICE (difference <= +0.1 for MICE), abstract and conclusion say
   so. Per group: mean difference, per-stream values, moving-block bootstrap intervals (grid) and one-sided bounds (real).
E. Expected cost: A about 2-3 h alone on the GPU; C about 3-4 h with 3 workers. All configurations reported, including
   infeasible ones.
Answer: Decision (register as is / register with listed changes / redesign) / Supporting evidence / Alternative options /
Key risks / Remaining uncertainty / Confidence / Requires user approval. At most 6 points. No essays.
