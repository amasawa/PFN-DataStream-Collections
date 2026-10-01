# PFN × Zhilin OOD under Beyond-IID splits — project root

| folder | content | start here |
|---|---|---|
| `refs/` | reference PDFs, original categories kept: `zhilinpapers/` (Zhao & Cao OOD papers), `noiidpapers/` (TabArena, Beyond IID), `baseline/` (TabDPT) | — |
| `exp/` | code, raw results, figures, English draft | [`exp/README.md`](exp/README.md) |
| `logs/` | how deep the exploration went and how it was done | [`logs/DEFECT_EXPERIMENTS.md`](logs/DEFECT_EXPERIMENTS.md) → first section "最终汇总" |
| `overleaf/` | ICML 2026 LaTeX paper (`icml2026/main.tex`, `refs.bib`, figures, official style) | upload the folder to Overleaf, compile with pdflatex |
| `data/` | parquet backup of the 11 BeyondArena tasks used (`beyondarena/<task>/{data.parquet,splits.json,meta.json}`), checkpoint list (`ckpt/README.md`) | [`data/export_beyondarena.py`](data/export_beyondarena.py) |
| `env/` | exact package versions of the two environments | `exp/README.md` §1 |

## logs/ in detail
- `DEFECT_EXPERIMENTS.md` — research logic: final summary (template), then rounds 1–17 in time order, incl. negative results.
- `EXPERIMENT_LOG.md` — commands, files changed, key outputs, errors, per experiment task (first part T1–T6 detailed; later tasks one section each).
- `20260927-PFN-session-b8578f99-dialogue.md` — this session turn by turn (user input / Claude reply, 02:06–13:17 UTC).
- `20260927-PFN-session-c275378b-dialogue.md` — an earlier short session the same day.
- `20260927-PFN-ZhilinNonIID-Experiments.log`, `20260927-PFN-BeyondIID-ZhilinOOD-ExperimentAndMethod.log` — the two logs from before this session.
- `claude_memory/` — Claude Code memory of this project (user preferences: state runtime before running, lightweight exp/, env and data outside exp/, Zhilin-style AUROC evaluation, method-paper goal). To reuse on a new machine, copy into `~/.claude/projects/<project-dir>/memory/`.

## Status (2026-09-27)
Defect A (main) and Defect B (supporting) established; method AgDR frozen and evaluated on held-out trials;
ICML draft compiled. Open: theory for the agreement weight, `% TODO verify` entries in `overleaf/icml2026/refs.bib`,
more non-IID datasets for statistical power (see `logs/DEFECT_EXPERIMENTS.md` F6).

## Status (2026-09-29, evening)
Direction A fixed: the paper borrows the I-Div framework (Zhao et al., NeurIPS 2024). New AISTATS draft in
`overleaf/aistats2026/` (theory: Thm 1 familiarity, Thm 2 decomposition, Prop 2 OOD posterior, Cor 1 rank statistic,
Thm 3 group conformal, Props 3-4 entity columns; method GOR-adapter; final test on trials 15-19 done once:
mean AUROC 79.9 vs 76.7 for the best baseline). The ICML draft in `overleaf/icml2026/` (AgDR) is kept unchanged.
Theory notes: `logs/THEORY_IDIV.md`; run log: `logs/EXPERIMENT_LOG.md`; today's dialogue:
`logs/20260929-PFN-session-4f58d8bd-dialogue.md`.

## Status (2026-09-30)
Proofs completed in `overleaf/aistats2026/` (Thm 1(f) pointwise familiarity, Cor 2 entity columns, self-contained Thm 3(b),
Cor 3 valid GOR calibration, Prop 5 monotone adapter). GOR-v1 failed on one cardio final trial (AUROC 39.2); post-hoc
diagnosis: negative adapter weights invert on extreme OOD rows. Round 2: sign-constrained adapter chosen on trials 20-24
by a pre-set rule, frozen, final test 2 on trials 25-29 run once: mean AUROC 80.9 vs 77.9 (kNN†, p = .057, n.s.), best
mean rank / FPR95 / worst table. Both final tests are reported in the paper. Parallel runner: `exp/par_run.py`.
