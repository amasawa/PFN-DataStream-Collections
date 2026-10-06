#!/bin/bash
# Utilisation watchdog until the 05:00 restart: every 5 min, if the mean GPU utilisation over the last 5 min is below 90%,
# start one extra chain (run_queue2.sh) on results/queue_seeds.txt (shared locks with the relay's seed chains); once every
# line of that queue is claimed, use results/queue_seeds3.txt (TabPFN seed 3) instead. At most 6 extra chains, none when
# GPU memory > 26 GB, none after 04:35. Decisions go to results/keep_busy.txt.
cd "$(dirname "$0")"; R=$PWD/../results; extra=0
while true; do
  sum=0; for i in $(seq 30); do sum=$((sum + $(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits))); sleep 10; done
  mean=$((sum / 30)); mem=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits); now=$(date +%H%M)
  [ "$now" -ge 0435 -a "$now" -lt 0500 ] && { echo "$(date +%T) stop (04:35), $extra extra chains started" >> $R/keep_busy.txt; break; }
  if [ $mean -lt 90 ] && [ $extra -lt 6 ] && [ $mem -lt 26000 ]; then
    Q=$R/queue_seeds.txt; [ $(ls ~/.reset_locks/queue_seeds 2>/dev/null | wc -l) -ge $(wc -l < $Q) ] && Q=$R/queue_seeds3.txt
    extra=$((extra + 1)); tmux new-session -d -s extra$extra "bash $PWD/run_queue2.sh $Q $R/extra$extra.log"
    echo "$(date +%T) mean util $mean%, mem $mem MiB -> started extra$extra on $(basename $Q)" >> $R/keep_busy.txt
  else
    echo "$(date +%T) mean util $mean%, mem $mem MiB, extra $extra" >> $R/keep_busy.txt
  fi
done
