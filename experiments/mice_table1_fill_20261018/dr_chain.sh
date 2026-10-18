#!/bin/bash
# Drift-Resilient TabPFN on the 92 registered streams, one GPU process (user 2026-10-18), operational rules of
# AMENDMENT_BASELINES_20261018c.md: before every process start two 12-batch elec2 canaries in fresh processes must be
# bit-identical to each other and to the clean reference; no restart while ~/pfn-runs/GPU_STOP exists (fecs_watch.sh);
# after a process death the checkpoint of the stream in progress is moved to quarantine, so that stream restarts
# from batch 1; a stream that killed 3 processes is given up (reported). Usage: dr_chain.sh (background)
X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments; NB=$HOME/pfn-runs/mice-table1-newbase; Q=$NB/q_drtabpfn
PYDR=$HOME/pfn-venvs/drtabpfn/bin/python; CMP="$HOME/pfn-venvs/tsbase/bin/python $X/gpu_verify_20261018/verify_compare.py"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $Q/logs $Q/fails $NB/dr_canary $NB/drtabpfn_quarantine
say() { echo "$(date '+%F %T') $*" >> $Q/progress.txt; }
while true; do
  [ -e $HOME/pfn-runs/GPU_STOP ] && { say "GPU_STOP present: chain exits (restart by hand after 30 quiet minutes)"; exit 1; }
  c=$NB/dr_canary/$(date +%m%d_%H%M%S)
  for k in a b; do $PYDR $X/gpu_verify_20261018/canary_dr.py $c/$k >> $c.log 2>&1 || { say "canary $k crashed ($c)"; exit 1; }; done
  $CMP $c/a $c/b elec2__drtabpfn > $c.ab.txt && $CMP $c/a $NB/evidence_fecs_20261018/drgpu elec2__drtabpfn > $c.ref.txt \
    || { say "CANARY FAILED ($c): chain stops"; exit 1; }
  say "canary ok ($c)"
  $PYDR $X/mice_table1_fill_20261018/pool_gpu.py $Q 1 >> $Q/logs/w1.log 2>&1 && { say "finished"; exit 0; }
  i=$(cat $Q/running_1 2>/dev/null); rm -f $Q/running_1
  if [ -n "$i" ]; then
    s=$(sed -n "$((i + 1))p" $Q/tasks.txt | python3 -c 'import json, sys; print(json.load(sys.stdin)["stream"])')
    ck=$NB/drtabpfn/${s}__drtabpfn.ckpt.npz
    [ -e $ck ] && mv $ck $NB/drtabpfn_quarantine/${s}__drtabpfn.ckpt.$(date +%m%d_%H%M%S).npz
    echo x >> $Q/fails/$i; n=$(wc -l < $Q/fails/$i)
    say "process died in task $i ($s), death $n; its checkpoint quarantined (restart from batch 1)"
    [ "$n" -lt 3 ] && rmdir $Q/claims/$i || say "GAVE UP task $i ($s)"
  else
    say "process died outside a task"
  fi
  sleep 30
done
