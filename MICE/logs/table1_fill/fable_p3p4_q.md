# Question to Fable (expert / decision maker): settings of P3 (extra backbones) and P4 (CURE)

Read: experiments/clean_rerun_mice_h800/PLAN_P3_P4_draft.md (the draft, with checked facts), and
experiments/clean_rerun_mice_h800/ACTIVATION_20261019.md sections "Extra backbones" and "CURE" (binding rules, user
decisions). MICE/code/run.py lines 25-50 (TFM class). Do not read anything else unless needed for one specific point.
Web tools are not available; rely on the facts in the draft.

Context: MICE = mixture of in-context experts over a frozen tabular foundation model; theory-driven paper. P3 is a
robustness check (same protocol as the existing TabICL check, all listed backbones reported). P4 adds CURE (concurrent
work, ICML workshop, code read in full; summary in the draft) as a main-table baseline with published defaults and no
tuning; its tau has no published default for other data (it was set per dataset, 0.1-0.4, with TabICL).

Decide, each briefly:
Q1. TabPFN v2.5/v2.6/v3/v3.5: n_estimators = 4 (as v2, TabICL) or the package default "auto"? v3.5 or v3.5-fast?
Q2. Mitra-v2: fine_tune = False (frozen, as MICE's "same frozen backbone") or its default fine_tune = True?
Q3. LimiX: LimiX-2 (400M) or LimiX-16M; no-retrieval config?
Q4. CURE tau: option (a) median 0.3, (b) select on the 5 dev streams from {0.1..0.4}, (c) report all four, (d) other.
    ACTIVATION says "published defaults; no tuning; if undefined, value and reason fixed before any run".
Q5. CURE adaptation to batch arrival (draft item 7): is it faithful, or is there a better mapping?
Q6. Anything in the draft that would make a reviewer call P3 or P4 unfair or misleading (one or two points at most).

Answer format: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence /
Requires user approval. Short; no essay.
