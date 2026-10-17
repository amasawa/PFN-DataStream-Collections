# Real-stream confirmation of detected segmentation (CIC-IDS2017, Bitcoin Heist; PokerHand supplementary)

Pre-registration: `experiments/mice_confirm_cp_20261017/PLAN.md` (commit df475cc, pushed before the first task).
Evaluator: `experiments/mice_confirm_cp_20261017/analyse.py` (unchanged since registration), run once on the complete
outputs of `~/pfn-runs/mice-confirm-cp-20261017` on 2026-10-18 04:41.

## Execution
- Start 2026-10-17 23:23 (after waiting for the GPU and RAM of another project), end 2026-10-18 04:40 (about 5.3 hours).
- 66 GPU tasks (11 segments x micecp1000_500, micev1000_500, winens1000, ddm1000, ltm1000_75, fifo1000) and 22 CPU tasks
  (ARF, SRP). Every task succeeded on its first attempt; no CUDA fault, no restart, no task given up.
- Deviations from PLAN.md: none. Operational: a third GPU worker was started at 02:26 (PLAN: "2 workers, 3 if stable";
  26 of 26 tasks had succeeded and GPU utilisation was 36% on the light Bitcoin Heist segments).

## Hypotheses (9 primary segments; points = percentage points of accuracy)
| | Rule | Result | Met |
|---|---|---|---|
| H1 | mean of mice_cp - mice, lower bound > -0.2 | mean -0.005, lb -0.013 | yes |
| H2 | every segment: lb of mice_cp - fifo > -0.3 | lowest: cc_btc_2016 -0.246, cc_btc_2017 -0.182 | yes |
| H3 | every segment: mice_cp - max(fifo, ddm) >= -0.5 | lowest: cc_btc_2016 -0.172 | yes |
| H4 | per-source mean above fifo, ltm, ddm, winens; above all four on >= 6 of 9 | per-source margins bitcoinheist -0.055, cicids2017 -0.013; above all four on 4 of 9 | **no** |
| H5 | mice_cp above mice_cp_nopool on >= 6 of 9 | 8 of 9 | yes |

Descriptive (blocks of 50 batches): H1 lb -0.013; H2 lowest lb cc_btc_2016 -0.265 (all > -0.3).

H4 fails on both parts. Bitcoin Heist: fifo (98.081%) and ddm (98.060%) have higher means than mice_cp (98.026%);
on cc_btc_2016 ltm is 0.53 points higher. CIC-IDS2017: ltm (99.310%) is above mice_cp (99.297%); on cc_cic_fri ltm is
0.23 points higher. The margins are small because every primary segment is near its majority rate or separable
(primary-segment means 98.2-98.6% for every TabPFN method), as stated under "Expected difficulty" in PLAN.md.

## Mean accuracy (%), primary segments and per source
| method | primary (9) | Bitcoin Heist (5) | CIC-IDS2017 (4) | PokerHand (2, supplementary) |
|---|---|---|---|---|
| mice_cp | 98.591 | 98.026 | 99.297 | 93.817 |
| mice | 98.595 | 98.028 | 99.305 | 93.796 |
| mice_cp_nopool | 98.546 | 98.018 | 99.206 | 92.887 |
| fifo | 98.569 | 98.081 | 99.178 | 93.110 |
| ltm | 98.211 | 97.333 | 99.310 | 90.537 |
| ddm | 98.493 | 98.060 | 99.035 | 84.646 |
| winens | 98.439 | 97.929 | 99.076 | 91.817 |
| arf | 98.384 | 97.788 | 99.129 | 72.182 |
| srp | 98.600 | 98.029 | 99.313 | 76.455 |

Probability metrics, mean over the 9 primary segments (x100; ECE, half Brier and log-loss lower is better):
mice_cp F1 75.79, AUC 90.79, ECE 0.49, Brier 1.18, log-loss 5.72; mice 75.87 / 90.48 / 0.49 / 1.18 / 5.84;
fifo 76.90 / 90.21 / 0.49 / 1.21 / 6.50; ddm 76.71 / 89.65 / 0.55 / 1.28 / 7.14; ltm 81.14 / 93.45 / 2.52 / 1.72 / 7.19;
winens 74.26 / 88.87 / 0.70 / 1.30 / 6.79; mice_cp_nopool 75.68 / 89.95 / 0.59 / 1.21 / 6.48.

Files: acc.csv, metrics.csv (fractions), hypotheses.csv, summary.csv (percent, points). Use of the result (PLAN.md):
H4 is not met, so the paper states that the real-stream confirmation of the detected method did not pass H4 and lists
it in the limitations; H1, H2, H3 and H5 passed.
