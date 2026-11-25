# -*- coding: utf-8 -*-
"""
只重画 K 选择图（完整扫描 K=1~20），不改动任何聚类结果。
和 cluster_unsupervised.py 里的 K 扫描逻辑完全一致（同样的子样本、同样的参数），
只是把扫描下界从 5 改到 1，并单独保存成 K选择_<条带>_full.png（不覆盖原图）。
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
sel = (wls >= 450.0) & (wls <= 950.0)
wls_sel = wls[sel]
print('条带 %s: %d波段 -> %d (保留 %.0f–%.0f nm)' % (STRIP, BANDS, sel.sum(), 450.0, 950.0))

# ---- 读数据 + 有效像元筛选 + 标准化（与原脚本完全一致） ----
d = np.fromfile(DATA_FILE, dtype=np.float32).reshape(BANDS, LINES, SAMPLES)[sel]
dsum = d.sum(axis=0)
valid = np.isfinite(dsum) & (dsum > 0)
print('有效像元: %.1f%%' % (valid.mean() * 100))

X = d[:, valid].T.astype(np.float32)
del d
mu = X.mean(axis=0)
sd = X.std(axis=0)
sd[sd == 0] = 1
Xz = (X - mu) / sd

rng = np.random.default_rng(0)
N_SWEEP = min(20000, X.shape[0])
idx = rng.choice(X.shape[0], N_SWEEP, replace=False)
Xs = Xz[idx]

# ---- 完整扫描 K=1~20 ----
Ks = list(range(1, 21))
sse, ch = [], []
for K in Ks:
    km = MiniBatchKMeans(n_clusters=K, batch_size=4096, max_iter=30, n_init=2, random_state=0)
    lab = km.fit_predict(Xs)
    sse.append(float(km.inertia_))
    if K >= 2:
        try:
            ch.append(float(calinski_harabasz_score(Xs, lab)))
        except ValueError:
            ch.append(np.nan)
    else:
        ch.append(np.nan)   # CH 在 K=1 无定义
    print('K=%2d  SSE=%.3e  CH=%s' % (K, sse[-1], 'NaN' if K == 1 else '%.1f' % ch[-1]))

bestK = int(Ks[int(np.nanargmax(ch))])
print('CH 指数最大对应 K =', bestK)

# ---- 画图（SSE 用 1~20，CH 从 2 起有值） ----
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].plot(Ks, sse, 'o-')
ax[0].set_xlabel('K')
ax[0].set_ylabel('SSE')
ax[0].set_title('SSE 肘部曲线(K=1~20)')
ax[0].grid(alpha=.3)
ax[1].plot(Ks, ch, 'o-')
ax[1].axvline(bestK, color='r', ls='--', label='CH最大 K=%d' % bestK)
ax[1].set_xlabel('K')
ax[1].set_ylabel('CH 指数')
ax[1].set_title('CH 指数(越大越好)')
ax[1].legend()
ax[1].grid(alpha=.3)
fig.suptitle('%s 聚类数 K 选择(完整扫描)' % STRIP)
fig.tight_layout()
out = os.path.join(RESULT_DIR, 'K选择_%s_full.png' % STRIP)
fig.savefig(out, dpi=150)
print('已保存:', out)
