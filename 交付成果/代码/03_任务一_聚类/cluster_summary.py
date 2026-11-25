# -*- coding: utf-8 -*-
"""
任务一辅助：打印每个聚类簇的光谱指标，帮助判断各簇对应什么地物。
用法(在本目录运行)：python cluster_summary.py [条带名]
"""
import os
import sys
import re
import numpy as np

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_10096'
DATA_DIR = '原始数据'
RESULT_DIR = '结果'

hdr = open(os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr'), encoding='utf-8', errors='ignore').read()
SAMPLES = int(re.search(r'samples\s*=\s*(\d+)', hdr).group(1))
LINES = int(re.search(r'lines\s*=\s*(\d+)', hdr).group(1))
BANDS = int(re.search(r'bands\s*=\s*(\d+)', hdr).group(1))
wls = 399.483 + np.arange(BANDS) * 2.222
sel = (wls >= 450) & (wls <= 950)
wls_sel = wls[sel]

d = np.fromfile(os.path.join(DATA_DIR, STRIP + '_rd_rf_or'), np.float32).reshape(BANDS, LINES, SAMPLES)[sel]
lab = np.load(os.path.join(RESULT_DIR, 'cluster_labels_%s.npy' % STRIP))

def band(lam):
    return int(np.argmin(np.abs(wls_sel - lam)))

g, r, nir = band(550), band(650), band(800)
K = int(np.nanmax(lab)) + 1
print('簇号  占比%%   绿550   红650  近红外800   NDVI     初步判断')
for c in range(K):
    m = d[:, lab == c]
    if m.size == 0:
        continue
    ms = m.mean(1)
    ndvi = (ms[nir] - ms[r]) / (ms[nir] + ms[r])
    pct = (lab == c).mean() * 100
    # 启发式判断
    if ms[nir] < 0.08:
        guess = '水体/阴影(整体很暗)'
    elif ndvi > 0.4:
        guess = '植被(NDVI高)'
    elif ndvi > 0.15:
        guess = '草地/稀疏植被'
    else:
        guess = '人工地物(道路/建筑)'
    print('%-4d %5.1f  %.3f   %.3f   %.3f     %.2f    %s' % (c, pct, ms[g], ms[r], ms[nir], ndvi, guess))
