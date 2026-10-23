# 1. Rerun check (2026-10-23)

## 1.1 Source

The cluster rerun (8 A800, experiments/clean_rerun_mice_h800, log MICE/logs/CLUSTER_RERUN_LOG.md) was returned to the Mac as ~/Desktop/mice_h800_results, 26140 files, all of which pass SHA256SUMS. Because the returned files contain outputs only, the run inputs (data/, kstar.json) are taken from the tars in mice_h800_bundle/runs. The make_* and check_* scripts of MICE/code and experiments/ ran unchanged in an isolated workspace, so neither the repository nor the returned files were modified.

## 1.2 Files

**tables/** holds the paper tables regenerated from the rerun. **diff_vs_paper.txt** compares them cell by cell with the paper's current row files: the in-context policies differ by at most 0.3 points and no conclusion changes. Differences of up to 4.3 points occur only in the trained-learner column, because the river ensembles are not deterministic. **table1_summary_rerun.csv** and **newbase_streams.csv** are the Table 1 readout (scripts/export_table1_fill_rerun.py, scripts/nb_metrics.py), and **tab_main_rows_paper.tex** is the Table 1 that went into the paper: the trained learners use the rerun (user decision, option B), and dtmoe was dropped. **backbone_robustness.txt** holds the TabPFN 3.5 and TabDPT backbones (scripts/p3.py).

## 1.3 Not checked

cost and cpres keep the timings of the original machine (user decision), because the r13 and tkde benchmarks were cancelled. For the same reason the accuracy part of poolcap (analyse_pools a1acc) cannot be read out. The oracle table needs new TabPFN calls (oracle_recall.py). The scripts contain the absolute paths of the session's workspace.
