#!/bin/bash
# Local GPU order of AMENDMENT_BASELINES_20261018d.md item 3: dtmoe probes -> Drift-Resilient TabPFN -> (if the probes
# passed) dtmoe development grid -> post-grid bookend probes; then stops for the coordinator. Usage: gpu_local.sh (background)
X=/mnt/c/Users/zhwu9808/Desktop/dataStream/experiments/mice_table1_fill_20261018; D=$HOME/pfn-runs/mice-table1-newbase/dtmoe_local
mkdir -p $D; say() { echo "$(date '+%F %T') gpu_local: $*" >> $D/progress.txt; }
bash $X/dtmoe_local.sh probe pre; P=$?; say "probes exit $P"
[ -e $HOME/pfn-runs/GPU_STOP ] && exit 1
bash $X/dr_chain.sh; R=$?; say "dr_chain exit $R"
[ -e $HOME/pfn-runs/GPU_STOP ] && exit 1
[ $R = 0 ] || { say "dr_chain did not finish cleanly (canary failure or a stop): nothing more runs"; exit 1; }
[ $P = 0 ] || { say "probes did not pass: dtmoe path stopped (user decides the fallback)"; exit 0; }
bash $X/dtmoe_local.sh grid; say "grid exit $?"
[ -e $HOME/pfn-runs/GPU_STOP ] && exit 1
bash $X/dtmoe_local.sh probe post_grid; say "post-grid bookend exit $? ; waiting for the coordinator (selection)"
