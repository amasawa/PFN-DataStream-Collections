# Tabular distribution-shift benchmarks: multiclass tables with group/time structure (state: 1 Oct 2026)

Provenance note: web sources were read through a summarising fetch tool, so numbers quoted from papers are as reported
by that tool and were not re-read in the PDF. The BeyondArena tallies were computed by me from the task/dataset
metadata JSON of the HF dataset `TabArena/BeyondArena` (local HF cache, read-only, same files that
`exp/screen_datasets.py` reads); they are not numbers printed in the paper.

## TableShift (Gardner et al., NeurIPS 2023): the 15 tasks, label type, domain column. Any multiclass?

### Takeaway
All 15 TableShift tasks are binary by design (binary label is an explicit inclusion criterion), so none can supply a held-out class. Five of the 15 need credentialed access.

### Cited Findings
- The paper states "TableShift contains 15 binary classification tasks in total, each with an associated shift", and lists as selection criterion "Binary Classification: supports a meaningful binary classification task (regression tasks are not included)." — [TableShift paper, arXiv 2312.07577](https://ar5iv.labs.arxiv.org/html/2312.07577)
- Task list (target; shift variable; observations; source; access) — [tableshift.org/datasets](https://tableshift.org/datasets.html):

| Task | Target (all binary) | Domain / shift column | Rows | Source | Access |
|---|---|---|---|---|---|
| Voting | voted in US presidential election | geographic region | 8,280 | ANES | credentialed |
| ASSISTments | next answer correct | school | 2,667,776 | Kaggle | public |
| Childhood Lead | blood lead above CDC threshold | poverty level | 27,499 | NHANES | public |
| College Scorecard | low degree completion rate | institution type | 124,699 | College Scorecard | public |
| Diabetes | diabetes diagnosis | race/ethnicity | 1,444,176 | BRFSS | public |
| Food Stamps | food stamp recipiency | geographic region | 840,582 | ACS | public |
| HELOC | loan repayment | external risk estimate | 10,459 | FICO | credentialed |
| Hospital Readmission | 30-day readmission | admission source | 99,493 | UCI | public |
| Hypertension | hypertension diagnosis | BMI category | 846,761 | BRFSS | public |
| ICU Length of Stay | stay >= 3 days | insurance type | 23,944 | MIMIC-III | credentialed |
| ICU Mortality | hospital mortality | insurance type | 23,944 | MIMIC-III | credentialed |
| Income | income >= $56k | geographic region | 1,664,500 | ACS | public |
| Public Health Insurance | public coverage | disability status | 5,916,565 | ACS | public |
| Sepsis | sepsis onset within 6 h | length of stay | 1,552,210 | PhysioNet | public |
| Unemployment | unemployment status | education level | 1,795,434 | ACS | public |

- The site's own summary: 10 public datasets, 5 requiring credentialed access / data use agreements. — [tableshift.org/datasets](https://tableshift.org/datasets.html)

### Inferences
- TableShift fails R1 for every task. Its absence from our table is a consequence of the binary-only design, not a gap in our screening.
- Two TableShift-derived tasks appear in BeyondArena, both binary: `anes_voting_2026` (temporal) and `sepsis_prediction` (grouped by `Patient_ID`); see the BeyondArena section. That these correspond to TableShift's Voting and Sepsis is my inference from the names and sources, not a statement found in the paper.

### Gaps
- Feature counts per TableShift task: the dataset page does not give them ("Not specified"); not verified.
- The table lists 5 credentialed rows (Voting, HELOC, ICU LOS, ICU Mortality = 4 distinct rows shown above as credentialed) — the page says 5; the tool output marks only 4 rows credentialed, so one row's access flag may be mis-transcribed. Not resolved.

## TabReD (Rubachev et al.): datasets, task types, temporal structure. Any multiclass?

### Takeaway
TabReD has 8 datasets, 3 binary classification and 5 regression, all with timestamp-based splits; no multiclass task.

### Cited Findings
- Datasets and task type per the paper (Table 2 / App. B): Homesite Insurance (binary, 224K, 296 feat.), Ecom Offers (binary, 106K, 119), HomeCredit Default (binary, 381K, 696), Sberbank Housing (regression, 20K, 387), Cooking Time (regression, 228K, 195), Delivery ETA (regression, 224K, 225), Maps Routing (regression, 192K, 1026), Weather (regression, 605K, 98). "No multiclass datasets are included." — [TabReD paper, arXiv 2406.19380](https://ar5iv.labs.arxiv.org/html/2406.19380)
- The repo README gives different "rows used"/feature numbers: Homesite 260,753 / 299; Ecom Offers 160,057 / 119; Homecredit 381,664 / 696; Sberbank 28,321 / 392; Cooking Time 319,986 / 192; Delivery ETA 416,451 / 223; Maps Routing 340,981 / 986; Weather 423,795 / 103. — [github.com/yandex-research/tabred](https://github.com/yandex-research/tabred); differs from [the paper](https://ar5iv.labs.arxiv.org/html/2406.19380)
- Described as "eight industry-grade tabular datasets" with "temporal distribution shift"; a default time split plus 3 random and 3 sliding-window split variants; data on Kaggle; repo code licence Apache-2.0. — [github.com/yandex-research/tabred](https://github.com/yandex-research/tabred)

### Inferences
- TabReD fails R1 everywhere. The row/feature discrepancy between paper and repo is probably a benchmark version difference (subsampled vs full); cite one source consistently.
- TabReD members appear in BeyondArena as temporal tasks (`home_credit_default_stability` binary; `cooking_time`, `delivery_eta`, `maps_router_eta`, `sberbank_housing_market_forecasting`, `climate_model_weather_forecasting` regression) — name-based matching by me.

### Gaps
- Exact time spans per dataset were not extracted.

## WILDS, Wild-Time, WhyShift, Shifts, Folktables/ACS: contents, binary vs multiclass, group column

### Takeaway
Of these five, only the Shifts weather dataset has a tabular multiclass label with real group/time structure (9 precipitation classes, climate type and time). WILDS has no tabular member; Wild-Time's only non-image/text tasks (MIMIC-IV) are binary and credentialed; WhyShift and the Folktables predefined tasks are all binary.

### Cited Findings
- WILDS: iWildCam (image, 182 classes, camera), Camelyon17 (image, binary, hospital), RxRx1 (image, 1,139 classes, batch), OGB-MolPCBA (graph, 128 binary labels, scaffold), GlobalWheat (detection), CivilComments (text, binary), FMoW (image, 62 classes, year x region), PovertyMap (image, regression), Amazon (text, 5 classes, reviewer), Py150 (code). None is a feature-vector table. — [wilds.stanford.edu/datasets](https://wilds.stanford.edu/datasets/)
- Wild-Time: MIMIC-IV supplies two tasks, MIMIC-Readmission (readmitted within 15 days, binary) and MIMIC-Mortality (in-hospital death, binary); input is the concatenated ICD9 diagnosis and treatment codes per patient; time is grouped in three-year blocks 2008-2010, 2011-2013, 2014-2016, 2017-2019; MIMIC-IV covers 382,278 patients. — [Wild-Time paper, arXiv 2211.14238](https://arxiv.org/pdf/2211.14238)
- WhyShift: 22 settings over 5 datasets, all binary: ACS Income (>= $50k; 9 features; state shift), ACS Mobility (same address; 21 features; state), ACS Public Coverage (18 features; state and year), Taxi (duration >= 30 min; 7 features; city), US Accident (severity, binarised; 47 features; state). Code MIT; Kaggle sources CC BY-SA 4.0 as reported; ACS under Census Bureau terms. — [github.com/namkoong-lab/whyshift](https://github.com/namkoong-lab/whyshift); paper [arXiv 2307.05284](https://arxiv.org/abs/2307.05284)
- Folktables: predefined tasks ACSIncome, ACSPublicCoverage, ACSMobility, ACSEmployment, ACSTravelTime are all binary; data span all US states and several survey years; code MIT; data "governed by the terms of use provided by the Census Bureau". — [github.com/socialfoundations/folktables](https://github.com/socialfoundations/folktables)
- Shifts weather (Malinin et al., 2021): 123 meteorological features, 4 metadata attributes (time, latitude, longitude, climate type), 2 targets (air temperature = regression; precipitation class = 9-class classification, classes labelled 0-8). Canonical partition: train 3,129,592; dev_in 50,000; dev_out 50,000; eval_in 561,105; eval_out 576,626 rows. Train / in-domain: Tropical, Dry, Mild Temperate climates, Sep 2018 - 8 Apr 2019. dev_out: Snow climate, 8 Jul - 1 Sep 2019. eval_out: Snow and Polar, 14 May - 8 Jul 2019. — [Shifts paper, arXiv 2107.07455](https://ar5iv.labs.arxiv.org/html/2107.07455)
- Shifts weather full dataset: about 10 million entries, 129 columns, uniformly distributed between 1 Sep 2018 and 1 Sep 2019. — [Shifts paper, arXiv 2107.07455](https://arxiv.org/pdf/2107.07455)
- Shifts weather data licence: CC BY NC SA 4.0; downloads: canonical partition `https://storage.yandexcloud.net/yandex-research/shifts/weather/canonical-partitioned-dataset.tar`, full `.../weather/full-dataset.tar`. — [github.com/Shifts-Project/shifts](https://github.com/Shifts-Project/shifts). A search snippet reported "Apache-2.0" for this dataset, which is the code-repo/third-party-mirror licence, not the data licence — [whylogs dataset page](https://whylogs.readthedocs.io/en/stable/datasets/weather.html)

### Inferences
- Wild-Time MIMIC is not a fixed-width table (code sequences), is binary, and needs PhysioNet credentialing: fails R1 and is unusable under an open-data constraint.
- The raw ACS PUMS table contains multi-valued columns (occupation, class of worker, marital status, etc.) with state/year structure, so a multiclass grouped task could be constructed from it, but that would be a task we define ourselves, not a benchmark task; no benchmark above ships one.
- US Accident has a 4-level severity in its original Kaggle form; WhyShift binarises it. Same caveat: a self-defined task, not a benchmark task. (The 4-level fact is from my background knowledge, not a fetched source.)

### Gaps
- Shifts precipitation: per-class row counts (hence the smallest class with >= 30 rows) were not found in the paper excerpt or the repo README; needs the data (canonical tar is several GB; not downloaded).
- WILDS/Wild-Time row counts were not collected because none qualify.
- WhyShift per-setting sample sizes are ranges only (e.g. ACS Income 4.9k-195k per state).

## Which multiclass tables with group or time structure exist in these benchmarks and are NOT among our 9?

### Takeaway
Exactly two: Shifts weather precipitation (outside BeyondArena; passes R1-R3 on paper, R4 unverified) and BeyondArena's own `micro_mass` (grouped by strain, rejected by R3 with 1,082 features). All other benchmarks surveyed are binary/regression-only or non-tabular.

### Cited Findings
- Shifts weather precipitation: 9 classes (8 ID classes after hold-out, within the <= 10 limit), 123 features (<= 500), group columns climate type (5 types: Tropical, Dry, Mild Temperate, Snow, Polar) and time; 4,367,323 rows in the canonical partition (sum of the five parts above), ~10M in the full set; CC BY NC SA 4.0. — [Shifts paper](https://ar5iv.labs.arxiv.org/html/2107.07455); [Shifts repo](https://github.com/Shifts-Project/shifts)
- `micro_mass` in BeyondArena: multiclass, official grouped split on `Strain`, source UCI, licence CC BY 4.0, 1,082 feature columns after removing target and group column, so R3 (<= 500 features) rejects it. — metadata of [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena), tallied locally (`exp/results_screen/screen.csv`)
- BeyondArena contains 8 multiclass tasks with an official grouped or temporal split: grouped `asp_potassco_classification`, `cardiotocography`, `covertype`, `dementia_prediction`, `mice_protein_trisomy_discriminant`, `micro_mass`; temporal `consumer_complaints`, `ghanas_indigenous_intel`. Seven are in our table; the eighth is `micro_mass`. — metadata of [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)

### Inferences
- Within the surveyed shift benchmarks, the 9-table set is complete under R1-R4 except for one candidate outside BeyondArena: Shifts precipitation. A defensible sentence for the paper: TableShift, TabReD, WhyShift and Folktables contain only binary or regression tasks, WILDS has no tabular task, Wild-Time's MIMIC tasks are binary; the only multiclass shifted table is Shifts weather.
- Reasons one could give for not adding Shifts precipitation, each needing a check before being written: (i) non-commercial licence (but `dementia_prediction` is already CC BY NC, so licence alone is not a consistent exclusion reason); (ii) only 5 climate groups (but `covertype` has 3); (iii) scale (3.1M training rows; `consumer_complaints` is already 1.2M). None of our rules R1-R4 obviously excludes it; the honest position is that it lies outside the BeyondArena universe the screening was defined over. Adding it as a tenth table or stating the universe restriction explicitly are the two clean options.
- Precipitation classes in Shifts combine precipitation type and cloud cover, so the "unseen class" there is semantically close to its neighbours; this affects the interpretation of a held-out class but not eligibility.

### Gaps
- R4 for Shifts precipitation (smallest class with >= 30 rows) is unverified; class frequencies were not found.
- `micro_mass` row and class counts were not loaded by the screening script (it loads data only for tasks passing R2 and R3) and were not verified here.
- Not searched in this pass: other shift collections outside the list (e.g. TabZilla/OpenML temporal tasks, Kaggle tabular playground). Scope was limited to the benchmarks named in the assignment.

## What exactly does BeyondArena contain?

### Takeaway
BeyondArena has 142 tasks: 103 IID, 21 temporal, 18 grouped; 73 binary, 25 multiclass, 44 regression. Only 8 of the 25 multiclass tasks have an official non-IID split (6 grouped, 2 temporal); the other 17 are IID.

### Cited Findings
- Paper: "Beyond IID: How General Are Tabular Foundation Models, Really?", Purucker, Tschalzev, Erickson, Blayer, Holzmüller, Arazi, Pfefferle, Tajjar, Varoquaux, Hutter; arXiv 2606.30410, submitted 29 June 2026; 11 models, 142 curated datasets; task types IID, temporal, grouped. — [arXiv 2606.30410](https://arxiv.org/abs/2606.30410)
- "We gathered datasets from 21 tabular benchmark studies": 14 prior tabular benchmarks (304 datasets re-evaluated) plus 7 non-IID/multimodal benchmarks: TabReD, TableShift, the string-vectorizing benchmark, CARTE, TextTabBench, TabSTAR, AutoGluon Multimodal; plus searches of UCI, OpenML, Hugging Face, Kaggle, Zindi, ASlib and government sites. "We collected 1128 datasets, of which 142 met our selection criteria." — [arXiv 2606.30410 HTML](https://arxiv.org/html/2606.30410)
- Selection criteria: unique within the benchmark; >= 100 training samples; IID or non-IID tabular task; published for predictive classification/regression; representative of real applications; no obvious ethical concerns. — [arXiv 2606.30410 HTML](https://arxiv.org/html/2606.30410)
- Code `https://tabarena.ai/code`, data tooling `https://github.com/TabArena/data-foundry`. — [arXiv 2606.30410](https://arxiv.org/pdf/2606.30410)
- HF dataset card: 142 subsets, 197 to 1.25M rows, licence field "copyright-at-original-authors", linked papers arXiv 2606.30410 and 2506.16791. — [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)
- Composition, tallied from the per-task metadata (`group_on` / `time_on` / `problem_type`) of all 142 tasks — [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena):

| split type | binary | multiclass | regression | total |
|---|---|---|---|---|
| IID | 60 | 17 | 26 | 103 |
| grouped | 5 | 6 | 7 | 18 |
| temporal | 8 | 2 | 11 | 21 |
| total | 73 | 25 | 44 | 142 |

- Grouped classification tasks (group column; source; licence): binary `amex_non_iid` (customer_ID; Kaggle; competition licence), `musk` (molecule_name; UCI; CC BY 4.0), `pancreatic_cancer_mouse_detection` (mouse_id; none stated), `parkinsons_biomedical_voice_measurements` (patient_id; UCI; CC BY 4.0), `sepsis_prediction` (Patient_ID; ODbL); multiclass `asp_potassco_classification` (task_id; ASlib; GPLv3), `cardiotocography` (patient_id; UCI; CC BY 4.0), `covertype` (Wilderness_Area; UCI; CC BY 4.0), `dementia_prediction` (Subject ID; CC BY NC 3.0), `mice_protein_trisomy_discriminant` (MouseID; UCI; CC BY 4.0), `micro_mass` (Strain; UCI; CC BY 4.0). — [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)
- Temporal classification tasks (time column): binary `acquire_valued_shoppers_challenge` (offerdate), `anes_voting_2026` (VCF0004), `home_credit_default_stability` (date_decision), `hotel_booking_demand` (arrival_date), `ieee_fraud_detection` (Transaction_date), `kick` (PurchDate), `kickstarter` (created_at), `lending_club` (issue_d); multiclass `consumer_complaints` (Date received; US Government Works), `ghanas_indigenous_intel` (prediction_time; CC-BY-SA 4.0). — [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)
- The 17 IID multiclass tasks: maternal_health_risk, mic, predict_students_dropout_and_academic_success, sdss_17, splice, website_phishing, audiology_diagnosis, biomechanical_orthopaedic_prediction, ecoli_proteins, eryhemato_squamous_disease, forensic_glass_identification, hepatitis_c_prediction, horse_colic_survival, ljubljana_primary_tumor, otto_group_product_classification_challenge, biogeographical_ancestry_prediction, lung_cancer. — [HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)

### Inferences
- Our 9 tables = 7 of the 8 officially non-IID multiclass tasks (all but `micro_mass`, R3) + 2 IID tasks with an entity column (`sdss_17`/plate, `predict_students_dropout`/Course). So the selection exhausts BeyondArena's non-IID multiclass tasks under R3.
- BeyondArena screened TableShift and TabReD but took no multiclass task from either, consistent with both being binary/regression-only. Shifts, WhyShift, WILDS, Wild-Time and Folktables are not named among its 21 sources, so Shifts precipitation was never a BeyondArena candidate.
- BeyondArena's `climate_model_weather_forecasting` (temporal regression, `fact_time`, CC-BY-NC-SA-4.0) is a Yandex weather temperature task; whether it is TabReD Weather or the Shifts weather table was not verified. Either way only the temperature regression target is used, not the precipitation class.

### Gaps
- The paper text (as fetched) does not print the IID/temporal/grouped or binary/multiclass/regression counts; the table above is my tally from metadata and should be cited as such (or checked against the paper's Figure 3 / appendix tables).
- The full names of the 14 "prior tabular benchmarks" were not extracted.
- Whether the paper version changed after June 2026 (later arXiv versions, task additions) was not checked; the tally reflects the locally cached HF snapshot.
