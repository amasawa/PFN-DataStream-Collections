#!/bin/bash
# usage: runone.sh <model-tag> <task N|C>
B=$(dirname "$0"); m=$1; t=$2; P=$B/task$t.txt; O=$B/out_${m}_$t; s=$(date +%s.%N)
case $m in
  sonnet) claude -p --model claude-sonnet-5-5 --output-format json --tools "" --setting-sources "" < $P > $O.json 2>$O.err ;;
  haiku)  claude -p --model claude-haiku-4-5-20251001 --output-format json --tools "" --setting-sources "" < $P > $O.json 2>$O.err ;;
  luna)   codex exec --skip-git-repo-check -s read-only -C $B/empty_$t -m gpt-6-luna -c model_reasoning_effort='"medium"' -o $O.txt "$(cat $P)" </dev/null > $O.log 2>&1 ;;
  flash)  d=$B/mimo_flash_$t; mkdir -p $d; (cd $d && timeout 1200 ~/.mimocode/bin/mimo run "$(cat $P)" --agent auditor -m xiaomi/mimo-v2.6-flash --variant low --format json --dir $d </dev/null > $O.json 2>$O.err) ;;
  pro)    d=$B/mimo_pro_$t; mkdir -p $d; (cd $d && timeout 1800 ~/.mimocode/bin/mimo run "$(cat $P)" --agent auditor -m xiaomi/mimo-v2.6-pro --variant high --format json --dir $d </dev/null > $O.json 2>$O.err) ;;
esac
echo "$m $t exit=$? sec=$(echo "$(date +%s.%N) - $s" | bc)" >> $B/timing.txt
