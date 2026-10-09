Overall assessment: A promising, substantially improved paper with useful theoretical analysis and candid reporting of negative results. The narrowed claims are credible, but the central synthetic evidence remains insufficiently specified for independent scientific assessment.

Score: **4 — borderline reject**

Distance to TKDE acceptance: Excluding pending item (2), a focused revision making the controlled-grid and learning-curve experiments reproducible from the manuscript could bring this close to acceptance. This does not require changing the method.

**Issue (Severity P1): The experiment supporting the central learning-curve contribution is materially underspecified.**

Finding status: **Missing information**

Location: Section 5, “Streams,” `main.tex:482–487`; Section 5.1, `main.tex:501–514`; Appendix “Experimental Details and Full Results,” `main.tex:1015–1019`; Figure 2.

Evidence: The grid description supplies centroid counts, block lengths and recurrence structure, but omits feature dimensionality, centroid sampling, covariance/separation, mixture weights, class count and the precise class-assignment permutation procedure. These determine concept difficulty. The paper also does not specify how the learning curves were estimated: context sizes sampled, numbers of independent contexts and query rows, repetitions, or whether context and query samples were independent. The appendix substitutes generator filenames for an experimental specification.

Why it is the most severe: The paper’s distinctive scientific claim is that independently measured learning curves predict the value of recall. Without the data-generating distribution and curve-estimation protocol, readers cannot reproduce that evidence or assess whether the reported relationship depends on particular construction and sampling choices. This affects the central contribution independently of the excluded pool control.

Required fix: Add a complete mathematical generator description and parameter table, plus the learning-curve sampling and evaluation procedure, including context/query independence and replication counts. State which randomness is shared between curve measurement and stream evaluation. **This is feasible without changing the method**; it requires documenting the experiment actually performed.

Confidence: **High that the specification is missing; no claim that the underlying experiments were incorrectly executed.**