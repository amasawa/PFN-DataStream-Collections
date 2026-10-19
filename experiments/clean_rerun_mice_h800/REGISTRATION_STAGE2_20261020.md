# Stage 2 of the tuned Table 1 baselines on the cluster: P2b (fsnet, onenet, adaptz, shifts), P5 (dtmoe) and TOT's
# stage 2 in P6 (registered 2026-10-20, before any development grid of the cluster has returned)

Binding:
- amendment c items 1-4: selection, one full extension, re-selection, freezing before tests;
- PLAN_BASELINES "Tuning": the extension values lr × 10 or / 10, and n_steps 25;
- ACTIVATION item 4: cluster outputs only; local selections stay records;
- AMENDMENT_20261020 item 5: returned results in ~/h800.

Records: PLAN_P5_P6_draft.md, MICE/logs/table1_fill/fable_p5p6_a.md (Q1), sonnet_p5p6.md (finding 2).

## The procedure (the same for every method m)
1. **Wait for the development grid.** The development grid of m is complete on the cluster, with every task done and
   none given up:
   - fsnet, onenet, adaptz, shifts: ts_dev of tasks_p2.jsonl (720 tasks);
   - dtmoe: dtmoe_dev of tasks.jsonl (180), which runs only after its probe cap and the user's decision (ACTIVATION
     item 2);
   - tot: its development grid of P6 (180; registered later).

   The outputs are returned to ~/h800. A given-up task stops the selection of its method, and its disposition is
   fixed now:
   - an infrastructure failure (killed by a signal or a time limit, out of memory, node failure, as shown in its log)
     gets one more attempt, registered by the coordinator;
   - an error raised by the method's own code goes to the user, with the log, before any selection of that method.
2. **Selection** on the coordinator machine, with the unchanged select_frozen.py:
   - command: `select_frozen.py ~/h800/pfn-runs/mice-table1-newbase/<D>/P <m> MICE/results_paper/table1_fill/frozen_cluster`;
   - D = dev_cluster (CPU methods, tot) or dev_h800 (dtmoe);
   - output: frozen_cluster/frozen_<m>.json, committed and pushed.

   No local selection file (MICE/results_paper/table1_fill/frozen/) is read.
3. **Extension.** `make_tasks_stage2.py ext <m> frozen_cluster/frozen_<m>.json` writes
   tasks_stage2_<m>_ext.jsonl and its manifest. The manifest holds the sha256 of the selection file, the expected
   count and the actual count; it stops if they differ.

   | edge reached by the best configuration | new value |
   |---|---|
   | lr = 1e-4 (lower) | 1e-5 |
   | lr = 1e-2 (upper) | 1e-1 |
   | n_steps = 5 (upper) | 25 |
   | n_steps = 1 | none (the smallest value) |

   Every new value is crossed with every value of the other axes, corners included, minus the original grid, on the 5
   development streams. The outputs go into the same development directory. If no edge is reached, the list is
   empty. The list and its manifest are committed and pushed before the list runs.
4. **Re-selection.** `select_frozen.py ... --final` gives frozen_cluster/frozen_<m>_final.json. Ties go to the
   original grid first, and the result is frozen even if it is on a boundary. It is committed and pushed before any
   test task of m exists.
5. **Tests.** `make_tasks_stage2.py test <m> frozen_cluster/frozen_<m>_final.json` writes the frozen configuration on
   the 92 Table 1 streams:
   - 29 real, 24 grid and 30 generator streams on MICE/data, and 9 confirmation segments on the confirmation data;
     the generator asserts 83 + 9 and 29 real;
   - in the order of amendment c item 4: real and confirmation streams first, then grid and generator;
   - outputs in test_cluster/P (CPU methods, tot) or test_h800/P (dtmoe);
   - list and manifest committed and pushed before the tests run.

   Every test cell is reported.

## Devices and environments
| methods | device and environment | thread setting |
|---|---|---|
| fsnet, onenet, adaptz, shifts, tot | cluster CPU, P2 node type; {PYTS} (tot: the P2 environment plus einops 0.4.0, P6) | 1 thread, CUDA hidden |
| dtmoe | H800, strict deterministic mode; {PYTOT} | as in dtmoe_dev |

## Guards
- **Generator.** make_tasks_stage2.py is committed and pushed with this note, and checked by its self-test on
  hand-written fixtures of selection files only (stream shapes are read from the data). The fixtures cover:
  - no extension, an upper n_steps, an upper lr, and a lower lr with an upper n_steps (corner included);
  - dtmoe and tot routing;
  - rejection of values outside the table;
  - the 92-stream test list, with 9 confirmation streams;
  - rejection of a non-final file for tests.

  A list is generated once: an existing list stops the generator. Every manifest records the generator's sha256. A
  list whose manifest shows a sha256 other than that of the generator committed with this note needs a new
  registration first.
- **Processes.** On the cluster, each CPU worker has a fixed core count on the P2 node type (HANDOFF P2). This
  replaces the local limit of 12 processes (amendment c items 2 and 5), which concerned the local machine.
- **Cost.** A generated list is never shortened. If its projected cost exceeds 3000 CPU-hours, or 300 H800-hours for
  dtmoe (REGISTRATION_P6_GATE_A cost limits), it goes to the user before it runs. For example, n_steps 25 costs about
  five times n_steps 5. The user's options are only "run the list as generated" or "do not run it; the method is
  reported as not run, for its cost". The list itself is never changed.
- **Paper footnote.** The update steps per batch of every method, and whether its frozen configuration lies on a
  boundary (amendment c item 3).
