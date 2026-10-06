#!/bin/bash
# Stage 3 resumed after the 04:14 shutdown: wait until the 9 restarted seed chains (results/seedR[1-9].log) are all
# CHAIN_DONE, then run the seed comparison and the per-seed analysis, append to the logs and commit + push.
# Every hour it also commits the logs so far (the machine has shut down without warning twice).
cd "$(dirname "$0")"; R=../results; last=$(date +%s)
while [ "$(cat $R/seedR[1-9].log 2>/dev/null | grep -c '^CHAIN_DONE')" -lt 9 ]; do
  sleep 60
  if [ $(( $(date +%s) - last )) -ge 3600 ]; then
    last=$(date +%s)
    (cd ../.. && git add ResetEval/results/*.log ResetEval/results/*.csv && \
      git commit -q -m "ResetEval stage 3 resumed: progress logs (auto-committed)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && \
      git push -q origin main) >> $R/finish_stage3.txt 2>&1
  fi
done
nice ~/pfn-venvs/venv/bin/python seed_compare.py 1 2 > $R/console_stage3_seeds.txt 2>&1
for s in 1 2; do nice ~/pfn-venvs/venv/bin/python analyse_backbone.py tabpfn_s$s > $R/console_stage3_tabpfn_s$s.txt 2>&1; done
tmux kill-session -t gpu_sampler3 2>/dev/null
STATS=$(awk -F, '$1 >= "2026-10-07_06" {n++; u+=$2; if ($2 < 70) lo++} END {printf "%d samples, mean utilisation %.1f%%, minutes below 70%%: %d", n, u/n, lo}' $R/gpu_util_stage3.csv)
{ echo; echo "## 2026-10-07 $(date +%H:%M)：阶段 3 续跑（TabPFN 种子 1 剩余、种子 2、两个种子的合成流）运行完毕（自动写入，未经人工核对）"
  echo "- 9 条链 CHAIN_DONE；重试 $(cat $R/seedR[1-9].log | grep -c '^RETRY') 次；续跑期间 GPU：$STATS（\`results/gpu_util_stage3.csv\`）。"
  grep -E "^(== seed|S1|seed [12], )" $R/console_stage3_seeds.txt | sed 's/^/- /'
  for s in 1 2; do grep -E "^(H[1-4]'|T[12]|PARTIAL)" $R/console_stage3_tabpfn_s$s.txt | sed "s/^/- [s$s] /"; done
  echo "- 完整输出：\`results/console_stage3_seeds.txt\`、\`results/console_stage3_tabpfn_s1.txt\`、\`results/console_stage3_tabpfn_s2.txt\`。"; } >> ../logs/EXPERIMENT_LOG.md
echo "- $(date +%H:%M) stage 3 resumed run ended: 9 chains, GPU: $STATS." >> ../../env/MACHINE_LOG.md
cd ../.. && git add ResetEval/logs ResetEval/results ResetEval/code env/MACHINE_LOG.md && \
  git commit -q -m "ResetEval stage 3 (TabPFN seeds 1, 2, real + synthetic): finished, analysis (auto-committed)" \
    -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push origin main >> ResetEval/results/finish_stage3.txt 2>&1
echo "FINISHED $(date +%T)" >> ResetEval/results/finish_stage3.txt
