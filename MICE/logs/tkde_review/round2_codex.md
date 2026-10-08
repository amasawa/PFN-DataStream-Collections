**Issue:** P1 — Confirmed evaluation gap: the experiments do not isolate MICE’s concept-organized recall from the benefit of additional historical storage and inference.

**Location (section, line):** §4, lines 382–398; §5 protocol, lines 424–434; §5 RQ4, lines 605–609 in [main.tex](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:382).

**Evidence:** The stated “\(M=1000\) for every policy” is a per-context limit: MICE can retain twelve additional 1000-row contexts and evaluates up to fifteen experts. The paper acknowledges 5–18× runtime. Removing the pool simultaneously removes historical data and expert evaluations. Neither that ablation nor the reported baselines compares against a similarly resourced historical-context ensemble using the same two-level aggregation.

**Why it is the most severe:** The results establish that adding MICE’s pool helps, but do not establish whether its concept identification and merging provide value beyond a simple archive of past contexts. That leaves the central methodological contribution empirically unresolved; additional descriptive results or minor wording changes cannot resolve it.

**Required fix (feasible without changing the method):** Add a chronological snapshot-bank baseline with matched storage and expert-call budgets, identical windows and aggregation, but no discrepancy-based merging. Compare on the recurring grid and real streams, reporting paired differences and actual resource use. Preserve existing results and distinguish the added evaluation from the original registrations. Narrow the contribution claims if this control matches MICE.

**Confidence:** High that the control is missing; moderate-high that this warrants major revision.