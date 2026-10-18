**Decision:** Register interpretation C, a bounded cross: the boundary axis is extended by one value and crossed with the other optimizer axis only, with L and the mechanism parameter fixed at the frozen best. Concretely, n_steps 25 × lr {1e-4, 1e-3, 1e-2} at best (L, mech) for shifts, fsnet, onenet. For adaptz, the extended axes are lr {1e-5, 1e-4, 1e-3, 1e-2} × n_steps {1, 5, 25}, new cells only, at best (L, mech). The corner lr 1e-5 × n_steps 25 is included. Re-selection is over the original 36 configs plus the added cells, then stop. No second extension even if the new best is again on a boundary; report it.

**Supporting evidence**
- The registered text says "the grid is extended", so a pure B (one moved config) is a post hoc narrowing a reviewer can call out. lr and n_steps are coupled (effective step ≈ lr × n_steps), so testing n_steps 25 only at lr 1e-3 does not answer whether the boundary is a real optimum.
- L and mech are discrete architectural knobs. Their winners rarely flip with n_steps, and re-crossing them is what inflates A to about 235 CPU-h.
- Rough cost of C: shifts <1, adaptz ~9, fsnet ~10, onenet ~22 CPU-h, about 42 total, roughly 3 to 4 h wall on 12 lanes, bounded by onenet's 15 jobs.

**Alternative options**
- A, full slice: literal reading, cleanest for a reviewer, ~20 h wall. Choose it if wall time is not binding.
- B, local probe: cheapest, but ignores the lr × n_steps coupling and deviates most from "the grid is extended". Not recommended.

**Key risks**
- If n_steps 25 wins, every test run of that baseline costs ~5x; check the test-phase budget before launching, and register a compute-parity note for Table 1.
- Under C, a new best at n_steps 25 was not re-tuned over L and mech. State this in the amendment.
- Tie rule: define that added cells sort after the original grid so "first in sorted order" favors the original configuration.

**Remaining uncertainty:** the 5x wall-time scaling for n_steps 25 is extrapolated from dev timings; onenet could run longer. Whether MICE's own tuning budget is comparable is not in the question.

**Confidence:** moderate to high on C versus B; moderate on C versus A, which is a legitimate literalist choice.

**Requires user approval:** yes. This amends a registered rule and commits roughly 42 CPU-h, and A versus C is a budget call only the user can make.