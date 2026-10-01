# Tabular anomaly-detection suites (ADBench, ODDS, DAMI, successors) and whether reviewers expect them in a held-out-class OOD paper on grouped/temporal tables (state: October 2026)

Reading conventions: "Cited Findings" are what a source states (verification level noted where I only saw a search snippet rather than the page itself). "Inferences" are my own assessment. Sources I could not open are listed under "Gaps", not cited as fact. Draft context read: `overleaf/aistats2026/main.tex` (EXPERIMENTS, RELATED WORK, LIMITATIONS, DATASETS appendix, `tab_data.tex`).

## Q1. ADBench: the 57 datasets, the 47 tabular ones, how anomalies are defined, sizes, group/time structure, overlap with our nine tables

### Takeaway
ADBench is 47 pre-existing tabular sets (mostly inherited from ODDS/DAMI, i.e. classification data with one class or a downsampled minority relabelled as anomaly) plus 10 CV/NLP embedding sets; it uses random stratified 70/30 splits and explicitly excludes time-series and graph structure, so it carries no group IDs or timestamps. Only two of our nine tables have counterparts (cardiotocography as `cardio`/`Cardiotocography`, covertype as `cover`), and in both cases the ADBench version is a different task (binary, re-sampled, patient/area identity dropped).

### Cited Findings
- ADBench evaluates 30 algorithms on 57 datasets; "47 are existing ones and we create 10"; the 10 new ones are CV/NLP sets turned into tabular form via ResNet18 / BERT embeddings — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- For the created multi-class sets the construction is: "we set one of the multi-classes as normal, downsample the remaining classes to 5% of the total instances as anomalies, and report the average results over all the respective classes" — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- ADBench keeps only datasets whose anomaly ratio is below 40% — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- Split protocol: "We use 70% data for training and the remaining 30% as the test set. We use stratified sampling to keep the anomaly ratio consistent. We repeat each experiment 3 times" — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- Scope statement: "we focus on the tabular AD algorithms and datasets in this work"; benchmarks for time-series and graph AD "are different from tabular AD in nature" — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- Three supervision settings: unsupervised (no labels), semi-supervised (a fraction of labelled anomalies, 1% to 100%), supervised (full binary labels). 14 unsupervised algorithms (PCA, OCSVM, LOF, CBLOF, COF, HBOS, KNN, SOD, IForest, ECOD, COPOD, LODA, DAGMM, DeepSVDD), 7 semi-supervised (incl. XGBOD, DeepSAD, REPEN, DevNet, PReNet, FEAWAD), 9 supervised (incl. RF, XGBoost, LightGBM, CatBoost, ResNet, FT-Transformer) — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426); algorithm table in [ADBench README](https://github.com/Minqi824/ADBench)
- The 47 tabular datasets (samples / features / anomalies / % anomaly), from the README table — [ADBench README](https://github.com/Minqi824/ADBench):
  ALOI 49534/27/1508/3.04; annthyroid 7200/6/534/7.42; backdoor 95329/196/2329/2.44; breastw 683/9/239/34.99; campaign 41188/62/4640/11.27; **cardio 1831/21/176/9.61**; **Cardiotocography 2114/21/466/22.04**; celeba 202599/39/4547/2.24; census 299285/500/18568/6.20; **cover 286048/10/2747/0.96**; donors 619326/10/36710/5.93; fault 1941/27/673/34.67; fraud 284807/29/492/0.17; glass 214/7/9/4.21; Hepatitis 80/19/13/16.25; http 567498/3/2211/0.39; InternetAds 1966/1555/368/18.72; Ionosphere 351/32/126/35.90; landsat 6435/36/1333/20.71; letter 1600/32/100/6.25; Lymphography 148/18/6/4.05; magic.gamma 19020/10/6688/35.16; mammography 11183/6/260/2.32; mnist 7603/100/700/9.21; musk 3062/166/97/3.17; optdigits 5216/64/150/2.88; PageBlocks 5393/10/510/9.46; pendigits 6870/16/156/2.27; Pima 768/8/268/34.90; satellite 6435/36/2036/31.64; satimage-2 5803/36/71/1.22; shuttle 49097/9/3511/7.15; skin 245057/3/50859/20.75; smtp 95156/3/30/0.03; SpamBase 4207/57/1679/39.91; speech 3686/400/61/1.65; Stamps 340/9/31/9.12; thyroid 3772/6/93/2.47; vertebral 240/6/30/12.50; vowels 1456/12/50/3.43; Waveform 3443/21/100/2.90; WBC 223/9/10/4.48; WDBC 367/30/10/2.72; Wilt 4819/5/257/5.33; wine 129/13/10/7.75; WPBC 198/33/47/23.74; yeast 1484/8/507/34.16.
- The 10 non-tabular ones: CIFAR10, FashionMNIST, MNIST-C, MVTec-AD, SVHN (512-d embeddings), Agnews, Amazon, Imdb, Yelp, 20newsgroups (768-d embeddings), each at 5% anomalies — [ADBench README](https://github.com/Minqi824/ADBench)
- Size range summary: from 80 rows (Hepatitis) to 619,326 (donors); 3 to 1,555 features; anomaly ratio 0.03% to 39.91% — computed from the table in [ADBench README](https://github.com/Minqi824/ADBench)
- Later criticism of ADBench (MacrOData, Ding, Klüttermann, Wen, Chen, Akoglu; KDD 2026 per the arXiv listing): 57 datasets "severely restricts diversity and statistical power"; near-duplicates exist ("Cardio and Cardiography, or Satellite and Satimage-2"); selection "somewhat arbitrary"; inclusion of non-tabular embeddings; saturation (BreastW >90% AUROC, Yeast near chance); "Thyroid dataset exhibits only five features compared to the standard six"; Wine has "a mere 10 anomalies"; ADBench "likely exhibits datasets with outliers that align well with Gaussian noise", i.e. mostly global outliers — [MacrOData, arXiv 2602.09329](https://arxiv.org/html/2602.09329)
- Our draft's nine tables: cardio (UCI, 2,126 rows, 22 features, 3 classes, grouped by patient, OOD = pathologic, 176 rows), mice, dementia, covertype (512,625 rows, 13 features, 3 classes, grouped by area, OOD = Krummholz), asp, consumer, ghana, sdss17, students — draft `tab_data.tex` (local file, no URL)

### Inferences
- Overlap is exactly two of nine: cardiotocography and covertype. Nothing in the ADBench table corresponds to mice protein, SDSS17, students dropout, dementia (OASIS), consumer complaints, ghana, or ASP-POTASSCO (checked name by name against the 47 rows above).
- ADBench `cardio` has 176 anomalies, the same number as our pathologic OOD class (176 rows). The ADBench/ODDS version therefore appears to use the same semantic class as the anomaly, but as a binary one-class problem with the "suspect" class removed (1831 = 2126 minus the suspect rows, consistent with the UCI class counts) and with no patient identifier. `Cardiotocography` (2114 rows, 466 anomalies) is the DAMI variant of the same data. I did not open the ODDS page to confirm the construction (see Gaps).
- ADBench `cover` (286,048 rows, 10 features, 2,747 anomalies) is a two-class subset using only the quantitative attributes; our covertype is the BeyondArena grouped task with 3 classes and wilderness area as group. These are not the same task.
- Because the split is random and stratified, and because the datasets ship as bare `X, y` arrays, no ADBench dataset can express "ID rows from unseen groups versus OOD rows", which is the quantity our paper studies. Reintroducing groups would require going back to the raw UCI files, which is what BeyondArena already did for cardiotocography.
- Many ADBench sets are binary after relabelling (one "normal" class, one "anomaly" class), so they fail our rule R1 (at least two ID classes after hold-out): there is no in-context classifier to speak of with one ID class, and MSP is undefined.

### Gaps
- The ODDS site (odds.cs.stonybrook.edu) refused the TLS handshake on every attempt, so the per-dataset construction notes for "Cardio" and "ForestCover" (which class is the outlier, which is discarded, downsampling) are not verified from the primary source.
- The ADBench appendix table B1 (which records the upstream source of each of the 47 sets: ODDS, DAMI, etc.) was not readable; the provenance "mostly ODDS/DAMI" is my recollection plus MacrOData's characterisation, not a quote.
- ADRepository (Pang et al.) was not checked; no source retrieved.
- DAMI / Campos et al. 2016 primary source not opened; only the count (23 datasets) via MacrOData.

## Q2. Successor suites 2023-2026 and how they are built

### Takeaway
The successors keep the same recipe (classification or flagged-category tables turned into inlier/outlier problems, random splits) and scale it up; none adds group or time structure, and one of them explicitly calls one-vs-rest construction a "proxy" for OOD detection.

### Cited Findings
- Earlier suites by size: ODDS 31 datasets, DAMI 23, Emmott et al. 20, ADBench 57 — [MacrOData](https://arxiv.org/html/2602.09329)
- MacrOData = OddBench (790 datasets, real-world semantic anomalies) + OvRBench (856 datasets, one-vs-rest "statistical outliers") + SynBench (800 synthetic), 2,446 in total — [MacrOData abstract](https://arxiv.org/abs/2602.09329)
- OddBench construction: from TabLib, drop tables with <1000 rows or <3 numerical features, then search for "datasets where exactly one categorical feature value is associated with anomaly detection (e.g., 'fraud', 'failure', 'defect')" — [MacrOData](https://arxiv.org/html/2602.09329)
- OvRBench construction: classification tables from TabLib, OpenML-CC18, AutoML, TabZilla, Talent-CLS, TabRepo, BCCO-CLS and TabArena; "We designate this majority category as the inlier class" and "subsample the remaining classes as anomalies at a given anomaly ratio randomly drawn from the range [0.05, 0.2]" — [MacrOData](https://arxiv.org/html/2602.09329)
- Curation filter: a supervised Random Forest must reach at least 60% ROC-AUC; 2,907 candidates inspected manually — [MacrOData](https://arxiv.org/html/2602.09329)
- Split: "50% of inliers to Train, and rest 50% inliers plus all outliers to Test", inlier-only training; supports one-class (inductive) and unsupervised (transductive) use — [MacrOData](https://arxiv.org/html/2602.09329)
- The only OOD remark: one-vs-rest "remains a vital proxy for e.g., capturing concept shift and OOD detection" — [MacrOData](https://arxiv.org/html/2602.09329)
- Methods in MacrOData: OCSVM, KNN, LOF, CBLOF, IForest, EGMM, DTE-NP; GOAD, ICL, DTE-C, NPT-AD; foundation models TabPFN-OD, FoMo-0D, OutFormer. "tabular foundation models significantly outperform all classical and deep OD methods, except EGMM" — [MacrOData](https://arxiv.org/html/2602.09329)
- ReTabAD (Yoon et al., arXiv October 2025) restores semantic metadata (feature descriptions, units, domain context) to tabular AD datasets and evaluates classical, deep and LLM-based detectors — [ReTabAD, arXiv 2510.02060](https://arxiv.org/abs/2510.02060v1) (search-snippet level; page not opened)

### Inferences
- The field's own successor benchmark (MacrOData) treats "one class versus the rest" as a legitimate anomaly construction and as a stand-in for OOD. A reviewer from the outlier-detection community may therefore see our held-out-class task as an instance of what OvRBench already covers, and ask why we do not report there. The answer is the difference in supervision and structure (Q4), not a difference in how the OOD rows are produced.
- No suite found carries group or time annotations. This is a statement about the sources I read, not a proof of absence.

### Gaps
- Whether MacrOData's public release keeps original column names / entity columns that would allow regrouping was not checked.
- ReTabAD dataset count and venue not verified.

## Q3. Recent tabular papers with foundation or deep models that use ADBench/ODDS, and their protocol

### Takeaway
Every tabular foundation-model detection paper I found (FoMo-0D, OutFormer, TabPFN-OD, uLEAD-TabPFN) and the deep tabular AD line (DTE, MCM, DRL, ICL, GOAD) evaluates on ADBench or its descendants under a label-free one-class or unsupervised protocol; none uses ID class labels, and none is an OOD-detection-with-classifier paper.

### Cited Findings
- FoMo-0D (ICML 2025 listing): a PFN pretrained on synthetic data for zero-shot outlier detection; evaluated on ADBench's 57 datasets against 26 baselines; "highly competitive", no statistically significant difference from the second-best method — [FoMo-0D, arXiv 2409.05672](https://arxiv.org/html/2409.05672v4); [ICML 2025 page](https://icml.cc/virtual/2025/47523)
- FoMo-0D protocol: inductive one-class, "clean inlier-only training data", train and test disjoint, 5 random splits; metrics AUROC, AUPR, F1; baselines include LOF, CBLOF, HBOS, kNN, OCSVM, IForest, DTE variants, DDPM, SLAD, ICL; TabPFN is not a baseline — [FoMo-0D](https://arxiv.org/html/2409.05672v4)
- OutFormer ("From Zero to Hero", ICML 2026 poster) evaluates on ADBench ("the de facto OD benchmark with 57 datasets"), OddBench, OvRBench and SynBench, inductive setting with inlier-only training. Baselines: FoMo-0D, TabPFN-OD, kNN, LOF, IForest, DeepSVDD, DDPM, GOAD, ICL, DTE-NP, DTE-C — [OutFormer, arXiv 2602.03018](https://arxiv.org/html/2602.03018); [ICML 2026 poster](https://icml.cc/virtual/2026/poster/60786)
- TabPFN-OD in that paper is TabPFN repurposed by treating "each feature as a prediction target and averaging prediction errors across features to derive an outlier score" — [OutFormer](https://arxiv.org/html/2602.03018)
- Prior Labs' own unsupervised extension scores a row by a chain-rule decomposition of the joint feature density, each conditional predicted by TabPFN, averaged over feature permutations — [Prior Labs docs, anomaly detection](https://docs.priorlabs.ai/capabilities/anomaly-detection) (search-snippet level)
- uLEAD-TabPFN (arXiv 2604.20255), a dependency-based detector built on TabPFN, reports on the 57 ADBench datasets — [summary page](https://www.emergentmind.com/papers/2604.20255) (aggregator, snippet only; treat as unverified)
- DTE, "On Diffusion Modeling for Anomaly Detection" (ICLR 2024), is evaluated on ADBench — [arXiv 2305.18593](https://arxiv.org/html/2305.18593v3) (snippet level)
- MCM (ICLR 2024) is framed as one-class tabular AD — [ICLR 2024 proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/13ec20547d2b1ff3a3a7a7c68a28e742-Abstract-Conference.html) (snippet level)
- DRL (ICLR 2025): 40 tabular datasets, 16 competing tabular AD algorithms — [ICLR 2025 proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/3da45dddfc85d9c6e962ce95cff0d127-Abstract-Conference.html) (snippet level)
- AnoLLM (ICLR 2025): tabular AD as LLM density estimation on normal rows — [ML Anthology](https://mlanthology.org/iclr/2025/tsai2025iclr-anollm) (snippet level)

### Inferences
- In the anomaly-detection line, ADBench is the default and a paper proposing a new unsupervised detector without it would be criticised. That norm attaches to the task (label-free AD), not to the modality (tables).
- Two baselines in that literature are directly relevant to an in-context-model paper and are absent from our draft: TabPFN-OD / unsupervised TabPFN (same backbone, label-free score) and FoMo-0D / OutFormer (PFNs trained for detection). Both can be run on our nine tables without changing our protocol, since they need only ID rows.

### Gaps
- I did not find any paper that evaluates TabICL or TabDPT for outlier or OOD detection; this may exist and I did not search it specifically.
- Public OpenReview reviews of FoMo-0D, OutFormer, DTE, MCM, DRL were not read, so I have no direct evidence of what reviewers asked those papers for.
- Exact dataset subsets used by MCM and DTE not verified from the papers.

## Q4. Conceptual difference between unsupervised anomaly detection and OOD detection with a labelled multi-class training set

### Takeaway
The standard survey separates them by supervision and by procedure: AD treats ID data as one undifferentiated class and outlier detection is transductive with contamination, whereas OOD detection and open-set recognition presuppose a multi-class ID classifier whose accuracy must be preserved, and their benchmarks are built by splitting a classification dataset by class. Our protocol is the second kind.

### Cited Findings
- Yang, Zhou, Li, Liu, "Generalized Out-of-Distribution Detection: A Survey" unifies five problems (AD, novelty detection, open set recognition, OOD detection, outlier detection) — [arXiv 2110.11334](https://arxiv.org/html/2110.11334v2)
- "AD treats ID samples as a whole, which means that regardless of the number of classes (or statistical modalities) in ID data, AD does not require the differentiation in the ID samples." — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- Semantic AD "detects test samples with label shift, assuming that normalities come from the same semantic distribution (category), i.e., normalities should belong to only one class." — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- Novelty detection comes as one-class or multi-class, according to the number of classes in the training set — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- "Open set recognition requires the multi-class classifier to simultaneously: 1) accurately classify test samples from 'known known classes', and 2) detect test samples from 'unknown unknown classes'." OSR benchmarks "usually split one multi-class classification dataset into ID and OOD parts according to classes." — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- "OOD detection should NOT harm the ID classification capability." — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- Outlier detection "does not follow the train-test procedure but has access to all observations, approaches to this problem are usually transductive rather than inductive." — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- ADBench's "unsupervised" setting has no labels at all, and its datasets are restricted to anomaly ratios below 40% (contamination is part of the problem) — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- In tabular medical data, an OOD benchmark that does use trained predictors found that post-hoc (classifier-based) detectors are weak alone but "improve substantially when coupled with distance-based mechanisms", and that far-OOD looks solved while near-OOD remains open — [Azizmalayeri et al., arXiv 2309.16220](https://arxiv.org/abs/2309.16220v1)

### Inferences
- In Yang et al.'s vocabulary our task (split a multi-class table by class, keep a classifier on the ID classes, detect the held-out class) is open-set recognition / multi-class novelty detection under semantic shift. ADBench's task is one-class or contaminated AD. The two differ in three operational ways: (a) class labels of ID rows are available and used (MSP and our familiarity score need them); (b) the "normal" set is multi-modal by construction; (c) anomalies in ADBench are a rare minority mixed into training in the unsupervised setting, whereas our context is clean ID rows.
- Our paper adds a fourth axis that neither literature has: the null distribution is "ID rows of unseen groups", so the claim under test is about calibration and ranking against a group-out reference. A suite with random splits cannot test that claim regardless of how many datasets it has.
- The draft currently does not state this distinction. RELATED WORK cites I-Div, density-ratio estimation, novelty detection, open-set label shift and full-spectrum OOD, but no tabular AD benchmark and no survey that separates AD from OOD. One sentence with Yang et al. and ADBench would pre-empt the question.

### Gaps
- Salehi et al., "A Unified Survey on Anomaly, Novelty, Open-Set, and Out-of-Distribution Detection" was not opened; no quote available.
- I found no tabular-specific published statement that draws the AD versus OOD line; the closest is MacrOData calling one-vs-rest a "proxy" for OOD detection (Q2).

## Q5. Do published tabular OOD-detection papers report on ADBench in addition to class-holdout protocols?

### Takeaway
In the examples I could verify, tabular OOD-detection papers that train a classifier use class-holdout or cohort-shift protocols on their own choice of classification tables and do not report ADBench/ODDS; conversely ADBench-based papers do not run classifier-based OOD scores. The two literatures are disjoint in practice, though the evidence base here is small (three papers, none at NeurIPS/ICML/ICLR).

### Cited Findings
- Deep-MCDD (Lee, Yu, Yu; KDD 2020): tabular sets GasSensor, Shuttle, DriveDiagnosis and MNIST; "one of classes as the OOD class and the rest of them as the ID classes. We exclude the samples of the OOD class from the training set"; baselines softmax (MSP), Mahalanobis, Deep-SVDD, ALAD, ProtoNet, Deep-NCM; metrics include ID accuracy, TNR at 85% TPR, AUROC, AUPR. No ODDS/ADBench suite — [Deep-MCDD, ar5iv 2104.00941](https://ar5iv.labs.arxiv.org/html/2104.00941)
- "Unmasking the Chameleons" (medical tabular OOD benchmark): eICU and MIMIC-IV, near and far OOD, 10 density-based methods plus 17 post-hoc detectors on MLP, ResNet and Transformer predictors; ADBench/ODDS are not mentioned in the abstract — [arXiv 2309.16220](https://arxiv.org/abs/2309.16220v1); journal version in [Int. J. Medical Informatics](https://www.sciencedirect.com/science/article/pii/S1386505624004258)
- Zhao, Cao, Yu, "Out-of-Distribution Detection by Regaining Lost Clues" (Artificial Intelligence 339, 2025): proposes a transformer chain and claims it "significantly surpasses state-of-the-art methods for OOD detection in tabular data" — [lab news page](https://datasciences.org/news/aij-out-of-distribution-detection-by-regaining-lost-clues/). Our draft states that this paper uses eight tables, the smallest class as OOD and five repetitions (draft `main.tex`, appendix DATASETS; not independently verified by me).
- "Out-of-Distribution Aware Classification for Tabular Data" (CIKM 2024) addresses joint ID classification and OOD detection for tables where no unrelated dataset can serve as OOD training data — [ACM DL](https://dl.acm.org/doi/10.1145/3627673.3679755) (snippet only; page returned 403)
- Shuttle appears in both worlds: as an ID/OOD class-holdout table in Deep-MCDD and as a one-class AD set in ADBench (49,097 rows, 7.15% anomalies) — [Deep-MCDD](https://ar5iv.labs.arxiv.org/html/2104.00941); [ADBench README](https://github.com/Minqi824/ADBench)

### Inferences
- Precedent supports class-holdout without ADBench for classifier-based tabular OOD papers. It is thin precedent: the verified examples are KDD 2020, a medical-informatics journal and AIJ. I found no NeurIPS/ICML/ICLR/AISTATS paper on tabular class-holdout OOD detection at all, in either direction.
- Deep-MCDD does include Deep-SVDD and ALAD as "non-classifier-based detectors" inside its class-holdout protocol. That is the more common form of cross-over: bring AD methods into the OOD protocol as baselines, rather than take the OOD method to the AD suite.

### Gaps
- No verified example of a top-venue tabular OOD paper that reports both protocols. Absence in my search is weak evidence.
- Dataset list and baselines of Zhao et al. 2025 (TC) and of the CIKM 2024 paper could not be read from primary sources.
- OpenReview reviews for tabular OOD submissions were not searched; reviewer requests for ADBench in such submissions are neither confirmed nor ruled out.

## Q6. Baselines common in these suites that our paper lacks

### Takeaway
Our five baselines (MSP, kNN, Emb-kNN, Mahalanobis, IForest) cover one confidence score, the distance family and one classical AD method. Missing relative to the two literatures are: logit-based post-hoc scores (energy, max-logit, ODIN/ViM-style), classical AD staples (LOF, OCSVM, ECOD/COPOD), a deep AD method (Deep SVDD or DTE), and, most pointedly for a PFN paper, the PFN-native detectors (TabPFN-OD / unsupervised TabPFN, FoMo-0D, OutFormer).

### Cited Findings
- Draft baselines: "MSP, kNN, kNN in the PFN embedding (Emb-kNN), the Mahalanobis distance (Maha) and the isolation forest (IForest)" — draft `main.tex`, EXPERIMENTS (local file)
- ADBench's unsupervised set: PCA, OCSVM, LOF, CBLOF, COF, HBOS, KNN, SOD, IForest, ECOD, COPOD, LODA, DAGMM, DeepSVDD — [ADBench README](https://github.com/Minqi824/ADBench)
- FoMo-0D's 26 baselines include LOF, CBLOF, HBOS, kNN, OCSVM, IForest, DTE variants, DDPM, SLAD, ICL — [FoMo-0D](https://arxiv.org/html/2409.05672v4)
- OutFormer's baselines: FoMo-0D, TabPFN-OD, kNN, LOF, IForest, DeepSVDD, DDPM, GOAD, ICL, DTE-NP, DTE-C — [OutFormer](https://arxiv.org/html/2602.03018)
- MacrOData's method list: OCSVM, KNN, LOF, CBLOF, IForest, EGMM, DTE-NP, GOAD, ICL, DTE-C, NPT-AD, TabPFN-OD, FoMo-0D, OutFormer; foundation models beat all classical and deep methods except EGMM — [MacrOData](https://arxiv.org/html/2602.09329)
- The medical tabular OOD benchmark uses 17 post-hoc detectors on trained predictors in addition to 10 density-based methods — [arXiv 2309.16220](https://arxiv.org/abs/2309.16220v1)
- Deep-MCDD's tabular baselines include Deep-SVDD and ALAD next to MSP and Mahalanobis — [Deep-MCDD](https://ar5iv.labs.arxiv.org/html/2104.00941)

### Inferences
- Ranked by how likely a reviewer is to ask, in my assessment:
  1. TabPFN-OD / unsupervised TabPFN and FoMo-0D or OutFormer. A paper about OOD detection with in-context tabular models that omits the existing in-context detectors has an obvious hole, and MacrOData reports these as the strongest methods on AD suites.
  2. Energy / max-logit. They are the default companions of MSP in post-hoc OOD work and cost nothing given the PFN's logits. The draft's ten input scores to the adapter may already include some of them; if so, reporting them as standalone rows closes the gap.
  3. LOF and OCSVM (and ECOD/COPOD as parameter-free references). Cheap, in PyOD, and present in every AD comparison above.
  4. One deep one-class method (Deep SVDD or DTE-NP/DTE-C). DTE-NP is non-parametric and cheap.
  5. ODIN/ViM/ReAct-style methods need gradients or penultimate features of a trained network; for a frozen in-context model they are awkward, and saying so is a sufficient answer.
- kNN and IForest, which we have, are consistently among the strongest classical methods in these suites, so the existing baseline set is not weak; it is narrow.

### Gaps
- I did not verify which of the ten adapter input scores in the draft already correspond to energy or class-conditional distances; the EXPERIMENTS text does not list them.
- Licence and input-size limits of FoMo-0D / OutFormer checkpoints (FoMo-0D degrades beyond its pretraining dimension, per its paper) were not checked against our tables (asp has 136 features, mice 76).

## Q7. Assessment: would reviewers expect these suites, and the arguments for and against

### Takeaway
My assessment: reporting ADBench is not a requirement for this paper and would not test its claim, but the paper should say why in two or three sentences and should import the AD literature's baselines into its own protocol; the residual risk is a reviewer from the outlier-detection community who reads "nine tables" against ADBench's 57 or MacrOData's 2,446.

### Cited Findings
- ADBench is called "the de facto OD benchmark" by a 2026 ICML paper — [OutFormer](https://arxiv.org/html/2602.03018)
- ADBench uses random stratified splits and excludes time-series and graph structure — [ADBench, ar5iv](https://ar5iv.labs.arxiv.org/html/2206.09426)
- The AD community itself now regards ADBench as too small, partly duplicated and saturated — [MacrOData](https://arxiv.org/html/2602.09329)
- OOD detection presupposes an ID classifier; AD "does not require the differentiation in the ID samples" — [Yang et al.](https://arxiv.org/html/2110.11334v2)
- Classifier-based tabular OOD papers verified here use class-holdout on a handful of tables (Deep-MCDD: four) without AD suites — [Deep-MCDD](https://ar5iv.labs.arxiv.org/html/2104.00941)
- One-vs-rest construction is described as a "proxy" for OOD detection by the newest AD benchmark — [MacrOData](https://arxiv.org/html/2602.09329)

### Inferences
Arguments against reporting on ADBench/ODDS (all my assessment):
- Wrong null. The paper's claim concerns ID rows from unseen groups versus OOD rows. ADBench has no groups and random splits, so the "familiar" and "group-out" references coincide and the method reduces to something the theory does not distinguish from its baselines. A result there would be neither support nor refutation.
- Wrong supervision. Most ADBench sets are one normal class plus anomalies. With one ID class there is no classifier, MSP is undefined, and the pseudo-task construction (holding out modes of known classes) has little to work with. Running it would require redesigning the method for a setting the paper does not claim.
- Different contamination regime. ADBench's unsupervised setting mixes anomalies into training; our context is clean ID rows.
- Quality. Near-duplicates, saturated and near-chance sets, old UCI tables; the draft's argument that BeyondArena is a curated pool not selected by detector performance is stronger than "we also ran ADBench".
- Scope discipline. The draft already uses every BeyondArena multiclass task with a non-IID split that fits TabPFN v2; adding an unrelated suite dilutes a paper whose experiments are meant to serve a theoretical argument.

Arguments for (again my assessment):
- Recognition. ADBench is what reviewers with an AD background know; "nine tables, eight in the final test" invites the comparison. A short negative-control experiment is cheap insurance.
- A useful control exists. On tables without group structure the theory predicts no familiarity gap, so GOR should be roughly on par with tuned kNN, not better. Showing that on a few multi-class IID tables (the 17 IID multiclass BeyondArena tasks are a more defensible source than ADBench, since they keep class labels) would be a prediction check rather than a benchmark chase.
- The construction overlaps. OvRBench and ADBench's own CV/NLP sets are built by designating classes as anomalies; a reviewer can reasonably say the OOD rows are produced the same way. The paper needs to answer with the supervision and reference-distribution argument, not with "different field".
- Two tables overlap (cardiotocography, covertype), so a reviewer may ask how the numbers relate to known ADBench results on `cardio` and `cover`. They are not comparable (binary, re-sampled, no patient/area split), and one sentence in the DATASETS appendix can say so.

Recommended minimum, in order of value per effort:
1. Add one or two sentences to RELATED WORK or the DATASETS appendix: ADBench/ODDS/MacrOData target label-free anomaly detection with random splits and no entity or time annotation; our task needs ID class labels and a group-out reference; two of our tables have ADBench counterparts that are different binary tasks. Cite Yang et al. for the taxonomy.
2. Bring AD baselines into our protocol: TabPFN-OD or unsupervised TabPFN, FoMo-0D or OutFormer if the checkpoints fit our feature counts, energy, LOF, and one of OCSVM/ECOD/DTE-NP. This addresses the baseline question on our own tables, which is where the claim lives.
3. Optional appendix control on IID multi-class tables with random splits, framed as a test of the prediction that the gain vanishes without group structure. I would not present ADBench numbers in the main text.
4. Mention in LIMITATIONS that one-class anomaly detection without ID labels is outside the paper's scope.

Risk if nothing is done: moderate. AISTATS reviewers are more often theory-oriented than benchmark-oriented, and the verified tabular OOD precedents do not use AD suites; but the draft currently contains no sentence that positions itself against the AD literature and no AD-native or PFN-native detector among its baselines, and the second omission is the one I would expect to be raised first.

### Gaps
- No direct evidence from reviews. I did not read any OpenReview thread in which a reviewer asked a tabular OOD paper for ADBench results, so the expectation above is inferred from publication practice, not observed.
- I did not find a top-venue (NeurIPS/ICML/ICLR/AISTATS) tabular class-holdout OOD paper to serve as a direct precedent for either choice.
- Whether GOR can be run at all on single-ID-class datasets was not examined in the code; the claim that it has "little to work with" there follows from the method description in the draft only.
