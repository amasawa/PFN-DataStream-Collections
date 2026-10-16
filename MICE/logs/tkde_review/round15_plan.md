# Round 15 plan (proof gap in Proposition 3: adaptively selected reference window)

Claude's judgement: the issue holds. The reference window starts after the batch that follows the previous declared change; that change was declared from errors that can include the compared rows, so n1 and the window are data-dependent and the fixed-window Azuma argument does not cover them. Fix (no change to the method or constants): union bound over the R_cp - 1 = 4 possible reference lengths (2 to 5 batches); every pair (candidate b, length m) is a fixed set of rows with fixed weights, to which Azuma applies.

Replacement text:

Assumption 2 (b): "After a change at batch b, the mean rate on the batches b,...,t-1 exceeds that on every run of two to R_cp consecutive batches that ends at batch b-1 and follows the previous change by at least beta."

Proposition 3:
(i) False alarms. If no change occurs in the batches t-H_cp-R_cp, ..., t-1, the probability that (eq:cp) declares one at t is at most (R_cp - 1) H_cp delta_cp.
(ii) Detection. If a change occurs at batch b, b is a candidate at t with at least two compared batches before it, and beta >= 2 tau(2B, n_2), then at t the excess at b is positive, and a change is declared, with probability at least 1 - (R_cp - 1) delta_cp.

Proof: Fix a candidate b and a number m in {2,...,R_cp} of compared batches before it; Z over the rows of batches b-m..b-1 (pre, n1 = mB) and b..t-1 (post). For fixed b and m the rows and the weights 1/n1, 1/n2 do not depend on the data; the context of each batch is fixed before its rows are seen, so the error indicators minus their conditional rates, in row order, are a martingale difference sequence; Azuma-Hoeffding as before. The reference window used by (eq:cp) starts after the previous declared change, which depends on earlier errors, possibly of the compared rows; it is one of these R_cp - 1 windows, and a union bound over m covers this selection. (i) No change in batches t-H-R..t-1: by Assumption 2(a) Zbar <= 0 for every b and m; union over at most H candidates and R-1 lengths. (ii) For every eligible m, Assumption 2(b) gives Zbar >= beta >= 2 tau(2B, n2) >= 2 tau(mB, n2) (tau decreases in n1); the excess at b is non-positive only if Z - Zbar <= -tau for the selected m; union over the R-1 lengths.

Remark (numbers): with B=100, H_cp=3, R_cp=5, delta_cp=1e-3: false-alarm probability per batch at most 0.012 (was 0.003); with n2 = 200 and the shortest reference n1 = 200, 2 tau = 0.37 (was 0.31 at n1 = 500), so changes between concepts that disagree on more than about 37% of the inputs (was "about a third") are detected within two batches with probability at least 0.996 (was 0.999). Measured: 575/576 changes detected and no false cut on the confirmation streams (unchanged).
