# Fable: which extra TFM backbones (2026-10-19 23:47-23:50, ~2.49 USD; web tools denied in -p mode)

## Question
You are the senior expert / decision adviser (read-only; you may use WebSearch/WebFetch for research). Answer in English: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence / Requires user approval. <= 600 words.

## Context
MICE paper: MICE/overleaf/tkde/main.tex (read the abstract, the method summary around lines 90-150, the experimental setup ~615-630, and the robustness paragraphs ~1020-1055 and ~1495-1530). MICE keeps a pool of stored contexts (segments) for a tabular foundation model (TFM) on drifting streams and recalls the context of a recurring concept; the theory is about recall under the posterior-predictive view of a TFM. Backbone: TabPFN v2 (4 ensemble members); robustness: TabICL (tabicl 2.2.0 = TabICLv2 checkpoint) on four held-out segments + a second backbone seed. Paper positioning (user rule): theory-driven; it does NOT need to show a universal advantage over all baselines.
The whole MICE is about to be rerun on 8 H800 (integrity rerun). The user now wants to ADD further TFM backbones as a robustness check (same protocol as the TabICL check: held-out sets, MICE + main comparison policies, no constant changed). Candidates: TabPFN v2.5, v2.6, 3, 3.5 (same `tabpfn` 9.0.0 package, ModelVersion enum; non-commercial weights), TabDPT (Apache-2.0, real-data pretraining, retrieval), Mitra-v2 (Amazon/AutoGluon, Apache-2.0), LimiX (16M/2M/LimiX-2; non-commercial). User's words: "我倾向于全部测试，看结果再说但是你最好问下fable 让他deepresearch 一下如果没必要那就不用测" (inclined to test all and decide after seeing results, but ask Fable to research deeply; if not necessary, don't test).
Also relevant prior work found: arXiv 2606.18677 "Bounded Context Management for Tabular Foundation Models on Stream Learning".

## Questions (research them)
1. Which candidates (if any) are scientifically necessary or clearly useful for MICE's claims, given the theory (does the recall mechanism depend on properties that differ across these models, e.g. context-length limits, retrieval inside the model (TabDPT), fine-tuning, per-row cost)? Which would be redundant?
2. Practical feasibility per candidate on streams with up to ~3000-row contexts, up to 69 features and up to 26+ classes (e.g. class limits, max features, availability of weights offline, licence for an academic paper).
3. Integrity: the user said "看结果再说". What reporting rule must be registered before running so that the choice of what to report is not made after seeing results?
4. Should arXiv 2606.18677 change anything (positioning or a needed baseline)? Read it if you can.
Recommend a concrete set (possibly empty) with reasons.

## Answer
**Note first:** WebSearch/WebFetch were denied this session, so arXiv 2606.18677 is unread and package facts for v2.6/3/3.5, Mitra‑v2 and LimiX‑2 are unverified. Evidence below is from the repo and my knowledge up to June 2026.

## Decision
Add **two** backbones, not seven: (A) **one** newest TabPFN checkpoint available in `tabpfn` 9.0.0, and (B) **TabDPT 1.3.1**. Skip v2.5/v2.6/v3 (redundant with A), Mitra‑v2 and LimiX (redundant in mechanism with TabICL, high integration cost, licence friction). Same protocol as the TabICL check: the 14 segments (first held‑out set, 4 of the third, 6 of the fourth), fixed segmentation, same policies, no constant changed, same four hypotheses. Register before launch; run after the integrity rerun finishes or on spare GPUs only.

## Supporting evidence
- **What the theory depends on.** The recall gain is the area between stored‑context accuracy and the backbone's learning curve; majority‑purity recall and the R‑divergence repair assume the TFM conditions on the *whole* context (posterior‑predictive view). Backbones therefore matter along two axes: learning‑curve speed (gain magnitude) and whether the whole context is used (mechanism).
- **TabDPT is the only non‑redundant candidate.** Its in‑model kNN retrieval makes the effective context query‑dependent, so it is the one model that stresses the whole‑context assumption. Its real‑data pretraining includes CoverType (repo note in `pdfs/research_notes/.../candidate_tables.md`), which the theory predicts should *shrink* the gain. That is a falsifiable, theory‑driven prediction rather than a universality claim. Feasibility is settled: ResetEval already runs it on every held‑out segment including 10‑class PokerHand (`ResetEval/code/reset_eval.py:55-76`, `ResetEval/results/queue_tabdpt.txt`), with a label‑remapping wrapper you can copy.
- **Newest TabPFN** answers the inevitable "old backbone" objection with a one‑line change to `ModelVersion` in `MICE/code/run.py:39`. Successive checkpoints share prior family, API and mechanism; four of them add four points on one lineage and no new test of the theory.
- **Mitra and LimiX** are synthetic/structured‑prior full‑context transformers, the class TabICL already represents. Mitra needs AutoGluon plumbing per fit call (MICE calls fit thousands of times per stream); LimiX needs its own repo and non‑commercial weights. Cost without a new scientific axis.
- Class limits are not binding: held‑out segments have at most 10 classes (second set was selected that way; PokerHand and Rialto are the maximum).

## Alternative options
- Minimal: TabDPT only (the mechanism test). Acceptable if GPU time is tight.
- Maximal (user's inclination): run all seven, but only as a descriptive appendix on the first held‑out set, registered as such. Not recommended: it costs time during an integrity rerun and buys reviewer‑proofing, not evidence.

## Key risks
- **Result‑contingent reporting.** Register now, in git, before any run: (1) backbone list and versions; (2) every started backbone is reported in the robustness paragraph and the pre‑registration appendix whatever the outcome; (3) exclusion only on result‑blind grounds fixed now (weights unavailable offline, class/feature error, OOM under the 28 GB cap, time per batch above a stated multiple of TabPFN v2), logged before any accuracy is read; (4) the same four hypotheses as TabICL; (5) optional directional hypothesis: the backbone with the faster grid learning curve (measured on dev seeds first) shows the smaller gain over reset on grid seeds 20/21.
- TabDPT pretraining leakage on CoverType inflates all policies equally; state it.
- Newest TabPFN weights may need a Hugging Face download on the H800 node.
- Contention with the integrity rerun.

## arXiv 2606.18677
Unread. Decide this **before** the rerun, because it may touch the main table, not the appendix. Rule: if it stores or recalls multiple past contexts, cite as concurrent work and add it as an in‑context baseline in the rerun. If it only manages one bounded context (eviction/selection), cite beside LTM; add as a fifth baseline only if code is public and fits the budget M=1000.

## Remaining uncertainty
Existence and limits of v2.6/3/3.5, Mitra‑v2, LimiX‑2; licences; content of 2606.18677.

## Confidence
Medium‑high on the two‑backbone choice; low on the unread paper and unverified versions.

## Requires user approval
Yes: which TabPFN version counts as newest, GPU scheduling relative to the rerun, and someone with web access reading 2606.18677.

# Sonnet review (23:51, 11 s)
1. **Date and version claim conflict:** The advice says its knowledge runs "up to June 2026" and calls v2.6/3/3.5 unverified. FACTS show tabpfn 9.0.0 has v2, v2.5, v2.6, v3, v3.5 and v3.5-fast, and the TabPFN-3.5 report is dated Sep 2026. Fix: drop the "existence unverified" caveat and name a specific checkpoint, v3.5 or v3.5-fast, before registering.

2. **Wrong licence reasoning:** TabPFN-3.5 weights are non-commercial, and the advice drops LimiX partly for that reason. It never flags the same constraint on its own pick (A). Fix: state the licence for A, and apply the same licence standard to every backbone considered.

3. **User instruction not followed:** The user leaned toward "test everything, see results", with the condition "skip if not necessary". The advice picks 2 of 7 on its own judgment and calls the all-seven option "not recommended". Fix: say plainly which of the user's backbones are skipped and why, and offer the all-seven descriptive run as a cheap, separately registered option (for example on spare GPUs). Or run all of them, since the user leans that way and the advice's own risk list shows the cost is only scheduling.

4. **CURE paper wrongly handled:** The advice says 2606.18677 is "unread" and defers it to someone with web access. FACTS give its content: a single bounded context with entropy-gated admission and redundancy-aware eviction, public code, not cited in the MICE paper. Its own rule then says to cite it beside LTM and add it as a fifth baseline only if the code is public and fits M=1000. Fix: apply that rule now. Cite CURE as concurrent work and decide on the baseline before the rerun starts, because the baseline would change the main table.

5. **Pre-registration gap:** Item (5), the directional hypothesis, is optional and depends on dev-seed learning curves. Nothing says those dev seeds must be disjoint from the evaluation seeds 20/21 or fixed before any run. Fix: register the dev seeds and the "faster curve means smaller gain" rule before the learning curves are measured. Then the hypothesis can't be chosen after seeing the results.

6. **Overstated feasibility claim:** The advice says feasibility is "settled" for TabDPT because ResetEval already runs it. ResetEval is a different pipeline, and MICE calls fit thousands of times per stream, so per-fit cost and time under the 28 GB cap have not been shown for MICE. Fix: run a result-blind smoke test of TabDPT inside MICE, covering time per batch and memory, before registering the exclusion thresholds.

# Executor facts checked by web (23:5x)
- arXiv 2606.18677 (CURE; Lee, Choi, Choi, Yoo; 17 Jun 2026): one bounded context, entropy-gated admission, redundancy-aware eviction; code github.com/morcellinus/CURE-ICML-FMSD. Not cited in MICE.
- arXiv 2609.17895 TabPFN-3.5 (15 Sep 2026); tabpfn 9.0.0 ModelVersion: v2, v2.5, v2.6, v3, v3.5, v3.5-fast.
