#!/bin/bash
# One full grid extension of the CPU baselines (AMENDMENT_BASELINES_20261018c.md, item 2): the new value of every
# boundary axis of frozen/frozen_<method>.json crossed with all values of the other axes; outputs into the same dev/P
# (distinct names); existing outputs are skipped. Usage: tune_ext.sh "<methods>" <P (<= 12)>  (background)
R=$HOME/pfn-runs/mice-table1-newbase/dev; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
DATA=/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/data; F=/mnt/c/Users/zhwu9808/Desktop/dataStream/MICE/results_paper/table1_fill/frozen
DEV="elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced"
[ "$2" -le 12 ] || { echo "at most 12 processes (amendment c)"; exit 1; }
exec 9> $R/tune_ext.lock; flock -n 9 || { echo "another tune_ext.sh is running (one invocation at a time: 12-process limit)"; exit 1; }
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
T=$R/tasks_ext_$(echo $1 | tr ' ' _)_$(date +%m%d_%H%M%S).txt
for m in $1; do
  case $m in
    fsnet|onenet) LS="16 32"; MS="0.5 0.75 0.9" ;;
    adaptz)       LS="1 16";  MS="1e-4 1e-3 1e-2" ;;
    shifts)       LS="16 32"; MS="0.5 1 2" ;;
  esac
  ext=$(python3 -c "import json; print(json.load(open('$F/frozen_$m.json'))['boundary_extension_needed'])")
  LR="1e-4 1e-3 1e-2"; ST="1 5"
  python3 -c "import json, sys; e = json.load(open('$F/frozen_$m.json'))['boundary_extension_needed']; sys.exit(0 if e else 1)" || continue
  NEWLR=$(python3 -c "import json; e = json.load(open('$F/frozen_$m.json'))['boundary_extension_needed']; print('%g' % e['lr'] if 'lr' in e else '')")
  NEWST=$(python3 -c "import json; e = json.load(open('$F/frozen_$m.json'))['boundary_extension_needed']; print(e.get('steps', ''))")
  for lr in $LR $NEWLR; do for st in $ST $NEWST; do
    case " $LR " in *" $lr "*) ol=1 ;; *) ol=0 ;; esac; case " $ST " in *" $st "*) os=1 ;; *) os=0 ;; esac
    [ $ol = 1 ] && [ $os = 1 ] && continue          # the original grid: already run
    for L in $LS; do for mech in $MS; do for s in $DEV; do echo "$m $L $lr $st $mech $s"; done; done; done
  done; done >> $T
  echo "$(date '+%F %T') $m extension $ext" >> $R/progress.txt
done
echo "$(date '+%F %T') start extension $1: $(wc -l < $T) tasks, P=$2" >> $R/progress.txt
xargs -P $2 -L 1 bash -c '~/pfn-venvs/tsbase/bin/python '$X'/run_ts.py --data '$DATA' --out '$R'/P --streams $5 --method $0 --L $1 --lr $2 --steps $3 --mech $4 \
  >> '$R'/logs/$5__$0_$1_$2_$3_$4.log 2>&1 && echo "$(date +%T) ok $0 $*" >> '$R'/progress.txt || echo "$(date +%T) FAIL $0 $*" >> '$R'/progress.txt' < $T
echo "$(date '+%F %T') done extension $1" >> $R/progress.txt
