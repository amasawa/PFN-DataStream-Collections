#!/bin/bash
# wait for all six ResetEval re1 chains, then run the four remaining duo streams as parallel chains
R=/mnt/c/Users/zhwu9808/Desktop/pfn/ResetEval/results
until [ $(cat $R/re1.log $R/re1[a-e].log 2>/dev/null | grep -c CHAIN_DONE) -ge 6 ]; do sleep 30; done
cd /mnt/c/Users/zhwu9808/Desktop/pfn/MiceDuo/code
echo "RESTART $(date +%T) (after ResetEval re1; 4 parallel chains, checkpoint every 20 batches)" >> ../results/console.txt
for s in elec2 h2_airlines h2_poker h2_rialto; do
  tmux new-session -d -s duo_$s "export PYTHONWARNINGS=ignore OMP_NUM_THREADS=2; until nice ~/pfn-venvs/venv/bin/python -u check_duo.py $s >> ../results/console_$s.txt 2>&1; do echo RETRY \$(date +%T) >> ../results/console_$s.txt; sleep 45; done; echo DONE \$(date +%T) >> ../results/console_$s.txt"
done
until [ $(ls ../results/duo/*.npz 2>/dev/null | grep -vc tmp) -ge 7 ]; do sleep 30; done
~/pfn-venvs/venv/bin/python analyse_duo.py >> ../results/console.txt 2>&1; echo CHECK_DONE $(date +%T) >> ../results/console.txt
