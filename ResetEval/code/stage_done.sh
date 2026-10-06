#!/bin/bash
# Called once by supervisor.sh when every line of queue $1 is complete: run its analysis, append the verdict lines to
# logs/EXPERIMENT_LOG.md (marked as auto-written), commit and push.
cd "$(dirname "$0")"; R=../results; PY=~/pfn-venvs/venv/bin/python; q=$1; out=$R/console_$q.txt
case $q in
  queue_seeds)   { $PY seed_compare.py 1 2; for s in 1 2; do $PY analyse_backbone.py tabpfn_s$s; done; } > $out 2>&1 ;;
  queue_seeds3b) { $PY seed_compare.py 1 2 3; $PY analyse_backbone.py tabpfn_s3; } > $out 2>&1 ;;
  queue_M500)    $PY analyse_backbone.py tabpfn_M500 > $out 2>&1 ;;
  queue_M2000)   $PY analyse_backbone.py tabpfn_M2000 > $out 2>&1 ;;
  queue_hsens)   $PY analyse_variants.py hsens > $out 2>&1 ;;
  queue_trained_ht) $PY analyse_variants.py trained ht > $out 2>&1 ;;
  queue_trained_nb) $PY analyse_variants.py trained nb > $out 2>&1 ;;
esac
{ echo; echo "## 2026-10-07 起的无人值守运行：$q 全部完成，$(date '+%m-%d %H:%M') 自动分析（自动写入，未经人工核对）"
  grep -E "^(== seed|S1|seed [0-9], |H[1-4]'|T[12] |TR[1-3] |HS |full reset|  full reset|  \+hedge|PARTIAL|tail over|[0-9]+ common)" $out | grep -v Warning | sed 's/^ */- /'
  echo "- 完整输出：\`results/console_$q.txt\`。"; } >> ../logs/EXPERIMENT_LOG.md
cd ../.. && git add ResetEval/logs ResetEval/results/*.txt ResetEval/results/*.csv ResetEval/results/*.log ResetEval/code && \
  git commit -q -m "ResetEval $q: complete, analysis (auto-committed)" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && \
  git push -q origin main
echo "DONE $(date +%T)"
