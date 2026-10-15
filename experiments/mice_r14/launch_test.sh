#!/bin/bash
# Round 14 frozen test (PLAN.md): two workers, each works through T1 (~/pfn-runs/mice-r14-test) and then the existing
# streams and real streams (~/pfn-runs/mice-r14-exist; T2, T3 micecp, T3 archcp, in tasks.txt order).
cd "$(dirname "$0")"
for w in $(seq 1 ${NW:-4}); do
  ( ./worker.sh ~/pfn-runs/mice-r14-test $w; ./worker.sh ~/pfn-runs/mice-r14-exist $w ) &
done
wait
