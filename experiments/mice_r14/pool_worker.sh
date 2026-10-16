#!/bin/bash
# Round 14.b: restarts pool_worker.py (one long-lived process running many tasks) after a CUDA fault; the restarted
# process resumes its held task from run.run's checkpoint. Gives up the held task after 3 consecutive deaths without
# progress (as worker.sh) and moves on. Usage: pool_worker.sh <root> <worker id>
R=$1; W=$2; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream
mkdir -p $R/claims $R/logs $R/held
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 MICE_CKPT_EVERY=10 \
       HF_HUB_OFFLINE=1 TABPFN_DISABLE_TELEMETRY=1 TABPFN_MODEL_CACHE_DIR=$HOME/pfn-venvs/cache/tabpfn
unset PYTORCH_CUDA_ALLOC_CONF
L=$R/logs/pool_w$W.log; stall=0; last=-1; prev=""
while true; do
  ~/pfn-venvs/venv/bin/python $REPO/experiments/mice_r14/pool_worker.py $R $W >> $L 2>&1 && break
  h=$(cat $R/held/w$W 2>/dev/null)
  [ "$h" != "$prev" ] && { stall=0; last=-1; prev="$h"; }
  cur=$(awk -v h="TASK $h" '$0 == h {r = ""} /resumed at batch/ {r = $NF} END {print r}' $L)
  [ "${cur:-0}" -gt "$last" ] && { stall=0; last=${cur:-0}; } || stall=$((stall + 1))
  echo "$(date +%T) p$W FAIL $h (resumed at ${cur:-0})" >> $R/progress.txt
  if [ $stall -ge 3 ]; then
    echo "$(date +%T) p$W GAVE UP $h" >> $R/progress.txt; rm -f $R/held/w$W; stall=0; last=-1; prev=""
  fi
  sleep 20
done
echo "$(date +%T) p$W exited" >> $R/progress.txt
