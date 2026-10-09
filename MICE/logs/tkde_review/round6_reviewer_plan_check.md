**Verdict: Partly satisfies.** The proposed ordering resolves the central ambiguity: losses score predictions made before the corresponding labels arrived, including the historical fast mixture. Three details should be explicit:

1. **Complete initialisation.** Specify the first prediction step when no previous labelled batch exists: initial fast weights/losses, \(L_{0,k}=0\), and any warm-up convention. Retain the proposed median rule for newly added experts and identity-preserving treatment of merges.

2. **Make the cache and indices unambiguous.** Cache the default prediction and the fast mixture formed with that batch’s original weights—not merely individual expert predictions. At step \(t\), write
   \[
   L_{t-1,k}=\gamma L_{t-2,k}+\ell_{t-1,k},
   \qquad v_{t,k}\propto e^{-\eta_2\gamma L_{t-1,k}}.
   \]
   State that \(\ell_{t-1,k}\) is the **mean** half Brier score of those cached predictions. Theorem 2 then concerns the two adaptive prediction sequences, under its stated learning-rate condition.

3. **Bound the provenance statement.** Identify the frozen implementation/replay version and which reported results use this procedure. Where replay constructs mixtures from cached component predictions, explain that weights use only earlier labels; distinguish these mixtures from predictions emitted by the original run.

**Still unsupported:** From the paper and this plan alone, I cannot independently verify “method unchanged” or “every reported number is computed this way.” Also, Theorem 2 does not extend to the log-loss or \(\eta_2=10\) variants merely because they use cached predictions.