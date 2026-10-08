**Issue:** P1 — Confirmed evidential gap: the central claim of confirmatory accuracy “safety” rests on point estimates, not uncertainty-aware non-inferiority evidence.

**Location (section, line):** RQ3, [main.tex:542](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/overleaf/tkde/main.tex:542); pre-registration, lines 838–843.

**Evidence:** The confirmatory checks merely compare observed accuracy differences against −0.5/−0.3-point thresholds ([check_heldout4.py:28](/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/code/check_heldout4.py:28)). The six segments come from three previously used sources. The reported bootstrap interval concerns the **mean improvement on the third set**, not non-inferiority on each confirmatory segment. Theorem 2 bounds discounted Brier loss, so it cannot establish accuracy safety.

**Why it is the most severe:** Safety is the principal real-stream contribution, where gains are small. Pre-registration prevents retrospective threshold selection; it does not establish that uncertainty excludes materially harmful accuracy differences.

**Required fix (feasible without changing the method):** Analyze the frozen paired predictions using justified temporal dependence assumptions and one-sided confidence bounds against the registered margins. Report results by source and distinguish backbone-seed replication from independent data evidence. Where bounds are inconclusive, replace “confirmed safety/non-inferiority” with descriptive benchmark claims and restrict generalization accordingly.

**Confidence:** High that the inferential evidence is missing; whether the existing predictions would establish non-inferiority remains unknown.