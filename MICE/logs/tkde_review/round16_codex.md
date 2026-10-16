**Rebuttal verdict: Answered; round-15 wording issue closed.** The remark now bounds the joint eligibility-and-failure event and reserves 0.996 for almost-sure eligibility.

**Updated score: 6/8**, assuming satisfactory resolution of the separately pending item. The previous scoring assumption is not available in this context.

**Single most severe remaining issue for round 16:**

- **Severity / status:** P1 — Confirmed overstatement of theoretical applicability.
- **Location:** Proposition 2; §5.2, “Detection, location and purity”; abstract.
- **Evidence:** “All closes were majority-pure, the condition under which [Proposition 2] identifies the concept.” But Proposition 2 requires “both concepts be deterministic” and \(P_X=Q_X\).
- **Why it matters:** Majority share alone does not guarantee recall for stochastic labels—even in the population limit. For example, \(p=(0.6,0.4)\), \(q=(0,1)\), and a 60% share of \(P\) produce mixture \((0.36,0.64)\), reversing \(P\)’s preferred class. The Gaussian-centroid generator has overlapping components, so deterministic centroid labels do not imply deterministic labels given features.
- **Concrete fix:** Qualify the majority-recall claims throughout with the proposition’s full assumptions. Describe measured majority purity as an empirical diagnostic, not verification of its identification guarantee.
- **Method change or new data:** Neither required for this correction.