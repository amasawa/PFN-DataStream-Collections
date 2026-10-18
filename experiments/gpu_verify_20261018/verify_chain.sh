#!/bin/bash
# Verification replays of GPU outputs exposed to the FECS fault periods (PLAN.md). One GPU process at a time, a fresh
# process per task, outputs under ~/pfn-runs/verify-20261018 (never in the original run directories). Stops when
# ~/pfn-runs/GPU_STOP exists (written by fecs_watch.sh) or a canary fails. Usage: verify_chain.sh <stage> ...
#   stages, in this order by default: canary dtmoe confirm_cp r14_confirm probs_gen cp_gen
REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream; X=$REPO/experiments/gpu_verify_20261018; V=$HOME/pfn-runs/verify-20261018
NB=$HOME/pfn-runs/mice-table1-newbase; STOP=$HOME/pfn-runs/GPU_STOP; LOG=$V/progress.txt
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 MICE_CKPT_EVERY=10 \
       HF_HUB_OFFLINE=1 TABPFN_DISABLE_TELEMETRY=1 TABPFN_MODEL_CACHE_DIR=$HOME/pfn-venvs/cache/tabpfn
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $V; say() { echo "$(date '+%F %T') $*" >> $LOG; }
halt() { say "CHAIN STOP: $*"; echo "$(date '+%F %T') $*" > $V/CHAIN_STOP; exit 1; }
gate() { [ -e $STOP ] && halt "GPU_STOP present"; [ -e $V/CHAIN_STOP ] && exit 1
  [ $(( $(date +%s) - $(stat -c %Y $HOME/pfn-runs/fecs_watch.log.last 2>/dev/null || echo 0) )) -lt 150 ] || halt "fecs_watch not alive"; true; }
CMP="$HOME/pfn-venvs/tsbase/bin/python $X/verify_compare.py"

canary() {   # two DR canaries in fresh processes must be bit-identical to each other and to the clean reference
  gate; local c=$V/canary/$(date +%m%d_%H%M%S); mkdir -p $c
  for k in a b; do ~/pfn-venvs/drtabpfn/bin/python $X/canary_dr.py $c/$k >> $c/log 2>&1 || halt "canary $k crashed ($c)"; gate; done
  $CMP $c/a $c/b elec2__drtabpfn > $c/cmp_ab.txt || halt "canary a != b ($c)"
  $CMP $c/a $NB/evidence_fecs_20261018/drgpu elec2__drtabpfn > $c/cmp_ref.txt || halt "canary != reference ($c)"
  say "canary ok $c"
}

# one task of set <set>: remove any earlier replay output of <stem> (complete replay, no resumed checkpoint), run <cmd>
# into <vdir>, compare the files of <stem> with <odir>; one fresh retry after a crash; a mismatch stops the chain
clean() { rm -f $1/$2.npz $1/$2.pkl $1/$2.closes.pkl $1/$2__probs.npz $1/$2.ckpt*; }   # run.py: <dst>.ckpt(.tmp)
task() { local set=$1 vdir=$2 odir=$3 stem=$4; shift 4
  gate; local t0=$(date +%T) lg=$V/logs/$set/$stem.log cm=$V/cmp/$set/$stem.txt; mkdir -p $V/logs/$set $V/cmp/$set
  clean $vdir $stem
  if ! "$@" >> $lg 2>&1 < /dev/null; then
    gate; clean $vdir $stem; say "crash $set $stem, fresh retry"
    "$@" >> $lg 2>&1 < /dev/null || { gate; halt "crash twice $set $stem"; }
  fi
  gate
  if $CMP $vdir $odir "${stem}" > $cm.tmp; then mv $cm.tmp $cm; say "IDENTICAL $set $stem ($t0-$(date +%T))"; return; fi
  mv $cm.tmp $cm.DIFF; say "DIFFERENT $set $stem ($t0-$(date +%T)): $(grep -E 'DIFFERENT|MISSING' $cm.DIFF | tr '\n' ';')"
  echo "$stem" >> $V/MISMATCH.txt
  halt "mismatch $stem (PLAN.md: a second independent replay is decided by hand)"
}

dtmoe() {   # dtmoe development tasks 1-38 of the queue (task 0 was verified at 12:48)
  local vp=$V/dtmoe_dev/P; mkdir -p $vp
  for i in $(seq 1 38); do
    read s L lr st m < <(sed -n "$((i + 1))p" $NB/q_dtmoe_dev/tasks.txt | python3 -c 'import json, sys; t = json.load(sys.stdin)
print(t["stream"], t["L"], t["lr"], t["steps"], t["mech"])')
    stem=$(python3 -c "print(f'${s}__dtmoe_L$L' + f'_lr{float(\"$lr\"):g}_s$st' + f'_m{float(\"$m\"):g}')")
    [ -n "$s" ] || halt "dtmoe queue line $((i + 1)) unreadable"
    [ -e $NB/dev/P/$stem.npz ] || { say "skip $stem (no original)"; continue; }
    [ -e $V/cmp/dtmoe/$stem.txt ] && continue
    task dtmoe $vp $NB/dev/P $stem env TS_DEVICE=cuda ~/pfn-venvs/totgpu/bin/python -c "
import sys, torch; sys.path.insert(0, '$REPO/experiments/mice_table1_fill_20261018'); import run_ts; torch.set_num_threads(1)
sys.path.insert(0, f'{run_ts.EXT}/{run_ts.METHODS[\"dtmoe\"].REPO}')
run_ts.run('$REPO/MICE/data', '$vp', '$s', 'dtmoe', $L, $lr, $st, $m)"
  done
}

mice_set() {   # <name> <original root> <run_task.py> <method order>: every task of the original tasks.txt
  local name=$1 orig=$2 rt=$3 order=$4 root=$V/$1 nrun=0 nskip=0
  mkdir -p $root/P
  # a copy (never a link into the original run), checked byte for byte at every start
  [ -e $root/data ] || { rm -rf $root/data.part; cp -r $orig/data $root/data.part && mv $root/data.part $root/data; }
  diff -r -q $orig/data $root/data > /dev/null || halt "data copy differs ($name)"
  for m in $order; do
    while read -r s mm _ <&3; do
      [ "$mm" = "$m" ] || continue
      [ -e $orig/P/${s}__${m}.npz ] || { say "skip $name ${s}__$m (no original)"; nskip=$((nskip + 1)); continue; }
      nrun=$((nrun + 1))
      [ -e $V/cmp/$name/${s}__${m}.txt ] && continue   # replayed and compared already
      task $name $root/P $orig/P ${s}__${m} ~/pfn-venvs/venv/bin/python $rt $root $s $m
    done 3< <(tr -d '\r' < $orig/tasks.txt)
  done
  local nt=$(grep -c . $orig/tasks.txt)
  say "set $name: $nrun tasks replayed and compared, $nskip without original, tasks.txt has $nt lines"
  [ $((nrun + nskip)) -eq $nt ] || halt "set $name: $nrun + $nskip tasks != $nt lines of tasks.txt"
}

mkdir -p $V/logs $V/cmp
for st in ${@:-canary dtmoe confirm_cp r14_confirm probs_gen cp_gen}; do
  gate; say "stage $st start"
  case $st in
    canary) canary ;;
    dtmoe) canary; dtmoe ;;
    confirm_cp) canary; mice_set confirm_cp $HOME/pfn-runs/mice-confirm-cp-20261017 $REPO/experiments/mice_confirm_cp_20261017/run_task.py \
                  "micecp1000_500 micev1000_500 fifo1000 ddm1000 ltm1000_75 winens1000" ;;
    r14_confirm) canary; mice_set r14_confirm $HOME/pfn-runs/mice-r14-confirm $REPO/experiments/mice_r14/run_task.py \
                  "$(tr -d '\r' < $HOME/pfn-runs/mice-r14-confirm/tasks.txt | awk '{print $2}' | awk '!a[$0]++' | tr '\n' ' ')" ;;
    probs_gen) canary; mice_set probs_gen $HOME/pfn-runs/mice-table1-probs-gen $REPO/experiments/mice_confirm_cp_20261017/run_task.py "ddm1000 ltm1000_75" ;;
    cp_gen) canary; mice_set cp_gen $HOME/pfn-runs/mice-table1-cp-gen $REPO/experiments/mice_r14/run_task.py "micecp1000_500" ;;
  esac
  say "stage $st done"
done
say "chain done"
