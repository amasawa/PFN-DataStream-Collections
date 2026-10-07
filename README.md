# dataStream — tabular foundation models on data streams

Split on 2026-10-07 from the joint repository `oodpfn` (which also held the OOD projects AgDR and GOR, now in the
`ood` repository). History of the folders below was kept with `git filter-repo`; commit hashes therefore differ from
those quoted in older log entries (the old hashes still resolve in `oodpfn`).

| folder | content | start here |
|---|---|---|
| `MICE/` | Mixture of In-Context Experts for recurring drift (MOOE-based); also the stream data (`MICE/data/`) used by the other projects | `MICE/logs/EXPERIMENT_LOG.md` |
| `DriftTriage/` | benign vs harmful vs novel drift for in-context learners (I-Div-based; method line stopped) | `DriftTriage/logs/EXPERIMENT_LOG.md` |
| `ResetEval/` | evaluation paper (TMLR): error-driven context resets on TFMs — heavy left tail, removed by hedging against FIFO | `ResetEval/logs/EXPERIMENT_LOG.md` |
| `GrayContext/` | contaminated label streams for in-context learners | `GrayContext/logs/EXPERIMENT_LOG.md` |
| `MiceDuo/` | MICE-DUO, a separate paper from MICE | `MiceDuo/logs/EXPERIMENT_LOG.md` |
| `Emergence/` | a class turning from OOD into ID inside the context | `Emergence/logs/EXPERIMENT_LOG.md` |
| `FeatEvo/` | TFMs on streams with an evolving feature space | `FeatEvo/logs/EXPERIMENT_LOG.md` |
| `InterTFM/` | disagreement between TFMs as a drift signal (feasibility check only) | `InterTFM/logs/EXPERIMENT_LOG.md` |
| `pdfs/`, `env/`, `skills/`, `SETUP.md` | shared with the `ood` repository (same content at the split) | `SETUP.md` |

Each project keeps its own experiment log; never mix them. Several projects read `MICE/data/` through relative paths
(`../../MICE/data`), so keep the folders side by side. Machine issues and their fixes: `env/MACHINE_LOG.md`.
