- **Rebuttal verdict: answered.** The remark now states an “effective horizon of ten batches” and explicitly says adaptation depends on earlier losses and the post-change loss gap.
- **Remaining required change for round 19:** none.
- **Updated score:** **6/8**, assuming the excluded open item closes as implied.
- **Acceptable at TKDE under that assumption:** **yes**, with the minor clarification below.

**Round 20 — single most severe remaining issue within the reviewed scope**

**Severity:** P2. **Finding status:** Confirmed issue.  
**Location:** Remark after Corollary 3, [main.tex:485](/tmp/claude-1000/-mnt-c-Users-zhwu9808-Desktop-dataStream/ddb2746a-c254-444c-acb3-004905f96da7/scratchpad/paper_r19/main.tex:485).  
**Evidence:** “The bounded, exp-concave loss is essential: it confines the step to \(\eta_2\le\tfrac12\).”  
**Why it matters:** This conflates the half-Brier-specific step condition with a necessity for bounded losses. The Appendix’s potential argument uses exp-concavity; log-loss also has this property despite being unbounded. Its observed sensitivity after a switch does not establish that boundedness is necessary for a regret guarantee.  
**Concrete fix:** State that \(\eta_2\le\tfrac12\) provides the proved half-Brier guarantee, while boundedness limits individual batches’ influence; describe the log-loss failure as an empirical adaptation problem.  
**Method changes or new data required:** **No.**