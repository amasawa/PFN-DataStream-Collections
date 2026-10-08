**Issue:** P1 — Confirmed issue: the central recall-versus-relearn formula is not proved as stated, and its numerical validation does not consistently implement that formula.

**Location (section, line):** §III-C, [main.tex:296](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:296); Appendix A, lines 738–743; §V-A, lines 452–467.

**Evidence:** The proof assumes “Both learners lose the first batch.” Delayed labels do **not** imply equal first-batch accuracy. The stated assumptions leave their difference unconstrained, so the equality omits a term \((A_{\mathrm{mixture},1}-A_{\mathrm{reset},1})/J\). Separately, the prediction calculation uses a full \(M=1000\)-row memory on both recurring visits ([predict_gain.py:19](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/predict_gain.py:19)), whereas the theorem specifies only 500 stored rows on the second visit when \(L=500\). Using the saved test learning curves and the same interpolation, the theorem’s visit-dependent formula gives **9.21 points**, versus the reported **10.44**, for 100 centroids.

**Why it is the most severe:** This undermines the paper’s central explanatory contribution—that learning curves determine recall’s gain—and the experiment presented as validating it. Strong benchmark results cannot establish an incorrect theoretical equality.

**Required fix (concrete, feasible without changing the method):** Correct the theorem with an explicit first-batch term and precise oracle-selection/context assumptions. Distinguish this idealized result from operational MICE versus DDM, including detection and slow-level effects. Recompute predictions using visit-specific memory sizes; update the correlations, figure, table, and headline claims. This requires substantive theoretical and analytical revision, without changing MICE.

**Confidence:** High on the mathematical and numerical defects; moderate-high that this blocks acceptance with only minor revision.