#!/bin/bash
# Restart loop around pool_gpu.py (operational): when the process dies (CUDA fault), the claim of its task in progress
# is released and a new process starts; it stops when a process exits cleanly (no task left). A task that killed 6
# processes is given up. Usage: pool_gpu.sh <queue dir> <worker id> <python>
Q=$1; W=$2; PY=$3; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 TS_DEVICE=cuda
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $Q/logs $Q/fails
while true; do
  $PY $X/pool_gpu.py $Q $W >> $Q/logs/w$W.log 2>&1 && { echo "$(date +%T) w$W finished" >> $Q/progress.txt; break; }
  i=$(cat $Q/running_$W 2>/dev/null); rm -f $Q/running_$W
  if [ -n "$i" ]; then
    echo x >> $Q/fails/$i; n=$(wc -l < $Q/fails/$i)
    echo "$(date +%T) w$W FAIL task $i (death $n)" >> $Q/progress.txt
    [ "$n" -lt 6 ] && rmdir $Q/claims/$i || echo "$(date +%T) w$W GAVE UP task $i" >> $Q/progress.txt
  else
    echo "$(date +%T) w$W FAIL outside a task" >> $Q/progress.txt
  fi
  sleep 15
done
