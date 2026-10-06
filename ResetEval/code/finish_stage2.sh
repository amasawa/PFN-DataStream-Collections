#!/bin/bash
# wait for all TabICL queue chains, then run the stage-2 analysis and append a pointer to the log (auto-generated)
cd "$(dirname "$0")"
# finish when all 9 chains are done, or at 04:45 at the latest (the machine restarts at 05:00): then analyse what is complete
until [ $(cat ../results/icl[1-9].log 2>/dev/null | grep -c '^CHAIN_DONE') -ge 9 ] || [ "$(date +%H%M)" -ge 0445 -a "$(date +%H%M)" -lt 0500 ]; do sleep 60; done
NDONE=$(cat ../results/icl[1-9].log 2>/dev/null | grep -c '^CHAIN_DONE')
nice ~/pfn-venvs/venv/bin/python analyse_backbone.py tabicl > ../results/console_stage2_tabicl.txt 2>&1
{ echo; if grep -q '^PARTIAL' ../results/console_stage2_tabicl.txt; then
    echo "## 2026-10-07 $(date +%H:%M)：阶段 2（TabICL）在 05:00 重启前没有跑完——以下只是部分结果，判定不作数（自动写入，未经人工核对）"
    grep '^PARTIAL' ../results/console_stage2_tabicl.txt | cut -c1-300 | sed 's/^/- /'
    echo "- 重启后：删除 \`~/.reset_locks/queue_tabicl\`，重开 9 条链（\`code/run_queue.sh\`，同一队列），完成的文件自动跳过；然后再运行 \`code/finish_stage2.sh\`。"
  else
    echo "## 2026-10-07 $(date +%H:%M)：阶段 2（TabICL）运行完毕，分析已自动运行（自动写入，未经人工核对）"
  fi
  echo "- 队列链 $NDONE/9 条 CHAIN_DONE；重试 $(cat ../results/icl[1-9].log | grep -c '^RETRY') 次。判定结果（原样摘自 \`results/console_stage2_tabicl.txt\`）："
  grep -E "^(H1'|H2'|H3'|H4'|T1|T2|tail)" ../results/console_stage2_tabicl.txt | sed 's/^/  - /'; } >> ../logs/EXPERIMENT_LOG.md
U=../results/gpu_util_stage2.csv
STATS=$(awk -F, -v s="$(head -1 $U | cut -d, -f1)" '{n++; u+=$2; if ($2 < 70) lo++; m+=$3} END {printf "%d samples (one per minute), mean utilisation %.1f%%, minutes below 70%%: %d, mean memory %.0f MiB", n, u/n, lo, m/n}' $U)
RET=$(cat ../results/icl[1-9].log | grep -c '^RETRY')
echo "- 运行期间的 GPU：$STATS（\`results/gpu_util_stage2.csv\`）；CUDA 重试 $RET 次。机器方面的记录见 \`env/MACHINE_LOG.md\`。" >> ../logs/EXPERIMENT_LOG.md
{ echo; echo "## 2026-10-07 $(date +%H:%M) ResetEval stage 2 (TabICL), unattended run finished (auto-written)"
  echo "- 9 queue chains; CUDA retries: $RET; GPU: $STATS."; } >> ../../env/MACHINE_LOG.md
tmux kill-session -t gpu_sampler 2>/dev/null
echo FINISHED $(date +%T) >> ../results/finish_stage2.txt
