# -*- coding: utf-8 -*-
"""
RF 波段重要性分析：看哪些波长对分类贡献最大(用于机理解释)。
用法(在 高光谱反射率数据 目录运行)：python rf_importance.py [条带名，默认 raw_7216]
输出(到 结果/)：RF波段重要性_<条带>.png
"""
import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_7216'
DATA_DIR = '原始数据'
TRAIN_DIR = '训练集'
RESULT_DIR = '结果'
os.makedirs(RESULT_DIR, exist_ok=True)

hdr = open(os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr'), encoding='utf-8', errors='ignore').read()
BANDS = int(re.search(r'bands\s*=\s*(\d+)', hdr).group(1))
wls = 399.483 + np.arange(BANDS) * 2.222
sel = (wls >= 450.0) & (wls <= 950.0)
wls_sel = wls[sel]

X = np.load(os.path.join(TRAIN_DIR, 'X_%s.npy' % STRIP)).astype(np.float32)[:, sel]
y = np.load(os.path.join(TRAIN_DIR, 'y_%s.npy' % STRIP)).astype(np.int64)

# 样本均衡
MAX = 2000
keep = []
for c in np.unique(y):
    ci = np.where(y == c)[0]
    if ci.size > MAX:
        ci = np.random.default_rng(0).choice(ci, MAX, replace=False)
    keep.append(ci)
keep = np.sort(np.concatenate(keep))
X, y = X[keep], y[keep]

# 标准化(不用 PCA，保证重要性对应原始波长)
sc = StandardScaler().fit(X)
X = sc.transform(X)

rf = RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1).fit(X, y)
imp = rf.feature_importances_


def smooth(a, w=9):
    k = np.ones(w) / w
    return np.convolve(a, k, mode='same')


imp_s = smooth(imp, 9)

plt.figure(figsize=(11, 5))
plt.plot(wls_sel, imp, alpha=0.35, lw=1, color='gray', label='原始重要性')
plt.plot(wls_sel, imp_s, lw=2, color='#C0392B', label='平滑后')
plt.xlabel('波长 nm')
plt.ylabel('波段重要性')
plt.title('%s 随机森林波段重要性' % STRIP)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
out = os.path.join(RESULT_DIR, 'RF波段重要性_%s.png' % STRIP)
plt.savefig(out, dpi=200)
print('已保存 %s' % out)

top = np.argsort(imp)[::-1][:10]
print('重要性最高的 10 个波段(波长 nm):')
for i in sorted(top):
    print('  %.1f nm  importance=%.4f' % (wls_sel[i], imp[i]))

# 分区重要性(看哪个光谱区间整体最重要)
regions = [('蓝 450-500', 450, 500), ('绿 500-600', 500, 600), ('红 600-680', 600, 680),
           ('红边 680-750', 680, 750), ('近红外 750-950', 750, 950)]
print('各光谱区间重要性占比(%):')
tot = imp.sum()
for name, lo, hi in regions:
    m = (wls_sel >= lo) & (wls_sel < hi)
    print('  %-14s %.1f%%' % (name, imp[m].sum() / tot * 100))
