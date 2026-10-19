#!/bin/bash
# Supplement bundle of phases P3 and P4 (REGISTRATION_P3_P4_20261020.md): the P3 weights (pinned Hugging Face commits,
# urls.txt), the LimiX code (commit 516bf39) and the CURE code (commit f7c6b2f; its data directory left out: not used).
# Per-file SHA-256 inside every tar, SHA256SUMS over the bundle. Usage: make_bundle_p3.sh <dest dir>
set -e
D=$1; S=$(mktemp -d)
test -e $D && { echo "$D exists"; exit 1; }; mkdir -p $D
tar -C $HOME -cf $S/p3_weights.tar --exclude=dl.sh mice-p3-weights
tar -C $HOME/ext-baselines -cf $S/ext-baselines-p3.tar --exclude=.git --exclude="*.pdf" --exclude=doc --exclude="*.egg-info" \
    --exclude=__pycache__ --exclude=CURE-ICML-FMSD/data LimiX CURE-ICML-FMSD
for t in $S/p3_weights.tar $S/ext-baselines-p3.tar; do
  mkdir -p $S/x && tar -C $S/x -xf $t && (cd $S/x && find . -type f -print0 | sort -z | xargs -0 sha256sum) > $t.files.sha256 && rm -rf $S/x
done
(cd $HOME/ext-baselines/LimiX && echo "LimiX $(git rev-parse HEAD)"; cd $HOME/ext-baselines/CURE-ICML-FMSD && echo "CURE-ICML-FMSD $(git rev-parse HEAD)"; \
 for r in LimiX CURE-ICML-FMSD; do cd $HOME/ext-baselines/$r; test -z "$(git status --porcelain --untracked-files=no)" && echo "$r clean" || echo "$r MODIFIED"; done) > $S/COMMITS.txt
cp $S/* $D/
(cd $D && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
rm -rf $S; du -sh $D; cat $D/COMMITS.txt
