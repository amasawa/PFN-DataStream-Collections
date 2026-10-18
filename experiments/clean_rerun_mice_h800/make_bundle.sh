#!/bin/bash
# Input bundle of the clean MICE rerun (HANDOFF.md), written to OneDrive. Inputs only: no original output is copied
# (the cluster run must not see any). Symlinked data directories are dereferenced. Usage: make_bundle.sh <dest dir>
set -e
D=$1; REPO=/mnt/c/Users/zhwu9808/Desktop/dataStream; RUNS=$HOME/pfn-runs; S=$(mktemp -d)
test -e $D && { echo "$D exists"; exit 1; }; mkdir -p $D
tar -C $REPO/MICE -cf $S/MICE_data.tar data
ROOTS="mice-r14-test mice-r14-exist mice-r14b-acc mice-r14-confirm mice-table1-cp-gen mice-main-cp-grid10 mice-confirm-cp-20261017
       mice-table1-probs-gen mice-tkde-control-20261009 mice-r13-bench mice-r14b-bench mice-tkde-bench-20261009
       mice-r14-dev mice-r14-devtrim"
mkdir -p $S/runs
for r in $ROOTS; do   # inputs: data dirs, held-out lists, code snapshots, task lists, frozen selections
  inc=$(cd $RUNS/$r && ls -d data* held controller source tasks.txt tasks.json kstar.json m_star.json 2>/dev/null | grep -v superseded || true)
  tar -C $RUNS/$r -chf $S/runs/$r.tar $inc
  echo "$r: $inc" >> $S/runs/CONTENTS.txt
done
for r in mice-r13-bench mice-r14b-bench mice-tkde-bench-20261009; do   # benchmark reruns: data only, fresh selections
  inc=$(cd $RUNS/$r && ls -d data* 2>/dev/null)
  tar -C $RUNS/$r -chf $S/runs/$r-h800.tar --transform "s,^,$r-h800/," $inc
  echo "$r-h800: $inc (into <root>-h800)" >> $S/runs/CONTENTS.txt
done
tar -C $HOME/ext-baselines -cf $S/ext-baselines.tar --exclude=checkpoints Drift-Resilient_TabPFN Dynamic-TMoE TOT_neurips_supp
tar -C $HOME/pfn-venvs/cache -cf $S/tabpfn_cache.tar tabpfn
# per-file SHA-256 of every input inside the tars, computed on the original files (checked after untar on the cluster)
for t in $S/MICE_data.tar $S/runs/*.tar $S/ext-baselines.tar $S/tabpfn_cache.tar; do
  mkdir -p $S/x && tar -C $S/x -xf $t && (cd $S/x && find . -type f -print0 | sort -z | xargs -0 sha256sum) > $t.files.sha256 && rm -rf $S/x
done
cp -r $S/* $D/
mkdir -p $D/claude_rules; cp $HOME/.claude/CLAUDE.md $D/claude_rules/global_CLAUDE.md
(cd $D && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
rm -rf $S; du -sh $D; cat $D/runs/CONTENTS.txt
