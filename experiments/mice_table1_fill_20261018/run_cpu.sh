#!/bin/bash
# Item 1 of PLAN.md: every (stream, method) of the trained learners, one process each, 6 in parallel; outputs that
# exist are skipped (so a rerun of this script resumes). Usage: run_cpu.sh  (background)
R=$HOME/pfn-runs/mice-table1-trained-probs; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
M="mooe_rff4000_100_2_0.01 levbag srp adwinbag mooe_rff2000_100_2_0.01 nse arf hat"   # slowest first
mkdir -p $R/P $R/logs
{ for m in $M; do
    while read -r s; do echo "$X/../../MICE/data $s $m"; done < $X/streams_main.txt
    while read -r s; do echo "$HOME/pfn-runs/mice-confirm-cp-20261017/data $s $m"; done < $X/streams_confirm.txt
  done; } > $R/tasks.txt
echo "$(date '+%F %T') start $(wc -l < $R/tasks.txt) tasks" >> $R/progress.txt
xargs -P 6 -L 1 bash -c '~/pfn-venvs/stream/bin/python '$X'/run_trained_probs.py --data $0 --out '$R'/P --streams $1 --methods $2 \
  >> '$R'/logs/$1__$2.log 2>&1 && echo "$(date +%T) ok $1 $2" >> '$R'/progress.txt || echo "$(date +%T) FAIL $1 $2" >> '$R'/progress.txt' < $R/tasks.txt
echo "$(date '+%F %T') done" >> $R/progress.txt
