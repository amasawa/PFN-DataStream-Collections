#!/bin/bash
# Development grid of PLAN_BASELINES.md ("Tuning") for the CPU methods: every (method, configuration, development
# stream) is one process; P in parallel; existing outputs are skipped. Usage: tune_ts.sh "<methods>" <P>
R=$HOME/pfn-runs/mice-table1-newbase/dev; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
DATA=/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/data
DEV="elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p $R/P $R/logs
for m in $1; do
  case $m in
    fsnet|onenet) LS="16 32"; MS="0.5 0.75 0.9" ;;
    adaptz)       LS="1 16";  MS="1e-4 1e-3 1e-2" ;;
    shifts)       LS="16 32"; MS="0.5 1 2" ;;
    dtmoe)        LS="16 32"; MS="1 2 3" ;;
  esac
  for lr in 1e-4 1e-3 1e-2; do for st in 1 5; do for L in $LS; do for mech in $MS; do for s in $DEV; do
    echo "$m $L $lr $st $mech $s"; done; done; done; done; done
done > $R/tasks_$(echo $1 | tr ' ' _).txt
echo "$(date '+%F %T') start $1: $(wc -l < $R/tasks_$(echo $1 | tr ' ' _).txt) tasks, P=$2" >> $R/progress.txt
nice_=$([ "$1" = dtmoe ] && echo 19 || echo 0); nice -n $nice_ xargs -P $2 -L 1 bash -c '~/pfn-venvs/tsbase/bin/python '$X'/run_ts.py --data '$DATA' --out '$R'/P --streams $5 --method $0 --L $1 --lr $2 --steps $3 --mech $4 \
  >> '$R'/logs/$5__$0_$1_$2_$3_$4.log 2>&1 && echo "$(date +%T) ok $0 $*" >> '$R'/progress.txt || echo "$(date +%T) FAIL $0 $*" >> '$R'/progress.txt' < $R/tasks_$(echo $1 | tr ' ' _).txt
echo "$(date '+%F %T') done $1" >> $R/progress.txt
