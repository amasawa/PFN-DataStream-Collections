# Manifest: MICE paper items -> analysis scripts -> GPU result sets (traced 2026-10-18)

Paper: MICE/overleaf/tkde/main.tex (the arXiv build is generated from it by MICE/code/make_arxiv.py). Its tables are
`\input` row files written by MICE/code/make_*.py; the figure fig_recall.pdf by make_paper_fig.py. The sets in the
last column are the task sets of tasks.jsonl (all GPU); after the rerun, the analysis column is run unchanged on the
new outputs (CPU), then the make_* scripts.

| paper item (row file) | make script | analysis (CSV producer) | GPU result sets |
|---|---|---|---|
| tab_real_rows, tab_real_summary_rows, tab_grid_rows | make_paper_tables | (all.csv, same script) | results_grid_test, results_grid_test3, results_test, results_heldout, results_heldout2, results_heldout3, results_heldout4, results_heldout_tabicl (+ CPU: results_river, results_trained, results_heldout34_trained) |
| tab_metrics_rows | make_metric_table | compute_metrics, export_main_table, experiments/mice_table1_fill_20261018/export_table1_fill | results_probs, mice-r14-exist, mice-confirm-cp-20261017, mice-table1-cp-gen, mice-table1-probs-gen, mice-main-cp-grid10, drtabpfn, dtmoe (+ CPU: mice-main-trained-grid20, mice-table1-trained-probs, CPU baselines) |
| tab_misaligned_rows, tab_offset_rows | make_robust_tables | check_misaligned, check_offset | results_grid_test3, mice-tkde-control-20261009 (mis, off stages) |
| (seg_origin.csv in tab_offset) | make_robust_tables | check_seg_origin | mice-tkde-control-20261009, mice_seg_origin_r12 |
| tab_pool_grid_rows, tab_pool_real_rows | make_pool_tables | check_pool_control, pool_control_grid_ci, pool_control_grid_resources, pool_control_real | results_grid_test3, results_test, results_heldout*, mice-tkde-control-20261009 (arch, snap, ctl, snapreal) |
| tab_poolcap_rows | make_poolcap_table | experiments/mice_tkde_control/analyse_pools | mice-r13-acc, mice-r13-bench(-h800), mice-tkde-control-20261009, results_grid_test3, results_heldout2, results_heldout4, results_test |
| tab_cost_rows, tab_fifo3000_rows | make_cost_tables | experiments/mice_tkde_control/analyse_bench, fifo_m_real | mice-tkde-bench-20261009(-h800), mice-tkde-control-20261009 (fifoM), results_test, results_heldout4 |
| tab_oracle_rows, fig_recall.pdf | make_oracle_table, make_paper_fig | oracle_recall, check_identification (dev, not rerun) | mice_oracle_r11, results_grid_test |
| tab_fresh_rows, tab_segsum_rows | make_r14_tables | experiments/mice_r14/analyse_test, analyse_confirm | mice-r14-test, mice-r14-exist, mice-r14-confirm, mice-tkde-control-20261009, results_* |
| tab_cpres_rows | make_cpres_table | experiments/mice_r14/analyse_14b | mice-r14b-acc, mice-r14b-bench(-h800), mice-r14-confirm |
| numbers in the text from check_heldout4 (seed and backbone robustness) | - | check_heldout4 | results_heldout3_seed1, results_heldout4_seed1, results_heldout3_tabicl, results_heldout4_tabicl, results_heldout4_tabicl_e |

Not rerun (CPU, not exposed): results_river, results_trained, results_heldout34_trained, mice-main-trained-grid20,
mice-table1-trained-probs, the CPU baselines of Table 1 (fsnet, onenet, adaptz, shifts: mice-table1-newbase/dev and
their test runs), arf / srp of the confirmation sets. Not rerun (development; frozen choices are inputs):
results_dev, results_grid_dev, results_dt_dev, results_delay_dev, results_trained_dev, mice-r14-dev, mice-r14-devtrim.
Open items: TOT (Table 1) is not implemented yet; check_identification reads results_grid_dev (development) and
stays on the original; every "numbers in the text" outside the row files must be traced again when the paper is
regenerated (the coordinator checks every number against the new CSVs).
