#!/bin/bash
# dtmoe on the CPU, development and test (AMENDMENT_BASELINES_20261018e.md). Every task in a fresh single-thread
# process (tsbase env, TS_DEVICE unset = cpu), nice 19, at most P at once; stops on $D/STOP (written by
# dtmoe_guard.sh). Usage: dtmoe_cpu.sh probe pre <P>     (three probes, runs a into dev/P and b into probe_pre/b)
#                         dtmoe_cpu.sh grid <P>          (registered grid, 180 tasks, into dev/P)
#                         dtmoe_cpu.sh bookend <stage>   (elec2 L16 lr1e-4 s1 m1 into probe_post_<stage>)
#                         dtmoe_cpu.sh oldcmp            (informational: the 3 files of dev/P_cpu_dtmoe vs dev/P)
X=/mnt/c/Users/zhwu9808/Desktop/dataStream; NB=$HOME/pfn-runs/mice-table1-newbase; D=$NB/dtmoe_cpu
PY=$HOME/pfn-venvs/tsbase/bin/python; CMP="$PY $X/experiments/gpu_verify_20261018/verify_compare.py"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 D X PY
unset TS_DEVICE TS_DETERMINISTIC CUBLAS_WORKSPACE_CONFIG PYTORCH_CUDA_ALLOC_CONF
mkdir -p $D/logs $D/quarantine $D/deaths $D/dev/P
say() { echo "$(date '+%F %T') $*" >> $D/progress.txt; }; export -f say
tag() { python3 -c "print(f'$1__dtmoe_L$2_lr{float(\"$3\"):g}_s$4_m{float(\"$5\"):g}')"; }; export -f tag
loads() { $PY -c "import numpy as np, sys, json; z = np.load(sys.argv[1]); [z[k] for k in z.files]; \
assert json.loads(str(z['config']))['device'] == 'cpu'" $1 2>/dev/null; }; export -f loads
task() {   # <out dir> <stream> <L> <lr> <steps> <mech>: one task, fresh process; a death is quarantined and rerun once
  o=$1; t=$(tag $2 $3 $4 $5 $6); [ -e $o/$t.npz ] && loads $o/$t.npz && return 0
  while true; do
    [ -e $D/STOP ] && return 1
    nd=$(cat $D/deaths/$(basename $o)__$t 2>/dev/null | wc -l); [ $nd -ge 2 ] && { say "GAVE UP $t (2 deaths)"; return 1; }
    ls $o/$t.* > /dev/null 2>&1 && { q=$D/quarantine/$t.leftover.$(date +%m%d_%H%M%S); mkdir -p $q; mv $o/$t.* $q/; say "leftover of $t quarantined"; }
    nice -n 19 $PY $X/experiments/mice_table1_fill_20261018/run_ts.py --data $X/MICE/data --out $o --streams $2 \
      --method dtmoe --L $3 --lr $4 --steps $5 --mech $6 >> $D/logs/$(basename $o)__$t.log 2>&1 < /dev/null
    rc=$?
    if [ $rc = 0 ] && loads $o/$t.npz; then say "ok $(basename $o) $t"; return 0; fi
    if [ -e $D/STOP ]; then k=stop; else k=death; fi
    q=$D/quarantine/$t.$k.$(date +%m%d_%H%M%S); mkdir -p $q; mv $o/$t.* $q/ 2>/dev/null
    [ $k = stop ] && { say "stopped during $t (rc $rc; not counted as a death)"; return 1; }
    echo "$(date '+%F %T') rc $rc" >> $D/deaths/$(basename $o)__$t; say "death $((nd + 1)) of $t (rc $rc; partial outputs quarantined)"
  done
}; export -f task
GRID() { for lr in 1e-4 1e-3 1e-2; do for st in 1 5; do for L in 16 32; do for m in 1 2 3; do
  for s in elec2 insects_abrupt_balanced insects_gradual_balanced insects_incremental_balanced insects_incremental_reoccurring_balanced; do
    echo "$s $L $lr $st $m"; done; done; done; done; done; }
PROBES="elec2 16 1e-4 1 1
elec2 32 1e-4 1 1
insects_abrupt_balanced 32 1e-3 5 3"
[ -e $D/STOP ] && { echo "$D/STOP exists: $(cat $D/STOP)"; exit 1; }
ls $D/UNVERIFIED_* > /dev/null 2>&1 && [ "$1" != oldcmp ] && { echo "UNVERIFIED marker present: stop"; exit 1; }
nohup bash $X/experiments/mice_table1_fill_20261018/dtmoe_guard.sh > /dev/null 2>&1 < /dev/null &   # exits at once if a guard runs
case $1 in
  probe)
    [ "$2" = pre ] || exit 1; test -e $D/probe_pre && { say "probe_pre exists: refusing"; exit 1; }; mkdir -p $D/probe_pre/b
    say "probe pre start, P=$3"
    { echo "$PROBES" | sed "s|^|$D/dev/P |"; echo "$PROBES" | sed "s|^|$D/probe_pre/b |"; } |
      xargs -P $3 -L 1 bash -c 'task "$@"' _
    ok=1
    while read s L lr st m; do t=$(tag $s $L $lr $st $m)
      $CMP $D/probe_pre/b $D/dev/P $t > $D/probe_pre.$t.txt || { ok=0; say "probe pre $t DIFFERENT or MISSING"; }
    done <<< "$PROBES"
    [ $ok = 1 ] && { date "+%F %T" > $D/PROBE_PRE_PASSED; say "probe pre PASSED"; exit 0; }; say "probe pre FAILED"; exit 3 ;;
  grid)
    exec 9> $D/grid.lock; flock -n 9 || { echo "grid already running"; exit 1; }
    [ -e $D/PROBE_PRE_PASSED ] || { echo "probe pre has not passed"; exit 1; }
    say "grid start, P=$2"
    GRID | sed "s|^|$D/dev/P |" | xargs -P $2 -L 1 bash -c 'task "$@"' _
    n=0; while read s L lr st m; do f=$D/dev/P/$(tag $s $L $lr $st $m).npz; loads $f && n=$((n + 1)) || say "missing $(basename $f)"; done < <(GRID)
    say "grid pass ended: $n of 180 valid outputs" ;;
  bookend)
    o=$D/probe_post_$2; test -e $o && { say "$o exists: refusing"; exit 1; }; mkdir -p $o
    t=$(tag elec2 16 1e-4 1 1); task $o elec2 16 1e-4 1 1 || { say "bookend $2 not run (stop or gave up)"; exit 1; }
    if $CMP $o $D/dev/P $t > $o.txt; then say "bookend $2 PASSED"
    else echo "$(date '+%F %T') bookend $2 did not pass" > $D/UNVERIFIED_$2; say "UNVERIFIED_$2 written"; exit 3; fi ;;
  oldcmp)   # informational only (amendment e item 3): never used for selection
    for t in elec2__dtmoe_L16_lr0.0001_s1_m1 elec2__dtmoe_L16_lr0.0001_s1_m2 insects_gradual_balanced__dtmoe_L16_lr0.0001_s1_m1; do
      $CMP $NB/dev/P_cpu_dtmoe $D/dev/P $t > $D/oldcmp.$t.txt; say "oldcmp $t exit $?"; done ;;
esac
