**Finding 1**
- Severity: P2 (Suspected issue / missing information)
- Location: "Both capped pools also stay within the time of \method{} on each of the four grid streams (0.78 and 0.80 s on average)."
- Evidence: The summary gives only 4-stream *averages* (MICE 1.05, arch2 0.78, snap2 0.80), and the registered capacity rule covered only "all three prefixes" (real), not grid streams. The per-stream claim "on each of the four grid streams" is stronger than anything in the supplied material.
- Fix: weaken to "stay within the time of \method{} on average over the four grid streams (0.78 and 0.80 s vs 1.05 s)", or cite per-stream timings.

**Finding 2**
- Severity: P2 (Borderline overclaim)
- Location: "At the same pool size of 12, \method{} is within 0.3 points of ... the archive on the aligned grid" (and "matches ... a twelve-expert archive on the aligned grid")
- Evidence: k=12 aligned archive delta is exactly +0.30 — at the stated bound, not strictly *within* 0.3 (rounding could hide a value >0.3).
- Fix: "within 0.3 points (0.30)" or "within about 0.3 points"; or give the unrounded value.

**Finding 3**
- Severity: P2 (Omission of an unfavourable listed result)
- Location: "more accurate ... on average over nine real streams (by 0.35 and 0.27)" / "on a source-balanced subset of nine real streams, by 0.35 and 0.27 points"
- Evidence: the summary's win rates for that subset are 7/9 (archive) and 6/9 (snapshot), i.e. the control wins on 2 and 3 streams; the added text states "all eight streams" for the grid but never reports the 7/9 and 6/9 counts.
- Fix: append "(positive on 7/9 and 6/9 streams)" — the "on average" phrasing and CIs already keep the claim itself accurate.

No contradictions found: sign/direction claims check out (archive k=12 shifted is indeed 2.88 points above \method{} since Delta = MICE − control = −2.88; level with snapshot on shifted +0.00 [−0.64,+0.47]; timings 1.11/0.93/0.98/1.27/1.38/2.49/2.84 and 1.05/1.58/1.63 all match), and unfavourable results (shifted archive −2.88, real snapshot −0.03, shifted snapshot 4/8, snap4 over MICE's time) are acknowledged.
06:14:55
