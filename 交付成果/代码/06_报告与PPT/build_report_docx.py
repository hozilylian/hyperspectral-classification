# -*- coding: utf-8 -*-
"""生成实验报告 .docx（含图、表、中文排版）"""
import os
from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = r'C:\Users\ASUS\Desktop\遥感数据'
RES = os.path.join(BASE, '高光谱反射率数据', '结果')


def set_font(run, east='宋体', latin='Times New Roman', size=10.5, bold=False, color=None):
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:eastAsia'), east)


def body(doc, text, size=10.5, bold=False, align=None, east='宋体'):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_font(r, east=east, size=size, bold=bold)
    if align is not None:
        p.alignment = align
    return p


def heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        set_font(r, east='黑体', size={1: 14, 2: 12, 3: 11}.get(level, 11), bold=True)
    return p


def caption(doc, text):
    p = body(doc, text, size=9, align=WD_ALIGN_PARAGRAPH.CENTER, east='楷体')
    return p


def add_fig(doc, fname, width_in, cap):
    path = os.path.join(RES, fname)
    if os.path.exists(path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Inches(width_in))
        caption(doc, cap)
    else:
        body(doc, '[缺图: %s]' % fname)


def make_table(doc, rows, header_bold=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = 'Table Grid'
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ''
            r = cell.paragraphs[0].add_run(str(val))
            set_font(r, size=9.5, bold=(header_bold and i == 0))
    return t


doc = Document()

# ---- 标题 ----
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('基于非监督-监督联合学习的高光谱校园地物精细分类')
set_font(r, east='黑体', size=18, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run('——以珠海校区无人机高光谱影像为例')
set_font(r, east='黑体', size=14, bold=True)

# ---- 摘要 ----
heading(doc, '摘要', 1)
body(doc, '本文以珠海校区无人机高光谱影像为研究对象，开展校园地物的精细分类研究。数据由大疆 M300 RTK 搭载 '
          'Nano-Hyperspec 高光谱成像仪获取，覆盖 400–1000 nm 共 272 个波段，空间分辨率约 0.37 m，并配有地面光谱仪实测光谱作为真值。'
          '研究采用"非监督-监督联合"的两阶段策略：首先利用 MiniBatch K-Means 聚类在无标注条件下探索数据可分性，'
          '依据 SSE 肘部准则与 Calinski-Harabasz 指数确定最优聚类数 K=5，对应水体/阴影、草地、树木、建筑、道路五类地物；'
          '随后构建标注样本，对比支持向量机（SVM）、随机森林（RF）与多层感知机（MLP）三种监督分类模型。'
          '实验结果表明，随机森林在条带内总体精度达 80.6%（Kappa 0.758），优于 MLP（79.1%）与 SVM（76.4%）；'
          '跨条带验证精度约 70%，反映了真实泛化能力。进一步利用地面实测光谱做光谱角（SAM）验证，树木类获得强吻合；'
          '波段重要性分析表明近红外与蓝波段是分类的关键光谱区间。本文完成了从非监督探索到监督分类、再到多层验证的完整闭环，'
          '为校园尺度高光谱地物精细识别提供了可行方案。')
body(doc, '关键词：高光谱遥感；地物分类；随机森林；支持向量机；多层感知机；光谱角验证', bold=True)

# ---- 1 研究目的 ----
heading(doc, '1 研究目的与任务说明', 1)
body(doc, '无人机高光谱遥感兼具高空间分辨率与高光谱分辨率，能在精细地物识别中发挥显著优势。校园场景地物类型多样、'
          '空间结构复杂，既包含草地、树木等植被，也包含道路、建筑等人工地物，是验证高光谱智能解译方法的典型对象。'
          '然而高光谱数据维度高、信息冗余大，直接分类面临挑战。')
body(doc, '针对上述问题，本文设计两个递进式任务：任务一在无人工标注条件下，采用非监督聚类探索校园地物在高光谱特征空间中的可分性，'
          '并据此确定类别方案；任务二在此基础上构建标注样本，引入监督分类模型（SVM、RF、MLP）开展精细分类，'
          '并通过随机/空间/跨条带划分以及地面真值光谱角验证等多层手段检验分类可靠性。')

# ---- 2 数据 ----
heading(doc, '2 数据来源与预处理', 1)
heading(doc, '2.1 数据来源', 2)
body(doc, '研究数据为珠海校区无人机平台获取的高光谱遥感影像。飞行平台为大疆 M300 RTK，搭载 Headwall Nano-Hyperspec '
          '高光谱成像仪（光谱范围 400–1000 nm，270 个通道），飞行高度 400 m，地面空间分辨率约 0.37 m。'
          '影像以 ENVI 标准格式存储，已完成辐射定标（转为反射率）与正射校正。研究区覆盖体育场、道路、建筑、湖泊及植被等多种地物。'
          '此外，配套有地面光谱仪实测光谱数据（含对应照片），作为分类结果验证的"真值"。')
heading(doc, '2.2 数据预处理', 2)
body(doc, '预处理包括四步：（1）波段选择，剔除 400–450 nm 与 950–1000 nm 两端信噪比低的波段，保留 450–950 nm 共 225 个波段；'
          '（2）无效像元剔除，将全波段为 0 或近 0 的无数据边缘像元排除；（3）波段标准化（Z-score），使各波段量纲一致；'
          '（4）主成分分析（PCA）降维，在保留 99% 方差的前提下将 225 维光谱压缩至 3~4 个主成分，去除相邻波段间的高度冗余。')

# ---- 3 任务一 ----
heading(doc, '3 任务一：非监督聚类探索', 1)
heading(doc, '3.1 聚类数 K 的选取', 2)
body(doc, '采用 MiniBatch K-Means 算法对像元光谱进行聚类。为确定类别数，在 K=5~20 范围内开展预实验，'
          '分别计算类内平方误差（SSE）与 Calinski-Harabasz（CH）指数。SSE 衡量类内紧凑度，随 K 增大而下降；'
          'CH 指数综合类内紧凑度与类间分离度，值越大越好。实验结果表明 CH 指数在 K=5 处取得最大值，'
          '据此选取 K=5 作为最优聚类数。')
add_fig(doc, 'K选择_raw_10096.png', 6.0, '图 1 聚类数 K 的选取（SSE 肘部曲线与 CH 指数）')

heading(doc, '3.2 聚类结果与光谱分析', 2)
body(doc, 'K=5 的聚类结果显示，五类在空间上具有较好的连续性与区域一致性。对各簇平均光谱分析可知：'
          '两簇植被类别具有"红波段吸收、近红外高反射"的典型植被光谱特征，但近红外反射率与 NDVI 存在差异，'
          '分别对应草地与树木；其余三簇分别对应水体/阴影（整体反射率低）、建筑（高反射率）与道路（中等反射率）。'
          '上述结果表明非监督聚类能有效挖掘高光谱数据的可分性，为任务二确定类别方案提供了依据。')
add_fig(doc, '聚类图_raw_10096.png', 4.5, '图 2 K=5 非监督聚类结果')
add_fig(doc, '聚类平均光谱_raw_10096.png', 6.0, '图 3 各聚类簇平均光谱曲线')

# ---- 4 任务二 ----
heading(doc, '4 任务二：监督精细分类', 1)
heading(doc, '4.1 数据集制作', 2)
body(doc, '依据任务一定类结果，确定五类地物：水体/阴影、草地、树木、建筑、道路。采用 labelme 对假彩色影像进行多边形标注。'
          '以 raw_7216 条带作为训练条带（51 个多边形），raw_10096 与 raw_5232 作为有标注的测试条带（分别 71、41 个多边形），'
          'raw_1200 与 raw_3088 用于无标注的定性应用。训练集共提取 518,385 个像素，'
          '经样本均衡（每类最多 2000）后得到 10,000 个训练样本，保证五类平权。')

heading(doc, '4.2 分类模型', 2)
body(doc, '对比三种监督分类模型：支持向量机（SVM，RBF 核，C=10，gamma=scale）、'
          '随机森林（RF，300 棵决策树）与多层感知机（MLP，两层全连接 128→64，ReLU 激活，Adam 优化，early stopping）。'
          '三者均以标准化+PCA 后的特征为输入，采用 70% 训练、30% 测试的随机划分评估精度。')

heading(doc, '4.3 分类结果对比', 2)
make_table(doc, [
    ['模型', '总体精度 OA', 'Kappa'],
    ['随机森林 RF', '80.6%', '0.758'],
    ['多层感知机 MLP', '79.1%', '0.739'],
    ['支持向量机 SVM', '76.4%', '0.705'],
])
caption(doc, '表 1 三种模型在训练条带(raw_7216)上的分类精度')
body(doc, '结果表明，随机森林精度最高，MLP 次之，SVM 最低。随机森林凭借集成学习与两处随机机制对高光谱波段冗余和噪声具有更强的鲁棒性，'
          '因而在高光谱逐像素分类任务上表现最优。')
add_fig(doc, 'classification_map_raw_7216.png', 4.5, '图 4 raw_7216 监督分类结果图')
add_fig(doc, 'class_mean_spectra_raw_7216.png', 6.0, '图 5 各类平均光谱曲线')

# ---- 5 验证 ----
heading(doc, '5 精度验证', 1)
heading(doc, '5.1 随机划分与空间划分', 2)
body(doc, '为检验模型是否存在空间自相关导致的精度虚高，分别进行随机划分与空间划分评估。随机划分将标注像素随机分为 70% 训练、30% 测试；'
          '空间划分按列将影像左侧 70% 作为训练、右侧 30% 作为测试。结果表明，随机划分 OA 80.6%，空间划分 OA 80.4%，两者接近，'
          '说明模型在条带内空间泛化良好，未出现明显的空间泄漏问题。')

heading(doc, '5.2 跨条带验证', 2)
body(doc, '以 raw_7216 训练模型，应用到有标注的 raw_10096 与 raw_5232 条带进行独立验证。')
make_table(doc, [
    ['测试条带', '总体精度 OA', 'Kappa', '说明'],
    ['raw_10096', '69.2%', '0.592', '有标注'],
    ['raw_5232', '71.4%', '0.572', '有标注'],
])
caption(doc, '表 2 跨条带验证精度')
body(doc, '跨条带精度较条带内下降约 10 个百分点，反映了不同航线光照与大气条件差异带来的真实泛化差距，'
          '这也是比随机划分精度更具说服力的泛化指标。')
add_fig(doc, 'cross_raw_7216_to_raw_10096.png', 4.5, '图 6 跨条带预测结果(raw_10096)')
add_fig(doc, 'cross_raw_7216_to_raw_5232.png', 4.5, '图 7 跨条带预测结果(raw_5232)')

# ---- 6 SAM ----
heading(doc, '6 地面真值光谱角(SAM)验证', 1)
body(doc, '利用地面光谱仪实测的 16 个地面点光谱作为真值，与影像中同类地物的平均光谱计算光谱角（SAM）。'
          '光谱角越小，说明两者光谱形态越接近。')
make_table(doc, [
    ['类别', '地面点数', '吻合情况', 'SAM 角度'],
    ['树木', '5', '5/5', '5.8°–9.6°'],
    ['建筑', '3', '2/3', '2.3°–16.1°'],
    ['草地', '5', '0/5', '更接近"树木"'],
    ['道路', '3', '0/3', '材质差异大'],
])
caption(doc, '表 3 地面实测光谱与影像同类光谱的 SAM 验证结果')
body(doc, '结果表明：树木类获得地面真值的强验证，5 个实测点全部与影像树木类吻合，平均光谱角仅约 7.6°；'
          '草地类地面光谱反而更接近影像的"树木"类，这与分类混淆矩阵中草地与树木大量混淆的现象相互印证，'
          '说明在 0.37 m 高光谱下草地与树木光谱本身高度相似；人工地物因材质多样（水泥、沥青、瓦片等），单一地面点代表性有限。')
add_fig(doc, 'SAM_验证_raw_7216.png', 6.2, '图 8 地面实测光谱与影像类平均光谱比对')

# ---- 7 波段重要性 ----
heading(doc, '7 波段重要性机理分析', 1)
body(doc, '利用随机森林的特征重要性分析各光谱区间对分类的贡献。')
make_table(doc, [
    ['光谱区间', '重要性占比'],
    ['近红外 750–950 nm', '33.9%'],
    ['蓝 450–500 nm', '23.4%'],
    ['绿 500–600 nm', '17.0%'],
    ['红 600–680 nm', '15.8%'],
    ['红边 680–750 nm', '9.8%'],
])
caption(doc, '表 4 各光谱区间重要性占比')
body(doc, '近红外波段是区分植被与非植被的核心（植被强烈反射近红外），贡献最大；蓝波段是区分水体/阴影等暗色地物与建筑、道路等'
          '亮色人工地物的关键。红边波段单独重要性较低，原因是它与红、近红外波段高度相关，信息被共享。'
          '该结果表明高光谱分类依靠多波段综合而非单一波段，体现了高光谱相对普通 RGB 影像的优势。')
add_fig(doc, 'RF波段重要性_raw_7216.png', 6.0, '图 9 随机森林波段重要性曲线')

# ---- 8 讨论 ----
heading(doc, '8 讨论', 1)
body(doc, '从混淆矩阵看，水体/阴影（86–87%）与树木（80–89%）分类效果最好，而草地与树木、建筑与道路之间存在明显混淆。'
          '这主要是因为植被子类（草与树）光谱形态相似、人工子类（建筑与道路）光谱亦相近。针对该问题，'
          '可考虑将草地与树木合并为"植被"、建筑与道路合并为"人工地物"的三类方案以进一步提升精度，'
          '或引入光谱-空间联合特征与深度学习模型。此外，跨条带精度的下降提示不同航线间的辐射一致性有待改善，'
          '未来可采用辐射归一化等手段增强跨条带泛化能力。')

# ---- 9 结论 ----
heading(doc, '9 结论', 1)
body(doc, '本文基于珠海校区无人机高光谱影像，完成了"非监督探索—监督分类—多层验证"的完整闭环研究。'
          '主要结论如下：（1）非监督聚类表明校园高光谱数据天然可分五类地物；（2）监督分类中随机森林表现最优，'
          '条带内 OA 达 80.6%，跨条带约 70%；（3）地面真值 SAM 验证证实树木类高度可靠，并揭示草地与树木光谱相似这一机理；'
          '（4）波段重要性分析表明近红外与蓝波段是分类关键。研究为校园尺度高光谱精细分类提供了可行方案与机理认识。')

# ---- 参考文献 ----
heading(doc, '参考文献', 1)
refs = [
    '童庆禧, 张兵, 郑兰芬. 高光谱遥感——原理、技术与应用. 北京: 高等教育出版社, 2006.',
    'Breiman L. Random Forests. Machine Learning, 2001, 45(1): 5-32.',
    'Cortes C, Vapnik V. Support-Vector Networks. Machine Learning, 1995, 20(3): 273-297.',
    'Melgani F, Bruzzone L. Classification of hyperspectral remote sensing images with support vector machines. IEEE Trans. Geosci. Remote Sens., 2004, 42(8): 1778-1790.',
    'Foody G M, Mathur A. A relative evaluation of multiclass image classification by support vector machines. IEEE Trans. Geosci. Remote Sens., 2004, 42(6): 1335-1343.',
    'Ghamisi P, Plaza J, et al. Advanced spectral classifiers for hyperspectral images: A review. IEEE Geosci. Remote Sens. Mag., 2017, 5(1): 8-32.',
]
for i, rf in enumerate(refs, 1):
    body(doc, '[%d] %s' % (i, rf), size=9.5)

out = os.path.join(BASE, '实验报告.docx')
doc.save(out)
print('已保存:', out)
