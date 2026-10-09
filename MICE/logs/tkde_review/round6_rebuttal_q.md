You are a strict reviewer for IEEE TKDE. Judge only the paper in this directory (main.tex, table/figure files,
main.pdf). Do not ask for or inspect code, logs or result files.

Your issue in this round: expert-loss timing was underspecified (do losses score cached predictions issued before the
labels arrived or recomputed ones; initialisation of new experts; slow-level losses must be those of the issued
predictions for Theorem 2 to apply). In your plan check you also asked for complete initialisation, unambiguous cache
contents and indices, and a bounded provenance statement.

The authors revised Section 4: Algorithm 1 (alg:mice), the "Experts" paragraph and a new "Timing" paragraph. (The
pool-control issue is being revised separately; ignore it here.)

Answer:
Rebuttal verdict: Answered / Partly answered / Not answered
Reasons:
Remaining required changes for this issue (at most 3), or none:
Updated overall score (1 strong reject; 2 reject; 3 weak reject; 4 borderline reject; 5 borderline accept; 6 weak
accept; 7 accept; 8 strong accept) and distance to TKDE acceptance:
Does any remaining gap require a change to the method itself (yes/no)?
