# -*- coding: utf-8 -*-
"""
SAM 光谱角验证：把地面光谱仪实测光谱(真值)与无人机影像同类平均光谱比对。
用法(在 高光谱反射率数据 目录运行)：python sam_validate.py [影像条带名，默认 raw_7216]
输出(到 结果/)：SAM_验证_<条带>.png
"""
import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_7216'
DATA_DIR = '原始数据'
TRAIN_DIR = '训练集'
RESULT_DIR = '结果'
GROUND_DIR = os.path.normpath(os.path.join('..', '实测光谱', 'BeiShiDa'))

os.makedirs(RESULT_DIR, exist_ok=True)

CLASS_ORDER = ['水体/阴影', '草地', '树木', '建筑', '道路']
GT_CLASSES = ['树木', '草地', '建筑', '道路']   # 有地面真值的 4 类(水体无实测点)

# ---- 读对照表：点编号 -> 规范类别 ----
mapping = {}
for line in open(os.path.join(GROUND_DIR, '对照表.txt'), encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    parts = line.split()
    idx = int(parts[0])
    raw = parts[1]
    if raw.startswith('树木'):
        cls = '树木'
    elif raw.startswith('草地'):
        cls = '草地'
    elif raw.startswith('建筑'):
        cls = '建筑'
    elif raw.startswith('道路'):
        cls = '道路'
    else:
        cls = raw
    mapping[idx] = cls
print('地面实测点映射:', mapping)

# ---- 读影像类平均光谱 ----
X = np.load(os.path.join(TRAIN_DIR, 'X_%s.npy' % STRIP)).astype(np.float32)
y = np.load(os.path.join(TRAIN_DIR, 'y_%s.npy' % STRIP)).astype(np.int64)
hdr = open(os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr'), encoding='utf-8', errors='ignore').read()
BANDS = int(re.search(r'bands\s*=\s*(\d+)', hdr).group(1))
wls = 399.483 + np.arange(BANDS) * 2.222
sel = (wls >= 450.0) & (wls <= 950.0)
wls_sel = wls[sel]

X = X[:, sel]
img_mean = {}
for c, name in enumerate(CLASS_ORDER):
    m = X[y == c]
    img_mean[name] = m.mean(axis=0) if m.size else None


def sam(a, b):
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(np.dot(a, b), -1, 1))))


# ---- 对每个地面点算 SAM(只和 4 个有真值的类比) ----
results = []
for idx in sorted(mapping):
    cls = mapping[idx]
    a = np.loadtxt(os.path.join(GROUND_DIR, '22-02-27_%d.dat' % idx), skiprows=10)
    g = np.interp(wls_sel, a[:, 0], a[:, 3] / 100.0)   # 反射率% -> 0~1，插值到影像波段
    angles = {name: sam(g, img_mean[name]) for name in GT_CLASSES}
    results.append((idx, cls, g, angles))

# ---- 表格 ----
print('\n%-5s %-5s' % ('点', '真值'), end='')
for name in GT_CLASSES:
    print(' %8s' % name, end='')
print('   判为')
correct = 0
for idx, cls, g, angles in results:
    print('%-5d %-5s' % (idx, cls), end='')
    for name in GT_CLASSES:
        print(' %8.1f°' % angles[name], end='')
    pred = min(angles, key=angles.get)
    ok = (pred == cls)
    if ok:
        correct += 1
    print('   %s%s' % (pred, ' 对' if ok else ' 错'))
print('\n地面实测点与影像同类光谱匹配正确率: %d/%d' % (correct, len(results)))

# ---- 画图：4 类，影像类均值(黑粗线) + 该类地面实测光谱(细线) ----
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
for ax, cls in zip(axes.ravel(), GT_CLASSES):
    ax.plot(wls_sel, img_mean[cls], color='black', lw=2.2, label='影像类平均光谱')
    for idx, c2, g, angles in results:
        if c2 == cls:
            ax.plot(wls_sel, g, lw=1, alpha=0.75, label='实测点%d (SAM=%.1f°)' % (idx, angles[cls]))
    ax.set_title(cls, fontsize=13)
    ax.set_xlabel('波长 nm')
    ax.set_ylabel('反射率')
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
fig.suptitle('%s：地面实测光谱 vs 影像类平均光谱（SAM 验证）' % STRIP, fontsize=14)
fig.tight_layout()
out = os.path.join(RESULT_DIR, 'SAM_验证_%s.png' % STRIP)
fig.savefig(out, dpi=200)
print('\n已保存 %s' % out)
