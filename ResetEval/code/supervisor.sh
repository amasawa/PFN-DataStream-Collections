#!/bin/bash
# Unattended supervisor (logs/EXPERIMENT_LOG.md, 2026-10-07 06:22). Limits from the user: GPU utilisation >= 90%, memory
# <= 20 GB (enforced for both GPU memory and system RAM). Every minute it samples utilisation, GPU memory and RAM:
#  - GPU memory > 19.5 GB on two samples in a row: stop the newest GPU chain, release its line (it is redone later) and
#    lower the GPU chain cap by one; RAM > 19.5 GB: stop the newest CPU chain (else the newest GPU chain).
#  - every 5 min: if the 5-min mean utilisation < 90%, GPU memory < 16.5 GB, RAM < 17 GB and a GPU queue has an
#    unclaimed line, start one GPU chain (two if < 70%); keep up to NCPU CPU chains while CPU queues have work.
#  - a queue whose lines are all complete is analysed once by stage_done.sh (append to the log, commit, push).
#  - every hour: commit and push the logs.
# Environment: NCPU, GCAP, GKILL (MiB, default 19500), GHITS (samples in a row, default 2), GADMIT (default 16500).
# Chains: tmux g<N> (run_queue3.sh over GPU_Q, in order), c<N> (over CPU_Q); the earlier seedR1-9 (run_queue2.sh) count
# as GPU chains. Decisions go to results/supervisor.txt.
cd "$(dirname "$0")"; C=$PWD; R=$(cd ../results && pwd); PY=~/pfn-venvs/venv/bin/python
GPU_Q="$R/queue_seeds.txt $R/queue_M500.txt $R/queue_M2000.txt $R/queue_seeds3b.txt $R/queue_tabdpt.txt"; NGQ=$(echo $GPU_Q | wc -w)
CPU_Q="$R/queue_hsens.txt $R/queue_trained_ht.txt $R/queue_trained_nb.txt"; NCQ=$(echo $CPU_Q | wc -w)
NCPU=${NCPU:-6}; GCAP=${GCAP:-12}; ng_new=$(ls $R/g*.log 2>/dev/null | wc -l); nc_new=$(ls $R/c*.log 2>/dev/null | wc -l); hi=0; cool=0; tick=0; lastc=$(date +%s); utils=()
log() { echo "$(date +%F_%T) $*" >> $R/supervisor.txt; }
chains() { tmux ls -F '#{session_name} #{session_created}' 2>/dev/null | awk -v p="$1" '$1 ~ p' | sort -k2n | awk '{print $1}'; }
stop_chain() {                                     # stop tmux session $1, release the line it was running
  local s=$1 pp lk
  pp=$(tmux list-panes -t "$s" -F '#{pane_pid}' 2>/dev/null | head -1)
  [ -n "$pp" ] || return
  lk=$(cat ~/.reset_locks/run/$pp 2>/dev/null)      # run_queue3.sh chains; seedR lines: release_seedR_orphans
  kids=$(pgrep -P "$pp")
  tmux kill-session -t "$s"; sleep 2
  for k in $kids; do pkill -TERM -P $k 2>/dev/null; kill -TERM $k 2>/dev/null; done
  sleep 5
  if [ -n "$lk" ] && [ -d "$lk" ] && [ ! -e "$lk/done" ]; then rmdir "$lk" && log "released $lk"; fi
  rm -f ~/.reset_locks/run/$pp
  log "stopped $s (pane $pp)"
}
release_seedR_orphans() {                          # lines of queue_seeds claimed by stopped seedR chains and unfinished
  for lk in ~/.reset_locks/queue_seeds/*; do
    k=$(basename $lk); s=${k%_s*}; sd=${k##*_s}
    pgrep -f "reset_eval.py $s\$" >/dev/null && continue
    [ "$($PY -c "import sys; sys.path.insert(0,'$C'); import queue_status as q; print(q.line_status('$R/queue_seeds.txt', '$s x $sd')[0])")" = True ] && continue
    rmdir $lk 2>/dev/null && log "released orphan $lk"
  done
}
log "start NCPU=$NCPU GCAP=$GCAP"
while true; do
  u=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits); gm=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
  ram=$(free -m | awk '/^Mem/{print $2 - $7}'); utils+=($u); [ ${#utils[@]} -gt 5 ] && utils=("${utils[@]:1}")
  G=($(chains '^(g[0-9]+|seedR[0-9])$')); Cc=($(chains '^c[0-9]+$'))
  if [ "$gm" -gt ${GKILL:-19500} ]; then hi=$((hi + 1)); else hi=0; fi
  if [ $hi -ge ${GHITS:-2} ] && [ ${#G[@]} -gt 1 ]; then
    GCAP=$(( ${#G[@]} - 1 )); log "GPU memory $gm MiB > ${GKILL:-19500} x${GHITS:-2} -> stop newest GPU chain, cap $GCAP"
    stop_chain ${G[-1]}; release_seedR_orphans; hi=0; cool=10
  elif [ "$ram" -gt 19500 ]; then
    log "RAM $ram MiB > 19500 -> stop newest chain"
    if [ ${#Cc[@]} -gt 0 ]; then stop_chain ${Cc[-1]}; NCPU=$(( ${#Cc[@]} - 1 )); else stop_chain ${G[-1]}; release_seedR_orphans; GCAP=$(( ${#G[@]} - 1 )); fi
    cool=10
  fi
  [ $cool -gt 0 ] && cool=$((cool - 1))
  tick=$((tick + 1))
  if [ $((tick % 5)) = 0 ]; then
    mean=$(( ($(IFS=+; echo "${utils[*]}")) / ${#utils[@]} ))
    ST=$($PY queue_status.py $GPU_Q $CPU_Q); gun=$(echo "$ST" | head -$NGQ | awk '{s+=$4} END {print s}'); cun=$(echo "$ST" | tail -$NCQ | awk '{s+=$4} END {print s}')
    log "util5 $mean% gmem $gm ram $ram gpu_chains ${#G[@]}/$GCAP cpu_chains ${#Cc[@]}/$NCPU unclaimed gpu $gun cpu $cun | $(echo $ST | tr '\n' ' ')"
    if [ $cool = 0 ] && [ $mean -lt 90 ] && [ $gm -lt ${GADMIT:-16500} ] && [ $ram -lt 17000 ] && [ $gun -gt 0 ]; then
      n=1; [ $mean -lt 70 ] && n=2
      for i in $(seq $n); do
        [ $(( ${#G[@]} + i - 1 )) -ge $GCAP ] && break
        ng_new=$((ng_new + 1)); tmux new-session -d -s g$ng_new "bash $C/run_queue4.sh $R/g$ng_new.log $GPU_Q"; log "started g$ng_new"
        sleep 2
      done
    fi
    while [ ${#Cc[@]} -lt $NCPU ] && [ $cun -gt 0 ] && [ $ram -lt 17000 ]; do
      nc_new=$((nc_new + 1)); tmux new-session -d -s c$nc_new "bash $C/run_queue4.sh $R/c$nc_new.log $CPU_Q"; log "started c$nc_new"
      Cc+=(c$nc_new); sleep 2
    done
    echo "$ST" | while read q n done un; do
      [ "$done" = "$n" ] && [ ! -e $R/stage_done_$q.txt ] && { log "queue $q complete -> stage_done.sh"; bash $C/stage_done.sh $q > $R/stage_done_$q.txt 2>&1; }
    done
  fi
  if [ $(( $(date +%s) - lastc )) -ge 3600 ]; then
    lastc=$(date +%s)
    (cd $R/../.. && git add ResetEval/results/*.log ResetEval/results/*.csv ResetEval/results/*.txt ResetEval/logs ResetEval/code && \
      git commit -q -m "ResetEval unattended run: progress logs (auto-committed)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && \
      git push -q origin main) >> $R/supervisor.txt 2>&1
  fi
  sleep 60
done
