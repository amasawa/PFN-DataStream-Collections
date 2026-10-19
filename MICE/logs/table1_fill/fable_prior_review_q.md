# Fable review of the work already done for the clean MICE rerun on the H800 cluster (user request 2026-10-20:
# "之前任务也让fable审核一下")

Read these files in experiments/clean_rerun_mice_h800/: ACTIVATION_20261019.md (binding; user decisions), PLAN.md,
HANDOFF.md (what the Mac mini Claude Code session will execute on the cluster), make_bundle.sh, MANIFEST.md,
REGISTRATION_P2_20261020.md, and rerun.py (runner). Do not read tasks*.jsonl in full (2828 + 2358 lines); grep it if
needed. Already reviewed: ACTIVATION (Fable + Sonnet), P2 (Fable, MiMo, Sonnet). Not yet reviewed by you as a whole:
the P1 path end to end (HANDOFF steps, bundle contents vs what the tasks need, runner behaviour on the cluster) and
the consistency of the whole package.

Question: as the decision maker, what would make this rerun fail, give results that cannot be reported, or let a
reviewer call it unfair or not clean? Consider: an executor on a cluster it has not seen (Slurm, no internet on compute
nodes perhaps), inputs missing from the bundle, order of phases, determinism probe and acceptance, where results are
returned, and anything in HANDOFF that contradicts ACTIVATION.

At most 8 findings, most severe first, each: Severity (P0/P1/P2), Location (file:line), Evidence (quote), Why it
matters, Correction. Then one line: overall verdict (ready to hand over / ready after fixes / not ready). Answer in
Chinese. No essay.
