# -*- coding: utf-8 -*-
"""生成暗色高级风格汇报 PPT"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---- 配色(暗色高级) ----
BG = RGBColor(0x0E, 0x13, 0x1F)      # 深蓝黑背景
CARD = RGBColor(0x1A, 0x22, 0x33)    # 卡片深蓝
TITLE_C = RGBColor(0xFF, 0xFF, 0xFF)
BODY_C = RGBColor(0xC6, 0xCD, 0xDA)
MUTED = RGBColor(0x8A, 0x94, 0xA6)
GOLD = RGBColor(0xE3, 0xB6, 0x5E)    # 金
GOLD_DIM = RGBColor(0xB8, 0x8A, 0x3C)
BLUE = RGBColor(0x6E, 0xA8, 0xFE)    # 次级蓝

FONT = 'Microsoft YaHei'
RES = r'C:\Users\ASUS\Desktop\遥感数据\高光谱反射率数据\结果'


def set_run(r, size=18, color=BODY_C, bold=False):
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.name = FONT
    rPr = r._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        from lxml import etree
        ea = etree.SubElement(rPr, qn('a:ea'))
    ea.set('typeface', FONT)


prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = 13.333, 7.5


def new_slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s


def rect(s, x, y, w, h, color, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def tb(s, x, y, w, h):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    return tf


def para(tf, text, size=16, color=BODY_C, bold=False, align=PP_ALIGN.LEFT, sa=6, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(sa)
    r = p.add_run()
    r.text = text
    set_run(r, size, color, bold)
    return p


def bullet(tf, text, size=16, color=BODY_C, bold=False, sa=8, first=False, marker='▪ '):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(sa)
    r0 = p.add_run()
    r0.text = marker
    set_run(r0, size, GOLD, True)
    r = p.add_run()
    r.text = text
    set_run(r, size, color, bold)
    return p


def header(s, section, title):
    rect(s, 0.6, 0.55, 0.06, 0.75, GOLD)          # 左侧金色竖条
    tf = tb(s, 0.85, 0.5, 11.5, 1.0)
    para(tf, section, size=12, color=GOLD, bold=True, sa=2, first=True)
    para(tf, title, size=27, color=TITLE_C, bold=True, sa=0)


def divider(num, title, sub):
    s = new_slide()
    tf = tb(s, 1.0, 2.2, 11.3, 3.0)
    para(tf, num, size=64, color=GOLD_DIM, bold=True, sa=0, first=True)
    para(tf, title, size=36, color=TITLE_C, bold=True, sa=10)
    para(tf, sub, size=16, color=MUTED, sa=0)


def pic(s, fname, x, y, w=None, h=None, cap=None, cap_w=None):
    path = os.path.join(RES, fname)
    if os.path.exists(path):
        kw = {}
        if w:
            kw['width'] = Inches(w)
        if h:
            kw['height'] = Inches(h)
        s.shapes.add_picture(path, Inches(x), Inches(y), **kw)
    if cap:
        tf = tb(s, x, y + (h if h else 3.2), cap_w if cap_w else (w if w else 6), 0.7)
        para(tf, cap, size=11, color=MUTED, sa=0, first=True)


# ==================== 1 封面 ====================
s = new_slide()
rect(s, 0, 0, W, H, BG)
rect(s, 0.9, 2.55, 0.7, 0.05, GOLD)
tf = tb(s, 0.9, 2.0, 11.5, 1.6)
para(tf, '高光谱校园地物精细分类', size=44, color=TITLE_C, bold=True, sa=8, first=True)
tf2 = tb(s, 0.9, 3.35, 11.5, 1.0)
para(tf2, '基于 SVM · 随机森林 · 多层感知机 的对比研究', size=22, color=GOLD, bold=True, sa=0, first=True)
tf3 = tb(s, 0.9, 5.9, 11.5, 1.2)
para(tf3, '珠海校区无人机高光谱影像 ｜ 400–1000 nm · 272 波段 · 0.37 m', size=14, color=MUTED, sa=4, first=True)
para(tf3, '小组成员：×××  ×××  ×××', size=14, color=MUTED, sa=0)

# ==================== 2 目录 ====================
s = new_slide()
header(s, 'CONTENTS', '目录')
items = [
    ('01', '数据预处理', '从 272 波段到可训练的特征'),
    ('02', '模型训练', 'SVM / 随机森林 / 多层感知机 三种算法'),
    ('03', '结果分析', '精度、真值验证与机理解释'),
]
y = 1.9
for num, t, sub in items:
    rect(s, 1.2, y, 0.06, 1.1, GOLD)
    tf = tb(s, 1.5, y - 0.05, 10.5, 1.2)
    para(tf, '%s  %s' % (num, t), size=24, color=TITLE_C, bold=True, sa=3, first=True)
    para(tf, sub, size=14, color=MUTED, sa=0)
    y += 1.75

# ==================== 3 Part 01 ====================
divider('01', '数据预处理', '把 272 个波段的高维反射率，整理成模型可用的低维特征')

# ==================== 4 数据来源 ====================
s = new_slide()
header(s, '01 · 数据预处理', '数据来源')
tf = tb(s, 0.85, 1.9, 11.6, 4.6)
bullet(tf, '无人机：大疆 M300 RTK ＋ Headwall Nano-Hyperspec 高光谱成像仪', first=True)
bullet(tf, '光谱范围 400–1000 nm，272 个连续波段，地面分辨率约 0.37 m')
bullet(tf, '数据已由老师完成辐射定标（转为反射率）与正射校正，可直接分析')
bullet(tf, '目标类别 5 类：水体/阴影、草地、树木、建筑、道路')
para(tf, '关键点：每个像素不是 3 个值（RGB），而是 272 个值——一条完整光谱曲线', size=15, color=GOLD, bold=True, sa=0)

# ==================== 5 预处理四步 ====================
s = new_slide()
header(s, '01 · 数据预处理', '做了什么：四步预处理')
tf = tb(s, 0.85, 1.75, 6.3, 5.2)
bullet(tf, '① 波段截取 272 → 225', size=17, color=TITLE_C, bold=True, first=True)
para(tf, '去掉 400–450、950–1000 nm 两端噪声大的波段', size=14, sa=12)
bullet(tf, '② 无效像元剔除', size=17, color=TITLE_C, bold=True)
para(tf, '去掉全 0 / 近 0 的无数据边缘像元', size=14, sa=12)
bullet(tf, '③ 标准化（Z-score）', size=17, color=TITLE_C, bold=True)
para(tf, '每个波段减均值除标准差，统一量纲', size=14, sa=12)
bullet(tf, '④ PCA 降维 225 → 3~4 维', size=17, color=TITLE_C, bold=True)
para(tf, '相邻波段高度相关、冗余大，保留 99% 方差只需 3~4 个主成分', size=14, sa=0)
pic(s, 'class_mean_spectra_raw_7216.png', 7.5, 1.9, w=5.2, cap='图 每类地物是一条 225 维光谱曲线——高维、冗余，故需 PCA', cap_w=5.2)

# ==================== 6 Part 02 ====================
divider('02', '模型训练', '三种算法，覆盖「核方法 / 集成学习 / 神经网络」三大路线')

# ==================== 7 共同流程 ====================
s = new_slide()
header(s, '02 · 模型训练', '为什么选这三种 + 共同流程')
tf = tb(s, 0.85, 1.7, 11.6, 2.6)
para(tf, '选模型，先看高光谱分类的两个难点', size=15, color=GOLD, bold=True, sa=5, first=True)
bullet(tf, '难点① 225 个波段高度相关、冗余大；难点② 草-树、楼-路光谱重叠', size=15, sa=8)
bullet(tf, 'SVM（RBF 核）：高维小样本经典方法，用核函数处理非线性边界 → 传统基线', size=15, sa=6)
bullet(tf, 'RF：对高维冗余和噪声最鲁棒，还能产出波段重要性 → 主力模型', size=15, sa=6)
bullet(tf, 'MLP：神经网络自动学特征，检验深度学习是否更优 → 对比模型', size=15, sa=0)
tf2 = tb(s, 0.85, 4.45, 11.6, 2.4)
para(tf2, '共同流程', size=17, color=GOLD, bold=True, sa=8, first=True)
bullet(tf2, '数据集（5 类，7216 条带标注，10000 均衡样本）→ 标准化 → PCA 降维', sa=6)
bullet(tf2, '→ 训练分类器 → 用 OA / Kappa / 混淆矩阵 评价精度', sa=0)

# ==================== 8 SVM ====================
s = new_slide()
header(s, '02 · 模型训练', 'SVM 支持向量机')
rect(s, 0.85, 1.7, 5.6, 5.2, CARD)
tf = tb(s, 1.1, 1.95, 5.1, 4.8)
para(tf, '是什么', size=16, color=GOLD, bold=True, sa=6, first=True)
bullet(tf, '找一条「最大间隔」超平面把类别分开', size=14, sa=10)
para(tf, '为什么选', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '理论经典、边界清晰，小样本也稳定', size=14, sa=10)
para(tf, '处理流程', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '线性分不开 → RBF 核映射高维 → 找最大间隔 → 多分类一对一投票', size=14, sa=10)
para(tf, '参数 / 结果', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, 'C=10、gamma=scale；OA 76.4%', size=14, sa=0)
tf = tb(s, 6.8, 1.9, 5.9, 4.8)
para(tf, '好处与局限', size=16, color=GOLD, bold=True, sa=8, first=True)
bullet(tf, '优点：理论严谨、仅由支持向量决定、可解释', sa=8)
bullet(tf, '局限：对参数 C、gamma 敏感，多类光谱重叠时偏弱', sa=8)
para(tf, '为什么它是三者最弱（76.4%）', size=15, color=BLUE, bold=True, sa=6)
bullet(tf, '高光谱多类、类间有重叠，非线性边界不好调', sa=0)

# ==================== 9 RF ====================
s = new_slide()
header(s, '02 · 模型训练', 'RF 随机森林')
rect(s, 0.85, 1.7, 5.6, 5.2, CARD)
tf = tb(s, 1.1, 1.95, 5.1, 4.8)
para(tf, '是什么', size=16, color=GOLD, bold=True, sa=6, first=True)
bullet(tf, '300 棵决策树投票，多数表决', size=14, sa=10)
para(tf, '为什么选', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '波段多、有噪声，RF 最鲁棒', size=14, sa=10)
para(tf, '处理流程', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '每棵树随机抽样本(bootstrap)＋随机抽波段 → 各自建树 → 投票', size=14, sa=10)
para(tf, '参数 / 结果', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, 'n_estimators=300；OA 80.6%（最优）', size=14, sa=0)
tf = tb(s, 6.8, 1.9, 5.9, 4.8)
para(tf, '好处与局限', size=16, color=GOLD, bold=True, sa=8, first=True)
bullet(tf, '优点：抗过拟合、抗噪、高维鲁棒', sa=8)
bullet(tf, '附带产出「波段重要性」，可做机理解释', sa=8)
para(tf, '为什么它最优（80.6%）', size=15, color=BLUE, bold=True, sa=6)
bullet(tf, '两处随机让树各不相同、错误互相抵消，最适合高维冗余数据', sa=0)

# ==================== 10 MLP ====================
s = new_slide()
header(s, '02 · 模型训练', 'MLP 多层感知机')
rect(s, 0.85, 1.7, 5.6, 5.2, CARD)
tf = tb(s, 1.1, 1.95, 5.1, 4.8)
para(tf, '是什么', size=16, color=GOLD, bold=True, sa=6, first=True)
bullet(tf, '两层全连接神经网络：128 → 64 → 5', size=14, sa=10)
para(tf, '为什么选', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '自动学特征，贴合 AI 方向', size=14, sa=10)
para(tf, '处理流程', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, 'ReLU 激活 → softmax 输出概率 → 交叉熵损失 → 反向传播 + Adam 更新', size=14, sa=10)
para(tf, '参数 / 结果', size=16, color=GOLD, bold=True, sa=6)
bullet(tf, '128×64、early stopping；OA 79.1%', size=14, sa=0)
tf = tb(s, 6.8, 1.9, 5.9, 4.8)
para(tf, '好处与局限', size=16, color=GOLD, bold=True, sa=8, first=True)
bullet(tf, '优点：非线性映射灵活、自动提特征', sa=8)
bullet(tf, '局限：样本有限、特征已 PCA 降维，优势没发挥', sa=8)
para(tf, '为什么它居中（79.1%）', size=15, color=BLUE, bold=True, sa=6)
bullet(tf, '比 SVM 灵活，但数据量（1 万）相对网络偏少，略低于 RF', sa=0)

# ==================== 11 三模型对比 ====================
s = new_slide()
header(s, '02 · 模型训练', '三模型精度对比')
rows = [
    ('模型', '总体精度 OA', 'Kappa', '核心思路'),
    ('随机森林 RF', '80.6%', '0.758', '多树集成投票'),
    ('多层感知机 MLP', '79.1%', '0.739', '多层非线性映射'),
    ('支持向量机 SVM', '76.4%', '0.705', '最大间隔超平面'),
]
tbl = s.shapes.add_table(4, 4, Inches(1.2), Inches(1.9), Inches(10.9), Inches(2.8)).table
tbl.columns[0].width = Inches(2.9)
tbl.columns[1].width = Inches(2.7)
tbl.columns[2].width = Inches(2.0)
tbl.columns[3].width = Inches(3.3)
for i, row in enumerate(rows):
    for j, val in enumerate(row):
        c = tbl.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = GOLD_DIM if i == 0 else CARD
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = val
        set_run(r, 16 if i else 17, TITLE_C if (i == 0 or j == 0 or j == 1) else BODY_C, bold=(i == 0 or j == 0))
tf = tb(s, 1.2, 5.2, 10.9, 1.2)
para(tf, '结论：随机森林最优——对高光谱「波段冗余＋噪声」最鲁棒；SVM 受参数敏感拖累；MLP 因样本有限未充分发挥。',
     size=15, color=GOLD, bold=True, first=True)

# ==================== 12 Part 03 ====================
divider('03', '结果分析', '精度验证 + 地面真值比对 + 波段机理')

# ==================== 13 条带内精度 + 分类图 ====================
s = new_slide()
header(s, '03 · 结果分析', '条带内精度：随机 ≈ 空间')
tf = tb(s, 0.85, 1.85, 6.0, 4.8)
bullet(tf, '随机划分 OA 80.6% ≈ 空间划分 OA 80.4%', size=18, color=TITLE_C, bold=True, first=True)
bullet(tf, '说明模型在条带内空间泛化良好，没有「空间泄漏虚高」', sa=10)
bullet(tf, '分类图（右）：5 色对应 5 类，白色为无数据边缘', sa=10)
bullet(tf, '水体/阴影(蓝)、草地(棕黄)、树木(绿)、建筑(棕红)、道路(灰)', sa=0)
pic(s, 'classification_map_raw_7216.png', 7.2, 1.35, h=5.4, cap='图 raw_7216 分类结果（白色=无数据边缘）', cap_w=5.0)

# ==================== 14 跨条带验证 ====================
s = new_slide()
header(s, '03 · 结果分析', '跨条带验证：真实泛化')
tf = tb(s, 0.85, 1.85, 12.0, 1.6)
bullet(tf, '7216 训练 → 10096 测试 OA 69.2%；→ 5232 测试 OA 71.4%', size=18, color=TITLE_C, bold=True, first=True)
bullet(tf, '比条带内掉约 10 点 = 不同航线光照/大气差异带来的真实泛化差距', sa=0)
pic(s, 'cross_raw_7216_to_raw_10096.png', 1.3, 3.7, h=3.2, cap='预测 10096（OA 69.2%）', cap_w=4.5)
pic(s, 'cross_raw_7216_to_raw_5232.png', 7.3, 3.7, h=3.2, cap='预测 5232（OA 71.4%）', cap_w=4.5)

# ==================== 15 SAM 真值验证 ====================
s = new_slide()
header(s, '03 · 结果分析', '地面真值 SAM 验证')
tf = tb(s, 0.85, 1.85, 12.0, 1.7)
bullet(tf, '16 个地面光谱仪实测点 与 影像同类光谱 算光谱角（越小越像）', size=18, color=TITLE_C, bold=True, first=True)
bullet(tf, '树木 5/5 强吻合（平均约 7.6°）；草地更接近「树木」→ 印证草-树光谱相似', sa=0)
pic(s, 'SAM_验证_raw_7216.png', 1.6, 3.7, w=9.8, cap='图 影像类平均光谱（黑）与地面实测光谱（彩）比对（SAM）', cap_w=9.8)

# ==================== 16 波段重要性 ====================
s = new_slide()
header(s, '03 · 结果分析', '波段重要性：机理')
tf = tb(s, 0.85, 1.85, 12.0, 1.7)
bullet(tf, '近红外 750–950 nm 占 33.9%（区分植被）；蓝 450–500 nm 占 23.4%（区分暗/亮地物）', size=17, color=TITLE_C, bold=True, first=True)
bullet(tf, '红边单独占比低：与红、近红外高度相关，信息被共享', sa=0)
pic(s, 'RF波段重要性_raw_7216.png', 1.8, 3.9, w=9.6, cap='图 随机森林波段重要性（越高越关键）', cap_w=9.6)

# ==================== 17 讨论 ====================
s = new_slide()
header(s, '03 · 结果分析', '误差分析：谁和谁混、为什么')
tf = tb(s, 0.85, 1.7, 11.6, 5.5)
bullet(tf, '分得好：水体/阴影 86–87%、树木 80–89% —— 近红外特征鲜明', size=16, color=TITLE_C, bold=True, first=True)
bullet(tf, '草地 ↔ 树木：都含叶绿素——红光吸收谷(≈680nm)、绿光反射峰、近红外高反射一致，光谱形态几乎相同', size=15, sa=6)
bullet(tf, '　　　差异只在近红外强度（冠层结构、叶面积不同），不足以稳定分开', size=15, sa=10)
bullet(tf, '建筑 ↔ 道路：都是混凝土/沥青硬化面——无植被吸收谷、反射率随波长平缓上升、量级接近', size=15, sa=6)
bullet(tf, '　　　屋顶与路面同为灰白时，光谱几乎重合', size=15, sa=10)
bullet(tf, '跨条带掉约 10 点：不同航线光照角度、大气程辐射不同 → 同一地物反射率系统性偏移', size=15, sa=10)
bullet(tf, '改进：合并大类提精度；光谱-空间联合；跨条带辐射归一化', size=15, sa=0)

# ==================== 18 结论 ====================
s = new_slide()
header(s, 'CONCLUSION', '结论')
tf = tb(s, 0.85, 1.7, 11.6, 5.3)
bullet(tf, '完成「非监督探索定类 → 监督分类 → 多层验证」的完整闭环', size=17, color=TITLE_C, bold=True, first=True)
bullet(tf, '随机森林最优：条带内 OA 80.6%（优于 MLP 79.1%、SVM 76.4%）；跨条带约 70%', size=16, sa=10)
bullet(tf, '地面真值 SAM：树木类 5/5 强吻合，并揭示草-树光谱高度相似这一机理', size=16, sa=10)
bullet(tf, '波段重要性：近红外（区分植被）+ 蓝波段（区分暗/亮）是分类关键', size=16, sa=10)
bullet(tf, '展望：光谱-空间联合、细分地物、辐射归一化以提升跨条带泛化', size=16, sa=0)

# ==================== 19 致谢 ====================
s = new_slide()
rect(s, 0, 0, W, H, BG)
tf = tb(s, 0, 3.0, W, 1.5)
para(tf, '谢谢', size=48, color=TITLE_C, bold=True, align=PP_ALIGN.CENTER, first=True)
tf2 = tb(s, 0, 4.6, W, 1.0)
para(tf2, 'BEIJING NORMAL UNIVERSITY ｜ 小组成员：×××  ×××  ×××', size=14, color=MUTED, align=PP_ALIGN.CENTER, first=True)

out = r'C:\Users\ASUS\Desktop\遥感数据\交付成果\汇报PPT.pptx'
prs.save(out)
print('已保存:', out)
