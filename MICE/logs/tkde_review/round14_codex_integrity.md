# Round 14 integrity arbitration (Codex gpt-6-astra, xhigh, 2026-10-16 09:36–09:37)

## Prompt
Integrity arbitration (read-only; answer from the evidence below, no exploration needed).

Decision question: how must a misstatement in a frozen registration be handled and reported, given that the registered
test has already been run and evaluated?

Facts
- Registration (committed and pushed before any test run, 2026-10-15) of a test of a changed stream-learning method:
  72 synthetic streams, "data seeds 40-43 (never used; independent concept draws)", 30/100 centroids, three block-length
  regimes, three random row offsets prepended per stream. Primary criterion C1 per regime (24 streams each): mean gain
  over reset >= +1.0 points, >= 18/24 positive, hierarchical-bootstrap 95% lower bound > 0. All criteria were met
  (per regime +5.17, +1.48, +1.91; lower bounds +4.59, +1.22, +1.74).
- An auditor found that seeds 40 and 41 were used on 2026-10-14 in an earlier registered "oracle" test of the paper's
  recall theorem: same generator, so the same concept draws (centroids, class labels). The oracle streams with 500- and
  2000-row blocks are row-identical to the corresponding test streams after the prepended offset rows (variable-block
  streams differ). The oracle test used oracle boundaries and concept identities, measured a theoretical area term with
  the frozen fixed-segment components, and its results (in the paper) were seen. It involved no change detector and
  tuned nothing. The detector constants were set on development seeds 0 and 1 only; the method change did not use any
  seed-40/41 result. The registration author overlooked this reuse when writing "never used".
- Post-hoc split (not registered): seeds 42-43 only (36 streams): mean gain +2.84, 36/36 positive; per regime +5.35
  [+4.53,+6.15], +1.41 [+1.11,+1.71], +1.76 [+1.57,+1.95] (12 streams each; same hierarchical bootstrap). Seeds 40-41:
  +2.87, 34/36 positive; +5.00, +1.55, +1.76... (per regime +5.00 [4.26,5.66], +1.55 [1.21,1.89], +2.05 [1.91,2.23]).

Alternatives
A. Keep the registered C1 verdict on all 72 streams; correct the record: state in the paper (main text one clause +
   appendix provenance) that seeds 40-41 had been used in the oracle test (no tuning, no detector), report the seeds
   42-43 split as a post-hoc sensitivity analysis clearly labelled; add a dated correction note next to PLAN.md
   (not editing PLAN.md itself); log it.
B. Re-designate seeds 42-43 as the primary test (changes the frozen analysis after seeing results) - presumably not
   allowed.
C. Run a further fresh set (new seeds, e.g. 50-53) under the same frozen protocol as a confirmation, in addition to A.
D. Something else.

Constraints: frozen criteria are never changed retrospectively; old and new results kept separate; unfavourable facts
reported; the user has a standing authorisation for additional controls on existing generators with the method
unchanged, but frozen-protocol amendments require the user's explicit approval.

Answer with: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence /
Requires user approval. Under 350 words. Say whether this is P0, P1 or P2, and whether C is required or optional.

## Answer
**Decision:** Choose **A**, retaining a qualified verdict: “The preregistered numerical C1 criteria were met, with a disclosed deviation from the stated unused-data provenance.” **Severity: P1. Finding status: Confirmed issue. Location:** PLAN.md’s “never used” assertion. **Recommended correction:** Preserve PLAN.md and original results; add a dated, linked correction and log entry, with main-text disclosure and appendix provenance. **C is optional**, recommended for a stronger claim of confirmation on previously unseen data. P0 is not established by the supplied facts.

**Supporting evidence:** Seeds 40–41 had prior exposure, including identical evaluation rows in two regimes; prepended offsets do not remove that exposure. However, the earlier test used no detector, tuned nothing, and reportedly did not inform the method change. The frozen all-72 calculations still meet C1. The favourable seeds 42–43 results support robustness but do not retrospectively repair the registration.

**Alternative options:** Reject **B as a retrospective primary-test substitution**. Report seeds 42–43 only as a post-hoc sensitivity analysis; its 12-stream regime subsets cannot receive the original 24-stream C1 verdict. If undertaking **C**, prospectively record fresh seeds, sample size, unchanged method, analysis and criteria before execution, as a separate confirmation; preserve and report both studies.

**Key risks:** **Why it matters:** The false provenance statement overstates the strength of independent validation. Neither absence of tuning nor favourable sensitivity results establishes that prior exposure was irrelevant to every research decision. Avoid describing all 72 streams as previously unseen or concealing the deviation behind the passing thresholds.

**Remaining uncertainty:** This assessment relies on the supplied account of no result-informed method development. Reconcile the conflicting seeds 40–41 third-regime means, +1.76 versus +2.05, before publication.

**Confidence:** High on reporting requirements; moderate on the absence of consequential contamination.

**Requires user approval:** No additional approval for A or a separately documented C within the stated standing authorization; Claude executes. Any amendment to the original frozen protocol requires explicit approval. Approval cannot make a retrospective change prospectively registered.
Note (Claude): the prompt's seeds 40-41 line had a typo ('+1.76...' trailing); the correct per-regime values are +5.00, +1.55, +2.05, as in its parenthesis.
