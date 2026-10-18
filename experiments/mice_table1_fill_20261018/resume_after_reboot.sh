#!/bin/bash
# Restart of the Table 1 fill after the Windows reboot of 2026-10-18 (operational). Every run function skips outputs that
# exist and writes atomically, so all claims are released and the queues are simply restarted.
#   resume_after_reboot.sh cpu   -> CPU jobs: trained learners with probabilities, dev grids of shifts/adaptz/fsnet/onenet
#   resume_after_reboot.sh gpu N -> GPU jobs after the GPU checks: N long-lived dtmoe dev workers, staggered by 60 s
#   resume_after_reboot.sh probs -> 1 worker for ddm/ltm probabilities on the generator streams
X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018
NB=$HOME/pfn-runs/mice-table1-newbase
case $1 in
  cpu)
    nohup setsid bash $X/run_cpu.sh > /dev/null 2>&1 < /dev/null &
    nohup setsid bash $X/tune_ts.sh "shifts adaptz fsnet onenet" 6 > /dev/null 2>&1 < /dev/null & ;;
  gpu)
    Q=$NB/q_dtmoe_dev; rm -rf $Q/claims $Q/running_* $Q/fails
    for w in $(seq 1 ${2:-1}); do nohup setsid bash $X/pool_gpu.sh $Q $w $HOME/pfn-venvs/totgpu/bin/python > /dev/null 2>&1 < /dev/null & sleep 60; done ;;
  probs)
    R=$HOME/pfn-runs/mice-table1-probs-gen; rm -rf $R/claims
    for f in $R/P/*.npz; do case $f in *__probs.npz) ;; *) [ -e "${f%.npz}__probs.npz" ] || rm -f "$f";; esac; done
    nohup setsid bash $X/../mice_confirm_cp_20261017/worker.sh $R 1 > /dev/null 2>&1 < /dev/null & ;;
esac
echo "$(date '+%F %T') resume_after_reboot.sh $*" >> $NB/resume.log
