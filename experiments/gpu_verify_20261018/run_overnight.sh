#!/bin/bash
# 2026-10-18 night, one GPU process: wait for the dtmoe development worker (not exposed: single process, no FECS since
# 14:22), one more pass over its given-up tasks, then verify_chain.sh (PLAN.md). Usage: run_overnight.sh (background)
NB=$HOME/pfn-runs/mice-table1-newbase; Q=$NB/q_dtmoe_dev; X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments
while ps -eo args | grep -q "[p]ool_gpu.sh $Q"; do sleep 60; done
[ -e $HOME/pfn-runs/GPU_STOP ] && exit 1
if grep -q "GAVE UP" $Q/progress.txt; then
  echo "$(date +%T) overnight: second pass over the given-up tasks" >> $Q/progress.txt
  rm -rf $Q/claims $Q/fails $Q/running_*
  bash $X/mice_table1_fill_20261018/pool_gpu.sh $Q 1 $HOME/pfn-venvs/totgpu/bin/python
fi
[ -e $HOME/pfn-runs/GPU_STOP ] && exit 1
bash $X/gpu_verify_20261018/verify_chain.sh
