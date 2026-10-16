1. **6/8 — weak accept.** Under [TMLR’s criteria](https://jmlr.org/tmlr/acceptance-criteria.html), the central claims appear supported and appropriately qualified. **Already on the acceptance side:** I see no demonstrated scientific blocker; a reproducibility clarification remains.

2. **Single most severe remaining issue**
   - **Severity:** P2.
   - **Finding status:** Missing information.
   - **Location:** §1, Contributions; Appendix B, Reproducibility details.
   - **Evidence:** “Code, streams and all cached predictions will be released with the paper.” The supplied package contains the manuscript and summary tables, but no implementation or underlying prediction records.
   - **Why it matters:** The reported replay agreement and empirical guarantee checks cannot be independently verified from this package. This limits verification, without establishing that the results are incorrect.
   - **Concrete fix:** Provide an anonymous reproducibility archive containing the evaluation/replay code, exact checkpoint identifiers, and underlying results sufficient to regenerate the tables and bound checks.
   - **Method change or new data?** Neither; release existing materials.

3. **Confidence:** Moderate. I checked the mathematical argument and manuscript consistency, but could not independently validate the experimental implementation or outputs.