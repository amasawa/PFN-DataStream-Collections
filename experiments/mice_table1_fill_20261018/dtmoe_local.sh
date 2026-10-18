#!/bin/bash
# dtmoe on the local GPU in strict deterministic mode (AMENDMENT_BASELINES_20261018d.md items 4, 5, 7). One process at
# a time; stops on ~/pfn-runs/GPU_STOP. Usage: dtmoe_local.sh probe <name>   (three probes; twice if name = pre)
#                                              dtmoe_local.sh grid            (registered grid, 180 tasks)
X=/mnt/c/Users/zhwu9808/Desktop/dataStream; NB=$HOME/pfn-runs/mice-table1-newbase; D=$NB/dtmoe_local
CMP="$HOME/pfn-venvs/tsbase/bin/python $X/experiments/gpu_verify_20261018/verify_compare.py"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 CUDA_LAUNCH_BLOCKING=0 TS_DEVICE=cuda TS_DETERMINISTIC=1 \
       CUBLAS_WORKSPACE_CONFIG=:4096:8
unset PYTORCH_CUDA_ALLOC_CONF
mkdir -p $D/logs $D/quarantine; say() { echo "$(date '+%F %T') $*" >> $D/progress.txt; }
guard() {  # amendment d item 2: fecs_watch alive (heartbeat < 150 s) and no GPU_STOP
  [ -e $HOME/pfn-runs/GPU_STOP ] && { say "GPU_STOP present: stop"; exit 1; }
  [ $(( $(date +%s) - $(stat -c %Y $HOME/pfn-runs/fecs_watch.log.last 2>/dev/null || echo 0) )) -lt 150 ] || { say "fecs_watch not alive: stop"; exit 1; }
}
keep_watch_log() { cp $HOME/pfn-runs/fecs_watch.log $1/fecs_watch.log.$(date +%m%d_%H%M%S) 2>/dev/null; }
loads() { $HOME/pfn-venvs/tsbase/bin/python -c "import numpy as np, sys; z = np.load(sys.argv[1]); [z[k] for k in z.files]" $1 2>/dev/null; }
one() {   # <out dir> <stream> <L> <lr> <steps> <mech>: one task in a fresh process
  guard
  $HOME/pfn-venvs/totgpu/bin/python $X/experiments/mice_table1_fill_20261018/run_ts.py --data $X/MICE/data --out $1 \
    --streams $2 --method dtmoe --L $3 --lr $4 --steps $5 --mech $6 >> $D/logs/$(echo ${1#$D/} | tr / _)__$2_$3_$4_$5_$6.log 2>&1 < /dev/null
}
tag() { python3 -c "print(f'$1__dtmoe_L$2_lr{float(\"$3\"):g}_s$4_m{float(\"$5\"):g}')"; }
PROBES="elec2,16,1e-4,1,1 elec2,32,1e-4,1,1 insects_abrupt_balanced,32,1e-3,5,3"
PASSED=0; STAGE=$1_${2:-}
on_exit() {   # every exit: keep the fecs_watch log; a bookend that did not pass flags its stage (amendment d item 7)
  keep_watch_log $D
  if [ "$STAGE" != probe_pre ] && [ "${STAGE#probe_}" != "$STAGE" ] && [ $PASSED != 1 ]; then
    echo "$(date '+%F %T') bookend $STAGE did not pass" > $D/UNVERIFIED_${STAGE#probe_}; say "UNVERIFIED_${STAGE#probe_} written"
  fi
}
trap on_exit EXIT
case $1 in
  probe)
    for k in $([ "$2" = pre ] && echo "a b" || echo a); do
      o=$D/probe_$2/$k; test -e $o && { say "$o exists: refusing"; exit 1; }; mkdir -p $o
      for p in $PROBES; do IFS=, read s L lr st m <<< "$p"; one $o $s $L $lr $st $m || { say "probe $2/$k $s L$L crashed or raised"; exit 2; }; done
    done
    ok=1
    for p in $PROBES; do IFS=, read s L lr st m <<< "$p"; t=$(tag $s $L $lr $st $m)
      ref=$D/probe_pre/a; [ "$2" = pre ] && cmpd=$D/probe_pre/b || cmpd=$D/probe_$2/a
      $CMP $cmpd $ref $t > $D/probe_$2.$t.txt || { ok=0; say "probe $2 $t DIFFERENT"; }
    done
    keep_watch_log $D/probe_$2
    [ $ok = 1 ] && { PASSED=1; say "probe $2 PASSED"; exit 0; }
    if [ "$2" = pre ]; then   # item 4: a third run of each probe, for classification only (never to choose)
      o=$D/probe_pre/c; mkdir -p $o
      for p in $PROBES; do IFS=, read s L lr st m <<< "$p"; one $o $s $L $lr $st $m; t=$(tag $s $L $lr $st $m)
        $CMP $o $D/probe_pre/a $t > $D/probe_pre.c_vs_a.$t.txt; ca=$?; $CMP $o $D/probe_pre/b $t > $D/probe_pre.c_vs_b.$t.txt; cb=$?
        say "probe pre classification $t: c vs a exit $ca, c vs b exit $cb"; done
    fi                        # (a failed bookend is flagged by on_exit)
    say "probe $2 FAILED"; exit 3 ;;
  grid)
    o=$D/dev/P; mkdir -p $o
    for lr in 1e-4 1e-3 1e-2; do for st in 1 5; do for L in 16 32; do for m in 1 2 3; do
      for s in elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced; do
        t=$(tag $s $L $lr $st $m); [ -e $o/$t.npz ] && loads $o/$t.npz && continue
        for a in 1 2; do
          ls $o/$t.* > /dev/null 2>&1 && { mkdir -p $D/quarantine/$t.pre$a; mv $o/$t.* $D/quarantine/$t.pre$a/; say "leftover of $t quarantined"; }
          if one $o $s $L $lr $st $m && loads $o/$t.npz && [ ! -e $HOME/pfn-runs/GPU_STOP ]; then say "ok $t"; break; fi
          mkdir -p $D/quarantine/$t.$a; mv $o/$t.* $D/quarantine/$t.$a/ 2>/dev/null
          [ -e $HOME/pfn-runs/GPU_STOP ] && { say "GPU_STOP during $t: partial outputs quarantined, stop"; exit 1; }
          say "death $a of $t (partial outputs quarantined)"; [ $a = 2 ] && say "GAVE UP $t"
        done
      done; done; done; done; done
    keep_watch_log $D/dev; say "grid done" ;;
esac
