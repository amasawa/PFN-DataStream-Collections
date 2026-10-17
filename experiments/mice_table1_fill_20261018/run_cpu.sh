#!/bin/bash
# Item 1 of PLAN.md: every (stream, method) of the trained learners, one process each, in two lanes run at the same
# time: MOOE (its random-feature matrix of a 150,000-row stream holds 4.8 GB with 4,000 features) 2 in parallel, the
# other six learners 4 in parallel. Outputs that exist are skipped (a rerun of this script resumes).
# Usage: run_cpu.sh  (background)
R=$HOME/pfn-runs/mice-table1-trained-probs; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p $R/P $R/logs
[ -z "$(cat $X/streams_main.txt $X/streams_confirm.txt | tr -d '\r' | sort | uniq -d)" ] || { echo "stream names repeat"; exit 1; }
tasks() { for m in $1; do
    while read -r s; do echo "$X/../../MICE/data $s $m"; done < <(tr -d '\r' < $X/streams_main.txt)
    while read -r s; do echo "$HOME/pfn-runs/mice-confirm-cp-20261017/data $s $m"; done < <(tr -d '\r' < $X/streams_confirm.txt)
  done; }
tasks "mooe_rff4000_100_2_0.01 mooe_rff2000_100_2_0.01" > $R/tasks_mooe.txt      # slowest first
tasks "levbag srp adwinbag nse arf hat" > $R/tasks_other.txt
echo "$(date '+%F %T') start $(cat $R/tasks_mooe.txt $R/tasks_other.txt | wc -l) tasks" >> $R/progress.txt
lane() { xargs -P $1 -L 1 bash -c '~/pfn-venvs/stream/bin/python '$X'/run_trained_probs.py --data $0 --out '$R'/P --streams $1 --methods $2 \
  >> '$R'/logs/$1__$2.log 2>&1 && echo "$(date +%T) ok $1 $2" >> '$R'/progress.txt || echo "$(date +%T) FAIL $1 $2" >> '$R'/progress.txt' < $2; }
lane 2 $R/tasks_mooe.txt & lane 4 $R/tasks_other.txt & wait
echo "$(date '+%F %T') done" >> $R/progress.txt
