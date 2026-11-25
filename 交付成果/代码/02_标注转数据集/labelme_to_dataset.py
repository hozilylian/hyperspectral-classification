# -*- coding: utf-8 -*-
"""
第2步：把 labelme 标注的多边形 json 转成训练集 (X, y, coords)。
用法(在本目录运行)：
  python labelme_to_dataset.py              # 默认 raw_10096
  python labelme_to_dataset.py raw_5232     # 另一条条带
前置：先把对应条带的假彩色 PNG 用 labelme 标注，json 放 标注/ 文件夹。
输出(到 训练集/)：X_<条带>.npy, y_<条带>.npy, coords_<条带>.npy, class_map_<条带>.txt
"""
import os
import re
import sys
import glob
import json
import numpy as np
from matplotlib.path import Path

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_10096'
DATA_DIR = '原始数据'
ANNO_DIR = '标注'
TRAIN_DIR = '训练集'
DATA_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or')
HDR_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr')

# 统一类别顺序（labelme 标签文字要一模一样）
CLASS_ORDER = ['水体/阴影', '草地', '树木', '建筑', '道路']

# 标签别名：把常见的同义写法归并到上面 5 类（避免漏标）
LABEL_ALIAS = {'水体': '水体/阴影', '湖泊': '水体/阴影', '阴影': '水体/阴影'}

os.makedirs(TRAIN_DIR, exist_ok=True)

# ---- 从 .hdr 自动读尺寸 ----
txt = open(HDR_FILE, encoding='utf-8', errors='ignore').read()
SAMPLES = int(re.search(r'samples\s*=\s*(\d+)', txt).group(1))
LINES = int(re.search(r'lines\s*=\s*(\d+)', txt).group(1))
BANDS = int(re.search(r'bands\s*=\s*(\d+)', txt).group(1))
print('条带 %s: %d列 x %d行 x %d波段' % (STRIP, SAMPLES, LINES, BANDS))

data = np.fromfile(DATA_FILE, dtype=np.float32).reshape(BANDS, LINES, SAMPLES)
X_all = data.reshape(BANDS, -1).T          # (像素数, 波段)

cols, rows = np.meshgrid(np.arange(SAMPLES), np.arange(LINES))
pts = np.stack([cols.ravel(), rows.ravel()], axis=1)

name2id = {n: i for i, n in enumerate(CLASS_ORDER)}
Xs, ys, cs = [], [], []

jfiles = sorted(set(glob.glob(os.path.join(ANNO_DIR, STRIP + '_falsecolor*.json'))
                    + glob.glob(os.path.join(ANNO_DIR, STRIP + '_truecolor*.json'))))
if not jfiles:
    raise SystemExit('没找到 %s 的 labelme json（应在 %s 文件夹）' % (STRIP, ANNO_DIR))

for jf in jfiles:
    with open(jf, encoding='utf-8') as f:
        d = json.load(f)
    print('处理:', os.path.basename(jf))
    for sh in d['shapes']:
        label = sh['label'].strip()
        label = LABEL_ALIAS.get(label, label)   # 同义归并
        if label not in name2id:
            print('  警告: 未知标签 "%s" 已跳过' % label)
            continue
        path = Path(sh['points'])
        inside = path.contains_points(pts).reshape(LINES, SAMPLES)
        idx = np.where(inside.ravel())[0]
        if idx.size == 0:
            print('  警告: "%s" 没覆盖到像素' % label)
            continue
        Xs.append(X_all[idx])
        ys.append(np.full(idx.size, name2id[label], dtype=np.int64))
        cs.append(np.stack([idx // SAMPLES, idx % SAMPLES], axis=1))  # (行, 列)
        print('  %-8s -> %d 个像素' % (label, idx.size))

if not Xs:
    raise SystemExit('没提取到任何样本')

X = np.concatenate(Xs).astype(np.float32)
y = np.concatenate(ys)
coords = np.concatenate(cs).astype(np.int32)
np.save(os.path.join(TRAIN_DIR, 'X_%s.npy' % STRIP), X)
np.save(os.path.join(TRAIN_DIR, 'y_%s.npy' % STRIP), y)
np.save(os.path.join(TRAIN_DIR, 'coords_%s.npy' % STRIP), coords)
with open(os.path.join(TRAIN_DIR, 'class_map_%s.txt' % STRIP), 'w', encoding='utf-8') as f:
    for n, i in sorted(name2id.items(), key=lambda kv: kv[1]):
        f.write('%d\t%s\n' % (i, n))
print('完成: X=%s y=%s 各类=%s' % (X.shape, y.shape, np.bincount(y).tolist()))
