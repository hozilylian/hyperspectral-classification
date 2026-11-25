# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 1. 设置默认字体为 Windows 自带的中文字体（黑体）[2,3](@ref)
plt.rcParams['font.sans-serif'] = ['SimHei']
# 备选：如果 SimHei 报错，可以换成微软雅黑：['Microsoft YaHei']

# 2. 解决负号('-')显示为方块的问题[2,3](@ref)
plt.rcParams['axes.unicode_minus'] = False

# ================= 1. 模拟光谱立方体数据 =================
bands, rows, cols = 272, 20, 20

x = np.linspace(0, 1, cols)
y = np.linspace(0, 1, rows)
X, Y = np.meshgrid(x, y)
base_reflectance = 0.3 + 0.2 * X + 0.1 * Y

wavelengths = np.linspace(400, 1000, bands)
spectrum_curve = 1 - 0.5 * np.exp(-((wavelengths - 700)**2) / 2000)

hypercube = np.zeros((bands, rows, cols))
for i in range(bands):
    hypercube[i, :, :] = base_reflectance * spectrum_curve[i] + np.random.rand(rows, cols) * 0.05

# ================= 2. 开始 3D 可视化（仅保留左图，全部中文） =================
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 1. 绘制立方体线框边界
r = [0, rows]
c = [0, cols]
b = [0, bands]
for s, e in zip(r, r):
    ax.plot3D([s, s], [c[0], c[1]], [b[0], b[0]], 'k-', linewidth=2)
    ax.plot3D([s, s], [c[0], c[1]], [b[1], b[1]], 'k-', linewidth=2)
for s, e in zip(c, c):
    ax.plot3D([r[0], r[1]], [s, s], [b[0], b[0]], 'k-', linewidth=2)
    ax.plot3D([r[0], r[1]], [s, s], [b[1], b[1]], 'k-', linewidth=2)
for s, e in zip(b, b):
    ax.plot3D([r[0], r[1]], [c[0], c[0]], [s, s], 'k-', linewidth=2)
    ax.plot3D([r[0], r[1]], [c[1], c[1]], [s, s], 'k-', linewidth=2)

# 2. 绘制顶面（伪彩色图像，代表空间分布）
xx, yy = np.meshgrid(np.arange(cols), np.arange(rows))
zz = np.full_like(xx, bands, dtype=float)
ax.plot_surface(xx, yy, zz,
                facecolors=plt.cm.viridis(hypercube[2, :, :]),
                rstride=1, cstride=1, alpha=0.8)

# 3. 绘制侧面（光谱曲线束，代表光谱维度）
for i in range(0, cols, 5):
    for j in range(0, rows, 5):
        curve = hypercube[:, j, i] * rows
        ax.plot3D([i]*bands, [j]*bands, np.arange(bands) + curve,
                  color='gray', alpha=0.5, linewidth=1)

# 4. 高亮提取某一个像元的完整光谱曲线（红色粗线）
target_c, target_r = 10, 10
target_curve = hypercube[:, target_r, target_c] * rows
ax.plot3D([target_c]*bands, [target_r]*bands, np.arange(bands) + target_curve,
          color='red', linewidth=3, label='目标像元光谱')
ax.scatter3D(target_c, target_r, bands, color='red', s=50, zorder=5)

# 设置坐标轴标签（中文）
ax.set_xlabel('列数（样本）')
ax.set_ylabel('行数（扫描线）')
ax.set_zlabel('波段数（272个，400~1000 nm）')
ax.set_title('光谱立方体三维示意图', fontsize=14)
ax.legend(loc='upper left')
ax.view_init(elev=25, azim=-45)

plt.tight_layout()
plt.show()