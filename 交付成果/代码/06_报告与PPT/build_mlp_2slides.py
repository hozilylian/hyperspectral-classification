# -*- coding: utf-8 -*-
"""生成 MLP 2 页讲解 PPT"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BG = RGBColor(0x0E, 0x13, 0x1F)
TITLE_C = RGBColor(0xFF, 0xFF, 0xFF)
BODY_C = RGBColor(0xC6, 0xCD, 0xDA)
MUTED = RGBColor(0x8A, 0x94, 0xA6)
GOLD = RGBColor(0xE3, 0xB6, 0x5E)
BLUE = RGBColor(0x6E, 0xA8, 0xFE)
FONT = 'Microsoft YaHei'
FIGS = r'C:\Users\ASUS\Desktop\遥感数据\交付成果\mlp_figs'


def set_run(r, size, color, bold=False):
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


def slide():
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    return s


def rect(s, x, y, w, h, color):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh


def tb(s, x, y, w, h):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    box.text_frame.word_wrap = True
    return box.text_frame


def para(tf, text, size=16, color=BODY_C, bold=False, align=PP_ALIGN.LEFT, sa=6, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align; p.space_after = Pt(sa)
    r = p.add_run(); r.text = text; set_run(r, size, color, bold)
    return p


def bullet(tf, text, size=16, color=BODY_C, bold=False, sa=6, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(sa)
    r0 = p.add_run(); r0.text = '▪ '; set_run(r0, size, GOLD, True)
    r = p.add_run(); r.text = text; set_run(r, size, color, bold)
    return p


def header(s, title):
    rect(s, 0.6, 0.5, 0.06, 0.7, GOLD)
    tf = tb(s, 0.85, 0.42, 12.2, 0.9)
    para(tf, title, size=24, color=TITLE_C, bold=True, first=True)


# ==================== 第 1 页 ====================
s = slide()
header(s, 'MLP 分类器（1/2）· 输入输出 / 训练架构 / 参数层级')
pic = os.path.join(FIGS, 'fig1.png')
if os.path.exists(pic):
    s.shapes.add_picture(pic, Inches(0.95), Inches(1.3), width=Inches(11.4))
tf = tb(s, 0.85, 6.55, 11.7, 0.7)
para(tf, '输入 = 每像素 3~4 个主成分｜输出 = softmax 5 类概率｜全连接 FNN（非 CNN）｜参数 ≈ 9200 个（梯度下降自动学出）',
     size=14, color=GOLD, bold=True, first=True)

# ==================== 第 2 页 ====================
s = slide()
header(s, 'MLP 分类器（2/2）· 如何预测 / Pipeline')
pic = os.path.join(FIGS, 'fig2.png')
if os.path.exists(pic):
    s.shapes.add_picture(pic, Inches(0.7), Inches(1.25), width=Inches(11.9))
tf = tb(s, 0.85, 5.35, 11.7, 2.0)
para(tf, '如何预测（训练完成后）', size=16, color=GOLD, bold=True, sa=5, first=True)
bullet(tf, '① 每个像素做同样的 标准化 + PCA → ② 喂进 MLP 得 5 个概率，取 argmax → ③ 结果重塑回 884×1658 二维图', size=15, sa=7)
bullet(tf, '训练迭代：随机初始化 → 前向传播 → 交叉熵损失 → 反向传播 → Adam 更新（最多 300 轮，early stopping）', size=15, sa=0)

out = r'C:\Users\ASUS\Desktop\遥感数据\交付成果\MLP讲解.pptx'
prs.save(out)
print('已保存:', out)
