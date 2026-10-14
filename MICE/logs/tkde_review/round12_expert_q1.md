Role: senior research expert (read-only). One bounded decision about a registered diagnostic, before it is run.

Context: MICE stores fixed 500-row segments as in-context experts. In 4.b, 8 grid streams were preceded by 200 extra rows
of the first concept, so every concept boundary lies 200 rows into a segment; MICE - DDM on matched batches fell from
the aligned value by 6.76 points on average (8/8 negative) and the archive beat MICE on all 8. The reviewer says the
prefix also changes initial history, so 4.b does not separate segment impurity from history, and that the method
depends on alignment. The user chose to diagnose first with the method unchanged.

Registered design (experiments/mice_tkde_control/PLAN.md, section "Round 12"; read it): rerun MICE and the archive on
the same offset streams with the segment origin at row 200 (oracle phase), giving three conditions A (aligned), O
(offset, origin 0), P (offset, origin 200); C_imp = P - O, C_hist = P - A; H1 P: MICE-DDM > 0 on >=7/8, mean >= +1;
H2 mean C_imp >= +5.0; H3 |mean C_hist| <= 1.0. Code: MICE/code/seg_origin_run.py, MICE/code/check_seg_origin.py,
MICE/code/check_offset.py, MICE/code/run.py (MiceV1, PoolControl, run). Verified: concept boundaries at rows 200+kL in
all offset streams; patched objects start with closed=200.

Question: Is this design valid for separating segment impurity from initial history, and are the hypotheses and
thresholds sound? Any confound or code-level mismatch with the registration that must be fixed before running?

Answer: Decision (run as is / run with listed changes / redesign) / Supporting evidence / Alternative options / Key
risks / Remaining uncertainty / Confidence / Requires user approval. At most 6 points. No essays.
