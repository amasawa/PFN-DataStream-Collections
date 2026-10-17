#!/bin/bash
# Waits until the GPU and RAM are free (5 consecutive checks, 1 min apart: GPU memory used < 12 GB, utilisation < 30 %,
# RAM available > 8 GB), then starts 2 GPU workers on <root>/tasks.txt and, in parallel, the CPU tasks (arf, srp) one
# after the other with the stream venv. Usage: wait_and_launch.sh  (in tmux)
R=$HOME/pfn-runs/mice-confirm-cp-20261017; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream; X=$REPO/experiments/mice_confirm_cp_20261017
ok=0
while [ $ok -lt 5 ]; do
  read mem util < <(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr -d ',')
  avail=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
  if [ "$mem" -lt 12000 ] && [ "$util" -lt 30 ] && [ "$avail" -gt 8 ]; then ok=$((ok + 1)); else ok=0; fi
  echo "$(date '+%F %T') gpu_mem=${mem}MiB util=${util}% ram_avail=${avail}GB ok=$ok" >> $R/wait.log
  sleep 60
done
echo "$(date '+%F %T') starting workers" >> $R/progress.txt
for w in 1 2; do bash $X/worker.sh $R $w & sleep 30; done
( export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
  for s in $(cut -d' ' -f1 $R/tasks.txt | uniq); do for m in arf srp; do
    ~/pfn-venvs/stream/bin/python $X/run_task.py $R $s $m >> $R/logs/cpu_${s}__$m.log 2>&1 \
      && echo "$(date +%T) cpu ok $s $m" >> $R/progress.txt || echo "$(date +%T) cpu FAIL $s $m" >> $R/progress.txt
  done; done; echo "$(date +%T) cpu finished" >> $R/progress.txt ) &
wait
