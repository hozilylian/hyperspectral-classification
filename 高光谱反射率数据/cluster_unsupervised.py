# -*- coding: utf-8 -*-
"""
任务一：非监督聚类探索（MiniBatchKMeans + SSE/CH 选 K），不需要任何标注。
用法(在本目录运行)：
  python cluster_unsupervised.py              # 默认 raw_10096
  python cluster_unsupervised.py raw_5232     # 其他条带
输出(到 结果/)：
  K选择_<条带>.png         —— SSE肘部曲线 + CH指数，看最优K
  聚类图_<条带>.png        —— 整图聚类结果
  聚类平均光谱_<条带>.png   —— 各簇的平均光谱曲线(帮你判断每个簇是什么地物)
  cluster_labels_<条带>.npy —— 聚类标签，供后续任务二参考
"""
import os
import sys
import re
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import calinski_harabasz_score

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

STRIP = sys.argv[1] if len(sys.argv) > 1 else 'raw_10096'
DATA_DIR = '原始数据'
RESULT_DIR = '结果'
DATA_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or')
HDR_FILE = os.path.join(DATA_DIR, STRIP + '_rd_rf_or.hdr')
os.makedirs(RESULT_DIR, exist_ok=True)

txt = open(HDR_FILE, encoding='utf-8', errors='ignore').read()
SAMPLES = int(re.search(r'samples\s*=\s*(\d+)', txt).group(1))
LINES = int(re.search(r'lines\s*=\s*(\d+)', txt).group(1))
BANDS = int(re.search(r'bands\s*=\s*(\d+)', txt).group(1))

wls = 399.483 + np.arange(BANDS) * 2.222
LO_NM, HI_NM = 450.0, 950.0
sel = (wls >= LO_NM) & (wls <= HI_NM)
wls_sel = wls[sel]
print('条带 %s: %d波段 -> %d (保留 %.0f–%.0f nm)' % (STRIP, BANDS, sel.sum(), LO_NM, HI_NM))

# ---- 读数据 + 有效像元筛选(剔除全0/含NaN的背景) ----
d = np.fromfile(DATA_FILE, dtype=np.float32).reshape(BANDS, LINES, SAMPLES)[sel]
dsum = d.sum(axis=0)
valid = np.isfinite(dsum) & (dsum > 0)
print('有效像元: %.1f%%' % (valid.mean() * 100))

X = d[:, valid].T.astype(np.float32)      # (N, 波段) 原始反射率
del d
mu = X.mean(axis=0)
sd = X.std(axis=0)
sd[sd == 0] = 1
Xz = (X - mu) / sd                        # 波段标准化(各波段同权重)

# ---- K 选择(在子样本上做，快) ----
rng = np.random.default_rng(0)
N_SWEEP = min(20000, X.shape[0])
idx = rng.choice(X.shape[0], N_SWEEP, replace=False)
Xs = Xz[idx]

Ks = list(range(5, 21))
sse, ch = [], []
for K in Ks:
    km = MiniBatchKMeans(n_clusters=K, batch_size=4096, max_iter=30, n_init=2, random_state=0)
    lab = km.fit_predict(Xs)
    sse.append(float(km.inertia_))
    try:
        ch.append(float(calinski_harabasz_score(Xs, lab)))
    except ValueError:
        ch.append(np.nan)
    print('K=%2d  SSE=%.3e  CH=%.1f' % (K, sse[-1], ch[-1]))

bestK = int(Ks[int(np.nanargmax(ch))])
print('CH 指数最大对应 K =', bestK)

# ---- 画 K 选择图 ----
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].plot(Ks, sse, 'o-'); ax[0].set_xlabel('K'); ax[0].set_ylabel('SSE'); ax[0].set_title('SSE 肘部曲线'); ax[0].grid(alpha=.3)
ax[1].plot(Ks, ch, 'o-'); ax[1].axvline(bestK, color='r', ls='--'); ax[1].set_xlabel('K'); ax[1].set_ylabel('CH 指数'); ax[1].set_title('CH 指数(越大越好)'); ax[1].grid(alpha=.3)
fig.suptitle('%s 聚类数 K 选择' % STRIP)
fig.tight_layout()
fig.savefig(os.path.join(RESULT_DIR, 'K选择_%s.png' % STRIP), dpi=150)

# ---- 全量聚类 ----
km = MiniBatchKMeans(n_clusters=bestK, batch_size=8192, max_iter=50, n_init=3, random_state=0)
labels_full = km.fit_predict(Xz)

lab_map = np.full((LINES, SAMPLES), np.nan, dtype=np.float32)
lab_map[valid] = labels_full

plt.figure(figsize=(8, 12))
plt.imshow(lab_map, cmap='tab20', vmin=0, vmax=bestK - 1)
plt.colorbar(ticks=range(bestK))
plt.title('%s K=%d 聚类结果' % (STRIP, bestK))
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, '聚类图_%s.png' % STRIP), dpi=200)

plt.figure(figsize=(9, 5))
for c in range(bestK):
    plt.plot(wls_sel, X[labels_full == c].mean(axis=0), label='簇%d' % c)
plt.xlabel('波长 nm'); plt.ylabel('反射率')
plt.legend(ncol=2, fontsize=8); plt.grid(alpha=.3)
plt.title('%s K=%d 各簇平均光谱' % (STRIP, bestK))
plt.tight_layout()
plt.savefig(os.path.join(RESULT_DIR, '聚类平均光谱_%s.png' % STRIP), dpi=200)

np.save(os.path.join(RESULT_DIR, 'cluster_labels_%s.npy' % STRIP), lab_map)
cnt = np.bincount(labels_full, minlength=bestK)
print('各簇像素占比(%):', np.round(cnt / cnt.sum() * 100, 1).tolist())
print('完成，输出在 %s' % RESULT_DIR)
