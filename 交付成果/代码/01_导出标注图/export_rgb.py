# -*- coding: utf-8 -*-
"""
第1步(单条带)：导出一条真彩色 PNG（植被呈绿色）到 标注/ 文件夹（供 labelme 标注）。
用法(在本目录运行)：python export_rgb.py
"""
import os
import numpy as np
from matplotlib import pyplot as plt

# ---- 配置 ----
DATA_DIR = '原始数据'
ANNO_DIR = '标注'
FILE = os.path.join(DATA_DIR, 'raw_10096_rd_rf_or')
SAMPLES, LINES, BANDS = 756, 1246, 272
OUT = os.path.join(ANNO_DIR, 'raw_10096_truecolor.png')

os.makedirs(ANNO_DIR, exist_ok=True)

# 波长 ≈ 399.483 + idx*2.222
wls = 399.483 + np.arange(BANDS) * 2.222

def band(lam):
    return int(np.argmin(np.abs(wls - lam)))

# ---- 读数据 (BSQ 波段优先存储, float32) ----
d = np.fromfile(FILE, dtype=np.float32).reshape(BANDS, LINES, SAMPLES)
print('shape:', d.shape, 'min:', float(np.nanmin(d)), 'max:', float(np.nanmax(d)))

# ---- 真彩色合成：R=红650nm, G=绿550nm, B=蓝460nm（植被呈绿色）----
r, g, b = band(650), band(550), band(460)
rgb = np.stack([d[r], d[g], d[b]], axis=-1).astype(np.float32)
rgb = np.where(np.isfinite(rgb), rgb, 0.0)   # 去掉 NaN/Inf

# 2%~98% 分位数线性拉伸到 0~1
lo, hi = np.percentile(rgb, 2), np.percentile(rgb, 98)
rgb = np.clip((rgb - lo) / (hi - lo), 0, 1)

plt.imsave(OUT, rgb)
print('已保存:', OUT)
