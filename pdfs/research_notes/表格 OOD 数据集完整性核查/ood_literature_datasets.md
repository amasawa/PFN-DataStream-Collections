# Datasets and benchmarks used in tabular OOD detection / open-set / novel-class literature (state: 1 Oct 2026)

Method note: dataset names and protocols below were read from the full text of the primary PDFs (arXiv / NeurIPS
proceedings / the local copy of the AIJ paper in `refs/zhilinpapers/`), not from abstracts, unless a bullet says
"snippet only". "Semantic shift" = OOD rows come from a class absent at training; "covariate shift" = same label
space, different input law; "AD" = unsupervised / one-class anomaly detection.

## Q1. Which datasets do I-Div (Zhao et al., NeurIPS 2024) and its follow-up zhao2025tc use? Any tabular experiments?

### Takeaway
I-Div (NeurIPS 2024) has NO tabular experiment: every dataset is an image dataset. The tabular protocol cited in
our draft comes only from Zhao, Cao & Yu, "Out-of-distribution detection by regaining lost clues" (Artificial
Intelligence 339, 2025, 104275; the TC paper): eight tables (Stellar, Skyserver, Arrhythmia, Gisette, SHABD, Gene,
Wine, Speech), smallest class = OOD, ID split 8:2, five random trials.

### Cited Findings
- I-Div Section 4.1 "Experiments on different classes": "We utilize two datasets, CIFAR10 and SVHN ... we select samples from one class to serve as the test dataset, with the samples from the remaining nine classes forming the training dataset." This is a class-holdout (semantic-shift) protocol, on images. — [NeurIPS 2024 paper PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/469eb28a0a67dba79f79cbb03f84cd90-Paper-Conference.pdf)
- I-Div Section 4.2 "different datasets": CIFAR10 as training set against "Randomly Generated Images (RGI), SVHN, DTD, Flowers102, OxfordIIITPet, SEMEION, Caltech256, CIFAR100, CIFAR10.1, and STL10"; ImageNet as training set against "Open Images Dataset v4 (OIDv4), Caltech256, Flowers102, and DTD" (ResNet50, ViT-B/16); domain-adaptation sets "PACS and Office-Home". The paper also has sections on corrupted and adversarial data. The word "tabular" does not occur in the experimental sections (full-text search of the PDF). — [NeurIPS 2024 paper PDF](https://proceedings.neurips.cc/paper_files/paper/2024/file/469eb28a0a67dba79f79cbb03f84cd90-Paper-Conference.pdf)
- TC paper, Section 6.2 "OOD detection performance on tabular data": "We chose eight datasets, five of which (Stellar, Skyserver, Gisette, SHABD, Speech) are sourced from Kaggle, while the remaining three (Arrhythmia, Gene, Wine) are from the UCI machine learning repository." — [Artificial Intelligence 339:104275, DOI 10.1016/j.artint.2024.104275](https://doi.org/10.1016/j.artint.2024.104275) (ScienceDirect returns 403 to automated fetch; text read from the local PDF `refs/zhilinpapers/1-s2.0-S000437022400211X-main.pdf`)
- TC protocol, verbatim: "we designate the samples from the smallest class as OOD and the samples from the other classes as ID. Subsequently, we partition the ID samples into training and test sets with an 8:2 ratio. In cases where the number of labels is two, an extra class is introduced during training to prevent all test samples from receiving 100% confidence." Results "averaged over five random trials". — [same paper, DOI](https://doi.org/10.1016/j.artint.2024.104275)
- TC Table 1 (instances / features / labels): Stellar 100000 / 16 / 3; Skyserver 100000 / 17 / 3; Arrhythmia 87553 / 187 / 5; Gisette 6000 / 5000 / 2; SHABD 243456 / 1024 / 384; Gene 801 / 20531 / 5; Wine 1143 / 11 / 6; Speech 3960 / 12 / 6. — [same paper, DOI](https://doi.org/10.1016/j.artint.2024.104275)
- TC baselines on tabular data: MSP, MLS, RA, DSVDD, DG, OE, MOS, DE; metrics AUROC and detection error. TC also has an image check: CIFAR10 as ID, "SVHN, CIFAR100, LSUN, and TinyImageNet as the OOD datasets". Code: github.com/Lawliet-zzl/TC. — [same paper, DOI](https://doi.org/10.1016/j.artint.2024.104275)
- The paper was also reprinted as an abstract in the IJCAI 2025 journal track. — [IJCAI 2025 proceedings](https://www.ijcai.org/proceedings/2025/1235)

### Inferences
- The draft's statement (main.tex l.829) "eight tables, the smallest with 801 rows, the smallest class as OOD and five random repetitions" is consistent with the primary source (Gene has 801 instances).
- TC's eight tables are all IID tables with a random 8:2 split; none has a group or time structure in the protocol. So the closest in-house precedent gives a class-holdout precedent but not a grouped/temporal one.
- TC's "Stellar" (100000 rows, 3 labels, Kaggle) is very probably the Kaggle "Stellar Classification Dataset - SDSS17", i.e. the same source as our `sdss_17` (BeyondArena lists 78,053 rows after its own curation). This is an inference from name, source, row count and class count; the TC paper gives no URL per dataset.
- A reviewer who knows I-Div cannot ask us to "reuse I-Div's tabular benchmark": there is none.

### Gaps
- TC gives no per-dataset URL or citation, so the exact Kaggle identity of Skyserver, SHABD and Speech, and which UCI "Wine" (1143 rows, 6 labels) and "Arrhythmia" (87553 rows, 187 features, 5 labels; this matches the size of the MIT-BIH heartbeat table, not the 452-row UCI Arrhythmia) are meant, could not be verified. The GitHub repository was not inspected.
- I did not check Zhao et al.'s other papers (R-Div NeurIPS 2023, WNB, CA) for tabular experiments.

## Q2. Which datasets do papers on OOD detection / uncertainty with TabPFN, TabICL, TabDPT and other tabular foundation models use?

### Takeaway
I found exactly one prior paper that evaluates unseen-class detection with a tabular foundation model: Cheng et al.,
"Realistic Evaluation of TabPFN v2 in Open Environments" (arXiv 2505.16226), which uses a leave-one-class-out
protocol on four small IID tables (EyeMovement, CMC, Wine-Red, Wine-White) with MSP as the score. All other
foundation-model work is either OOD generalisation under covariate/temporal shift (TableShift, WhyShift, Wild-Time
style data) or unsupervised outlier detection on ADBench and its successors.

### Cited Findings
- Cheng, Jia, Zhou, Li, Guo (Nanjing University), arXiv 2505.16226. "Emerging New Classes" task: "Based on multi-class datasets (Appendix E.1), we implement a leave-one-class-out protocol: for k-class problems, we perform k runs, each excluding one class"; score = "the maximum predicted probability"; metrics ROC-AUC and AUPR; "An equal number of samples from the remaining classes are randomly sampled as known". Datasets (Table 1): EyeMovement (Kaggle eye-movements, 3 classes, 27 features), CMC (UCI Contraceptive Method Choice, 1,473 rows, 3 classes), Wine-Red and Wine-White (UCI Wine Quality). Compared models: RandomForest, XGBoost, CatBoost, MLP, RealMLP, ModernNCA, TabPFN v2. Claim: "TabPFN v2 has the potential to detect new classes". — [arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)
- Same paper, distribution-shift task (generalisation, not detection): "nine fully numerical datasets drawn from the WhyShift and TableShift benchmarks"; feature-shift task uses TabFSBench (twelve datasets). — [arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)
- Loza et al., "Empirical Evaluation of Out-Of-Distribution Performance of Tabular Foundation Models", arXiv 2607.26000 (28 Jul 2026): nine models (TabPFNv2, v2.5, v2.6, v3, TabICL, TabICLv2, Mitra, LimiX, TabFM) on three datasets, HELOC (label shift), Childhood Lead (NHANES; socioeconomic shift) and Voting (ANES; geographic shift); metric is ROC-AUC and the ID-OOD "shift gap". This is OOD generalisation, not detection; the three tasks are TableShift tasks. — [arXiv 2607.26000](https://arxiv.org/html/2607.26000v1)
- Purucker et al., "Beyond IID: How General Are Tabular Foundation Models, Really?" (arXiv 2606.30410, 29 Jun 2026): 142 curated datasets, 11 models, task types IID / temporal / grouped; curation funnel "1128 datasets from 21 benchmarks and public data repositories ... 142 remain"; additional sources "7 non-IID or multimodal tabular benchmarks: TabReD, TableShift, the string vectorizing benchmark, the CARTE benchmark, TextTabBench, the TabSTAR benchmark, and the AutoGluon Multimodal benchmark". It measures predictive performance only; a full-text search finds no "open-set", "unseen class" or "novel class", and "out-of-distribution" occurs once. — [arXiv 2606.30410](https://arxiv.org/pdf/2606.30410)
- Helli, Schnurr, Hollmann, Müller, Hutter, "Drift-Resilient TabPFN" (NeurIPS 2024, arXiv 2411.10634): temporal-shift generalisation; "evaluations across 18 synthetic and real-world datasets", baselines include "methods featured in the Wild-Time benchmark". The appendix describes 28 datasets (evaluation plus validation), e.g. synthetic Rotated Two Moons, Intersecting Blobs, Binary Label Shift, Rotating Hyperplane, RandomRBF Drift, Rotating Segments, Sliding Circle, Shifting Two Spirals; real Free Light Chain Mortality, Electricity, Absenteeism at Work, Heart Disease, Parking Birmingham, Ames Housing Prices, Folktables US Census, Chess, Diabetes 130-US Hospitals, Airlines Delay, Pima Indians Diabetes, Room Occupancy Detection. Not OOD detection. — [arXiv 2411.10634](https://arxiv.org/pdf/2411.10634); [NeurIPS 2024 poster page](https://neurips.cc/virtual/2024/poster/93581)
- TabPFN-3 technical report (arXiv 2605.13986): the "Out-of-distribution prior" is described as "We add out-of-distribution prediction tasks, allowing models trained on our prior data to remain performant under distribution shifts, as well as moving from pure interpolation to extrapolation", with a figure "demonstrating the extrapolation capabilities of TabPFN-3 (using our out-of-distribution compatible preprocessing)". So the TabPFN-3 "ood" material concerns prediction under shift / extrapolation, not detection of OOD rows. — [arXiv 2605.13986](https://arxiv.org/pdf/2605.13986)
- TabPFN unsupervised extension (Prior Labs docs): outlier score = joint density by the chain rule over features, P(X) = prod_i P(X_i | X_<i), averaged over feature permutations; this is unsupervised anomaly detection, with no benchmark named on the docs page. — [Prior Labs docs](https://docs.priorlabs.ai/capabilities/anomaly-detection)
- FoMo-0D (Shen et al., TMLR 09/2025): zero-shot tabular outlier-detection PFN, evaluated on "57 real-world datasets from ADBench (Han et al., 2022)" against 26 baselines. AD protocol. — [arXiv 2409.05672](https://arxiv.org/pdf/2409.05672)
- OutFormer (Ding, Wen, Klüttermann, Akoglu, arXiv 2602.03018): "ADBench (Han et al., 2022) is the de facto OD benchmark with 57 datasets. We introduce two new OD benchmarks, OddBench and OvRBench, with 690 and 756 datasets respectively"; "OvRBench re-purposes classification benchmarks (TabArena, TabRepo, TabZilla, etc.) by selecting one class as inliers and subsampling the rest as outliers"; plus SynBench with 800 synthetic datasets. — [arXiv 2602.03018](https://arxiv.org/pdf/2602.03018)
- macrOData (Ding et al., arXiv 2602.09329, 10 Feb 2026): OddBench (790 datasets, semantic anomalies filtered from TabLib), OvRBench (856 datasets, one-vs-rest: "the majority category as the inlier class", sources OpenML-CC18, TabZilla, TabRepo, TabArena, TabLib), SynBench (800 synthetic); 2,446 datasets in total; unsupervised and one-class detection with "inlier-only training data". Counts differ from the OutFormer paper (690 / 756), which I report as a conflict between the two sources. — [arXiv 2602.09329](https://arxiv.org/html/2602.09329v1); differing counts in [arXiv 2602.03018](https://arxiv.org/pdf/2602.03018)
- uLEAD-TabPFN (arXiv 2604.20255): TabPFN-based anomaly detection, "57 tabular datasets from ADBench" (snippet only, not read in full). — [arXiv 2604.20255](https://arxiv.org/pdf/2604.20255)

### Inferences
- The only direct precedent for "TabPFN + held-out class" (arXiv 2505.16226) uses four small IID tables, all-classes leave-one-out, and MSP only. Our nine grouped/temporal tables with one held-out class is a larger and structurally harder pool than this precedent. A reviewer could still ask for (a) its four tables, or (b) leave-one-class-out over all classes instead of one fixed OOD class.
- For foundation-model outlier detection the de facto benchmark is ADBench (57 datasets). ADBench is an anomaly-detection benchmark (one "normal" population, anomalies as the positive class, no K-class classifier), so it is not a benchmark for our multi-class unseen-class setting; but it is the name a reviewer from the AD community will mention. OvRBench is the nearest large-scale object to class-holdout, but with one inlier class only.
- No paper found uses TabICL or TabDPT for OOD / unseen-class detection.

### Gaps
- I found no paper titled "TabPFN unleashed" in searches and did not verify its content; no dataset claim is made about it here.
- TabICL / TabICLv2 / TabDPT papers were not read for OOD-detection experiments; searches returned none.
- The Prior Labs extension has no paper-level evaluation that I could locate for its outlier score.
- The exact 18 evaluation datasets (vs validation datasets) of Drift-Resilient TabPFN were not separated.

## Q3. Which datasets do dedicated tabular OOD-detection benchmark / method papers use, and are they semantic-shift or covariate-shift?

### Takeaway
The two "benchmark" papers for tabular OOD detection are both medical ICU studies (MIMIC-III/IV, eICU) and use
covariate / subgroup shift, not held-out classes. Papers that do use held-out classes on tables each pick their own
small set of UCI/Kaggle tables (4 to 8), with almost no overlap between papers; the recurring names are Covertype,
Sensorless Drive Diagnosis, Gas Sensor, Shuttle, Letter, Pendigits, HAR, US Census 1990 and flattened MNIST.

### Cited Findings
Covariate / subgroup-shift protocols (medical)
- Ulmer, Meijerink, Cinà, "Trust Issues: Uncertainty Estimation Does Not Enable Reliable OOD Detection On Medical Tabular Data" (ML4H 2020, PMLR): MIMIC-III (61532 ICU stays) and eICU. OOD groups: "clinically relevant OOD groups" by age (newborns, MIMIC-III only), ethnicity (white, black), gender, admission type (elective vs emergency); eICU stays as OOD for MIMIC-III models and vice versa; artificial perturbation by scaling one feature. — [arXiv 2011.03274](https://arxiv.org/pdf/2011.03274)
- Azizmalayeri, Abu-Hanna, Cinà, "Unmasking the Chameleons: A Benchmark for Out-of-Distribution Detection in Medical Tabular Data" (arXiv 2309.16220; journal version on ScienceDirect): "We use eICU and MIMIC-IV"; far-OOD: "each of these datasets is considered as far-OOD set for the other one"; near-OOD: split by time-independent variables, "age (older than 70 as ID), gender (females as ID), and ethnicity (Caucasian or African American as ID) in eICU, and Age (older than 70 as ID), gender (females as ID), admission type (surgical in the same day of admission as ID), and first care unit (CVICU as ID) in MIMIC-IV"; also feature-scaling OOD. Finding: "solved for far-OODs, but remains open for near-OODs". Methods: 10 density-based and 17 post-hoc detectors on MLP, ResNet, Transformer. — [arXiv 2309.16220](https://arxiv.org/pdf/2309.16220); [journal version](https://www.sciencedirect.com/science/article/pii/S1386505624004258)
- A search snippet for the same benchmark says it "leverages 4 different and large public medical datasets, including eICU and MIMIC-IV"; the arXiv text I read names only eICU and MIMIC-IV. Conflict between abstract versions, unresolved. — [arXiv 2309.16220v1 abstract](https://arxiv.org/abs/2309.16220v1)
- Gardner, Popovic, Schmidt, TableShift (NeurIPS 2023 D&B): benchmark of domain shift for prediction; our draft already states its 15 tasks are binary and not a detection benchmark. — [arXiv 2607.26000 describing TableShift use](https://arxiv.org/html/2607.26000v1)

Semantic-shift (held-out class) protocols on tables
- Zhao, Cao, Yu, TC (Artificial Intelligence 2025): Stellar, Skyserver, Arrhythmia, Gisette, SHABD, Gene, Wine, Speech; smallest class = OOD (see Q1). — [DOI 10.1016/j.artint.2024.104275](https://doi.org/10.1016/j.artint.2024.104275)
- Lee, Yu, Yu, "Multi-Class Data Description for Out-of-distribution Detection" (Deep-MCDD; arXiv 2104.00941): "four multi-class tabular datasets with real-valued attributes: GasSensor, Shuttle, DriveDiagnosis, and MNIST ... downloaded from UCI"; sizes GasSensor 128 attr / 13,910 / 6 classes, Shuttle 9 / 58,000 / 7, DriveDiagnosis 48 / 58,509 / 11, MNIST 784 / 70,000 / 10. Protocol: "regarding one of classes as the OOD class and the rest of them as the ID classes. We exclude the samples of the OOD class from the training set ... The evaluations are repeated while alternately c[hanging the OOD class]" (leave-one-class-out over all classes). — [arXiv 2104.00941](https://arxiv.org/pdf/2104.00941)
- Chudasama et al. (Mastercard), DNN-GDITD (arXiv 2409.00980): Synthetic Financial (143,670 / 943 features / 3 classes), Gas Sensor, Drive Diagnosis, MNIST; a fixed class ("class 0") is the OOD class; adds minority-class down-sampling ratios. Follows the Deep-MCDD datasets. — [arXiv 2409.00980](https://arxiv.org/html/2409.00980v2)
- Bhumika, Vidhya, Krishnan, "A Probabilistic Circuit-Induced Pseudo-Metric for Out-of-Distribution Detection" (arXiv 2608.09117): "Adult, Covertype, Sensorless, Census-KDD, Connect-4 tabular datasets from the UCI Machine Learning Repository and ... binarized MNIST"; "class-wise OOD protocol. For each experiment, one class is treated as ID, while each remaining class is considered as a separate OOD." (density-model variant of class holdout). — [arXiv 2608.09117](https://arxiv.org/pdf/2608.09117)
- Cheng et al., TabPFN v2 open environments: EyeMovement, CMC, Wine-Red, Wine-White; leave-one-class-out (see Q2). — [arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)
- Ansari, Wang, Xiong, "Out-of-Distribution Aware Classification for Tabular Data" (CIKM 2024) exists and targets tabular OOD-aware classification; datasets not retrieved. — [ACM DL](https://dl.acm.org/doi/10.1145/3627673.3679755)

Novel class discovery (NCD) on tables: classes held out, but the task is clustering the unknown classes, not detection
- Troisemaine et al., TabularNCD (arXiv 2209.01217): "Six public tabular classification datasets were selected: Forest Cover Type, Letter Recognition, Human Activity Recognition, Satimage, Pen-Based Handwritten Digits Recognition and 1990 US Census Data, as well as MNIST". Known/unknown class splits: MNIST 5/5, Forest Cover type 4/3, Letter recognition 19/7, Human activity 3/3, Satimage 3/3, Pendigits 5/5, 1990 US Census 12/6. Metrics: clustering ACC, BACC, NMI, ARI. — [arXiv 2209.01217](https://arxiv.org/pdf/2209.01217)
- Troisemaine et al., "A Practical Approach to Novel Class Discovery in Tabular Data" (Data Mining and Knowledge Discovery, 2024; arXiv 2311.05440): "7 tabular classification datasets were selected: Human Activity Recognition, Letter Recognition, Pen-Based Handwritten Digits, 1990 US Census Data, Multiple Features, Handwritten Digits and CNAE-9". — [arXiv 2311.05440](https://arxiv.org/pdf/2311.05440); [HAL record](https://hal-lara.archives-ouvertes.fr/LAB-STICC_MATHNET/hal-04283853v2)

Open-set recognition on network-intrusion flow tables (snippet level only)
- Search results report that work on unknown-attack detection uses "Three datasets (NSL-KDD, UNSW-NB15, CICIDS-2017)" and that "In CIC-IDS-2017 experiments, DoS attack samples were held out as unknowns"; OSR modules "DOC++, DOC, OpenMax, and AutoSVM have been evaluated on the CIC-IDS2017 dataset". These are held-out attack class (semantic shift) protocols on flow-feature tables. Papers surfaced: — [Open Set Intrusion Recognition for Fine-Grained Attack Categorization, arXiv 1703.02244](https://arxiv.org/pdf/1703.02244); [An Adaptable Deep Learning-Based IDS to Zero-Day Attacks, arXiv 2108.09199](https://arxiv.org/pdf/2108.09199); [Open Set Classifier for IoT NIDS, arXiv 2309.07461](https://arxiv.org/pdf/2309.07461); [Evaluating Tabular Representation Learning for Network Intrusion Detection, arXiv 2605.02519](https://arxiv.org/pdf/2605.02519)

Other
- Ginanjar et al., "Representation Learning on Out of Distribution in Tabular Data" (arXiv 2502.10095): Adult, Helena, Jannis, Higgs Small, Aloi, Cover Type, California Housing, Year, Yahoo, Microsoft; OOD rows are obtained by thresholding OpenMax / temperature-scaling scores, and the task is prediction on those rows (OOD generalisation, non-standard protocol). — [arXiv 2502.10095](https://arxiv.org/html/2502.10095v2)

### Inferences
- Protocol map: (i) medical "benchmarks" = covariate/subgroup shift, binary outcomes, credentialed data; (ii) method papers with held-out classes = ad hoc UCI/Kaggle tables, random IID split; (iii) NCD = held-out classes, clustering metrics; (iv) AD benchmarks = ADBench and one-vs-rest constructions.
- No class-holdout paper found uses a grouped or temporal split. Combining class holdout with grouped/temporal deployment appears to be new in the surveyed literature; this is an argument for the paper, but it also means there is no inherited dataset pool for that exact setting.
- Dataset reuse across class-holdout papers is thin: Deep-MCDD and DNN-GDITD share Gas Sensor and Drive Diagnosis; the PC paper and Deep-MCDD share Sensorless Drive Diagnosis; Covertype appears in the PC paper, TabularNCD and Ginanjar et al., and is in our pool. Wine Quality appears in TC and in Cheng et al.

### Gaps
- Venue of Deep-MCDD (I believe KDD 2020) and of TabularNCD (I believe ICDM 2022) were not verified against a primary source in this session; the arXiv IDs are verified.
- The journal of the Azizmalayeri ScienceDirect version (pii S1386505624004258) was not opened; journal name not confirmed.
- CIKM 2024 (Ansari et al.) datasets not retrieved (ACM page not fetched).
- Network-intrusion OSR evidence is from search snippets, not full texts; the list is illustrative, not exhaustive.
- Not covered: OOD detection inside tabular generative / LLM-based detectors (e.g. AnoLLM), the Shifts weather table, Wild-Tab; these are AD or generalisation work as far as I know, but I did not verify.

## Q4. Is there an established, widely adopted benchmark for semantic-shift OOD detection on tabular data, comparable to OpenOOD for images?

### Takeaway
No. I found no established, widely adopted benchmark for semantic-shift (unseen-class) OOD detection on tabular
data. OpenOOD is image-only; the tabular items called "benchmark" are either medical covariate-shift studies
(eICU/MIMIC), prediction-under-shift benchmarks (TableShift, WhyShift, TabReD, BeyondArena), or anomaly-detection
benchmarks (ADBench, macrOData).

### Cited Findings
- OpenOOD provides "9 benchmarks under generalized OOD detection that originated from anomaly detection (AD), open set recognition (OSR), and OOD detection", all on image datasets (e.g. the ImageNet-200 benchmark). — [OpenOOD, NeurIPS 2022 D&B](https://papers.neurips.cc/paper_files/paper/2022/file/d201587e3a84fc4761eadc743e9b3f35-Paper-Datasets_and_Benchmarks.pdf); [OpenOOD v1.5](https://arxiv.org/pdf/2306.09301)
- The only tabular work self-described as an OOD-detection benchmark uses eICU and MIMIC-IV with subgroup and cross-dataset shift, not unseen classes. — [arXiv 2309.16220](https://arxiv.org/pdf/2309.16220)
- Cheng et al. (2025) state that "Existing benchmarks for evaluating model performance in open environments typically focus on a single task, such as distribution shift or feature shift", and build their new-class task themselves from four UCI/Kaggle tables rather than citing an existing new-class benchmark. — [arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)
- Loza et al. (2026): "While existing benchmarks such as TableShift have evaluated the OOD effect on traditional machine learning models, the robustness of TFMs to distribution shifts remains underexplored" (prediction under shift, not detection). — [arXiv 2607.26000](https://arxiv.org/html/2607.26000v1)
- ADBench is called "the de facto OD benchmark with 57 datasets" for tabular outlier detection; its 2026 successors (OddBench, OvRBench, SynBench) are one-class / unsupervised. — [arXiv 2602.03018](https://arxiv.org/pdf/2602.03018); [arXiv 2602.09329](https://arxiv.org/html/2602.09329v1)
- Each class-holdout paper assembles its own tables: TC (8 tables), Deep-MCDD (4), DNN-GDITD (4), PC pseudo-metric (5 + MNIST), Cheng et al. (4). — [TC DOI](https://doi.org/10.1016/j.artint.2024.104275); [arXiv 2104.00941](https://arxiv.org/pdf/2104.00941); [arXiv 2409.00980](https://arxiv.org/html/2409.00980v2); [arXiv 2608.09117](https://arxiv.org/pdf/2608.09117); [arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)

### Inferences
- The absence is a negative result from targeted searches (about 10 queries) plus the related-work framing of the 2025-2026 papers read; it is not a proof. I am fairly confident nothing with OpenOOD-like adoption exists, because every class-holdout paper I read builds its own pool and none cites a shared one.
- The paper can state: "there is no standard benchmark for unseen-class OOD detection on tables; prior work uses 4 to 8 ad hoc tables with a random split", citing TC, Deep-MCDD and Cheng et al. A principled screen of a curated benchmark (BeyondArena, 142 tasks, rules R1-R4) is then defensible as more systematic than the precedents.
- The benchmark a reviewer is most likely to name is ADBench; the answer is that it is a one-class AD benchmark without a K-class label space or group/time structure.

### Gaps
- Papers with Code was not queried directly. OpenReview submissions under review in late 2026 were not searched.

## Q5. Which of the datasets found are NOT in BeyondArena / our nine tables?

### Takeaway
Overlap is small. From the class-holdout literature only Covertype and (probably) Stellar/SDSS17 are in our nine
tables; BeyondArena additionally contains the HELOC and ANES voting tasks (binary) and Wine Quality (as regression).
Everything else used by the literature (Gas Sensor, Sensorless Drive Diagnosis, Shuttle, Letter, Pendigits,
Satimage, HAR, US Census 1990, Gisette, Gene, Arrhythmia, Eye Movements, CMC, MIMIC/eICU, CIC-IDS2017 etc.) is
outside BeyondArena, and none of those tables is used with a group or time split in the papers.

### Cited Findings
- BeyondArena's dataset table (full text) contains `covertype`, `sdss_17` (Kaggle 2022, 78,053 rows, 3 classes, listed as IID), `splice` (UCI 1991, 3,190 rows, 3 classes, IID), `otto_group_product_classification_challenge` (Kaggle 2015, 61,878 rows, 9 classes, IID), `wine_quality` (UCI 2009, 6,497 rows, regression, IID), `heloc` (Kaggle 2021, binary, IID), `anes_voting_2026` (48,587 rows, binary, temporal), `asp_potassco_classification` (ASlib 2014, 1,212 rows, 11 classes, grouped). — [arXiv 2606.30410](https://arxiv.org/pdf/2606.30410)
- A case-insensitive search of the BeyondArena PDF text gives zero hits for: skyserver, arrhythmia, gisette, eye movements, contracept / cmc, pendigits, satimage, census, optdigits, cnae, mfeat, helena, jannis, aloi, connect-4, sensorless, mimic, eicu, unsw, cic-ids, adbench, whyshift; "letter", "adult" and "gene" each occur once and not as dataset names in the table. — [arXiv 2606.30410](https://arxiv.org/pdf/2606.30410)

Membership table (literature dataset -> status)

| Dataset (paper) | Protocol in that paper | In BeyondArena? | In our 9? |
|---|---|---|---|
| Covertype / Forest Cover Type (PC pseudo-metric; TabularNCD; Ginanjar) | class holdout / NCD | yes | yes |
| Stellar (TC) | smallest class OOD | probably = `sdss_17` (inference) | yes (if same) |
| Wine (TC); Wine-Red, Wine-White (Cheng et al.) | class holdout | `wine_quality` present, but as regression | no |
| HELOC, ANES Voting (Loza et al.; TableShift) | covariate/label shift, binary | yes (`heloc`, `anes_voting_2026`), binary | no (fail R1) |
| Childhood Lead (Loza et al.; TableShift) | covariate shift, binary | not found by search | no |
| Skyserver, Arrhythmia, Gisette, SHABD, Gene, Speech (TC) | smallest class OOD | not found | no |
| EyeMovement, CMC (Cheng et al.) | leave-one-class-out | not found | no |
| GasSensor, Shuttle, DriveDiagnosis / Sensorless (Deep-MCDD; DNN-GDITD; PC) | leave-one-class-out | not found | no |
| Adult, Census-KDD, Connect-4 (PC) | one class ID vs each other class | not found | no |
| Letter, HAR, Satimage, Pendigits, US Census 1990, Multiple Features, Optdigits, CNAE-9 (TabularNCD) | NCD | not found | no |
| MNIST flattened (Deep-MCDD; DNN-GDITD; TabularNCD; PC) | class holdout | no (image) | no |
| MIMIC-III, MIMIC-IV, eICU (Ulmer; Azizmalayeri) | subgroup / cross-dataset shift | not found | no |
| NSL-KDD, UNSW-NB15, CIC-IDS2017 (intrusion OSR) | held-out attack class | not found | no |
| ADBench 57; OddBench; OvRBench; SynBench (FoMo-0D; OutFormer; macrOData) | one-class AD | no | no |

Sources for the table rows: [arXiv 2606.30410](https://arxiv.org/pdf/2606.30410) for the BeyondArena column; per-paper sources as cited in Q1-Q3.

### Inferences
- None of the missing tables is "standard" in the sense of being shared by a benchmark; each is used by one or two papers. The most defensible additions, if a reviewer asks for literature tables, would be those reused across papers and multiclass: Sensorless Drive Diagnosis and Gas Sensor (3 papers / 2 papers), Shuttle, Letter / Pendigits / HAR (NCD line), and the TC set (to match zhao2025tc exactly). All of these are IID tables without a group or time column in the cited protocols, except that Gas Sensor Array Drift is recorded in batches over time and HAR has subject identifiers at source; whether those support our R2 (real group/time split) would need checking against the raw data. This last point is from my background knowledge, not from the papers read.
- The medical ICU data (MIMIC/eICU) are the only "benchmark" a tabular-OOD reviewer is likely to call standard, and they are a different protocol (covariate shift, binary label, credentialed access). They are grouped by hospital (eICU) and time, so they are closest in spirit to our deployment story, but they do not support class holdout without redefining the label.
- Intrusion-detection tables (CIC-IDS2017, UNSW-NB15) are multiclass and temporal by capture day, so they are the only literature family that could pass both R1 and a temporal R2; they are outside BeyondArena and have known data-quality criticism. Background knowledge, not verified here.
- Our auxiliary script `exp/ood_lostclues.py` already runs the TC protocol on eight BeyondArena tables including `splice` and `otto`, which mirrors the TC table count but not its tables.

### Gaps
- Membership was checked by string search on the extracted PDF text of arXiv 2606.30410 (v1), not against the BeyondArena metadata files; a dataset present under a different name would be missed (e.g. HAR, Gas Sensor or Shuttle under another task name). Verify against the BeyondArena metadata in `data/` before stating non-membership in the paper.
- Whether TC's "Stellar" equals BeyondArena's `sdss_17` is inferred, not confirmed.
- I did not enumerate the 25 multiclass BeyondArena tasks; the draft's screening script is the authority for that.
