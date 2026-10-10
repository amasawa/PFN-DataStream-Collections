---
name: anti-defensive-writing
description: Rewrite or edit a research paper so every sentence advances the argument; delete sentences that only pre-empt criticism, and frame the paper as method + elegant theory + experiments that support both (not leaderboard-chasing). Use when writing, revising or reviewing a paper with this user, especially with Codex/MiMo.
---

# Anti-defensive writing (user's rules, 2026-10-10)

## Framing
- A paper presents **a method with an elegant theory, and experiments that support the method and the theory**.
- It does **not** need to show that no cheaper or better method exists. "General and robust superiority over every
  baseline" is score-chasing, not the goal.
- Organise the argument around what the theory predicts (when the method helps, when it does not), and place each
  experiment where it tests a prediction. Results outside the method's favourable regime are evidence for the
  theory's conditions, not apologies.

## The sentence test
User's rule, verbatim: **"如果某句话的作用只是防止被质疑，而不是推进论证，请删除。"**

Delete every sentence whose **only** role is to pre-empt criticism rather than advance the argument.

Keep a sentence if it
- states a result (a number, a comparison, an outcome),
- states a condition under which a claim holds (assumptions, scope, sample, hardware, what a bound covers), or
- gives a definition or describes the method.

Delete or move it if it
- anticipates an objection without adding information ("this does not show ...", "we therefore only claim ...",
  "the statements above compare ...", "whether X holds was not tested"),
- repeats a verdict or caveat already stated,
- narrates the review or registration history in the main text ("in response to review", "registered before the
  run", "we measured X and only then ...").

Registration, development history and provenance go into **one appendix section**; the main text may point to it.

## Guardrails (do not cross)
- Never delete an unfavourable result. Place it where the theory predicts it (conditions of validity) or in the
  limitations, and never keep a main-text claim that it contradicts.
- Keep load-bearing conditions even if they sound cautious: theorem assumptions, what a bound covers (e.g. Brier
  versus accuracy), bootstrap/sample scope, that controls are complete policies with different budgets, bounds versus
  measurements.
- Distinguish "the theory predicts X" from "X falls outside the theory's premise" and from "consistent with the
  theory" when the quantity was not measured.
- Changing a registered reporting rule (for example what must appear in the abstract) is the user's decision and is
  recorded as such.
- Numbers come from scripts; after rewriting, have MiMo (auditor) check that every number is unchanged.

## Workflow with the agents
1. Ask the Codex expert (read-only) for: a theory-driven outline, an exhaustive list of defensive sentences with line
   numbers and delete/move decisions, the load-bearing sentences that must stay, and a rewritten abstract and
   contributions using only existing numbers.
2. Verify each item yourself (Codex can be wrong), then rewrite in passes, compiling after each.
3. MiMo audit: numbers unchanged, no unfavourable result lost, no contradicted claim left.
4. Codex reviewer reads the rewritten paper.
