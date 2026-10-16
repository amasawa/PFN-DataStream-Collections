**Yes with changes.** The anchor-preserving random expert and identical mixture are the right control, but execution as written leaves four gaps:

1. **Define what establishes incremental value in deployment.** R1 alone establishes an expert-level advantage. Pre-specify how paired **MICE+sel versus MICE+rand** results support the deployed claim, separately for controlled recurrence and real streams. Make the decision rule consistent with calling accuracy and log-loss “co-primary”; a positive log-loss point estimate alone is weak evidence.

2. **Fix the uncertainty analysis.** Drop the paired-t interval over 22 dependent prefixes—even labelled “descriptive,” it does not provide valid uncertainty. Report source-level effects and explicitly limited inference from four sources, alongside justified conditional uncertainty on these fixed streams.

3. **Account for random-selector variability in the primary comparison.** Use draw-averaged effects for the replicated K=3 analysis, and add independent selector draws on held-out streams while holding backbone seeds fixed. Distinguish selector variability from backbone variability.

4. **Make runtime comparable and conclusions calibrated.** Measure both methods with matched timing boundaries, hardware and concurrency, including ranking, context prediction and mixing; historical contention-affected timings are insufficient. Also replace “not better” after a failed R1 with “no advantage established”: failure to reject does not establish equivalence.

With these changes, the experiment can answer the requirement; whether it resolves the P1 depends on the observed advantage and its uncertainty.