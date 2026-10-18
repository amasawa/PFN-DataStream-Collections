#!/bin/bash
# pool_gpu.sh for long drtabpfn tasks (operational, 2026-10-18 14:3x): a task whose checkpoint advanced since its last
# death starts its death count again, so only 6 deaths in a row without checkpoint progress give a task up (a
# 450-batch stream at ~7 s per batch outlives several CUDA faults on this machine). A separate file because a running
# bash script must not be edited. Usage: pool_gpu_dr.sh <queue dir> <worker id> <python>
Q=$1; W=$2; PY=$3; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $Q/logs $Q/fails
while true; do
  $PY $X/pool_gpu.py $Q $W >> $Q/logs/w$W.log 2>&1 && { echo "$(date +%T) w$W finished" >> $Q/progress.txt; break; }
  i=$(cat $Q/running_$W 2>/dev/null); rm -f $Q/running_$W
  if [ -n "$i" ]; then
    ck=$(sed -n "$((i + 1))p" $Q/tasks.txt | python3 -c 'import json, sys; t = json.load(sys.stdin)
print(t["out"] + "/" + t["stream"] + "__drtabpfn.ckpt.npz" if t["kind"] == "dr" else "")')
    [ -n "$ck" ] && [ -e "$ck" ] && [ -e $Q/fails/$i ] && [ "$ck" -nt $Q/fails/$i ] && rm $Q/fails/$i
    echo x >> $Q/fails/$i; n=$(wc -l < $Q/fails/$i)
    echo "$(date +%T) w$W FAIL task $i (death $n in a row)" >> $Q/progress.txt
    [ "$n" -lt 6 ] && rmdir $Q/claims/$i || echo "$(date +%T) w$W GAVE UP task $i" >> $Q/progress.txt
  else
    echo "$(date +%T) w$W FAIL outside a task" >> $Q/progress.txt
  fi
  sleep 15
done
