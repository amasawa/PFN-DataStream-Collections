# Follow-up to Fable on CURE tau (one decision). Your first answer: MICE/logs/table1_fill/fable_p3p4_a.md.
Sonnet review: MICE/logs/table1_fill/sonnet_p3p4.md. Executor verification of Sonnet's points:
- Point 3 (warm-fill) and 5 (Mitra classes) do not hold: warm_fill_ratio = 1.0 in CURE's __init__; _meta_score returns
  entropy only; the 10 P3 segments have at most 9 classes (h3_poker_b 9, h4_poker_e 9).
- Point 4 (slice P to the context classes before the entropy) and 6 (signal stale up to one batch; log the long-bank
  admission rate; state it) are accepted.
- Point 1 holds: option (b) needs CURE dev runs before tau exists, so it must be a two-stage registration (procedure +
  tie rule registered and pushed first, dev runs, then the frozen tau registered before any test run), as P2b does for
  the other baselines.
- Point 2 holds and is new: 7 of the 92 Table 1 streams come from datasets with a published CURE tau:
  h2_weather = NOAA weather (18159 rows, CURE "noaa", tau 0.4), h2_rialto (CURE "rialto", 0.1), and five PokerHand
  streams h2_poker, h3_poker_b/_c, h4_poker_d/_e (CURE "poker", 0.3). Agrawal: CURE's agr_a is the MOA abrupt Agrawal
  stream; ours (agrawal_s10..14) are our own generator streams. The five development streams of the Table 1 baselines
  are elec2 and four INSECTS streams (no published tau). Those taus were tuned by CURE's authors with TabICL, row by row.

Decide the tau rule, one of:
 (A) one tau for all 92 streams, from (b) dev selection over {0.1,0.2,0.3,0.4} (two-stage registration);
 (B) published per-dataset tau on the 7 matching streams, (b) dev-selected tau elsewhere;
 (C) one fixed tau = 0.3 everywhere (no dev runs; ACTIVATION "no tuning" kept literally);
 (D) other.
Consider: ACTIVATION says "CURE's published defaults; no tuning; if undefined, value and reason fixed before any run";
user approval is needed for any change to that sentence; the published taus were tuned on (possibly the same) data
with another backbone and protocol. Format: Decision / Supporting evidence / Alternatives / Key risks / Confidence /
Requires user approval. At most 15 lines.
