Two items are not implemented.

1. **Adaptz mechanism parameter.**
   - REVIEW asked for adaptz's gradient-history length to join the dev grid at three values around the official default, with fire counts logged.
   - PLAN says "adaptz: … No threshold parameter", so the grid has no mechanism axis for adaptz.

2. **Shifts mechanism parameter.**
   - REVIEW asked for shifts' mask sparsity weight to join the dev grid at three values around the official default.
   - PLAN says "shifts: … No extra mechanism parameter" and describes a parameter-free threshold at the mean, so shifts has no mechanism axis either.

Everything else is implemented:
- All learners train online from batch 0, ADAPT-Z included, with the departure from its frozen base documented.
- TOT is reproduced on OneNet behind a sanity-check gate, and the row is reported as skipped if the gate fails.
- L = 1 is allowed only for adaptz.
- The n_steps extension goes to 25.
- The mechanism parameter is added for dtmoe, fsnet and onenet.
- The RevIN handicap goes in the README.
- Drtabpfn uses relative domain indices.
- Batch-0 padding is by repeating the first row.

I did not count the "offline forecasters run online" footnote as missing. PLAN only says every change is listed in the README, not that the footnote is added verbatim.
