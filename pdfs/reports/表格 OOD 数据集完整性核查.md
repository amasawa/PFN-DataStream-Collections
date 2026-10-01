# 九张表穷尽了 BeyondArena，但未穷尽公开数据

在论文自己划定的范围内，数据集是完整的：BeyondArena 的 25 个多分类任务里只有 8 个带官方 grouped/temporal 划分，论文用了其中 7 个（第 8 个 micro_mass 因 1,082 个特征被 R3 排除），再加两张带实体列的 IID 表，没有任何通过 R1–R4 的任务被遗漏。在这个范围之外，结论不同：调研笔记找到 **Shifts weather（9 类降水，按气候带与时间分组）** 这一张存在于知名 shift benchmark 中的多分类表，以及 **8 张 BeyondArena 之外、同时具备组结构与至少 3 个类别、且不在 TabDPT 与 Real-TabPFN-2.5 预训练清单里的公开表**（OULAD、batteryless wearable、HAR70+、WISDM v1.1、MoCap Hand Postures、eucalyptus、N-BaIoT、Gesture Phase Segmentation）。文献方面没有“漏掉标准 benchmark”的问题，因为表格数据上的 unseen-class OOD 检测根本不存在类似 OpenOOD 的公认 benchmark，每篇 class-holdout 论文都自选 4 到 8 张随机划分的 IID 表。ADBench 不是本文必须报告的套件，它没有组或时间标注，多数数据集只有一个正常类，无法检验“新组 ID 行对 OOD 行”这一论断；但草稿目前既没有一句话与 anomaly detection 文献划界，也没有任何 PFN 原生检测器（TabPFN-OD、FoMo-0D、OutFormer）作基线，后者是最容易被审稿人指出的缺口。建议是：主结论保持“对 BeyondArena 的穷尽筛选”不变，另加一个事先固定、单独标注来源的外部补充表组（首选 OULAD、batteryless wearable、eucalyptus，并对 Shifts weather 给出明确交代），补 5 个左右基线，在 RELATED WORK 与 DATASETS 附录各加两三句话。本报告中凡标“已核实”的内容来自调研者当日读到的原始页面或亲自计数的文件，标“未核实”的数字在写入论文前必须重新计数，标“判断”的是调研者或本报告的评估而非事实。

## 表格 unseen-class OOD 检测没有公认 benchmark，文献各自挑 4 到 8 张 IID 表

**已核实的事实。** 论文方法框架的来源 I-Div（NeurIPS 2024）没有任何表格实验，其 class-holdout 实验用的是 CIFAR10 与 SVHN，全文实验部分不出现 “tabular” 一词（[I-Div](https://proceedings.neurips.cc/paper_files/paper/2024/file/469eb28a0a67dba79f79cbb03f84cd90-Paper-Conference.pdf)）。表格协议只出自 Zhao, Cao & Yu 的 TC 论文（Artificial Intelligence 339, 2025）：**八张表 Stellar、Skyserver、Arrhythmia、Gisette、SHABD、Gene、Wine、Speech，最小类作 OOD，ID 行按 8:2 随机划分，五次重复**，最小的 Gene 为 801 行（[TC](https://doi.org/10.1016/j.artint.2024.104275)，正文读自本地 PDF）。草稿附录中“eight tables, the smallest with 801 rows”的表述与原文一致。

唯一一篇用 tabular foundation model 做 unseen-class 检测的先行工作是 Cheng 等人的 “Realistic Evaluation of TabPFN v2 in Open Environments”：在 **EyeMovement、CMC、Wine-Red、Wine-White 四张小型 IID 表**上做 leave-one-class-out，分数只有 MSP（[arXiv 2505.16226](https://arxiv.org/pdf/2505.16226)）。其余 class-holdout 论文同样各选各的表：Deep-MCDD 用 GasSensor、Shuttle、DriveDiagnosis 与展平的 MNIST，对每个类轮流留出（[arXiv 2104.00941](https://arxiv.org/pdf/2104.00941)）；DNN-GDITD 沿用 Gas Sensor 与 Drive Diagnosis 并加一张合成金融表（[arXiv 2409.00980](https://arxiv.org/html/2409.00980v2)）；probabilistic-circuit 伪度量论文用 Adult、Covertype、Sensorless、Census-KDD、Connect-4（[arXiv 2608.09117](https://arxiv.org/pdf/2608.09117)）；TabularNCD 系列用 Forest Cover Type、Letter、HAR、Satimage、Pendigits、US Census 1990，但任务是对未知类聚类而非检测（[arXiv 2209.01217](https://arxiv.org/pdf/2209.01217)）。自称 “benchmark” 的两篇表格 OOD 检测工作都是医疗 ICU 研究，用 MIMIC 与 eICU 上的子群体或跨库 covariate shift，而不是留出类别（[Ulmer et al.](https://arxiv.org/pdf/2011.03274)；[Azizmalayeri et al.](https://arxiv.org/pdf/2309.16220)）。OpenOOD 的全部 benchmark 都是图像（[OpenOOD v1.5](https://arxiv.org/pdf/2306.09301)）。

知名 shift benchmark 也无法提供留出类别的表。TableShift 的 15 个任务全部为二分类，且“二分类”本身是其入选标准（[TableShift](https://ar5iv.labs.arxiv.org/html/2312.07577)）；TabReD 的 8 个数据集是 3 个二分类加 5 个回归，论文明言不含多分类（[TabReD](https://ar5iv.labs.arxiv.org/html/2406.19380)）；WhyShift 的 5 个数据集与 Folktables 的预定义任务都是二分类（[WhyShift](https://github.com/namkoong-lab/whyshift)；[Folktables](https://github.com/socialfoundations/folktables)）；WILDS 没有特征向量形式的表格任务（[WILDS](https://wilds.stanford.edu/datasets/)）；Wild-Time 的 MIMIC-IV 任务是二分类且需要资质认证（[Wild-Time](https://arxiv.org/pdf/2211.14238)）。**唯一的例外是 Shifts weather：123 个气象特征，9 类降水标签，带时间、经纬度与气候带元数据，规范划分共 4,367,323 行，数据许可为 CC BY NC SA 4.0**（[Shifts 论文](https://ar5iv.labs.arxiv.org/html/2107.07455)；[Shifts 仓库](https://github.com/Shifts-Project/shifts)）。需要说明的是，shift benchmark 这部分数字是经由摘要式抓取工具读到的，调研者没有在 PDF 上复核。

BeyondArena 内部的构成由调研者从 HF 数据集 `TabArena/BeyondArena` 的任务元数据自行统计，不是论文印出的数字：142 个任务中 103 个 IID、21 个 temporal、18 个 grouped；73 个二分类、25 个多分类、44 个回归；多分类且带官方非 IID 划分的只有 8 个，即 asp_potassco、cardiotocography、covertype、dementia_prediction、mice_protein、micro_mass、consumer_complaints、ghanas_indigenous_intel（[HF TabArena/BeyondArena](https://huggingface.co/datasets/TabArena/BeyondArena)）。这与草稿附录 “R1 leaves 25 multiclass tasks … 8 of them have an official non-IID split (6 grouped, 2 temporal)” 完全吻合。

**与我们数据池的重合。** 文献用过的表里，只有 Covertype 在我们的九张表中。BeyondArena 另含 `wine_quality`（作为回归任务）以及 `heloc`、`anes_voting_2026`（均为二分类，不过 R1）。对 BeyondArena 论文全文的字符串搜索中，skyserver、arrhythmia、gisette、eye movements、cmc、pendigits、satimage、census、sensorless、mimic、eicu、unsw、cic-ids、adbench 等均为零命中（[arXiv 2606.30410](https://arxiv.org/pdf/2606.30410)）。

**未核实。** TC 没有给出每张表的 URL。它的 “Stellar”（100,000 行，3 类，Kaggle）很可能就是我们的 `sdss_17` 的来源，但这是根据名称、行数与类别数作出的推断。Skyserver、SHABD、Speech、Wine（1,143 行，6 类）与 Arrhythmia（87,553 行，187 个特征）的确切身份无法确认。Deep-MCDD（KDD 2020）与 TabularNCD（ICDM 2022）的会议归属出自调研者记忆。CIKM 2024 的 “Out-of-Distribution Aware Classification for Tabular Data” 存在，但其数据集清单未能读到。网络入侵检测方向的 open-set 工作（NSL-KDD、UNSW-NB15、CIC-IDS2017 上留出攻击类别）只有搜索摘要级别的证据。上述 BeyondArena 非成员判断基于论文文本与文件夹名的字符串匹配，改名收录的情形会被漏掉。

**判断。** 不存在被我们遗漏的“标准” benchmark，这一否定结论来自约十次定向搜索加上 2025–2026 年几篇论文的 related work，不是证明，但把握较大：读到的每篇 class-holdout 论文都自建数据池，没有一篇引用共享的数据池。文献中被重复使用的表只有 Gas Sensor 与 Sensorless Drive Diagnosis（各两到三篇）、Covertype（三篇）、Wine Quality（两篇），其余都只出现一次。没有任何一篇 class-holdout 论文使用 grouped 或 temporal 划分，因此“留出类别加新组部署”这一组合在已调研的文献中是新的；这是论文的卖点，同时意味着这个设定没有可继承的数据池。审稿人仍可能提两点要求：补上 Cheng 等人的四张表，或把“固定留出一个类”改成对所有类轮流留出。后者在现有九张表上就能做，成本低于加数据集。

## BeyondArena 之外有八张干净的候选表，两张最“显然”的候选已被预训练污染

下表汇总调研笔记中的候选表。筛选沿用 `exp/screen_datasets.py` 的 R1–R4。预训练一栏的依据是 TabDPT 附录 B 的 OpenML 训练清单（[arXiv 2410.18164](https://arxiv.org/html/2410.18164)）与 Real-TabPFN-2.5 附录 C.1 的 43 个真实数据集清单（[arXiv 2511.08667](https://arxiv.org/html/2511.08667)）。八张干净候选的名称在两份清单中均无命中；TabDPT 清单的否定检查是对整页文本做字符串搜索，拼写不同的名称仍可能被漏掉。BeyondArena 的 142 个文件夹名中也没有与这些候选匹配的条目（[HF API](https://huggingface.co/api/datasets/TabArena/BeyondArena/tree/main)）。

| 表 | 来源与许可 | 规模（行 / 特征） | 组列与组数 | 类别 | TabDPT / Real-TabPFN-2.5 预训练 | 核实状态 |
|---|---|---|---|---|---|---|
| OULAD `studentInfo` | [UCI 349](https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset)，CC BY 4.0 | 32,593 / 约 9 个人口学特征 | `code_module` × `code_presentation`，22 个 | 4：Pass 12,361、Withdrawn 10,156、Fail 7,052、Distinction 3,024 | 否 / 否 | 许可与 7 个课程模块已核实；**行数、类别计数、22 个组均出自记忆，未核实** |
| Batteryless wearable activity | [UCI 427](https://archive.ics.uci.edu/dataset/427/activity+recognition+with+healthy+older+people+using+a+batteryless+wearable+sensor)，CC BY 4.0 | 75,128 / 8 | 试验文件（文件名含参与者编号），87 个 | 4：lying 51,520、sit on bed 16,406、sit on chair 4,911、ambulating 2,291 | 否 / 否 | **全部由下载文件计数核实**；页面摘要称 91 个文件，压缩包内为 87 个 |
| eucalyptus | [OpenML 188](https://www.openml.org/api/v1/json/data/qualities/188)，“Public” | 736 / 19 | `Abbrev`（试验点），16 个 | 5：good 214、none 180、average 130、low 107、best 105 | 否 / 否 | **文件计数核实**；两个试验点只含一个类 |
| HAR70+ | [UCI 780](https://archive.ics.uci.edu/dataset/780/har70)，CC BY 4.0 | 2,259,597 / 6 加时间戳 | 每位受试者一个 CSV，18 个 | 7 种活动 | 否 / 否 | 页面核实；类别计数不在页面上 |
| WISDM v1.1（transformed） | [WISDM lab](https://www.cis.fordham.edu/wisdm/dataset.php)，无正式许可，要求引用 | 5,424 / 43 | user，36 个 | 6：最小类 Standing 247 | 否 / 否 | 页面核实；**transformed ARFF 是否含 user 列未核实** |
| MoCap Hand Postures | [UCI 405](https://archive.ics.uci.edu/dataset/405/motion+capture+hand+postures)，CC BY 4.0 | 78,095 / 36 | `User`，12 个 | 5 种手势 | 否 / 否 | 页面核实；类别计数未核实；大量缺失标记点 |
| N-BaIoT | [UCI 442](https://archive.ics.uci.edu/dataset/442/detection+of+iot+botnet+attacks+n+baiot)，CC BY 4.0 | 7,062,606 / 115 | 设备，9 个 | 11：benign 加 10 种攻击 | 否 / 否 | 页面核实；**特征数 115 未核实** |
| Gesture Phase Segmentation | [UCI 302](https://archive.ics.uci.edu/static/public/302/gesture+phase+segmentation.zip)，CC BY 4.0（UCI 默认，当日未重读） | 9,901 / 18 加时间戳 | 视频文件，7 个（3 位用户） | 5：最小类 Hold 998 | 否 / 否 | 文件计数核实 |
| Shifts weather（precipitation） | [Shifts 仓库](https://github.com/Shifts-Project/shifts)，CC BY NC SA 4.0 | 4,367,323（规范划分）/ 123 | 气候带 5 类，另有时间 | 9 | 两份清单均未针对性检查 | 经摘要工具读取；**各类行数未知，R4 未核实** |
| Gas Sensor Array Drift | [UCI 224](https://archive.ics.uci.edu/dataset/224/gas+sensor+array+drift+dataset)，CC BY 4.0 | 13,910 / 128 | 批次文件，10 个，跨 36 个月 | 6：最小类 1,641 | **是 / 是** | 页面核实；OpenML 副本丢失批次列；各批次行数未核实 |
| eye_movements | [OpenML 1044](https://www.openml.org/api/v1/json/data/features/1044) | 10,936 / 27 | `assgNo`（组数未计数） | 3：最小类 2,870 | **是 / 是** | API 核实 |
| ldpa | [UCI 196](https://archive.ics.uci.edu/api/dataset?id=196) | 164,860 / 7 | 25 个序列，5 人 | 11：最小类 1,381 | **是** / 否 | API 核实 |

**已核实的附带事实。** 我们现有九张表中的 cardiotocography（OpenML 1466）与 covertype（OpenML 1596）在 TabDPT 的训练清单里；Real-TabPFN-2.5 的清单里有 SDSS DR14 与 DR16，即 `sdss_17` 同一巡天的早期发布（[TabDPT 附录 B](https://arxiv.org/html/2410.18164)；[Real-TabPFN-2.5 附录 C.1](https://arxiv.org/html/2511.08667)）。草稿 Pretraining data 一段已如实写明这三处暴露，并给出了 synthetic-only checkpoint 与 GOR$_6$ 两个对照，这部分无需改动。

**不适合的表及原因。** HAR Using Smartphones 有 561 个特征，UJIIndoorLoc 有 520 个，均超过 R3 的 500 上限（[OpenML 1478](https://www.openml.org/api/v1/json/data/qualities/1478)；[UCI 310](https://archive.ics.uci.edu/api/dataset?id=310)）。Anuran Calls 有 60 个录音组，但调研者对文件的计数显示每个录音恰好只含一个 Family、Genus 与 Species，留出类别就等于留出组，组偏移与类别新颖性无法分离（[UCI 406](https://archive.ics.uci.edu/static/public/406/anuran+calls+mfccs.zip)）；home-activity gas sensors 同理。Room Occupancy Estimation 的非零类别只出现在 7 天中的 3 天，Steel Industry 的标签跟随时钟排班，二者形式上是 temporal 多分类表，实质很弱（[UCI 864](https://archive.ics.uci.edu/static/public/864/room+occupancy+estimation.zip)；[UCI 851](https://archive.ics.uci.edu/static/public/851/steel+industry+energy+consumption.zip)）。Wall-Following Robot 没有任何 ID 或时间戳列。UNSW-NB15 仅限学术研究使用（[UNSW](https://research.unsw.edu.au/projects/unsw-nb15-dataset)）。walking-activity 的类别就是人本身，且在 TabDPT 预训练中。Richter's Predictor、SDSS DR14/DR16、Internet Firewall 在 Real-TabPFN-2.5 清单中；road-safety、KDDCup99、sf-police-incidents、Diabetes130US 在 TabDPT 清单中。Diabetes 130-US、Heart Disease 各站点、Hepatitis C、Lending Club、Otto、Student Performance 已在 BeyondArena 内，已被我们的脚本筛过。HARTH、MHEALTH 被记为 12 类超限，但这个类别数出自记忆。MIMIC、eICU 等需要数据使用协议，且标签为二分类。PAMAP2、HHAR、CIC-IDS2017、Sensorless Drive 等十余张表当日完全没有检查。Kaggle 与 DrivenData 页面无法直接读取，ECG arrhythmia 特征表、Pump it Up、Austin 动物收容所数据的许可与类别计数均未核实。

**判断。** 排序的理由如下。OULAD 与现有的 `students` 同属教育领域，实体是课程期次，四个类都很大，是最自然的补充，但它的全部关键数字都未核实，必须先下载 `studentInfo.csv`（3.3 MB）重新计数。Batteryless wearable 是唯一每个数字都从文件核实过的表，87 个组中 65 个含全部四类。eucalyptus 规模小、能直接放进 TabPFN context，提供一个农学领域的站点分组；调研者回忆它属于 OpenML-CC18（TabDPT 的评测集而非训练集），这一点未重新核对。HAR70+、MoCap、Gesture Phase 与 batteryless wearable 都是每个时间采样一行，组内行强自相关，有效样本量远小于行数；HAR70+ 与 N-BaIoT 还必须下采样。N-BaIoT（9 个设备）与 Gesture Phase（7 个视频）的组数偏少，但多于现有 covertype 的 3 个区域，与论文自身的先例一致。以文件为组的表需要加载器自行补上组列，任何 OpenML 镜像都会丢掉它。

Gas Sensor Array Drift 值得单独说明。它是文献中复用最多的 class-holdout 表，也是文献表中唯一自带真实时间批次结构的一张，从“与文献对齐”的角度价值最高。但它同时在两份预训练清单中。论文的主 backbone 是合成先验的 TabPFN v2，不受影响；而现有的 cardiotocography 与 covertype 已经在 TabDPT 清单里，所以“被预训练见过”在本文中并不是一致的排除理由。本报告的判断是不把它放进主补充组：一旦加入，草稿中 “none of our tables is among them”（针对 Real-TabPFN-2.5）这句话就不再成立，暴露对照也要重做，代价高于收益。若审稿人点名要求，可以在 v2 及 synthetic-only backbone 上补跑并注明暴露。

## ADBench 检验不了本文的论断，但 PFN 原生检测器是明显的基线缺口

**已核实的事实。** ADBench 评测 30 种算法、57 个数据集，其中 47 个是既有表格数据集，10 个是由 CV 与 NLP 数据经 ResNet18 或 BERT 嵌入转成的表；划分是分层随机的 70/30，重复三次；论文明确把时间序列与图结构排除在范围之外（[ADBench](https://ar5iv.labs.arxiv.org/html/2206.09426)）。47 张表的规模从 80 行到 619,326 行，异常比例从 0.03% 到 39.91%，以裸 `X, y` 数组发布，没有组 ID 或时间戳（[ADBench README](https://github.com/Minqi824/ADBench)）。我们的九张表中只有两张在 ADBench 里有对应：cardiotocography 对应 `cardio`（1,831 行，176 个异常）与 `Cardiotocography`（2,114 行，466 个异常），covertype 对应 `cover`（286,048 行，10 个特征，2,747 个异常）；其余七张逐一比对后没有对应项。

后继套件沿用同样的做法并扩大规模。MacrOData 由 OddBench（790 个）、OvRBench（856 个，one-vs-rest：多数类作 inlier，其余类按 5% 到 20% 的比例下采样作异常）与 SynBench（800 个合成）组成，共 2,446 个数据集，训练只用 inlier；它批评 ADBench 数据集太少、存在近重复（Cardio 与 Cardiotocography，Satellite 与 Satimage-2）、部分已饱和，并称 one-vs-rest 是 OOD 检测的 “proxy”（[MacrOData](https://arxiv.org/html/2602.09329)）。OutFormer 的论文称 ADBench 为 “the de facto OD benchmark”，但给出的 OddBench 与 OvRBench 规模是 690 与 756，与 MacrOData 的 790 与 856 不一致，两处来源的冲突未解决（[OutFormer](https://arxiv.org/html/2602.03018)）。

所有已找到的 tabular foundation model 检测论文都在 ADBench 或其后继上、以无标签的 one-class 或 unsupervised 协议评测：FoMo-0D 在 57 个数据集上对比 26 个基线（[FoMo-0D](https://arxiv.org/html/2409.05672v4)）；OutFormer 的基线包括 FoMo-0D、TabPFN-OD、kNN、LOF、IForest、DeepSVDD、DDPM、GOAD、ICL、DTE-NP、DTE-C，其中 TabPFN-OD 是把每个特征轮流当预测目标并平均预测误差（[OutFormer](https://arxiv.org/html/2602.03018)）；MacrOData 报告 foundation model 显著优于除 EGMM 之外的所有经典与深度方法（[MacrOData](https://arxiv.org/html/2602.09329)）。反过来，已核实的、带分类器的表格 OOD 论文都不报告 ADBench：Deep-MCDD 在自己的 class-holdout 协议里纳入 Deep-SVDD 与 ALAD 作基线，报告 ID 准确率、AUROC 与 AUPR（[Deep-MCDD](https://ar5iv.labs.arxiv.org/html/2104.00941)）；医疗 benchmark 在训练好的预测器上跑 17 个 post-hoc 检测器外加 10 个密度方法（[Azizmalayeri et al.](https://arxiv.org/abs/2309.16220v1)）。

两个任务的概念区分有标准出处。Yang 等人的综述写道，AD 把 ID 样本视为一个整体，不要求区分 ID 内部的类别；open set recognition 要求多分类器同时对已知类准确分类并检测未知类，其 benchmark 通常把一个多分类数据集按类别拆成 ID 与 OOD 两部分；OOD 检测不应损害 ID 分类能力（[Yang et al.](https://arxiv.org/html/2110.11334v2)）。

草稿的现状读自本地 `main.tex`：基线为 MSP、kNN（含调参版 kNN†）、Emb-kNN、Mahalanobis、IForest；adapter 的十个输入是 MSP、归一化熵、Margin、到预测类最近 context 行的距离、原始空间 1/10/50 近邻距离、嵌入空间 10 近邻距离、Mahalanobis 距离与 isolation 分数。调研笔记把“十个输入中是否已含 energy”列为未查项，本报告对照草稿的特征定义确认：**不含 energy 或 max-logit**，熵与 Margin 在其中但没有作为独立基线行报告。RELATED WORK 没有引用任何表格 AD benchmark，也没有引用区分 AD 与 OOD 的综述。

**未核实。** ODDS 站点当日无法访问，`cardio` 与 `cover` 的具体构造（哪一类作异常、哪一类被丢弃）没有从原始来源确认；“ADBench 的 `cardio` 等于去掉 suspect 类后的二分类问题”是由行数关系（1,831 加上 suspect 类恰为 2,126，176 个异常与我们的 pathologic 类行数相同）推出的。DTE、MCM、DRL、AnoLLM、ReTabAD、uLEAD-TabPFN 与 Prior Labs 的无监督扩展只有搜索摘要级别的信息。没有读过任何 OpenReview 评审，因此“审稿人会不会要求 ADBench”没有直接证据。没有找到任何用 TabICL 或 TabDPT 做 outlier 或 OOD 检测的论文，但也没有专门搜索。FoMo-0D 与 OutFormer 的 checkpoint 许可及输入维度上限没有对照我们的表检查（asp 有 136 个特征，mice 有 76 个）；GOR 能否在单一 ID 类的数据集上运行也没有在代码中验证。

**判断。** 不报告 ADBench 的理由有四条。其一，零分布不对：本文的论断是“新组的 ID 行对 OOD 行”，ADBench 没有组且随机划分，familiar 参照与 group-out 参照在那里重合，结果既不支持也不反驳理论。其二，监督形式不对：多数 ADBench 数据集是一个正常类加异常，只有一个 ID 类时没有分类器，MSP 无定义，伪任务构造也无从下手。其三，污染设定不同：ADBench 的 unsupervised 设定把异常混入训练集，而我们的 context 是干净的 ID 行。其四，AD 领域自己也认为 ADBench 偏小、重复、饱和。支持报告的理由是识别度：有 AD 背景的审稿人会拿“九张表、终测八张”去比 57 或 2,446；而且 OvRBench 与 ADBench 的 CV/NLP 部分同样是“指定某些类为异常”，审稿人可以合理地说 OOD 行的产生方式相同，论文必须用监督形式与参照分布来回答，而不能只说领域不同。综合来看，风险为中等：AISTATS 审稿人多偏理论，已核实的表格 OOD 先例都不用 AD 套件；但先例很薄（KDD 2020、一本医学信息学期刊、AIJ），没有找到任何 NeurIPS、ICML、ICLR 或 AISTATS 上的表格 class-holdout OOD 论文可作正反两方面的直接先例。

缺失基线按被问到的可能性排序如下。第一是 TabPFN-OD 或 Prior Labs 的 unsupervised TabPFN，以及 FoMo-0D 或 OutFormer：一篇研究 in-context 表格模型 OOD 检测的论文不比较现有的 in-context 检测器是明显的漏洞，而它们只需要 ID 行，可以直接在我们的协议下运行。第二是 energy 与 max-logit，它们是 MSP 的默认同伴，有 PFN 的 logits 就能零成本算出；熵与 Margin 已经算出来了，也应列为独立行。第三是 LOF、OCSVM，以及无参数的 ECOD 或 COPOD，都在 PyOD 里，出现在上述每一份 AD 对比中。第四是一个深度 one-class 方法，DTE-NP 非参数且便宜，Deep SVDD 是 Deep-MCDD 与 TC 都用过的。ODIN、ViM、ReAct 一类需要梯度或可训练网络的倒数第二层特征，对冻结的 in-context 模型不适用，写明这一点即可。现有的 kNN 与 IForest 在这些套件里一贯属于最强的经典方法，所以目前的基线集并不弱，问题在于覆盖面窄。

## 建议：主结论不动，加一个事先固定的外部补充组和三处文字交代

以下全部是本报告的判断。

**数据集。** 保持“对 BeyondArena 142 个任务的穷尽筛选”作为主实验的唯一选择规则，这是相对所有先例最强的论据：先例都是 4 到 8 张自选 IID 表，我们是对一个不按检测器性能挑选的 curated 池做了规则化的全量筛选。外部表以单独的补充表格出现，自带来源列，选择规则与留出类别在看到任何结果之前写死，并明说它们不是 BeyondArena 的任务。推荐的最小补充组是三张：**OULAD**（先核实行数、四类计数与 22 个组）、**batteryless wearable**（数字已全部核实）、**eucalyptus**（数字已核实，注意两个单类站点）。它们全部通过 R1–R4，许可为 CC BY 4.0 或 Public，不在任一预训练清单中，能把终测表数从 8 提到 11，同时补上“老年人传感器”与“农学站点”两个现有九张表没有的领域。若还要加强“受试者分组的传感器”这一族，再从 MoCap Hand Postures、HAR70+、WISDM v1.1 中取一到两张，其中 WISDM 需先确认 user 列存在且接受其没有正式许可；N-BaIoT 与 Gesture Phase 作为备选。

**Shifts weather 必须有明确交代。** 它是全部已调研 shift benchmark 中唯一带真实组与时间结构的多分类表，知道 Shifts 的审稿人会直接点名。现有规则没有一条能干净地排除它：非商用许可不成立（`dementia_prediction` 已是 CC BY NC），组数少不成立（5 个气候带多于 covertype 的 3 个），规模大也不成立（`consumer_complaints` 已有 120 万行）。诚实的说法只有一个：它不在 BeyondArena 的 21 个来源之内，因此不在筛选所定义的范围里。两个干净的选项是把它加为补充表（先下载规范划分并核实各类行数是否满足 R4），或在附录里用一句话说明范围限制。本报告倾向前者，前提是 R4 核实通过；它的降水类别由降水类型与云量组合而成，留出类与邻近类语义很近，结果预期偏难，这一点应在文中说明而不是回避。

**不建议加入的。** Gas Sensor Array Drift 与 eye_movements（两份预训练清单都有）、ldpa（TabDPT 清单中，且 11 类已到上限）、ADBench 与 OvRBench 的任何数据集（无组结构，多为单一 ID 类）、TC 的八张表与 Cheng 等人的四张表（均为 IID 随机划分，无法构造新组参照；项目里的 `exp/ood_lostclues.py` 已在 BeyondArena 的八张表上复现了 TC 协议，可作为与该协议的衔接）、MIMIC 与 eICU（需资质认证，二分类）、Anuran 一类标签在组内恒定的表。

**基线。** 在现有协议下补 TabPFN-OD（或 unsupervised TabPFN）、FoMo-0D 或 OutFormer（先查 checkpoint 许可与维度上限）、energy、LOF，以及 OCSVM、ECOD、DTE-NP 中的一个；把熵与 Margin 列为独立行。不在正文报告 ADBench 数字。

**可选的对照实验。** 在没有组结构的表上，理论预测不存在 familiarity gap，GOR 应与调参后的 kNN 大致持平而不是更好。在 BeyondArena 的 17 个 IID 多分类任务上用随机划分验证这一预测，比跑 ADBench 更站得住，因为这些任务保留了类别标签，而且它检验的是理论的一个预测而非追逐 benchmark。

**论文中应写明的内容。** 第一，在 RELATED WORK 或 DATASETS 附录加两三句，大意如下：

> To our knowledge there is no established benchmark for unseen-class OOD detection on tabular data. Prior work evaluates on four to eight self-selected tables with a random split (Zhao et al., 2025; Lee et al., 2020; Cheng et al., 2025). Anomaly-detection suites such as ADBench and its successors target label-free one-class detection with random splits and carry no entity or time annotation; most of their datasets have a single normal class, so they define neither an ID classifier nor a new-group reference (Yang et al., 2024). Two of our tables have ADBench counterparts (cardio, cover); these are re-sampled binary tasks without patient or area identifiers, and the numbers are not comparable.

第二，在 Task suitability 一段把目前只针对 TableShift 的说明扩展为：TableShift、TabReD、WhyShift 与 Folktables 只含二分类或回归任务，WILDS 没有表格任务，Wild-Time 的 MIMIC 任务是二分类；Shifts weather 是我们所知唯一的多分类 shifted 表，并说明它被纳入补充组或因在筛选范围之外而未纳入。第三，把 “No table that passes the rules is left out” 的范围限定为 BeyondArena，并把外部表描述为独立于筛选的补充。第四，在 LIMITATIONS 加一句：不使用 ID 标签的 one-class anomaly detection 不在本文范围内；留出类别是固定的最小类而非对所有类轮流留出（若不补 leave-one-class-out 实验）。第五，新增表逐一写入 Pretraining data 段的暴露说明，目前的补充候选均为“不在两份清单中”，但 Shifts weather 需先对两份清单做一次针对性检查。

**写入论文前必须重新核实的数字。** OULAD 的行数、类别计数与组数；HAR70+、MoCap、N-BaIoT 的类别计数与 N-BaIoT 的特征数；WISDM transformed 文件中的 user 列；Shifts 降水各类行数；eucalyptus 的 CC18 成员身份；BeyondArena 各类任务的计数应引为“据元数据统计”或对照其论文图表；候选表不在 BeyondArena 中这一点应对照 `data/` 下的任务元数据而非仅凭文件夹名；TC 的 Stellar 与 `sdss_17` 是否同源，在未确认前不要写进论文。

## Conclusion

这次核查改变的不是“九张表够不够”的答案，而是这个问题该如何表述。论文的数据选择在它声明的范围内无懈可击，弱点在于范围本身没有被说清楚：读者看不到为什么范围是 BeyondArena，看不到范围之外唯一的同类表（Shifts weather）被如何处置，也看不到与规模大两个数量级的 anomaly detection 套件的关系。这三处都可以用文字解决，而且比多加几张表更能消除“表太少”的印象，因为审稿人质疑的通常是选择是否任意，而不是数量本身。

数据集之外的发现同样重要。文献里没有任何 class-holdout 工作用过 grouped 或 temporal 划分，也没有任何工作用 TabICL 或 TabDPT 做过 OOD 检测，这两点在已调研范围内都是本文的首次；但与之相邻的 PFN 检测器文献（FoMo-0D、OutFormer、TabPFN-OD）在 2025–2026 年发展很快，全部建立在无标签协议上。把它们作为基线引入我们的协议，既补上最可能被指出的缺口，也让本文的论点更清楚：在有组结构的部署场景里，问题不在于检测器是否由 foundation model 驱动，而在于它参照的是哪一个零分布。
