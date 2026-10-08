**Issue:** P1 — Missing information: the central recall result is validated only with drift boundaries perfectly aligned to MICE’s segmentation.

**Location (section, line):** `main.tex`: §IV, 385–389; §V, 438–440; §V-B, 523–526.

**Evidence:** MICE closes a segment every 500 rows. Every controlled-grid concept lasts exactly 500 or 2,000 rows, starting at row zero (`MICE/code/grid_streams.py`, 20–26, 33). Consequently, every archived segment contains one concept. The hardest reported cell—an 8.5-point improvement—uses 500-row concepts, exactly matching the segmentation period. No misaligned-boundary experiment is reported.

**Why it is the most severe:** This favorable synchronization bypasses a central difficulty: constructing reusable contexts when concept boundaries are unknown. With an offset, segments can mix conflicting concepts and compromise subsequent recall. Real-stream accuracy and non-inferiority do not establish that this recall mechanism survives. This leaves the central contribution’s applicability unresolved, beyond a minor editorial revision.

**Required fix (feasible without changing the method):** Freeze MICE and run a pre-specified robustness experiment with several boundary offsets and non-multiple or variable block lengths, keeping the same baselines and pending pool controls. Report recurrence-local and overall gains. If gains collapse, explicitly restrict the contribution to conditions yielding sufficiently pure stored segments.

**Confidence:** High that the alignment and validation gap exist; its quantitative impact remains untested.