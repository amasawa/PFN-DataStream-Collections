# Sonnet 审查方案与 Fable 答复（09:2x，30 秒）

1. **Tau is chosen by runs, but ACTIVATION requires it fixed before any run (Draft item 8 / Expert Q4).**
   - Evidence: ACTIVATION says "the value and the reason are fixed in the P4 registration before any run" and "registered before any run". Fable says to select tau on the five dev streams and then "写入 P4 注册".
   - Why it matters: option (b) needs CURE runs before the registration exists. That breaks the registration-before-runs rule, not just the "no tuning" sentence. Fable's only proposed fix is rewording line 96, which doesn't cover this.
   - Correction: choose one of these.
     - Fall back to (a), a pre-written fixed value.
     - Register the dev-stream selection procedure and its tie rule first, then run the dev streams, then register the frozen tau as a dated amendment.
     - Have the user amend both the "no tuning" and the "before any run" wording.

2. **Published per-dataset taus are ignored without saying so (Draft item 8; facts section).**
   - Evidence: The draft lists published taus for noaa, meter, rialto, posture, nomao, poker and agr_a, but "The paper and code define no tau for other data".
   - Why it matters: ACTIVATION says "CURE's published defaults". If the 92 streams include any of those seven datasets, tau is not undefined for them. Using the published value gives CURE a tau tuned by its authors, possibly on the test streams. Using a global value ignores a published default. Neither text says which applies, and neither maps the Table 1 streams to those seven datasets.
   - Correction: Map the 92 streams to the seven datasets. State whether published taus apply to those streams, and apply the same rule to every stream. Disclose in the paper that those taus were author-tuned.

3. **Warm-fill condition is misdescribed (Draft facts, CURE).**
   - Evidence: The draft says the row enters the long bank "if the long bank is still below capacity". The code has `warm_fill_target = int(round(self.long_capacity * self.warm_fill_ratio))` and `bypass_gate = self.long_size() < warm_fill_target`.
   - Why it matters: if `warm_fill_ratio` is below 1, the warm-fill threshold is lower than capacity. Reasoning about batch-0 rows and the gate would then be wrong.
   - Correction: Read the `warm_fill_ratio` default and use it in the draft. Check also that `_meta_score` is entropy alone, since the code shows margin_uncertainty is also stored.

4. **Entropy normalisation: the fix is right but the source is not quoted (Expert Q5.2; Draft item 7).**
   - Evidence: Fable says the denominator comes from "TabICL classes_". The quoted code uses `max_entropy = log(p.size)`, the length of whatever vector is passed in. Draft item 7 passes "the probabilities predicted for that row", and MICE's P covers the global label set with zero columns.
   - Why it matters: if the adapter passes the global-K vector, K changes and the clip at 1e-12 on the zero columns changes the entropy. This breaks faithfulness to CURE and makes tau mean something different.
   - Correction: In `run_cure.py`, slice P to the context's classes before calling `record_prediction_signal`, then renormalise. Make it an explicit MiMo check. Also state that `y_pred` is passed as in CURE's runner.

5. **Per-segment exclusion contradicts ACTIVATION (Expert Q2 risks; Draft item 6).**
   - Evidence: Fable says "部分段按「类数错误」规则排除" for Mitra's 10-class limit. ACTIVATION excludes a backbone ("a backbone is excluded only for reasons…"), not individual segments.
   - Why it matters: dropping segments changes the "at least three of four" hypotheses and the denominators for Mitra only. Nobody has decided whether Mitra is excluded or run on a subset.
   - Correction: Before any accuracy is read, list the segments with more than 10 classes. State whether Mitra is excluded entirely or evaluated on a fixed subset. If a subset, say how the hypotheses and the 40-task count change.

6. **Mismatch between the batch protocol and per-row CURE is not disclosed as a fairness caveat (Draft item 7, Expert Q5).**
   - Evidence: The draft says "This is the only change". In CURE's loop, the signal for row t comes from a model whose memory already holds rows 0..t-1. Under the batch mapping, all 100 rows of a batch get signals from the same pre-batch memory.
   - Why it matters: this shifts the entropy distribution, and especially the gate's admission rate, relative to the per-row setting that tau was tuned in. A reviewer will ask about this. Fable only calls it "一视同仁".
   - Correction: Log the long-bank admission rate per stream. State in the paper that the signal staleness is up to a batch. Treat the mismatch as a limit of any fixed tau, not only a backbone-scale issue.
