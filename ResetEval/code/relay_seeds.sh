#!/bin/bash
# Keep ~9 GPU processes busy after the TabICL run: each time a TabICL chain ends, start one seed chain on
# results/queue_seeds.txt (TabPFN seeds 1 and 2); no new chain after 04:35. At 04:40 (or when every seed chain is done)
# run the seed comparison, append to the log and commit + push (the machine restarts at 05:00).
cd "$(dirname "$0")"; R=../results; Q=$PWD/$R/queue_seeds.txt; started=0
tmux new-session -d -s gpu_sampler3 "while true; do echo \"\$(date +%F_%T),\$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)\" >> $PWD/$R/gpu_util_stage3.csv; sleep 60; done"
while true; do
  now=$(date +%H%M); icl=$(cat $R/icl[1-9].log 2>/dev/null | grep -c '^CHAIN_DONE')
  while [ $started -lt $icl ] && [ $started -lt 9 ] && ! [ "$now" -ge 0435 -a "$now" -lt 0500 ]; do
    started=$((started + 1)); tmux new-session -d -s seed$started "bash $PWD/run_queue2.sh $Q $PWD/$R/seed$started.log"
    echo "$(date +%T) started seed$started" >> $R/relay_seeds.txt; sleep 2
  done
  sd=$(cat $R/seed[1-9].log 2>/dev/null | grep -c '^CHAIN_DONE')
  { [ "$now" -ge 0440 -a "$now" -lt 0500 ]; } || { [ $started -ge 9 ] && [ $sd -ge 9 ]; } && break
  sleep 30
done
nice ~/pfn-venvs/venv/bin/python seed_compare.py 1 2 > $R/console_stage3_seeds.txt 2>&1
for s in 1 2; do nice ~/pfn-venvs/venv/bin/python analyse_backbone.py tabpfn_s$s > $R/console_stage3_tabpfn_s$s.txt 2>&1; done
tmux kill-session -t gpu_sampler3 2>/dev/null
STATS=$(awk -F, '{n++; u+=$2; if ($2 < 70) lo++} END {printf "%d samples (whole relay period, incl. the TabICL tail), mean utilisation %.1f%%, minutes below 70%%: %d", n, u/n, lo}' $R/gpu_util_stage3.csv)
{ echo; echo "## 2026-10-07 $(date +%H:%M)：阶段 3（TabPFN 种子 1、2）——运行到 05:00 重启前为止的结果（自动写入，未经人工核对）"
  echo "- seed 链 $started 条启动，$sd 条 CHAIN_DONE；重试 $(cat $R/seed[1-9].log 2>/dev/null | grep -c '^RETRY') 次；GPU：$STATS（\`results/gpu_util_stage3.csv\`）。"
  grep -E "^(== seed|S1)" $R/console_stage3_seeds.txt | sed 's/^/- /'
  echo "- 完整输出：\`results/console_stage3_seeds.txt\`、\`results/console_stage3_tabpfn_s1.txt\`、\`results/console_stage3_tabpfn_s2.txt\`；没跑完的流列在 PARTIAL 行，重启后可用 \`code/run_queue2.sh results/queue_seeds.txt\` 续跑（先删 \`~/.reset_locks/queue_seeds\`）。"; } >> ../logs/EXPERIMENT_LOG.md
echo "- $(date +%H:%M) stage 3 seeds relay ended: $started chains, $sd finished, GPU: $STATS." >> ../../env/MACHINE_LOG.md
cd ../.. && git add ResetEval/logs ResetEval/results ResetEval/code env/MACHINE_LOG.md && \
  git commit -q -m "ResetEval stage 3 (TabPFN seeds 1, 2): results up to the 05:00 restart (auto-committed)" \
    -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push origin main >> ResetEval/results/relay_seeds.txt 2>&1
echo "FINISHED $(date +%T)" >> ResetEval/results/relay_seeds.txt
