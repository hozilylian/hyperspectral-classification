# -*- coding: utf-8 -*-
"""
生成 RF / SVM / MLP 三种算法的混淆矩阵图（raw_7216 测试集）。
流程与 train_classify.py 完全一致：波段截取(225) → 均衡(每类2000) → 7:3划分 →
标准化 → PCA(0.99) → 训练三模型 → 混淆矩阵。
输出(到 结果/)：
  confusion_matrix_RF_raw_7216.png
  confusion_matrix_SVM_raw_7216.png
  confusion_matrix_MLP_raw_7216.png
  confusion_matrix_all_raw_7216.png   (三连对比图)
"""
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

STRIP = 'raw_7216'
DATA_DIR = '原始数据'
TRAIN_DIR = '训练集'
RESULT_DIR = '结果'
os.makedirs(RESULT_DIR, exist_ok=True)

hdr = open(os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr'), encoding='utf-8', errors='ignore').read()
BANDS = int(re.search(r'bands\s*=\s*(\d+)', hdr).group(1))
wls = 399.483 + np.arange(BANDS) * 2.222
sel = (wls >= 450.0) & (wls <= 950.0)
print('波段: %d -> %d' % (BANDS, sel.sum()))

X = np.load(os.path.join(TRAIN_DIR, 'X_%s.npy' % STRIP)).astype(np.float32)[:, sel]
y = np.load(os.path.join(TRAIN_DIR, 'y_%s.npy' % STRIP)).astype(np.int64)
labels = [l.strip().split('\t')[-1] for l in open(
    os.path.join(TRAIN_DIR, 'class_map_%s.txt' % STRIP), encoding='utf-8') if l.strip()]
print('类别:', labels)

# ---- 样本均衡：每类最多 2000 ----
MAX = 2000
keep = []
for c in np.unique(y):
    ci = np.where(y == c)[0]
    if ci.size > MAX:
        ci = np.random.default_rng(0).choice(ci, MAX, replace=False)
    keep.append(ci)
keep = np.sort(np.concatenate(keep))
X, y = X[keep], y[keep]
print('均衡后样本:', X.shape, '各类:', np.bincount(y).tolist())

# ---- 7:3 划分 ----
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=0)

# ---- 标准化 + PCA ----
sc = StandardScaler().fit(Xtr)
Xtr, Xte = sc.transform(Xtr), sc.transform(Xte)
pca = PCA(0.99).fit(Xtr)
Xtr_p, Xte_p = pca.transform(Xtr), pca.transform(Xte)
print('PCA 主成分数 =', pca.n_components_)

models = [
    ('RF', RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=1)),
    ('SVM', SVC(kernel='rbf', C=10, gamma='scale', random_state=0)),
    ('MLP', MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300, early_stopping=True, random_state=0)),
]


def evaluate(name, clf):
    clf.fit(Xtr_p, ytr)
    yp = clf.predict(Xte_p)
    oa = accuracy_score(yte, yp)
    kappa = cohen_kappa_score(yte, yp)
    cm = confusion_matrix(yte, yp)
    print('\n=== %s ===  OA=%.4f  Kappa=%.4f' % (name, oa, kappa))
    print(cm)
    return cm, oa, kappa


def draw(ax, cm, oa, kappa, name):
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)  # 行归一化 = 各类召回率
    im = ax.imshow(cm_norm, cmap='Blues', vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    for i in range(len(labels)):
        for j in range(len(labels)):
            c = 'white' if cm_norm[i, j] > 0.5 else 'black'
            ax.text(j, i, '%d\n(%.0f%%)' % (cm[i, j], cm_norm[i, j] * 100),
                    ha='center', va='center', color=c, fontsize=9)
    ax.set_title('%s\nOA=%.1f%%  Kappa=%.3f' % (name, oa * 100, kappa), fontsize=11)
    return im


results = {}
for name, clf in models:
    cm, oa, kappa = evaluate(name, clf)
    results[name] = (cm, oa, kappa)
    fig, ax = plt.subplots(figsize=(5.2, 4.8))
    im = draw(ax, cm, oa, kappa, name)
    ax.set_xlabel('预测类别')
    ax.set_ylabel('真实类别')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='行归一化比例')
    fig.tight_layout()
    out = os.path.join(RESULT_DIR, 'confusion_matrix_%s_%s.png' % (name, STRIP))
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print('已保存:', out)

# ---- 三连对比图 ----
fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
for ax, (name, clf) in zip(axes, models):
    cm, oa, kappa = results[name]
    im = draw(ax, cm, oa, kappa, name)
axes[0].set_ylabel('真实类别')
axes[1].set_xlabel('预测类别')
fig.suptitle('三种算法混淆矩阵对比（raw_7216 测试集）', fontsize=14)
fig.tight_layout()
out = os.path.join(RESULT_DIR, 'confusion_matrix_all_%s.png' % STRIP)
fig.savefig(out, dpi=200)
print('已保存合并图:', out)
