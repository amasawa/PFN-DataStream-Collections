#!/bin/bash
# GPU task queue for the Table 1 fill (operational): <queue dir>/tasks.txt holds one command per line; each worker claims
# a line atomically (mkdir on Linux storage), runs it in a fresh process and retries it (up to 6 attempts) when the
# process dies (intermittent CUDA faults); tasks resume from their own checkpoints where they have one, otherwise they
# restart (deterministic). Usage: gpu_queue.sh <queue dir> <worker id>
Q=$1; mkdir -p $Q/claims $Q/logs
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 TS_DEVICE=cuda
unset PYTORCH_CUDA_ALLOC_CONF
n=0
while IFS= read -r cmd; do
  n=$((n + 1)); [ -z "$cmd" ] && continue
  mkdir $Q/claims/$n 2>/dev/null || continue
  for a in 1 2 3 4 5 6; do
    bash -c "$cmd" >> $Q/logs/$n.log 2>&1 && { echo "$(date +%T) w$2 ok $n attempt $a" >> $Q/progress.txt; break; }
    echo "$(date +%T) w$2 FAIL $n attempt $a" >> $Q/progress.txt; sleep 10
    [ $a = 6 ] && echo "$(date +%T) w$2 GAVE UP $n" >> $Q/progress.txt
  done
done < $Q/tasks.txt
echo "$(date +%T) w$2 finished" >> $Q/progress.txt
