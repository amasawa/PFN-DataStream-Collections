#!/bin/bash
# One-shot (2026-10-07 14:4x): gas at M = 2000 needs 11-19 GB of GPU memory on its own, so the supervisor's cap fell to 1.
# Wait until that line is done, then restart the supervisor with GCAP=8 (other flags unchanged).
cd "$(dirname "$0")"; R=$PWD/../results
until [ -e ~/.reset_locks/queue_M2000/gas_M2000/done ]; do sleep 30; done
tmux kill-session -t supervisor; sleep 2
tmux new-session -d -s supervisor "NCPU=4 GCAP=8 GKILL=19000 GHITS=1 GADMIT=15000 bash $PWD/supervisor.sh 2>> $R/supervisor.err"
echo "$(date +%F_%T) after_gas.sh: gas_M2000 done -> restarted supervisor with GCAP=8" >> $R/supervisor.txt
