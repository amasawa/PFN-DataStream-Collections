**Rebuttal verdict: answered.** Localisation now explicitly concerns the 570 and 575 boundary-matched declarations; the unmatched cut is reported separately; joint premises hold on only 67/72 and 71/72 streams, establishing that they did not hold globally. **Remaining round-18 change: none.**

**Updated score: 6/8**, assuming the excluded resource item closes as implied. **Acceptable at TKDE: yes**, with the minor clarification below.

**Round 19 — single most severe remaining issue:**

- **Severity:** P2. **Finding status:** Confirmed issue.
- **Location:** Remark after Corollary 3, [main.tex:480](/tmp/claude-1000/-mnt-c-Users-zhwu9808-Desktop-dataStream/ddb2746a-c254-444c-acb3-004905f96da7/scratchpad/paper_r18/main.tex:480).
- **Evidence:** “the slow level needs about ten batches … to follow the better of the two experts.”
- **Why it matters:** The ten-batch effective discount horizon is not an adaptation-time guarantee. Overcoming accumulated preference depends on the previous loss gap and the new expert’s advantage; a small advantage can require substantially longer. The regret theorem itself is unaffected.
- **Concrete fix:** Replace this with: “The discount gives an effective memory horizon of ten batches; adaptation time depends on past losses and the post-change loss gap.”
- **Method change or new data required:** Neither; textual clarification only.