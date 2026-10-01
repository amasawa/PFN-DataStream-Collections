# Candidate public tables (outside BeyondArena) for unseen-class OOD on grouped / temporal tables (state: 2026-10-01)

Conventions. "VERIFIED-FILE" = I downloaded the (small) released file today and counted it myself. "VERIFIED-PAGE" = number read on the primary source page / API today. "UNVERIFIED (memory)" = value recalled from the literature, NOT confirmed on a primary source in this session; must be re-counted before use. Rules R1-R4 as in `exp/screen_datasets.py` (>=3 classes; group or time structure; <=500 features, <=10 ID classes; smallest class with >=30 rows is the OOD class).

## Q1. Which tables have subject / device / site / batch IDs (or timestamps) and >=3 classes? Shortlist and ranking

### Takeaway
Seven tables pass R1-R4, are outside BeyondArena, and are absent from both pretraining lists: OULAD, batteryless-wearable activity (UCI 427), HAR70+, WISDM v1.1 (transformed), MoCap Hand Postures, eucalyptus, and N-BaIoT; Gesture Phase Segmentation is a usable eighth with only 7 groups. The two "obvious" candidates, Gas Sensor Array Drift and eye_movements, satisfy R1-R4 but are in the pretraining data of BOTH TabDPT and Real-TabPFN-2.5.

### Cited Findings

#### Ranked shortlist (best first)

| # | table | source | licence | rows | feat. | classes (counts) | group column / #groups | status |
|---|---|---|---|---|---|---|---|---|
| 1 | OULAD `studentInfo` | UCI 349 | CC BY 4.0 | 32,593 (UNVERIFIED, memory) | ~9 demographic (+ aggregates from other tables) | 4: Pass 12,361 / Withdrawn 10,156 / Fail 7,052 / Distinction 3,024 (UNVERIFIED, memory) | `code_module` x `code_presentation`, 22 module-presentations over 7 modules (22 UNVERIFIED; 7 modules VERIFIED-PAGE) | clean |
| 2 | Activity recognition, healthy older people, batteryless wearable | UCI 427 | CC BY 4.0 | 75,128 | 8 (time, 3 acc, antenna id, RSSI, phase, frequency) | 4: lying 51,520 / sit on bed 16,406 / sit on chair 4,911 / ambulating 2,291 | trial file (participant id + sex in filename, e.g. `d1p33F`); 87 files, 2 rooms (60 + 27) | clean, VERIFIED-FILE |
| 3 | HAR70+ | UCI 780 | CC BY 4.0 | 2,259,597 | 6 (2 x 3-axis acc) + timestamp | 7: walking, shuffling, stairs up, stairs down, standing, sitting, lying (counts not on page) | one CSV per subject, 18 subjects | clean, VERIFIED-PAGE |
| 4 | WISDM Activity Prediction v1.1, transformed | Fordham WISDM lab | no formal licence; citation requested, readme must accompany redistribution | 5,424 | 46 attributes incl. id/user/class (43 features) | 6: Walking 2,082 / Jogging 1,626 / Upstairs 633 / Downstairs 529 / Sitting 307 / Standing 247 | user, 36 users | clean; user column in the transformed ARFF UNVERIFIED |
| 5 | Motion Capture Hand Postures | UCI 405 | CC BY 4.0 | 78,095 | 36 (X/Y/Z of up to 12 markers) | 5 postures (counts not on page; roughly balanced, UNVERIFIED) | `User`, 12 users | clean, VERIFIED-PAGE |
| 6 | eucalyptus | OpenML 188 | "Public" | 736 | 19 | 5: good 214 / none 180 / average 130 / low 107 / best 105 | `Abbrev` (trial site), 16 sites; also `Locality` (8), `Year` (5) | clean, VERIFIED-FILE |
| 7 | N-BaIoT | UCI 442 | CC BY 4.0 | 7,062,606 | 115 (UNVERIFIED count; page gives none) | 11: benign + 10 attacks (Mirai, BASHLITE) | device, 9 devices (files per device) | clean, VERIFIED-PAGE |
| 8 | Gesture Phase Segmentation (raw files) | UCI 302 | CC BY 4.0 (UCI default; not re-read today) | 9,901 raw rows | 18 + timestamp (raw); 32 (processed) | 5: Rest 2,769 / Stroke 2,950 / Preparation 2,097 / Retraction 1,087 / Hold 998 | video file, 7 videos from 3 users (a1-a3, b1, b3, c1, c3) | clean, VERIFIED-FILE |

Details and caveats for the shortlist:

- OULAD: licence CC BY 4.0; five CSV files (studentInfo 3.3 MB, studentVle 432.8 MB, ...); seven courses, presentations coded B (February) and J (October); "more than 30,000 students" — [UCI 349](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset). The UCI API reports `num_instances = 0` for this entry, so the row and class counts in the table are not on the primary page — [UCI API 349](https://archive.ics.uci.edu/api/dataset?id=349).
- Batteryless wearable: page states 75,128 instances, 14 participants aged 66-86, two room settings (S1 with 4 antennas, S2 with 3), 4 activity labels, CC BY 4.0, DOI 10.24432/C5GG6B — [UCI 427](https://archive.ics.uci.edu/dataset/427/activity+recognition+with+healthy+older+people+using+a+batteryless+wearable+sensor). My count of the released zip: 87 data files (60 in room 1, 27 in room 2), 75,128 rows, class counts as in the table; rows per file min 7, median 457, max 4,638; 65 of 87 files contain all 4 classes, 14 contain 3, 4 contain 2, 4 contain 1 — [UCI 427 zip](https://archive.ics.uci.edu/static/public/427/activity+recognition+with+healthy+older+people+using+a+batteryless+wearable+sensor.zip). Conflict: the page summary (as read by the fetch tool) says 91 files, the zip holds 87 files matching `d[12]pNN[MF]`.
- HAR70+: 18 older adults (70-95 years), one CSV per subject, columns timestamp + back x/y/z + thigh x/y/z + label, label codes 1, 3, 4, 5, 6, 7, 8, CC BY 4.0, DOI 10.24432/C5CW3D — [UCI 780](https://archive.ics.uci.edu/dataset/780/har70).
- WISDM v1.1: raw 1,098,207 examples, transformed 5,424 examples, 36 users, 46 transformed attributes, class distribution as in the table, citation request (Kwapisz, Weiss & Moore 2010) — [WISDM lab dataset page](https://www.cis.fordham.edu/wisdm/dataset.php).
- MoCap Hand Postures: 78,095 records, columns `Class`, `User`, X0-X11/Y0-Y11/Z0-Z11, 12 users, '?' for missing markers (3 to 12 visible markers per record), markers unlabeled and permutable, leave-one-user-out recommended by the donors, near-duplicate frames within a user, CC BY 4.0, DOI 10.24432/C5TG86 — [UCI 405](https://archive.ics.uci.edu/dataset/405/motion+capture+hand+postures).
- eucalyptus: 736 rows, 20 columns incl. target `Utility`, 448 missing values — [OpenML qualities 188](https://www.openml.org/api/v1/json/data/qualities/188). My count of the ARFF: rows per site Cly 24, Cra 30, K81 65, K81a 33, K82 45, K83 49, Lon 53, Mor 63, Nga 22, Paw 55, Puk 84, WSh 5, WSp 59, Wai 70, Wak 73, Wen 6; sites Mor and Wen contain a single class, WSh two; planting years 1980-1986 — [OpenML ARFF 188](https://www.openml.org/data/download/3625/dataset_194_eucalyptus.arff).
- N-BaIoT: 7,062,606 records, 9 commercial IoT devices, "10 classes of attacks, plus 1 class of benign", files organised per device, CC BY 4.0, DOI 10.24432/C5RC8J — [UCI 442](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot).
- Gesture Phase Segmentation: raw files have 18 numeric attributes, a timestamp and the class; processed files 32 attributes — [UCI API 302](https://archive.ics.uci.edu/api/dataset?id=302). My count of the 7 raw files: a1 1,747 / a2 1,264 / a3 1,834 / b1 1,073 / b3 1,424 / c1 1,111 / c3 1,448 rows; all five phases in every file; smallest per-file class 39 rows (Hold in a1); one mislabelled row "Preparação" in b1 — [UCI 302 zip](https://archive.ics.uci.edu/static/public/302/gesture+phase+segmentation.zip).

#### Further candidates that pass R1-R4 but carry a blocking or serious caveat

| table | source | rows / feat. / classes | group | caveat |
|---|---|---|---|---|
| Gas Sensor Array Drift | UCI 224, OpenML 1476 | 13,910 / 128 / 6 gases, min class 1,641 | 10 batches over 36 months | in TabDPT AND Real-TabPFN-2.5 pretraining |
| eye_movements | OpenML 1044 | 10,936 / 27 / 3 (min 2,870, max 4,262) | `assgNo`, `lineNo` columns present | in TabDPT AND Real-TabPFN-2.5 pretraining |
| Localization Data for Person Activity (ldpa) | UCI 196, OpenML 1483 | 164,860 / 7 / 11 (min 1,381, max 54,480) | 25 sequences, 5 persons, timestamps | in TabDPT pretraining; 11 classes is the upper limit |
| Room Occupancy Estimation | UCI 864 | 10,129 / 16 + Date, Time / 4: 0 -> 8,228, 1 -> 459, 2 -> 748, 3 -> 694 | timestamp, 7 calendar days | non-zero classes occur on only 3 of 7 days |
| Steel Industry Energy Consumption | UCI 851 | 35,040 / 9 + date / 3: Light 18,072, Medium 9,696, Maximum 7,272 | timestamp, 15-min steps over 2018 | label is a time-of-day schedule |
| Anuran Calls (MFCCs) | UCI 406 | 7,195 / 22 / Family 4 (4,420 / 2,165 / 542 / 68), Genus 8, Species 10 (min 68) | `RecordID`, 60 recordings | label constant within group |
| UNSW-NB15 | UNSW | 2,540,044 / 49 / 10 (normal + 9 attacks) | time (Stime/Ltime, UNVERIFIED on page) | academic-research-only licence; class counts not on page |
| ECG Arrhythmia Classification (MIT-BIH features) | Kaggle sadmansakib7 | ~100k beats (UNVERIFIED) / 34 / 5 (N, S, V, F, Q) | `record` = patient | licence and counts not verified; class Q very small (UNVERIFIED) |
| Pump it Up (Tanzania water points) | DrivenData | 59,400 / 40 / 3 | `region`, `date_recorded` | competition data, licence not stated in what I could read |
| Wall-Following Robot Navigation | UCI 194, OpenML 1497 | 5,456 / 24 / 4 (min 328, max 2,205) | none; row order only | no ID or timestamp column |

- Gas drift: 13,910 measurements, January 2007 to February 2011, 128 features (8 per sensor x 16 sensors), six gases (ethanol, ethylene, ammonia, acetaldehyde, acetone, toluene), ten files `batch1.dat` ... `batch10.dat`, CC BY 4.0, DOI 10.24432/C5RP6W — [UCI 224](https://archive.ics.uci.edu/dataset/224/gas+sensor+array+drift+dataset). The OpenML copy (1476) has no batch column (129 columns V1-V128 + Class) — [OpenML features 1476](https://www.openml.org/api/v1/json/data/features/1476).
- eye_movements: columns `lineNo`, `assgNo`, 25 gaze features, `label` in {0, 1, 2} — [OpenML features 1044](https://www.openml.org/api/v1/json/data/features/1044); class sizes — [OpenML qualities 1044](https://www.openml.org/api/v1/json/data/qualities/1044).
- ldpa: sequence names A01 ... E05 (5 people x 5 sequences), 4 tags, unique timestamps, 11 activities — [UCI API 196](https://archive.ics.uci.edu/api/dataset?id=196); class sizes — [OpenML qualities 1483](https://www.openml.org/api/v1/json/data/qualities/1483).
- Room occupancy: my count of the CSV (10,129 x 19): rows per date 2017/12/22 1,462 (4 classes), 12/23 2,779 (4), 12/24 1,064 (1), 12/25 1,716 (1), 12/26 1,063 (1), 2018/01/10 997 (3), 01/11 1,048 (1) — [UCI 864 zip](https://archive.ics.uci.edu/static/public/864/room+occupancy+estimation.zip).
- Steel industry: my count of the CSV (35,040 x 11, 01/01/2018 to 31/12/2018) — [UCI 851 zip](https://archive.ics.uci.edu/static/public/851/steel+industry+energy+consumption.zip).
- Anuran: my count of `Frogs_MFCCs.csv` (7,195 x 26): 60 RecordIDs, 1 to 458 rows per record, exactly one Family / Genus / Species per RecordID — [UCI 406 zip](https://archive.ics.uci.edu/static/public/406/anuran+calls+mfccs.zip).
- UNSW-NB15: 2,540,044 records in four CSV files, 49 features, nine attack categories, training set 175,341 and testing set 82,332 records, "free use ... for academic research purposes", commercial use by agreement — [UNSW-NB15 page](https://research.unsw.edu.au/projects/unsw-nb15-dataset).
- ECG features: first column `record` is the subject/patient, column `type` holds 5 classes (N, S, V, F, Q), 34 further columns (17 features per lead) — [mirror of the Kaggle dataset card](https://baselight.app/u/kaggle/dataset/sadmansakib7_ecg_arrhythmia_classification_dataset) (aggregator, not the Kaggle page itself).
- Pump it Up: 59,400 pumps, 40 columns, three classes (functional / functional needs repair / non functional), data from Taarifa and the Tanzanian Ministry of Water — [write-up](https://towardsdatascience.com/predicting-the-functionality-of-water-pumps-with-xgboost-8768b07ac7bb) (secondary source).
- Wall-following robot: 24 ultrasound readings + class — [UCI API 194](https://archive.ics.uci.edu/api/dataset?id=194); class sizes — [OpenML qualities 1497](https://www.openml.org/api/v1/json/data/qualities/1497).

#### Considered and rejected

| table | reason |
|---|---|
| HAR Using Smartphones (UCI 240, OpenML 1478) | 561 features > 500 (30 subjects, 6 classes, 10,299 rows otherwise fine) — [OpenML qualities 1478](https://www.openml.org/api/v1/json/data/qualities/1478) |
| UJIIndoorLoc (UCI 310) | 520 WAP features > 500 (has UserID, PhoneID, timestamp; BuildingID 3 / Floor 5 classes) — [UCI API 310](https://archive.ics.uci.edu/api/dataset?id=310) |
| HARTH (UCI 779) | raw 50 Hz samples, 6,461,328 rows; 12 activity labels (UNVERIFIED, memory) > 11 — [UCI API 779](https://archive.ics.uci.edu/api/dataset?id=779) |
| MHEALTH (UCI 319) | raw sensor logs per subject, 12 activities (UNVERIFIED, memory) > 11 — [UCI API 319](https://archive.ics.uci.edu/api/dataset?id=319) |
| WISDM 2019 smartphone + smartwatch (UCI 507) | 18 activity codes A-S, 51 subjects, 15.6M raw rows — [UCI API 507](https://archive.ics.uci.edu/api/dataset?id=507) |
| EMG Data for Gestures (UCI 481) | raw 8-channel time series with time in ms, not a flat feature table — [UCI API 481](https://archive.ics.uci.edu/api/dataset?id=481) |
| Gas sensors for home activity monitoring (UCI 362) | 100 inductions, each a single stimulus: label determined by the group; raw time series — [UCI API 362](https://archive.ics.uci.edu/api/dataset?id=362) |
| walking-activity (OpenML 1509) | the class IS the person (22 classes); also in TabDPT pretraining — [OpenML features 1509](https://www.openml.org/api/v1/json/data/features/1509) |
| Traffic_violations (OpenML 42345) | 70,340 rows, 3 classes (min 3,506), but the OpenML release has no date or officer column (`Year` is the vehicle year) — [OpenML features 42345](https://www.openml.org/api/v1/json/data/features/42345) |
| Heart Disease (UCI 45) | already in BeyondArena as three separate site tasks (cleveland, hungary, va_long_beach); only 4 sites — [BeyondArena tree](https://huggingface.co/api/datasets/TabArena/BeyondArena/tree/main) |
| Diabetes 130-US hospitals (UCI 296) | already in BeyondArena (`diabetes_130_us`) and in TabDPT pretraining (45022) — same sources as above and [TabDPT](https://arxiv.org/html/2410.18164) |
| Hepatitis C, Lending Club, Otto, Student Performance (Portuguese) | already in BeyondArena (`hepatitis_c_prediction`, `lending_club`, `otto_group_product_classification_challenge`, `student_portuguese_performance`) — [BeyondArena tree](https://huggingface.co/api/datasets/TabArena/BeyondArena/tree/main) |
| Richter's Predictor (Nepal earthquake damage, 3 classes, geo-level IDs) | in Real-TabPFN-2.5 fine-tuning list — [arXiv 2511.08667 App. C.1](https://arxiv.org/html/2511.08667) |
| SDSS DR14, SDSS DR16 (Kaggle) | in Real-TabPFN-2.5 fine-tuning list; also near-duplicates of our sdss_17 — [arXiv 2511.08667 App. C.1](https://arxiv.org/html/2511.08667) |
| Internet Firewall Data | in Real-TabPFN-2.5 fine-tuning list; no group or time column — [arXiv 2511.08667 App. C.1](https://arxiv.org/html/2511.08667) |
| road-safety, KDDCup99, sf-police-incidents | in TabDPT pretraining (45038, 42746, 42732) — [TabDPT Table B.1](https://arxiv.org/html/2410.18164) |
| Austin Animal Center outcomes (Kaggle "Shelter Animal Outcomes") | temporal and multiclass, but no licence is stated on the data.gov listing and class counts were not verified — [data.gov listing](https://catalog.data.gov/dataset/austin-animal-center-outcomes) |

### Inferences
- Ranking logic: OULAD first because it mirrors our `students` table (education, entity = course presentation) with 22 groups and four large classes; the batteryless-wearable table second because every number was re-counted from the file and most groups contain all classes; HAR70+, WISDM and MoCap give a subject-grouped sensor family that our nine tables lack; eucalyptus gives a small site-grouped agronomy table; N-BaIoT gives a device-grouped security table.
- Under the current rule set, N-BaIoT (9 devices) and Gesture Phase (7 videos) fall below the "at least ~10 groups" preference but above our existing covertype (3 areas), so they are consistent with the paper's own precedent.
- HAR70+, the batteryless table, MoCap and Gesture Phase have one row per time sample or frame: rows within a group are strongly autocorrelated, so the effective sample size is far below the row count, and HAR70+ and N-BaIoT need subsampling to fit a TabPFN context.
- Eucalyptus `Utility` and OULAD `final_result` are ordinal or outcome-like labels; holding out the smallest class with >=30 rows gives "best" (105) and "Distinction" (3,024, if the recalled counts hold).
- Tables whose label is constant within a group (Anuran, home-activity gas sensors) make a held-out class coincide with held-out groups, so group shift and class novelty cannot be separated; they are unsuitable for the paper's design.
- Room Occupancy and Steel Industry are formally temporal multiclass tables but are weak: in the former three of four classes vanish on 4 of 7 days, in the latter the label follows the clock.

### Gaps
- OULAD row count, class counts and the number of module-presentations were not confirmed on a primary source today (UCI page lists no counts; the Scientific Data paper redirected to a login). The 432.8 MB zip was not downloaded.
- Class counts for HAR70+, MoCap Hand Postures and N-BaIoT are not on the UCI pages and the files were not downloaded (size). The N-BaIoT feature count (115) and the claim that two devices lack Mirai traffic are from memory, unverified.
- Whether the WISDM v1.1 transformed ARFF contains the user attribute was not confirmed (the page lists "46 attributes" without naming them).
- Gas-drift per-batch sizes (445 / 1,244 / 1,586 / 161 / 197 / 2,300 / 3,613 / 294 / 470 / 3,600) are recalled from Vergara et al. 2012 and only their sum (13,910) matches the page; per-batch class coverage not verified.
- Kaggle and DrivenData pages could not be read directly: licences and class counts for the ECG feature table, Pump it Up, and the shelter-outcomes data remain unverified.
- Not examined at all for lack of time: PAMAP2, Daily and Sports Activities, HHAR, Sleep-EDF feature tables, ISOLET, Epileptic Seizure Recognition, Sensorless Drive, CIC-IDS2017, Gaia, Kepler KOI, PetFinder, Costa Rican household poverty. My recollection is that each fails a rule (raw time series, >11 classes, >500 features, no group column, or label fixed per group), but none was checked today.
- Credentialed medical sources (MIMIC, eICU, ADNI/TADPOLE) were not examined; they require data-use agreements.

## Q2. For strong candidates, are the numbers and the group ID confirmed in the released file?

### Takeaway
Group IDs and counts were confirmed from the released file for four tables (batteryless wearable, eucalyptus, Gesture Phase, plus the caveated Anuran / Room Occupancy / Steel); for HAR70+, MoCap, N-BaIoT and gas drift the group structure is confirmed on the UCI page only; for OULAD and WISDM the group column is not confirmed today.

### Cited Findings
- Batteryless wearable: group = file name inside the zip, 87 files, counts as in Q1 — [UCI 427 zip](https://archive.ics.uci.edu/static/public/427/activity+recognition+with+healthy+older+people+using+a+batteryless+wearable+sensor.zip).
- eucalyptus: `Abbrev` (16 values), `Locality` (8 values) and `Year` are columns of the ARFF — [OpenML features 188](https://www.openml.org/api/v1/json/data/features/188).
- Gesture Phase: group = one raw CSV per video (a1, a2, a3, b1, b3, c1, c3), timestamp column present — [UCI 302 zip](https://archive.ics.uci.edu/static/public/302/gesture+phase+segmentation.zip).
- HAR70+: 18 per-subject CSV files listed on the page — [UCI 780](https://archive.ics.uci.edu/dataset/780/har70).
- MoCap: `User` is a documented column — [UCI API 405](https://archive.ics.uci.edu/api/dataset?id=405).
- N-BaIoT: files organised per device — [UCI 442](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot).
- Gas drift: batch = file (`batch1.dat` ... `batch10.dat`) in the UCI release, but lost in the OpenML copy — [UCI 224](https://archive.ics.uci.edu/dataset/224/gas+sensor+array+drift+dataset); [OpenML features 1476](https://www.openml.org/api/v1/json/data/features/1476).
- eye_movements: `assgNo` and `lineNo` are columns of OpenML 1044 — [OpenML features 1044](https://www.openml.org/api/v1/json/data/features/1044).

### Inferences
- For file-as-group tables (HAR70+, batteryless, Gesture Phase, N-BaIoT, gas drift) the loader must add the group column itself; any OpenML mirror drops it.

### Gaps
- Number of distinct `assgNo` values in eye_movements was not counted.
- OULAD and WISDM group columns: see Q1 gaps.

## Q3. Which candidates are in the pretraining data of TabDPT or Real-TabPFN-2.5?

### Takeaway
Gas drift and eye_movements are in both lists; ldpa, road-safety, Diabetes130US, KDDCup99 and walking-activity are in TabDPT only; Richter's Predictor, SDSS DR14/DR16 and Internet Firewall are in Real-TabPFN-2.5 only. None of the eight shortlisted tables appears in either list. Side finding for the paper: two of our nine current tables, cardiotocography (OpenML 1466) and covertype (OpenML 1596), are in TabDPT's training list.

### Cited Findings
- TabDPT Table B.1 (parsed from the arXiv HTML; my parse recovered 120 OpenML entries, the paper speaks of 123) contains: 1044 eye_movements, 1476 gas-drift, 1477 gas-drift-different-concentrations, 1483 ldpa, 1509 walking-activity, 375 JapaneseVowels, 1459 artificial-characters, 1466 cardiotocography, 1596 covertype, 45022 Diabetes130US, 45038 road-safety, 42746 KDDCup99, 42732 sf-police-incidents, 44136 wine_quality, 3050 QSAR-TID-11, 1116 musk, 45026 heloc, 41162 kick — [arXiv 2410.18164, Appendix B](https://arxiv.org/html/2410.18164).
- The same table contains no entry matching eucalyptus, wall-robot-navigation, har, GesturePhaseSegmentation, isolet, Traffic_violations, mice protein, SDSS, or any OULAD / HAR70+ / WISDM / MoCap / N-BaIoT / anuran name — [arXiv 2410.18164, Appendix B](https://arxiv.org/html/2410.18164).
- TabDPT evaluates on CC18 (72 classification datasets) and CTR23 (35 regression datasets), kept apart from the training list — [arXiv 2410.18164](https://arxiv.org/html/2410.18164).
- Real-TabPFN-2.5 Appendix C.1, full list as parsed (43 names). OpenML: artificial-characters, BNG(breast-w), BNG(tic-tac-toe), connect_4, eeg-eye-state, Employee-Turnover-at-TECHCO, eye_movements, FOREX_eurpln-hour-High, gas-drift, higgs, Intersectional-Bias-Assessment-(Training-Data), law-school-admission-binary, Medical-Appointment, microaggregation2, fried, mushroom, NewspaperChurn, nursery, WBCAtt, Internet Firewall Data. Kaggle: aam_avaliacao_dataset, Air Traffic Data, ansible-defects-prediction, AV Healthcare Analytics II, Candidate Selection, Cardio Disease, Classification - Crop Damages in India (2015-2019), CSGO Round Winner Classification, Flower Type Prediction Machine Hack, Horse Racing - Tipster Bets, How severe the accident could be, hr-comma-sep, ip-network-traffic-flows-labeled-with-87-apps, Janatahack cross-sell prediction, L&T Vehicle Loan Default Prediction, League of Legends Diamond Games (First 15 Minutes), Richter's Predictor Modeling Earthquake Damage, Server Logs - Suspicious, Sloan Digital Sky Survey DR14, Sloan Digital Sky Survey DR16, Term Deposit Prediction Data Set, trajectory-based-ship-classification, Travel Insurance — [arXiv 2511.08667, Appendix C.1](https://arxiv.org/html/2511.08667).
- Real-TabPFN-2.5 is described as trained on 43 real-world datasets from OpenML and Kaggle, "deduplicated against all internal benchmarks and the full TabArena suite" — [arXiv 2511.08667](https://arxiv.org/html/2511.08667).

### Inferences
- Eucalyptus, wall-robot-navigation and GesturePhaseSegmentationProcessed are CC18 members (my recollection of the CC18 suite, not re-checked today), which would explain their absence from TabDPT's training list: they are TabDPT evaluation data, not training data.
- SDSS DR14/DR16 in the Real-TabPFN-2.5 list are earlier releases of the same survey as our sdss_17, with the same schema; overlap of objects between releases is plausible and worth a sentence in the paper's contamination discussion.
- The synthetic-prior TabPFN v2 backbone is unaffected by either list; the flags matter only for TabDPT and Real-TabPFN-2.5 as supplementary backbones.

### Gaps
- My regex parse of TabDPT Table B.1 listed 120 names, while the HTML table has 123 rows (three multi-line names not captured). The negative checks were therefore repeated as plain string searches over the whole page text (zero hits for eucalyptus, wall-robot, Gesture, student, OULAD, mice, sdss, WISDM, anuran, botnet, dementia, complaint, potassco), so they do not depend on the parse; a name spelled differently from these strings would still be missed.
- The CC18 membership of eucalyptus / wall-robot / GesturePhase was not re-verified against the OpenML suite today.
- Pretraining corpora of other backbones (TabICL, Mitra, etc.) were out of scope.

## Q4. Which candidates are already inside BeyondArena / TabArena?

### Takeaway
The BeyondArena repository lists 142 task folders; none of the eight shortlisted tables nor any caveated candidate in Q1 is among them. Candidates from the brief that ARE inside BeyondArena, and hence were already screened by our script: diabetes_130_us, heart_disease (cleveland / hungary / va_long_beach as separate tasks), hepatitis_c_prediction, lending_club, otto, student_portuguese_performance, thyroid_discordant.

### Cited Findings
- Folder names in `TabArena/BeyondArena` (142 task folders + 5 repo files) include: diabetes_130_us, heart_disease_cleveland, heart_disease_hungary, heart_disease_va_long_beach, hepatitis_c_prediction, lending_club, otto_group_product_classification_challenge, student_portuguese_performance, thyroid_discordant, telemonitoring_parkinsons_biomedical_voice_measurements, parkinsons_biomedical_voice_measurements, wine_quality, polish_companies_bankruptcy, kick, musk, plus our nine tables — [HF API tree](https://huggingface.co/api/datasets/TabArena/BeyondArena/tree/main).
- No folder name matches OULAD / open_university, gas drift, HAR / activity, WISDM, mocap / hand postures, eucalyptus, N-BaIoT / botnet, gesture phase, eye_movements, ldpa, room occupancy, steel industry, anuran, UNSW, ECG / arrhythmia, pump / water — [HF API tree](https://huggingface.co/api/datasets/TabArena/BeyondArena/tree/main).
- Our screening script reads exactly this repository and applies R1-R4 to every multiclass task — `/mnt/c/Users/zhwu9808/Desktop/pfn/exp/screen_datasets.py` (local file, read-only).

### Inferences
- The shortlisted tables are a genuine extension beyond BeyondArena rather than tasks our rules rejected, so adding any of them would be an "external tables" supplement with its own provenance column, not a change to the screening result.
- The heart-disease sites cannot be recombined into a site-grouped task without stepping outside the benchmark's task definitions; with 4 sites and (recalled, unverified) fewer than 30 rows in the most severe class, it would be weak anyway.

### Gaps
- The name match is on folder names only; a BeyondArena task could contain one of these tables under an unrelated name. I did not open the per-task metadata.
- Why each in-BeyondArena candidate failed our rules (e.g. diabetes_130_us problem type) was not re-derived; `results_screen/screen.csv` has that answer.
