#!/bin/bash
# One GPU process at a time (user 2026-10-18 14:3x: "只用 1 个 GPU 进程"): waits for the dtmoe development worker to
# finish, gives the tasks it gave up one more pass, then starts the drtabpfn worker (pool_gpu_dr.sh). Operational.
X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018; NB=$HOME/pfn-runs/mice-table1-newbase
busy() { ps -eo args | grep -q "[p]ool_gpu.py $1"; }
Q=$NB/q_dtmoe_dev
while busy $Q || ps -eo args | grep -q "[p]ool_gpu.sh $Q"; do sleep 60; done
if grep -q "GAVE UP" $Q/progress.txt; then
  echo "$(date +%T) chain: second pass over the given-up tasks" >> $Q/progress.txt
  rm -rf $Q/claims $Q/fails $Q/running_*
  bash $X/pool_gpu.sh $Q 1 $HOME/pfn-venvs/totgpu/bin/python
fi
echo "$(date '+%F %T') chain: dtmoe dev done, drtabpfn starts" >> $NB/resume.log
bash $X/pool_gpu_dr.sh $NB/q_drtabpfn 1 $HOME/pfn-venvs/drtabpfn/bin/python
echo "$(date '+%F %T') chain: drtabpfn worker ended" >> $NB/resume.log
