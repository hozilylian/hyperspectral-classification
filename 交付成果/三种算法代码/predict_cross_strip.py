# -*- coding: utf-8 -*-
"""
跨条带验证：用训练条带(默认 raw_7216)训练模型，应用到其他所有条带。
  - 对每条带输出整图分类图；
  - 若该条带有标注(训练集里存在 X_<条带>.npy)，同时计算跨条带精度 OA/Kappa。
用法(在本目录运行)：
  python predict_cross_strip.py              # 默认训练条带 raw_7216
前置：先跑 labelme_to_dataset.py <训练条带>，以及需要验证精度的测试条带
输出(到 结果/)：cross_<训练条带>_to_<测试条带>.png
"""
import os
import sys
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

TRAIN_STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_7216'
DATA_DIR = '原始数据'
TRAIN_DIR = '训练集'
RESULT_DIR = '结果'
os.makedirs(RESULT_DIR, exist_ok=True)


def read_hdr(strip):
    txt = open(os.path.join(DATA_DIR, strip + '_rd_rf_or.hdr'), encoding='utf-8', errors='ignore').read()
    s = int(re.search(r'samples\s*=\s*(\d+)', txt).group(1))
    l = int(re.search(r'lines\s*=\s*(\d+)', txt).group(1))
    b = int(re.search(r'bands\s*=\s*(\d+)', txt).group(1))
    return s, l, b


_, _, BANDS = read_hdr(TRAIN_STRIP)
wls = 399.483 + np.arange(BANDS) * 2.222
sel = (wls >= 450.0) & (wls <= 950.0)

# ---- 读训练集 ----
X = np.load(os.path.join(TRAIN_DIR, 'X_%s.npy' % TRAIN_STRIP)).astype(np.float32)[:, sel]
y = np.load(os.path.join(TRAIN_DIR, 'y_%s.npy' % TRAIN_STRIP)).astype(np.int64)
labels = [l.strip().split('\t')[-1] for l in open(os.path.join(TRAIN_DIR, 'class_map_%s.txt' % TRAIN_STRIP), encoding='utf-8') if l.strip()]
print('训练条带 %s: 样本 %s, 各类 %s' % (TRAIN_STRIP, X.shape, np.bincount(y).tolist()))

# 样本均衡
MAX_PER_CLASS = 2000
keep = []
for c in np.unique(y):
    ci = np.where(y == c)[0]
    if ci.size > MAX_PER_CLASS:
        ci = np.random.default_rng(0).choice(ci, MAX_PER_CLASS, replace=False)
    keep.append(ci)
keep = np.sort(np.concatenate(keep))
X, y = X[keep], y[keep]
print('均衡后: %s, 各类 %s' % (X.shape, np.bincount(y).tolist()))

# 训练集自检(随机划分)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)
sc = StandardScaler().fit(Xtr)
pca = PCA(0.99).fit(sc.transform(Xtr))
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1).fit(pca.transform(sc.transform(Xtr)), ytr)
yp = rf.predict(pca.transform(sc.transform(Xte)))
print('训练集自检(随机划分) RF: OA=%.3f Kappa=%.3f' % (accuracy_score(yte, yp), cohen_kappa_score(yte, yp)))

# 用全部训练样本重训最终模型
sc = StandardScaler().fit(X)
pca = PCA(0.99).fit(sc.transform(X))
rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1).fit(pca.transform(sc.transform(X)), y)
print('最终模型已用全部训练样本训练 (PCA主成分=%d)\n' % pca.n_components_)

# ---- 应用到其他条带 ----
# 固定配色(按 class_map 顺序：水体/阴影, 草地, 树木, 建筑, 道路)
CLASS_COLORS = ['#2E86DE', '#C8A24E', '#3AA655', '#B5533C', '#8C8C8C']
cmap = ListedColormap(CLASS_COLORS[:len(labels)])
cmap.set_bad('white')
for hdr in sorted(glob.glob(os.path.join(DATA_DIR, 'raw_*_rd_rf_or.hdr'))):
    strip = os.path.basename(hdr).replace('_rd_rf_or.hdr', '')
    if strip == TRAIN_STRIP:
        continue
    data_file = os.path.join(DATA_DIR, strip + '_rd_rf_or')
    if not os.path.exists(data_file):
        continue
    s, l, b = read_hdr(strip)
    d = np.fromfile(data_file, np.float32).reshape(b, l, s)
    d = d[sel]                       # 只取选中波段(释放原始272波段)
    valid = np.isfinite(d.sum(axis=0)) & (d.max(axis=0) > 1e-3)   # 剔除无数据边缘
    Xall = d.reshape(d.shape[0], -1).T
    idx_valid = np.where(valid.ravel())[0]
    yall = np.full(Xall.shape[0], np.nan, dtype=np.float32)
    CHUNK = 100000
    for st in range(0, idx_valid.size, CHUNK):
        en = min(st + CHUNK, idx_valid.size)
        ci = idx_valid[st:en]
        yall[ci] = rf.predict(pca.transform(sc.transform(Xall[ci])))
    ymap = yall.reshape(l, s)
    plt.figure(figsize=(8, 12))
    plt.imshow(ymap, cmap=cmap, vmin=0, vmax=len(labels) - 1)
    cbar = plt.colorbar(ticks=range(len(labels)))
    cbar.ax.set_yticklabels(labels)
    plt.title('训练%s → 预测%s' % (TRAIN_STRIP, strip))
    plt.axis('off')
    plt.tight_layout()
    out = os.path.join(RESULT_DIR, 'cross_%s_to_%s.png' % (TRAIN_STRIP, strip))
    plt.savefig(out, dpi=200)
    plt.close()
    print('已保存 %s' % out)

    # 若该条带有标注，计算跨条带精度
    xf = os.path.join(TRAIN_DIR, 'X_%s.npy' % strip)
    yf = os.path.join(TRAIN_DIR, 'y_%s.npy' % strip)
    if os.path.exists(xf) and os.path.exists(yf):
        Xt = np.load(xf).astype(np.float32)[:, sel]
        yt = np.load(yf).astype(np.int64)
        yt_p = rf.predict(pca.transform(sc.transform(Xt)))
        print('  跨条带 %s: 标注像素 %d, OA=%.3f Kappa=%.3f' % (strip, Xt.shape[0], accuracy_score(yt, yt_p), cohen_kappa_score(yt, yt_p)))
        print('  混淆矩阵(行=真值,列=预测):')
        print(confusion_matrix(yt, yt_p))
    else:
        print('  跨条带 %s: 无标注, 仅输出预测图' % strip)

print('\n跨条带验证完成')
