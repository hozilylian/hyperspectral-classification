# -*- coding: utf-8 -*-
"""
把所有条带各导出一张真彩色 PNG（植被呈绿色）到 标注/ 文件夹，方便看每条带覆盖哪个区域。
用法(在本目录运行)：python export_all_rgb.py
"""
import os
import re
import glob
import numpy as np
from matplotlib import pyplot as plt

DATA_DIR = '原始数据'
ANNO_DIR = '标注'
os.makedirs(ANNO_DIR, exist_ok=True)


def band(wls, lam):
    return int(np.argmin(np.abs(wls - lam)))


for hdr in sorted(glob.glob(os.path.join(DATA_DIR, 'raw_*_rd_rf_or.hdr'))):
    strip = os.path.basename(hdr).replace('_rd_rf_or.hdr', '')
    data_file = os.path.join(DATA_DIR, strip + '_rd_rf_or')
    if not os.path.exists(data_file):
        print('跳过 %s (没有数据文件)' % strip)
        continue
    txt = open(hdr, encoding='utf-8', errors='ignore').read()
    samples = int(re.search(r'samples\s*=\s*(\d+)', txt).group(1))
    lines = int(re.search(r'lines\s*=\s*(\d+)', txt).group(1))
    bands = int(re.search(r'bands\s*=\s*(\d+)', txt).group(1))
    wls = 399.483 + np.arange(bands) * 2.222

    d = np.fromfile(data_file, dtype=np.float32).reshape(bands, lines, samples)
    rgb = np.stack([d[band(wls, 650)], d[band(wls, 550)], d[band(wls, 460)]], -1).astype(np.float32)
    rgb = np.where(np.isfinite(rgb), rgb, 0.0)
    lo, hi = np.percentile(rgb, 2), np.percentile(rgb, 98)
    rgb = np.clip((rgb - lo) / (hi - lo), 0, 1)

    out = os.path.join(ANNO_DIR, strip + '_truecolor.png')
    plt.imsave(out, rgb)
    print('%s: %d x %d -> %s' % (strip, samples, lines, out))
