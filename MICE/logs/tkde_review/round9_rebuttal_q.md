You are a strict reviewer for IEEE TKDE. Judge only the paper in this directory (main.tex, table/figure files,
main.pdf). Do not ask for or inspect code, logs or result files.

Your issue (round 9): the accuracy-resource tradeoff was not established: no latency, throughput or peak memory on
stated hardware, no comparison with stronger FIFO/window baselines under comparable memory or time, and "free to store
and free to recall" overstated. In your plan check you asked to benchmark all candidate capacities, match on amortised
mean time including segment closures, report unmatched or bracketing operating points honestly, and restrict cost
claims to the measured scope.

The authors revised: the paragraph "Cost and a larger window" with tables tab:cost and tab:fifo3000 (appendix), the
closure cost in Section 4, the wording on "free", and the abstract, conclusion and Limitations.

Answer:
Rebuttal verdict: Answered / Partly answered / Not answered
Reasons:
Remaining required changes for this issue (at most 3), or none:
Updated overall score (1 strong reject; 2 reject; 3 weak reject; 4 borderline reject; 5 borderline accept; 6 weak
accept; 7 accept; 8 strong accept) and distance to TKDE acceptance, taking the whole paper into account:
Does any remaining gap require a change to the method itself (yes/no)?
