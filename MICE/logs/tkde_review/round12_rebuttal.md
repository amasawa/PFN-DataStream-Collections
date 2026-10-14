**Rebuttal verdict: Answered—as a diagnosis and limitation of the unchanged method.** This does not establish boundary-robust deployment.

**Reasons:**

- Test (c) directly addresses the initial-history confound. On the same shifted streams, realignment restores MICE’s mean advantage over reset from **−3.67 to +3.01 points**, close to the original **+3.09**. All eight realigned streams beat reset.
- The archive comparison also returns almost exactly to its aligned value: **+0.29 versus +0.30 points**. This makes the recovery more convincing than a comparison against reset alone.
- The supported conclusion is that **segment phase matters at fixed observed history**. Realignment changes both segment composition and expert availability, so contamination alone is not isolated. The revised section explicitly acknowledges this distinction.
- The paper reports the failed robustness criteria, identifies the known-phase intervention, and preserves the deployment limitation. I would not require a new segmentation algorithm merely to close this diagnostic question.

**Remaining required changes for this issue that do not change the method:** None. Further separation of contamination from availability timing would refine the mechanism, but is unnecessary for the appropriately qualified conclusion.

**Updated overall score: 4 — borderline reject.**

The learning-curve characterisation, direct oracle experiment, two-level safeguard, and unusually transparent negative results give the paper substantive scientific value. However, the strongest recall gains remain conditional on favourable segmentation, while the practical advantage over simpler memory policies is modest. I regard it as one substantive contribution-validation step short of borderline acceptance; additional wording alone would not change my score.

**Single most severe remaining issue for the next round:**

- **Severity:** P1 Major.
- **Finding status:** Missing information.
- **Location:** “Pool Organisation, Probability Quality and Resources”; tables `tab:poolgrid`, `tab:poolreal`, and `tab:cost`.
- **Evidence:** MICE exceeds the archive by only **0.30 points** on the aligned hard grid and **0.07 points** on real streams, and trails the snapshot pool by **0.08 points** on real streams. Its demonstrated organisational benefit is fewer experts and calls—**9.7 versus 14.0 calls per batch**—but the latency benchmark excludes these two closest competitors. Calls with different context lengths need not have comparable costs. Separately, FIFO-3000 wins on **21/29 streams** and is substantially cheaper on the measured prefixes.
- **Why it matters:** The paper establishes the value of retaining historical contexts more strongly than the practical value of its particular discrepancy-based organisation. The remaining justification for that component depends heavily on efficiency, which the closest-baseline measurements do not yet establish.
- **Concrete fix:** Keep MICE frozen and provide a bounded accuracy–latency–memory comparison against the archive and snapshot pools, including smaller pool capacities selected using timings alone. Cover aligned and shifted streams plus representative real streams. Establish where MICE offers a useful resource tradeoff; superiority everywhere is unnecessary.

**Does any remaining gap require changing the method itself? Yes:** overcoming the demonstrated dependence on unknown boundary phase requires an algorithmic remedy. The resource-comparison gap above does not. A convincing boundary-robust remedy preserving the existing gains and safety would move my score approximately **one point, from 4 to 5**, with the comparative-efficiency question still relevant.