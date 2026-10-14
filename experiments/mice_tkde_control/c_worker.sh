#!/bin/bash
# Round 13 part C worker (amendment 2026-10-14): claims tasks "<k>_<idx>" atomically (mkdir on Linux storage) and runs
# each in a fresh process; a failed process is retried (run.run resumes from its checkpoint) as long as the resumed
# batch keeps advancing; a task is given up after 3 consecutive attempts without progress.
# Claims are not released: before relaunching after a crash, remove the claims of tasks without a final npz (their
# .ckpt is resumed). Completeness (all 100 npz load) is checked by the analysis. Usage: c_worker.sh <worker id>
R=~/pfn-runs/mice-r13-acc; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream
mkdir -p $R/claims $R/logs
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 MICE_CKPT_EVERY=10 \
       HF_HUB_OFFLINE=1 TABPFN_DISABLE_TELEMETRY=1 TABPFN_MODEL_CACHE_DIR=$HOME/pfn-venvs/cache/tabpfn
unset PYTORCH_CUDA_ALLOC_CONF
for k in 2 4; do for i in $(seq 0 49); do
  mkdir $R/claims/${k}_$i 2>/dev/null || continue
  a=0; stall=0; last=-1
  while [ $stall -lt 3 ]; do
    a=$((a + 1))
    MICE_R13_K=$k ~/pfn-venvs/venv/bin/python $REPO/MICE/code/pool_cap_run.py $i >> $R/logs/${k}_$i.log 2>&1 \
      && { echo "$(date +%T) w$1 ok k$k task $i attempt $a" >> $R/progress.txt; break; }
    cur=$(grep -o "resumed at batch [0-9]*" $R/logs/${k}_$i.log | tail -n 1 | grep -o "[0-9]*$")
    [ "${cur:-0}" -gt "$last" ] && { stall=0; last=${cur:-0}; } || stall=$((stall + 1))
    echo "$(date +%T) w$1 FAIL k$k task $i attempt $a (resumed at ${cur:-0})" >> $R/progress.txt; sleep 20
  done
  [ $stall -ge 3 ] && echo "$(date +%T) w$1 GAVE UP k$k task $i" >> $R/progress.txt
done; done
echo "$(date +%T) w$1 finished" >> $R/progress.txt
