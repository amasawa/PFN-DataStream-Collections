#!/bin/bash
# Round 14 worker: claims lines of <root>/tasks.txt ("<stream> <method>") atomically (mkdir on Linux storage) and runs
# each in a fresh process; a failed process is retried (run.run resumes from its checkpoint) while the resumed batch
# advances; a task is given up after 3 consecutive attempts without progress. Usage: worker.sh <root> <worker id>
R=$1; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream
mkdir -p $R/claims $R/logs
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 MICE_CKPT_EVERY=10 \
       HF_HUB_OFFLINE=1 TABPFN_DISABLE_TELEMETRY=1 TABPFN_MODEL_CACHE_DIR=$HOME/pfn-venvs/cache/tabpfn
unset PYTORCH_CUDA_ALLOC_CONF
while read -r s m; do
  [ -z "$s" ] && continue
  mkdir $R/claims/${s}__$m 2>/dev/null || continue
  L=$R/logs/${s}__$m.log; a=0; stall=0; last=-1
  while [ $stall -lt 3 ]; do
    a=$((a + 1))
    ~/pfn-venvs/venv/bin/python $REPO/experiments/mice_r14/run_task.py $R $s $m >> $L 2>&1 \
      && { echo "$(date +%T) w$2 ok $s $m attempt $a" >> $R/progress.txt; break; }
    cur=$(grep -o "resumed at batch [0-9]*" $L | tail -n 1 | grep -o "[0-9]*$")
    [ "${cur:-0}" -gt "$last" ] && { stall=0; last=${cur:-0}; } || stall=$((stall + 1))
    echo "$(date +%T) w$2 FAIL $s $m attempt $a (resumed at ${cur:-0})" >> $R/progress.txt; sleep 20
  done
  [ $stall -ge 3 ] && echo "$(date +%T) w$2 GAVE UP $s $m" >> $R/progress.txt
done < $R/tasks.txt
echo "$(date +%T) w$2 finished" >> $R/progress.txt
