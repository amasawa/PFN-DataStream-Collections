1. **"The cluster run under env_lock repairs that."** A never mentions an `env_lock`. It says only that the original CPU venv versions are unrecorded and river 0.26.1 is recorded. Nothing in A shows the cluster environment is locked or that a rerun fixes the provenance gap.

2. **"P2 costs no GPU-hours and no calendar time."** A says P2 costs "almost no calendar time by itself", and P2b (selection and tests of the four baselines) needs a round trip. "No calendar time" overstates this. The claim holds only because the round trip coincides with dtmoe stage 2.

3. **"Scheduled into the GPU-idle gap of the select/extend/test round trip, the calendar cost is zero."** A does not say the GPUs are idle during round trips. B lists this as an uncertainty later, yet states "zero" as fact here.

4. **"About 19 exclusive GPU-hours out of 760-960, about 2-2.5 percent."** The logic is flawed. The 19 h are RTX 5000 Ada durations, and the 760-960 figure is A800 process-hours. Dividing one by the other mixes hardware. The A800 benchmark cost is unknown, and the "5 GPUs in parallel, about 6 h wall" figure is also an Ada number.

5. **"The analyse_bench/analyse_pools/analyse_14b path adaptations must be audited."** A names only `analyse_bench.py` (and `make_cost_tables.py`). `analyse_pools` and `analyse_14b` are not in A, so they are unsupported.
