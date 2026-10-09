Overall assessment: A coherent methodological contribution with unusually candid reporting of negative results. The narrowed scientific claims are substantially better supported, but the practical case for the proposed stream learner remains incomplete.

Score: **4 — borderline reject**

Distance to TKDE acceptance: Apart from pending item (2), the principal remaining requirement is a resource-aware evaluation establishing what the accuracy gains cost and whether they justify that cost. This can be addressed without changing the method.

**Issue (Severity P1): The accuracy–resource tradeoff is not established.**

**Finding status:** Missing information.

**Location:** Section IV, `main.tex` lines 397–432; Section V, lines 471–472; Section VII, lines 812–834.

**Evidence:** The stated \(M=1000\) budget limits each context. MICE additionally retains up to twelve stored contexts and evaluates up to fifteen experts per batch, whereas FIFO uses one context. The paper acknowledges a **5–18× runtime multiplier**, but supplies no hardware-specific latency, throughput, peak-memory measurements, or accuracy comparisons under comparable resource budgets. Its mean real-stream advantage over FIFO is **0.57 percentage points**. Calling memory “free to store and free to recall” in the conclusion also exceeds the supported claim of zero additional training.

**Why it is the most severe:** The reported accuracy improvements remain valid at their respective configurations, but readers cannot determine whether MICE offers a worthwhile operating point for streaming deployment or whether spending comparable resources on a baseline would recover the advantage. This concerns the practical significance of the complete method, independently of the pending archive control.

**Required fix:** Keep MICE frozen. Report end-to-end batch latency, throughput and peak memory on specified hardware, including segment processing; distinguish per-context capacity from total retained data. Add a bounded resource comparison against stronger FIFO/window-ensemble configurations given comparable memory or inference time, and present the resulting accuracy–cost tradeoff. Replace “free” with “requires no additional training.” **No method change is required.**

**Confidence:** High that the resource evidence is missing; moderate that this should determine rejection rather than a substantial revision.