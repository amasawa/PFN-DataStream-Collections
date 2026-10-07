#!/bin/bash
# throttle duo chains: >=4 RETRY in the last 10 min -> pause the chain with most retries (if >=2 run);
# a paused chain is relaunched when another finishes and the last 10 min had <2 retries
cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1; Q=paused.txt; touch $Q
launch() { tmux new-session -d -s duo_$1 "cd ../code; export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2; until nice ~/pfn-venvs/venv/bin/python -u check_duo.py $1 >> ../results/console_$1.txt 2>&1; do echo RETRY \$(date +%T) >> ../results/console_$1.txt; sleep 45; done; echo DONE \$(date +%T) >> ../results/console_$1.txt"; }
recent() { now=$(date +%s); for f in console_*.txt; do grep -h '^RETRY' $f 2>/dev/null | while read _ t; do [ $((now - $(date -d "$t" +%s))) -lt 600 ] && echo "$f"; done; done; }
until grep -q CHECK_DONE console.txt; do
  sleep 60
  run=$(tmux ls 2>/dev/null | grep -o '^duo_[a-z0-9_]*' | grep -vE 'launch|guard')
  n=$(recent | wc -l)
  if [ $n -ge 4 ] && [ $(echo "$run" | grep -c .) -ge 2 ]; then
    worst=$(recent | sort | uniq -c | sort -rn | awk '{print $2}' | sed 's/console_//;s/.txt//' | while read s; do echo "$run" | grep -qx "duo_$s" && echo $s && break; done)
    [ -n "$worst" ] && { tmux kill-session -t duo_$worst; echo $worst >> $Q; echo "THROTTLE $(date +%T) paused $worst ($n retries in 10 min)" | tee -a console.txt; }
  elif [ -s $Q ] && [ $n -lt 2 ] && [ $(echo "$run" | grep -c .) -lt 4 ]; then
    s=$(head -1 $Q); sed -i 1d $Q; launch $s; echo "RESUME $(date +%T) relaunched $s" | tee -a console.txt
  fi
done
