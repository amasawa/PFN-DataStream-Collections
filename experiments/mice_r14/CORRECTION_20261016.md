# Correction to PLAN.md (2026-10-16; PLAN.md itself is not edited)

PLAN.md states that test data seeds 40-43 were "never used; independent concept draws". This is wrong for seeds 40 and
41: the registered oracle test of the recall theorem (round 11, run 2026-10-14, MICE/code/oracle_recall.py) used the
same generator with seeds 40 and 41, so the concept draws are the same, and its 500- and 2000-row-block streams are
row-identical to the corresponding round-14 test streams after the prepended offset rows. The oracle test used oracle
boundaries and concept identities, involved no change detector and tuned nothing; the detector constants were set on
development seeds 0 and 1. The reuse was overlooked when PLAN.md was written and was found by the MiMo audit of the
paper revision after the test had been evaluated.

Handling (Codex gpt-6-astra xhigh, 2026-10-16, MICE/logs/tkde_review/round14_codex_integrity.md): the registered
verdicts stand as computed on all 72 streams, with the deviation disclosed in the paper; a seeds-42/43 split is
reported as post-hoc sensitivity only; a separate confirmation on unused seeds 50-53 is registered in PLAN_CONFIRM.md.
