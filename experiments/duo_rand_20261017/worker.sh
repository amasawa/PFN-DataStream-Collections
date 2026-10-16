#!/bin/bash
# Restarts worker.py after a process death (CUDA faults kill the process; they are never caught in-process). A task
# whose process died 3 times is marked FAILED in its claim directory, reported, and skipped; 5 deaths outside any task
# stop the wrapper. Usage: worker.sh <root> <id>
R=$1; W=$2; D=$(dirname $(readlink -f $0))
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 HF_HUB_OFFLINE=1 \
       TABPFN_DISABLE_TELEMETRY=1 TABPFN_MODEL_CACHE_DIR=$HOME/pfn-venvs/cache/tabpfn
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $R/logs; L=$R/logs/w$W.log; fails=0; prev=""
while true; do
  ~/pfn-venvs/venv/bin/python $D/worker.py $R $W >> $L 2>&1 && break
  h=$(cat $R/held/w$W 2>/dev/null)
  [ "$h" != "$prev" ] && { fails=0; prev="$h"; }
  fails=$((fails + 1)); echo "$(date +%T) w$W DIED on $h ($fails)" >> $R/progress.txt
  if [ -z "$h" ] && [ $fails -ge 5 ]; then echo "$(date +%T) w$W STOPPED: 5 deaths without a task" >> $R/progress.txt; exit 1; fi
  if [ -n "$h" ] && [ $fails -ge 3 ]; then
    touch $h/FAILED; rm -f $R/held/w$W; echo "$(date +%T) w$W FAILED $h" >> $R/progress.txt; fails=0; prev=""
  fi
  sleep 20
done
echo "$(date +%T) w$W exited" >> $R/progress.txt
