# -*- coding: utf-8 -*-
"""
第3步：PCA + SVM/随机森林 分类 + 精度评价(随机划分 vs 空间划分) + 整图出图。
用法(在本目录运行)：
  python train_classify.py              # 默认 raw_10096
  python train_classify.py raw_5232     # 另一条条带
前置：先跑 labelme_to_dataset.py <条带>
输出(到 结果/)：classification_map_<条带>.png, class_mean_spectra_<条带>.png
"""
import os
import sys
import re
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_10096'
DATA_DIR = '原始数据'
TRAIN_DIR = '训练集'
RESULT_DIR = '结果'
DATA_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or')
HDR_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr')
X_FILE = os.path.join(TRAIN_DIR, 'X_%s.npy' % STRIP)
Y_FILE = os.path.join(TRAIN_DIR, 'y_%s.npy' % STRIP)
C_FILE = os.path.join(TRAIN_DIR, 'coords_%s.npy' % STRIP)
MAP_FILE = os.path.join(TRAIN_DIR, 'class_map_%s.txt' % STRIP)

os.makedirs(RESULT_DIR, exist_ok=True)

txt = open(HDR_FILE, encoding='utf-8', errors='ignore').read()
SAMPLES = int(re.search(r'samples\s*=\s*(\d+)', txt).group(1))
LINES = int(re.search(r'lines\s*=\s*(\d+)', txt).group(1))
BANDS = int(re.search(r'bands\s*=\s*(\d+)', txt).group(1))

# 波长 + 截波段(去两端噪声)
wls = 399.483 + np.arange(BANDS) * 2.222
LO_NM, HI_NM = 450.0, 950.0
sel = (wls >= LO_NM) & (wls <= HI_NM)
print('条带 %s: %d波段 -> %d (保留 %.0f–%.0f nm)' % (STRIP, BANDS, sel.sum(), LO_NM, HI_NM))

X = np.load(X_FILE).astype(np.float32)[:, sel]
y = np.load(Y_FILE).astype(np.int64)
coords = np.load(C_FILE).astype(np.int32)
labels = [l.strip().split('\t')[-1] for l in open(MAP_FILE, encoding='utf-8') if l.strip()]
print('样本:', X.shape, '各类:', np.bincount(y).tolist())

# ---- 样本均衡：每类最多 MAX_PER_CLASS 个像素 ----
MAX_PER_CLASS = 2000
_keep = []
for c in np.unique(y):
    ci = np.where(y == c)[0]
    if ci.size > MAX_PER_CLASS:
        ci = np.random.default_rng(0).choice(ci, MAX_PER_CLASS, replace=False)
    _keep.append(ci)
_keep = np.sort(np.concatenate(_keep))
X, y, coords = X[_keep], y[_keep], coords[_keep]
print('均衡后:', X.shape, '各类:', np.bincount(y).tolist())


def fit_eval(Xtr, ytr, Xte, yte, name, use_svm=True):
    sc = StandardScaler().fit(Xtr) #先标准化
    Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
    pca = PCA(0.99).fit(Xtr)       #保留99%方差，自动选择主成分数
    Xtr_p, Xte_p = pca.transform(Xtr), pca.transform(Xte) #应用PCA变换降维
    print('\n=== %s (PCA主成分=%d) ===' % (name, pca.n_components_))
    rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1).fit(Xtr_p, ytr)
    yp = rf.predict(Xte_p)
    print('[RF] OA=%.3f  Kappa=%.3f' % (accuracy_score(yte, yp), cohen_kappa_score(yte, yp)))
    print(confusion_matrix(yte, yp))
    if use_svm:
        svm = SVC(kernel='rbf', C=10, gamma='scale', random_state=0).fit(Xtr_p, ytr)
        yp2 = svm.predict(Xte_p)
        print('[SVM] OA=%.3f  Kappa=%.3f' % (accuracy_score(yte, yp2), cohen_kappa_score(yte, yp2)))
        mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300, early_stopping=True, random_state=0).fit(Xtr_p, ytr)
        yp3 = mlp.predict(Xte_p)
        print('[MLP] OA=%.3f  Kappa=%.3f' % (accuracy_score(yte, yp3), cohen_kappa_score(yte, yp3)))
    return rf, sc, pca


# 1) 随机划分(像素级)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)
rf, sc, pca = fit_eval(Xtr, ytr, Xte, yte, '随机划分(像素级)')

# 2) 空间划分：左边70%训练，右边30%测试(更真实的泛化)
col = coords[:, 1]
sp_test = col >= int(SAMPLES * 0.7)
if 0 < sp_test.sum() < y.size:
    print('\n--- 空间划分: 训练 %d, 测试 %d ---' % ((~sp_test).sum(), sp_test.sum()))
    fit_eval(X[~sp_test], y[~sp_test], X[sp_test], y[sp_test],
             '空间划分(左训练/右测试)', use_svm=False)
else:
    print('\n空间划分跳过：右边30%没有样本')

# ---- 整图预测(用随机划分训练出的 RF)，只预测有效像元 ----
data = np.fromfile(DATA_FILE, dtype=np.float32).reshape(BANDS, LINES, SAMPLES)
d = data[sel]
del data
valid = np.isfinite(d.sum(axis=0)) & (d.max(axis=0) > 1e-3)   # 剔除无数据(全0/近0)边缘
X_all = d.reshape(d.shape[0], -1).T
idx_valid = np.where(valid.ravel())[0]
y_all = np.full(LINES * SAMPLES, np.nan, dtype=np.float32)
CHUNK = 100000
for s in range(0, idx_valid.size, CHUNK):
    e = min(s + CHUNK, idx_valid.size)
    ci = idx_valid[s:e]
    y_all[ci] = rf.predict(pca.transform(sc.transform(X_all[ci])))
    #复用PCA和标准化器
y_all = y_all.reshape(LINES, SAMPLES)

# 固定配色(按 class_map 顺序：水体/阴影, 草地, 树木, 建筑, 道路)
CLASS_COLORS = ['#2E86DE', '#C8A24E', '#3AA655', '#B5533C', '#8C8C8C']
cmap = ListedColormap(CLASS_COLORS[:len(labels)])
cmap.set_bad('white')
plt.figure(figsize=(8, 12))
im = plt.imshow(y_all, cmap=cmap, vmin=0, vmax=len(labels) - 1)
cbar = plt.colorbar(im, ticks=range(len(labels)))
cbar.ax.set_yticklabels(labels)
plt.title(STRIP + ' 分类结果')
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, 'classification_map_%s.png' % STRIP), dpi=200, bbox_inches='tight')
print('\n已保存 %s' % os.path.join(RESULT_DIR, 'classification_map_%s.png' % STRIP))

# ---- 各类平均光谱(报告用，也是和实测光谱对比的基础) ----
plt.figure(figsize=(9, 5))
for c in sorted(np.unique(y)):
    plt.plot(wls[sel], X[y == c].mean(axis=0), label=labels[c])
plt.xlabel('波长 nm')
plt.ylabel('反射率')
plt.legend()
plt.grid(alpha=0.3)
plt.title(STRIP + ' 各类平均光谱')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, 'class_mean_spectra_%s.png' % STRIP), dpi=200, bbox_inches='tight')
print('已保存 %s' % os.path.join(RESULT_DIR, 'class_mean_spectra_%s.png' % STRIP))
