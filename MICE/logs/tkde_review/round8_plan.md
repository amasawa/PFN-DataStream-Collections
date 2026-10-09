# Round 8 — plan (Claude, 2026-10-09)

Judgement: accepted (documentation only; method unchanged). Facts taken from the code that produced the results
(MICE/code/grid_streams.py, learning_curve.py, predict_gain*.py, run.py). One correction found while checking: the
paper says the class assignment is "permuted" between concepts; the code draws each concept's labels independently.

Additions (new appendix subsection "Controlled grid and learning curves", with a parameter table, and a corrected
sentence in Section 5 "Streams"):
- Generator. d = 10 features, 4 classes, K = 3 concepts. Centroids C_j ~ U([0,1]^10) i.i.d., j = 1..m, m in {5, 30,
  100}; mixture weights w_j = u_j / sum u, u_j ~ U(0,1). Labels: for each concept k an independent vector
  lambda_k(j) ~ U{0,1,2,3} i.i.d. over centroids (not a permutation; two concepts can agree on a centroid). A row of
  concept k: j ~ Categorical(w), x = C_j + N(0, 0.15^2 I_10), y = lambda_k(j). Concepts 1,2,3 in blocks of L rows,
  L in {500, 2000}, three cycles (9 blocks). P_X is the same for all concepts. One NumPy generator per data seed
  draws C, w, lambda first and then the rows.
- Data seeds: 0, 1 development; 10, 11 registered test; 20, 21 confirmatory; 30, 31 misaligned test (a); test (b)
  reuses 20, 21 with a separately seeded prefix.
- Learning curves (registered before the grid test). For data seeds 10 and 11 and each m: one block of 4000 fresh
  rows per concept from the same generator and seed (so the same centroids, weights and labels as the seed-10/11
  grid streams; the rows are new draws). Rows 1-3000 are the context pool, rows 3001-4000 the 1000 test rows,
  disjoint. Context sizes n in {50, 100, 200, 500, 1000, 2000}; three contexts per n drawn without replacement from
  the pool with generator seeds 0, 1, 2 (contexts of different n and repetitions overlap). Frozen TabPFN v2
  (4 estimators, random state = data seed); accuracy on the 1000 test rows. a(n) = mean over 2 seeds x 3 concepts x
  3 repetitions; values between measured sizes interpolated linearly in log n.
- Shared randomness: for grid seeds 10 and 11 the curves and the streams share the concept definitions (C, w,
  lambda) but not the rows; for seeds 20 and 21 the predictions use the seed-10/11 curves, i.e. the same generator
  distribution with different concept draws. Stream evaluation uses backbone random state 0.
