#!/bin/bash
# Item 2 of PLAN.md: waits until the GPU and RAM are free (5 consecutive checks, 1 min apart), then starts 2 round-14
# workers on <root>/tasks.txt (= tasks_cp_gen.txt). Usage: wait_gpu.sh  (background)
R=$HOME/pfn-runs/mice-table1-cp-gen; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream; ok=0
while [ $ok -lt 5 ]; do
  read mem util < <(nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits | tr -d ',')
  avail=$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
  if [ "$mem" -lt 12000 ] && [ "$util" -lt 30 ] && [ "$avail" -gt 8 ]; then ok=$((ok + 1)); else ok=0; fi
  echo "$(date '+%F %T') gpu_mem=${mem}MiB util=${util}% ram_avail=${avail}GB ok=$ok" >> $R/wait.log
  sleep 60
done
echo "$(date '+%F %T') starting workers" >> $R/progress.txt
for w in 1 2; do bash $REPO/experiments/mice_r14/worker.sh $R $w & sleep 30; done
wait
